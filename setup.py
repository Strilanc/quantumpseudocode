from distutils.core import setup
from Cython.Build import cythonize
import numpy as np

setup(
    ext_modules = cythonize("quantumpseudocode/cython/bit_buf_view.pyx", language_level="3"),
    include_dirs=[np.get_include()]
)
