======================
Interface with NGspice
======================

.. image:: ../img/colorCode.svg

SLiCAP runs NGspice simulations from a Python script and turns the results into traces, measurements and plots. It requires:

#. `NGspice <https://ngspice.sourceforge.io/>`_ for circuit simulation (`NGspice manual <https://ngspice.sourceforge.io/docs/ngspice-manual.pdf>`_); its location is set in the ``[commands]`` section of the SLiCAP configuration file (see `Installation <install.html>`_).
#. An NGspice schematic (``.spice_sch``), drawn with the SLiCAP schematic editor and its NGspice symbol library, or a hand-written netlist ``cir/<name>.cir``. See `NGspice schematics <../../GUI/schematics/schematic.html>`_ in the GUI manual.

Supported analysis
==================

One function per NGspice analysis runs the simulation and returns a result object with the simulated vectors under their NGspice names:

#. `op() <../reference/SLiCAPngspice.html#SLiCAP.SLiCAPngspice.op>`__: operating point analysis
#. `dc() <../reference/SLiCAPngspice.html#SLiCAP.SLiCAPngspice.dc>`__: DC sweep of a source, or of the temperature (``"TEMP"``)
#. `ac() <../reference/SLiCAPngspice.html#SLiCAP.SLiCAPngspice.ac>`__: small-signal frequency-domain analysis
#. `tran() <../reference/SLiCAPngspice.html#SLiCAP.SLiCAPngspice.tran>`__: time-domain analysis, with FOURIER or FFT post-processing
#. `noise() <../reference/SLiCAPngspice.html#SLiCAP.SLiCAPngspice.noise>`__: small-signal frequency-domain noise analysis

All of them accept:

- ``step``: a parameter step dictionary, ``{"param": "C_c", "method": "lin", "start": "2p", "stop": "20p", "num": 10}``, with method ``"lin"``, ``"log"`` or ``"list"`` (``"values": [...]``); the temperature is stepped with ``"param": "TEMP"``.
- ``params``: an ordered list of ``(name, value)`` parameter definitions for this run only, overriding the values on the schematic.
- ``stimuli``: another stimulus for an independent source for this run only, e.g. ``{"V1": ["SIN", 0, "{V_p}", "100k"]}``.

Numbers are written in SLiCAP notation (``"10M"``, ``"2p"``), not in NGspice notation (``10MEG``).

Compatibility mode
------------------

Netlists and device libraries written for other simulators use syntax that NGspice reads only in a compatibility mode. Every analysis function has the keyword ``behavior``, which is passed to NGspice as its variable ``ngbehavior`` (NGspice manual, section 12.11.1). NGspice reads the keyword by scanning it for the following two-letter flags, so a combination is written as one word: ``"ltpsa"`` is ``lt`` + ``ps`` + ``a``.

.. csv-table::
    :header: "Flag", "Meaning"
    :widths: auto

    "``ps``", "PSPICE syntax"
    "``lt``", "LTSPICE syntax"
    "``hs``", "HSPICE syntax (``ps`` and ``hs`` are mutually exclusive; NGspice switches to ``ps``)"
    "``spe``", "Spectre syntax"
    "``s3``", "Spice3 behaviour, disables some NGspice extensions"
    "``ki``", "KiCad vector names that contain a slash"
    "``eg``", "EAGLE compatible voltage vector output"
    "``a``", "transform the **whole netlist**; without it the selected syntax applies to libraries added with ``.include`` only"

The last flag is the one that matters in practice: a device model written in PSPICE syntax inside the circuit itself needs ``behavior="psa"``, and ``behavior="ps"`` leaves it untouched. In the schematic editor the flags are check boxes on the NGspice instruction dialog.

Simulator options
-----------------

Every analysis function has the keyword ``options``: a dictionary of NGspice simulator options (NGspice manual, chapter 11) that holds for this run only. Each entry is written as an ``option name = value`` command before the analysis; a value of ``None`` writes a flag without a value. Numbers are written in SLiCAP notation.

.. code-block:: python

    OP1 = sl.op("myAmp", behavior="psa", options={"rshunt": "1e12"})
    TR1 = sl.tran("myAmp", "1n", "1u", options={"method": "gear", "reltol": "1e-4"})

The first line is the usual cure for a vendor macro-model that does not converge. Such models often have internal nodes without a DC path to ground (a node between two zener diodes, or between a current source and an inductor); NGspice then reports ``singular matrix`` and gmin stepping, source stepping and the transient operating point all fail. ``rshunt`` adds a resistance from every node to ground, ``gmin`` (``"1e-10"``) adds a conductance across every pn junction; both give the model an operating point without affecting the results. Loosening ``reltol`` or ``abstol`` does not help in this case. In the schematic editor the options are a table on the NGspice instruction dialog.

