================
Perform analysis
================
    
.. image:: /img/colorCode.svg

SLiCAP has a number of predefined analysis types. However, since it built upon the powerful sympy CAS (Computer Algebra System), the user can easily extend SLiCAP's capabilities and add other analysis types.

General Instruction format
==========================

The general instruction format is:

.. code-block:: python

    result = do<Instruction>(cir, transfer='gain', source='circuit', detector='circuit', 
                             lgref='circuit', convtype=None, pardefs=None, numeric=False, 
                             stepdict=None)

where <Instruction> describes the analysis to be performed. 

The return value of all instructions is an `allResults <../reference/SLiCAPprotos.html#SLiCAP.SLiCAPprotos.allResults)>`__ object. Execution of the instruction will set some attributes of this object. Detailed information for each instruction is given in de `Reference section <../reference/SLiCAPshell.html>`__

The funstion arguments are:

#. **cir**: `circuit <../reference/SLiCAPprotos.html#SLiCAP.SLiCAPprotos.circuit>`__ object use for the instruction
#. **transfer**: None, 'gain', 'asymptotic', 'loopgain', 'servo', or 'direct'; defaults to 'gain'

   A transfer type is required for transfer related analysis types
   
   - None: no transfer type is specified; SLiCAP will calculate the detector voltage or curremt or perform analysis that do not require a source specification
   - 'gain': source to detector transfer
   - 'asymptotic': Gain of a circuit is which the loop gain reference is replaced with a nullor (the 'asymptotic-gain')
   - 'direct': Gain of a circuit in which the value of the loop gain reference is set to zero (the 'direct transfer')
   - 'loopgain': Gain enclosed in the loop involving the loop gain reference (the 'loop gain')
   - 'servo': :math:`\frac{-L}{1-L}`, where :math:`L` is the loop gain as defined above (the 'servo function')
   
#. **source**: None,'circuit', <refDes>, defaults to : 'circuit'

   - None: No source required or desired
   - 'circuit': SLiCAP uses the source specification from the netlist
   - <refDes>: Name of an independent voltage or current source that must be used as signal source
   
   Obtain list of independent sources in your circuit:
   
   .. code-block:: python
   
      import SLiCAP as sl
      sl.initProject("my Project")
      cir = sl.makeCircuit(<myCircuit>)
      # Obtain the list of independent sources in <myCircuit>
      print(cir.indepVars)
   
#. **detector**: None,'circuit', <refDes>, defaults to : 'circuit'

   - None: No detector required or desired
   - 'circuit': SLiCAP uses the detector specification from the netlist
   - <refDes>: Name of an independent variable (nodal voltage or branch current through a current-controlled element) that must be used as signal detector
   
   Obtain list with names of dependent variables in your circuit:
   
   .. code-block:: python
   
      import SLiCAP as sl
      sl.initProject("my Project")
      cir = sl.makeCircuit(<myCircuit>)
      # Obtain the list names of dependent variables in <myCircuit>
      print(cir.depVars())

#. **lgref**: None,'circuit', <refDes>, defaults to : 'circuit'

   - None: No loop gain reference required or desired
   - 'circuit': SLiCAP uses the loop gain reference specification from the netlist
   - <refDes>: Name of a dependent source (controlled source) that must be used as loop gain reference
   
   Obtain list with names of dependent variables in your circuit:
   
   .. code-block:: python
   
      import SLiCAP as sl
      sl.initProject("my Project")
      cir = sl.makeCircuit(<myCircuit>)
      # Obtain the list names of dependent sources in <myCircuit>
      print(cir.controlled)
      
#. **convtype**: None, 'all', 'dd', 'dc', 'cd', or 'cc'; defaults to None

   The conversion type is used to convert balanced circuits into differential-mode and common-mode equivalent circuits.
   
   - None: No matrix conversion will be applied
   
   - 'all': Dependent variables and independent variables will be grouped in differential-mode and common-mode variables. 
   
     The circuit matrix dimension is not changed.
     
     Conversion type only be used with the doMatrix() instruction
     
   - 'dd': After grouping of the vaiables in differential-mode and common-mode variables, only the differential-mode variables of both dependent and independent variables are considered. 
   
     The matrix equation describes the differential-mode behavior of the circuit.
   
   - 'cc': After grouping of the vaiables in differential-mode and common-mode variables, only the common-mode variables of both dependent and independent variables are considered. 
   
     The matrix equation describes the common-mode behavior of the circuit.
     
   - 'dc': After grouping of the vaiables in differential-mode and common-mode variables, only the differential-mode dependent variables and the common-mode independent variables are considered. 
   
     The matrix equation describes the common-mode to differential-mode conversion of the circuit.

   - 'cd': After grouping of the vaiables in differential-mode and common-mode variables, only the common-mode dependent variables and the differential-mode independent ariables are considered. 

     The matrix equation describes the differential-mode to common-mode conversion of the circuit.

#. **pardefs**: None, 'circuit', or dict; defaults to None

   - None: Analysis will be performed without substitution of parameters
   - 'circuit': Analysis will be performed with all parameters defined with the circuit (cir.parDefs) recursively substituted
   - dict: Analysis will be performed with all parameters defined in dict (key = parameter name, value = parameter value or expression)
   
   Obtain a dictionary with parameter the circuit parameter definitions and a list with undefined parameters:
   
   .. code-block:: python
   
      import SLiCAP as sl
      sl.initProject("my Project")
      cir = sl.makeCircuit(<myCircuit>)
      # Obtain the parameter definitions in <myCircuit>
      for key in cir.parDefs.keys():
        print(key, ':', cir.parDefs[key])
      # Print a list with undefined parameters:
      print(cir.params)
      
