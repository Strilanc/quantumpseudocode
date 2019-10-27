from libc.string cimport memcpy, memset
from libc.stdint cimport uint64_t
from cpython.mem cimport PyMem_Malloc, PyMem_Free
import numpy as np
cimport numpy as np


cdef struct BitSpanPtr:
    # A pointer augmented with bit alignment and length information.
    uint64_t *loc
    int off
    int bits


cdef struct IndexOffset:
    int index
    int offset


cdef class BitView:
    """Exposes read/write access to possibly unaligned and non-contiguous bits."""

    cdef BitSpanPtr* spans
    cdef size_t num_spans
    cdef size_t num_bits

    def __cinit__(self, size_t num_spans):
        self.spans = <BitSpanPtr*> PyMem_Malloc(num_spans * sizeof(BitSpanPtr))
        self.num_spans = num_spans
        self.num_bits = 0
        if not self.spans:
            raise MemoryError("Failed to allocate BitView.spans.")

    def __dealloc__(self):
        PyMem_Free(self.spans)

    cpdef BitView concat(BitView self, BitView other):
        cdef BitView result = BitView(self.num_spans + other.num_spans)
        result.num_bits = self.num_bits + other.num_bits
        memcpy(result.spans, self.spans, sizeof(BitSpanPtr) * self.num_spans)
        memcpy(result.spans + self.num_spans, other.spans, sizeof(BitSpanPtr) * other.num_spans)
        return result

    cdef IndexOffset _bit_to_span_index(self, int index):
        cdef IndexOffset result
        assert 0 <= index < self.num_bits
        while self.spans[result.index].bits <= start:
            start -= self.spans[result.index].bits
            result.index += 1
        result.offset = start
        return result

    cdef void _read_bits_into(self, uint64_t *out):
        cdef BitSpanPtr s
        cdef int pos = 0
        for i in range(self.num_spans):
            s = self.spans[i]
            unaligned_memcpy(out + (pos >> 6), pos & 63, s.loc, s.off, s.bits)
            pos += s.bits

    cdef void _xor_bits_into(self, uint64_t *out):
        cdef BitSpanPtr s
        cdef int pos = 0
        for i in range(self.num_spans):
            s = self.spans[i]
            unaligned_memxor(out + (pos >> 6), pos & 63, s.loc, s.off, s.bits)
            pos += s.bits

    cdef void _write_bits_from(self, uint64_t *inp):
        cdef BitSpanPtr s
        cdef int pos = 0
        for i in range(self.num_spans):
            s = self.spans[i]
            unaligned_memcpy(s.loc, s.off, inp + (pos >> 6), pos & 63, s.bits)
            pos += s.bits

    cdef void _xor_bits_from(self, uint64_t *inp):
        cdef BitSpanPtr s
        cdef int pos = 0
        for i in range(self.num_spans):
            s = self.spans[i]
            unaligned_memxor(s.loc, s.off, inp + (pos >> 6), pos & 63, s.bits)
            pos += s.bits

    def __len__(self):
        return self.num_bits

    def __getitem__(self, index):
        cdef IndexOffset found
        cdef size_t start
        cdef size_t stop
        cdef BitView view

        if isinstance(index, int):
            assert 0 <= index < self.num_bits
            found = self._bit_to_span_index(index)
            found.offset += self.spans[found.index].off
            return (self.spans[found.index].loc[found.offset >> 6] >> (found.offset & 63)) & 1

        return NotImplemented

    def uint64s(self):
        cdef size_t words = (self.num_bits + 63) >> 6
        cdef np.ndarray[np.uint64_t, ndim=1, mode='c'] out = np.zeros(words, dtype=np.uint64)
        self._read_bits_into(<uint64_t*> out.data)
        return out

    def write_int(self, v):
        cdef size_t words = (self.num_bits + 63) >> 6
        cdef uint64_t* buf = <uint64_t*> PyMem_Malloc(words * sizeof(uint64_t))
        memset(buf, 0, words * sizeof(uint64_t))
        for i in range(words):
            buf[i] = (v >> (i * 64)) & 63
        self._write_bits_from(buf)
        PyMem_Free(buf)

    def write_bits(self, bits):
        cdef size_t words = (len(bits) + 63) >> 6
        cdef int i
        cdef uint64_t* buf = <uint64_t*> PyMem_Malloc(words * sizeof(uint64_t))
        memset(buf, 0, words * sizeof(uint64_t))
        for i in range(len(bits)):
            if bits[i]:
                buf[i >> 6] |= 1ULL << (i & 63)
        self._write_bits_from(buf)
        PyMem_Free(buf)

    def __ixor__(self, BitView other):
        if self.num_bits < other.num_bits:
            raise ValueError(
                "Can't xor a larger BitView into a smaller BitView.")
        cdef size_t words = (self.num_bits + 63) >> 6
        cdef uint64_t* buf = <uint64_t*> PyMem_Malloc(words * sizeof(uint64_t))
        memset(buf, 0, words * sizeof(uint64_t))
        other._read_bits_into(buf)
        self._xor_bits_from(buf)
        PyMem_Free(buf)
        return self

    def __int__(self):
        result = 0
        for word in self.uint64s():
            result <<= 64
            result |= int(word)
        return result

    def bits(self):
        cdef int k
        uint64s = self.uint64s()
        result = np.zeros(self.num_bits, dtype=np.bool)
        for k in range(self.num_bits):
            result[k] = (int(uint64s[k >> 6]) >> (k & 63)) & 1
        return result

    def __str__(self):
        return ''.join(['1' if b else '0' for b in self.bits()])


