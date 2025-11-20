import numpy as np


def quantize(coefs, step, preserve_ll=True, levels=1):
    """Uniform scalar quantization. Returns integer quantized coefficients.

    coefs: 2D float array from dwt2
    step: quantization step (positive float)
    preserve_ll: if True, do not quantize the final LL band
    levels: number of decomposition levels used
    """
    q = np.rint(coefs / step).astype(np.int32)
    if preserve_ll:
        # zero-out quantization for LL at final level by restoring original (rounded) values
        h, w = coefs.shape
        ll_h = h >> levels
        ll_w = w >> levels
        q[:ll_h, :ll_w] = np.rint(coefs[:ll_h, :ll_w]).astype(np.int32)
    return q


def dequantize(qcoefs, step, preserve_ll=True, levels=1):
    f = qcoefs.astype(np.float64) * step
    if preserve_ll:
        h, w = qcoefs.shape
        ll_h = h >> levels
        ll_w = w >> levels
        f[:ll_h, :ll_w] = qcoefs[:ll_h, :ll_w].astype(np.float64)  # assume stored as original ints
    return f
