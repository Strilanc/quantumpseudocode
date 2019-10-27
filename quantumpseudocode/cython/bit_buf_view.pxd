from libc.stdint cimport uint64_t
cdef uint64_t unaligned_word_read(uint64_t* src, int off)
cdef uint64_t unaligned_partial_word_read(uint64_t* src, int off, int width)
cdef void unaligned_word_write(uint64_t* dst, int off, uint64_t val)
cdef void unaligned_partial_word_write(uint64_t* dst, int off, int width, uint64_t val)
cdef void unaligned_memcpy(uint64_t* dst, int dst_off, uint64_t* src, int src_off, int bits)
