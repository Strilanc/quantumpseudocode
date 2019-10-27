cimport quantumpseudocode.cython.bit_buf_view as bit_buf_view
from libc.stdint cimport uint64_t


def _view(x):
    if isinstance(x, int) and 0 <= x < 2**64:
         r = hex(x)[2:]
         return '0x' + '0' * (16 - len(r)) + r
    return repr(x)


def _assert_eq(actual, expected):
    if actual != expected:
        raise AssertionError(f'Not equal.\n'
                             f'  actual: {_view(actual)}\n'
                             f'expected: {_view(expected)}')


def test_unaligned_word_read():
    cdef uint64_t[6] data
    data[0] = 0x0123456789ABCDEFu
    data[1] = 0x8ACE13579BCF0246u
    data[2] = 0
    data[3] = 0xFFFFFFFFFFFFFFFFu
    data[4] = 0
    data[5] = 0xFFFFFFFFFFFFFFFFu
    _assert_eq(bit_buf_view.unaligned_word_read(data, 0), data[0])
    _assert_eq(bit_buf_view.unaligned_word_read(data + 1, 0), data[1])

    _assert_eq(bit_buf_view.unaligned_word_read(data, 4), 0x60123456789ABCDE)
    _assert_eq(bit_buf_view.unaligned_word_read(data, 8), 0x460123456789ABCD)
    _assert_eq(bit_buf_view.unaligned_word_read(data, 12), 0x2460123456789ABC)

    _assert_eq(bit_buf_view.unaligned_word_read(data + 4, 0), 0)
    _assert_eq(bit_buf_view.unaligned_word_read(data + 4, 1), 2**63)
    _assert_eq(bit_buf_view.unaligned_word_read(data + 3, 63), 1)

    _assert_eq(bit_buf_view.unaligned_word_read(data + 3, 0), 0xFFFFFFFFFFFFFFFF)
    _assert_eq(bit_buf_view.unaligned_word_read(data + 3, 1), 0x7FFFFFFFFFFFFFFF)
    _assert_eq(bit_buf_view.unaligned_word_read(data + 2, 63), 0xFFFFFFFFFFFFFFFE)

    _assert_eq(bit_buf_view.unaligned_word_read(data + 5, 0), 0xFFFFFFFFFFFFFFFF)


def test_unaligned_partial_word_read():
    cdef uint64_t[6] data
    data[0] = 0x0123456789ABCDEFu
    data[1] = 0x8ACE13579BCF0246u
    data[2] = 0
    data[3] = 0xFFFFFFFFFFFFFFFFu
    data[4] = 0
    data[5] = 0xFFFFFFFFFFFFFFFFu

    _assert_eq(bit_buf_view.unaligned_partial_word_read(data + 3, 0, 64), 0xFFFFFFFFFFFFFFFF)
    _assert_eq(bit_buf_view.unaligned_partial_word_read(data + 3, 0, 8), 0xFF)
    _assert_eq(bit_buf_view.unaligned_partial_word_read(data + 3, 56, 8), 0xFF)
    _assert_eq(bit_buf_view.unaligned_partial_word_read(data + 3, 57, 8), 0x7F)
    _assert_eq(bit_buf_view.unaligned_partial_word_read(data + 4, 57, 8), 0x80)