cdef class BitBuf:
    """A contiguous chunk of bits arranged into 64 bit words."""

    cdef uint64_t* data
    cdef size_t num_words

    def __cinit__(self, size_t words):
        self.data = <uint64_t*> PyMem_Malloc(words * sizeof(uint64_t))
        memset(self.data, 0, words * sizeof(uint64_t))
        self.num_words = words
        if not self.data:
            raise MemoryError("Failed to allocate BitBuf.data.")

    def __dealloc__(self):
        PyMem_Free(self.data)

    def __len__(self):
        """Number of bits."""
        return self.length << 6

    def __getitem__(self, index):
        """Get a bit or a view over bits."""
        cdef size_t start
        cdef size_t stop
        cdef BitView view

        if isinstance(index, int):
            start = index
            return (self.data[start >> 6] >> (start & 63)) & 1

        if isinstance(index, slice):
            assert index.step is None
            start = index.start or 0
            stop = index.stop or self.num_words << 6
            assert 0 <= start < stop <= self.num_words << 6
            view = BitView(1)
            view.num_bits = stop - start
            view.spans[0].loc = self.data + (start >> 6)
            view.spans[0].off = start & 63
            view.spans[0].bits = stop - start
            return view

        return NotImplemented


cdef uint64_t unaligned_word_read(uint64_t* src, int off):
    # Reads a 64 bit word from the given location, with a bit offset that may
    # spread it across two aligned words in memory.
    #
    # Args:
    #     src: The word-aligned location to offset from and read from.
    #     off: The bit misalignment, between 0 and 63.
    #
    # Returns:
    #     The bits, packed into a 64 bit unsigned integer.
    cdef uint64_t result = src[0] >> off
    if off:
        result |= src[1] << (64 - off)
    return result


cdef uint64_t unaligned_partial_word_read(uint64_t* src, int off, int width):
    # Reads up to 64 bits from the given location, with a bit offset that may
    # spread it across two aligned words in memory.
    #
    # Args:
    #     src: The word-aligned location to offset from and read from.
    #     off: The bit misalignment, between 0 and 63.
    #     width: The number of bits to read.
    #
    # Returns:
    #     The bits, packed into a 64 bit unsigned integer.
    cdef uint64_t result = src[0] >> off
    if 64 - off < width:
        result |= src[1] << (64 - off)
    if width != 64:
        result &= ~(-1ULL << width)
    return result


cdef void unaligned_word_write(uint64_t* dst, int off, uint64_t val):
    # Writes a 64 bit word to the given location, with a bit offset that may
    # spread it across two aligned words in memory.
    #
    # Args:
    #     dst: The word-aligned location to offset from and write to.
    #     off: The bit misalignment, between 0 and 63.
    #     val: The word to write.
    if off:
        dst[0] &= (1ULL << off) - 1
        dst[1] &= ~(1ULL << (64 - off))
        dst[0] |= val << off
        dst[1] |= val >> (64 - off)
    else:
        dst[0] = val


