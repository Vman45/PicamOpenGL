from threading import Event

from picamera import PiCamera, mmal, mmalobj as mo
import numpy as np

# from memory_profiler import profile

class CameraMO(mo.MMALPythonComponent):
    def __init__(self, width, height, run, event, tflite):
        super(CameraMO, self).__init__(name='py.CameraMO')
        self.inputs[0].supported_formats = mmal.MMAL_ENCODING_RGB24

        self.w = width
        self.h = height
        self.count = 0
        self.run = run

        self.event = event

        self.tflite = tflite

    # @profile
    def _handle_frame(self, port, buf):
        # Get picam width and height
        cam_width = port._format[0].es[0].video.width
        cam_height = port._format[0].es[0].video.height
        # Convert raw data for numpy
        ori_img = np.frombuffer(buf.data, dtype="uint8").reshape(cam_height, cam_width, 3)
        np_img = ori_img[:self.h, :self.w]

        if self.tflite:
            self.tflite.run(np_img)

        self.count += 1
        if self.count >= self.run:
            self.event.set()

        return False

# @profile
def picam_mmal(width, height, run, tflite=None):
    camera = mo.MMALCamera()
    camera.outputs[1].framesize = (width, height)
    camera.outputs[1].commit()

    event = Event()

    transform = CameraMO(width, height, run, event, tflite)

    # connect to camera out[1]
    transform.inputs[0].connect(camera.outputs[1])
    # enable the connection
    transform.connection.enable()

    # enable all components
    transform.enable()
    camera.enable()

    # Enable capture
    camera.outputs[1].params[mmal.MMAL_PARAMETER_CAPTURE] = True

    # Wait for event object to be set before returning
    event.wait()

    # Disable capture
    camera.outputs[1].params[mmal.MMAL_PARAMETER_CAPTURE] = False
    # Cleanup
    camera.close()

# @profile
def picam_normal(width, height, run, tflite=None):
    with PiCamera() as camera:
        camera.resolution = (width, height)
        # (H,W,C) layout
        np_img = np.empty((height, width, 3), dtype=np.uint8)
        for _ in range(run):
            camera.capture(np_img, 'rgb', use_video_port=True, resize=(width, height))
            if tflite:
                tflite.run(np_img)