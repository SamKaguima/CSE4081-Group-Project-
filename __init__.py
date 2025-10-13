"""Haar-Rice compression package

This package contains a small implementation of a 2D Haar DWT,
uniform quantization, and an adaptive Rice coder for demonstration
and educational purposes.
"""
from .compress import compress, decompress
from .dwt import dwt2, idwt2
from .quant import quantize, dequantize
from .rice import RiceCoder

__all__ = ["compress", "decompress", "dwt2", "idwt2", "quantize", "dequantize", "RiceCoder"]
