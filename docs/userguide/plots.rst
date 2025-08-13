============
Create plots
============

.. image:: ../img/colorCode.svg

SLiCAP output displayed on this manual page, is generated with the script: ``plots.py``, imported by ``Manual.py``.

.. literalinclude:: ../plots.py
    :linenos:
    :lines: 1-10
    :lineno-start: 1

.. image :: /img/myPassiveNetwork.svg
    :width: 800
    
SLiCAP provides a number of plot functions for pre-formatted plotting of instruction results. Plot types, axis types, trace colors, markers, labels and plot legends are automatically selected from the instruction settings.

Plot functions are collected in the SLiCAP module `SLiCAPplots.py <../reference/SLiCAPplots.html>`_.

SLiCAP plots are hierarchically structured:

- A `figure <../reference/SLiCAPplots.html#SLiCAP.SLiCAPplots.figure>`_ object is the main object that can be plotted using its ``.plot()`` method.
- The figure's ``.axis`` attribute is a list of lists with `axis <../reference/SLiCAPplots.html#SLiCAP.SLiCAPplots.axis>`_ objects for each row, from left to right.
- The ``.traces`` attribute of each ``axis`` object is a list with `trace <../reference/SLiCAPplots.html#SLiCAP.SLiCAPplots.trace>`_ objects that will be plotted the axis. Trace xdata, ydata, lables, colors, markers, etc, are all attributes of a ``trace`` object.

SLiCAP built-in figures are single-axis figures. 

SLiCAP has three built-in plot functions:

- `plotSweep() <../reference/SLiCAPplots.html#SLiCAP.SLiCAPplots.plotSweep>`_
- `plotPZ() <../reference/SLiCAPplots.html#SLiCAP.SLiCAPplots.plotPZ>`_
- `plot() <../reference/SLiCAPplots.html#SLiCAP.SLiCAPplots.plot>`_

SLiCAP plot functions use the Python module `matplotlib <https://matplotlib.org/>`_. When using SLiCAP built-in plot functions, knowledge about matplotlib is not required.

Built-in plot types
===================

plotSweep()
-----------

`plotSweep() <../reference/SLiCAPplots.html#SLiCAP.SLiCAPplots.plotSweep>`_ displays traces from expressions with one symbolic variable. It can be used for plotting time-domain responses, frequency-domain responses and swept parameter plots.

plotPZ()
--------

`plotPZ() <../reference/SLiCAPplots.html#SLiCAP.SLiCAPplots.plotPZ>`_ displays X-Y scatter plots. These plots are configured for plotting the results of pole-zero analysis. 

plot()
------

`plot() <../reference/SLiCAPplots.html#SLiCAP.SLiCAPplots.plot>`_ generates X-Y line plots from a dictionary with traces. Such dictionaries can be generated from data from other applications, such as, LTspice, SImetrix, NGspice, or Cadence, or from ``.csv`` files.

Plot settings
=============

Plot settings are found in the **[plot]** section of the ``SLiCAP.ini`` file in the project directory. These settings can be changed from within the Python environment.

.. code-block::

    >>> import SLiCAP as sl
    >>> sl.ini.dump("plot")

    PLOT
    ----
    ini.gain_colors_gain       = b
    ini.gain_colors_loopgain   = k
    ini.gain_colors_asymptotic = r
    ini.gain_colors_servo      = m
    ini.gain_colors_direct     = g
    ini.gain_colors_vi         = c
    ini.axis_height            = 5
    ini.axis_width             = 7
    ini.line_width             = 2
    ini.line_type              = -
    ini.plot_fontsize          = 12
    ini.marker_size            = 7
    ini.legend_loc             = best
    ini.default_colors         = ['r', 'b', 'g', 'c', 'm', 'y', 'k']
    ini.default_markers        = ['']
    ini.plot_file_type         = svg
    ini.svg_margin             = 1
    
.. admonition:: note
    :class: note
    
    Pole-zero plots are square plots: the axis width is set to the axis height.

Creating and updating plots
---------------------------

The three built-in plot functions create a figure object. After creation, traces can be added to a plot and the figure objects needs to be updated. The method ``figure.plot()`` recreates the plot.

Showing plots
-------------

All plot functions have a keyword argument ``show=False`` by default. In this way they don't pop up running a script blocking further execution of the script during pop-up.

Saving plots
------------

All plot functions by default store a ``.pdf`` graphics file and a graphics file of the type set by ``ini.plot_file_type`` in the project image folder set by ``ini.img_path``:

.. code-block::

    >>> import SLiCAP as sl
    >>> sl.ini.dump("paths")

    ini.project_path           = /home/USR/DATA/SLiCAP/SLiCAP_github/SLiCAP_python/docs/
    ini.html_path              = html/
    ini.cir_path               = cir/
    ini.img_path               = img/
    ini.csv_path               = csv/
    ini.txt_path               = txt/
    ini.tex_path               = tex/
    ini.user_lib_path          = lib/
    ini.sphinx_path            = sphinx/
    ini.tex_snippets           = tex/SLiCAPdata/
    ini.html_snippets          = sphinx/SLiCAPdata/
    ini.rst_snippets           = sphinx/SLiCAPdata/
    ini.myst_snippets          = sphinx/SLiCAPdata/
    ini.md_snippets            = sphinx/SLiCAPdata/
    
.. admonition:: Important
    :class: note
    
    Plots are always saved, independent of the value of the keyword argument ``show``.
    
Frequency-characteristics
=========================

.. literalinclude:: ../plots.py
    :linenos:
    :lines: 12-14
    :lineno-start: 12

Magnitude
---------

.. literalinclude:: ../plots.py
    :linenos:
    :lines: 16-18
    :lineno-start: 16
    
