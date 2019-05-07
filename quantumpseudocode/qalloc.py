from typing import List, Optional, Union, Tuple, Callable, TYPE_CHECKING, Iterable, Any

import quantumpseudocode as qp


def qmanaged(val: Union[None, int, 'qp.Qubit', 'qp.Qureg', 'qp.Quint'] = None, *, name: Optional[str] = None) -> 'qp.QallocManager':
    if val is None:
        q = qp.Qubit('qalloc' if name is None else name)
        return QallocManager(qp.RawQureg([q]), q)

    if isinstance(val, int):
        q = qp.NamedQureg('' if name is None else name, val)
        return QallocManager(q, q)

    if isinstance(val, qp.Qubit):
        assert name is None
        return QallocManager(qp.RawQureg([val]), val)

    if isinstance(val, qp.Qureg):
        assert name is None
        return QallocManager(val, val)

    if isinstance(val, qp.Quint):
        assert name is None
        return QallocManager(val.qureg, val)

    raise NotImplementedError()


def qmanaged_int(*, bits: int, name: str = ''):
    return qp.qmanaged(qp.Quint(qp.NamedQureg(name, bits)))


class QallocManager:
    def __init__(self, qureg: 'qp.Qureg', wrap: Any):
        self.qureg = qureg
        self.wrap = wrap

    def __enter__(self):
        if len(self.qureg):
            qp.emit(AllocQuregOperation(self.qureg))
        return self.wrap

    def __exit__(self, exc_type, exc_val, exc_tb):
        if len(self.qureg) and exc_type is None:
            qp.emit(ReleaseQuregOperation(self.qureg))


def qalloc(val: Union[None, int] = None,
           *,
           name: Optional[str] = None,
           x_basis: bool = False) -> 'Any':
    if val is None:
        result = qp.Qubit(name or '')
        reg = qp.RawQureg([result])
    elif isinstance(val, int):
        result = qp.NamedQureg(name or '', length=val)
        reg = result
    else:
        raise NotImplementedError()

    if len(reg):
        qp.emit(AllocQuregOperation(reg, x_basis))

    return result


def qfree(target: Union[qp.Qubit, qp.Qureg, qp.Quint],
          equivalent_expression: 'Union[None, bool, int, qp.RValue[Any]]' = None,
          dirty: bool = False):

    if equivalent_expression is not None:
        qp.rval(equivalent_expression).del_storage_location(
            target, qp.QubitIntersection.EMPTY)

    if isinstance(target, qp.Qubit):
        reg = qp.RawQureg([target])
    elif isinstance(target, qp.Qureg):
        reg = target
    elif isinstance(target, qp.Quint):
        reg = target.qureg
    else:
        raise NotImplementedError()
    if len(reg):
        qp.emit(qp.ReleaseQuregOperation(reg, dirty=dirty))


def qalloc_int(*,
               bits: int,
               name: Union[None, str, 'qp.UniqueHandle'] = None) -> 'Any':
    result = qp.Quint(qureg=qp.NamedQureg(length=bits, name=name or ''))
    if bits:
        qp.emit(AllocQuregOperation(result.qureg))
    return result


class AllocQuregOperation(qp.FlagOperation):
    def __init__(self,
                 qureg: 'qp.Qureg',
                 x_basis: bool = False):
        self.qureg = qureg
        self.x_basis = x_basis

    def inverse(self):
        return ReleaseQuregOperation(self.qureg, self.x_basis)

    def __str__(self):
        return 'ALLOC[{}, {}] {}'.format(
            len(self.qureg), 'X' if self.x_basis else 'Z', self.qureg)

    def __repr__(self):
        return 'qp.AllocQuregOperation({!r})'.format(self.qureg)

    def controlled_by(self, controls):
        raise ValueError("Can't control allocation.")


class ReleaseQuregOperation(qp.FlagOperation):
    def __init__(self,
                 qureg: 'qp.Qureg',
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
