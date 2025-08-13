================
Perform analysis
================
    
.. image:: /img/colorCode.svg

SLiCAP has 16 predefined analysis types. However, since SLiCAP is built upon the powerful `Sympy CAS <https://www.sympy.org/en/index.html>`_ (Computer Algebra System), users can easily extend SLiCAP's capabilities and add functionality.

General instruction format
==========================

The general instruction format is (with default keyword arguments):

.. code-block:: python

    result = do<Instruction>(cir, transfer='gain', source='circuit', detector='circuit', 
                             lgref='circuit', convtype=None, pardefs=None, numeric=False, 
                             stepdict=None)

where <Instruction> describes the analysis to be performed. 

The return value of all instructions is an `instrucion <../reference/SLiCAPinstruction.html)>`_ object. Execution of the instruction will set some attributes of this object. Detailed information for each instruction is given in de `Reference section <../reference/SLiCAPshell.html>`__.

The function arguments are discussed in separate sections below.

The circuit object
------------------

**cir**: `circuit <../reference/SLiCAPprotos.html#SLiCAP.SLiCAPprotos.circuit>`__ object use for the instruction. **cir** is the only required argument for all instructions.

The transfer type
-----------------

**transfer**: None \| 'gain' \| 'asymptotic' \| 'loopgain' \| 'servo' \| 'direct'; defaults to 'gain'.

A transfer type is required for transfer related analysis types.
   
- None: no transfer type is specified; SLiCAP will calculate the detector voltage or current, or perform analysis that do not require a source specification.
- 'gain': source to detector transfer
- 'asymptotic': Gain of a circuit withthe loop gain reference replaced with a nullor (the 'asymptotic-gain'); see `Work with feedback <feedback.html>`_
- 'direct': Gain of a circuit with the value of the loop gain reference set to zero (the 'direct transfer'); see `Work with feedback <feedback.html>`_
- 'loopgain': Gain enclosed in the loop involving the loop gain reference (the 'loop gain'); see `Work with feedback <feedback.html>`_
- 'servo': :math:`\frac{-L}{1-L}`, where :math:`L` is the loop gain as defined above (the 'servo function'); see `Work with feedback <feedback.html>`_

The signal source
-----------------
   
**source**: None \| 'circuit' \| <refDes> \| [<refDes+>, <refDes->], defaults to : 'circuit'

- None: No source required or desired
- 'circuit': SLiCAP uses the source specification from the netlist
- <refDes>, <refDes+>, <refDes->: Name of an independent voltage or current source that must be used as signal source
   
.. admonition:: Important
    :class: note
    
    The circuit object attribute `indepVars <../reference/SLiCAPprotos.html#SLiCAP.SLiCAPprotos.circuit.indepVars>`__ returns a list with circuit independent sources that can be used as signal source.
   
    .. code-block:: python

        import SLiCAP as sl
        sl.initProject("my Project")
        cir = sl.makeCircuit(<myCircuit>)
        # Obtain the list of independent sources in <myCircuit>
        print(cir.indepVars)

A signal **source** specification is required for transfers: 'gain', 'direct', and 'asymptotic'.

If a source definition is given, the instructions 'doNoise()' and 'doDCvar()' also return the source-referred noise and source referred DC variance, respectively.

A signal source can be specified in three different ways:

- On the schematic

  Place a SPICE directive (command) ``.source`` on the schematic.
  
  - The format for a single-ended source is: ``.source <refdes-independent-source>``
  - The format for a differential source is: ``.source <refdes-positive-source> <refdes-negative-source>``
  
- In the circuit file

  Place the above commands in the netlist (.cir) file
  
- With the instruction

  This is done by using th keyword argument ``source`` in the instruction. The format is as follows
  
  - Single-ended source: ``source=<refdes-independent-source>``
  - Differential source: ``source=[<refdes-positive-source>, <refdes-negative-source>]``
    
The signal detector
-------------------
   
**detector**: None \| 'circuit' \| <detName> \| [<detName+>, <detName->], defaults to : 'circuit'

- None: No detector required or desired
- 'circuit': SLiCAP uses the detector specification from the netlist
- <detName>, <detName+>, <detName->: Name of a dependent variable (nodal voltage or branch current) that must be used as signal detector

.. admonition:: Important
    :class: note
    
    The circuit object method `depVars() <../reference/SLiCAPprotos.html#SLiCAP.SLiCAPprotos.circuit.depVars>`__ returns a list with circuit dependent variables that can be used as detector.
   
    .. code-block:: python
       
        import SLiCAP as sl
        sl.initProject("my Project")
        cir = sl.makeCircuit(<myCircuit>)
        # Obtain the list names of dependent variables in <myCircuit>
        print(cir.depVars())

A signal **detector** specification is **NOT** required for the instructions:
                     
- ``doMatrix()``
- ``doDenom()``
- ``doPoles()``
- ``doSolve()``
- ``doDCsolve()``
- ``doTimeSolve()``

**AND** for transfer types:
  
- ``loopgain``
- ``servo``
               