.. image:: /img/f_mag.svg
    :width: 500px

dB Magnitude
------------

.. literalinclude:: ../plots.py
    :linenos:
    :lines: 20-22
    :lineno-start: 20

.. image:: /img/f_dBm.svg
    :width: 500px

Phase
-----

.. literalinclude:: ../plots.py
    :linenos:
    :lines: 24-26
    :lineno-start: 24

.. image:: /img/f_phs.svg
    :width: 500px

Group delay
-----------

.. literalinclude:: ../plots.py
    :linenos:
    :lines: 28-31
    :lineno-start: 28

.. image:: /img/f_del.svg
    :width: 500px

Polar Magnitude-phase
---------------------

.. literalinclude:: ../plots.py
    :linenos:
    :lines: 33-35
    :lineno-start: 33

.. image:: /img/p_mag.svg
    :width: 500px

Polar dB magnitude-phase
------------------------

.. literalinclude:: ../plots.py
    :linenos:
    :lines: 37-40
    :lineno-start: 37

.. image:: /img/p_dBm.svg
    :width: 500px

Time-domain plots
=================

Unit impulse response
---------------------

.. literalinclude:: ../plots.py
    :linenos:
    :lines: 44-47
    :lineno-start: 44

.. image:: /img/delta_t.svg
    :width: 500px

Unit Step response
------------------

.. literalinclude:: ../plots.py
    :linenos:
    :lines: 49-52
    :lineno-start: 49

.. image:: /img/mu_t.svg
    :width: 500px

Time-domain response
--------------------

.. literalinclude:: ../plots.py
    :linenos:
    :lines: 54-57
    :lineno-start: 54

.. image:: /img/v_time.svg
    :width: 500

Periodic pulse response
-----------------------

Modify trace data and label
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../plots.py
    :linenos:
    :lines: 59-63
    :lineno-start: 59

.. image:: /img/pp_time.svg
    :width: 500px
    
Noise spectrum
==============

Detector-referred noise
-----------------------

.. literalinclude:: ../plots.py
    :linenos:
    :lines: 65-69
    :lineno-start: 65

.. image:: /img/onoise_f.svg
    :width: 500px

Contributions to detector-referred noise
----------------------------------------

.. literalinclude:: ../plots.py
    :linenos:
    :lines: 71-74
    :lineno-start: 71

.. image:: /img/all_onoise_f.svg
    :width: 500px

Source-referred noise
---------------------

.. literalinclude:: ../plots.py
    :linenos:
    :lines: 76-78
    :lineno-start: 76

.. image:: /img/inoise_f.svg
    :width: 500px

Swept parameter plots
=====================

In the circuit model used for this page the parameter :math:`C_b` is defined as a function of the frequency :math:`f_s`.

This function can be plotted using a swept parameter plot.

.. literalinclude:: ../plots.py
    :linenos:
    :lines: 79-86
    :lineno-start: 79

.. image:: /img/Cb_fs.svg
    :width: 500px
    
Pole-zero plots
===============

Poles
-----

.. literalinclude:: ../plots.py
    :linenos:
    :lines: 90-92
    :lineno-start: 90

.. image:: /img/p_plot.svg
    :width: 350px
    
Zeros
-----

.. literalinclude:: ../plots.py
    :linenos:
    :lines: 94-96
    :lineno-start: 94

.. image:: /img/z_plot.svg
    :width: 350px

Observable and controllable poles and zeros
-------------------------------------------

.. literalinclude:: ../plots.py
    :linenos:
    :lines: 98-102
    :lineno-start: 98

.. image:: /img/pz_plot.svg
    :width: 350px

Multiple results in one plot
============================

.. literalinclude:: ../plots.py
    :linenos:
    :lines: 104-107
    :lineno-start: 104

.. image:: /img/ppzz_plot.svg
    :width: 350px

Parameter stepping
==================

.. literalinclude:: ../plots.py
    :linenos:
    :lines: 109-115
    :lineno-start: 109

Stepped plotSweep()
-------------------

.. literalinclude:: ../plots.py
    :linenos:
    :lines: 117-122
    :lineno-start: 117
    
.. image:: /img/f_dBmStepped.svg
    :width: 500px
    
Stepped plotPZ(): root locus plots
----------------------------------

.. literalinclude:: ../plots.py
    :linenos:
    :lines: 124-128
    :lineno-start: 124

A stepped pole-zero plot shows:

- The start end en locations of poles as :math:`\times` and :math:`+`, respectively
- For each step value a dot at the pole location
- The start end en locations of zeros as :math:`\circ` and :math:`\square`, respectively
- For each step value a dot at the zero location

.. image:: /img/pzStepped.svg
    :width: 350px
    
Stepped parameter sweep
-----------------------

.. literalinclude:: ../plots.py
    :linenos:
    :lines: 130-142
    :lineno-start: 130
    
.. image:: /img/Cb_fs_L.svg
    :width: 500
    
Work with traces
================

Extract traces from a figure
----------------------------

.. literalinclude:: ../plots.py
    :linenos:
    :lines: 144-145
    :lineno-start: 144

Add a dictionary with traces to an existing plot
------------------------------------------------

The function `traces2fig() <../reference/SLiCAPplots.html#SLiCAP.SLiCAPplots.SLiCAPplots.traces2fig>`_ adds traces to a figure.

.. literalinclude:: ../plots.py
    :linenos:
    :lines: 147-157
    :lineno-start: 147

.. image:: /img/all_onoise.svg
    :width: 500
    
Create and plot a dictionary with traces
----------------------------------------

.. literalinclude:: ../plots.py
    :linenos:
    :lines: 159-179
    :lineno-start: 159

.. image:: /img/powers_x.svg
    :width: 500

.. image:: /img/colorCode.svg
