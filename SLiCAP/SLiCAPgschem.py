#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SLiCAP scripts for generating a netlist from a gSchem or lepton-eda schematic 
with gnetlist spice-noqsi.
"""

import os
import platform
import subprocess
import SLiCAP.SLiCAPconfigure as ini

def _gNetlist(fileName, cirTitle):
    """
    Creates a netlist from a schematic file generated with lepton-eda or gschem.

    :param fileName: Name of the file, absolute, or relative to project path
    :type fileName: str

    :param cirTitle: Title of the schematic.
    :type cirTitle: str
    """
    if os.path.isfile(fileName):
        baseFileName = fileName.split('.')[0]
        outputfile   = baseFileName + '.net'
        cirFileName  = ini.cir_path + baseFileName.split('/')[-1] + '.cir'
        print("Creating netlist of {} using gNetlist.".format(fileName))
        generated = False
        if platform.system() != 'Windows':
            try:
                subprocess.run([ini.gnetlist, '-q', '-g', 'spice-noqsi', '-o', outputfile, fileName])
                generated = True
            except:
                print("Could not generate netlist using gNetlist.")
        else:
            outputfile = outputfile.replace('\\','\\\\')
            inputfile = fileName.replace('\\','\\\\')
            try:
                subprocess.run([ini.gnetlist, '-q', '-g', 'spice-noqsi', '-o', outputfile, inputfile])
                generated = True
            except:
                print("Could not generate netlist using gNetlist.")
        if generated:
            try:
                f = open(baseFileName + '.net', 'r')
                netlistLines = ['"' + cirTitle + '"\n'] + f.readlines()[1:] + ['.end\n']
                f.close()
                f = open(cirFileName, 'w')
                f.writelines(netlistLines)
                f.close()
            except:
                print("Error: could not open: '{0}'.".format(baseFileName + '.net'))
        if ini.lepton_eda != '':
            print("Creating drawing-size SVG and PDF images of {}.".format(fileName))
            pdfFile = ini.img_path + baseFileName.split('/')[-1] + '.pdf'
            svgFile = ini.img_path + baseFileName.split('/')[-1] + '.svg'
            subprocess.run([ini.lepton_eda, 'export', '-o', pdfFile, fileName], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
            subprocess.run([ini.lepton_eda, 'export', '-o', svgFile, fileName], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        else:
            print("\nWarning: Auto-update of schematic diagram image files, "
                  + "not supported with gSchem.\nPlease update the image file "
                  + "manually!\n")
    else:
        print("Error: could not open: '{}'.".format(fileName))
    return
