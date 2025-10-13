import numpy as np
from haar_rice.compress import compress, decompress


def test_roundtrip_small():
    # simple 8x8 gradient
    arr = np.arange(64, dtype=np.uint8).reshape((8,8))
    container = compress(arr, levels=1, qstep=5.0, block_size=16)
    rec = decompress(container)
    # allow some error due to quantization
    assert rec.shape == arr.shape
    diff = np.abs(rec.astype(int) - arr.astype(int))
    assert diff.mean() < 10
