Haar-Rice Image Compression (Python)
===================================

A small implementation of a lossy image compressor using the 2D Haar wavelet transform, uniform quantization, and adaptive Rice entropy coding. The project implements a complete end-to-end encoder/decoder pipeline in pure Python (NumPy + Pillow) with a small CLI and a demo script.

What you'll find in this workspace
----------------------------------
- `haar_rice/` — package sources
  - `dwt.py` — 2D Haar DWT / inverse
  - `quant.py` — uniform quantization / dequantization
  - `bitstream.py` — efficient BitWriter / BitReader (MSB-first)
  - `rice.py` — adaptive Rice coder (per-block m selection)
  - `compress.py` — top-level compress/decompress (containerized format)
  - `cli.py` — command-line interface (encode / decode)
- `tests/` — pytest tests (one round-trip smoke test)
- `demo_metrics.py` — demo script to report file sizes (original + compressed + decompressed), PSNR on luma channel, and compression ratio.


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

### MacOS/Linux
```bash
python -m venv .venv
source .venv/bin/activate
```

Commands 
--------
Encode / decode with the CLI

ext = png, jpg, bmp, etc.

### Encode 
```bash
python -m haar_rice.cli encode test_images/original_image.ext test_out/compressed_image.hrc --levels 1 --qstep 10.0 --block-size 32
```

### Decode 
```bash
python -m haar_rice.cli decode test_out/compressed_image.hrc test_out/recon_image.ext
```
### Run the demo for metrics (compress + decompress + report PSNR on luma channel)
```bash
python demo_metrics.py test_images/original_image.ext test_out/compressed_image.hrc test_out/reconstructed_image.ext
```

Compression parameters
----------------------
This implementation has three main parameters that control compression behavior:

- `--levels` (DWT decomposition levels): how many times the 2D Haar wavelet is applied. Higher levels increase the transform depth, producing larger low-frequency (LL) bands and finer high-frequency subbands. Increasing `levels` can improve compression of smooth images but requires image dimensions divisible by `2**levels`.

- `--qstep` (quantization step, float): uniform quantization step size applied to wavelet coefficients. Larger `qstep` → more aggressive quantization → higher compression and lower bitrate, but increased distortion (lower PSNR). Smaller `qstep` (closer to 0) preserves more detail and yields higher PSNR at the cost of larger payloads. Typical default: `10.0`.

- `--block-size` (integer): the number of quantized coefficients grouped into blocks for adaptive Rice coding. Larger block sizes can slightly improve entropy coding efficiency (fewer coding headers) but increase per-block adaptation cost and memory working set. Typical default: `32`.

Guidance and trade-offs
- For high-quality reconstructions (high PSNR): use fewer `levels` (1–2) and a small `qstep` (e.g., 1.0–5.0). File size will be larger.
- For stronger compression: increase `qstep` (e.g., 8.0–20.0). You may also experiment with higher `levels` on images with large smooth regions.
- `block-size` rarely needs tuning; keep the default unless you are profiling compression ratio vs block-encoding overhead.

CLI flags
- `--levels N` — integer (default `1`)
- `--qstep F` — float (default `10.0`)
- `--block-size N` — integer (default `32`)


### Run the verifier (lossy vs lossless round-trip test)
```bash
python metrics/verify.py test_images/original_image test_out/reconstructed_image.ext
```

### Run the compressesed image viewer 
```bash
python view_compressed.py test_out/compressed_image.hrc
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




