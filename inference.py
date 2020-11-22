import argparse
import atexit

from utils import camera, queue_helper, render, tflite, common

# Mapping
MODEL_MAPPING = {
    "blazeface": tflite.Blazeface_Tflite
}
RENDERER_MAPPING = {
    "opengl": render.OpenGLRenderer,
    "null": render.NullRenderer
}
CAM_INPUT_MAPPING = {
    "mmal": camera.CameraMmal,
    "thread": camera.CameraThread,
    "mp": camera.CameraMp
}
QUEUE_MAPPING = {
    "mmal": queue_helper.QueueHelper,
    "thread": queue_helper.QueueHelper,
    "mp": queue_helper.QueueHelperMp
}

def main(width=None, height=None, model=None,
    weight=None, anchor=None, renderer=None, cam_input=None):
    if model not in MODEL_MAPPING or \
        renderer not in RENDERER_MAPPING or \
        cam_input not in CAM_INPUT_MAPPING:
        raise Exception("Invalid options")

    s_queue = QUEUE_MAPPING[cam_input]()
    tflite_obj = MODEL_MAPPING[model](weight, anchor=anchor)
    img_width, img_height = tflite_obj.get_reso()

    renderer_obj = RENDERER_MAPPING[renderer](s_queue, img_width=img_width, img_height=img_height)
    cam_obj = CAM_INPUT_MAPPING[cam_input](img_width, img_height)
    # Need set as daemon to thread, don't matter if cam_obj is CameraMain
    # No conflict with CameraMain's variables
    cam_obj.daemon = True
    # Register atexit
    # Link: https://stackoverflow.com/a/19896361
    atexit.register(lambda cam: cam.stop(), cam_obj)

    # Set next nodes
    common.set_nodes([cam_obj, tflite_obj, s_queue])

    cam_obj.start()
    renderer_obj.render(width=width, height=height)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--width", type=int, default=256, help="Width of render display [Default: 256]")
    parser.add_argument("--height", type=int, default=256, help="Height of render display [Default: 256]")
    parser.add_argument("--model", default="blazeface", help="Type of model [Default: blazeface]")
    parser.add_argument("--weight", default="weights/face_detection_front.tflite", 
        help="Weights for BlazeFace"
    )
    parser.add_argument("--anchor", default="weights/anchors.npy", 
        help="Anchors for BlazeFace"
    )
    parser.add_argument("--renderer", default="opengl", help="Type of renderer [Default: opengl | null]")
    parser.add_argument("--cam_input", default="mmal", help="Type of camera input implementation [Default: mmal | thread]")
    args = parser.parse_args()
    main(**vars(args))