The result objects are post-processed with the functions of the `trace model <plots.html#work-with-traces>`_: `make_traces() <../reference/SLiCAPtraces.html#SLiCAP.SLiCAPtraces.make_traces>`__ builds traces from expressions over the simulated vectors, `measure() <../reference/SLiCAPtraces.html#SLiCAP.SLiCAPtraces.measure>`__ reduces them to numbers with goal functions, and `plot() <../reference/SLiCAPplots.html#SLiCAP.SLiCAPplots.plot>`__ plots the traces. NGspice's own vector names, ``v(out)``, ``i(v2)``, ``onoise_spectrum``, are not Python identifiers; the keyword ``variables`` of these functions maps them onto names of your own.

.. admonition:: Important
    :class: note
    
    The schematic editor writes the same function calls into the project's instruction file (:menuselection:`Instruction --> Create / edit NGspice instruction…`), so everything on this page can be composed in the GUI as well.

Example
=======
   
The SLiCAP output displayed on this manual page, is generated with the script: ``ngspice.py``, imported by ``Manual.py``.

.. literalinclude:: ../ngspice.py
    :linenos:
    :lines: 1-7
    :lineno-start: 1

.. image:: /API/img/colorCode.svg

Schematic capture, operating point and netlist generation
=========================================================

The circuit is a two-stage transistor amplifier drawn with the NGspice symbols of the schematic editor. The independent sources carry their stimuli (a ``dc`` value, an ``ac`` value and a transient waveform), the parameters ``C_c`` and ``V_S`` are defined in a parameter block, and the transistor model is included from a library file.

.. literalinclude:: ../ngspice.py
    :linenos:
    :lines: 9-16
    :lineno-start: 9

`op() <../reference/SLiCAPngspice.html#SLiCAP.SLiCAPngspice.op>`__ takes the circuit name, exports the netlist from the schematic when it is newer than the netlist, and writes the operating point to ``cir/VampQspice_op.raw``. `makeCircuit() <../reference/SLiCAPshell.html#SLiCAP.SLiCAPshell.makeCircuit>`__ recognizes the NGspice schematic by its extension, exports the netlist, the schematic image and an HTML page with the circuit data, and returns the netlist text. The image carries the **operating point annotations**: the DC voltages of the nets and the DC currents of the sources for which they were switched on in the schematic editor (see `Component properties <../../GUI/schematics/component_properties.html>`_), read from the most recent unstepped operating-point run. Whenever a new operating point is simulated, the image is exported again.

.. image:: /API/img/VampQspice.svg
    :scale: 80 %

Netlist
-------

.. literalinclude:: ../cir/VampQspice.cir
    :linenos:

Operating point information
===========================

Without parameter stepping the result of ``op()`` holds one number per NGspice vector, under the NGspice name; with parameter stepping it holds one array per vector.

.. literalinclude:: ../ngspice.py
    :linenos:
    :lines: 18-29
    :lineno-start: 18

This yields:

.. code-block:: text

    V_c1 : 2.491854967999738
    V_b1 : 1.7636793328341864
    V_e1 : 1.1567937843803244
    V_c2 : 4.2957257123120804
    V_e2 : 1.8125941183950072
    I_V2 : -0.0029693879095610215

Typesetted:

.. include:: ../sphinx/SLiCAPdata/table-VampQ-opinfo.rst

Currents follow the NGspice sign convention: the current through a voltage source is measured into its positive terminal, so a source that delivers current reads negative.

DC sweep
========

.. literalinclude:: ../ngspice.py
    :linenos:
    :lines: 31-37
    :lineno-start: 31
    
The trace specifications are dictionaries: ``"y"`` is an expression over the simulated vectors, named through ``variables``, and ``"label"`` the legend entry. The sweep variable is the abscissa; its name and units are given with the plot.

.. image:: /API/img/VampQspiceDC.svg
    :width: 500px

AC analysis
===========

With parameter stepping every signal holds one row per run, and ``make_traces()`` returns one trace per run, labelled with the step value. The expressions ``dB()`` and ``phase()`` are evaluated on the complex vectors.

.. literalinclude:: ../ngspice.py
    :linenos:
    :lines: 39-50
    :lineno-start: 39

.. image:: /API/img/VampQspiceM.svg
    :width: 500px

.. image:: /API/img/VampQspiceP.svg
    :width: 500px

Transient analysis
==================

.. literalinclude:: ../ngspice.py
    :linenos:
    :lines: 52-59
    :lineno-start: 52

.. image:: /API/img/VampQspiceT1.svg
    :width: 500px

