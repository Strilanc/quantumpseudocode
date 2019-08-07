from distutils.core import setup
from Cython.Build import cythonize

setup(
    ext_modules = cythonize("quantumpseudocode/cython/bit_buf_view.pyx", language_level="3")
)