def test_unaligned_word_write():
    cdef uint64_t[6] data
    data[0] = 0
    data[1] = 0
    data[2] = 0
    data[3] = 0
    data[4] = 0
    data[5] = 0

    bit_buf_view.unaligned_word_write(data + 3, 0, 0xFFFFFFFFFFFFFFFF)
    _assert_eq(data[2], 0)
    _assert_eq(data[3], 0xFFFFFFFFFFFFFFFF)
    _assert_eq(data[4], 0)

    bit_buf_view.unaligned_word_write(data + 3, 0, 0x987654321ABC0DEF)
    _assert_eq(data[2], 0)
    _assert_eq(data[3], 0x987654321ABC0DEF)
    _assert_eq(data[4], 0)

    bit_buf_view.unaligned_word_write(data + 3, 0, 0)
    _assert_eq(data[2], 0)
    _assert_eq(data[3], 0)
    _assert_eq(data[4], 0)

    bit_buf_view.unaligned_word_write(data + 3, 1, 0xFFFFFFFFFFFFFFFF)
    _assert_eq(data[2], 0)
    _assert_eq(data[3], 0xFFFFFFFFFFFFFFFE)
    _assert_eq(data[4], 1)
    data[3] = 0
    data[4] = 0

    bit_buf_view.unaligned_word_write(data + 3, 63, 0xFFFFFFFFFFFFFFFF)
    _assert_eq(data[2], 0)
    _assert_eq(data[3], 2**63)
    _assert_eq(data[4], 0x7FFFFFFFFFFFFFFF)
    data[3] = 0
    data[4] = 0

    bit_buf_view.unaligned_word_write(data + 3, 32, 0x987654321ABC0DEF)
    _assert_eq(data[2], 0)
    _assert_eq(data[3], 0x1ABC0DEF00000000)
    _assert_eq(data[4], 0x98765432)
    data[3] = 0
    data[4] = 0

    bit_buf_view.unaligned_word_write(data + 5, 0, 0xFFFFFFFFFFFFFFFF)
    _assert_eq(data[4], 0)
    _assert_eq(data[5], 0xFFFFFFFFFFFFFFFF)

    data[4] = 0xFFFFFFFFFFFFFFFF
    data[5] = 0xFFFFFFFFFFFFFFFF
    bit_buf_view.unaligned_word_write(data + 5, 0, 0)
    _assert_eq(data[4], 0xFFFFFFFFFFFFFFFF)
    _assert_eq(data[5], 0)


def test_unaligned_partial_word_write():
    cdef uint64_t[6] data
    data[0] = 0
    data[1] = 0
    data[2] = 0
    data[3] = 0
    data[4] = 0
    data[5] = 0

    bit_buf_view.unaligned_partial_word_write(data + 2, 0, 64, 0xF123456789ABCDEF)
    _assert_eq(data[1], 0)
    _assert_eq(data[2], 0xF123456789ABCDEF)
    _assert_eq(data[3], 0)

    data[1] = 0
    data[2] = 0
    data[3] = 0
    bit_buf_view.unaligned_partial_word_write(data + 2, 32, 64, 0xF123456789ABCDEF)
    _assert_eq(data[1], 0)
    _assert_eq(data[2], 0x89ABCDEF00000000)
    _assert_eq(data[3], 0xF1234567)

    data[1] = 0xFFFFFFFFFFFFFFFF
    data[2] = 0xFFFFFFFFFFFFFFFF
    data[3] = 0xFFFFFFFFFFFFFFFF
    bit_buf_view.unaligned_partial_word_write(data + 2, 32, 64, 0xF123456789ABCDEF)
    _assert_eq(data[1], 0xFFFFFFFFFFFFFFFF)
    _assert_eq(data[2], 0x89ABCDEFFFFFFFFF)
    _assert_eq(data[3], 0xFFFFFFFFF1234567)

    data[1] = 0xFFFFFFFFFFFFFFFF
    data[2] = 0xFFFFFFFFFFFFFFFF
    data[3] = 0xFFFFFFFFFFFFFFFF
    bit_buf_view.unaligned_partial_word_write(data + 2, 32, 48, 0x456789ABCDEF)
    _assert_eq(data[1], 0xFFFFFFFFFFFFFFFF)
    _assert_eq(data[2], 0x89ABCDEFFFFFFFFF)
    _assert_eq(data[3], 0xFFFFFFFFFFFF4567)

    data[1] = 0
    data[2] = 0
    data[3] = 0
    bit_buf_view.unaligned_partial_word_write(data + 2, 32, 48, 0x456789ABCDEF)
    _assert_eq(data[1], 0)
    _assert_eq(data[2], 0x89ABCDEF00000000)
    _assert_eq(data[3], 0x4567)

    data[1] = 0
    data[2] = 0
    data[3] = 0
    bit_buf_view.unaligned_partial_word_write(data + 2, 4, 8, 0xFF)
    _assert_eq(data[1], 0)
    _assert_eq(data[2], 0xFF0)
    _assert_eq(data[3], 0)

    data[1] = 0xFFFFFFFFFFFFFFFF
    data[2] = 0xFFFFFFFFFFFFFFFF
    data[3] = 0xFFFFFFFFFFFFFFFF
    bit_buf_view.unaligned_partial_word_write(data + 2, 4, 8, 0)
    _assert_eq(data[1], 0xFFFFFFFFFFFFFFFF)
    _assert_eq(data[2], 0xFFFFFFFFFFFFF00F)
    _assert_eq(data[3], 0xFFFFFFFFFFFFFFFF)

    data[1] = 0xFFFFFFFFFFFFFFFF
    data[2] = 0xFFFFFFFFFFFFFFFF
    data[3] = 0xFFFFFFFFFFFFFFFF
    bit_buf_view.unaligned_partial_word_write(data + 2, 60, 8, 0)
    _assert_eq(data[1], 0xFFFFFFFFFFFFFFFF)
    _assert_eq(data[2], 0x0FFFFFFFFFFFFFFF)
    _assert_eq(data[3], 0xFFFFFFFFFFFFFFF0)

    data[1] = 0
    data[2] = 0
    data[3] = 0
    bit_buf_view.unaligned_partial_word_write(data + 2, 60, 8, 0xFF)
    _assert_eq(data[1], 0)
    _assert_eq(data[2], 0xF000000000000000)
    _assert_eq(data[3], 0xF)