In all other cases a definition of a detector is required.

A signal detector can be specified in three different ways:

- On the schematic

  Place a SPICE directive (command) ``.detector`` on the schematic.
  
  - The format for a single voltage detector is: ``.detector V_<node-name>``
  - The format for a differential voltage detector is: ``.detector V_<positive-node>  V_<negative-node>``
  - The format for a single current detector is: ``.detector I_<element-refdes>``
  - The format for a differential current detector is: ``.detector I_<positive-element> I_<negative-element>``
  
- In the circuit file

  Place the above commands in the netlist (.cir) file
  
- With the instruction

  Use the keyword argument ``detector`` in the instruction. The format is as follows
  
  - Single-ended voltage detector: ``detector="V_<node-name>"``
  - Differential voltage detector: ``detector=["V_<positive-node>", "V_<negative-node>"]``
  - Single-ended current detector: ``detector="I_<element-refdes>"``
  - Differential current detector: ``detector=["I_<positive-element>", "I_<negative-element>"]``
    
The loop gain reference
-----------------------

**lgref**: None \| 'circuit' \| <refDes> \| [<refDes+>, <refDes->], defaults to : 'circuit'; see `Work with feedback circuits <feedback.html>`_.

- None: No loop gain reference required or desired
- 'circuit': SLiCAP uses the loop gain reference specification from the netlist
- <refDes>, <refDes+>, <refDes->: Name of a dependent source (controlled source) that must be used as loop gain reference
   
.. admonition:: Important
    :class: note
    
    The circuit object attribute `controlled <../reference/SLiCAPprotos.html#SLiCAP.SLiCAPprotos.circuit.controlled>`__ returns a list with circuit dependent sources that can be used as loop gain reference.
   
    .. code-block:: python
       
        import SLiCAP as sl
        sl.initProject("my Project")
        cir = sl.makeCircuit(<myCircuit>)
        # Obtain the list names of dependent sources in <myCircuit>
        print(cir.controlled)

A **loop gain reference** specification is required for the transfers: 'asymptotic', direct', 'loopgain', and 'servo'; see `Work with feedback circuits <feedback.html>`_.

A loop gain reference source can be specified in three different ways:

- On the schematic

  Place a SPICE directive (command) ``.lgref`` on the schematic.
  
  - The format for a single-ended source is: ``.lgref <refdes-dependent-source>``
  - The format for a differential source is: ``.lgref <refdes-pos-dep-source> <refdes-neg-dep-source>``
  
- In the circuit file

  Place the above commands in the netlist (.cir) file
  
- With the instruction

  This is done by using the keyword argument ``lgref`` in the instruction. The format is as follows
  
  - Single-ended loop gain reference: ``lgref="<refdes-dependent-source>"``
  - Differential loop gain reference: ``lgref["<refdes-pos-dep-source>" "<refdes-neg-dep-source>"]``
      
The conversion type
-------------------
    
**convtype**: None \| 'all' \| 'dd' \| 'dc' \| 'cd' \| 'cc'; defaults to None. See `Work with balanced circuits <balanced.html>`_

The conversion type is used to convert balanced circuits into differential-mode and common-mode equivalent networks.
   
- None: No matrix conversion will be applied
   
- 'all': Dependent variables and independent variables will be grouped in differential-mode and common-mode variables. 
   
  The circuit matrix dimension is not changed.
     
  This conversion type can only be used with the doMatrix() instruction.
     
- 'dd': After grouping of the vaiables in differential-mode and common-mode variables, only the differential-mode variables of both dependent and independent variables are considered. 
   
  The matrix equation describes the differential-mode behavior of the circuit.
   
- 'cc': After grouping of the vaiables in differential-mode and common-mode variables, only the common-mode variables of both dependent and independent variables are considered. 
   
  The matrix equation describes the common-mode behavior of the circuit.
     
- 'dc': After grouping of the vaiables in differential-mode and common-mode variables, only the differential-mode dependent variables and the common-mode independent variables are considered. 
   
  The matrix equation describes the common-mode to differential-mode conversion of the circuit. This conversion type can only be used with the doMatrix() instruction.

- 'cd': After grouping of the vaiables in differential-mode and common-mode variables, only the common-mode dependent variables and the differential-mode independent ariables are considered. 

  The matrix equation describes the differential-mode to common-mode conversion of the circuit. This conversion type can only be used with the doMatrix() instruction.

The parameter definitions
-------------------------

**pardefs**: None \| 'circuit' \| dict; defaults to None

- None: Analysis will be performed without substitution of parameters
- 'circuit': Analysis will be performed with all parameters defined with the circuit (cir.parDefs), recursively substituted
- dict: Analysis will be performed with all parameters defined in dict (key = parameter name, value = parameter value or expression)
   
Example: obtain a dictionary with the circuit parameter definitions and a list with undefined parameters:
   
