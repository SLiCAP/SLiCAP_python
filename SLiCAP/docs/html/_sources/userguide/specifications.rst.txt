========================
Work with specifications
========================

.. image:: /img/colorCode.svg

Working with specifications is a powerful feature of SLiCAP. Specifications can be read from and stored to CSV files. Editing of the CSV file with a spreadsheet program or a text editor is possible but not preferred.

Creating specItem objects
=========================

The preferred way of working is to create SLiCAP specItem objects. Detailed information about specItems can be found in the `specItem() <../reference/SLiCAPdesignData.html#SLiCAP.SLiCAPdesignData.specItem>`__.

The example below shows how to create a list with specifications. In this example we will define four specifications for a transimpedance amplifier:

#. The typical value of the signal source capacitance in F; this is considered an 'interface' specification
#. The target value of its current-to-voltage transfer (transimpedance gain); this is considered a 'functional' specification
#. The target value of its -3dB bandwidth; this is considered a 'performance' specification
#. The target value of its (unweighted) RMS output noise; this is considered a 'performance' specification

The designer is free to define any type of specification. In reports, SLiCAP places specifications of the same type in one table.

.. code:: python

    # Import SLiCAP modules in a separate namespace
    import SLiCAP as sl
    # Create SLiCAP project
    sl.initProject("Specifications")
    # It is convenient to define the values at the top of the file
    # This makes it easy to modify them
    Cs = 10e-12 # Typical value of the source capacitance
    Zt = 1e6    # Target value transimpedance gain in Ohm
    Bf = 5e4    # Target value -3dB bandwidth in Hz
    Vn = 5e-4   # Maximum unweighted RMS output noise voltage
    # Now assign these values to specification items and put these items in a list
    # Create the list
    specs = []
    # Create specification items and append them to the list
    specs.append(sl.specItem("C_s", 
                             description = "Typical value of the source capacitance",
                             value       = Cs,
                             units       = "F",
                             specType    = "Interface"))
    specs.append(sl.specItem("Z_t", 
                             description = "Target value transimpedance gain in Ohm",
                             value       = Zt,
                             units       = "Ohmega",
                             specType    = "Functional"))
    specs.append(sl.specItem("B_f", 
                             description = "Target value -3dB bandwidth in Hz",
                             value       = Bf,
                             units       = "Hz",
                             specType    = "Performance"))
    specs.append(sl.specItem("V_n", 
                             description = "Maximum unweighted RMS output noise voltage",
                             value       = Vn,
                             units       = "V",
                             specType    = "Performance"))

.. admonition:: Note
    :class: warning
    
    **You can only assign a single value or expression to a parameter.** A list of values is not supported because this would conflict with assigning values of specified prameters to circuit parameters.

Storing specs in CSV files
==========================

The specifications can be stored in a CSV file with `specs2csv() <../reference/SLiCAPdesignData.html#SLiCAP.SLiCAPdesignData.specs2csv>`__). The specifications are stored in the 'sl.ini.csv_path' folder. By default this is the 'csv' folder in the project directory.

Importing specs from CSV files
==============================

The can be imported from this file with `csv2specs() <../reference/SLiCAPdesignData.html#SLiCAP.SLiCAPdesignData.specs2csv>`__).
    
The example below shows how to store them in a csv file and import them from this file.

.. code:: python

    sl.specs2csv(specs, "specs.csv")   # Store the specifications in the file "specs.csv"
    specs = sl.csv2specs("specs.csv")  # Import the specifications from the file "specs.csv"

Assigning specs to circuit parameters
=====================================

Specifications can be assigned to circuit parameters using `specs2circuit() <../reference/SLiCAPdesignData.html#SLiCAP.SLiCAPdesignData.specs2circuit>`__). Circuit parameters that have the same name as a specItem() will then obtain the value of that specItem().

Displaying specs on an HTML page
================================

Specifications can be listed on the active HTML page using `specs2html() <../reference/SLiCAPdesignData.html#SLiCAP.SLiCAPdesignData.specs2html>`__).
                             
