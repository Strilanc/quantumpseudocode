from typing import Union, ContextManager, Any, Optional

import cirq
from typing_extensions import Protocol

import quantumpseudocode as qp
from .lvalue import LValue
from quantumpseudocode.rvalue import RValue


@cirq.value_equality
class Quint(RValue[int], LValue[int]):
    class Borrowed(Protocol):
        # Union[int, 'qp.Quint', 'qp.RValue[int]']
        pass

    def __init__(self, qureg: 'qp.Qureg'):
        self.qureg = qureg

    def resolve(self, sim_state: 'qp.ClassicalSimState', allow_mutate: bool):
        buf = sim_state.quint_buf(self)
        return buf if allow_mutate else int(buf)

    def existing_storage_location(self) -> Any:
        return self

    def make_storage_location(self, name: Optional[str] = None):
        return qp.Quint(qp.NamedQureg(name, len(self)))

    def init_storage_location(self,
                              location: 'qp.Quint',
                              controls: 'qp.QubitIntersection'):
        location ^= self & qp.controlled_by(controls)

    def del_storage_location(self,
                             location: 'qp.Quint',
                             controls: 'qp.QubitIntersection'):
        with qp.measurement_based_uncomputation(location.qureg) as bits:
            for b, q in zip(bits, self.qureg):
                qp.phase_flip(b & q & controls)

    def _value_equality_values_(self):
        return self.qureg

    def hold_padded_to(self, min_len: int) -> ContextManager['qp.Quint']:
        return qp.pad(self, min_len=min_len)

    def __len__(self):
        return len(self.qureg)

    def __getitem__(self, item):
        if isinstance(item, int):
            return self.qureg[item]
        return Quint(self.qureg[item])

    def __rlshift__(self, other):
        if other == 1:
            return qp.UnaryRValue(self)
        return NotImplemented

    def init(self,
             value: 'qp.RValue[int]',
             controls: 'qp.QubitIntersection' = None):
        qp.emit(
            qp.LetRValueOperation(value, self).controlled_by(
                controls or qp.QubitIntersection.ALWAYS))

    def clear(self,
              value: 'qp.RValue[int]',
              controls: 'qp.QubitIntersection' = None):
        qp.emit(
            qp.DelRValueOperation(value, self).controlled_by(
                controls or qp.QubitIntersection.ALWAYS))

    def __setitem__(self, key, value):
        if value != self[key]:
            raise NotImplementedError(
                "quint.__setitem__ is only for syntax like q[0] ^= q[1]. "
                "Don't know how to write {!r} into quint {!r}.".format(
                    value, key))
        return value

    def __mul__(self, other):
        if isinstance(other, int):
            return qp.ScaledIntRValue(self, other)
        return NotImplemented

    def __rmul__(self, other):
        return self.__mul__(other)

    def __le__(self, other):
        return qp.IfLessThanRVal(qp.rval(self),
                                 qp.rval(other),
                                 qp.rval(True))

    def __lt__(self, other):
        return qp.IfLessThanRVal(qp.rval(self),
                                 qp.rval(other),
                                 qp.rval(False))

    def __ge__(self, other):
        return qp.IfLessThanRVal(qp.rval(other),
                                 qp.rval(self),
                                 qp.rval(True))

    def __gt__(self, other):
        return qp.IfLessThanRVal(qp.rval(other),
                                 qp.rval(self),
                                 qp.rval(False))

    def __ixor__(self, other):
        other, controls = qp.ControlledRValue.split(other)
        if controls == qp.QubitIntersection.NEVER:
            return self

        if isinstance(other, int):
            qp.emit(qp.XorEqualConst(lvalue=self, mask=other).controlled_by(controls))
            return self

        if isinstance(other, Quint):
            qp.emit(qp.XorEqual(lvalue=self, mask=other).controlled_by(controls))
            return self

        rev = getattr(other, '__rixor__', None)
        if rev is not None:
            return rev(qp.ControlledLValue(controls, self))

        return NotImplemented

    def __iadd__(self, other):
        other, controls = qp.ControlledRValue.split(other)
        if controls == qp.QubitIntersection.NEVER:
            return self

        other_rval = qp.rval(other, default=other)
        rev = getattr(other_rval, '__riadd__', None)
        if rev is not None:
            result = rev(qp.ControlledLValue(controls, self))
            if result is not NotImplemented:
                return result

        if isinstance(other, (qp.Quint, qp.RValue)):
            qp.arithmetic.do_addition(
                lvalue=self,
                offset=other,
                carry_in=False,
                control=controls)
            return self

        return NotImplemented

    def __imul__(self, other):
        rev = getattr(other, '__rimul__', None)
        if rev is not None:
            result = rev(self)
            if result is not NotImplemented:
                return result

        rval_other = qp.rval(other, None)
        rev = getattr(rval_other, '__rimul__', None)
        if rev is not None:
            result = rev(self)
            if result is not NotImplemented:
                return result

        return NotImplemented

    def __isub__(self, other):
        with qp.invert():
            return self.__iadd__(other)

    def __str__(self):
        return str(self.qureg)

    def __repr__(self):
        return 'qp.Quint({!r})'.format(self.qureg)
