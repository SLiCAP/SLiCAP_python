=====================
Define an instruction
=====================

Working with SLiCAP comes to the definition and execution of SLiCAP instructions. After setting all relevant attributes of a `SLiCAP instruction object <../reference/SLiCAPinstruction.html#SLiCAP.SLiCAPinstruction.SLiCAPinstruction.instruction>`_, its execution returns a result object that comprises results and instruction settings. 

SLiCAP has built-in plot functions and HTML report functions to convert these result objects automatically into plots or HTML pages.

Before execution, SLiCAP always checks the completeness and consistency of the instruction.

See :ref:`Execute` for execution of the instruction and a description of the result object that comprises the instruction results.

The following sections discuss the main attributes of the instruction:

#. :ref:`defCircuit`
#. :ref:`defSimType`
#. :ref:`defGainType`
#. :ref:`source`
#. :ref:`detector`
#. :ref:`LGref`
#. :ref:`defConvType`
#. :ref:`defDataType`

.. _defCircuit:

-------------------------------------------------------
Create a circuit object and assign it to an instruction
-------------------------------------------------------

The `instruction.setCircuit() <../reference/SLiCAPinstruction.html#SLiCAP.SLiCAPinstruction.SLiCAPinstruction.instruction.setCircuit>`_ method checks syntax of the netlist, converts the netlist into a *flattened* `circuit <../reference/SLiCAPprotos.html#SLiCAP.SLiCAPprotos.SLiCAPprotos.circuit>`_ object, and assignes this circuit to the `instruction.circuit <../reference/SLiCAPinstruction.html#SLiCAP.SLiCAPinstruction.SLiCAPinstruction.instruction.circuit>`_  attribute.

.. code-block:: python

    >>> from SLiCAP import *
    >>> prj = initProject('My first RC network') # Initialize a SLiCAP project
    >>> instr = instruction()        # Create an instance of an instruction object
    >>> instr.setCircuit('myFirstRCnetwork.cir') # Create a circuit object from the netlist 
                                     # file 'myFirstRCnetwork.cir' and make it an attribute 
                                     # *instr.circuit* of the instruction object
    No errors found for circuit: 'My first RC network' from file: 'myFirstRCnetwork.cir'.

View section :ref:`html` for displaying circuit data on an HTML page.

.. _defSimType:

--------------------------
Define the simulation type
--------------------------

SLiCAP can perform symbolic and numeric analyis. The `simType <../reference/SLiCAPinstruction.html#SLiCAP.SLiCAPinstruction.SLiCAPinstruction.instruction.simType>`_ attribute of an instruction tells SLiCAP which method to use. However, in most cases, SLiCAP uses symbolic methods, even if the data is numerical. If the simulation type has been set to *numeric*, parameter values are recursively substituted into the circuit element expressions.

The simulation type can be set with the `instruction.setSymType() <../reference/SLiCAPinstruction.html#SLiCAP.SLiCAPinstruction.SLiCAPinstruction.instruction.setSimType>`_ method.

.. code-block:: python

    >>> from SLiCAP import *
    >>> prj = initProject('My first RC network') # Initialize a SLiCAP project
    >>> instr = instruction()        # Create an instance of an instruction object
    >>> instr.setCircuit('myFirstRCnetwork.cir') # Create a circuit object from the netlist 
                                     # file 'myFirstRCnetwork.cir' and make it an attribute 
                                     # *instr.circuit* of the instruction object
    No errors found for circuit: 'My first RC network' from file: 'myFirstRCnetwork.cir'.

    >>> instr.setSimType('numeric')  # Set the simulation type to 'numeric'.
    >>> print(instr.simType)         # Print the current setting of the simulation type
    numeric
    >>> instr.setSimType('symbolic') # Set the simulation mode to 'symbolic'
    >>> print(instr.simType)         # Print the current setting of the simulation type
    symbolic

.. _defGainType:

--------------------
Define the gain type
--------------------

SLiCAP can provide expressions for:

#. Detector voltage or current (see :ref:`detector` for definition of the detector); this requires:

   - gain type: *vi*

