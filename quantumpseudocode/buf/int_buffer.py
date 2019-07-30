import random
from typing import Iterable, Sequence, Union


class Buffer:
    """An abstract bit array interface."""
    def __getitem__(self, item) -> int:
        raise NotImplementedError()

    def __setitem__(self, key, value):
        raise NotImplementedError()

    def __len__(self):
        raise NotImplementedError()


class RawIntBuffer(Buffer):
    """A bit array backed by the bits in a python int."""

    def __init__(self, val: int, length: int):
        assert 0 <= val < 1 << length
        self._val = val
        self._len = length

    def __getitem__(self, item):
        if isinstance(item, int):
            assert 0 <= item < self._len
            return (self._val >> item) & 1

        if isinstance(item, slice):
            assert item.step is None
            assert 0 <= item.start <= item.stop <= len(self)
            length = item.stop - item.start
            return (self._val >> item.start) & ~(-1 << length)

        return NotImplemented

    def __setitem__(self, key, value):
        if isinstance(key, int):
            assert value in [False, True, 0, 1]
            assert 0 <= key < self._len
            mask = 1 << key
            if value:
                self._val |= mask
            else:
                self._val &= ~mask
            return self[key]

        if isinstance(key, slice):
            assert key.step is None
            assert 0 <= key.start <= key.stop <= self._len
            n = key.stop - key.start
            assert 0 <= value < 1 << n
            mask = ~(-1 << n)
            written = value & mask
            self._val &= ~(mask << key.start)
            self._val |= written << key.start
            return written

        return NotImplemented

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return self._val == other._val and self._len == other._len
        return NotImplemented

    def __len__(self):
        return self._len

    def __str__(self):
        return ''.join(str(self[i]) for i in range(len(self))[::-1])

    def __repr__(self):
        return 'RawIntBuffer(0b{}, {!r})'.format(str(self), self._len)


class RawConcatBuffer(Buffer):
    """Exposes two buffers as one concatenated buffer."""

    def __init__(self, buf0: Buffer, buf1: Buffer):
        assert buf0 is not buf1
        self.buf0 = buf0
        self.buf1 = buf1

    @staticmethod
    def balanced_concat(parts: Sequence[Buffer]) -> 'Buffer':
        """Creates a buffer over many concatenated parts.

        Arranges RawConcatBuffer instances into a balanced search tree.
        """
        assert len(parts)
        if len(parts) == 1:
            return parts[0]
        middle = len(parts) >> 1
        return RawConcatBuffer(
            RawConcatBuffer.balanced_concat(parts[:middle]),
            RawConcatBuffer.balanced_concat(parts[middle:]))

    def __getitem__(self, item):
        n = len(self.buf0)

        if isinstance(item, int):
            if item < n:
                return self.buf0[item]
            return self.buf1[item - n]

        if isinstance(item, slice):
            assert item.step is None
            assert 0 <= item.start <= item.stop <= len(self)
            b0 = item.start >= n
            b1 = item.stop > n
            if not b0 and not b1:
                return self.buf0[item]
            if b0 and b1:
                return self.buf1[item.start - n:item.stop - n]
            cut = item.stop - n
            k = n - item.start
            return self.buf0[item.start:n] | (self.buf1[0:cut] << k)

        return NotImplemented

    def __setitem__(self, key, value):
        n = len(self.buf0)

        if isinstance(key, int):
            assert value in [False, True, 0, 1]
            assert 0 <= key < len(self)
            if key < n:
                self.buf0[key] = value
            else:
                self.buf1[key] = value

        if isinstance(key, slice):
            assert key.step is None
            assert 0 <= key.start <= key.stop <= len(self)
            b0 = key.start >= n
            b1 = key.stop > n
            if not b0 and not b1:
                self.buf0[key] = value
                return value
            if b0 and b1:
                self.buf1[key.start - n:key.stop - n] = value
                return value
            cut = key.stop - n
            k = n - key.start
            self.buf0[key.start:n] = value & ~(-1 << k)
            self.buf1[0:cut] = value >> k
            return value

        return NotImplemented

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return self.buf0 == other.buf0 and self.buf1 == other.buf1
        return NotImplemented

    def __len__(self):
        return len(self.buf0) + len(self.buf1)

    def __str__(self):
        return '{} {}'.format(self.buf0, self.buf1)

    def __repr__(self):
        return 'RawConcatBuffer({!r}, {!r})'.format(self.buf0, self.buf1)


class RawWindowBuffer(Buffer):
    """Exposes a subset of a buffer as a buffer."""

    def __new__(cls,
                buf: Buffer,
                start: int,
                stop: int):
        if isinstance(buf, RawWindowBuffer):
            result = RawWindowBuffer(
                buf._buf,
                buf._start + start,
                buf._start + stop)
            return result
        return super().__new__(cls)

    def __init__(self,
                 buf: Buffer,
                 start: int,
                 stop: int):
        if isinstance(buf, RawWindowBuffer):
            return
        self._buf = buf
        self._start = start
        self._stop = stop

    def __getitem__(self, item) -> int:
        if isinstance(item, int):
            index = range(self._start, self._stop)[item]
            return self._buf[index]

        if isinstance(item, slice):
            assert item.step is None
            span = range(self._start, self._stop)[item]
            assert span.start <= span.stop
            return self._buf[span.start:span.stop]

        return NotImplemented

    def __setitem__(self, key, value):
        if isinstance(key, int):
            index = range(self._start, self._stop)[key]
            self._buf[index] = value
            assert self._buf[index] == value
            return value

        if isinstance(key, slice):
            assert key.step is None
            assert 0 <= key.start <= key.stop <= len(self)
            n = key.stop - key.start
            assert 0 <= value < 1 << n
            span = range(self._start, self._stop)[key]
            self._buf[span.start:span.stop] = value
            return value

        return NotImplemented

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return self._buf == other._buf and self._start == other._start and self._stop == other._stop
        return NotImplemented

    def __len__(self):
        return self._stop - self._start

    def __str__(self):
        return '{}[{}:{}]'.format(self._buf, self._start, self._stop)

    def __repr__(self):
        return 'RawWindowBuffer({!r}, {!r}, {!r})'.format(self._buf, self._start, self._stop)


