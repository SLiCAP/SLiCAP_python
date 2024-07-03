.. _parameterStepping:

==================
Parameter stepping
==================

SLiCAP can execute an instruction while stepping the value of one or more circuit parameters. 

SLiCAP functions for parameters stepping are discussed below

#. :ref:`stepMethod`
#. :ref:`stepVar`
#. :ref:`stepVals`
#. :ref:`stepEnable`

.. _stepMethod:

----------------------
Define the step method
----------------------

SLiCAP has four methods for parameter stepping:

#. Three of them are intended for stepping of a single parameter:

   - linear stepping: **SLiCAPinstruction.instruction.stepMethod** = 'lin'
   - logarithmic stepping: **SLiCAPinstruction.instruction.stepMethod** = 'log'
   - stepping through a list of values **SLiCAPinstruction.instruction.stepMethod** = 'list'

#. One method is intended for concurrently stepping multiple parameters:

   - array stepping: **SLiCAPinstruction.instruction.stepMethod** = 'array'

The step method is defined with by the method **SLiCAPinstruction.instruction.setStepMethod(*args)**:

.. code-block:: python

    >>> instr = instruction()         # Create an instance of the instruction object
    >>> instr.setStepmethod('lin')    # linear stepping  
    >>> instr.setStepMethod('log')    # logarithmic stepping 
    >>> instr.setStepMethod('list')   # stepping through a list
    >>> instr.setStepMethod('array')  # concurrent stepping of multiple parameters 
 
.. _stepVar:
   
---------------------------
Define the step variable(s)
---------------------------

Linear, log and list stepping
-----------------------------

The step variable for linear logarithmic and list stepping can be selected from the available circuit parameters.

.. code-block:: python

    >>> from SLiCAP import *
    >>> prj = initProject('My first RC network') # Initialize a SLiCAP project
    >>> instr = instruction()        # Create an instance of an instruction object
    >>> instr.setCircuit('myFirstRCnetwork.cir') # Create a circuit from 'myFirstRCnetwork.cir'
    No errors found for circuit: 'My first RC network' from file: 'myFirstRCnetwork.cir'.

    >>> all_params = instr.circuit.parDefs.keys() + instr.circuit.params
    >>> print(all_params)
    [f_c, C, R]
    >>> instr.setStepVar('R')        # Define 'R' as step parameter
    >>> print(instr.stepVar)
    R

Array stepping
--------------

As with single parameters stepping, the step variables can be selected from all available circuit parameters:

.. code-block:: python

    >>> from SLiCAP import *
    >>> prj = initProject('My first RC network') # Initialize a SLiCAP project
    >>> instr = instruction()         # Create an instance of an instruction object
    >>> instr.setCircuit('myFirstRCnetwork.cir') # Create a circuit from 'myFirstRCnetwork.cir'
    No errors found for circuit: 'My first RC network' from file: 'myFirstRCnetwork.cir'.

    >>> all_params = instr.circuit.parDefs.keys() + instr.circuit.params
    >>> print(all_params)             # Print the names of the circuit parameters
    [f_c, C, R]
    >>> instr.setStepVars(['R', 'C']) # Define 'R' and 'C' as step parameters
    >>> print(instr.stepVars)
    ['R', 'C']

.. _stepVals:

----------------------
Define the step values
----------------------

Linear and logarithmic stepping
-------------------------------

Linear and logarithmic stepping required the definition of the step variable, the start value, the stop value and the number of steps.

.. code-block:: python

    >>> from SLiCAP import *
    >>> prj = initProject('My first RC network') # Initialize a SLiCAP project
    >>> instr = instruction()        # Create an instance of an instruction object
    >>> instr.setCircuit('myFirstRCnetwork.cir') # Create a circuit from 'myFirstRCnetwork.cir'
    No errors found for circuit: 'My first RC network' from file: 'myFirstRCnetwork.cir'.

    >>> all_params = instr.circuit.parDefs.keys() + instr.circuit.params
    >>> print(all_params)            # Print the names of the circuit parameters
    [f_c, C, R]
    >>> instr.setStepVar('R')        # Define 'R' as step parameter
    >>> instr.setStepStart(10)       # Define the start value of 'R' 10 Ohm
    >>> instr.setStepStop('0.1k')    # Define the stop value of 'R' 100 Ohm
    >>> instr.setStepMethod('lin')   # Define linear stepping
    >>> instr.setStepNum(10)         # Take 10 values
    >>> instr.stepOn()               # Enable stepping

With logarithmic stepping SLiCAP calculates the number of decades and the number of points per decade from the start, the stop value and the total number of steps. Logarithmically stepping through zero is not allowed.

Stepping through a list of values
---------------------------------

The function `stepList(<listOfValues>)` is used to define a list of step values for a step variable.

.. code-block:: python

    >>> from SLiCAP import *
    >>> prj = initProject('My first RC network') # Initialize a SLiCAP project
    >>> instr = instruction()        # Create an instance of an instruction object
    >>> instr.setCircuit('myFirstRCnetwork.cir') # Create a circuit from 'myFirstRCnetwork.cir'
    No errors found for circuit: 'My first RC network' from file: 'myFirstRCnetwork.cir'.

    >>> all_params = instr.circuit.parDefs.keys() + instr.circuit.params
    >>> print(all_params)                     # Print the names of the circuit parameters
    [f_c, C, R]
    >>> instr.setStepVar('R')                 # Define 'R' as step parameter
    >>> instr.setStepMethod('list')           # Define list type stepping
    >>> instr.setStepList([10, 20, 50, 100])  # Take these four values
    >>> instr.stepOn()                        # Enable stepping

Array stepping
--------------

For array stepping the step values need to be provided in the form of a matrix. Row i in the matrix carries the values of SLiCAPinstruction.instruction.stepVars[i]. Hence, the number of rows equals the number of times the instruction will be executed.

.. code-block:: python

    >>> from SLiCAP import *
    >>> prj = initProject('My first RC network') # Initialize a SLiCAP project
    >>> instr = instruction()        # Create an instance of an instruction object
    >>> instr.setCircuit('myFirstRCnetwork.cir') # Create a circuit from 'myFirstRCnetwork.cir'
    No errors found for circuit: 'My first RC network' from file: 'myFirstRCnetwork.cir'.

    >>> all_params = instr.circuit.parDefs.keys() + instr.circuit.params
    >>> print(all_params)                     # Print the names of the circuit parameters
    [f_c, C, R]
    >>> instr.setStepVars(['R', 'C'])         # Define 'R' and 'C' as step parameters
    >>> instr.setStepMethod('array')          # Define array type stepping
    >>> instr.setStepArray([[100, 200], ['50p', '100p']])
    >>> instr.stepOn()                        # Enable stepping

.. _stepEnable:

------------------------------------
Enable or disable parameter stepping
------------------------------------

Parameter stepping can be enabled or disabled without affecting the settings for parameter stepping, such as, the step variable, the step method, etc.

.. code-block:: python

    >>> from SLiCAP import *
    >>> prj = initProject('My first RC network') # Initialize a SLiCAP project
    >>> instr = instruction()        # Create an instance of an instruction object
    >>> instr.setCircuit('myFirstRCnetwork.cir') # Create a circuit from 'myFirstRCnetwork.cir'
    No errors found for circuit: 'My first RC network' from file: 'myFirstRCnetwork.cir'.

    >>> instr.stepOn()   # Enable stepping, this does not affect the settings for stepping
    >>> instr.stepOff()  # Disable stepping,  this does not affect the settings for stepping
