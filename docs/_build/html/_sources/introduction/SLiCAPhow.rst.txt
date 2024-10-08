=================
How to use SLiCAP
=================

.. image:: /img/colorCode.svg

Way of working
==============

Working with SLiCAP usually proceeds as follows:

#. Initialize a SLiCAP project; this will

   - Create the directory structure for your project
   - Create a configuration file for your project 
   - Create the main html index page for this project

#. Create a circuit that models the performance aspect(s) and/or cost factor(s) of interest and create  netlist from this circuit.

   - SLiCAP supports netlist generation with KiCAD, LTspice, gSchem and lepton-eda
    
#. Import design budgets for performance and cost factors, as well as circuit parameters determined in earlier design steps to the circuit

   - SLiCAP writes and reads design data to and from a CSV file
   
#. Perform a mixed symbolic/numeric analysis to obtain an expression that writes the performance or costs as a function of the circuit parameters.

   SLiCAP has 18 predefined analysis types grouped in:
   
   - DC and DC variance analysis for finding budgets for:
    
     - resistor tolerances
     - offset voltages and currents and their temperature dependency
     - matching and temperature tracking properties of resistors
   
   - Noise analysis for finding budgets for:
   
     - resistor values
     - equivalent input noise sources of operational amplifiers
     - geometry and operating current of semiconductor devices
     
   - Complex frequency domain analysis (Laplace)
   
   - Time-domain analysis (Inverse Laplace)
     
#. Obtain valid ranges for circuit parameters (component values, geometry and operating voltages and currents) and save them in the design database.

#. Go to (2) for the next design aspect.

.. image:: /img/colorCode.svg
