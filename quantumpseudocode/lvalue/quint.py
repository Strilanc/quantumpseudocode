import cirq

import quantumpseudocode


@cirq.value_equality
class Quint:
    def __init__(self, qureg: 'quantumpseudocode.Qureg'):
        self.qureg = qureg

    def _value_equality_values_(self):
        return self.qureg

    def __len__(self):
        return len(self.qureg)

    def __getitem__(self, item):
        if isinstance(item, int):
            return self.qureg[item]
        return Quint(self.qureg[item])

    def __setitem__(self, key, value):
        if value != self[key]:
            raise NotImplementedError(
                "quint.__setitem__ is only for syntax like q[0] ^= q[1]. "
                "Don't know how to write {!r} into {!r}.".format(
                    value, key))

    def __mul__(self, other):
        if isinstance(other, int):
            return quantumpseudocode.ScaledIntRValue(self, other)
        return NotImplemented

    def __rmul__(self, other):
        return self.__mul__(other)

    def __le__(self, other):
        return quantumpseudocode.IfLessThanRVal(quantumpseudocode.rval(self),
                                    quantumpseudocode.rval(other),
                                    quantumpseudocode.rval(True))

    def __lt__(self, other):
        return quantumpseudocode.IfLessThanRVal(quantumpseudocode.rval(self),
                                    quantumpseudocode.rval(other),
                                    quantumpseudocode.rval(False))

    def __ge__(self, other):
        return quantumpseudocode.IfLessThanRVal(quantumpseudocode.rval(other),
                                    quantumpseudocode.rval(self),
                                    quantumpseudocode.rval(False))

    def __gt__(self, other):
        return quantumpseudocode.IfLessThanRVal(quantumpseudocode.rval(other),
                                    quantumpseudocode.rval(self),
                                    quantumpseudocode.rval(True))

    def __ixor__(self, other):
        if isinstance(other, int):
            quantumpseudocode.emit(quantumpseudocode.OP_XOR_C(self, other))
            return self

        if isinstance(other, Quint):
            quantumpseudocode.emit(quantumpseudocode.OP_XOR(self, other))
            return self

        rev = getattr(other, '__rixor__', None)
        if rev is not None:
            return rev(self)

        return NotImplemented

    def __iadd__(self, other):
        rev = getattr(other, '__riadd__', None)
        if rev is not None:
            return rev(self)

        # Constant addition.
        if isinstance(other, (int, quantumpseudocode.IntRValue)):
            known = other.val if isinstance(other, quantumpseudocode.IntRValue) else other
            if known == 0:
                return self
            k = quantumpseudocode.leading_zero_bit_count(known)
            quantumpseudocode.emit(quantumpseudocode.PlusEqualGate(lvalue=self[k:],
                                           offset=known >> k,
                                           carry_in=False))
            return self

        # Register addition.
        if isinstance(other, (Quint, quantumpseudocode.RValue)):
            quantumpseudocode.emit(quantumpseudocode.PlusEqualGate(lvalue=self,
                                           offset=other,
                                           carry_in=False))
            return self

        return NotImplemented

    def __isub__(self, other):
        with quantumpseudocode.invert():
            return self.__iadd__(other)

    def __str__(self):
        return str(self.qureg)

    def __repr__(self):
        return 'quantumpseudocode.Quint({!r})'.format(self.qureg)
