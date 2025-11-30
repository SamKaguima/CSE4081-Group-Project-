"""Bit-level IO helpers: BitWriter and BitReader.

This module provides a simple MSB-first bit writer and reader used by the
Haar-Rice compressor. The API is intentionally small and focused on the
package's internal bitstream format:

- BitWriter: accumulate bits (MSB-first within values) and obtain the
    packed bytes via `get_bytes()`, which returns a `(bytes, bit_length)`
    tuple. `bit_length` is the total number of bits written; if the final
    byte is partial it is left-aligned (high-order bits populated) and
    padded with zeros in the low-order bits.

- BitReader: read bits from a `bytes` buffer given a `bit_length` (the
    total number of valid bits). Reading is MSB-first and `read_bit()` will
    raise `StopIteration` if the reader advances past `bit_length`.

The module is intentionally small and designed to be compatible with the
Rice coder and other bit-level helpers in this educational project.
"""

class BitWriter:
    def __init__(self):
        self._bytes = bytearray()
        self._acc = 0  # accumulator for bits (left-aligned)
        self._nbits = 0  # number of bits currently in acc
        self.bit_length = 0

    def write_bit(self, bit: int):
        self._acc = (self._acc << 1) | (1 if bit else 0)
        self._nbits += 1
        self.bit_length += 1
        if self._nbits == 8:
            self._bytes.append(self._acc & 0xFF)
            self._acc = 0
            self._nbits = 0

    def write_bits(self, value: int, count: int):
        # write count bits of value, MSB-first
        for bit_position in range(count - 1, -1, -1):
            bit = (value >> bit_position) & 1
            self.write_bit(bit)

    def write_unary(self, q: int):
        # q ones followed by a zero
        for _ in range(q):
            self.write_bit(1)
        self.write_bit(0)

    def get_bytes(self):
        # return (bytes, bit_length)
        out = bytes(self._bytes)
        if self._nbits > 0:
            # add the last partial byte (left-aligned bits)
            out = out + bytes([self._acc << (8 - self._nbits)])
        return out, self.bit_length


class BitReader:
    def __init__(self, data: bytes, bit_length: int):
        self._data = data
        self._bit_length = bit_length
        self._pos = 0  # bit position

    def read_bit(self):
        if self._pos >= self._bit_length:
            raise StopIteration
        byte_index = self._pos // 8
        bit_index = 7 - (self._pos % 8)  # MSB-first
        b = (self._data[byte_index] >> bit_index) & 1
        self._pos += 1
        return b

    def read_bits(self, count: int):
        v = 0
        for _ in range(count):
            v = (v << 1) | self.read_bit()
        return v

    def read_unary(self):
        q = 0
        while True:
            b = self.read_bit()
            if b == 1:
                q += 1
            else:
                break
        return q
