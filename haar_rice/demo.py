import os
import sys
import argparse
import numpy as np
from PIL import Image
from .compress import compress, decompress, load_image_grayscale


def psnr(a, b):
    mse = np.mean((a.astype(np.float64) - b.astype(np.float64)) ** 2)
    if mse == 0:
        return float('inf')
    return 20.0 * np.log10(255.0 / np.sqrt(mse))


def main():
    p = argparse.ArgumentParser()
    p.add_argument('infile', nargs='?', default=None)
    p.add_argument('--levels', type=int, default=1)
    p.add_argument('--qstep', type=float, default=10.0)
    p.add_argument('--block-size', type=int, default=32)
    args = p.parse_args()

    if args.infile is None:
        # generate a synthetic RGB test image (gradient + checker)
        w, h = 256, 256
        xv = np.linspace(0, 255, w, dtype=np.uint8)
        yv = np.linspace(0, 255, h, dtype=np.uint8)[:, None]
        r = np.clip(xv[None, :], 0, 255).astype(np.uint8)
        g = np.clip(yv, 0, 255).astype(np.uint8)
        b = ((r // 32) ^ (g // 32)) * 32
        img = np.stack([r, g, b], axis=2)
        print('Using generated test image')
    else:
        im = Image.open(args.infile)
        img = np.array(im.convert('RGB'))

    original_size = img.nbytes
    container = compress(img, levels=args.levels, qstep=args.qstep, block_size=args.block_size)
    compressed_size = len(container)

    rec = decompress(container)

    if rec.ndim == 3:
        metric_src = img
        metric_rec = rec
    else:
        metric_src = Image.fromarray(img).convert('L') if img.ndim == 3 else img
        metric_rec = rec

    if metric_src.ndim == 3:
        # compute PSNR on Y channel
        from PIL import Image
        ysrc = np.array(Image.fromarray(metric_src).convert('YCbCr'))[:, :, 0]
        yrec = np.array(Image.fromarray(metric_rec).convert('YCbCr'))[:, :, 0]
        value = psnr(ysrc, yrec)
    else:
        value = psnr(metric_src, metric_rec)

    print(f'Original bytes: {original_size}')
    print(f'Compressed bytes: {compressed_size}')
    print(f'PSNR (Y): {value:.2f} dB')


if __name__ == '__main__':
    main()
