=============
Netlist lines
=============

Like with SPICE, a netlist description is organized in lines. The syntax for the symbolic simulator is SPICE compatible.

Since there exist various SPICE dialects, and since symbolic simulation requires a more complex handling of parameters in sub circuits and models, the correct SLiCAP netlist syntax has been described in the following sub sections.

Breaking long lines
-------------------

Long input lines can be split into a multiple of shorter lines. Lines starting with a plus sign ``+`` will be added to the previous line; without the plus sign itself. Leading and trailing white space characters of netlist lines are ignored.

Comment
-------

Any line starting with an asterix: ``*`` is considered as comment and will not be processed by the netlist parser. Any input following a semicolon ``;`` is also considered as comment and ignored.

Numbers
-------

Numeric values can be given in scientific notation: ``0.001 = 1E-3 = 1e-3`` or use metric prefixes: ``2.2k = 2200``. The following metric prefixes can be used:

.. csv-table:: SLiCAP metric prefixes
    :header: "name", "Symbol", "Base 10 value"
    :widths: 50, 10, 20

    "peta", "P", :math:`10^{15}`
    "tera", "T", :math:`10^{12}`
    "giga", "G", :math:`10^{9}`
    "mega", "M", :math:`10^{6}`
    "kilo", "k", :math:`10^{3}`
    "mili", "m", :math:`10^{-3}`
    "micro", "u", :math:`10^{-6}`
    "nano", "n", :math:`10^{-9}`
    "pico", "p", :math:`10^{-12}`
    "femto", "f", :math:`10^{-15}`
    "atto", "a", :math:`10^{-18}`

Please noitice these prefixes are case sentitive, and ``MEG`` and ``meg`` are not recognized as metric prefixes. This differs from the standard SPICE syntax.

From version 0.4 build 1350 the expression syntax checker can handle parameter names identical to metric prefixes. 

Expressions
-----------

As with SPICE, expressions should be placed between curly brackets: ``{< myExpression >}``. Metric prefix symbols, and white space characters can be included in expressions.

Reserved (sympy) symbols and SLiCAP built-in variables
------------------------------------------------------

Reserved symbols have a special meaning or value (within sympy). These symbols **cannot be used as free variables** in expressions:

+---------+-----------------------------------------------------------------+
|variable | Description                                                     |
+=========+=================================================================+
|E        | sympy.E = :math:`2.71828122845905 \cdots`                       |
+---------+-----------------------------------------------------------------+
|I        | sympy.I =  :math:`\sqrt{-1}`                                    |
+---------+-----------------------------------------------------------------+
|N        | sympy.N function; evaluates the numeric value of an expression  |
+---------+-----------------------------------------------------------------+
|O        | sympy.O function                                                |
+---------+-----------------------------------------------------------------+
|S        | sympy.S function                                                |
+---------+-----------------------------------------------------------------+
|beta     | sympy.beta function                                             |
+---------+-----------------------------------------------------------------+
|gamma    | sympy.gamma function                                            |
+---------+-----------------------------------------------------------------+
|lambda   | sympy.lambda function                                           |
+---------+-----------------------------------------------------------------+
|Lambda   | sympy.Lambda function                                           |
+---------+-----------------------------------------------------------------+
|pi       | sympy.pi = :math:`3.1459265358979 \cdots`                       |
+---------+-----------------------------------------------------------------+
|zeta     | sympy.zeta function                                             |
+---------+-----------------------------------------------------------------+

SLiCAP built-in variables are defined in the library file `SLiCAPmodels.lib <../../../../files/lib/SLiCAPmodels.lib>`_. These variables can be redefined by the user:

+--------------+---------------------------------------------------------------------------------------------------------+
|variable      | Description                                                                                             |
+==============+=========================================================================================================+
|c             | SLiCAP built-in variable for the speed of light :math:`c=2.99792458\cdot 10^8` m/s                      |
+--------------+---------------------------------------------------------------------------------------------------------+
|f             | SLiCAP default symbol for frequency in [Hz] (ini.frequency)                                             |
+--------------+---------------------------------------------------------------------------------------------------------+
|k             | SLiCAP built-in variable for Boltzmann's constant: :math:`k=1.38064852\cdot 10^{-23}` J/K               |
+--------------+---------------------------------------------------------------------------------------------------------+
|q             | SLiCAP built-in variable for the charge of an electron: :math:`q=1.60217662\cdot 10^{-19}` C            |
+--------------+---------------------------------------------------------------------------------------------------------+
|s             | SLiCAP default symbol for the Laplace variable (ini.Laplace)                                            |
+--------------+---------------------------------------------------------------------------------------------------------+
|T             | SLiCAP built-in variable for the absolute temperature :math:`T=300` K                                   |
+--------------+---------------------------------------------------------------------------------------------------------+
|U_T           | SLiCAP built-in variable for the thermal voltage: :math:`U_T=\frac{kT}{q}` [V]                          |
+--------------+---------------------------------------------------------------------------------------------------------+
|mu_0          | SLiCAP built-in vriable for the permittivity of vacuum : :math:`\mu_0=4\pi 10^{-7}` H/m                 |
+--------------+---------------------------------------------------------------------------------------------------------+
|epsilon_0     | SLiCAP built-in variable for the permittivity of vacuum: :math:`\epsilon_0=\frac{1}{\mu_0 c^2}` [F/m]   |
+--------------+---------------------------------------------------------------------------------------------------------+
| epsilon_SiO2 | SLiCAP built-in variable for the relative permittivity of :math:`SiO_2` : :math:`\epsilon_{SiO_2}=3.9`  |
+--------------+---------------------------------------------------------------------------------------------------------+

