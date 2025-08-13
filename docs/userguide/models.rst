================
Work with models
================

.. image:: /img/colorCode.svg

SLiCAP circuit elements have associated network models. Some of these are ``stamp`` models and others are ``expansion models``; see `Devices and built-in models <../syntax/devices.html>`_. Stamp models have a built-in MNA matrix stamp. Expansion models are described as subcircuits, ultimately using devices with stamp models as building blocks. Model expansion takes place during the execution of ``makeCircuit()``.

SLiCAP stamp models
===================

The table below lists the built-in stamp models. For SPICE compatibility, the **Device ID** is the first letter of the device's reference designator. But devices with the same device ID can have different nodels:

.. csv-table::
    :widths: auto
    :header: "Device ID", "Model", "Description"
    
    "C", "C", `Linear capacitor <../syntax/devices.html#model-c>`__ 
    "E", "E", `VCVS (voltage-controlled voltage source) <../syntax/devices.html#model-e>`__ 
    "E", "EZ", `VCVS with output impedance <../syntax/devices.html#model-ez>`__ 
    "F", "F", `CCCS (current-controlled current source) <../syntax/devices.html#model-f>`__ 
    "G", "G", `VCCS (voltage-controlled current source) <../syntax/devices.html#model-g>`__ 
    "G", "g", `VCCS only instantaneous <../syntax/devices.html#gg>`__ 
    "H", "H", `CCVS (current-controlled voltage source) <../syntax/devices.html#model-h>`__ 
    "H", "HZ", `CCVS with series impedance <../syntax/devices.html#model-hz>`__ 
    "I", "I", `Independent current source <../syntax/devices.html#model-i>`__ 
    "K", "K", `Coupling factor <../syntax/devices.html#model-k>`__ 
    "L", "L", `Linear inductor <../syntax/devices.html#model-l>`__ 
    "N", "N", `Nullor <../syntax/devices.html#model-n>`__ 
    "R", "R", `Linear resistor cannot have zero value <../syntax/devices.html#model-r>`__ 
    "R", "r", `Linear resistor can have zero value <../syntax/devices.html#rr>`__
    "T", "T", `Ideal transformer <../syntax/devices.html#model-t>`__ 
    "V", "V", `Independent voltage source <../syntax/devices.html#model-v>`__ 
    "W", "W", `Gyrator <../syntax/devices.html#model-w>`__ 

SLiCAP expansion models
=======================

The table below lists the built-in expansion models. The **Device ID** is the first letter of the device's reference designator. But devices with the same device ID can have different nodels:

.. csv-table::
    :widths: auto
    :header: "Device ID", "Model", "Description"
    
    "D", "D", `Small-signal model PN diode <../syntax/devices.html#d-diode>`__ 
    "J", "J", `Small-signal model JFET <../syntax/devices.html#j-junction-fet>`__ 
    "M", "M", `Small-signal model 4-terminal MOS <../syntax/devices.html#m-4-terminal-mos>`__ 
    "M", "MD", `Small-signal model MOS differential-pair <../syntax/devices.html#model-md>`__ 
    "O", "OV", `Small-signal model voltage-feedback operational amplifier <../syntax/devices.html#model-ov>`__ 
    "O", "OC", `Small-signal model current-feedback operational amplifier <../syntax/devices.html#model-oc>`__ 
    "Q", "QV", `Small-signal model vertical BJT <../syntax/devices.html#model-qv>`__ 
    "Q", "QL", `Small-signal model lateral BJT <../syntax/devices.html#model-ql>`__ 
    "Q", "QD", `Small-signal model BJT differential-pair <../syntax/devices.html#model-qd>`__ 

Model parameters
================

All models, except the **nullor** have model parameters (see `Devices and built-in models <../syntax/devices.html>`_). Model parameters can be passed to the model in three different ways:

#. In the netlist element definition line, after the declaration of the model type:

   .. code-block:: text
   
       O1 out 0 inP inN OV av={1e6/(1+s/(2*pi))} zo=100
       
#. In a netlist model statement

   .. code-block:: text
    
       O1 out 0 inP inN myOpAmp
       
       .model myOpAmp OV av={1e6/(1+s/(2*pi))} zo=100
       
#. In a library file and a call to it in the netlist:

   .. code-block:: text
   
       O1 out 0 inP inN myOpAmp
       .lib myLib.lib
       
   The library file must be stored in the ``lib/`` folder in the project directory. The format of a SLiCAP library file is identical to that of a circuit file:
   
   - The first line will be interpreted as the ``Title``. So don't start it with the line comment symbol: ``*``!
   - The library ends with a ``.end`` command.
   - It comprises definitions of subcircuits, parameters and models.
   
   An example of the syntax of myLib.lib, referred to above:

   .. code-block:: text
   
       "My own SLiCAP model Library"
       *****************************
       * File: myLib.lib
       *
       .model myOpAmp OV av={1e6/(1+s/(2*pi))} zo=100
       *
       .end

