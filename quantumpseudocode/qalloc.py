from typing import List, Optional, Union, Tuple, Callable, TYPE_CHECKING, Iterable, Any

import cirq

import quantumpseudocode as qp
from quantumpseudocode.ops import Operation


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

    if isinstance(val, qp.QuintMod):
        assert name is None
        return QallocManager(val.qureg, val)

    raise NotImplementedError('Unrecognized value to manage: {!r}'.format(val))


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


def alloc(bit_count: Union[None, int] = None,
          *,
          expr: Union[None, qp.RValue, int, bool] = None,
          name: Optional[str] = None,
          x_basis: bool = False) -> 'Any':
    """Allocates and initializes quantum data.

    Args:
        bit_count: The number of qubits to allocate.
        expr: An expression describing the value to initialize the allocated
            storage location to. Defaults to the location being zero'd.
        name: Debug information to associate with the allocated register.
        x_basis: When set, a plus state is allocated under the assumption that
            it is okay for a Toffoli simulator to allocate a random
            computational basis state.
    """
    if expr is not None:
        assert not x_basis
        assert bit_count is None
        expr = qp.rval(expr)
        loc = expr.make_storage_location(name)
        expr.init_storage_location(bit_count, qp.QubitIntersection.ALWAYS)
        return loc

    if bit_count is None:
        result = qp.Qubit(name or '')
        reg = qp.RawQureg([result])
    elif isinstance(bit_count, int):
        result = qp.NamedQureg(name or '', length=bit_count)
        reg = result
    else:
        raise NotImplementedError()

    if len(reg):
        qp.emit(AllocQuregOperation(reg, x_basis))

    return result


def free(loc: qp.LValue,
         *,
         expr: Union[None, bool, int, 'qp.RValue[Any]'] = None,
         dirty: bool = False) -> None:
    """Uncomputes and deallocates quantum data

    Args:
        loc: The location to deallocate.
        expr: An expression equivalent to the value at the location, expressed
            as a constant or an rvalue that can be used to uncompute it.
            Defaults to assuming the location is already zero'd.
        dirty: When not set, deallocate a non-zero'd qubit (or a qubit that
            failed to be uncomputed using the `expr` argument) causes an error.
            When set, no error is raised. The simulator may also disable this
            error checking globally.
    """

    if expr is not None:
        qp.rval(expr).del_storage_location(
            loc, qp.QubitIntersection.ALWAYS)

    if isinstance(loc, qp.Qubit):
        reg = qp.RawQureg([loc])
    elif isinstance(loc, qp.Qureg):
        reg = loc
    elif isinstance(loc, qp.Quint):
        reg = loc.qureg
    elif isinstance(loc, qp.QuintMod):
        reg = loc.qureg
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


def qalloc_int_mod(*,
                   modulus: int,
                   name: Union[None, str, 'qp.UniqueHandle'] = None) -> 'Any':
    assert modulus > 0
    bits = qp.ceil_lg2(modulus)
    result = qp.QuintMod(qureg=qp.NamedQureg(length=bits, name=name or ''),
                         modulus=modulus)
    if bits:
        qp.emit(AllocQuregOperation(result.qureg))
    return result


@cirq.value_equality
class AllocQuregOperation(Operation):
    def __init__(self,
                 qureg: 'qp.Qureg',
                 x_basis: bool = False):
        self.qureg = qureg
        self.x_basis = x_basis

    def validate_controls(self, controls: 'qp.QubitIntersection'):
        assert controls == qp.QubitIntersection.ALWAYS

    def mutate_state(self, sim_state: 'qp.ClassicalSimState', forward: bool):
        for name, length in _split_qureg(self.qureg):
            sim_state.alloc(name, length, x_basis=self.x_basis)

    def _value_equality_values_(self):
        return self.qureg, self.x_basis

    def __str__(self):
        return 'ALLOC[{}, {}] {}'.format(
            len(self.qureg), 'X' if self.x_basis else 'Z', self.qureg)

    def __repr__(self):
        return 'qp.AllocQuregOperation({!r})'.format(self.qureg)

    def controlled_by(self, controls):
        if controls.ALWAYS:
            return self
        raise ValueError("Can't control allocation.")


@cirq.value_equality
class ReleaseQuregOperation(Operation):
    def __init__(self,
                 qureg: 'qp.Qureg',
                 *,
                 dirty: bool = False):
        self.qureg = qureg
        self.dirty = dirty

    def mutate_state(self, sim_state: 'qp.ClassicalSimState', forward: bool):
        for name, _ in _split_qureg(self.qureg):
            sim_state.release(name, dirty=self.dirty)

    def validate_controls(self, controls: 'qp.QubitIntersection'):
        assert controls == qp.QubitIntersection.ALWAYS

    def _value_equality_values_(self):
        return self.qureg, self.dirty

    def __str__(self):
        return 'RELEASE {} [{}]'.format(
            self.qureg,
            ', dirty' if self.dirty else '')

    def controlled_by(self, controls):
        if controls.ALWAYS:
            return self
        raise ValueError("Can't control deallocation.")


def _split_qureg(qureg) -> List[Tuple[str, int]]:
    if isinstance(qureg, qp.NamedQureg):
        return [(qureg.name, len(qureg))]
    return [(q.name, 1) for q in qureg]
