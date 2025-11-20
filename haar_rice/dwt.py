import numpy as np


def _dwt1d(arr):
    n = arr.shape[0]
    assert n % 2 == 0
    half = n // 2
    a = (arr[0::2] + arr[1::2]) / 2.0
    d = (arr[0::2] - arr[1::2]) / 2.0
    return np.concatenate([a, d])


def _idwt1d(coefs):
    n = coefs.shape[0]
    half = n // 2
    a = coefs[:half]
    d = coefs[half:]
    s0 = a + d
    s1 = a - d
    out = np.empty(n, dtype=coefs.dtype)
    out[0::2] = s0
    out[1::2] = s1
    return out


def dwt2(img, levels=1):
    """Perform multilevel 2D Haar DWT on a 2D numpy array.
    Returns a new array with the same shape containing wavelet coefficients.
    """
    arr = img.astype(np.float64).copy()
    h, w = arr.shape
    for lev in range(levels):
        sh = h >> lev
        sw = w >> lev
        # operate on top-left sh x sw
        # row-wise
        for i in range(sh):
            arr[i, :sw] = _dwt1d(arr[i, :sw])
        # column-wise
        for j in range(sw):
            arr[:sh, j] = _dwt1d(arr[:sh, j])
    return arr


def idwt2(coefs, levels=1):
    arr = coefs.astype(np.float64).copy()
    h, w = arr.shape
    for lev in range(levels - 1, -1, -1):
        sh = h >> lev
        sw = w >> lev
        # inverse column-wise
        for j in range(sw):
            arr[:sh, j] = _idwt1d(arr[:sh, j])
        # inverse row-wise
        for i in range(sh):
            arr[i, :sw] = _idwt1d(arr[i, :sw])
    return arr
