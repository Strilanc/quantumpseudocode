from typing import List, Optional, Union, Tuple, Callable, TYPE_CHECKING, Iterable, Any

import cirq

import quantumpseudocode as qp


def qalloc(val: Union[None, int] = None,
           *,
           name: Optional[str] = None,
           x_basis: bool = False) -> 'Any':
    assert val is None or isinstance(val, int)
    alloc_op = AllocArgs(qureg_name=name or '',
                         qureg_length=1 if val is None else val,
                         x_basis=x_basis)

    qureg = qp.global_logger.do_allocate_qureg(alloc_op)
    assert isinstance(qureg, qp.Qureg)
    if val is None:
        return qureg[0]
    return qureg


def qfree(target: Union[qp.Qubit, qp.Qureg, qp.Quint],
          equivalent_expression: 'Union[None, bool, int, qp.RValue[Any]]' = None,
          dirty: bool = False):

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


def qalloc_int(*,
               bits: int,
               name: Union[None, str, 'qp.UniqueHandle'] = None) -> 'Any':
    qureg = qp.global_logger.do_allocate_qureg(AllocArgs(qureg_name=name, qureg_length=bits))
    return qp.Quint(qureg=qureg)


def qalloc_int_mod(*,
                   modulus: int,
                   name: Union[None, str, 'qp.UniqueHandle'] = None) -> 'Any':
    assert modulus > 0
    bits = qp.ceil_lg2(modulus)
    qureg = qp.global_logger.do_allocate_qureg(qp.AllocArgs(qureg_length=bits, qureg_name=name))
    return qp.QuintMod(qureg=qureg, modulus=modulus)


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
