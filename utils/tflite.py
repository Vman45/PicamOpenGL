import numpy as np
from tflite_runtime.interpreter import Interpreter

from utils.common import BaseNode
from utils.message import ResultMsg

class Tflite_CV_Helper(BaseNode):
    def __init__(self, model_path, threshold=0.7, nms_threshold=0.3):
        BaseNode.__init__(self)
        self.interpreter = Interpreter(model_path=model_path)
        self.interpreter.allocate_tensors()
        # (batch, height, width, channel) OR (B,H,W,C)
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
        self.width = self.input_details[0]['shape'][2]
        self.height = self.input_details[0]['shape'][1]
        self.threshold = threshold
        self.nms_threshold = nms_threshold

    def _nms(self, boxes):
        # Bottom left (x1, y1)
        # Top right (x2, y2)
        # Score at last column
        # Area width (x2 - x1) X height (y2 - y1)
        x1 = boxes[:,0]
        y1 = boxes[:,1]
        x2 = boxes[:,2]
        y2 = boxes[:,3]
        score = boxes[:,-1]
        area = (x2 - x1) * (y2 - y1)
        # Indices sorted by score, descending order
        indices = np.argsort(score)[::-1]

        # Indexes that should remain
        remain_list = []
        while indices.size > 0:
            # Take highest score to get overlap
            i = indices[0]
            remain_list.append(i)
            # Get all intersection coordinates where
            # Bottom left -> (max(Xa1, Xb1), max(Ya1, Yb1))
            # Top right -> (min(Xa2, Xb2), min(Ya1, Yb1))
            xx1 = np.maximum(x1[i], x1[indices[1:]])
            yy1 = np.maximum(y1[i], y1[indices[1:]])
            xx2 = np.minimum(x2[i], x2[indices[1:]])
            yy2 = np.minimum(y2[i], y2[indices[1:]])
            # Get indices that has overlap lesser than threshold
            w = np.maximum(0.0, xx2 - xx1)
            h = np.maximum(0.0, yy2 - yy1)
            overlap = (w * h) / area[indices[1:]]
            # Offset by 1, since overlap does not contain i
            new_indices = np.where(overlap < self.nms_threshold)[0] + 1
            # Only keeping those left than threshold
            indices = indices[new_indices]
        return remain_list

    def run(self, orig_img):
        raise NotImplementedError()

    def get_reso(self):
        return (self.width, self.height)

class Blazeface_Tflite(Tflite_CV_Helper):
    def __init__(self, model_path, anchor=None, threshold=0.7, nms_threshold=0.3, *_args, **kwargs):
        Tflite_CV_Helper.__init__(self, model_path, threshold, nms_threshold)
        self.anchors = np.load(anchor)

    def _decode_boxes(self, raw_boxes):
        # Anchors is important to scale
        # Scale x_centre and y_centre from (0,1) to (-1,1) range for OpenGL
        if raw_boxes.size == 0:
            return raw_boxes
        boxes = raw_boxes[:]
        x_centre = raw_boxes[..., 0] / self.width * self.anchors[:, 2] + self.anchors[:, 0]
        y_centre = raw_boxes[..., 1] / self.height * self.anchors[:, 3] + self.anchors[:, 1]
        x_centre = x_centre * 2 - 1.0
        y_centre = y_centre * 2 - 1.0

        w = raw_boxes[..., 2] / self.width * self.anchors[:, 2]
        h = raw_boxes[..., 3] / self.height * self.anchors[:, 3]

        boxes[..., 0] = x_centre - w
        boxes[..., 1] = y_centre - h
        boxes[..., 2] = x_centre + w
        boxes[..., 3] = y_centre + h

        return boxes

    def run(self, orig_img):
        # Convert from (H, W, C) to (1, H, W, C)
        np_img = np.expand_dims(orig_img, axis=0)
        # Convert to float and normalise to (-1, 1)
        np_img = (np_img.astype(np.float32) / 127.5) - 1.0

        # TFlite inference
        self.interpreter.set_tensor(self.input_details[0]['index'], np_img)
        self.interpreter.invoke()

        # Output shape [0] -> (1, 896, 16), [1] -> (1, 896, 1)
        # Shape is (896, 16)
        boxes = self.interpreter.get_tensor(self.output_details[0]['index'])[0]
        # Shape is (896, 1)
        scores = self.interpreter.get_tensor(self.output_details[1]['index'])[0]
        # Shape is (896, 17)
        combined = np.concatenate((boxes, scores), axis=1)
        # Convert to bounding box coord (x1, y1, x2, y2)
        combined = self._decode_boxes(combined)
        # Remove output lower than threshold
        combined = combined[np.where(combined[:, -1] >= self.threshold)[0]]

        result = []

        if combined.shape[0] > 0:
            # Keeping only those pass nms
            nms_indices = self._nms(combined)
            # Loop to add into json
            for i in nms_indices:
                result.append(
                    {
                        "boxes": np.copy(combined[i][:4]), # Required to copy as it is pointer
                        "scores": min(1.0, combined[i][-1])
                    }
                )

        if self.next_node:
            self.next_node.run(ResultMsg(orig_img.tobytes(), result))
        return 