==================
Pole-zero analysis
==================

SLiCAP can accurately determine poles and zeros of transfer functions. To this end, SLiCAP writes the MNA equations of the electrical circuit in the differential form as a function of the Laplace variable and uses fast division-free algorithms for evaluation of the determinant. 

SLiCAP has three data types for evaluation of poles and zeros:

#. :ref:`dataTypePoles`
#. :ref:`dataTypeZeros`
#. :ref:`dataTypePZ`

The result object returns values of poles and zeros in [rad/s]. The results of a pole-zero analysis can be displayed on an HTML page: pz2html(<*instructionresult*>), or in the python console: listPZ(<*instructionresult*>). These display methods are sensitive to the setting of *ini.Hz*. If *True* the results are displayed in [Hz], else in [rad/s]

.. _dataTypePoles:

-----------------
Data type 'poles'
-----------------

With *instruction.dataType='poles'* SLiCAP returns the solutions of the determinant of the network. Hence, it returns the solutions of the denominator of the transfer function set by *intruction.gainType*. These solutions are all poles of the network, including the *non-observable* or *non-controllable* poles. Both numeric and symbolic analysis methods are supported, however, symbolic calculation with may fail or take a long time.

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
    >>> instr.setDataType('poles')    # Define the data type
    >>> result = instr.execute()      # Execute the instruction and assign the results to 'result'
    >>> print result.poles            # Print the poles of the gain

    [-1/(C*R)]

    >>> instr.setSimType('numeric')   # Switch to numeric analysis
    >>> result = instr.execute()      # Execute the instruction and assign the results to 'result'
    >>> print result.poles            # Print the poles of the gain    

    [-6283.185307179608]

.. admonition:: Note

    The execution results of a pole-zero analysis are **always in [rad/s]**. 

.. _dataTypeZeros:

-----------------
Data type 'zeros'
-----------------

With *instruction.dataType='zeros'* SLiCAP returns the solutions of the determinant of the network after application of Cramer's rule. Hence, it returns the solution of the numerator of the transfer function set by *intruction.gainType*. Both numeric and symbolic analysis methods are supported, however, symbolic calculation with may fail or take a long time.

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
    >>> instr.setDataType('zeros')    # Define the data type
    >>> result = instr.execute()      # Execute the instruction and assign the results to 'result'
    >>> print(result.zeros)           # Print the poles of the gain

    []

.. _dataTypePZ:

--------------
Data type 'pz'
--------------

With *instruction.dataType='pz'* SLiCAP returns the zero-frequency value of the transfer and a reduced set of poles and zeros. Poles and zeros that coincide within the numerical display resolution (set by *ini.disp*) are left out. These poles are called *non-observable* or *non-controllable*. Both numeric and symbolic analysis methods are supported, however, symbolic calculation with may fail or take a long time.

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
    >>> instr.setDataType('pz')       # Define the data type
    >>> result = instr.execute()      # Execute the instruction and assign the results to 'result'
    >>> print(result.poles)           # Print the poles of the gain
    [-1/(C*R)]

    >>> print(result.zeros)           # Print the zeros of the gain
    []

    >>> print(result.DCvalue)         # Print the zero-frequency value of the transfer
    1.0

The function listPZ(<*instructionresult*>) can only print numeric pole-zero anlysis results. With ini.Hz==True the functions pz2html(<*instructionresult*>) and listPZ(<*instructionresult*>) display the values of poles and zeros in [Hz], else in [rad/s].

.. code-block:: python

    >>> print(ini.Hz)                 # Print diplay units for listPZ and pz2html
    True

    >>> instr.setSimType('numeric')   # Switch to numeric analysis
    >>> result = instr.execute()      # Execute the instruction and assign the results to 'result'
    >>> listPZ(result)

    DC value of gain:  1.00e+0

    Poles of gain:

     n  Real part [Hz]  Imag part [Hz]  Frequency [Hz]     Q [-] 
    --  --------------  --------------  --------------  --------
     0       -1.00e+03        0.00e+00        1.00e+03

    Found no zeros.

