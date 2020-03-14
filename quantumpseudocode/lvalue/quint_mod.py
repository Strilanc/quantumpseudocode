from typing import Union

import cirq

import quantumpseudocode as qp


@cirq.value_equality
class QuintMod:
    def __init__(self, qureg: 'qp.Qureg', modulus: int):
        assert len(qureg) == qp.ceil_lg2(modulus)
        self.qureg = qureg
        self.modulus = modulus

    def _value_equality_values_(self):
        return self.qureg

    def __len__(self):
        return len(self.qureg)

    def __getitem__(self, item):
        if isinstance(item, int):
            return self.qureg[item]
        return qp.Quint(self.qureg[item])

    def init(self,
             value: Union[int, 'qp.RValue[int]'],
             controls: 'qp.QubitIntersection' = None):
        if controls is None:
            controls = qp.QubitIntersection.ALWAYS
            qp.rval(value).init_storage_location(self[:], controls)

    def clear(self,
              value: 'qp.RValue[int]',
              controls: 'qp.QubitIntersection' = None):
        if controls is None:
            controls = qp.QubitIntersection.ALWAYS
        value.clear_storage_location(self[:], controls)

    def __setitem__(self, key, value):
        if value != self[key]:
            raise NotImplementedError(
                "quint.__setitem__ is only for syntax like q[0] += 5. "
                "Don't know how to write {!r} into quint {!r}.".format(
                    value, key))
        return value

    def __iadd__(self, other):
        other, controls = qp.ControlledRValue.split(other)
        if controls == qp.QubitIntersection.NEVER:
            return self

        rval_other = qp.rval(other, default=other)
        rev = getattr(rval_other, '__riadd__', None)
        if rev is not None:
            result = rev(qp.ControlledLValue(controls, self))
            if result is not NotImplemented:
                return result

        if isinstance(other, int):
            qp.arithmetic_mod.do_plus_const_mod(
                lvalue=self[:],
                offset=other,
                modulus=self.modulus,
                control=controls)
            return self

        if isinstance(other, (qp.Quint, qp.RValue)):
            qp.arithmetic_mod.do_plus_mod(
                lvalue=self[:],
                offset=other,
                modulus=self.modulus,
                control=controls)
            return self

        return NotImplemented

    def __isub__(self, other):
        other, controls = qp.ControlledRValue.split(other)
        if controls == qp.QubitIntersection.NEVER:
            return self

        rval_other = qp.rval(other, default=other)
        rev = getattr(rval_other, '__risub__', None)
        if rev is not None:
            result = rev(qp.ControlledLValue(controls, self))
            if result is not NotImplemented:
                return result

        if isinstance(other, int):
            qp.arithmetic_mod.do_plus_const_mod(
                lvalue=self[:],
                offset=other,
                modulus=self.modulus,
                control=controls,
                forward=False)
            return self

        if isinstance(other, (qp.Quint, qp.RValue)):
            other, controls = qp.ControlledRValue.split(other)
            qp.arithmetic_mod.do_plus_mod(
                lvalue=self[:],
                offset=other,
                modulus=self.modulus,
                control=controls,
                forward=False)
            return self

        return NotImplemented

    def __str__(self):
        return '{} (mod {})'.format(self.qureg, self.modulus)

    def __repr__(self):
        return 'qp.QuintMod({!r}, {!r})'.format(self.qureg, self.modulus)
