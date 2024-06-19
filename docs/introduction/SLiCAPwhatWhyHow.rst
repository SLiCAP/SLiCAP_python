==============
What is SLiCAP
==============

- SLiCAP is an acronym for: **S** ymbolic **Li** near **C** ircuit **A** nalysis **P** rogram
- SliCAP is a tool for **algorithm-based analog design automation**
- SLiCAP is intended for setting up and solving **design equations** of electronic circuits
- SLiCAP is a an **open source** application written in Python and maxima CAS
- SLiCAP is part of the tool set for teaching 'Structured Electronic Design' at the Delft University of Technology

=========================
Why should you use SLiCAP
=========================

- SLiCAP facilitates analog design automation
- SLiCAP speeds up the circuit engineering process
- SLiCAP makes complex symbolic math doable
- SLiCAP integrates documentation and design
- SLiCAP facilitates design education and knowledge building

Features
--------

- Accepts SPICE-like netlists as input
- Concurrent design and documentation
- Supports and facilitates structured analog design

Capabilities
------------

- Conversion of hierarchically structured SPICE netlist into mixed symbolic/numeric matrix equation
- Symbolic and numeric noise analysis
- Symbolic and numeric noise integration over frequency
- Symbolic and numeric determination of transfer functions and polynomial coefficients of transfer functions
- Symbolic and numeric determination of the Routh array
- Symbolic and numeric inverse Laplace Transform
- Symbolic and numeric determination of network solutions
- Accurate numeric pole-zero analysis
- Root-locus analysis with a arbitrarily selected circuit parameters as root locus variable(s)
- Symbolic and numeric DC and DC variance analysis for determination of budgets for resistor tolerances and offset and bias quantities
- Symbolic and numeric derivation and solution of design equations for bandwidh, frequency response, noise performance, dc variance and temperature stability
- Decomposition of balanced networks into four sub networks:

  #. A network that models the differential-mode behavior
  #. A network that models the differential-mode to common-mode conversion
  #. A network that models the common-mode to differential-mode conversion
  #. A network that models the common-mode behavior

- Use built-in small signal models for semiconductor devices of which the small-signal parameters are functions of the device geometry and the operating point:
  
  #. Gummel-Poon model for BJTs
  #. EKV model for MOS devices
  #. Any user-defined model with user-defined geometry parameters

  This makes it possible to design the signal performance of an amplifier before designing the biasing of the amplifier. The impact of errors introduces by bias sources on the signal transfer can be investigated and specified by simply adding these imperfections to the signal path design.

Technology
----------

- Python, Maxima CAS, HTML, CSS, LaTeX, MathJax, Python, Jupyther Notebook

=================
How to use SLiCAP
=================

Way of working
--------------

Working with SLiCAP usually requires the following steps:

#. Initialize a SLiCAP project; this will

   #. Create the directory structure for your project
   #. Create a configuration file for your project 
   #. Create the main html index page for this project

#. Create a circuit netlist and check the circuit

   SLiCAP supports netlist generation with gSchem and LTspice
    
#. Modify, add or delete circuit parameter definitions

#. Define an instruction

   You can change all the aspects of the instruction. If the instruction data is complete and consistent (this will be checked by SLiCAP), it can be executed. Definition of an instruction usually involves the following steps:

   #. Define the symbolic or numerical calculation mode: SLiCAP uses symbolic calculation methods, even if the data is numeric. If the simulation type is set to *numeric*, parameter values will recursively be substituted into the expressions for the circuit element values.
    
   #. Define the gain type and the data type: SLiCAP can provide symbolic and numeric expressions for:

      - The Laplace Transform, the Inverse Laplace Transform, and the DC value of 

        - Nodal voltages or currents through voltage sources (or other elements that have been defined in current-controlled notation, such as inductors)
        
        - Transfer functions of the asymptotic-gain model:
            
          - the gain (source to detector transfer)    
          - the asymptotic-gain           
          - the loop gain           
          - the direct transfer           
          - the servo function

      - Poles and zeros of these transfer functions (symbolic only for limited order)

      - Spectral densities of noise sources and their contributions to source-referred noise and/ore detector referred noise

      - Variance of DC voltage and currents resulting from resistor tolerances, and variances of voltage and current sources
    
   #. Define the signal source, the detector and the loop gain reference variable according to the asymptotic-gain feedback model.

   #. Define the matrix base converstion type:

      SLiCAP can automatically convert the complete network equation (MNA equation) of balanced circuits into smaller matrix equations that model the:  

      - differential-mode  behavior
      - differential-mode to common-mode conversion
      - common-mode to differential-mode conversion
      - common-mode behavior
        
   #. Define the data type: 
        
      SLiCAP can provide many types of data for both symbolic and numeric circuit analysis:
    
      - Matrix equations for the circuit, with the matrices adapted to the gaintype       
      - Laplace transform of voltages, currents or transfer functions
      - Numerator or denominator of the above Laplace transform       
      - Time functions, unit impulse and unit step functions; calculated from the inverse Laplace transform        
      - Contributions to spectral densities of source-referred or detector-referred noise or integrated noise        
      - Poles, zeros and DC gain of a transfer function, with and without cancellation of coinciding poles and zeros        
      - DC voltage and current and their variance due to offset errors, bias errors, and resistor tolerances
        
   #. Use parameter stepping for the instruction and define the step parameters and concurrently step multiple parameters.

#. Execute the instruction
    
#. Work with the results
    
   - SLiCAP has predefined functions for plotting, displaying tables and generation of web pages with beautifully typeset expressions, tables, figures and files. 
   - SLiCAP has a lot of postprocessing functions available for finding budgets (show-stopper values or design limits) for all kinds of performance parameters of electronic circuits:

     - Budgeting of noise sources:

       Given the integrated RMS noise of limits for source or detector referred noise, you can find show-stopper values for contributions of noise sources.

     - Budgeting of offset errors, bias errors and resistor tolerances:

       Given the total source or detector referred dc error (variance), you can find show-stopper values for contributions of tolerances of resistors, offset voltages and currents and bias voltages and currents.

     - Budgeting of GB product of operational amplifiers or loop gain-poles product of transistor feedback amplifiers:

       Given the required bandwidth of an amplifier in an application, SLiCAP helps you to find design limits or show-stopper values for different contributers to bandwidth limitation.

   - There are many examples available for the design of the dynamic behavior and the noise behavior of amplifiers:
     
     - It will be clear that once you have the (symbolic) matrix equation of a circuit, you have sufficient knowledge of Structured Analog Design, SLiCAP can help you with setting up and solving design equations for almost any design problem and, ultimately, with the automation of design engineering.
     - While doing your design work with SLiCAP, you concurrently generate a collection of linked html pages that document your work and help you to discuss your work with colleagues and present it to others on any platform with a web browser.