class IntBuf:
    """A fixed-width unsigned integer backed by a mutable bit buffer.

    Basically a complicated pointer into allocated memory.
    """

    def __init__(self, buffer: Buffer):
        self._buf = buffer
        assert isinstance(buffer, Buffer), 'Not a Buffer: {!r}'.format(buffer)

    def signed_int(self) -> int:
        """Return value as a signed int instead of an unsigned int."""
        if not len(self):
            return 0
        result = int(self)
        if self[len(self) - 1]:
            result -= 1 << len(self)
        return result

    @staticmethod
    def random(length: Union[int, range, Iterable[int]]) -> 'IntBuf':
        """Generates an IntBuf with random contents and a length sampled from the given allowed value(s)."""
        length = length if isinstance(length, int) else random.choice(length)
        return IntBuf.raw(length=length, val=random.randint(0, 2**length-1))

    def copy(self) -> 'IntBuf':
        return IntBuf.raw(length=len(self), val=int(self))

    def __len__(self):
        """The number of bits in this fixed-width integer."""
        return len(self._buf)

    def __int__(self):
        """The unsigned value of this fixed-width integer."""
        return self._buf[0:len(self._buf)]

    def padded(self, pad_len: int) -> 'IntBuf':
        """Returns a variant of this IntBuf with an extended width.

        The extra bits go at the end (the most significant side). The receiving
        IntBuf is not modified, but the head of the returned IntBuf is pointed
        at the same memory so modifying one's value will modify the other's.
        """
        if pad_len == 0:
            return self
        return IntBuf(RawConcatBuffer(self._buf, RawIntBuffer(0, pad_len)))

    @classmethod
    def zero(cls, length: int) -> 'IntBuf':
        """Returns a fresh zero'd IntBuf with the given length."""
        return IntBuf(RawIntBuffer(0, length))

    @classmethod
    def raw(cls, *, val: int, length: int) -> 'IntBuf':
        """Returns a fresh IntBuf with the given length and starting value."""
        return IntBuf(RawIntBuffer(val, length))

    @classmethod
    def concat(cls, bufs: Iterable['IntBuf']) -> 'IntBuf':
        """An IntBuf backed by the concatenated buffers of the given IntBufs."""
        frozen = list(bufs)
        if not frozen:
            return IntBuf.zero(0)
        seed = frozen[0]
        for buf in frozen[1:]:
            seed = seed.then(buf)
        return seed

    def then(self, other: 'IntBuf') -> 'IntBuf':
        """An IntBuf backed by the concatenated buffers of the given IntBufs."""
        return IntBuf(RawConcatBuffer(self._buf, other._buf))

    def __getitem__(self, item):
        """Get a bit or mutable window into this IntBuf."""

        if isinstance(item, int):
            index = range(0, len(self._buf))[item]
            return self._buf[index]

        if isinstance(item, slice):
            assert item.step is None
            span = range(0, len(self._buf))[item]
            assert span.start <= span.stop
            return IntBuf(RawWindowBuffer(self._buf, span.start, span.stop))

        return NotImplemented

    def __setitem__(self, key, value):
        """Overwrite a bit or window in this IntBuf."""

        if isinstance(key, int):
            index = range(0, len(self._buf))[key]
            self._buf[index] = value
            assert self._buf[index] == value
            return value

        if isinstance(key, slice):
            assert key.step is None
            span = range(0, len(self._buf))[key]
            written = int(value) & ~(-1 << (span.stop - span.start))
            self._buf[span.start:span.stop] = written
            assert self._buf[span.start:span.stop] == written
            return written

        return NotImplemented

    def __eq__(self, other):
        if isinstance(other, (int, IntBuf)):
            return int(self) == int(other)
        return NotImplemented

    def __str__(self):
        return ''.join(str(self[i]) for i in range(len(self)))

    def __bool__(self):
        return bool(int(self))

    def __iadd__(self, other):
        if isinstance(other, (int, IntBuf)):
            self[:] = int(self) + int(other)
            return self
        return NotImplemented

    def __imul__(self, other):
        if isinstance(other, (int, IntBuf)):
            self[:] = int(self) * int(other)
            return self
        return NotImplemented

    def __isub__(self, other):
        if isinstance(other, (int, IntBuf)):
            self[:] = int(self) - int(other)
            return self
        return NotImplemented

    def __ixor__(self, other):
        if isinstance(other, (int, IntBuf)):
            self[:] = int(self) ^ int(other)
            return self
        return NotImplemented

    def __iand__(self, other):
        if isinstance(other, (int, IntBuf)):
            self[:] = int(self) & int(other)
            return self
        return NotImplemented

    def __ior__(self, other):
        if isinstance(other, (int, IntBuf)):
            self[:] = int(self) | int(other)
            return self
        return NotImplemented

    def __repr__(self):
        return 'IntBuf({!r})'.format(self._buf)
