======================
Interface with NGspice
======================

.. image:: ../img/colorCode.svg

SLiCAP offers a simple interface for running basic NGspice simulations and plot graphs from within your SLiCAP application. It requires installation of:

#. NGspice for circuit simulation

   - `NGspice <https://ngspice.sourceforge.io/>`_
   - `NGspice manual <https://ngspice.sourceforge.io/docs/ngspice-manual.pdf>`_
   
#. KiCAD for creating circuit diagrams with symbols from the KiCAD SPICE symbol library

Supported analysis
==================

The function `ngspice2traces() <../reference/SLiCAPngspice.html#SLiCAP.SLiCAPngspice.ngspice2traces>`__ creates `SLiCAPplots.trace <../reference/SLiCAPplots.html#SLiCAP.SLiCAPplots.trace>`__ objects that can be plotted with the `SLiCAPplots.plot() <../reference/SLiCAPplots.html#SLiCAP.SLiCAPplots.plot>`__ function.

``ngspice2traces()`` supports:

#. OP: operating point analysis
#. DC: DC sweep
#. AC: small-signal frequency-domain analysis
#. TRAN: Time-domain analysis
#. DC TEMP: Temperature sweep
#. NOISE: small-signal frequency-domain noise analysis

Parameter stepping (including temperature: ``TEMP``) is supported on all above analysis types.

KiCAD SPICE symbol library
==========================

The KiCAD SPICE symbol library provided with SLiCAP supports all NGspice devices with associated parameters. The SPICE symbol library location is set in the SLiCAP.ini file in the user home directory. Below the location with SLiCAP installed for user *USR* in Python environment *ENV*:

.. code-block::

    >>> import SLiCAP as sl
    >>> sl.ini.ngspice_syms 
    /home/USR/ENV/lib/python3.12/site-packages/SLiCAP/files/kicad/SLiCAP

.. admonition:: Important
    :class: note
    
    NGspice netlist creation and simulation from within SLiCAP only works with SPICE symbols from the library mentioned above! 
    
    **Don't mix-up SLiCAP symbols and SPICE symbols in one schematic!**

Example
=======
   
The SLiCAP output displayed on this manual page, is generated with the script: ``ngspice.py``, imported by ``Manual.py``.

.. literalinclude:: ../ngspice.py
    :linenos:
    :lines: 1-7
    :lineno-start: 1

.. image:: /img/colorCode.svg

Schematic capture and netlist generation
----------------------------------------

`makeCircuit() <../reference/SLiCAPshell.html#SLiCAP.SLiCAPshell.makeCircuit>`__ with keyword argument ``language=SPICE`` creates and returns a NGspice compatible netlist of a KiCAD schematic file:

.. literalinclude:: ../ngspice.py
    :linenos:
    :lines: 9-12
    :lineno-start: 9

.. _fig-VampQspice:

.. Figure:: /img/VampQspice.svg
    :width: 450px
    :alt: KiCAD NGspice schematic 
    
    KiCAD NGspice schematic with SLiCAP SPICE symbols and automatically updated operating point information.
    
Please notice:

#. The value field of independent sources carries the SPICE specification of simulation signals (see: ``V1`` and ``V2``)
#. A standard library (no binned IC models) is included with an ``.INC`` directive
#. A binned IC device model library is included with a ``.LIB`` directive
#. The library path is relative to the project directory
#. All circuit parameters (here: ``C_c``) must be assigned a value with a ``.param`` directive
#. The netlist created from the KiCAD schematics is stored in the ``cir/`` folder in the project directory

Netlist
~~~~~~~
    
.. literalinclude:: ../cir/VampQspice.cir
    
Library
~~~~~~~
    
.. literalinclude:: ../lib/BC847.lib
    :linenos:

Create traces
-------------

The function `ngspice2traces <../reference/SLiCAPngspice.html#SLiCAP.SLiCAPngspice.ngspice2traces>`__ returns a dictionarys with `traces <../reference/SLiCAPplots.html#SLiCAP.SLiCAPplots.trace>`__, the swept variable name, and the swept variable units.

In case of an AC analysis the function returns two dictionaries with traces instead of one.

DC sweep
--------

Simulation command:

