====================
Work with parameters
====================

.. image:: /img/colorCode.svg


*Circuit parameters* are symbolic variables used in element expressions. There are four ways of assigning values or expressions to these parameters:

#. In the netlist using the SPICE '.PARAM' directives
#. In python using the circuit.defPar() method
#. In python using the 'pardefs' argument in an instruction
#. In python using the specs2circuit() function

Get all circuit parameters
==========================

A list with all circuit parameters can be obtained as follows:

.. code-block:: python

    import SLiCAP as sl
    sl.initProject('My first RC network') # Initialize a SLiCAP project
    # Create a circuit object from an existing netlist:
    cir = sl.makeCircuit(sl.ini.example_path + 'myFirstRCnetwork/cir/myFirstRCnetwork.cir')
    # Print the contents of the dictionary with circuit parameter definitions:
    if len(cir.parDefs.keys()):
        print("\nParameters with definitions:\n")
        for key in cir.parDefs.keys():
            print(key, cir.parDefs[key])
    else: 
        print("\nFound no parameter definitions")
    # Print the contents of the list with parameters that have no definition:
    if len(cir.params):
        print("\nParameters that have no definition:\n")
        for param in cir.params:
            print(param)
    else:
        print("\nFound no parameters without definition")
        
This yields:

.. code-block:: text

    Parameters with definitions:

    R 1000
    C 1/(2*pi*R*f_c)
    f_c 1000

    Found no parameters without definition

Assign a value or an expression to a parameter
==============================================

The method `circuit.defPar() <../reference/SLiCAPprotos.html#SLiCAP.SLiCAPprotos.circuit.defPar>`__ can be used to assign a value or an expression to a parameter.

.. code-block:: python

    import SLiCAP as sl
    sl.initProject('My first RC network') # Initialize a SLiCAP project
    # Create a circuit object from an existing netlist:
    cir = sl.makeCircuit(sl.ini.example_path + 'myFirstRCnetwork/cir/myFirstRCnetwork.cir')
    #
    cir.defPar('R', 'tau/C') # Define R = tau/C
    cir.defPar('C', '10n')   # Define C = 10 nF
    cir.defPar('tau', '1u')  # Define tau = 1 us
    print(cir.parDefs)
    
This yields:

.. code-block:: text

    {R: tau/C, C: 1/100000000, f_c: 1000, tau: 1/1000000}

Assign values or expressions to multiple parameters
===================================================

The method `circuit.defPars() <../reference/SLiCAPprotos.html#SLiCAP.SLiCAPprotos.circuit.defPars>`__ can be used to assign definitions to multiple parameters.

.. code-block:: python

    import SLiCAP as sl
    sl.initProject('My first RC network') # Initialize a SLiCAP project
    # Create a circuit object from an existing netlist:
    cir = sl.makeCircuit(sl.ini.example_path + 'myFirstRCnetwork/cir/myFirstRCnetwork.cir')
    #
    cir.defPars({'R': 'tau/C', 'C': '10n', 'tau': '1u'})
    print(cir.parDefs)
    
This yields the same as above:

.. code-block:: python

    {R: tau/C, C: 1/100000000, f_c: 1000, tau: 1/1000000}

Delete a parameter definition
=============================

You can delete a parameter definition using the method `circuit.delPar() <../reference/SLiCAPprotos.html#SLiCAP.SLiCAPprotos.circuit.delPar>`__ . This method does not delete the circuit parameter itself, it only clears its definition so that it can be used as a symbolic variable.

.. code-block:: python

    import SLiCAP as sl
    sl.initProject('My first RC network') # Initialize a SLiCAP project
    # Create a circuit object from an existing netlist:
    cir = sl.makeCircuit(sl.ini.example_path + 'myFirstRCnetwork/cir/myFirstRCnetwork.cir')
    #
    cir.defPar('R', 'tau/C')    # Define the value of R
    cir.defPar('C', '10n')      # Define the value of C
    cir.defPar('tau', '1/f_c')  # Define the value of tau
    cir.delPar('f_c')           # Delete the definition of f_c
    #
    # Print the contents of the dictionary with circuit parameter definitions:
    if len(cir.parDefs.keys()):
        print("\nParameters with definitions:\n")
        for key in cir.parDefs.keys():
            print(key, cir.parDefs[key])
    else: 
        print("\nFound no parameter definitions")
    # Print the contents of the list with parameters that have no definition:
    if len(cir.params):
        print("\nParameters that have no definition:\n")
        for param in cir.params:
            print(param)
    else:
        print("\nFound no parameters without definition")

This yields:

.. code-block:: text

    Parameters with definitions:

    R tau/C
    C 1/100000000
    tau 1/f_c

    Parameters that have no definition:

    f_c

Get the definition or value of a specific parameter
===================================================

The method `circuit.getParValue() <../reference/SLiCAPprotos.html#SLiCAP.SLiCAPprotos.circuit.getParValue>`__  returns the definition or the evaluated value of a parameter.

If the keyword argument 'substitute' is True (default), all circuit parameter definitions are recursively substituted until a final value or expression is obtained (see `fullSubs <../reference/SLiCAPmath.html#SLiCAP.SLiCAPmath.fullSubs>`__)

If the keyword argument 'numeric' is True (default is False), functions and constants are numerically evaluated in floating poit numbers.

.. code-block:: python

    import SLiCAP as sl

    sl.initProject('My first RC network') # Initialize a SLiCAP project
    # Create a circuit object from an existing netlist:
    cir = sl.makeCircuit(sl.ini.example_path + 'myFirstRCnetwork/cir/myFirstRCnetwork.asc')
    #

    cir.defPar('R', '1/2/pi/f_c/C')    # Define the value of R
    cir.defPar('C', '10n')             # Define the value of C
    cir.defPar('f_c', '1M')            # Define the value of tau

    R_defined           = cir.getParValue('R', substitute=False, numeric=False)
    R_evaluated         = cir.getParValue('R', substitute=True,  numeric=False)
    R_defined_numeric   = cir.getParValue('R', substitute=False, numeric=True)
    R_evaluated_numeric = cir.getParValue('R', substitute=True,  numeric=True)

    print('\nR_defined            :', R_defined)
    print('R_evaluated          :', R_evaluated)
    print('R_defined_numeric    :', R_defined_numeric)
    print('R_evaluated_numeric  :', R_evaluated_numeric)

This yields:

.. code-block:: text

    R_defined            : 1/(2*pi*C*f_c)
    R_evaluated          : 50/pi
    R_defined_numeric    : 0.159154943091895/(C*f_c)
    R_evaluated_numeric  : 15.9154943091895

Get the definitions or evaluated values of multiple parameters
==============================================================

The method `circuit.getParValue() <../reference/SLiCAPprotos.html#SLiCAP.SLiCAPprotos.circuit.getParValue>`__  returns a dictionary with key-value pairs. The keys are the names of the parameters and the values their defenition or evaluation of it. 

If the keyword argument 'substitute' is True (default), for each parameter, all circuit parameter definitions are recursively substituted until a final value or expression is obtained (see `fullSubs <../reference/SLiCAPmath.html#SLiCAP.SLiCAPmath.fullSubs>`__)

If the keyword argument 'numeric' is True (default is False), functions and constants are numerically evaluated in floating point numbers.
    
.. image:: /img/colorCode.svg

