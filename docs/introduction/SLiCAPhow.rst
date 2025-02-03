=================
How to use SLiCAP
=================

.. image:: /img/colorCode.svg

Workflow
========

Working with SLiCAP usually proceeds as follows:

#. **Initialize a SLiCAP project**: this will

   - Create the directory structure for your project
   - Create a configuration file for your project 
   - Create the main html index page for this project

#. **Create a circuit model** that models the performance aspect(s) and/or cost factor(s) of interest and create netlist from it

   .. admonition:: note
   
      The complexity of the model should be as low as possible: the model should have all the information to find the answer to a design question, but not more.

   - SLiCAP supports netlist generation with KiCAD, LTspice, gSchem and lepton-eda
    
#. **Import design budgets** for performance and cost factors, as well as circuit parameters determined in earlier design steps to the circuit

   - SLiCAP writes and reads design data to and from a CSV file
   
#. **Perform mixed symbolic/numeric circuit analysis** with this model and obtain an expression that writes the performance or costs as a function of the circuit parameters

   SLiCAP has 16 predefined (mixed symbolic/numeric) analysis types grouped in:
   
   - DC and DC variance analysis for finding valid ranges for:
    
     - resistor tolerances
     - offset voltages and currents and their temperature dependency
     - matching and temperature tracking properties of resistors
   
   - Noise analysis for finding valid ranges for:
   
     - resistor values
     - equivalent input noise sources of operational amplifiers
     - geometry and operating current of semiconductor devices
     
   - Complex frequency domain analysis (Laplace) for finding
   
     - minimum gain-bandwidth product of operational amplifiers
     - minimum number of stages in a feedback amplifier
     - budgets for geometry and operating current of semiconductor devices considering bandwidth limitations
     - component values for filters and frequency compensation elements
   
   - Complex frequency domain analysis (Poles and Zeros) for determination of
   
     - frequency stability
     - non-observable or non-controllable states
     
   - Time-domain analysis (Inverse Laplace) for finding valid ranges for
    
     - component values, geometry and operating current of semiconductor devices, considering settling time requirements
     
#. **Obtain valid ranges for circuit parameters** (component values, geometry and operating voltages and currents) and save them in the design database

#. **Assign values to circuit parameters** and save them in the data base

#. **Go to (2)** for the next design aspect or the next hierarchical level

.. image:: /img/colorCode.svg
