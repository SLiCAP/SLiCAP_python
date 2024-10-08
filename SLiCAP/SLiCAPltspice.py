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
    if not os.path.isfile(fileName):
        print("Error: could not open: '%s'."%(fileName))
    else:
        print("Creating netlist of {} using LTspice.".format(fileName))
        if platform.system() == 'Windows':
            fileName = fileName.replace('\\','\\\\')
            subprocess.run([ini.ltspice, '-netlist', fileName])
        else:
            subprocess.run(['wine', ini.ltspice, '-wine', '-netlist', fileName], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.STDOUT)
        baseFileName = fileName.split('.')[0]
        cirFileName = baseFileName.split('/')[-1]
        #try:
        f = open(baseFileName + '.net', 'r')
        netlistLines = ['"' + cirTitle + '"\n'] + f.readlines()
        f.close()
        f = open(ini.cir_path + cirFileName + '.cir', 'w')
        f.writelines(netlistLines)
        f.close()
        print("\nWarning: Auto-update of schematic diagram image files, "
              + "not supported with LTspice.\nPlease update the image file"
              + " manually!\n")
        #except:
        #    print("Error: could not open: '%s'."%(baseFileName + '.net'))
    return

def runLTspice(fileName):
    """
    Runs LTspice netlist (.cir) file.

    :param fileName: Name of the circuit (.cir) file, absolute path, or 
                     relative the the project directory
    
    :type fileName: str

    :return: None
    :rtype: Nonetype
    """
    if not os.path.isfile(fileName):
        print("Error: could not open: '%s'."%(fileName))
        return
    else:
        fileNameParts = fileName.split('.')
        fileType = fileNameParts[-1].lower()
        if fileType == 'cir':
            if platform.system() == 'Windows':
                fileName = fileName.replace('\\','\\\\')
                subprocess.run([ini.ltspice, '-b', fileName])
            else:
                subprocess.run(['wine', ini.ltspice, '-b', '-wine', fileName], 
                               stdout=subprocess.DEVNULL, 
                               stderr=subprocess.STDOUT)