cdef void unaligned_partial_word_write(uint64_t* dst, int off, int width, uint64_t val):
    # Writes up to 64 bits to the given location, with a bit offset that may
    # spread it across two aligned words in memory.
    #
    # Args:
    #     dst: The word-aligned location to offset from and write to.
    #     off: The bit misalignment, between 0 and 63.
    #     val: The word to write.
    #     width: The number of bits to write.
    cdef int n1 = min(width, 64 - off)
    cdef int n2 = width - n1
    cdef uint64_t m
    if n2 > 0:
        dst[1] &= -1ULL << n2
        dst[1] |= val >> n1
    if n1 == 64:
        dst[0] = val
    else:
        m = ~(-1ULL << n1)
        dst[0] &= ~(m << off)
        dst[0] |= (val & m) << off


cdef void unaligned_word_xor(uint64_t* dst, int off, uint64_t val):
    # Xors a 64 bit word to the given location, with a bit offset that may
    # spread it across two aligned words in memory.
    #
    # Args:
    #     dst: The word-aligned location to offset from and xor into.
    #     off: The bit misalignment, between 0 and 63.
    #     val: The word to xor in.
    dst[0] ^= val << off
    if off:
        dst[1] ^= val >> (64 - off)


cdef void unaligned_partial_word_xor(uint64_t* dst, int off, int width, uint64_t val):
    # Xors up to 64 bits into the given location, with a bit offset that may
    # spread it across two aligned words in memory.
    #
    # Args:
    #     dst: The word-aligned location to offset from and xor into.
    #     off: The bit misalignment, between 0 and 63.
    #     width: The number of bits to write.
    #     val: The word to xor in.
    cdef int n1 = min(width, 64 - off)
    cdef int n2 = width - n1
    cdef uint64_t m
    if n2 > 0:
        dst[1] ^= val >> n1
    if n1 == 64:
        dst[0] ^= val
    else:
        m = ~(-1ULL << n1)
        dst[0] ^= (val & m) << off


cdef void unaligned_memcpy(uint64_t* dst, int dst_off, uint64_t* src, int src_off, int bits):
    # A variant of memcpy that can be scoped down to the bit level.
    #
    # Args:
    #     dst: Word aligned location of destination buffer.
    #     dst_off: Bit misalignment of destination buffer, between 0 and 63.
    #     src: Word aligned location of source buffer.
    #     src_off: Bit misalignment of source buffer, between 0 and 63.
    #     bits: Length of range to copy from src to dst.
    cdef int i
    cdef uint64_t v

    # Work word by word where possible.
    for i in range(0, bits - 63, 64):
        v = unaligned_word_read(src, src_off)
        unaligned_word_write(dst, dst_off, v)
        src += 1
        dst += 1

    # Non word sized copy must manually combine with existing bits.
    bits &= 63
    if bits:
        v = unaligned_partial_word_read(src, src_off, bits)
        unaligned_partial_word_write(dst, dst_off, bits, v)


cdef void unaligned_memxor(uint64_t* dst, int dst_off, uint64_t* src, int src_off, int bits):
    # Xors bits from one place into another place, scoped down to the bit level.
    #
    # Args:
    #     dst: Word aligned location of destination buffer.
    #     dst_off: Bit misalignment of destination buffer, between 0 and 63.
    #     src: Word aligned location of source buffer.
    #     src_off: Bit misalignment of source buffer, between 0 and 63.
    #     bits: Length of range to xor from src into dst.
    cdef int i
    cdef uint64_t v

    # Work word by word where possible.
    for i in range(0, bits - 63, 64):
        v = unaligned_word_read(src, src_off)
        unaligned_word_xor(dst, dst_off, v)
        src += 1
        dst += 1

    # Non word sized copy must manually combine with existing bits.
    bits &= 63
    if bits:
        v = unaligned_partial_word_read(src, src_off, bits)
        unaligned_partial_word_xor(dst, dst_off, bits, v)
