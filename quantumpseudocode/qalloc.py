from typing import List, Optional, Union, Tuple, Callable, TYPE_CHECKING, Iterable, Any

import quantumpseudocode


def qmanaged(val: Union[None, int, 'quantumpseudocode.Qubit', 'quantumpseudocode.Qureg', 'quantumpseudocode.Quint'] = None, *, name: Optional[str] = None) -> 'quantumpseudocode.QallocManager':
    if val is None:
        q = quantumpseudocode.Qubit('qalloc' if name is None else name)
        return QallocManager(quantumpseudocode.RawQureg([q]), q)

    if isinstance(val, int):
        q = quantumpseudocode.NamedQureg('' if name is None else name, val)
        return QallocManager(q, q)

    if isinstance(val, quantumpseudocode.Qubit):
        assert name is None
        return QallocManager(quantumpseudocode.RawQureg([val]), val)

    if isinstance(val, quantumpseudocode.Qureg):
        assert name is None
        return QallocManager(val, val)

    if isinstance(val, quantumpseudocode.Quint):
        assert name is None
        return QallocManager(val.qureg, val)

    raise NotImplementedError()


def qmanaged_int(*, bits: int, name: str = ''):
    return quantumpseudocode.qmanaged(quantumpseudocode.Quint(quantumpseudocode.NamedQureg(name, bits)))


class QallocManager:
    def __init__(self, qureg: 'quantumpseudocode.Qureg', wrap: Any):
        self.qureg = qureg
        self.wrap = wrap

    def __enter__(self):
        if len(self.qureg):
            quantumpseudocode.emit(AllocQuregOperation(self.qureg))
        return self.wrap

    def __exit__(self, exc_type, exc_val, exc_tb):
        if len(self.qureg) and exc_type is None:
            quantumpseudocode.emit(ReleaseQuregOperation(self.qureg))


def qalloc(val: Union[None, int] = None,
           *,
           name: Optional[str] = None,
           x_basis: bool = False) -> 'Any':
    if val is None:
        result = quantumpseudocode.Qubit(name or '')
        reg = quantumpseudocode.RawQureg([result])
    elif isinstance(val, int):
        result = quantumpseudocode.NamedQureg(name or '', length=val)
        reg = result
    else:
        raise NotImplementedError()

    if len(reg):
        quantumpseudocode.emit(AllocQuregOperation(reg, x_basis))

    return result


def qfree(target: Union[quantumpseudocode.Qubit, quantumpseudocode.Qureg, quantumpseudocode.Quint],
          equivalent_expression: 'Union[None, bool, int, quantumpseudocode.RValue[Any]]' = None,
          dirty: bool = False):

    if equivalent_expression is not None:
        quantumpseudocode.rval(equivalent_expression).del_storage_location(
            target, quantumpseudocode.QubitIntersection.EMPTY)

    if isinstance(target, quantumpseudocode.Qubit):
        reg = quantumpseudocode.RawQureg([target])
    elif isinstance(target, quantumpseudocode.Qureg):
        reg = target
    elif isinstance(target, quantumpseudocode.Quint):
        reg = target.qureg
    else:
        raise NotImplementedError()
    if len(reg):
        quantumpseudocode.emit(quantumpseudocode.ReleaseQuregOperation(reg, dirty=dirty))


def qalloc_int(*, bits: int, name: Optional[str] = None) -> 'Any':
    result = quantumpseudocode.Quint(qureg=quantumpseudocode.NamedQureg(length=bits, name=name or ''))
    if bits:
        quantumpseudocode.emit(AllocQuregOperation(result.qureg))
    return result


class AllocQuregOperation(quantumpseudocode.FlagOperation):
    def __init__(self,
                 qureg: 'quantumpseudocode.Qureg',
                 x_basis: bool = False):
        self.qureg = qureg
        self.x_basis = x_basis

    def inverse(self):
        return ReleaseQuregOperation(self.qureg, self.x_basis)

    def __str__(self):
        return 'ALLOC[{}, {}] {}'.format(
            len(self.qureg), 'X' if self.x_basis else 'Z', self.qureg)

    def __repr__(self):
        return 'quantumpseudocode.AllocQuregOperation({!r})'.format(self.qureg)

    def controlled_by(self, controls):
        raise ValueError("Can't control allocation.")


class ReleaseQuregOperation(quantumpseudocode.FlagOperation):
    def __init__(self,
                 qureg: 'quantumpseudocode.Qureg',
                 x_basis: bool = False,
                 dirty: bool = False):
        self.qureg = qureg
        self.x_basis = x_basis
        self.dirty = dirty

    def inverse(self):
        if self.dirty:
            raise NotImplementedError()
        return AllocQuregOperation(self.qureg, self.x_basis)

    def __str__(self):
        return 'RELEASE {} [{}{}]'.format(
            self.qureg,
            'X' if self.x_basis else 'Z',
            ', dirty' if self.dirty else '')

    def controlled_by(self, controls):
        raise ValueError("Can't control deallocation.")