.. literalinclude:: ../ngspice.py
    :linenos:
    :lines: 61-69
    :lineno-start: 61

.. image:: /API/img/VampQspiceT2.svg
    :width: 500px

Change the stimulus
-------------------

The stimulus of an independent source can be changed for one run with the keyword ``stimuli``; the schematic and its netlist are left as they are. Here the pulse source becomes a sine with a stepped amplitude ``V_p``, a parameter that is defined for this run with ``params``.

.. literalinclude:: ../ngspice.py
    :linenos:
    :lines: 71-84
    :lineno-start: 71

.. image:: /API/img/VampQspiceS.svg
    :width: 500px

DC TEMP sweep
=============

.. literalinclude:: ../ngspice.py
    :linenos:
    :lines: 86-92
    :lineno-start: 86

.. image:: /API/img/VampQspiceTMP.svg
    :width: 500px

NOISE analysis
==============

NGspice returns the spectral densities of the output noise and of the source-referred noise in :math:`\mathrm{V^2/Hz}`; their square roots are plotted here.

.. literalinclude:: ../ngspice.py
    :linenos:
    :lines: 94-101
    :lineno-start: 94

.. image:: /API/img/VampQspiceNOISE.svg
    :width: 500px

The total noise follows from the goal function ``RMS_NOISE``, which integrates a spectral density over the simulated frequency range and takes the square root:

.. literalinclude:: ../ngspice.py
    :linenos:
    :lines: 103-105
    :lineno-start: 103

This yields:

.. code-block:: text

    Total output noise: 6.86794e-05 V

A goal function applied to a stepped result gives one value per run, and ``make_traces()`` then returns one trace whose points are the runs: the total output noise versus the temperature.

.. literalinclude:: ../ngspice.py
    :linenos:
    :lines: 107-115
    :lineno-start: 107

.. image:: /API/img/VampQspiceNOISETOT.svg
    :width: 500px  

Transient analysis with parameter substitution
==============================================

.. literalinclude:: ../ngspice.py
    :linenos:
    :lines: 117-124
    :lineno-start: 117

.. image:: /API/img/VampQspiceSIN.svg
    :width: 500px

Fourier and FFT post processing
===============================

Both post-processing options of ``tran()`` require the analysed vectors to be listed with ``save``. An entry ``"name = expression"`` defines a derived vector with NGspice ``let`` after the transient; here the operating-point voltage of the collector, taken from the ``op()`` result at the top of the script, is subtracted, so that the DC component does not leak into the spectrum through the window. The keyword ``tmax`` limits the internal time step of the integration; a small value keeps the numerical noise floor of the spectrum low. With ``fft`` the transient is linearized on the grid of the time step, which sets the highest frequency of the spectrum, and transformed; the result is in the frequency domain (``dataType 'fft'``, complex vectors and ``frequency``) and plots like an AC result. The window follows NGspice ``specwindow`` (default ``hanning``).

.. literalinclude:: ../ngspice.py
    :linenos:
    :lines: 126-135
    :lineno-start: 126

.. image:: /API/img/VampQspiceFFT.svg
    :width: 500px

With ``fourier="<fundamental>"`` (or ``{"freq": "100k", "nfreqs": 10}``) the result keeps the time-domain traces, and the harmonics are attached as the dictionary ``fourier`` of the result: the magnitude, phase and normalized values per harmonic, the total harmonic distortion ``thd(<vector>)`` in percent, and NGspice's own table as text. ``fourier`` is not available for stepped runs, ``fft`` is.

.. literalinclude:: ../ngspice.py
    :linenos:
    :lines: 137-142
    :lineno-start: 137

This yields:

.. code-block:: text

    Fourier analysis for v_ac:
      No. Harmonics: 10, THD: 0.0956276 %, Gridsize: 200, Interpolation Degree: 1
    Harmonic Frequency   Magnitude   Phase       Norm. Mag   Norm. Phase
    -------- ---------   ---------   -----       ---------   -----------
     0       0           0.000174029 0           0           0          
     1       100000      1.93937     69.4189     1           0          
     2       200000      0.000321188 98.5215     0.000165615 29.1026    
     3       300000      0.00179453  -63.719     0.000925317 -133.14    
     4       400000      8.47422e-05 -9.3169     4.36958e-05 -78.736    
     5       500000      0.000320489 -101.63     0.000165254 -171.05    
     6       600000      3.58591e-05 -53.403     1.84901e-05 -122.82    
     7       700000      6.65262e-05 -141.36     3.4303e-05  -210.78    
     8       800000      1.09453e-05 -92.258     5.64372e-06 -161.68    
     9       900000      1.44341e-05 177.589     7.4427e-06  108.17
