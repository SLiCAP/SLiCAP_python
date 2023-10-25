============
Create plots
============

SLiCAP provides some plot functions that facilitate easy plotting of graphs from execution results with automatic determination of colors, markers, plot legends, and axis labels.

Plot functions are collected in the SLiCAP module `SLiCAPplots.py <../reference/SLiCAPplots.html>`_.

SLiCAP plots are hierarchically structured:

- A `figure <../reference/SLiCAPplots.html#SLiCAP.SLiCAPplots.SLiCAPplots.figure>`_ object is the main object that can be plotted using its ``.plot()`` method.
- The figure's ``.axis`` attribute is a list of lists with `axis <../reference/SLiCAPplots.html#SLiCAP.SLiCAPplots.SLiCAPplots.axis>`_ objects for one row, from left to right.
- The ``.traces`` attribute of each `axis <../reference/SLiCAPplots.html#SLiCAP.SLiCAPplots.SLiCAPplots.axis>`_ object is a list with `trace <../reference/SLiCAPplots.html#SLiCAP.SLiCAPplots.SLiCAPplots.trace>`_ objects that will be plotted the axis. Trace xdata, ydata, lables, colors, markers, etc, are all attributes of a `trace <../reference/SLiCAPplots.html#SLiCAP.SLiCAPplots.SLiCAPplots.trace>`_ object.

SLiCAP built-in figures are single-axis figures.

- :ref:`plotSweep`

  The function `plotSweep() <../reference/SLiCAPplots.html#SLiCAP.SLiCAPplots.SLiCAPplots.plotSweep>`_ displays traces from expressions with one symbolic variable. It can be used for plotting time-domain responses, frequency-domain responses, and arbitrary single-variable functions.

- :ref:`plotPZ`

  The function `plotPZ() <../reference/SLiCAPplots.html#SLiCAP.SLiCAPplots.SLiCAPplots.plotPZ>`_ displays X-Y scatter plots. These plots are configured for plotting the results of pole-zero analysis. 

- :ref:`plotXY`

  The function `plot() <../reference/SLiCAPplots.html#SLiCAP.SLiCAPplots.SLiCAPplots.plot>`_ generates X-Y line plots from a dictionary with traces. Such dictionaries can be generated from data from other applications, such as, LTspice, SImetrix, NGspice, or Cadence, or from ``.csv`` files (see :ref:`extData`).

.. _plotSweep:

-----------------------------
Plots with a swept x-variable
-----------------------------

Below a few examples using `plotSweep() <../reference/SLiCAPplots.html#SLiCAP.SLiCAPplots.SLiCAPplots.plotSweep>`_.

.. code-block:: python

    >>> from SLiCAP import *
    >>> prj = initProject('My first RC network') # Initialize a SLiCAP project
    >>> instr = instruction()         # Create an instance of an instruction object
    >>> instr.setCircuit('myFirstRCnetwork.cir') # Create a circuit from 'myFirstRCnetwork.cir'
    No errors found for circuit: 'My first RC network' from file: 'myFirstRCnetwork.cir'.

    >>> instr.setSimType('numeric')   # Define the simulation type
    >>> instr.setSource('V1')         # Define the signal source
    >>> instr.setDetector('V_out')    # Nodal voltage 'V_out' is detector voltage
    >>> instr.setGainType('gain')     # Define the gain type
    >>> instr.setDataType('laplace')  # Define the data type
    >>> numGain = instr.execute()     # Execute the instruction and assign the results to 'numGain'

    >>> figMag = plotSweep('RCmag', 'Magnitude characteristic', numGain, 10, '100k', 100, yUnits = '-', show = True)

.. image:: ../img/RCmag.svg

.. code-block:: python

    >>> figPol = plotSweep('RCpolar', 'Polar plot', numGain, 10, '100k', 100, axisType = 'polar', show = True)

.. image:: ../img/RCpolar.svg

.. code-block:: python

    >>> figdBmag = plotSweep('RCdBmag', 'dB magnitude characteristic', numGain, 10, '100k', 100, funcType = 'dBmag', show = True)

.. image:: ../img/RCdBmag.svg