#. Transfer functions of the asymptotic-gain model  (see :ref:`detector` for definition of the detector, :ref:`source` for definition of the signal source, and :ref:`LGref` for definition of the loop gain reference)
	
   - source-to-detector transfer: gain type *gain*
		
	 This is the transfer from the source to the detector
				
   - asymptotic-gain: gain type *asymptotic*
		
	 This is the gain when the loop gain reference is replaced with a nullor.
				
   - loop gain: gain type *loopgain*
		
	 This is the transfer of the controlled source selected by the loop gain reference variable, multiplied with the transfer from the output quantity of this controlled source to its input quantity.
				
   - direct transfer: gain type *direct*
		
	 This is the transfer from source to the detector with the gain of the loop gain reference variable set to zero
				  
   - servo function: gain type *servo*
		
	 This is :math:`\frac{-L}{1-L}` in which :math:`L` is the loop gain according to the definition above.

The gain type can be defined with the `instruction.setGainType() <../reference/SLiCAPinstruction.html#SLiCAP.SLiCAPinstruction.SLiCAPinstruction.instruction.setGainType>`_ method. It sets the `gainType <../reference/SLiCAPinstruction.html#SLiCAP.SLiCAPinstruction.SLiCAPinstruction.instruction.gainType>`_ attribute of the instruction.
 
.. code-block:: python

    >>> from SLiCAP import *
    >>> prj = initProject('My first RC network') # Initialize a SLiCAP project
    >>> instr = instruction()           # Create an instance of an instruction object
    >>> instr.setCircuit('myFirstRCnetwork.cir') # Create a circuit from 'myFirstRCnetwork.cir'
    No errors found for circuit: 'My first RC network' from file: 'myFirstRCnetwork.cir'.

    >>> instr.setGainType('vi')         # Set the gain type to 'vi'.
    >>> print(instr.gainType)           # Print the current setting of the gain type
    vi
    >>> instr.setGainType('gain')       # Set the gain type to 'gain'.
    >>> print(instr.gainType)           # Print the current setting of the gain type
    gain
    >>> instr.setGainType('asymptotic') # Set the gain type to 'asymptotic'.
    >>> print(instr.gainType)           # Print the current setting of the gain type
    asymptotic
    >>> instr.setGainType('loopgain')   # Set the gain type to 'loopgain'.
    >>> print(instr.gainType)           # Print the current setting of the gain type
    loopgain
    >>> instr.setGainType('servo')      # Set the gain type to 'servo'.
    >>> print(instr.gainType)           # Print the current setting of the gain type
    servo
    >>> instr.setGainType('direct')     # Set the gain type to 'direct'.
    >>> print(instr.gainType)           # Print the current setting of the gain type
    direct

.. _source:

------------------------
Define the signal source
------------------------

Any independent current source or independent voltage source in the circuit can be selected as signal source. A source can be defined with the  `instruction.setSource() <../reference/SLiCAPinstruction.html#SLiCAP.SLiCAPinstruction.SLiCAPinstruction.instruction.setSource>`_ method.  The argument of the function should be the name (identifier) of an inpependent source in the circuit, or a list with the names of two sources. A list of available independent sources is returned by the method: `instruction.indepVars() <../reference/SLiCAPinstruction.html#SLiCAP.SLiCAPinstruction.SLiCAPinstruction.instruction.indepVars>`_. 

For the analysis of balanced circuits, SLiCAP supports the definition of dual (paired) sources.

.. code-block:: python

    >>> from SLiCAP import *
    >>> prj = initProject('My first RC network') # Initialize a SLiCAP project
    >>> instr = instruction()           # Create an instance of an instruction object
    >>> instr.setCircuit('myFirstRCnetwork.cir') # Create a circuit from 'myFirstRCnetwork.cir'
    No errors found for circuit: 'My first RC network' from file: 'myFirstRCnetwork.cir'.

    >>> print(instr.indepVars())        # Print a list with independent sources in the circuit
    ['V1']
    >>> instr.setSource('V1')           # Define the signal source
    >>> print(instr.source)             # Print the signal source
    [V1, None]

