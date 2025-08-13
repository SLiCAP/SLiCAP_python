#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SLiCAP functions for interfacing with LTspice.
"""
import os
import platform
import subprocess
import SLiCAP.SLiCAPconfigure as ini

def _LTspiceNetlist(fileName, cirTitle):
    """
    Creates a netlist from a schematic file generated with LTspice 

    :param fileName: Name of the file, absolute, or relative to project path
    :type fileName: str

    :param cirTitle: Title of the schematic.
    :type cirTitle: str
    """
    if ini.ltspice == "":
        print("Please install LTspice, delete '~/SLiCAP.ini', and run this script again.")
    else:
        if not os.path.isfile(fileName):
            print("Error: could not open: '{}'.".format(fileName))
        else:
            print("Creating netlist of '{}' using LTspice.".format(fileName))
            try:
                if platform.system() == 'Windows':
                    fileName = fileName.replace('\\','\\\\')
                    subprocess.run([ini.ltspice, '-netlist', fileName])
                else:
                    subprocess.run(['wine', ini.ltspice, '-wine', '-netlist', fileName], 
                                   stdout=subprocess.DEVNULL, 
                                   stderr=subprocess.STDOUT)
            except FileNotFoundError:
                print("\nError: could not run LTspice using '{}'.".format(ini.ltspice))   
            baseFileName = fileName.split('.')[0]
            cirFileName = baseFileName.split('/')[-1]
            try:
                f = open(baseFileName + '.net', 'r')
                netlistLines = ['"' + cirTitle + '"\n'] + f.readlines()
                f.close()
                f = open(ini.cir_path + cirFileName + '.cir', 'w')
                f.writelines(netlistLines)
                f.close()
                print("\nWarning: Auto-update of schematic diagram image files, "
                      + "not supported with LTspice.\nPlease update the image file"
                      + " manually!\n")
            except FileNotFoundError:
                print("\nError: could not open: '{}'.\nUnable to create netlist with LTspice.".format(baseFileName + '.net'))
    return
