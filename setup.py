# -*- coding: utf-8 -*-

import setuptools
from setuptools.command.install import install

INSTALLVERSION="3.3.0"

class InstallWrapper(install):
    """
    Provides a install wrapper for SLiCAP.
    Contains private functions that are to be run.
    """
    def run(self):
        """
        Runs the SLiCAP installation.

        Returns
        -------
        None.
        """
        self._set_version_config()
        install.run(self)

    def _set_version_config(self):
        """
        Sets and prints the SLiCAP version.
        
        Returns
        -------
        None.

        """
        self._SLiCAP_version = INSTALLVERSION
        print("SLiCAP version:", self._SLiCAP_version)
        
with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="SLiCAP_python",
    version=INSTALLVERSION,
    author="Anton Montagne",
    author_email="anton@montagne.nl",
    description="Symbolic Linear Circuit Analysis Program",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/SLiCAP/SLiCAP_python/",
    packages=setuptools.find_packages(),
    cmdclass={'install': InstallWrapper},
    license='MIT',
    include_package_data=True,
    python_requires='>=3.12',
    install_requires=[
    "docutils>=0.18",
    "numpy>=1.26",
    "sympy>=1.12",
    "scipy>=1.12",
    "ply>=3.11",
    "matplotlib>=3.8.0",
    "sphinx-rtd-theme>=1.2.0",
    "svgelements>=1.9.6",
    "cairosvg>=2.7.1",
    "IPython>=8.19",
    'windows_tools>=2.4; sys_platform == "win32"',
    'pywin32>306; sys_platform == "win32"',
    ],
)