.. _detector:

-------------------
Define the detector 
-------------------
	  
SLiCAP can calculate one of the following:

#. One branch current through an element defined by its V(I) relation in current-controlled notation
#. One nodal voltage
#. One branch voltage (difference between two nodal voltages)
#. One difference between two branch currents through elements defined by their V(I) relation in current-controlled notation
#. One transfer function
#. The complete network solution

For (1) - (5) this variable is defined by the detector, which can be set with the method: `instruction.setDetector() <../reference/SLiCAPinstruction.html#SLiCAP.SLiCAPinstruction.SLiCAPinstruction.instruction.setDetector>`_. The name of this function should be composed as follows:

- In the case of a voltage detector, the name should be the concatenation of 'V\_' and the name of the output node; in general: 'V_<outputNode>'. For the voltage difference between two nodes, simply use two arguments (see example below)

- In the case of a current detector, the name should be the concatenation of 'I\_' and the name of the element (identifier) whose current is taken as detector current.

Any dependent circuit variable can be selected as detector quantity. A symbolic list with available dependent variables is returned by the method: `instruction.depVars() <../reference/SLiCAPinstruction.html#SLiCAP.SLiCAPinstruction.SLiCAPinstruction.instruction.depVars>`_.

.. code-block:: python

    >>> from SLiCAP import *
    >>> prj = initProject('My first RC network') # Initialize a SLiCAP project
    >>> instr = instruction()           # Create an instance of an instruction object
    >>> instr.setCircuit('myFirstRCnetwork.cir') # Create a circuit from 'myFirstRCnetwork.cir'
    No errors found for circuit: 'My first RC network' from file: 'myFirstRCnetwork.cir'.

    >>> print(instr.depVars())          # print a list with ipossible detectors in the circuit
    ['I_V1', 'V_0', 'V_N001', 'V_out']
    >>> instr.setDetector('V_out')      # Nodal voltage 'V_out' is detector voltage
    >>> print(instr.detector)           # Print the detector
    ['V_out', None]
    >>> instr.setDetector(['V_out', 'V_N001']) # Voltage 'V_out'-'V_N001' is the detector voltage
    >>> print(instr.detector)           # Print the detector
    ['V_out', 'V_N001']
    >>> instr.setDetector('I_V1')       # Current through 'V1' is the detector current
    >>> print(instr.detector)           # Print the detector
    ['I_V1', None]

.. _LGref:

------------------------------
Define the loop gain reference
------------------------------

The asymptotic-gain negative-feedback model uses one controlled source of the circuit as *loop gain reference variable*. A list with controlled sources that are available for this purpose is returned by the method:  `instruction.controlled() <../reference/SLiCAPinstruction.html#SLiCAP.SLiCAPinstruction.SLiCAPinstruction.instruction.controlled>`_. 

Any controlled source from this list can be assigned as loop gain reference variable. This can be done with the method `instruction.setLGref() <../reference/SLiCAPinstruction.html#SLiCAP.SLiCAPinstruction.SLiCAPinstruction.instruction.setLGref>`_. 

For the analysis of balanced circuits, SLiCAP supports the definition of dual (paired) loop gain references.

.. code-block:: python

    >>> from SLiCAP import *
    >>> prj = initProject('My first RC network') # Initialize a SLiCAP project
    >>> instr = instruction()           # Create an instance of an instruction object
    >>> instr.setCircuit('myFirstRCnetwork.cir') # Create a circuit from 'myFirstRCnetwork.cir'
    No errors found for circuit: 'My first RC network' from file: 'myFirstRCnetwork.cir'.

    >>> print instr.controlled()        # Print a list with names of controlled sources
    []

.. _defConvType:

---------------------------------
Define the matrix conversion type
---------------------------------

The definition of the matrix conversion type is only required when working with balanced networks. See :ref:`balanced` for detailed information.

SLiCAP can convert the MNA equation of a network into an equivalent equation of