#. **numeric**: True, False; defaults to False

   - False: Analysis will be performed with rational numbers and without numeric evaluation of constants (:math:`\pi`) or functions. In some cases, however, pole-zero analysis and noise integration will switch to floating point calculation.
   - True: Analysis will be performed with all constants and functions numerically evaluated
   
#. **stepdict**: None, dict

   - None: Analysis will be performed withoud parameter stepping
   - dict: Analysis will be repeated for a number of steps with a different (set of) parameter(s)
   
     The step dictionary dict can have the following key-value pairs:
     
     - dict['stepmethod']: (str); 'lin', 'log', 'list', 'array'
     - dict['params']: (str, sympy.Symbol) for stepmethod: lin', 'log', and 'list' (list of str or sympy.Symbol) for stepmethod: 'array'
     - dict['start']: ( float, int, str): start value for linear and log stepping
     - dict['stop']: ( float, int, str): stop value for linear and log stepping
     - dict['num']: (int), number of steps for lin and log stepping
     - dict['values']: (list of int, float, or str) step values for stepmethod: 'list', (list of lists of int, float, or str) step values for stepmethod: 'array'

Predefined Analysis Types
=========================

Below an overview of instructions that have been implemented in SLiCAP. Links are provided to the detailed description of the functions in the `reference <../reference/SLiCAPshell.html>`__ section.

#. Network equations:

   - `doMatrix <../reference/SLiCAPshell.html#SLiCAP.SLiCAPshell.doMatrix>`__: matrix equation of the circuit

#. Complex frequency domain (Laplace) analysis:
    
   - `doLaplace <../reference/SLiCAPshell.html#SLiCAP.SLiCAPshell.doLaplace>`__: transfer function or detector current/voltage (Laplace expression)
   - `doNumer <../reference/SLiCAPshell.html#SLiCAP.SLiCAPshell.doNumer>`__: numerator of a transfer function or detector current/voltage 
   - `doDenom <../reference/SLiCAPshell.html#SLiCAP.SLiCAPshell.doDenom>`__ : denominator of a transfer function or detector current/voltage
   - `doSolve <../reference/SLiCAPshell.html#SLiCAP.SLiCAPshell.doSolve>`__: Laplace Transform of the network solution or detector current/voltage

#. Complex frequency domain analysis: Poles and zeros of transfer functions:

   - `doPoles <../reference/SLiCAPshell.html#SLiCAP.SLiCAPshell.doPoles>`__: poles of a transfer, including non-controllable and non-observable (complex frequency solutions of Denom)
   - `doZeros <../reference/SLiCAPshell.html#SLiCAP.SLiCAPshell.doZeros>`__: zeros of a transfer (complex frequency solutions of Numer)
   - `doPZ <../reference/SLiCAPshell.html#SLiCAP.SLiCAPshell.doPZ>`__: DC value, poles and zeros of a transfer (with pole-zero canceling)    
   
#. Noise analysis: spectral densities of detector and source-referred noise and the individual contributions of all independent noise sources

   - `doNoise <../reference/SLiCAPshell.html#SLiCAP.SLiCAPshell.doNoise>`__
   
#. Time domain analysis, based on the Inverse Laplace Transform:

   - `doTime <../reference/SLiCAPshell.html#SLiCAP.SLiCAPshell.doTime>`__: detector voltage or current
   - `doImpulse <../reference/SLiCAPshell.html#SLiCAP.SLiCAPshell.doImpulse>`__: unit-impulse response of a transfer
   - `doStep <../reference/SLiCAPshell.html#SLiCAP.SLiCAPshell.doStep>`__: unit-step response of a transfer
   - `doTimeSolve <../reference/SLiCAPshell.html#SLiCAP.SLiCAPshell.doTimeSolve>`__: Time-domain solution of a network
   
#. DC (zero-frequency) analysis:

   - `doDC <../reference/SLiCAPshell.html#SLiCAP.SLiCAPshell.doDC>`__: Zero-frequency value of a transfer or detector current/voltage
   - `doDCsolve <../reference/SLiCAPshell.html#SLiCAP.SLiCAPshell.doDCsolve>`__: DC network solution
   - `doDCvar <../reference/SLiCAPshell.html#SLiCAP.SLiCAPshell.doDCvar>`__: detector-referred and source-referred DC variance

Detector, source, and loop gain reference
=========================================

Some analysis types require definitions of a signal source, a signal detector, and/or a loop gain reference. Souce, detector and loop gain reference are specified with the circuit.

- A **detector** specification is **NOT** required for the instructions:
                     
  - doMatrix()
  - doDenom()
  - doPoles()
  - doSolve()
  - doDCsolve()
  - doTimeSolve()
  
  **AND** for transfer types:
      
  - loopgain
  - servo
                   
  In all other cases a definition of a detector is required.

- A **source** specification is required for transfers: 'gain', 'direct', and 'asymptotic'.

  If a source definition is given, instructions 'doNoise()' and 'doDCvar()' also return the source-referred noise and source referred DC variance, respectively.

- A **loop gain reference** specification is required for the transfers: 'asymptotic', direct', 'loopgain', and 'servo'.
  
.. image:: /img/colorCode.svg