.. literalinclude:: ../ngspice.py
    :linenos:
    :lines: 14,15
    :lineno-start: 14
    
The dictionary with names is a mapping of NGspice variable names on plot legend variable names.

.. literalinclude:: ../ngspice.py
    :linenos:
    :lines: 16
    :lineno-start: 16
    
The function `ngspice2traces <../reference/SLiCAPngspice.html#SLiCAP.SLiCAPngspice.ngspice2traces>`__ performs the simulation and returns the data:

.. literalinclude:: ../ngspice.py
    :linenos:
    :lines: 17
    :lineno-start: 17
    
In case of a DC sweep, the *x-units* are empty. They can be defined with the plot:

.. literalinclude:: ../ngspice.py
    :linenos:
    :lines: 19-21
    :lineno-start: 19

.. image:: /img/VampQspiceDC.svg
    :width: 500px
        
AC analysis
-----------

.. literalinclude:: ../ngspice.py
    :linenos:
    :lines: 23-29
    :lineno-start: 23
    
.. image:: /img/VampQspiceM.svg
    :width: 500px
    
.. image:: /img/VampQspiceP.svg
    :width: 500px
    
Transient analysis
------------------

.. literalinclude:: ../ngspice.py
    :linenos:
    :lines: 39-47
    :lineno-start: 39
    
.. image:: /img/VampQspiceT1.svg
    :width: 500px

.. literalinclude:: ../ngspice.py
    :linenos:
    :lines: 49-56
    :lineno-start: 49
    
.. image:: /img/VampQspiceT2.svg
    :width: 500px
    
Change the netlist
------------------

.. literalinclude:: ../ngspice.py
    :linenos:
    :lines: 58-75
    :lineno-start: 50
    
.. image:: /img/VampQspiceS.svg
    :width: 500px
       
DC TEMP sweep
-------------

.. literalinclude:: ../ngspice.py
    :linenos:
    :lines: 77-84
    :lineno-start: 77
    
.. image:: /img/VampQspiceTMP.svg
    :width: 500px
    
NOISE analysis
--------------

.. literalinclude:: ../ngspice.py
    :linenos:
    :lines: 86-94
    :lineno-start: 86
    
.. image:: /img/VampQspiceNOISE.svg
    :width: 500px

.. literalinclude:: ../ngspice.py
    :linenos:
    :lines: 96-105
    :lineno-start: 96  
    
.. image:: /img/VampQspiceNOISETOT.svg
    :width: 500px  
    
Operating point information
---------------------------

Without parameter stepping an ``OP`` instruction returns a dictionary with name-value pairs. With parameter stepping, it returns a dictionary with traces that can be plotted with `SLiCAPplots.plot() <../reference/SLiCAPplots.html#SLiCAP.SLiCAPplots.plot>`__.

.. literalinclude:: ../ngspice.py
    :linenos:
    :lines: 107-119
    :lineno-start: 107
    
This yields:

.. code-block:: text

    V_c1 : 2.49185497
    V_b1 : 1.76367933
    V_e1 : 1.15679378
    V_c2 : 4.29572571
    V_e2 : 1.81259412 
    I_V2 : -0.00296938791
    
Typesetted:

.. literalinclude:: ../ngspice.py
    :linenos:
    :lines: 121-123
    :lineno-start: 121

.. include:: ../sphinx/SLiCAPdata/table-VampQ-opinfo.rst

Display operating point information in KiCAD schematic
------------------------------------------------------

The SLiCAP function `backAnnotateSchematic() <../reference/SLiCAPkicad.html#SLiCAP.SLiCAPkicad.backAnnotateSchematic>`__ can be used to display parameter values and operating point information in a KiCAD schematic file and its ``svg`` and ``pdf`` image files. To this end, text fields with the keys from the ``OPinfo`` dictionary must be placed on the schematic. ``backAnnotateSchematic`` replaces these text fields with ``<name>:<OPinfo[name]>``. The result is shown in :numref:`fig-VampQspice`. Please notice that the keys of the ``OPinfo`` dictionary equal those of the ``names`` dictionary. 

.. literalinclude:: ../ngspice.py
    :linenos:
    :lines: 125-126
    :lineno-start: 125