.. code-block:: python

    >>> figPhase = plotSweep('RCphase', 'Phase characteristic', numGain, 10, '100k', 100, funcType = 'phase', show = True)

.. image:: ../img/RCphase.svg

.. code-block:: python

    >>> figDelay = plotSweep('RCdelay', 'Group delay characteristic', numGain, 10, '100k', 100, yScale = 'u', funcType = 'delay')

.. image:: ../img/RCdelay.svg

.. code-block:: python

    >>> i1.setDataType('step')
    >>> numStep = i1.execute()
    >>> figStep = plotSweep('RCstep', 'Unit step response', numStep, 0, 1, 50, sweepScale='m', show = True)

.. image:: ../img/RCstep.svg

Stepping parameters
-------------------

If a stepped-parameter instruction is executed, multiple traces will be plotted on the axis, one for each step value. The legend will show the step variable and the step variable and its value.

For array type stepping the legend text will be ``run: <i>`` where the number ``i`` indicates the i-th step using the i-th value for each step parameter.

Sweeping parameters
-------------------

Cicuit parameters can be assigned a numeric value or a function of other parameters. In the case of a single-variable function it can be plotted with the `plotSweep() <../reference/SLiCAPplots.html#SLiCAP.SLiCAPplots.SLiCAPplots.plotSweep>`_ function.

.. code-block:: python

    >>> from SLiCAP import *
    >>> prj = initProject('My first RC network') # Initialize a SLiCAP project
    >>> instr = instruction()         # Create an instance of an instruction object
    >>> instr.setCircuit('myFirstRCnetwork.cir') # Create a circuit from 'myFirstRCnetwork.cir'
    No errors found for circuit: 'My first RC network' from file: 'myFirstRCnetwork.cir'.

.. _plotPZ:

------------------------------
Pole-zero and root-locus plots
------------------------------

.. code-block:: python

    >>> from SLiCAP import *
    >>> prj = initProject('My first RC network') # Initialize a SLiCAP project
    >>> instr = instruction()         # Create an instance of an instruction object
    >>> instr.setCircuit('myFirstRCnetwork.cir') # Create a circuit from 'myFirstRCnetwork.cir'
    No errors found for circuit: 'My first RC network' from file: 'myFirstRCnetwork.cir'.

    >>> instr.setSimType('numeric')   # Define the simulation type
    >>> instr.setSource('V1')         # Define the signal source
    >>> instr.setDetector('V_out')    # Nodal voltage 'V_out' is detector voltage
    >>> instr.setGainType('gain')     # Define the gain type
    >>> instr.setDataType('pz')       # Define the data type
    >>> pzGain = instr.execute()      # Execute the instruction and assign the results to 'numGain'

    >>> figPZ = plotPZ('PZ', 'Poles and zeros of the RC network', pzGain)

.. image:: ../img/PZ.svg

Stepping parameters and root locus plots
----------------------------------------

SLiCAP can plot the poles and zeros while stepping parameters. A root-locus plot in SLiCAP is essensially a stepped-parameter analysis with the data type set to 'poles'. The formatting of the stepped pole-zero plots is as follows:

- Data type 'poles' or 'pz'

  - marker for each pole, first step: :math:`\times`
  - marker for each pole, last step: :math:`+`
  - marker for each pole, each step: :math:`\bullet`

- Data type 'zeros' or 'pz'

  - marker for each zero, first step: :math:`\circ`
  - marker for each zero, last step:  :math:`\Box`
  - marker for each zero, each step: :math:`\bullet`

Paths of poles and/or zeros traced out by stepping parameters are displayed as a collection of dots: :math:`\bullet`. Only the first value and the last value of the step parameter is displayed in the legend. For array type stepping only *run: 1* and *run: <number of steps>* is displayed in the legend.

.. _plotXY:

---------
X-Y plots
---------

.. _extData:

---------------------------------
Plot data from other applications
---------------------------------

Add traces to a figure
----------------------

The function `traces2fig() <../reference/SLiCAPplots.html#SLiCAP.SLiCAPplots.SLiCAPplots.traces2fig>`_ adds traces to a figure.
