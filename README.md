# SLiCAP: more than SYMBOLIC SPICE

## What it is
- SLiCAP is an acronym for: **S** ymbolic **Li** near **C** ircuit **A** nalysis **P** rogram
- SliCAP is a tool for **algorithm-based analog design automation**
- SLiCAP is intended for setting up and solving **design equations** of electronic circuits
- SLiCAP is a an **open source** application written in Python
- SLiCAP is part of the tool set for teaching [Structured Electronics Design](https://analog-electronics.tudelft.nl) at the Delft University of Technology

## Why you should use it
- SLiCAP facilitates analog design automation and stepwise, hierachically-structured, analog design 
- SLiCAP lets you relate circuit component and device geometry requirements to system performance requirements
- SLiCAP makes complex symbolic circuit analysis doable
- SLiCAP speeds up the circuit design process
- SLiCAP integrates documentation and design ("one-click" update of HTML or PDF design reports)
- SLiCAP facilitates design education and knowledge building

## Features
- Accepts SPICE-like netlists as input and provides netlist generation from, amongst others, Kicad and LTspice schematic files.
- Facilitates concurrent design and documentation
- Supports and facilitates structured analog design

## Capabilities
- Conversion of hierarchically structured SPICE netlist into a mixed symbolic/numeric matrix equation
- Symbolic and numeric noise analysis
- Symbolic and numeric noise integration over frequency
- Symbolic and numeric determination of transfer functions and polynomial coefficients of transfer functions
- Symbolic and numeric inverse Laplace Transform
- Symbolic and numeric determination of network solutions
- Symbolic and numeric pole-zero analysis (symbolic pole-zero analysis for low-order systems only)
- Symbolic and numeric Routh array
- Order estimation of feedback circuits (numeric only)
- Root-locus analysis with an arbitrarily selected circuit parameter as root locus variable
- Symbolic and numeric DC and DC variance analysis for determination of budgets for resistor tolerances, offset, temperature effects, matching and tracking
- Symbolic and numeric derivation and solution of design equations for bandwidh, frequency response, noise, dc variance, and temperature stability

## Installing SLiCAP from pypi

1. Enter: 

       pip install slicap

## Addidional software
- SLiCAP can generate netlists from schematic files from:
  - Kicad (all platforms, preferred!)
  - LTspice (MSWindows: install LTspice on the system drive, Linux and MacOS: use MSwindows version and wine)
  - gschem (MSWindows: install gschem and its netlister on the system drive, Linux and MacOS: use lepton-eda)
  - lepton-eda (Linux and MacOS, MSWindows: use gSchem for windows)
- Inkscape is used to:
  - convert the page size of SVG images of schematic files generates with Kicad, lepton-eda, or gSchem to the image size
  - convert the above svg images to pdf (for use in LaTeX).

Preferred for all platforms is to install or upgrade to the latest version of Kicad, and install Inkscape.

## First Run

To verify correct installation of SLiCAP run the example "myFirstRCnetwork.py" in the project folder. This project folder is found in the example folder in the SLiCAP home directory. 

On the first run:

- SLiCAP searches for installed applications:
  - Kicad,
  - LTspice
  - NGspice
  - gSchem (MSWindows only)
  - lepton-eda (Linux and MacOS)
- SLiCAP creates a SLiCAP.ini file in the SLiCAP home directory. This file contains initial setting and commands to start the above applications. It can be edited manually, and when deleted it will be recreated on the next run. Searching for applications on MSWindows may take a while!

On the first run of a project, SLiCAP creates a SLiCAP.ini file in the project folder, each time you run the project this file is updated. If you delete it it will be recreated on the next run.

## Project file locations
Do not place your project files in the **SLiCAP home directory**: /home/<yourUserName\>/SLiCAP/ (LINUX) or \users\<yourUserName\>\SLiCAP\ (MSWindows). 

This directory contains the libraries, the examples, and the documentation. 

**This directory will be deleted and recreated each time you install SLiCAP.**

## Documentation
By default, the documentation is placed in /home/<yourUserName\>/SLiCAP/docs/ (LINUX) or \users\<yourUserName\>\SLiCAP\docs\ (MSWindows). 

Execution of the SLiCAP command:

    >>> Help()
    
shows the HTML documentation in your default browser.

## Setting up SLiCAP from source code
1. Intall Python 3.12+ with the packages listed in requirements.txt (for MSwindows Anaconda installation is preferred)
2. Download or clone the SLiCAP archive from github
3. Extract it in some directory
4. Open a terminal (or an Anaconda terminal if you run python from Anaconda) in the directory with setup.py
5. Install requirements:

       python -m pip install -r requirements.txt

6. Make Documentation:

       cd ./doc
       make html
       cd ..

7. Lastly, Install: 

       python -m pip install .
   
   Don't forget the dot!

## Contributing
If you want to contribute to the development of SLiCAP, please [Email Us](mailto:anton@montagne.nl).

### Bugs
In case bugs are found, please report them to the 'Issues' page.
