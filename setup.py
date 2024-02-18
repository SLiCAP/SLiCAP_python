# -*- coding: utf-8 -*-
"""
Created on Tue Sep 29 09:28:49 2020

@author: luc_e

Modified by Anton January 27 2024:
Updated to version 1.8.0
"""

import os, shutil
from os.path import expanduser
import setuptools
from setuptools.command.install import install
import platform
import subprocess
import re
if platform.system() == 'Windows':
    import win32api
    import windows_tools.installed_software as wi

INSTALLVERSION="2.0.1"

class InstallWrapper(install):
    """
    Provides a install wrapper for SLiCAP.
    Contains private functions that are to be run.
    """
    _ltspice_cmd      = 'None'
    _kicad_cmd        = 'None'
    _inkscape_cmd     = 'None'
    _gnetlist_cmd     = 'None'
    _ngspice_cmd      = 'None'
    _SLiCAP_version   = None
    _library_location = None
    _doc_location     = None
    _install_location = None

    def run(self):
        """
        Runs the SLiCAP installation.

        Returns
        -------
        None.
        """
        package_list = ['LTspice', 'Inkscape', 'KiCad', 'gEDA', 'NGspice']
        self._set_commands(package_list)
        self._set_version_config()
        self._set_install_location()
        self._gen_config_file()
        install.run(self)

    def _find_installed_windows_software(self, package_list):
        """
        Searches for installed packages from the package list

        Returns
        -------
        Dictionary with key-value pairs: key = package name, value = command
        """
        commands = {}
        search_list = []
        software_list = wi.get_installed_software()
        for dct in software_list:
            name = dct["name"]
            if len(name) > 1:
                name = name.split()[0]
                if name in package_list:
                    search_list.append(name)
        if len(search_list) > 0:
            print("\nSearching installed software, this can take some time!")
            y_n = input("\nDo you have NGspice installed? [y/n] >>> ").lower()[0]
            while y_n != 'y' and y_n != 'n':
                y_n = input("\nPlease enter 'y' for 'yes' or 'n' for 'no' >>> ").lower()[0]
            if y_n == 'y':
                search_list.append('NGspice')
            print('')
            for drive in win32api.GetLogicalDriveStrings().split('\000')[:-1]:
                for root,dirs,files in os.walk(drive):
                    for name in dirs:
                        for package in search_list:
                            if package not in commands.keys():
                                if package == 'LTspice':
                                    if re.match('LT(S|s)pice*', name, flags=0):
                                        if os.path.exists(os.path.join(root,name,'XVIIx64.exe')):
                                            print("LTSpice command set as:", os.path.join(root,name,'XVIIx64.exe'))
                                            commands[package] = os.path.join(root,name,'XVIIx64.exe')
                                        elif  os.path.exists(os.path.join(root,name,'LTspice.exe')):
                                            print("LTSpice command set as:", os.path.join(root,name,'LTspice.exe'))
                                            commands[package] = os.path.join(root,name,'LTspice.exe')
                                        elif  os.path.exists(os.path.join(root,name,'ltspice.exe')):
                                            print("LTSpice command set as:", os.path.join(root,name,'ltspice.exe'))
                                            commands[package] = os.path.join(root,name,'ltspice.exe')
                                if package == 'Inkscape':
                                    if re.match('Inkscape', name, flags=0):
                                        file_name = os.path.join(root, name,'bin','inkscape.exe')
                                        if os.path.exists(file_name):
                                            print("Inkscape command set as:", os.path.join(root,name,'inkscape.exe'))
                                            commands[package] = file_name
                                if package == 'KiCad':
                                    if re.match('KiCad', name, flags=0):
                                        version=os.listdir(os.path.join(root, name))[0]
                                        file_name = os.path.join(root, name, version, 'bin','kicad-cli.exe')
                                        if os.path.exists(file_name):
                                            print("KiCad command set as:", os.path.join(root,name,'kicad-cli.exe'))
                                            commands[package] = file_name
                                if package == 'gEDA':
                                    if re.match('gEDA', name, flags=0):
                                        file_name = os.path.join(root, name, 'gEDA', 'bin' ,'gnetlist.exe')
                                        if os.path.exists(file_name):
                                            print("gnetlist command set as:", os.path.join(root,name,'gnetlist.exe'))
                                            commands[package] = file_name
                                if package == 'NGspice':
                                    if re.match('Spice64', name, flags=0):
                                        file_name = os.path.join(root, name, 'bin' ,'ngspice.exe')
                                        if os.path.exists(file_name):
                                            print("NGspice command set as:", os.path.join(root,name,'ngspice.exe'))
                                            commands[package] = file_name
                            if len(list(commands.keys())) == len(search_list):
                                return commands
        return(commands)

    def _find_LTspice_wine(self):
        """
        Searches for LTspice under Linux or MacOS

        Returns
        -------
        LTspice command
        """
        home = expanduser("~")
        drives = [os.path.join(home, '.wine', 'drive_c')]
        for drive in drives:
            drive = os.path.join(drive, 'Program Files')
            for root, dirs, files in os.walk(drive, topdown=True):
                for name in dirs:
                    if re.match('LT(S|s)pice*', name, flags=0):
                        if os.path.exists(os.path.join(root,name,'XVIIx64.exe')):
                            cmd = os.path.join(root,name,'XVIIx64.exe')
                        elif  os.path.exists(os.path.join(root,name,'LTspice.exe')):
                            cmd = os.path.join(root,name,'LTspice.exe')
                        elif  os.path.exists(os.path.join(root,name,'ltspice.exe')):
                            cmd = os.path.join(root,name,'ltspice.exe')
                        return cmd
        return 'None'

    def _set_commands(self, package_list):
        """
        Sets the commands for external packages
        """
        pltfrm = platform.system()
        if pltfrm == 'Windows':
            commands = self._find_installed_windows_software(package_list)
            for package in package_list:
                if package in commands.keys():
                    if package == 'LTspice':
                        self._ltpice_cmd = commands[package]
                    elif package == 'Inkscape':
                        self._inkscape_cmd = commands[package]
                    elif package == 'KiCad':
                        self._kicad_cmd = commands[package]
                    elif package == 'gEDA':
                        self._gnetlist_cmd = commands[package]
                    elif package == 'NGspice':
                        self._gnetlist_cmd = commands[package]
        elif pltfrm == 'Linux':
            self._ltspice_cmd  =  self._find_LTspice_wine()
            self._inkscape_cmd = 'inkscape'
            self._kicad_cmd    = 'kicad-cli'
            self._gnetlist_cmd = 'gnetlist'
            self._ngspice_cmd  = 'ngspice'
        else:
            self._ltspice_cmd  =  self._find_LTspice_wine()
            self._inkscape_cmd = 'inkscape'
            self._kicad_cmd    = '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
            self._gnetlist_cmd = 'gnetlist'
            self._ngspice_cmd  = 'ngspice'

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
            txt = txt.replace("$LTSPICE", self._ltspice_cmd)
            txt = txt.replace("$NGSPICE", self._ngspice_cmd)
            txt = txt.replace("$KICAD", self._kicad_cmd)
            txt = txt.replace("$INKSCAPE", self._inkscape_cmd)
            txt = txt.replace("$DOCPATH", self._doc_location)
            fi = open(filetarg, 'w')
            fi.write(txt)
            fi.close()
        print("Created config file: ", filetarg)


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
        "License :: Attribution-NonCommercial-NoDerivatives 4.0 International",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)