def test_unaligned_memcpy():
    cdef uint64_t[20] data
    cdef int i
    for i in range(20):
        data[i] = 0

    data[0] = 0xFFFFFFFFFFFFFFFF
    bit_buf_view.unaligned_memcpy(data + 10, 0, data, 0, 64)
    _assert_eq(data[0], 0xFFFFFFFFFFFFFFFF)
    _assert_eq(data[9], 0)
    _assert_eq(data[10], 0xFFFFFFFFFFFFFFFF)
    _assert_eq(data[11], 0)

    data[0] = 0x01234567FFFFFFFF
    data[1] = 0xFFFFFFFF76543210
    data[9] = 0
    data[10] = 0
    data[11] = 0
    bit_buf_view.unaligned_memcpy(data + 10, 0, data, 32, 64)
    _assert_eq(data[9], 0)
    _assert_eq(data[10], 0x7654321001234567)
    _assert_eq(data[11], 0)

    data[0] = 0x0123456789ABCDEF
    data[1] = 0
    data[9] = 0
    data[10] = 0
    data[11] = 0
    bit_buf_view.unaligned_memcpy(data + 10, 32, data, 0, 64)
    _assert_eq(data[9], 0)
    _assert_eq(data[10], 0x89ABCDEF00000000)
    _assert_eq(data[11], 0x01234567)

    data[0] = 0x1111111122222222
    data[1] = 0x3333333344444444
    data[2] = 0x5555555566666666
    data[3] = 0x7777777788888888
    data[4] = 0x99999999AAAAAAAA
    data[5] = 0xBBBBBBBBCCCCCCCC
    data[9] = 0
    data[10] = 0
    data[11] = 0
    bit_buf_view.unaligned_memcpy(data + 10, 16, data, 8, 64 * 5 + 4)
    _assert_eq(data[9], 0)
    _assert_eq(data[10], 0x1111112222220000)
    _assert_eq(data[11], 0x3333334444444411)
    _assert_eq(data[12], 0x5555556666666633)
    _assert_eq(data[13], 0x7777778888888855)
    _assert_eq(data[14], 0x999999AAAAAAAA77)
    _assert_eq(data[15], 0x00000000000CCC99)
    _assert_eq(data[16], 0)
