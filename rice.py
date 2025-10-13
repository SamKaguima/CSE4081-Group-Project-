from .bitstream import BitWriter, BitReader


class RiceCoder:
    def __init__(self, m_choices=(0, 1, 2, 3, 4, 5, 6, 7, 8)):
        # m is exponent so divisor = 2**m
        self.m_choices = tuple(m_choices)

    @staticmethod
    def _map_signed_to_unsigned(n: int) -> int:
        # map signed integers to non-negative using zig-zag like mapping
        return (-n) * 2 - 1 if n < 0 else n * 2

    @staticmethod
    def _map_unsigned_to_signed(u: int) -> int:
        return -((u + 1) // 2) if (u & 1) else (u // 2)

    def _estimate_bits_for_m(self, ints, m):
        # estimate bit length required to encode block with parameter m
        bits = 4  # 4-bit header for m
        for n in ints:
            u = self._map_signed_to_unsigned(n)
            q = u >> m
            bits += q + 1  # unary q ones + terminating zero
            bits += m  # remainder bits
        return bits

    def encode_block(self, ints):
        # choose best m from m_choices for this block
        best_m = None
        best_len = 10 ** 18
        for m in self.m_choices:
            l = self._estimate_bits_for_m(ints, m)
            if l < best_len:
                best_len = l
                best_m = m

        bw = BitWriter()
        # write header (4 bits)
        bw.write_bits(best_m, 4)
        # write values
        for n in ints:
            u = self._map_signed_to_unsigned(n)
            q = u >> best_m
            r = u & ((1 << best_m) - 1) if best_m > 0 else 0
            bw.write_unary(q)
            if best_m > 0:
                bw.write_bits(r, best_m)
        blk_bytes, bit_len = bw.get_bytes()
        return bit_len, blk_bytes

    def decode_block(self, blk_bytes: bytes, bit_len: int):
        br = BitReader(blk_bytes, bit_len)
        try:
            m = br.read_bits(4)
        except StopIteration:
            return []
        vals = []
        try:
            while True:
                q = br.read_unary()
                r = br.read_bits(m) if m > 0 else 0
                u = (q << m) | r
                vals.append(self._map_unsigned_to_signed(u))
        except StopIteration:
            pass
        return vals

    def encode_blocks_to_bytes(self, blocks):
        # blocks: list of lists of ints
        out = bytearray()
        for blk in blocks:
            bit_len, blk_bytes = self.encode_block(blk)
            # store bit length as uint32, then raw bytes
            out += bit_len.to_bytes(4, 'big')
            out += blk_bytes
        return bytes(out), 0

    def decode_bytes_to_blocks(self, b, pad=0):
        blocks = []
        i = 0
        n = len(b)
        while i + 4 <= n:
            bit_len = int.from_bytes(b[i:i+4], 'big')
            i += 4
            blen = (bit_len + 7) // 8
            if i + blen > n:
                break
            blk_bytes = b[i:i+blen]
            i += blen
            vals = self.decode_block(blk_bytes, bit_len)
            blocks.append(vals)
        return blocks
