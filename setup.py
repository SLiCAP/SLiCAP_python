# -*- coding: utf-8 -*-

import os, shutil
from os.path import expanduser
import setuptools
from setuptools.command.install import install

INSTALLVERSION="3.2.1"

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
        self._copy_files()
        install.run(self)

    def _set_version_config(self):
        """
        Sets the SLiCAP version variable to be set in the config file
        Can be appended to get the version variable from a website

        Returns
        -------
        None.

        """
        self._SLiCAP_version = INSTALLVERSION
        print("SLiCAP version:", self._SLiCAP_version)

    def _copy_files(self):
        """
        Sets the SLiCAP library variable to be set in the config file
        Includes copying of the default libraries

        Returns
        -------
        None.

        """
        home = expanduser("~")
        slicap_home = os.path.join(home, 'SLiCAP')
        try:
            if os.path.exists(slicap_home):
                shutil.rmtree(slicap_home)
            doc_loc = os.path.join(slicap_home, 'docs')
            shutil.copytree('files/', slicap_home)
            shutil.copytree('docs/_build/html/', doc_loc)
        except:
            print("ERROR: could not copy documentation, styles, and libraries.")


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
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.12',
)
