# Third-party notices

## OCT retinal-region U-Net architecture

The `RetinalRegionUNet` adapter in `engine/vigile/cv_unet.py` reimplements the tensor architecture used by [Strange-Philip/oct-retinal-layer-segmentation](https://github.com/Strange-Philip/oct-retinal-layer-segmentation). The upstream project lists Philip Abakah as author and publishes its code under the MIT License. Its trained checkpoint is kept only in the local ignored model directory and is not included in this repository.

```text
MIT License

Copyright (c) 2026 Philip Abakah

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## EchoNet-Dynamic checkpoint

The locally installed segmentation checkpoint was downloaded from the public v1.0.0 EchoNet-Dynamic release. No EchoNet-Dynamic source files are copied into ASTHRAL. The upstream software repository's license prohibits redistribution of its code without written permission. The checkpoint has no separate license statement identified during this integration; it remains local and is not included in Git. Users must confirm their research-use rights before deploying or sharing it. EchoNet-Dynamic's dataset is separately controlled by its non-commercial research-use agreement and is not bundled here.

## MediaPipe Holistic Landmarker

The Python API is pinned to MediaPipe 0.10.21. The official Google AI Edge `holistic_landmarker.task` asset is stored only in the local ignored model directory. MediaPipe is Apache-2.0; consult the [MediaPipe repository](https://github.com/google-ai-edge/mediapipe) and [Holistic Landmarker documentation](https://developers.google.com/edge/mediapipe/solutions/vision/holistic_landmarker) for current terms and API details.