- A network that decribes the differential-mode behavior: *instr.convType='dd'*
- A network that decribes the differential-mode to common-mode conversion: *instr.convType='dc'*
- A network that decribes the common-mode to differential-mode conversion: *instr.convType='cd'*
- A network that decribes the common-mode behavior: *instr.convType='cc'*
- The complete network transformed to a differential-mode and common-mode base: *instr.convType='all'*

.. code-block:: python

    >>> instr.setConvType('dd')  # differential-mode equivalent network
    >>> instr.setConvType('dc')  # differential-mode to common-mode equivalent network
    >>> instr.setConvType('cd')  # common-mode to differential-mode equivalent network
    >>> instr.setConvType('cc')  # common-mode equivalent network
    >>> instr.setConvType('all') # MNA matrix transformed to differential-mode and common-mode base
    >>> instr.setConvType(None)  # MNA matrix (default)

    >>> print(instr.convType)

    None

.. _defDataType:

--------------------
Define the data type
--------------------

SLiCAP can provide 16 types of data. It is defined with the method: `instruction.setDataType() <../reference/SLiCAPinstruction.html#SLiCAP.SLiCAPinstruction.SLiCAPinstruction.instruction.setDataType>`_. Below an overview of the availabe data types and their meaning.

#. dc     

    Calculates DC value of the detector voltage or the detector current; only for gain type 'vi'.

#. dcsolve

   Calculates DC solution of the network; only for gain type 'vi'.

#. dcvar

   Calculates contribution of all dc variances (sources and resistors) to the detector-referred variance. Only for gain type 'vi'. If a signal source has been defined it also calculates the contibutions to the source-referred variance.

#. denom

   Calculates the denominator of the Laplace Transform of the unit-impulse response or of a voltage or a current.

#. impulse

   Calculates inverse laplace transform of a transfer not for gain type 'vi'; may not work with symbolic values.

#. laplace

   Calculates the Laplace transfer function (Laplace transform of the unit-impulse response) or the Lapalce Transform of a voltage or a current.

#. matrix

   Returns the MNA matrix equation of the circuit.

#. noise

   Calculates contributions to the detector-referred noise of all noise sources. Only for gain type 'vi'. If a signal source has been defined it also calculates the contibutions to the source-referred noise.

#. numer

   Calculates the numerator of the Laplace Transform of the unit-impulse response or of a voltage or a current.

#. params

   Calculates the values of parameters, while sweeping or stepping other parameters.

#. poles

   Calculates the complex solutions of the denominator of the Laplace transform of a transfer function. Not available for gain type 'vi'.

#. pz

   Calculates the complex solutions of the numerator and of the denominator of the Laplace Transform of the unit-impulse response and the zero-frequency value of the transfer. Not available for gain type 'vi'. Poles and zeros with equal values are cancelled.

#. solve

   Calculates the network solution; only for gain type 'vi'.

#. step

   Calculates inverse Laplace transform of (1/s) times the transfer function. It may not work with symbolic values.

#. time

   Calculates inverse Laplace transform of a detector voltage or current. Only for gain type 'vi'. It may not work with symbolic values.

#. zeros

   Calculates the complex solutions of the numerator of the Laplace transform of a transfer function. Not available for gain type 'vi'.

.. code-block:: python

    >>> from SLiCAP import *
    >>> prj = initProject('My first RC network') # Initialize a SLiCAP project
    >>> instr = instruction()         # Create an instance of an instruction object
    >>> instr.setCircuit('myFirstRCnetwork.cir') # Create a circuit from 'myFirstRCnetwork.cir'
    No errors found for circuit: 'My first RC network' from file: 'myFirstRCnetwork.cir'.

    >>> instr.setSimType('symbolic')  # Define the simulation type
    >>> instr.setSource('V1')         # Define the signal source
    >>> instr.setDetector('V_out')    # Nodal voltage 'V_out' is detector voltage
    >>> instr.setGainType('gain')     # Define the gain type
    >>> instr.setDataType('laplace')  # Define the data type
    >>> result = instr.execute()      # Execute the instruction and assign the results to 'result'
    >>> print result.laplace          # Print the Laplace transform of the gain
    1.0/(1.0*C*R*s + 1.0)
