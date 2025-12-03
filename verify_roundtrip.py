"""Verify bit-identical round-trip between an original and a decompressed image.

Usage:
    python verify_roundtrip.py original_image decompressed_image [--luma]

By default the script performs an exact pixel-wise comparison. If the
images have different channel counts but you want to compare luma (Y)
values instead, pass `--luma` to convert both images to the Y channel
and compare those.

Exit code: 0 if images are bit-identical (under the chosen comparison),
1 otherwise.
"""
from __future__ import annotations

import sys
import argparse
from PIL import Image
import numpy as np


def load_array(path: str) -> np.ndarray:
    im = Image.open(path)
    # preserve mode: return grayscale as 2D array, color as 3D uint8 array
    if im.mode == 'L':
        return np.array(im)
    return np.array(im.convert('RGB'))


def to_luma(arr: np.ndarray) -> np.ndarray:
    # convert HxW or HxWx3 to luma (Y) channel
    if arr.ndim == 2:
        return arr
    im = Image.fromarray(arr.astype(np.uint8))
    ycbcr = np.array(im.convert('YCbCr'))
    return ycbcr[:, :, 0]


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    p = argparse.ArgumentParser(description='Verify bit-identical round-trip of images')
    p.add_argument('original')
    p.add_argument('decompressed')
    p.add_argument('--luma', action='store_true', help='Compare luma (Y) channel instead of full pixels')
    args = p.parse_args(argv)

    try:
        a = load_array(args.original)
    except Exception as e:
        print(f"Error loading original image: {e}", file=sys.stderr)
        return 2

    try:
        b = load_array(args.decompressed)
    except Exception as e:
        print(f"Error loading decompressed image: {e}", file=sys.stderr)
        return 3

    if args.luma:
        a = to_luma(a)
        b = to_luma(b)

    # check spatial dims
    if a.shape[0:2] != b.shape[0:2]:
        print("ERROR: images have different spatial dimensions:")
        print(f"  original: {a.shape}")
        print(f"  decompressed: {b.shape}")
        return 4

    # for exact pixel compare, shapes must match exactly
    if not args.luma and a.shape != b.shape:
        print("ERROR: images have different channel counts or shapes for exact compare:")
        print(f"  original: {a.shape}")
        print(f"  decompressed: {b.shape}")
        print("Use --luma to compare luma when channel counts differ.")
        return 5

    # compute difference statistics
    equal = np.array_equal(a, b)
    diff = np.abs(a.astype(np.int32) - b.astype(np.int32))
    max_diff = int(diff.max()) if diff.size > 0 else 0
    mean_diff = float(diff.mean()) if diff.size > 0 else 0.0
    num_pixels = diff.size
    num_nonzero = int(np.count_nonzero(diff))

    print(f"Bit-identical: {bool(equal)}")
    print(f"Max abs diff: {max_diff}")
    print(f"Mean abs diff: {mean_diff:.4f}")
    print(f"Pixels different: {num_nonzero}/{num_pixels} ({(num_nonzero/num_pixels*100 if num_pixels else 0):.4f}%)")

    return 0 if equal else 1


if __name__ == '__main__':
    raise SystemExit(main())
