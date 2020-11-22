# PicamOpengGL #

This project utilised `picamera` to capture the image data, run face detection on the image with `tflite` and render it via `PyOpenGL`.

### Tested Environment

- Hardware
> - Raspberry Pi 3B+
> - Raspberry Pi Camera Module v1
- OS
> - Raspberry Pi OS (32-bit) 2020-05-27

### Setup

1. Enable camera access via **Raspberry Pi Configuration**
2. Enable Fake KMS OpenGL driver via **raspi-config**
3. Run **./setup.sh**

### Run

```bash
1. source .env/bin/activate
2. python inference.py
3. To exit, press `q` (opengl) or `Ctrl + C` (null)

** For run options, use `python inference.py --help`
```

### Result

| Script                                            | FPS   |
|---------------------------------------------------|-------|
| inference.py --renderer=opengl --cam_input=mmal   | ~15.8 |
| inference.py --renderer=opengl --cam_input=thread | ~7.5  |
| inference.py --renderer=opengl --cam_input=mp     | ~7.5  |
| inference.py --renderer=null --cam_input=mmal     | ~15.8 |
| inference.py --renderer=null --cam_input=thread   | ~8.5  |
| inference.py --renderer=null --cam_input=mp       | ~8.5  |

#### Observation

- There is no significant difference in the result for `thread` and `mp`
> - Global Interpreter Lock does not affect significantly in this application

- Suspect there is a difference due to how the numpy array was constructed `thread` vs `mmal`
> - `thread` method uses `PiCamera` interface to write to `numpy` array
> - `mmal` convert raw buffer to `numpy` array
> - There could be overhead by using `PiCamera` as there is message when using `rgb` instead of `rgba`

```text
PiCameraAlphaStripping: using alpha-stripping to convert to non-alpha format; you may find the equivalent alpha format faster
  "using alpha-stripping to convert to non-alpha"
```

### Profiling

##### Pi cam

```bash
1. source .env/bin/activate
2. python profile_cam.py

** For run options, use `python profile_cam.py --help`
```

- `cProfile` and `memory_profiler` does not show anything significant in describing the differences
> - `cProfile`: [mmal](misc/cProfiler_mmal.log) & [picam](misc/cProfiler_picam.log)
> - `memory_profiler`: [more info](misc/memory_profiler.md)

### Links

- [`picamera`](https://picamera.readthedocs.io/en/release-1.13/)
- [`tflite`](https://www.tensorflow.org/lite/)
- [`PyOpenGL`](http://pyopengl.sourceforge.net/)
- [BlazeFace's bounding box anchors (anchors.npy)](https://github.com/hollance/BlazeFace-PyTorch)
- [BlazeFace's model weight (face_detection_front.tflite)](https://github.com/google/mediapipe)

### Reference

- PyOpenGL API document [Link](http://pyopengl.sourceforge.net/documentation/manual-3.0/index.html)
- Non Max suppression [Link](https://github.com/rbgirshick/fast-rcnn/blob/master/lib/utils/nms.py)
- Decoding the tflite model output coordinates [Link](https://github.com/hollance/BlazeFace-PyTorch/blob/5af71b66a9cdb285fa49638a75483f9eab913b22/blazeface.py#L271)