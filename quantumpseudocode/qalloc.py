from typing import Optional, Union, Any, overload

import cirq

import quantumpseudocode as qp


@overload
def qalloc(*,
           len: int,
           name: Optional[str] = None,
           x_basis: bool = False) -> 'qp.Quint':
    pass


@overload
def qalloc(*,
           modulus: int,
           name: Optional[str] = None,
           x_basis: bool = False) -> 'qp.QuintMod':
    pass


@overload
def qalloc(*,
           name: Optional[str] = None,
           x_basis: bool = False) -> 'qp.Qubit':
    pass


def qalloc(*,
           len: Optional[int] = None,
           modulus: Optional[int] = None,
           name: Optional[str] = None,
           x_basis: bool = False) -> 'Any':
    """Allocates new quantum objects.

    If no arguments are given, allocates a qubit.
    If the `len` argument is given, allocates a quint.
    If the `modulus` argument is given, allocates a modular quint.

    Args:
        len: Causes a quint to be allocated. Number of qubits in the quint register.
        modulus: Causes a modular quint, storing values modulo this modulus, to be allocated.
        name: Debug information to associate with the allocated object.
        x_basis: If set, the register is initialized into a uniform superposition instead of into the zero state.

    Returns:
        A qubit, quint, or modular quint.
    """
    if len is None and modulus is None:
        n = 1
        wrap = lambda e: e[0]
    elif len is not None and modulus is None:
        n = len
        wrap = qp.Quint
    elif len is None and modulus is not None:
        assert modulus > 0
        n = (modulus - 1).bit_length()
        wrap = lambda e: qp.QuintMod(e, modulus)
    else:
        raise ValueError(f'Incompatible argument combination.')

    qureg = qp.global_logger.do_allocate_qureg(AllocArgs(
        qureg_name=name or '',
        qureg_length=n,
        x_basis=x_basis))

    return wrap(qureg)


def qfree(target: Union[qp.Qubit, qp.Qureg, qp.Quint],
          equivalent_expression: 'Union[None, bool, int, qp.RValue[Any]]' = None,
          dirty: bool = False):
    """Deallocates quantum objects.

    Args:
        target: The quantum object to free.
        equivalent_expression: An entangled expression with the same computational basis value as the quantum object.
            Used to uncompute the quantum object before freeing it, to avoid revealing information.
        dirty: Indicates that the quantum object is not expected to be zero'd.
    """

    if equivalent_expression is not None:
        qp.rval(equivalent_expression).clear_storage_location(
            target, qp.QubitIntersection.ALWAYS)

    if isinstance(target, qp.Qubit):
        reg = qp.RawQureg([target])
    elif isinstance(target, qp.Qureg):
        reg = target
    elif isinstance(target, qp.Quint):
        reg = target.qureg
    elif isinstance(target, qp.QuintMod):
        reg = target.qureg
    else:
        raise NotImplementedError()
    if len(reg):
        qp.global_logger.do_release_qureg(qp.ReleaseQuregOperation(reg, dirty=dirty))


class AllocArgs:
    def __init__(self,
                 *,
                 qureg_length: int,
                 qureg_name: Union[None, str, 'qp.UniqueHandle'] = None,
                 x_basis: bool = False):
        assert qureg_name is None or isinstance(qureg_name, (str, qp.UniqueHandle))
        self.qureg_length = qureg_length
        self.qureg_name = qureg_name
        self.x_basis = x_basis


@cirq.value_equality
class ReleaseQuregOperation:
    def __init__(self,
                 qureg: 'qp.Qureg',
                 x_basis: bool = False,
                 dirty: bool = False):
        self.qureg = qureg
        self.x_basis = x_basis
        self.dirty = dirty

    def _value_equality_values_(self):
        return self.qureg, self.x_basis, self.dirty

    def __str__(self):
        return 'RELEASE {} [{}{}]'.format(
            self.qureg,
            'X' if self.x_basis else 'Z',
            ', dirty' if self.dirty else '')
