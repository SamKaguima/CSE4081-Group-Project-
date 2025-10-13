Haar-Rice Image Compression (Python)
===================================

A small educational implementation of a lossy image compressor using the 2D Haar wavelet transform, uniform quantization, and adaptive Rice entropy coding. The project implements a complete end-to-end encoder/decoder pipeline in pure Python (NumPy + Pillow) with a small CLI and a demo script.

What you'll find in this workspace
----------------------------------
- `haar_rice/` — package sources
  - `dwt.py` — 2D Haar DWT / inverse
  - `quant.py` — uniform quantization / dequantization
  - `bitstream.py` — efficient BitWriter / BitReader (MSB-first)
  - `rice.py` — adaptive Rice coder (per-block m selection)
  - `compress.py` — top-level compress/decompress (containerized format)
  - `cli.py` — command-line interface (encode / decode)
  - `demo.py` — simple demo that compresses/decompresses and reports PSNR
- `tests/` — pytest tests (one round-trip smoke test)
- `requirements.txt` — Python dependencies

Dependencies
------------
This project targets Python 3.8+ and uses the following third-party packages:
- numpy
- Pillow
- pytest (for running tests)

Install into a virtual environment (PowerShell example):

```powershell
python -m venv .venv
& .\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Quick examples
--------------
(Use PowerShell. Replace the python path if you're not using the workspace `.venv`.)

Run the demo (generates a test image if you don't give an input path):

```powershell
& 'C:/.../goup proj test/.venv/Scripts/python.exe' -m haar_rice.demo
# or with an input image
& 'C:/.../goup proj test/.venv/Scripts/python.exe' -m haar_rice.demo C:\path\to\image.jpg --levels 2 --qstep 8.0 --block-size 32
```

Encode / decode with the CLI

```powershell
# Encode (writes a single container file)
& 'C:/.../goup proj test/.venv/Scripts/python.exe' -m haar_rice.cli encode input.jpg output.hrc --levels 1 --qstep 10.0 --block-size 32

# Decode (reads container and writes reconstructed image)
& 'C:/.../goup proj test/.venv/Scripts/python.exe' -m haar_rice.cli decode output.hrc recon.png
```

Library usage (Python API)
--------------------------
You can import the package and call the functions directly from Python:

```python
from haar_rice.compress import compress, decompress
import numpy as np
# img: numpy array (H,W) uint8 or (H,W,3) uint8
container = compress(img, levels=1, qstep=10.0, block_size=32)
rec = decompress(container)
```

Container format (brief)
------------------------
The compressed output is a self-contained binary container. Current layout (version 1):

- 4 bytes: magic `b'HR01'`
- 1 byte: version (1)
- 4 bytes: height (uint32, big-endian)
- 4 bytes: width (uint32)
- 1 byte: levels (uint8)
- 1 byte: channels (uint8) — 1 for grayscale, 3 for YCbCr (RGB input converted to YCbCr)
- 4 bytes: qstep (float32 big-endian)
- 4 bytes: block_size (uint32)
- then, for each channel in order (Y, Cb, Cr or single channel):
  - 4 bytes: payload length in bytes (uint32)
  - payload bytes: Rice-coded blocks — each block itself internally stores each block's bit-length followed by bit-packed block bytes (see source for exact layout)

Notes
-----
- RGB images are converted to YCbCr for compression and converted back on decode. PSNR reported by the demo is computed on the luma (Y) channel.
- The implementation is educational and not optimized for production-level performance. The Rice coder and bitstreams are implemented in Python; for speed sensitive use-cases you could replace them with a C/Cython extension or optimize large-block vectorization.
- Quantization is uniform across channels; you may achieve better perceptual results using smaller qstep for Y and larger qstep for chroma channels, or by applying chroma subsampling (e.g., 4:2:0) which is not currently implemented.

Testing
-------
Run the unit tests with pytest:

```powershell
& 'C:/.../goup proj test/.venv/Scripts/python.exe' -m pytest -q
```

Developer notes and next steps
------------------------------
- Possible improvements:
  - Chroma subsampling (4:2:0) to reduce chroma payloads significantly.
  - Per-channel quantization steps (different qstep for Y vs Cb/Cr).
  - Replace Python string-based m-selection loops with NumPy vectorized heuristics or C acceleration.
  - Add a simple `.hrc` extension and more robust container metadata (codec versioning, original dtype, checksum).
  - Add PSNR/SSIM utilities for evaluation, and a small benchmarking script.

If you want, I can implement any of the above. Tell me which you'd like next (for example: add 4:2:0 subsampling and the corresponding decode upsampling, or save the container and reconstructed image from the demo automatically). 

License & disclaimer
--------------------
This code is educational and provided as-is. It's intended for experimentation and learning about wavelet-based compression and Rice coding, not for production use.
