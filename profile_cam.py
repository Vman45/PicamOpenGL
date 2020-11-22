import sys
import argparse
import cProfile

from profiling import camera
from utils import tflite

def profile_cam(run = None, cam_input = None, out_file = None):
    cam_input_mapping = {
        "mmal": camera.picam_mmal,
        "picam": camera.picam_normal
    }
    if cam_input not in cam_input_mapping:
        sys.exit("Invalid options")

    pr = cProfile.Profile()
    # Tf model
    tflite_obj = tflite.Blazeface_Tflite("weights/face_detection_front.tflite", "weights/anchors.npy")
    width, height = tflite_obj.get_reso()

    pr.enable()
    # Run camera profile
    cam_input_mapping[cam_input](width, height, run, tflite_obj)
    pr.disable()

    if out_file:
        pr.dump_stats(out_file)
    else:
        pr.print_stats()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("out_file", nargs='?', default=None, help="Output of profiler stats")
    parser.add_argument("--run", type=int, default=500, help="Number of runs [Default: 500]")
    parser.add_argument("--cam_input", default="mmal", help="Type of camera input implementation [Default: mmal | picam]")
    args = parser.parse_args()
    profile_cam(**vars(args))