The scope of model parameters
-----------------------------

Model parameters on the element definition line override those given model definition line (a netlist line starting with ``.model``). 

The operational amplifier in the netlist device definition line below, obtains all its parameter values from the library definition, except for ``av``. This parameter will be set to :math:`10^6`.

.. code-block:: text

   O1 inP inN out 0 myOpAmp av=1e6
   .lib myLib.lib

SLiCAP model expansion
======================

Expansion models are described as subcircuits. These subcircuits are recusrively expanded or "flattened" until all elements have stamp models. The expanded subcircuit is then included in the parent circuit. This is illustrated below.

SLiCAP output displayed on this manual page, is generated with the script: ``models.py``, imported by ``Manual.py``.

.. literalinclude:: ../models.py
    :linenos:
    :lines: 1-11
    :lineno-start: 1
    
Expanded circuit element data
-----------------------------

The script below creates the circuit object from the kicad schematic file:

.. literalinclude:: ../models.py
    :linenos:
    :lines: 13-14
    :lineno-start: 13    
    
The figure below shows the KiCAD circuit diagram.

.. image:: ../img/ZtoV.svg
    :width: 500 px

The netlist of the circuit:

.. literalinclude:: ../cir/ZtoV.cir

The sub circuit definition of the model ``OV`` is found in ``SLiCAPmodels.lib`` in the folder given in ``ini.main_lib_path``.

.. literalinclude:: ../../SLiCAP/files/lib/SLiCAPmodels.lib
    :linenos:
    :lines: 110-119
    :lineno-start: 110

The script below prints the expanded netlist.

.. literalinclude:: ../models.py
    :linenos:
    :lines: 16-31
    :lineno-start: 16

The result below shows the way in which the operational amplifiers have been replaced with their expanded subcircuits. The expanded circuit only comprises stamp elements and can directly be converted into an MNA matrix.

Below a netlist constructed from element data of the top-level circuit.

.. code-block:: text

    "Low-noise voltage amplifier"
    R1 4 in   R value={R_s} noisetemp={0} noiseflow={0} dcvar={0} dcvarlot={0} 
    R2 1 0   R value={R_a} noisetemp={0} noiseflow={0} dcvar={0} dcvarlot={0} 
    R3 2 1   R value={R_a*(A_1 - 1)} noisetemp={0} noiseflow={0} dcvar={0} dcvarlot={0} 
    R4 in out   R value={R_f} noisetemp={0} noiseflow={0} dcvar={0} dcvarlot={0} 
    R5 2 3   R value={R_b} noisetemp={0} noiseflow={0} dcvar={0} dcvarlot={0} 
    R6 3 out   R value={A_2*R_b} noisetemp={0} noiseflow={0} dcvar={0} dcvarlot={0} 
    V1 4 0   V value={0} noise={0} dc={0} dcvar={0} 
    E_O1 2 0 in 1   EZ value={A_0/(1 + s/(2*pi*p_1))} zo={R_o} 
    Gd_O1 in 1 in 1   g value={0} 
    Gc1_O1 in 0 in 0   g value={0} 
    Gc2_O1 1 0 1 0   g value={0} 
    Cd_O1 in 1   C value={0} vinit={0} 
    Cc1_O1 in 0   C value={0} vinit={0} 
    Cc2_O1 1 0   C value={0} vinit={0} 
    E_O2 out 0 0 3   EZ value={A_0/(1 + s/(2*pi*p_1))} zo={R_o} 
    Gd_O2 0 3 0 3   g value={0} 
    Gc1_O2 0 0 0 0   g value={0} 
    Gc2_O2 3 0 3 0   g value={0} 
    Cd_O2 0 3   C value={0} vinit={0} 
    Cc1_O2 0 0   C value={0} vinit={0} 
    Cc2_O2 3 0   C value={0} vinit={0} 
    .param R_s ={50}
    .end

Reference designators of expanded circuit elements
--------------------------------------------------

.. admonition:: Important
    :class: note
    
    The reference identifiers of the expanded netlist of subcircuits (or expansion models) are those of the parent element extended with ``_<ref_EL>``, where ``ref_EL`` is the reference identifier of the parent element.
    
    Hence, the reference designator of element "Gc1" of operational amplifier "O1" is "Gc1_O1".

Displaying a table with element data in LaTeX documents and on HTML pages
=========================================================================
    
With the aid of the report module `Create reports <reports.html>`_, a table with expanded netlist data can be displayed on HTML pages or in LaTeX documents. 

Below the script for generating the rst snippet for this help file.

.. literalinclude:: ../models.py
    :linenos:
    :lines: 36-40
    :lineno-start: 36
    
Below the expanded netlist table generated with this script.

.. include:: ../sphinx/SLiCAPdata/table-ZtoV_elements.rst

.. image:: /img/colorCode.svg
