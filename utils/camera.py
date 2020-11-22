from threading import Thread, Event
from multiprocessing import Process, Event as mp_Event

from picamera import PiCamera, mmal, mmalobj as mo
import numpy as np

from utils.common import BaseNode

class BaseCamera(BaseNode):
    def __init__(self, width, height):
        BaseNode.__init__(self)
        self.w = width
        self.h = height

    def start(self):
        raise NotImplementedError()

    def stop(self):
        raise NotImplementedError()

class CameraThread(Thread, BaseCamera):
    def __init__(self, width, height):
        Thread.__init__(self)
        BaseCamera.__init__(self, width, height)

        self.stop_event = Event()

    def run(self):
        with PiCamera() as camera:
            camera.resolution = (self.w, self.h)
            # (H,W,C) layout
            np_img = np.empty((self.h, self.w, 3), dtype=np.uint8)
            while not self.stop_event.is_set():
                camera.capture(np_img, 'rgb', use_video_port=True, resize=(self.w, self.h))
                if self.next_node:
                    self.next_node.run(np_img)

    def stop(self):
        self.stop_event.set()

class CameraMp(Process, BaseCamera):
    def __init__(self, width, height):
        Process.__init__(self)
        BaseCamera.__init__(self, width, height)

        self.stop_event = mp_Event()

    def run(self):
        with PiCamera() as camera:
            camera.resolution = (self.w, self.h)
            # (H,W,C) layout
            np_img = np.empty((self.h, self.w, 3), dtype=np.uint8)
            while not self.stop_event.is_set():
                camera.capture(np_img, 'rgb', use_video_port=True, resize=(self.w, self.h))
                if self.next_node:
                    self.next_node.run(np_img)

    def stop(self):
        self.stop_event.set()

class CameraMmal(BaseCamera):
    class CameraMO(mo.MMALPythonComponent, BaseNode):
        def __init__(self, width, height):
            mo.MMALPythonComponent.__init__(self, name='py.CameraMO')
            BaseNode.__init__(self)
            self.inputs[0].supported_formats = mmal.MMAL_ENCODING_RGB24

            self.w = width
            self.h = height

        def _handle_frame(self, port, buf):
            # Get picam width and height
            cam_width = port._format[0].es[0].video.width
            cam_height = port._format[0].es[0].video.height
            # Convert raw data for numpy
            ori_img = np.frombuffer(buf.data, dtype="uint8").reshape(cam_height, cam_width, 3)
            # TODO: Could look into resize like camera.capture instead of simple slicing
            np_img = ori_img[:self.h, :self.w]

            if self.next_node:
                self.next_node.run(np_img)

            return False

    def __init__(self, width, height):
        BaseCamera.__init__(self, width, height)

        self.camera = mo.MMALCamera()
        self.camera.outputs[1].framesize = (self.w, self.h)
        self.camera.outputs[1].commit()

        self.transform = self.CameraMO(self.w, self.h)

        # connect to camera out[1]
        self.transform.inputs[0].connect(self.camera.outputs[1])
        # enable the connection
        self.transform.connection.enable()

        # enable all components
        self.transform.enable()
        self.camera.enable()

    def set_next(self, node):
        self.transform.set_next(node)

    # Common interface for camera
    def start(self):
        # Need set to True before using it
        # Link: https://picamera.readthedocs.io/en/release-1.13/api_mmalobj.html#file-output-rgb-capture
        self.camera.outputs[1].params[mmal.MMAL_PARAMETER_CAPTURE] = True

    def stop(self):
        self.camera.outputs[1].params[mmal.MMAL_PARAMETER_CAPTURE] = False