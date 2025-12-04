"""Visualize contents of an HR01 compressed container.

This script extracts the quantized coefficient maps stored in the HR01
container (the values encoded by the Rice coder, before dequantization and
inverse DWT) and writes simple visualizations for each channel. Optionally
it can also run the normal decompressor and save the reconstructed image.

Usage:
    python view_compressed.py file.hrc --out-prefix out

Outputs (for each channel):
  - `{out_prefix}_ch{n}_quant.png`       : normalized quantized coefficients
  - `{out_prefix}_ch{n}_quant_log.png`   : log(1+abs(coeff)) normalized

Optional:
  --reconstruct : also write the reconstructed image using the existing decompress()
"""
from __future__ import annotations

import argparse
import os
import struct
import numpy as np
from PIL import Image

from haar_rice.rice import RiceCoder
from haar_rice.compress import decompress


def parse_hr01_header(path: str):
    with open(path, 'rb') as f:
        hdr = f.read(4)
        if hdr != b'HR01':
            raise ValueError('not an HR01 container')
        version = ord(f.read(1))
        h = struct.unpack('>I', f.read(4))[0]
        w = struct.unpack('>I', f.read(4))[0]
        levels = ord(f.read(1))
        channels = ord(f.read(1))
        qstep = struct.unpack('>f', f.read(4))[0]
        block_size = struct.unpack('>I', f.read(4))[0]
        # return file position and header info
        idx = f.tell()
    return {'version': version, 'h': h, 'w': w, 'levels': levels,
            'channels': channels, 'qstep': qstep, 'block_size': block_size,
            'payload_offset': idx}


def extract_quant_maps(path: str):
    info = parse_hr01_header(path)
    h, w = info['h'], info['w']
    channels = info['channels']
    coder = RiceCoder()
    maps = []
    with open(path, 'rb') as f:
        f.seek(info['payload_offset'])
        for c in range(channels):
            plen_be = f.read(4)
            if len(plen_be) < 4:
                raise ValueError('truncated container')
            plen = struct.unpack('>I', plen_be)[0]
            payload = f.read(plen)
            blocks = coder.decode_bytes_to_blocks(payload)
            flat = []
            for b in blocks:
                flat.extend(b)
            arr = np.array(flat, dtype=np.int32).reshape((h, w))
            maps.append(arr)
    return maps, info


def save_vis(arr: np.ndarray, path_prefix: str, ch: int):
    mn = float(arr.min())
    mx = float(arr.max())
    if mx == mn:
        norm = np.zeros_like(arr, dtype=np.uint8)
    else:
        norm = ((arr - mn) / (mx - mn) * 255.0).astype(np.uint8)
    Image.fromarray(norm).save(f"{path_prefix}_ch{ch}_quant.png")

    # log magnitude visualization
    log = np.log1p(np.abs(arr)).astype(np.float64)
    lm = log.max()
    if lm == 0:
        lnorm = np.zeros_like(log, dtype=np.uint8)
    else:
        lnorm = (log / lm * 255.0).astype(np.uint8)
    Image.fromarray(lnorm).save(f"{path_prefix}_ch{ch}_quant_log.png")


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        import sys
        argv = sys.argv[1:]

    p = argparse.ArgumentParser(description='Visualize HR01 compressed container')
    p.add_argument('container')
    p.add_argument('--out-prefix', default='out', help='output filename prefix')
    p.add_argument('--reconstruct', action='store_true', help='also write reconstructed image')
    args = p.parse_args(argv)

    maps, info = extract_quant_maps(args.container)
    for i, m in enumerate(maps):
        save_vis(m, args.out_prefix, i)

    if args.reconstruct:
        with open(args.container, 'rb') as f:
            cont = f.read()
        rec = decompress(cont)
        # save reconstructed; choose extension based on prefix
        outpath = f"{args.out_prefix}_recon.png"
        Image.fromarray(rec).save(outpath)
        print('Wrote reconstructed image to', outpath)

    print('Wrote quantized coefficient visualizations for', len(maps), 'channel(s)')
    return 0


if __name__ == '__main__':
    import sys
    raise SystemExit(main(sys.argv[1:]))
