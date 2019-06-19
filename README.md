Quantum Pseudo Code
-------------------

When attempting to do arithmetic with quantum computing languages, one is struck
by the lack of basic built-in constructs such as addition.
For example, it is rare to be able to type `a += b` instead of
`CuccaroLittleEndianAdder(b, a)`.
This library's goal is to be like the former, instead of the latter.

For example, assuming `a`, `b`, and `c` are quantum values, the line

```python
a += table[b] & controlled_by(c)
```

will perform the following steps:

1. Allocate a temporary quantum register.
2. Initialize the temporary register using a controlled QROM lookup with address `b` and control `c`. 
3. Add the temporary register's value into `a`.
4. Uncompute the controlled QROM lookup.
5. Release the temporary register.

This works because the right hand expression `table[b] & controlled_by(c)`
produces a `quantumpseudocode.RValue[int]`, specifically a `ControlledRValue` containing a
`LookupRValue`.
Every RValue class knows how to initialize registers so that they store the
value of its expression, and also how to clear those registers.
So, when the `quantumpseudocode.Quint.__iadd__` method is invoked with an rvalue, it can
ask that rvalue to please initialize a temporary register so it can be added
into the target of the addition.

Note that quantumpseudocode contains the bare minimum to make implementing Shor's algorithm
work.
There are a lot of holes in the functionality.
Also it's not very fast.
But it does make it possible to include in a paper what at first glance looks
like pseudo-code, but have that code actually be executable.

For example:

```python
from quantumpseudocode import *

def make_coset_register(value: int, length: int, modulus: int) -> Quint:
    reg = qalloc_int(bits=length)
    reg ^= value % modulus

    # Add coherent multiple of modulus into reg.
    pad_bits = length - modulus.bit_length()
    for i in range(pad_bits):
        offset = modulus << i
        q = qalloc(x_basis=True)
        reg += offset & controlled_by(q)
        qfree(q, equivalent_expression=reg >= offset)

    return reg
```
