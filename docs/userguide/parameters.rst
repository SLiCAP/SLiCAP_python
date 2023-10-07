====================
Work with parameters
====================

*Circuit parameters* are symbolic variables used in element expressions. There are two ways of assigning values or expressions to these parameters:

#. In the netlist using the SPICE '.PARAM' directives. 
#. From the python using the instruction.defPar() method.

When SLiCAP is working in numeric simulation mode, parameter and expressions values will recursively be substituted into element expressions. 

The sections show parameter related topics:

#. :ref:`parDefs`; including parameters without definition
#. :ref:`parVals`
#. :ref:`delPar`
#. :ref:`defPar`
#. :ref:`defPars`
#. :ref:`getPar`
#. :ref:`getPars`

.. _parDefs:

--------------------------
Get all circuit parameters
--------------------------

A list with all circuit parameters can be obtained as follows:

.. code-block:: python

    >>> from SLiCAP import *
    >>> prj = initProject('My first RC network') # Initialize a SLiCAP project
    >>> instr = instruction() # Create an instance of an instruction object
    >>> instr.setCircuit('myFirstRCnetwork.cir') # Create a circuit from 'myFirstRCnetwork.cir'
    No errors found for circuit: 'My first RC network' from file: 'myFirstRCnetwork.cir'.

    >>> all_param_names = list(instr.circuit.parDefs.keys()) + instr.circuit.params
    >>> print(all_param_names)
    [f_c, C, R]

.. _parVals:

-----------------------------
Get all parameter definitions
-----------------------------

A dictionary with key-value pairs of all circuit parameter definitions can be obtained as follows:

.. code-block:: python

    >>> from SLiCAP import *
    >>> prj = initProject('My first RC network') # Initialize a SLiCAP project
    >>> instr = instruction() # Create an instance of an instruction object
    >>> instr.setCircuit('myFirstRCnetwork.cir') # Create a circuit from 'myFirstRCnetwork.cir'
    No errors found for circuit: 'My first RC network' from file: 'myFirstRCnetwork.cir'.

    >>> all_par_defs = instr.circuit.parDefs
    >>> print(all_par_defs)
    {f_c: 1000.00000000000, C: 1/(2*pi*R*f_c), R: 1000.00000000000}

.. _delPar:

-----------------------------
Delete a parameter definition
-----------------------------

You can delete a parameter definition using the method **SLiCAPinstruction.instruction.delPar(*args)**. This method does not delete the circuit parameter itself: it only clears its definition so that it can be used as a symbolic variable in numeric simulations.

.. code-block:: python

    >>> from SLiCAP import *
    >>> prj = initProject('My first RC network') # Initialize a SLiCAP project
    >>> instr = instruction() # Create an instance of an instruction object
    >>> instr.setCircuit('myFirstRCnetwork.cir') # Create a circuit from 'myFirstRCnetwork.cir'
    No errors found for circuit: 'My first RC network' from file: 'myFirstRCnetwork.cir'.

    >>> instr.defPar('R', 'tau/C')      # Define the value of 'R'
    >>> instr.defPar('C', '10n')        # Define the value of 'C'  
    >>> instr.defPar('tau', '1u')       # Define the value of 'tau'
    >>> instr.delPar('f_c')             # Delete the definition of 'f_c'
    >>> print(instr.circuit.parDefs)
    {C: 1.00000000000000e-8, tau: 1.00000000000000e-6, R: tau/C}

.. _defPar:

----------------------------------------------
Assign a value or an expression to a parameter
----------------------------------------------

The method **SLiCAPinstruction.instruction.defPar(*args)** sets the value of a parameter.

.. code-block:: python

    >>> from SLiCAP import *
    >>> prj = initProject('My first RC network') # Initialize a SLiCAP project
    >>> instr = instruction() # Create an instance of an instruction object
    >>> instr.setCircuit('myFirstRCnetwork.cir') # Create a circuit from 'myFirstRCnetwork.cir'
    No errors found for circuit: 'My first RC network' from file: 'myFirstRCnetwork.cir'.

    >>> instr.defPar('R', 'tau/C')      # Define the value of 'R' as :math:`C=\frac{\tau}{C}`
    >>> instr.defPar('C', '10n')        # Define the value of 'C' as :math:`C=10 \cdot 10^{-9}`
    >>> instr.defPar('tau', '1u')       # Define the value of 'tau' as :math:`\tau = 1 \cdot 10^{-6}`
    >>> print(instr.circuit.parDefs)
    {f_c: 1000.00000000000, C: 1.00000000000000e-8, tau: 1.00000000000000e-6, R: tau/C}

