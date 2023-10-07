================
Define a circuit
================

SLiCAP requires a SPICE-like netlist of a circuit as input. It converts a hierarchical netlist into matrix equations with the aid of the 'Modified Nodal Analysis' method.

You can generate a netlist from a schematic drawing program, or by entering it manually in an ASCII editor. 

Netlist generation for SLiCAP is supported for schematics created with:

1. *gSchem* using the corresponding SLiCAP symbol library and the 'gnet-spice-noqsi' netlist plugin
2. *LTSPICE* using the corresponding SLiCAP symbol library

------------------------
Create a circuit netlist
------------------------

Differences between SPICE and SLiCAP netlist
--------------------------------------------

Many schematic capture programs can generate Spice netlist from schematics. However, the netlist syntax for SLiCAP slightly differs from the standard SPICE syntax. The differences are listed in the section `SLiCAP netlist syntax <../syntax/netlist.html>`_. For this reason, the netlist syntax associated with built-in schematic symbols of schematic capture packages needs to be adapted to generate correct SLiCAP netlists.

SLiCAP schematic symbols for LTspice, gschem, and lepton-eda are available in the ``LTspice/``, ``gSchem/symbols/``, and ``lepton-eda/symbols/`` directories in the user install path (default ``~/SLiCAP``).

Automatic generation of a netlist
---------------------------------

SLiCAP can create netlists from schematics created with LTspice (MSWindows, Linux), gSchem (MSWindows, Linux, MAC), and lepton-eda (Linux, MAC).

Below the syntax for generation of the netlist file ``myCircuit.cir`` from the 'gSchem' schematic file ``myCircuit.sch`` or from the 'LTspice' schematic file ``myCircuit.asc`` in the project directory. The title of the circuit needs to be added separately. It will be placed at the beginning of the netlist file and used in the table of contents of html reports.

.. code-block:: python

    >>> # Netlist generation from LTspice schematic files:
    >>> makeNetlist('myCircuit.asc', 'My Circuit Title') # Use the *LTspice* netlister.
    >>> #
    >>> # Netlist generation from gschem, or lepton-eda schematic files:
    >>> #
    >>> makeNetlist('myCircuit.sch', 'My Circuit Title') # Use the *gnet-spice-noqsi* netlister.

Tthe `makeNetlist() <../reference/SLiCAP.html#SLiCAP.SLiCAP.makeNetlist>`_ function inserts a title line at the start of the netlist file.