.. _title:

Title line
----------

The title definitions differs from SPICE:

**The first word or a double quoted string of an uncommented line of the netlist file is considered the title of the main circuit.** If a title comprises several words separated by white space characters it should be placed between double quotation marks: ``"``. Examples are listed below.

.. code-block:: text

    * myCircuit         ; a comment, not interpreted as title.

.. code-block:: text

    myCircuit           ; a title without spaces

.. code-block:: text

    "My first circuit"  ; a tittle including spaces
		
.lib line
---------

Library files containing model definitions and/or sub circuit definitions need to be included in the search path with the aid of the ``.lib`` instruction. Multiple library definitions can be included in one ``.lib`` line. Library files containing white space characters should be places between double quotation marks: ``"``. The search path for the library file is specified by the variable ``LIBRARYPATH`` in ``SLiCAPconfig.py`` in the project directory. 

The syntax for library files slightly differs from SPICE: 

- The first line is consideres as tile
- The last line should be ``.end``

In fact, SLiCAP library files have the same syntax as SLiCAP netlist files.

Library definitions should be declared before called. A call to a library occurs if a model name or sub circuit name occurs in an element definition while that model or sub circuit is not specified by a ``.model`` or a ``.subckt`` definition in the netlist itself. Valid library specifications look like:

.. code-block:: text

    .lib myLibrary.lib "my very own circuits.lib"

.. _subckt:

.subckt ... .ends lines
-----------------------

Although SLiCAP is intended for the design and the analysis of rather small circuits, it allows you to use an unlimited hierarchy. It also checks for hierarchical loops. The structure of a sub circuit definition is as follows:

.. code-block:: text

    .subckt < name > 
    + < node1 > < node2 > ( < node3 > ... )
    + ( < param1 = value1 | {expr1} param2 = value2 | {expr2} > ...)
    * circuit lines
    .ends
		
The input field ``name`` and a number of fields with the node names ``node1 node2 ...`` are required. Each parameter definition consists of a parameter name followed by an equal sign and a value or an expression. Parameter definitions should **not** be placed between brackets ``()``.

Passing sub circuit parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Parameters specified in the ``.subckt`` definition line are passed to the parent circuit. Other parameters used in element expressions and in parameter definitions between the ``.subckt`` and its corresponding ``.ends`` input lines remain local. Parameter values can be numerical or may be expressions comprising other parameters. Expressions need to be placed between curly brackets: ``{< myExpression >}``. Input lines between the ``.subckt`` and its corresponding ``.ends`` instruction can be of any type. Hence, nesting of sub circuits is allowed. 

Below an example of a netlist file with a sub circuit definition and a call to this sub circuit. The netlist file with the name ``subckt.cir`` is stored in the project directory. Please notice that this file only demonstrates the use of sub circuits with parameters. It is not at all a complete circuit description.

.. code-block:: text

    testCircuit		
    .subckt myOpamp in+ in- out GND A_0 = {A_1} tau={t} R_o = 0.5k
    E1 1 GND in+ in- {A_0/(1+s*tau)}
    R1 1 out {R_o}
    C1 in+ in- {C_i}
    .param C_i=10p R_o=100
    .ends
    X1 1 2 3 0 myOpamp tau = {t_a} R_o = 200
    .param A_1 = {g_m*Z_t} t_a = 1m g_m=10m Z_t=100M
    .end
		
Parameters given in the ``.subckt`` line are passed to the parent circuit. They can be redefined in the sub circuit call. Hence, ``A_0``, ``tau`` and ``R_o`` become parameters in the parent circuit. They can been assigned new values in the sub circuit call, in this example, this is the line:

.. code-block:: text

    X1 1 2 3 0 myOpamp tau = {t_a} R_o = 200