.. _defPars:

---------------------------------------------------
Assign values or expressions to multiple parameters
---------------------------------------------------

Multiple parameters can be assigned by passing a dictionary with key-value pairs of parameters as argument of the method **SLiCAPinstruction.instruction.defPar(*args)**:

.. code-block:: python

    >>> from SLiCAP import *
    >>> prj = initProject('My first RC network') # Initialize a SLiCAP project
    >>> instr = instruction() # Create an instance of an instruction object
    >>> instr.setCircuit('myFirstRCnetwork.cir') # Create a circuit from 'myFirstRCnetwork.cir'
    No errors found for circuit: 'My first RC network' from file: 'myFirstRCnetwork.cir'.

    >>> instr.defPars({'R': 'tau/C', 'C': '10n', 'tau': '1u'})
    >>> instr.setSimType('numeric')
    >>> print(instr.getParValue(['R', 'C']))
    {C: 1.00000000000000e-8, R: 100.000000000000}

.. _getPar:

------------------------------------------------------
Get the definition or the numeric value of a parameter
------------------------------------------------------

The method **SLiCAPinstruction.instruction.getParValue(*args)** returns the value of a parameter. If the simulation type (SLiCAPinstruction.instruction.simType) has been set to 'symbolic' it returns the symbolic definition of the parameter. If the simulation type has been set to 'numeric' it returns its value after recursive substitution of all parameter definitions:

.. code-block:: python

    >>> from SLiCAP import *
    >>> prj = initProject('My first RC network') # Initialize a SLiCAP project
    >>> instr = instruction() # Create an instance of an instruction object
    >>> instr.setCircuit('myFirstRCnetwork.cir') # Create a circuit from 'myFirstRCnetwork.cir'
    No errors found for circuit: 'My first RC network' from file: 'myFirstRCnetwork.cir'.

    >>> instr.defPar('R', 'tau/C')      # Define the value of 'R'
    >>> instr.defPar('C', '10n')        # Define the value of 'C'  
    >>> instr.defPar('tau', '1u')       # Define the value of 'tau'
    >>> instr.setSimType('symbolic')
    >>> R_sym_value = instr.getParValue('R')
    >>> print(R_sym_value)
    tau/C
    >>> instr.setSimType('numeric')
    >>> R_num_value = instr.getParValue('R')
    >>> print(R_num_value)
    100.000000000000

.. _getPars:

----------------------------------------------------------------
Get the definitions or the numeric values of multiple parameters
----------------------------------------------------------------

If the argument of the method **SLiCAPinstruction.instruction.getParValues(*args)** is a list with parameter names, this method returns a dict with key-value pairs of those parameters. If the simulation type (SLiCAPinstruction.instruction.simType) has been set to 'symbolic' it returns the symbolic definitions. If the simulation type has been set to 'numeric' it returns the values after recursive substitution of all parameter definitions:

.. code-block:: python

    >>> from SLiCAP import *
    >>> prj = initProject('My first RC network') # Initialize a SLiCAP project
    >>> instr = instruction() # Create an instance of an instruction object
    >>> instr.setCircuit('myFirstRCnetwork.cir') # Create a circuit from 'myFirstRCnetwork.cir'
    No errors found for circuit: 'My first RC network' from file: 'myFirstRCnetwork.cir'.

    >>> instr.defPar('R', 'tau/C')      # Define the value of 'R'
    >>> instr.defPar('C', '10n')        # Define the value of 'C'  
    >>> instr.defPar('tau', '1u')       # Define the value of 'tau'
    >>> instr.setSimType('symbolic')
    >>> R_C = getParValue(['R', 'C'])
    >>> print(R_C)
    {C: 1.00000000000000e-8, R: tau/C}
    >>> instr.setSimType('numeric')
    >>> R_C = instr.getParValue(['R', 'C'])
    >>> print(R_C)
    {C: 1.00000000000000e-8, R: 100.000000000000}
