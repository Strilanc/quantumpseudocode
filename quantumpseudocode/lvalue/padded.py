from typing import Union

import quantumpseudocode


def pad(base: 'Union[quantumpseudocode.Qureg, quantumpseudocode.Quint]', *, min_len: int) -> 'quantumpseudocode.PaddedQureg':
    assert min_len >= 0
    if isinstance(base, quantumpseudocode.Quint):
        return PaddedQureg(base.qureg, min_len)
    else:
        return PaddedQureg(base, min_len)


def pad_all(*bases: 'Union[quantumpseudocode.Qureg, quantumpseudocode.Quint]',
            min_len: int) -> 'quantumpseudocode.MultiWith':
    assert min_len >= 0
    return quantumpseudocode.MultiWith(pad(b, min_len=min_len) for b in bases)


class PaddedQureg:
    def __init__(self, base: 'quantumpseudocode.Qureg', min_len: int):
        self.base = base
        self.padded = None
        self.min_len = min_len

    def __len__(self):
        return len(self.padded)

    def __getitem__(self, item):
        return self.padded[item]

    def __enter__(self) -> 'quantumpseudocode.Qureg':
        if len(self.base) >= self.min_len:
            return self.base

        assert self.padded is None
        sub_name = str(self.base) if isinstance(self.base, quantumpseudocode.NamedQureg) else ''
        q = quantumpseudocode.NamedQureg('{}_pad'.format(sub_name), self.min_len - len(self.base))
        quantumpseudocode.emit(quantumpseudocode.AllocQuregOperation(q))
        self.padded = q
        return quantumpseudocode.RawQureg(list(self.base) + list(q))

    def __exit__(self, exc_type, exc_val, exc_tb):
        if len(self.base) >= self.min_len:
            return

        if exc_type is None:
            assert self.padded is not None
            quantumpseudocode.emit(quantumpseudocode.ReleaseQuregOperation(self.padded))
            self.padded = None
