===========================
Devices and built-in models
===========================

.. image:: /img/colorCode.svg

This section gives an overview of the devices and their built-in models with their parameters. SLiCAP distinguishes two kinds of models:

1. Models that have an associated matrix stamp.
2. Models that will be expanded into models with an associated matrix stamp.

Model data will be listed in tables. The fields in these tables have the following meaning:

1. ``name``: the name of the model. This name is associated with the implementation type:
2. ``type``: the implementation type of the model:

	a ``stamp``: a matrix stamp is associated with the model	
	b ``expansion``: the model is expanded into elements with models that have associated matrix stamps

3. ``I``: ``TRUE`` if a dependent variable for a branch current is added to the vector 
with dependent variables else: ``FALSE``. This field applies only for models with ``type=stamp``. The name of this current is ``I_<refdes>``, where ``refdes`` is the reference designator (name) of the device.

Valid model parameters and their default values are listed in the subsequent rows of the table:

1. ``param``: the name of the parameter (case sensitive)
2. ``value | {expression}``: the default value or expression for the model parameter
3. ``Laplace``: a boolean ``TRUE | FALSE`` indicating if the Laplace variable ``s`` is allowed in the parameter expression
4. ``description``: a description of the parameter

C: Capacitor
------------

Below the syntax and the symbol for a capacitor and the matrix stamp for model C_.

.. _C:

Model C
~~~~~~~

.. figure:: ../img/stampC.svg
	 :width: 800px
	 :alt: Syntax, symbol and matrix stamp of a capacitor
	 
	 Figure C: Syntax, symbol and matrix stamp of a capacitor.

+-------+------------------+-------+-------+
| name  | description      | type  | I     |
+=======+==================+=======+=======+
| C     | Linear capacitor | stamp | FALSE |
+-------+------------------+-------+-------+

Parameters model C
~~~~~~~~~~~~~~~~~~

+-------+------------------+---------+---------+
| name  | description      | default | Laplace |
+=======+==================+=========+=========+
| value | capacitance      | 1       | FALSE   | 
+-------+------------------+---------+---------+
| vinit | initial voltage  | 0       | FALSE   | 
+-------+------------------+---------+---------+

Examples
~~~~~~~~

.. code-block:: text

	C1 nodeP nodeN 100n                      ; Capacitor of 100n between nodeP and nodeN

.. code-block:: text

	C1 nodeP nodeN C value = 100n            ; Same as above

.. code-block:: text

	C1 nodeP nodeN C value = 100n vinit = 0  ; Same as above with initial condition (not yet implemented)

.. code-block:: text

	C1 nodeP nodeN {1/tau/R}                 ; Capacitance as an expression

.. code-block:: text

	C1 nodeP nodeN C value = {1/tau/R}       ; Same as above

.. code-block:: text

	C1 nodeP nodeN myCap                     ; Same as above with a .model line
	.model myCap C value={1/tau/R} vinit = 0

D: Diode
--------

Below the syntax, the symbol and the small-signal model expansion for the a diode: model D_.

.. _D:

Model D
~~~~~~~

.. figure:: ../img/modelD.svg
	 :width: 800
	 :alt: Syntax, symbol and small-signal model expansion for a diode
	 
	 Figure D: Syntax, symbol and small-signal model expansion for a diode.

+-------+--------------------------+-----------+
| name  | description              | type      |
+=======+==========================+===========+
| D     | Small-signal model diode | expansion |
+-------+--------------------------+-----------+

Parameters model D
~~~~~~~~~~~~~~~~~~

+-------+--------------------------+---------+---------+
| name  | description              | default | Laplace |
+=======+==========================+=========+=========+
| gd    | conductance              | 1       | FALSE   | 
+-------+--------------------------+---------+---------+
| cd    | capacitance              | 0       | FALSE   | 
+-------+--------------------------+---------+---------+
| rs    | series resistance        | 0       | FALSE   | 
+-------+--------------------------+---------+---------+

Examples
~~~~~~~~

.. code-block:: text

	D1 nodeA nodeC D ; Diode anode connected to nodeA cathode to nodeC and default parameters.
	
.. code-block:: text

	D1 nodeA nodeC D1N4148 
	+ gd = {q_e*I_D/K_b/T_A}
	+ cd = {q_e*I_D/K_b/T_A/2/PI/tau_F}
	+ rs = 25
	.model D1N4148 D
	.param tau_F = 4n I_D = 1m
	
E: Voltage-controlled voltage source
------------------------------------

SLiCAP has two models for voltage-controlled voltage sources: model E_ and model EZ_. The later one includes a series output impedance but has a compact matrix stamp.
		 
Models
~~~~~~

+-------+--------------------+-------+------+
| name  | description        | type  | I    |
+=======+====================+=======+======+
| E     | VCVS               | stamp | TRUE |
+-------+--------------------+-------+------+
| EZ    | VCVS with Z-series | stamp | TRUE |
+-------+--------------------+-------+------+

.. _E:

Model E
~~~~~~~

.. figure:: ../img/stampE.svg
	 :width: 800px
	 :alt: Syntax, symbol and matrix stamp of a VCVS: model E
	 
	 Syntax, symbol and matrix stamp of a VCVS model E
				
Parameters model E
~~~~~~~~~~~~~~~~~~
   
