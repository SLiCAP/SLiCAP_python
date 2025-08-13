========================
Work with specifications
========================

.. image:: /img/colorCode.svg

Working with specifications is a powerful feature of SLiCAP. Specifications can be read from and stored to CSV files. Editing of the CSV file with a spreadsheet program or a text editor is possible but not preferred.

SLiCAP output displayed on this manual page, is generated with the script: ``specifications.py``, imported by ``Manual.py``.

.. literalinclude:: ../specifications.py
    :linenos:
    :lines: 1-12
    :lineno-start: 1

Create specifications with specItem objects
===========================================

The preferred way of working is to create SLiCAP ``specItem`` objects. Detailed information about specItems can be found in the `specItem() <../reference/SLiCAPdesignData.html#SLiCAP.SLiCAPdesignData.specItem>`__.

The example below shows how to create a list with specifications. In this example we will define four specifications for a transimpedance amplifier:

#. The typical value of the signal source capacitance in F; this is considered an 'interface' specification
#. The target value of the peak input current; this is considered an 'interface' specification
#. The target value of the peak output voltage; this is considered a 'interface' specification
#. The target value of its -3dB bandwidth; this is considered a 'performance' specification
#. The target value of its (unweighted) RMS output noise; this is considered a 'performance' specification

The designer is free to define any type of specification. In reports, SLiCAP places specifications of the same type in one table.

Below an example of working with specifications.

.. literalinclude:: ../specifications.py
    :linenos:
    :lines: 14-48
    :lineno-start: 14

.. admonition:: Note
    :class: warning
    
    **You can only assign a single value or expression to a parameter.** A list of values is not supported because this would conflict with assigning parameter values to circuit parameters.

Save specifications in CSV files
================================

The specifications can be stored in a CSV file with `specs2csv() <../reference/SLiCAPdesignData.html#SLiCAP.SLiCAPdesignData.specs2csv>`__. The specifications are stored in the ``sl.ini.csv_path`` folder. By default this is the ``csv/`` folder in the project directory.

.. literalinclude:: ../specifications.py
    :linenos:
    :lines: 50-51
    :lineno-start: 50

Import specifications from CSV files
====================================

The can be imported from this file with `csv2specs() <../reference/SLiCAPdesignData.html#SLiCAP.SLiCAPdesignData.specs2csv>`__).
    
The example below shows how to store them in a csv file and import them from this file.

.. literalinclude:: ../specifications.py
    :linenos:
    :lines: 53-54
    :lineno-start: 53
    
Display specifications in the console
=====================================

The script below prints the name, the value and the units of the *interface specifications*:

.. literalinclude:: ../specifications.py
    :linenos:
    :lines: 56-64
    :lineno-start: 56
    
The output shows:

.. code-block:: text

    C_s 1.00e-11 F
    I_p 2.00e-5 A
    V_p 4.00 V
    B_f 5.00e+4 Hz
    V_n 1.00e-5 V

Assign specified parameters to circuit parameters
=================================================

Specifications can be assigned to circuit parameters using `specs2circuit() <../reference/SLiCAPdesignData.html#SLiCAP.SLiCAPdesignData.specs2circuit>`__. Circuit parameters that have the same name as a specItem() will then obtain the value of that specItem().

`Create a SLiCAP circuit object <circuit.html>`_ from a schematic file or a netlist:

.. literalinclude:: ../specifications.py
    :linenos:
    :lines: 68-69
    :lineno-start: 68
    
Below the netlist file created with the above script. It shows the expressions and parameters associated with circuit elements.

.. literalinclude:: ../cir/Transimpedance.cir

Below the ``.svg`` image file created with the above script.

.. image:: ../img/Transimpedance.svg
    :width: 450px

The script lines below assign the specifications to circuit parameters and shows the results in the console.

.. literalinclude:: ../specifications.py
    :linenos:
    :lines: 71-84
    :lineno-start: 71

The output below, shows the circuit parameters. The parameter definitions include SLiCAP built-in parameter definitions; see `Work with parameters <parameters.html>`_.

.. code-block:: text

    Circuit parameter definitions
    T 300.
    q 1.60e-19
    C_s 1.00e-11
    I_p 2.00e-5
    V_p 4.00
    B_f 5.00e+4
    V_n 1.00e-5

    Parameters that have no definition:

    R_t
    sigma_ID
    sigma_R
    I_D            

Display tables with specifications in LaTeX documents and on HTML pages
=======================================================================
    
With the aid of the report module `Creating reports <reports.html>`_, tables with specifications can be displayed on HTML pages or in LaTeX documents. 

Below the script for generating the rst snippets for this help file.

.. literalinclude:: ../specifications.py
    :linenos:
    :lines: 86-92
    :lineno-start: 86
    
Below the tables generated with this script.

.. include:: ../sphinx/SLiCAPdata/table-specs-performance.rst

.. include:: ../sphinx/SLiCAPdata/table-specs-interface.rst

.. image:: /img/colorCode.svg
