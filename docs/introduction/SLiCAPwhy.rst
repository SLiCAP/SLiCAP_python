=========================
Why should you use SLiCAP
=========================

.. image:: /img/colorCode.svg

- SLiCAP facilitates stepwise, hierachically-structured, analog circuit design 
- SLiCAP lets you relate circuit component and device geometry requirements to circuit performance requirements
- SLiCAP makes complex symbolic circuit analysis doable
- SLiCAP speeds up the circuit design process
- SLiCAP integrates documentation and design ("one-click" update of HTML or PDF design reports)
- SLiCAP facilitates design education and knowledge building

Features
========

- SLiCAP accepts SPICE-like netlists with unlimited hierarchy
- SLiCAP provides schematic symbols for Kicad, LTspice, gSchem, and Lepton-eda
- SLiCAP performs mixed numeric and symbolic circuit analysis with Python Sympy as underlying Computer Algebra System and Python Numpy for fast numeric computations
- SLiCAP has 16 different analysis types for designing the dynamic response, the frequency stability, the noise performance, the DC operating point variance and temperature stability, the PCB or chip area, and the power dissipation
- SLiCAP automatically converts balanced circuits into differential-mode and common-mode equivalent circuits
- SLiCAP automatically updates HTML and PDF design reports, with text, images, graphs, tables, equations, etc.
- SLiCAP has a minimized instruction set, only a few Python instructions provide useful analysis results:

.. code-block:: python

    import SLiCAP as sl          # Import SLiCAP modules in separate namespace 'sl'
    sl.initProject('myProject')  # Initialize SLiCAP, compile the libraries and 
                                 # create an HTML report
    # Convert a KiCAD schematic into a SLiCAP circuit object and place the image, 
    # together with circuit data on an HTML page:
    cir = sl.makeCircuit('~/circuits/myCircuit/myCircuit.kikad_sch', imgWidth = 800) 
    # Obtain a symbolic expression for the source to load transfer (Laplace Tansfer):
    laplace_transfer = sl.doLaplace(cir).laplace

Capabilities
============

- Conversion of hierarchically structured SPICE-like netlist into a mixed symbolic/numeric matrix equation
- Symbolic and numeric noise analysis
- Symbolic and numeric noise integration over frequency
- Symbolic and numeric determination of transfer functions and polynomial coefficients of transfer functions
- Symbolic and numeric Inverse Laplace Transform
- Symbolic and numeric determination of network solutions for DC, Laplace, and time-domain
- Symbolic and numeric pole-zero analysis
- Symbolic and numeric Routh array
- Order estimation of feedback circuits (numeric only)
- Root-locus analysis with an arbitrarily selected circuit parameter as root locus variable
- Symbolic and numeric DC and DC variance analysis for determination of budgets for resistor tolerances, offset, temperature effects, matching and tracking
- Symbolic and numeric derivation and solution of design equations for bandwidh, frequency response, noise, dc variance, and temperature stability
- Decomposition of balanced networks into four sub networks:

  #. A network that models the differential-mode behavior
  #. A network that models the differential-mode to common-mode conversion
  #. A network that models the common-mode to differential-mode conversion
  #. A network that models the common-mode behavior

- Built-in small signal semiconductor device models of which the small-signal parameters are writen as functions of the device geometry and the operating point.

  This facilitates the signal performance design of circuit and the definition of geometry and operating conditions.
  
  SLiCAP provides such models for diodes, BJTs, JFETs and MOSFETs:
  
  #. Gummel-Poon model for BJTs
  #. Shichman and Hodges JFET model
  #. EKV model for MOS devices
  #. Any user-defined model with user-defined equations for geometry and operating voltage/current

.. image:: /img/colorCode.svg