.. code-block:: python
   
    import SLiCAP as sl
    sl.initProject("my Project")
    cir = sl.makeCircuit(<myCircuit>)
    # Obtain the parameter definitions in <myCircuit>
    for key in cir.parDefs.keys():
        print(key, ':', cir.parDefs[key])
    # Print a list with undefined parameters:
    print(cir.params)

Conversion to float
-------------------
      
**numeric**: True \| False; defaults to False

- False: Analysis results with rational numbers and without numeric evaluation of constants (:math:`\pi`) or functions. In some cases, however, pole-zero analysis and noise integration, SLiCAP will switch to floating point calculation.
- True: Analysis results with all constants and functions numerically evaluated and converted to floats.

Parameter stepping
------------------
   
**stepdict**: None \| dict

- None: Analysis will be performed without parameter stepping
- dict: Analysis will be repeated for a number of steps with a different (sets of) parameter(s)
   
The step dictionary can have the following key-value pairs:
     
- *'method'*: 
     
  - (*str*); 'lin', 'log', 'list', 'array'
       
- *'params'*: 
     
  - (*str*, *sympy.Symbol*) for stepmethod: 'lin', 'log', and 'list'
  - (*list* with *str*, or *sympy.Symbol*) for stepmethod: 'array'
       
- *'start'*: 
     
  - (*float*, *int*, *str)*: start value for 'lin' and 'log' stepping
       
- *'stop'*: 
     
  - (*float*, *int*, *str*): stop value for 'lin' and 'log' stepping
       
- *'num'*: 
     
  - (*int)*: number of steps for 'lin' and 'log' stepping
       
- *'values'*: 
     
  - (*list* with *int*, *float*, or *str*) step values for stepmethod: 'list', 
  - (*list* with *lists* with *int*, *float*, or *str*) step values for stepmethod: 'array'

Predefined analysis types
=========================

Below an overview of instructions that have been implemented in SLiCAP. Links are provided to the detailed description of the functions in the `reference <../reference/SLiCAPshell.html>`__ section.

Network equations
-----------------

`doMatrix() <../reference/SLiCAPshell.html#SLiCAP.SLiCAPshell.doMatrix>`__: matrix equation of the circuit

Complex frequency domain (Laplace) analysis
-------------------------------------------
    
`doLaplace() <../reference/SLiCAPshell.html#SLiCAP.SLiCAPshell.doLaplace>`__: transfer function or detector current/voltage (Laplace expression)

`doNumer() <../reference/SLiCAPshell.html#SLiCAP.SLiCAPshell.doNumer>`__: numerator of a transfer function or detector current/voltage 

`doDenom() <../reference/SLiCAPshell.html#SLiCAP.SLiCAPshell.doDenom>`__ : denominator of a transfer function or detector current/voltage

`doSolve() <../reference/SLiCAPshell.html#SLiCAP.SLiCAPshell.doSolve>`__: Laplace Transform of the network solution or detector current/voltage

Complex frequency domain analysis: poles and zeros of transfer functions
------------------------------------------------------------------------

`doPoles() <../reference/SLiCAPshell.html#SLiCAP.SLiCAPshell.doPoles>`__: poles of a transfer, including non-controllable and non-observable (complex frequency solutions of Denom)

`doZeros() <../reference/SLiCAPshell.html#SLiCAP.SLiCAPshell.doZeros>`__: zeros of a transfer (complex frequency solutions of Numer)

`doPZ() <../reference/SLiCAPshell.html#SLiCAP.SLiCAPshell.doPZ>`__: DC value, poles and zeros of a transfer (with pole-zero canceling: only controllable and observable poles)    
   
Noise analysis
--------------

`doNoise() <../reference/SLiCAPshell.html#SLiCAP.SLiCAPshell.doNoise>`__ returns the spectral densities of the total detector-referred and source-referred noise, and the individual contributions of all independent noise sources.

Time domain analysis: Inverse Laplace Transform
-----------------------------------------------

`doTime() <../reference/SLiCAPshell.html#SLiCAP.SLiCAPshell.doTime>`__: detector voltage or current

`doImpulse() <../reference/SLiCAPshell.html#SLiCAP.SLiCAPshell.doImpulse>`__: unit-impulse response of a transfer

`doStep() <../reference/SLiCAPshell.html#SLiCAP.SLiCAPshell.doStep>`__: unit-step response of a transfer

`doTimeSolve() <../reference/SLiCAPshell.html#SLiCAP.SLiCAPshell.doTimeSolve>`__: Time-domain solution of a network
   
DC (zero-frequency) and DC variance analysis
--------------------------------------------

`doDC() <../reference/SLiCAPshell.html#SLiCAP.SLiCAPshell.doDC>`__: Zero-frequency value of a transfer or detector current/voltage

`doDCsolve() <../reference/SLiCAPshell.html#SLiCAP.SLiCAPshell.doDCsolve>`__: DC network solution

`doDCvar() <../reference/SLiCAPshell.html#SLiCAP.SLiCAPshell.doDCvar>`__: detector-referred and source-referred DC variance, and the individual contributions of all independent dcvar sources.

.. image:: /img/colorCode.svg
