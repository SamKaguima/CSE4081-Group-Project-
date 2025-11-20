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
        for i in range(count - 1, -1, -1):
            bit = (value >> i) & 1
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