+-------+------------------+---------+---------+
| name  | description      | default | Laplace |
+=======+==================+=========+=========+
| value | voltage gain     | 1       | TRUE    | 
+-------+------------------+---------+---------+

.. _EZ:

Model EZ
~~~~~~~~

.. figure:: ../img/stampEZ.svg
	 :width: 800px
	 :alt: Syntax, symbol and matrix stamp of a VCVS with series impedance: model EZ
	 
	 Syntax, symbol and matrix stamp of a VCVS with series impedance: model EZ

Parameters model EZ
~~~~~~~~~~~~~~~~~~~

+-------+------------------+---------+---------+
| name  | description      | default | Laplace |
+=======+==================+=========+=========+
| value | voltage gain     | 1       | TRUE    | 
+-------+------------------+---------+---------+
| zo    | series impedance | 1       | TRUE    | 
+-------+------------------+---------+---------+

Examples
~~~~~~~~

.. code-block:: text

	E1 outP outN inP inN 1M

.. code-block:: text
	
	E1 outP outN inP inN {1M/(1 + s/2/PI/f_-3dB)}

.. code-block:: text

	E1 outP outN inP inN EZ
	+ value = {A_0/(1 + s*tau)}
	+ zo = {R_out*(1 + s*L_out/R_out}

.. code-block:: text

	E2 outP outN inP inN simpleOpamp
	.model simpleOpamp EZ
	+ value = {A_0/(1 + s*tau)}
	+ zo = {R_out*(1 + s*L_out/R_out}
		
F: Current-controlled current source
------------------------------------

Below the syntax, the symbol and the matrix stamp for a CCCS: model F_. 

.. _F:

Model F
~~~~~~~

.. figure:: ../img/stampF.svg
	 :width: 800px
	 :alt: Syntax, symbol and matrix stamp of a CCCS: model F
	 
	 Syntax, symbol and matrix stamp of a CCCS model F
	 
Please notice the independent variable :math:`I_{Fx}` which is added to the vector of independent variables equals the product of the denominator of the current gain :math:`Df_s` and the input current :math:`Ii_{Fx}`, rather than the input current.

+-------+------------------+-------+------+
| name  | description      | type  | I    |
+=======+==================+=======+======+
| F     | VCVS             | stamp | TRUE |
+-------+------------------+-------+------+

Parameters model F
~~~~~~~~~~~~~~~~~~

+-------+------------------+---------+---------+
| name  | description      | default | Laplace |
+=======+==================+=========+=========+
| value | current gain     | 1       | TRUE    | 
+-------+------------------+---------+---------+

Examples
~~~~~~~~

.. code-block:: text

	F1 outP outN V1 20

.. code-block:: text

	F1 outP outN V1 {100/(1 + s/2/PI/f_-3dB)}

.. code-block:: text

	F1 outP outN V1 F value={A_i/(1 + s*tau)}

.. code-block:: text

	F2 outP outN V1 myCCCS
	.model myCCCS F value = {A_i/(1 + s*tau)}
		
G: Voltage-controlled current source
------------------------------------

SLiCAP has two models for voltage-controlled current sources, model 'G' for a complex transfer and model 'g' for a real transfer. 

Model 'G' can be used for sources that need to be selected as loop gain reference variable according to the asymptotic-gain model. The transadmittance can be a function of the Laplace variable 's'. Model 'g' is intended to be used as conductance or transconductance and cannot be selected a loop gain reference variable.

Models
~~~~~~

+-------+------------------+-------+-------+
| name  | description      | type  | I     |
+=======+==================+=======+=======+
| G     | VCGS             | stamp | TRUE  |
+-------+------------------+-------+-------+
| g     | VCGS             | stamp | FALSE |
+-------+------------------+-------+-------+

.. _G:

Model G
~~~~~~~

.. figure:: ../img/stampG.svg
	 :width: 800px
	 :alt: Syntax, symbol and matrix stamp of a VCCS: model G
	 
	 Syntax, symbol and matrix stamp of a VCCS: model G


Parameters model G
~~~~~~~~~~~~~~~~~~

+-------+------------------+---------+---------+
| name  | description      | default | Laplace |
+=======+==================+=========+=========+
| value | transadmittance  | 1       | TRUE    | 
+-------+------------------+---------+---------+

.. _Gg:

Model g
~~~~~~~

.. figure:: ../img/stampGm.svg
	 :width: 800px
	 :alt: Syntax, symbol and matrix stamp of a VCCS: model g
	 
	 Syntax, symbol and matrix stamp of a VCCS: model g

Parameters model g
~~~~~~~~~~~~~~~~~~

+-------+------------------+---------+---------+
| name  | description      | default | Laplace |
+=======+==================+=========+=========+
| value | transconductance | 1       | FALSE   | 
+-------+------------------+---------+---------+

Examples
~~~~~~~~

.. code-block:: text

	G1 outP outN inP inN 20m

.. code-block:: text

	G1 outP outN inP inN {1m/(1 + s/2/PI/f_-3dB)}

.. code-block:: text

	G1 outP outN inP inN G value = {A_y/(1 + s*tau)}

.. code-block:: text

	G2 outP outN inP inN myVCCS
	.model myVCCS G valu e= {A_y/(1 + s*tau)}

.. code-block:: text

	G3 outP outN inP inN g value = 1m

.. code-block:: text

	G3 outP outN inP inN g value = {q*I_c/k/T}
	
H: Current-controlled voltage source
------------------------------------

SLiCAP has two models for current-controlled voltage sources: model H_ and model HZ_. The later one includes a series output impedance but has a compact matrix stamp.

Models
~~~~~~

+-------+--------------------+-------+------+
| name  | description        | type  | I    |
+=======+====================+=======+======+
| H     | CCVS               | stamp | TRUE |
+-------+--------------------+-------+------+
| HZ    | CCVS with Z-series | stamp | TRUE |
+-------+--------------------+-------+------+

.. _H:

Model H
~~~~~~~

.. figure:: ../img/stampH.svg
	 :width: 800px
	 :alt: Syntax, symbol and matrix stamp of a CCVS: model H
	 
	 Syntax, symbol and matrix stamp of a CCVS model H
		
Parameters model H
~~~~~~~~~~~~~~~~~~

+-------+------------------+---------+---------+
| name  | description      | default | Laplace |
+=======+==================+=========+=========+
| value | transimpedance   | 1       | TRUE    | 
+-------+------------------+---------+---------+

.. _HZ:

Model HZ
~~~~~~~~

.. figure:: ../img/stampHZ.svg
	 :width: 800px
	 :alt: Syntax, symbol and matrix stamp of a CCVS with series impedance: model HZ
	 
	 Syntax, symbol and matrix stamp of a CCVS with series impedance: model HZ
		
Parameters model HZ
~~~~~~~~~~~~~~~~~~~

+-------+------------------+---------+---------+
| name  | description      | default | Laplace |
+=======+==================+=========+=========+
| value | transimpedance   | 1       | TRUE    | 
+-------+------------------+---------+---------+
| zo    | series impedance | 1       | TRUE    | 
+-------+------------------+---------+---------+

Examples
~~~~~~~~

.. code-block:: text

	H1 outP outN V1 1M

.. code-block:: text

	H1 outP outN V1 {1M/(1 + s/2/PI/f_-3dB)}	

.. code-block:: text

	H1 outP outN inP inN HZ
	+ value = {R_T/(1 + s*tau)}
	+ zo = {R_out*(1 + s*L_out/R_out}

.. code-block:: text

	H2 outP outN V1 simpleTransimpedanceAmp
	.model simpleTransimpedanceAmp HZ
	+ value = {R_T/(1 + s*tau)}
	+ zo = {R_out*(1 + s*L_out/R_out}	
		
I: Independent current source
-----------------------------

Below the syntax, the symbol and the matrix stamp for an independent current source: model I_.

.. _I:

Model I
~~~~~~~

.. figure:: ../img/stampI.svg
	 :width: 800px
	 :alt: Syntax, symbol and matrix stamp of an independent current source: model I
	 
	 Syntax, symbol and matrix stamp of an independent current source: model I

+-------+----------------------------+-------+-------+
| name  | description                | type  | I     |
+=======+============================+=======+=======+
| I     | Independent current source | stamp | FALSE |
+-------+----------------------------+-------+-------+
		
Parameters model I
~~~~~~~~~~~~~~~~~~

+-------+--------------------------------+---------+---------+
| name  | description                    | default | Laplace |
+=======+================================+=========+=========+
| value | Current (Laplace transform)    | 0       | TRUE    | 
+-------+--------------------------------+---------+---------+
| dc    | DC value              [A]      | 0       | FALSE   | 
+-------+--------------------------------+---------+---------+
| dcvar | Variance of DC value  [A^2]    | 0       | FALSE   | 
+-------+--------------------------------+---------+---------+
| noise | Noise current density [A^2/Hz] | 0       | FALSE   | 
+-------+--------------------------------+---------+---------+

Examples
~~~~~~~~

.. code-block:: text
		
	* Both definitions are equivalent:
	I1 n1 n2 1m
	I1 n1 n2 I value = 1m

.. code-block:: text

	Iin 0 input I value = {I_s} noise = 1e-24 dc=10n dcvar = 4e-18
	.param I_s = {1m/s}; Step of 1mA starting at t=0

J: Junction FET
---------------

Like the PN diode, the JFET model J_ is expanded into network elements that have a matrix stamp.

.. _J:

Model J
~~~~~~~

.. figure:: ../img/modelJ.svg
	 :width: 800
	 :alt: Syntax, symbol and network expansion of a junction FET: model J
	 
	 Syntax, symbol and network expansion of a junction FET: model J

+-------+--------------------------+-----------+
| name  | description              | type      |
+=======+==========================+===========+
| J     | Small-signal model JFET  | expansion |
+-------+--------------------------+-----------+
		
Parameters model J
~~~~~~~~~~~~~~~~~~
		
+-------+--------------------------+---------+---------+
| name  | description              | default | Laplace |
+=======+==========================+=========+=========+
| cgs   | contactance              | 0       | FALSE   | 
+-------+--------------------------+---------+---------+
| cdg   | capacitance              | 0       | FALSE   | 
+-------+--------------------------+---------+---------+
| gm    | forward transconductance | 1E-3    | FALSE   | 
+-------+--------------------------+---------+---------+
| go    | output conductance       | 0       | FALSE   | 
+-------+--------------------------+---------+---------+	

Examples
~~~~~~~~

.. code-block:: text

    J1 nodeD nodeG nodeS myJFET
    .model myJFET J cgs=20p cdg=1p gm=15m go=500u		

K: Coupling factor
------------------

Below the syntax, the symbol and the matrix stamp for a coupling between two inductors: model K_.

.. _K:

Model K
~~~~~~~

.. figure:: ../img/stampK.svg
	 :width: 800px
	 :alt: Syntax, symbol and matrix stamp of a coupling between two inductors: model K
	 
	 Syntax, symbol and matrix stamp of a coupling between two inductors: model K

+-------+------------------+-------+-------+
| name  | description      | type  | I     |
+=======+==================+=======+=======+
| K     | Coupling factor  | stamp | FALSE |
+-------+------------------+-------+-------+
		
Parameters model K
~~~~~~~~~~~~~~~~~~

+-------+------------------+---------+---------+
| name  | description      | default | Laplace |
+=======+==================+=========+=========+
| value | coupling factor  | 1       | FALSE   | 
+-------+------------------+---------+---------+

Examples
~~~~~~~~

.. code-block:: text

	L1 n1 n2 {L_a}
	L2 n3 n4 {L_b}
	k12 L1 L2 0.98	

L: Inductor
-----------

Below the syntax, the symbol and the matrix stamp for an inductor: model L_.

.. _L:

Model L:
~~~~~~~~

.. figure:: ../img/stampL.svg
	 :width: 800px
	 :alt: Syntax, symbol and matrix stamp of an inductor: model L
	 
	 Syntax, symbol and matrix stamp of an inductor: model L

+-------+------------------+-------+------+
| name  | description      | type  | I    |
+=======+==================+=======+======+
| L     | Linear inductor  | stamp | TRUE |
+-------+------------------+-------+------+
		
Parameters model L
~~~~~~~~~~~~~~~~~~

+-------+-------------------+---------+---------+
| name  | description       | default | Laplace |
+=======+===================+=========+=========+
| value | inductance        | 1       | FALSE   | 
+-------+-------------------+---------+---------+
| iinit | initial condition | 0       | FALSE   | 
+-------+-------------------+---------+---------+

Examples
~~~~~~~~

.. code-block:: text

	L1 n1 n2 {L_a}

.. code-block:: text

	L1 n1 n2 L value = {L_a}

.. code-block:: text

	L1 n1 n2 L myL
	.model myL L value = {L_a}	

.. code-block:: text

	L1 n1 n2 L myL
	.model myL L value = {L_a} iinit = 0	

M: 4-terminal MOS
-----------------

SLiCAP has two models for 4-terminal MOS transistors. Model M_ for a single MOS transistor and model MD_ for a differential-pair MOS. The latter one facilitates the design and analysis of negative-feedback amplifiers in which one controlled source that models the gain of the differential-pair MOS can be selected as loop gain reference variable.

Models
~~~~~~

+-------+------------------------------+-----------+
| name  | description                  | type      |
+=======+==============================+===========+
| M     | Four-terminal MOS            | expansion |
+-------+------------------------------+-----------+
| MD    | Four-terminal diff. pair MOS | expansion |
+-------+------------------------------+-----------+

.. _M:
		
Model M
~~~~~~~

.. figure:: ../img/modelM.svg
	 :width: 800
	 :alt: Syntax, symbol and network expansion of a 4-terminal MOS: model M
	 
	 Syntax, symbol and network expansion of a 4-terminal MOS: model M
		
Parameters model M
~~~~~~~~~~~~~~~~~~
		
+-------+--------------------------+---------+---------+
| name  | description              | default | Laplace |
+=======+==========================+=========+=========+
| cgs   | gate-source capacitance  | 0       | FALSE   | 
+-------+--------------------------+---------+---------+
| cgb   | gate-bulk capacitance    | 0       | FALSE   | 
+-------+--------------------------+---------+---------+
| cdg   | drain-gate capacitance   | 0       | FALSE   | 
+-------+--------------------------+---------+---------+
| cdb   | drain-bulk capacitance   | 0       | FALSE   | 
+-------+--------------------------+---------+---------+
| csb   | source-bulk capacitance  | 0       | FALSE   | 
+-------+--------------------------+---------+---------+
| gm    | forward transconductance | 1E-3    | FALSE   | 
+-------+--------------------------+---------+---------+
| gb    | bulk transconductance    | 0       | FALSE   | 
+-------+--------------------------+---------+---------+
| go    | output conductance       | 0       | FALSE   | 
+-------+--------------------------+---------+---------+
		

.. _MD:	

Model MD
~~~~~~~~

.. figure:: ../img/modelMD.svg
	 :width: 800
	 :alt: Syntax, symbol and network expansion of a 4-terminal MOS: model MD
	 
	 Syntax, symbol and network expansion of a 4-terminal MOS: model MD
			 
Parameters model MD
~~~~~~~~~~~~~~~~~~~
		
+-------+--------------------------+---------+---------+
| name  | description              | default | Laplace |
+=======+==========================+=========+=========+
| cgg   | gate-gate capacitance    | 0       | FALSE   | 
+-------+--------------------------+---------+---------+
| cdg   | drain-gate capacitance   | 0       | FALSE   | 
+-------+--------------------------+---------+---------+
| cdd   | drain-drain capacitance  | 0       | FALSE   | 
+-------+--------------------------+---------+---------+
| gm    | forward transconductance | 1E-3    | FALSE   | 
+-------+--------------------------+---------+---------+
| go    | output conductance       | 0       | FALSE   | 
+-------+--------------------------+---------+---------+

Examples
~~~~~~~~

Below three ways of defining a MOS in a circuit. The first example calls the mos model M with its default parameters and then overrides these parameters by local definitions in the call. The model parameter ``gm`` is passed as global parameter ``gm``.

.. code-block:: text

	M1 D G S B M gm={g_m} gb = 150u go = 100u cgs = 0.2p cdg = 10f
		
The second example calls the model from a library file and redefines ``g_m`` as a global parameter.

.. code-block:: text

	M1 D G S B myMOS gm = {g_m}
	.include myMOS.lib
		
The third example calls a model and its parameters. For a given process, geometry and device operating point, these small-signal parameters can be obtained from a SPICE simulation.

.. code-block:: text

	M1 D G S B M1
	.model M1 M gm = 2m gb = 150u go = 100u cgs = 0.2p cdg = 10f
		
The next example shows the application of a differential-pair MOS.

.. code-block:: text

	M1 D1 D2 G1 G2 myDiffPairMOS
	*parameters of the single MOS
	.param g_m = 1m g_o = 100u c_gs = 0.2p c_dg = 10f c_db = 5f
	*parameters of the diff. pair MOS
	.model myDiffPairMOS MD
	+ gm  = {g_m/2}
	+ go  = {g_o/2}
	+ cgg = {c_gs/2}
	+ cdg = {c_dg}
	+ cdd = {c_db/2}

N: Nullor
---------

.. _N:

Model N
~~~~~~~

.. figure:: ../img/stampN.svg
	 :width: 800
	 :alt: Syntax, symbol and matrix stamp of a nullor: model N
	 
	 Syntax, symbol and matrix stamp of a nullor: model N

+-------+----------------------------+-------+------+
| name  | description                | type  | I    |
+=======+============================+=======+======+
| N     | Nullor                     | stamp | TRUE |
+-------+----------------------------+-------+------+

Examples
~~~~~~~~

.. code-block:: text

	N_amp out 0 in+ in-
		
O: Operational amplifier
------------------------

SLiCAP has two built-in models for operational amplifiers:

1. A small-signal model for a voltage-feedbackoperational amplifier: model OV
2. A small-signal model for a current-feedback operational amplifier: model OC

Models
~~~~~~

+-------+------------------------------+-----------+
| name  | description                  | type      |
+=======+==============================+===========+
| OV    | Voltage-feedback OpAmp       | expansion |
+-------+------------------------------+-----------+
| OC    | Current-feedback OpAmp       | expansion |
+-------+------------------------------+-----------+

.. _OV:

Model OV
~~~~~~~~

.. figure:: ../img/modelOV.svg
	 :width: 800
	 :alt: Syntax, symbol and network expansion of a voltage-feedback operational amplifier: model OV
	 
	 Syntax, symbol and network expansion of a voltage-feedback operational amplifier: model OV

Parameters model OV
~~~~~~~~~~~~~~~~~~~
		
+------+--------------------------------------+---------+---------+
| name  | description                         | default | Laplace |
+======+======================================+=========+=========+
| cd   | differential-mode input capacitance  | 0       | FALSE   | 
+------+--------------------------------------+---------+---------+
| cc   | common-mode input capacitance        | 0       | FALSE   | 
+------+--------------------------------------+---------+---------+
| gd   | differential-mode input conductance  | 0       | FALSE   | 
+------+--------------------------------------+---------+---------+
| gc   | common-mode input conductance        | 0       | FALSE   | 
+------+--------------------------------------+---------+---------+
| av   | voltage gain                         | 1E6     | TRUE    | 
+------+--------------------------------------+---------+---------+
| zo   | output impedance                     | 0       | TRUE    | 
+------+--------------------------------------+---------+---------+
		
.. _OC:

Model OC
~~~~~~~~

.. figure:: ../img/modelOC.svg
	 :width: 800
	 :alt: Syntax, symbol and network expansion of a current-feedback operational amplifier: model OC
	 
	 Syntax, symbol and network expansion of a current-feedback operational amplifier: model OC
		
Parameters model OC
~~~~~~~~~~~~~~~~~~~
		
+------+---------------------------------------+---------+---------+
| name | description                           | default | Laplace |
+======+=======================================+=========+=========+
| cp   | input capacitance non-inverting input | 0       | FALSE   | 
+------+---------------------------------------+---------+---------+
| gp   | input conductance non-inverting input | 0       | FALSE   | 
+------+---------------------------------------+---------+---------+
| cpn  | input capacitance                     | 0       | FALSE   | 
+------+---------------------------------------+---------+---------+
| gpn  | input conductance                     | 0       | FALSE   | 
+------+---------------------------------------+---------+---------+
| gm   | input stage transconductance          | 20E-3   | FALSE   | 
+------+---------------------------------------+---------+---------+
| zt   | output stage transimpedance           | 1E6     | TRUE    | 
+------+---------------------------------------+---------+---------+
| zo   | output impedance                      | 0       | TRUE    | 
+------+---------------------------------------+---------+---------+

Examples
~~~~~~~~

.. code-block:: text

	O1 inP inN out 0 AD8610
	.model AD8610 OV
	+ cd = 15p
	+ cc = 8p
	+ av = {300k*(1-s*1.3n)/(1+s*2.4m)/(1+s*1.3n)}
	+ zo = 20	

.. code-block:: text
		
	O1 inP inN out 0 LT1223
	.model LT1223 OC
	+ cp = 1.5p
	+ gp = 100n
	+ gm = 65m
	+ zt = {5M/(1+s*680u)/(1+s*1.6n)}
	+ zo = 30	
		
Q: 4-terminal BJT
-----------------

SLiCAP incorporates three models for 4-terminal Bipolar Junction Transistors (BJTs):

1. Model QV_ for a single vertical BJT
2. Model QL_ for a single lateral BJT
3. Model QD_ for a differential pair.
		
		The latter one facilitates the design and analysis of negative-feedback amplifiers in which one controlled source that models the gain of the differential-pair BJT can be selected as loop gain reference variable.

Models
~~~~~~

+-------+------------------------------+-----------+
| name  | description                  | type      |
+=======+==============================+===========+
| QV    | Four-terminal vertical BJT   | expansion |
+-------+------------------------------+-----------+
| QL    | Four-terminal lateral BJT    | expansion |
+-------+------------------------------+-----------+
| QD    | Four-terminal diff. pair BJT | expansion |
+-------+------------------------------+-----------+

.. _QV:

Model QV
~~~~~~~~

.. figure:: ../img/modelQV.svg
	:width: 800
	:alt: SLiCAP built-in model for a 4-terminal vertical BJT: model QV

	SLiCAP built-in model for a 4-terminal vertical BJT: model QV

Parameters model QV
~~~~~~~~~~~~~~~~~~~
		
+-------+-------------------------------------+---------+---------+
| name  | description                         | default | Laplace |
+=======+=====================================+=========+=========+
| cpi   | internal base-emitter capacitance   | 0       | FALSE   | 
+-------+-------------------------------------+---------+---------+
| cbc   | internal base-collector capacitance | 0       | FALSE   | 
+-------+-------------------------------------+---------+---------+
| cbx   | external base-collector capacitance | 0       | FALSE   | 
+-------+-------------------------------------+---------+---------+
| cs    | collector-substrate capacitance     | 0       | FALSE   | 
+-------+-------------------------------------+---------+---------+
| gpi   | internal base-emitter conductance   | 1E-3    | FALSE   | 
+-------+-------------------------------------+---------+---------+
| gm    | transconductance                    | 0       | FALSE   | 
+-------+-------------------------------------+---------+---------+
| go    | output conductance                  | 0       | FALSE   | 
+-------+-------------------------------------+---------+---------+
| gbc   | internal base-collector conductance | 0       | FALSE   | 
+-------+-------------------------------------+---------+---------+
| rb    | base resistance                     | 0       | FALSE   | 
+-------+-------------------------------------+---------+---------+

.. _QL:

Model QL
~~~~~~~~

.. figure:: ../img/modelQL.svg
		:width: 800
		:alt: SLiCAP built-in model for a 4-terminal lateral BJT: model QL

		SLiCAP built-in model for a 4-terminal lateral BJT: model QL
   	
Parameters model QL
~~~~~~~~~~~~~~~~~~~
		
+-------+-------------------------------------+---------+---------+
| name  | description                         | default | Laplace |
+=======+=====================================+=========+=========+
| cpi   | internal base-emitter capacitance   | 0       | FALSE   | 
+-------+-------------------------------------+---------+---------+
| cbc   | internal base-collector capacitance | 0       | FALSE   | 
+-------+-------------------------------------+---------+---------+
| cbx   | external base-collector capacitance | 0       | FALSE   | 
+-------+-------------------------------------+---------+---------+
| cs    | base-substrate capacitance          | 0       | FALSE   | 
+-------+-------------------------------------+---------+---------+
| gpi   | internal base-emitter conductance   | 1E-3    | FALSE   | 
+-------+-------------------------------------+---------+---------+
| gm    | transconductance                    | 0       | FALSE   | 
+-------+-------------------------------------+---------+---------+
| go    | output conductance                  | 0       | FALSE   | 
+-------+-------------------------------------+---------+---------+
| gbc   | internal base-collector conductance | 0       | FALSE   | 
+-------+-------------------------------------+---------+---------+
| rb    | base resistance                     | 0       | FALSE   | 
+-------+-------------------------------------+---------+---------+
		
.. _QD:

Model QD
~~~~~~~~

.. figure:: ../img/modelQD.svg
		:width: 800
		:alt: SLiCAP built-in model for a differential-pair BJT: model QD

		SLiCAP built-in model for a differential-pair BJT: model QD
		
Parameters model QD
~~~~~~~~~~~~~~~~~~~
		
+-------+-------------------------------------+---------+---------+
| name  | description                         | default | Laplace |
+=======+=====================================+=========+=========+
| cbb   | internal base-base capacitance      | 0       | FALSE   | 
+-------+-------------------------------------+---------+---------+
| cbc   | internal base-collector capacitance | 0       | FALSE   | 
+-------+-------------------------------------+---------+---------+
| cbx   | external base-collector capacitance | 0       | FALSE   | 
+-------+-------------------------------------+---------+---------+
| gbb   | internal base-base conductance      | 0       | FALSE   | 
+-------+-------------------------------------+---------+---------+
| gm    | forward transconductance            | 1E-3    | FALSE   | 
+-------+-------------------------------------+---------+---------+
| gcc   | colector-collector conductance      | 0       | FALSE   | 
+-------+-------------------------------------+---------+---------+
| gbc   | internal base-colector conductance  | 0       | FALSE   | 
+-------+-------------------------------------+---------+---------+
| rb    | base resistance                     | 0       | FALSE   | 
+-------+-------------------------------------+---------+---------+

Examples
~~~~~~~~

Below a specification of a BJT of which the model parameters are expressed in SPICE model parameters, the operating point current ``I_C`` and the operating voltage ``V_CE``. The expressions are simplifications of the nonlinear device equations for a bipolar transistor.

.. code-block:: text

	Q1 C B E S QV
	+ gm  = {g_m}
	+ gpi = {g_m/beta_F}
	+ go  = {(I_c+V_ce)/VAF}
	+ cbc = {c_bc}
	+ cbx = {c_bx}
	+ cpi = {(CJE + TAUF*g_m)}
	+ rb  = {r_b}
	+ gbc = {g_bc}
	.param gm = I_c/U_T

Below a specification of a BJT that uses small-signal parameters in an operating point as they can be determined with the aid of a SPICE operating point simulation.

.. code-block:: text

	Q1 C B E S Q1
	.model Q1 QV 
	+ gm  = 20m 
	+ rb  = 50 
	+ go  = 10u 
	+ gbc = 0 
	+ cpi = 2p 
	+ cbc = 0.05p 
	+ cbx = 0.05p
	+ cs  = 0.2p
		
Below a specification of a lateral BJT that uses small-signal parameters in an operating point as they can be determined with the aid of a SPICE operating point simulation.

.. code-block:: text

	Q1 C B E S Q1
	.model Q1 QL 
	+ gm=20m 
	+ rb=50 
	+ go=10u 
	+ gbc=0 
	+ cpi=2p 
	+ cbc=0.05p 
	+ cbx=0.05p
	+ cs=0.2p

Below an example of a differential pair BJT of which the parameters are related to those of the single transistor stage, biased in the same operating point as the transistors of the differential pair.

.. code-block:: text

	Q1 C1 C2 B1 B2 myDiffPairBJT
	.model myDiffPairBJT QD
	+ gm  = {I_c/2/U_T}
	+ gpi = {I_c/2/U_T/beta_AC}
	+ go  = {2*(I_c+V_ce)/V_AF}
	+ cbc = {c_bc}
	+ cbx = {c_bx}
	+ cpi = {(CJE + TAUF*I_c/U_T)/2}
	+ rb  = {r_b}
	* below the device parameters of the single transistor
	.param r_b = 50 V_AF=50 g_bc = 0 CJE = 2p c_bc = 0.05p c_bx = 0.05p beta_AC=100
	* below the operating point the single transistor
	.param I_c = 1m V_ce=5

R: Resistor
-----------

The default model type for a resistor is ``R``. Zero value for its resistance causes a divide by zero error while building the matrix. If zero value is required, e.g. because of parameter stepping, model ``r`` should be used.

Models
~~~~~~

+-------+--------------------------+-------+-------+
| name  | description              | type  | I     |
+=======+==========================+=======+=======+
| R     | Resistor resistance > 0  | stamp | FALSE |
+-------+--------------------------+-------+-------+
| r     | Resistor resistance >= 0 | stamp | TRUE  |
+-------+--------------------------+-------+-------+
		
.. _R:

Model R
~~~~~~~

.. figure:: ../img/stampR.svg
	 :width: 800
	 :alt: Syntax, symbol and matrix stamp of a resistor: model R
	 
	 Syntax, symbol and matrix stamp of a resistor: model R

Parameters model R
~~~~~~~~~~~~~~~~~~

+-----------+-----------------------------+---------+---------+
| name      | description                 | default | Laplace |
+===========+=============================+=========+=========+
| value     | resistance                  | 1       | FALSE   | 
+-----------+-----------------------------+---------+---------+
| dcvar     | variance                    | 0       | FALSE   | 
+-----------+-----------------------------+---------+---------+
| dcvarlot  | variance of lot             | 0       | FALSE   | 
+-----------+-----------------------------+---------+---------+
| noisetemp | noise temperature           | 0       | FALSE   | 
+-----------+-----------------------------+---------+---------+
| noiseflow | corner frequency 1/f noise  | 0       | FALSE   | 
+-----------+-----------------------------+---------+---------+
| dcvar     | variance                    | 0       | FALSE   | 
+-----------+-----------------------------+---------+---------+
		
.. _Rr:

Model r
~~~~~~~

.. figure:: ../img/stampRr.svg
	 :width: 800
	 :alt: Syntax, symbol and matrix stamp of a resistor: model r
	 
	 Syntax, symbol and matrix stamp of a resistor: model r
	
Parameters model r
~~~~~~~~~~~~~~~~~~

+-----------+-----------------------------+---------+---------+
| name      | description                 | default | Laplace |
+===========+=============================+=========+=========+
| value     | resistance                  | 1       | FALSE   | 
+-----------+-----------------------------+---------+---------+
| dcvar     | variance                    | 0       | FALSE   | 
+-----------+-----------------------------+---------+---------+
| dcvarlot  | variance of lot             | 0       | FALSE   | 
+-----------+-----------------------------+---------+---------+
| noisetemp | noise temperature           | 0       | FALSE   | 
+-----------+-----------------------------+---------+---------+
| noiseflow | corner frequency 1/f noise  | 0       | FALSE   | 
+-----------+-----------------------------+---------+---------+
| dcvar     | variance                    | 0       | FALSE   | 
+-----------+-----------------------------+---------+---------+

Examples
~~~~~~~~

The examples below illustrates four different ways for specifying a resistor that is connected between the nodes nP and nN and has a numerical value of 10kOhm.

.. code-block:: text

	R1 nP nN R value = {R} noiseTemp = {T} noiseflow ={f_ell} dcvar = {sigma_R^2}

.. code-block:: text

	R1 nP nN {20 * alpha}

.. code-block:: text

	R1 nP nN r value = {R_a} dcvar = {sigma^2}

.. code-block:: text

	R1 nP nN myR
	.model myR R value = {20 * alpha}
	.param alpha = 500
			
T: Ideal transformer
--------------------

SLiCAP has a built-in model for an ideal transformer.

.. _T:

Model T
~~~~~~~

.. figure:: ../img/stampT.svg
	 :width: 800
	 :alt: Syntax, symbol and matrix stamp of an ideal transformer: model T
	 
	 Syntax, symbol and matrix stamp of an ideal transformer: model T

+-------+--------------------------+-------+------+
| name  | description              | type  | I    |
+=======+==========================+=======+======+
| T     | Ideal transformer        | stamp | TRUE |
+-------+--------------------------+-------+------+
				
Parameters model T
~~~~~~~~~~~~~~~~~~

+-------+------------------+---------+---------+
| name  | description      | default | Laplace |
+=======+==================+=========+=========+
| value | turns ratio      | 1       | FALSE   | 
+-------+------------------+---------+---------+

Examples
~~~~~~~~

.. code-block:: text

	T1 secP secN priP priN {Vpri/Vsec}

.. code-block:: text

	T1 secP secN priP priN T value={Vpri/Vsec}

.. code-block:: text

	T1 secP secN priP priN myTrafo

.. code-block:: text

	.model myTrafo T value={Vpri/Vsec}		
		
V: Independent voltage source
-----------------------------
	
.. _V:

Model V
~~~~~~~
				
.. figure:: ../img/stampV.svg
	 :width: 800
	 :alt: Symbol, syntax and matrix stamp of an ideal independent voltage source: model V
	 
	 Symbol, syntax and matrix stamp of an ideal independent voltage source: model V

+-------+--------------------------------------------------+-------+------+
| name  | description                                      | type  | I    |
+=======+==================================================+=======+======+
| V     | Independent voltage source                       | stamp | TRUE |
+-------+--------------------------------------------------+-------+------+
   
Parameters model V
~~~~~~~~~~~~~~~~~~

+-------+--------------------------------+---------+---------+
| name  | description                    | default | Laplace |
+=======+================================+=========+=========+
| value | Voltage (Laplace transform)    | 0       | TRUE    | 
+-------+--------------------------------+---------+---------+
| dc    | DC value                       | 0       | FALSE   | 
+-------+--------------------------------+---------+---------+
| dcvar | Variance of DC value  [V^2]    | 0       | FALSE   | 
+-------+--------------------------------+---------+---------+
| noise | Noise voltage density [V^2/Hz] | 0       | FALSE   | 
+-------+--------------------------------+---------+---------+
		
Examples
~~~~~~~~

.. code-block:: text
		
	* Both definitions are equivalent:
	V1 n1 n2 20m
	V1 n1 n2 V value = 20m

.. code-block:: text

	Vin 0 input V value = {V_s} noise = 1e-16 dc = 0 dcvar = 1e-4
	.param V_s = {1/s}; Step of 1V starting at t = 0

W: Gyrator
----------

SLiCAP is often used for conceptual design. For this reason the gyrator has been included.

.. _W:

Model W
~~~~~~~

.. figure:: ../img/stampW.svg
	 :width: 800
	 :alt: Syntax, symbol and matrix stamp of a gyrator: model W

+-------+--------------------------+-------+-------+
| name  | description              | type  | I     |
+=======+==========================+=======+=======+
| W     | Gyrator                  | stamp | FALSE |
+-------+--------------------------+-------+-------+

Parameters model W
~~~~~~~~~~~~~~~~~~

+-------+------------------+---------+---------+
| name  | description      | default | Laplace |
+=======+==================+=========+=========+
| value | transconductance | 1       | FALSE   | 
+-------+------------------+---------+---------+

Examples
~~~~~~~~

Below two definitions of a gyrator with a conversion gain of 10mA/V.

.. code-block:: text

	W1 outP outN inP inN 10m

.. code-block:: text

	W1 outP outN inP inN W value = 10m

X: Sub circuit call
-------------------

See examples in section: :ref:`subckt`.
