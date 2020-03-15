from typing import Union, ContextManager

import quantumpseudocode as qp


class Quint:
    Borrowed = Union[int, 'qp.Quint', 'qp.RValue[int]']

    def __init__(self, qureg: 'qp.Qureg'):
        self.qureg = qureg

    def resolve(self, sim_state: 'qp.ClassicalSimState', allow_mutate: bool):
        buf = sim_state.quint_buf(self)
        return buf if allow_mutate else int(buf)

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
             value: Union[int, 'qp.RValue[int]'],
             controls: 'qp.QubitIntersection' = None):
        if controls is None:
            controls = qp.QubitIntersection.ALWAYS
        qp.rval(value).init_storage_location(self, controls)

    def clear(self,
              value: Union[int, 'qp.RValue[int]'],
              controls: 'qp.QubitIntersection' = None):
        if controls is None:
            controls = qp.QubitIntersection.ALWAYS
        qp.rval(value).clear_storage_location(self, controls)

    def __setitem__(self, key, value):
        if value.qureg != self[key].qureg:
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
        if isinstance(other, int):
            if other < 0:
                return qp.rval(False)
            if other == 0:
                return self == 0
        return qp.IfLessThanRVal(qp.rval(self),
                                 qp.rval(other),
                                 qp.rval(True))

    def __lt__(self, other):
        if isinstance(other, int):
            if other <= 0:
                return qp.rval(False)
        return qp.IfLessThanRVal(qp.rval(self),
                                 qp.rval(other),
                                 qp.rval(False))

    def __eq__(self, other) -> 'qp.RValue[bool]':
        if isinstance(other, int):
            if other < 0:
                return qp.rval(False)
            return qp.QuintEqConstRVal(self, other)
        return NotImplemented

    def __ne__(self, other) -> 'qp.RValue[bool]':
        if isinstance(other, int):
            if other < 0:
                return qp.rval(True)
            return qp.QuintEqConstRVal(self, other, invert=True)
        return NotImplemented

    def __ge__(self, other):
        if isinstance(other, int):
            if other <= 0:
                return qp.rval(True)
        return qp.IfLessThanRVal(qp.rval(other),
                                 qp.rval(self),
                                 qp.rval(True))

    def __gt__(self, other):
        if isinstance(other, int):
            if other < 0:
                return qp.rval(True)
            if other == 0:
                return self != 0
        return qp.IfLessThanRVal(qp.rval(other),
                                 qp.rval(self),
                                 qp.rval(False))

    def __ixor__(self, other):
        other, controls = qp.ControlledRValue.split(other)
        if controls == qp.QubitIntersection.NEVER:
            return self

        if isinstance(other, int):
            qp.arithmetic.do_xor_const(lvalue=self, mask=other, control=controls)
            return self

        if isinstance(other, Quint):
            qp.arithmetic.do_xor(lvalue=self, mask=other, control=controls)
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
        lvalue = self
        lvalue ^= -1
        lvalue += other
        lvalue ^= -1
        return lvalue

    def __str__(self):
        return str(self.qureg)

    def __repr__(self):
        return 'qp.Quint({!r})'.format(self.qureg)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        qp.qfree(self)
