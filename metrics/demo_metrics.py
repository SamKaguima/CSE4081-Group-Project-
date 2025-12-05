"""Compute bytes and PSNR between original and decompressed images.

Usage:
    python demo_metrics.py original_file compressed_file decompressed_file

The script prints the file sizes (bytes) for the three files and the PSNR
between the original and decompressed images (computed on luma/Y channel
for color images).
"""
from __future__ import annotations

import os
import sys
import argparse
from typing import Tuple

import numpy as np
from PIL import Image
import struct


def filesize(path: str) -> int:
    return os.path.getsize(path)


def parse_hrc(path: str) -> dict | None:
    """Parse a simple HR01 container header and return info, or None if not HR01.

    Format (per README):
      4 bytes: magic b'HR01'
      1 byte: version (1)
      4 bytes: height (uint32, big-endian)
      4 bytes: width (uint32)
      1 byte: levels (uint8)
      1 byte: channels (uint8)
      4 bytes: qstep (float32 big-endian)
      4 bytes: block_size (uint32)
      then for each channel:
        4 bytes: payload length (uint32)
        payload bytes
    """
    try:
        with open(path, 'rb') as f:
            hdr = f.read(4)
            if hdr != b'HR01':
                return None
            ver = f.read(1)
            version = ver[0]
            be = f.read(4)
            height = struct.unpack('>I', be)[0]
            be = f.read(4)
            width = struct.unpack('>I', be)[0]
            levels = ord(f.read(1))
            channels = ord(f.read(1))
            qstep_be = f.read(4)
            qstep = struct.unpack('>f', qstep_be)[0]
            block_be = f.read(4)
            block_size = struct.unpack('>I', block_be)[0]

            payloads = []
            for c in range(channels):
                plen_be = f.read(4)
                if len(plen_be) < 4:
                    break
                plen = struct.unpack('>I', plen_be)[0]
                payloads.append(plen)
                # skip ahead by payload length
                f.seek(plen, os.SEEK_CUR)

            return {
                'version': version,
                'height': height,
                'width': width,
                'levels': levels,
                'channels': channels,
                'qstep': qstep,
                'block_size': block_size,
                'payloads': payloads,
                'payload_total': sum(payloads)
            }
    except Exception:
        return None


def load_image_as_array(path: str) -> np.ndarray:
    im = Image.open(path)
    # preserve grayscale if image is single-channel, otherwise use RGB
    if im.mode == 'L':
        return np.array(im)
    # convert RGBA to RGB, keep RGB as-is
    if im.mode == 'RGBA':
        return np.array(im.convert('RGB'))
    return np.array(im.convert('RGB'))


def psnr(a: np.ndarray, b: np.ndarray) -> float:
    # both arrays expected to have values in [0,255]
    a = a.astype(np.float64)
    b = b.astype(np.float64)
    mse = np.mean((a - b) ** 2)
    if mse == 0:
        return float('inf')
    return 20.0 * np.log10(255.0 / np.sqrt(mse))


