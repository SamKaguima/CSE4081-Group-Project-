import struct
import numpy as np
from PIL import Image
from .dwt import dwt2, idwt2
from .quant import quantize, dequantize
from .rice import RiceCoder


def compress(img_array, levels=1, qstep=10.0, block_size=32):
    """Compress a 2D numpy grayscale image. Returns bytes containing a self-contained container.

    Container format (binary):
    - 4 bytes magic: b'HR01'
    - 1 byte version
    - 4 bytes h (uint32), 4 bytes w (uint32)
    - 1 byte levels
    - 4 bytes float qstep (packed as float)
    - 4 bytes block_size (uint32)
    - followed by payload: rice-encoded blocks (see RiceCoder)
    """
    # accept grayscale (2D) or color (H,W,3)
    if img_array.ndim == 2:
        h, w = img_array.shape
        channels = 1
        chans = [img_array]
    elif img_array.ndim == 3 and img_array.shape[2] == 3:
        h, w, _ = img_array.shape
        channels = 3
        # convert to YCbCr to better match perceptual importance (luma first)
        # Use simple conversion via PIL for correctness
        pil = Image.fromarray(img_array.astype('uint8'))
        ycbcr = pil.convert('YCbCr')
        chans = [np.array(ycbcr)[:, :, i] for i in range(3)]
    else:
        raise ValueError('img_array must be 2D grayscale or 3D RGB')

    assert h % (2 ** levels) == 0 and w % (2 ** levels) == 0, "Image dimensions must be divisible by 2^levels"

    coder = RiceCoder()
    # build container: header then per-channel payloads (each prefixed with uint32 bitlen payload)
    header = bytearray()
    header += b'HR01'  # magic
    header += bytes([1])  # version
    header += int(h).to_bytes(4, 'big')
    header += int(w).to_bytes(4, 'big')
    header += bytes([levels])
    header += bytes([channels])
    header += struct.pack('>f', float(qstep))
    header += int(block_size).to_bytes(4, 'big')

    payload_all = bytearray()
    for ch in chans:
        coefs = dwt2(ch, levels=levels)
        q = quantize(coefs, qstep, preserve_ll=True, levels=levels)
        flat = q.flatten().tolist()
        blocks = [flat[i:i + block_size] for i in range(0, len(flat), block_size)]
        payload, _ = coder.encode_blocks_to_bytes(blocks)
        # store payload length as uint32 then payload
        payload_all += len(payload).to_bytes(4, 'big')
        payload_all += payload

    return bytes(header) + bytes(payload_all)


def decompress(container_bytes):
    # parse header
    if len(container_bytes) < 23:
        raise ValueError('container too small')
    magic = container_bytes[0:4]
    if magic != b'HR01':
        raise ValueError('bad magic')
    version = container_bytes[4]
    h = int.from_bytes(container_bytes[5:9], 'big')
    w = int.from_bytes(container_bytes[9:13], 'big')
    levels = container_bytes[13]
    channels = container_bytes[14]
    qstep = struct.unpack('>f', container_bytes[15:19])[0]
    block_size = int.from_bytes(container_bytes[19:23], 'big')

    coder = RiceCoder()
    idx = 23
    chans = []
    for c in range(channels):
        if idx + 4 > len(container_bytes):
            raise ValueError('truncated container')
        plen = int.from_bytes(container_bytes[idx:idx+4], 'big')
        idx += 4
        if idx + plen > len(container_bytes):
            raise ValueError('truncated payload')
        payload = container_bytes[idx:idx+plen]
        idx += plen
        blocks = coder.decode_bytes_to_blocks(payload)
        flat = []
        for b in blocks:
            flat.extend(b)
        arr = np.array(flat, dtype=np.int32).reshape((h, w))
        f = dequantize(arr, qstep, preserve_ll=True, levels=levels)
        rec = idwt2(f, levels=levels)
        rec = np.clip(np.rint(rec), 0, 255).astype(np.uint8)
        chans.append(rec)

    if channels == 1:
        return chans[0]
    else:
        # channels are in YCbCr order; convert back to RGB
        ycbcr = np.stack(chans, axis=2)
        pil = Image.fromarray(ycbcr, mode='YCbCr')
        rgb = np.array(pil.convert('RGB'))
        return rgb


def load_image_grayscale(path):
    im = Image.open(path).convert('L')
    return np.array(im)


def save_image_from_array(arr, path):
    im = Image.fromarray(arr)
    im.save(path)
