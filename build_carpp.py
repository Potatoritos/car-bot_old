from glob import glob
from setuptools import setup
from pybind11.setup_helpers import Pybind11Extension

ext_modules = [
    Pybind11Extension(
        "carpp",
        sorted(glob("carpp/*.cpp"))
    ),
]

setup(
    name='carpp',
    ext_modules=ext_modules
)