def compute_luma_channel(arr: np.ndarray) -> np.ndarray:
    # arr can be HxW (grayscale) or HxWx3 (RGB)
    if arr.ndim == 2:
        return arr
    # convert RGB to Y channel using ITU-R BT.601 luma
    # Use PIL for conversion to avoid manual mistakes
    im = Image.fromarray(arr.astype(np.uint8))
    ycbcr = np.array(im.convert('YCbCr'))
    return ycbcr[:, :, 0]


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    p = argparse.ArgumentParser(description='Report bytes and PSNR for given files')
    p.add_argument('original', help='Original image file (e.g., JPG/PNG)')
    p.add_argument('compressed', help='Compressed container/file (any file)')
    p.add_argument('decompressed', help='Decompressed image file (reconstructed image)')
    args = p.parse_args(argv)

    for path in (args.original, args.compressed, args.decompressed):
        if not os.path.exists(path):
            print(f"Error: file not found: {path}", file=sys.stderr)
            return 2

    # Print diagnostics: file types / image modes and raw pixel bytes
    def image_info(path: str) -> dict | None:
        try:
            im = Image.open(path)
        except Exception:
            return None
        mode = im.mode
        size = im.size  # (width, height)
        arr = np.array(im.convert('RGB')) if mode != 'L' else np.array(im)
        return {'mode': mode, 'size': size, 'nbytes': arr.nbytes}

    orig_info = image_info(args.original)
    decomp_info = image_info(args.decompressed)

    # parse HR01 header if present (we'll use payload_total below)
    hrc = parse_hrc(args.compressed)

    # Use raw in-memory bytes for images where possible; for compressed file use
    # HR01 payload_total when available, otherwise fall back to file size.
    if orig_info is not None:
        orig_bytes = int(orig_info['nbytes'])
    else:
        orig_bytes = filesize(args.original)

    if decomp_info is not None:
        decomp_bytes = int(decomp_info['nbytes'])
    else:
        decomp_bytes = filesize(args.decompressed)

    if hrc is not None and 'payload_total' in hrc:
        comp_bytes = int(hrc['payload_total'])
    else:
        comp_bytes = filesize(args.compressed)

    # Compute compression ratio and compressed-size percentage (using the
    # chosen byte semantics above: raw image bytes vs payload bytes).
    if comp_bytes > 0 and orig_bytes > 0:
        compression_ratio = float(orig_bytes) / float(comp_bytes)
        compressed_percent = float(comp_bytes) / float(orig_bytes) * 100.0
    else:
        compression_ratio = None
        compressed_percent = None

    try:
        orig_arr = load_image_as_array(args.original)
        decomp_arr = load_image_as_array(args.decompressed)
    except Exception as e:
        print(f"Error loading images for PSNR: {e}", file=sys.stderr)
        return 3

    # If spatial dimensions differ, that's an error.
    if orig_arr.shape[0:2] != decomp_arr.shape[0:2]:
        print("Error: original and decompressed images have different spatial dimensions:")
        print(f"  original: {orig_arr.shape}")
        print(f"  decompressed: {decomp_arr.shape}")
        print("Make sure the decompressed image has the same width/height as the original.")
        return 4

    # Handle color/grayscale mismatch: compare on luma when either image is color
    if orig_arr.ndim == 3 and decomp_arr.ndim == 2:
        y_orig = compute_luma_channel(orig_arr)
        y_decomp = decomp_arr
        psnr_val = psnr(y_orig, y_decomp)
    elif orig_arr.ndim == 2 and decomp_arr.ndim == 3:
        y_orig = orig_arr
        y_decomp = compute_luma_channel(decomp_arr)
        psnr_val = psnr(y_orig, y_decomp)
    elif orig_arr.ndim == 3 and decomp_arr.ndim == 3:
        # both color: compute PSNR on luma channel
        y_orig = compute_luma_channel(orig_arr)
        y_decomp = compute_luma_channel(decomp_arr)
        psnr_val = psnr(y_orig, y_decomp)
    else:
        # both grayscale
        psnr_val = psnr(orig_arr, decomp_arr)

    print(f"Original raw bytes: {orig_bytes:,} bytes")
    print(f"Compressed payload bytes: {comp_bytes:,} bytes")
    print(f"Space Saved : {orig_bytes - comp_bytes:,} bytes ({(orig_bytes - comp_bytes) / orig_bytes * 100:.2f}%)")
    print(f"Decompressed raw bytes: {decomp_bytes:,} bytes")
    if compression_ratio is None:
        print("Compression ratio: N/A")
    else:
        # show as "X.XX:1" and also compressed size as percentage of original
        print(f"Compression ratio (original / compressed): {compression_ratio:.2f}:1")
        print(f"Compressed size is {compressed_percent:.1f}% of original")
    if psnr_val == float('inf'):
        print("PSNR: inf (images identical)")
    else:
        print(f"PSNR: {psnr_val:.2f} dB")

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