or in parameter definition lines. In this example this is the line:

.. code-block:: text

    .param A_1 = {g_m*Z_t} t_a = 1m g_m=10m Z_t=100M


All other parameters in expressions and in parameter definitions of the sub circuit remain local. This will be done by adding the device name of the calling device as suffix to the parameter name:

- For nodes a dot ``_`` will be placed between the node name and the device name. 
- For parameters ``_`` will be placed between the parameter name and the device name.

All nodes except the connecting nodes and the ground node ``"0"`` are local.

.model line
-----------

Models can be defined in a line starting with the keyword ``.model`` (not case sensitive). The syntax for a ``.model`` line is:

.. code-block:: text

		.model < modelName > < modelType > 
		+ ( < param1 = value1 | {expr1} > < param2 = value2 | {expr2} > ...)

The fields ``modelName`` and ``modelType`` are required. Parameter definition fields are optional. If no parameter definitions are given, defaults values are assumed. A model name should not start with a number. This would result in misinterpretation by the netlist parser. Hence, a model name like ``2n3904`` could be interpreted as ``2e-9`` followed by ``3904`` which yields a syntax error in a value. Such errors can be prevented using a letter as first character in a model name, e.g. ``Q2n3904``. This is common practice in SPICE. 

Parameter definitions need not to be placed between brackets ``()``. This may differ from some SPICE dialects.

Passing model parameters
~~~~~~~~~~~~~~~~~~~~~~~~

Passing model parameters tworks similar as passing sub circuit parameters. This is elucidated in the example below. Consider hereto the following netlist file with a model definition:

.. code-block:: text

    modelTest
    I1 0 b 1u
    R1 c 0 1k
    Q1 c b 0 0 Q2N3904 gm={I_c*q_e/(k_B*T_A)} gpi={I_c*q_e/(k_B*T_A)/beta_AC}
    .param I_c=2m beta_AC={beta_DC} beta_DC=100
    .model Q2N3904 QV
    .end
		
The model ``QV`` is that of a 4-terminal vertical bipolar transistor. It can be used for a three terminal transistor by connecting the last two terminals (emitter and substrate) to the same circuit node. The built-in model for this device has the following parameters with their default values: ``cpi = 0``, ``cbc = 0``, ``cbx = 0``, ``cs = 0``, ``gpi = 400e-6``, ``gm = 40e-3``, ``go =0``, ``rb = 0``, ``gbc = 0``

The above model definition for the ``Q2N3904`` overrides the values of ``gpi`` and ``gm``, all other parameters obtain their default value. The input resistance and the transconductance of this transistor have been redefined as a function of the collector current ``I_c``. This current has been defined in the line: ``.param I_c=2m beta_AC=beta_DC beta_DC=100``

.param line
-----------

Parameter definition lines are used to assign numerical values or expressions to circuit parameters. At least one parameter definition should be given in a parameter definition line. The syntax for a parameter definition line is:

.. code-block:: text

		.param < param1 = value1 | {expr1} > ( < param2 = value2 | {expr2} ... )
		
Parameters defined in parameter definition lines in sub circuits are local for that sub circuit unless these parameters are passed to the parent circuit.

Device definition lines
-----------------------

The actual circuit is specified by the device definition lines. The syntax for these lines is:

.. code-block:: text

		< deviceID > < node1 | ref1 > < node2 | ref2 > ( < node3 > ...) >
		+ < value | {expr} | modelName > 
		+ ( < param1 = value1 | {expr1} > < param2 = value2 | {expr2} > ...)

A device definition line starts with the device identifier field: ``< deviceID >`` . The first character of name is interpreted as the device type identifier. The device type identifier is not case sensitive. 

Other required fields are: at least two fields with node names or deviceIDs of other devices. If no ``< value | {expr} | modelName >`` field is specified, a default model with default parameter valuess is
assumed. Node names and model names are case sensitive character strings.

A model name is a character string that cannot be interpreted as a number. Expressions need to be placed between curly brackets: ``{}``. A coupling factor device has two references to inductors instead of two nodes.

Parameter definitions can only be given in combination with a model name. If no model parameters are specified, values from a ``.model`` line are assumed. If such a line does not exist, default parameter values are assumed.

Below different ways of defining a resistor R1 of 10kOhm between nodes 1 and 2:

.. code-block:: text

    R1 1 2 10k ; default model (R) will be used

    R1 1 2 R value=10k ; model R: resistor value cannot be zero

    R1 1 2 r value=10k ; model r: resistor value can be zero

    R1 1 2 myR
    .model myR R value=10k

    R1 1 2 myOtherR value=10k
    .model myOtherR R 

.end line
---------
A line starting with ``.end`` concludes the netlist input. Lines following this line are ignored.
