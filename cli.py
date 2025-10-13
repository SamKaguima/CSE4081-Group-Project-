import argparse
import numpy as np
from .compress import load_image_grayscale, save_image_from_array, compress, decompress



def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='cmd')
    enc = sub.add_parser('encode')
    enc.add_argument('infile')
    enc.add_argument('outfile')
    enc.add_argument('--levels', type=int, default=1)
    enc.add_argument('--qstep', type=float, default=10.0)
    enc.add_argument('--block-size', type=int, default=32)
    dec = sub.add_parser('decode')
    dec.add_argument('infile')
    dec.add_argument('outfile')
    args = p.parse_args()
    if args.cmd == 'encode':
        arr = load_image_grayscale(args.infile)
        container = compress(arr, levels=args.levels, qstep=args.qstep, block_size=args.block_size)
        with open(args.outfile, 'wb') as f:
            f.write(container)
        print('Wrote', args.outfile)
    elif args.cmd == 'decode':
        with open(args.infile, 'rb') as f:
            container = f.read()
        arr = decompress(container)
        save_image_from_array(arr, args.outfile)
        print('Wrote', args.outfile)


if __name__ == '__main__':
    main()
