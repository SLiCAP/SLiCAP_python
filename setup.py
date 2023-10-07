# -*- coding: utf-8 -*-
"""
Created on Tue Sep 29 09:28:49 2020

@author: luc_e

Modified by Anton 1June 11 2023:
Updated to version 1.6.0
"""

import os, shutil
from os.path import expanduser
import setuptools
from setuptools.command.install import install
import platform
import subprocess
import re
from shutil import copy
if platform.system() == 'Windows':
    import win32api

INSTALLVERSION="2.0.1"

class InstallWrapper(install):
    """
    Provides a install wrapper for SLiCAP.
    Contains private functions that are to be run.
    """
    _LTSpice_cmd = "None"
    _SLiCAP_version = None
    _library_location = None
    _doc_location = None
    _install_location = None

    def run(self):
        """
        Runs the SLiCAP installation.

        Returns
        -------
        None.
        """
        self._set_ltspice_command()
        self._set_version_config()
        self._set_install_location()
        self._gen_config_file()
        install.run(self)

    def _set_ltspice_command(self):
        """
        Determining the LTSPICE command
        This contains two flows:
            Windows -   Searches the program files dir (e.g. C:\Program Files) for the LTSpice Command
            Linux   -   Searches the wine drive directory for the LTSpice command
        """
        self._LTSpice_cmd = " "
        print("Acquiring LTSpice Command")
        self._find_ltspice()
        if self._LTSpice_cmd != " ":
            print("Found the LTSpice directory: ", self._LTSpice_cmd)
        else:
            print("Could not find LTspice command, you need to edit the configuration file manually!")

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

    def _set_install_location(self):
        """
        Sets the SLiCAP library variable to be set in the config file
        Includes copying of the default libraries

        Returns
        -------
        None.

        """
        home = expanduser("~")
        slicap_home = os.path.join(home, 'SLiCAP')
        self.slicap_home = slicap_home
        try:
            if os.path.exists(slicap_home):
                shutil.rmtree(slicap_home)
            def_lib_loc = os.path.join(slicap_home, 'lib')
            def_doc_loc = os.path.join(slicap_home, 'docs')
            shutil.copytree('files/', slicap_home)
            self._library_location = def_lib_loc
            shutil.copytree('docs/_build/html/', def_doc_loc)
            self._doc_location = def_doc_loc
            self._install_location = slicap_home
        except:
            print("ERROR: could not set install location.")

    def _gen_config_file(self):
        """
        Generates the SLiCAP configiguration file: SLiCAPsetting.py

        Returns
        -------
        None.

        """
        print("Generating the configuration file")
        fileloc = os.path.join("SLiCAPtemplate.py")
        filetarg = os.path.join("SLiCAP", "SLiCAPsetting.py")
        if os.path.isfile(fileloc):
            print("Found template file: ", fileloc)
            fi = open(fileloc, 'r')
            txt = fi.read()
            fi.close()
            txt = txt.replace("$VERSION", self._SLiCAP_version)
            txt = txt.replace("$SYSINSTALL", ' ')
            txt = txt.replace("$USERPATH", self.slicap_home)
            txt = txt.replace("$LIBCOREPATH", self._library_location)
            txt = txt.replace("$LTSPICE", self._LTSpice_cmd)
            txt = txt.replace("$DOCPATH", self._doc_location)
            fi = open(filetarg, 'w')
            fi.write(txt)
            fi.close()
        print("Created config file: ", filetarg)

    def _find_ltspice(self):
        """
        Searches for the LTspice command under windows. If found it sets
        self._LTSpice_cmd.

        Returns
        -------
        None.
        """
        if platform.system() == 'Windows':
            drives = win32api.GetLogicalDriveStrings().split('\000')[:-1]
        else:
            # Assuming default 'wine' installation
            home = expanduser("~")
            drives = [os.path.join(home, '.wine', 'drive_c')]
        for drive in drives:
            drive = os.path.join(drive, 'Program Files')
            for root, dirs, files in os.walk(drive, topdown=True):
                for name in dirs:
                    if re.match('LT(S|s)pice*', name, flags=0):
                        path = os.path.join(root,name,'XVIIx64.exe')
                        print("LTSpice command set as:", path)
                        self._LTSpice_cmd = path
                        return

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
    url="https://github.com/Lenty/SLiCAP_python/",
    packages=setuptools.find_packages(),
    cmdclass={'install': InstallWrapper},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: Attribution-NonCommercial-NoDerivatives 4.0 International",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)
