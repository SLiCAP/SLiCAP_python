========================
Traces, axes and figures
========================

A plot is built in three layers, and each layer has its own dialog in the
:menuselection:`Instruction` menu:

#. A **trace set** holds traces. A trace is one curve: an expression in the
   results of your analyses, evaluated on numbers.
#. An **axis** holds traces. They can come from several trace sets.
#. A **figure** places axes in a grid. It writes the plot to ``img/`` as an
   SVG and a PDF file.

Each dialog writes one statement into the instruction file:

.. code-block:: python

   TR1  = sl.make_traces(sl.makeDataset({"LAPLACE1": LAPLACE1}, x="frequency",
                                        start="1", stop="1M", num=200),
                         [{"y": "dB(mag(LAPLACE1.laplace))", "label": "gain"},
                          {"y": "phase(LAPLACE1.laplace)", "label": "phase"}])
   AX1  = sl.traceAxis("", "semilogx", TR1["gain"], xName="frequency",
                       xUnits="Hz", yName="gain", yUnits="dB")
   AX2  = sl.traceAxis("", "semilogx", TR1["phase"], xName="frequency",
                       xUnits="Hz", yName="phase", yUnits="deg")
   FIG1 = sl.makeFigure([[AX1], [AX2]], "bode", shareX=[[AX1, AX2]])

Work in this order: traces, then axes, then figures.

.. note::

   Run the instruction file before you make traces. The dialogs offer the
   results of the last run, as the **Design data** pane lists them. A signal
   exists only after the run that produces it.

Traces and measurements
=======================

:menuselection:`Instruction --> Create / Edit Traces and Measurements…`
opens a dialog with two tabs. **Traces** makes a trace set:
``sl.make_traces(...)``. **Measurements** makes single values:
``sl.measure(...)``.

Names of results and signals
----------------------------

An expression names a signal with the name of its result in front of it,
as the Design data pane shows them: ``AC1.V_out``, ``LAPLACE1.laplace``,
``FLT1.H_fs``, ``R1.Ix``. One expression may use several results. The
dialog finds the results from these names. You do not select a result
first.

What each kind of result offers:

.. list-table::
   :header-rows: 1
   :widths: 30 40 30

   * - Result
     - Signals
     - Points
   * - NGspice analysis (``op``, ``dc``, ``ac``, ``tran``, ``noise``)
     - the saved vectors, such as ``v(out)``, under a Python name of your
       choice (see below)
     - those of the run
   * - System run (``sl.runSystem``)
     - the stored signals, such as ``R1.Ix``
     - those of the run
   * - SLiCAP result
     - ``laplace`` (doLaplace), ``numer``, ``denom``, ``onoise`` and
       ``inoise`` (doNoise), ``time``, ``impulse``, ``stepResp`` (doTime,
       doImpulse, doStep)
     - a range you give
   * - Filter made with ``sl.makeFilter()``
     - ``H_fs`` and ``H_fz``, the frequency responses of the Laplace and the
       z-transfer; ``impulse`` and ``stepResp``, the sampled responses
     - a range you give; in time the samples k·Ts
   * - Expression in s, f or t from the Design data
     - its own name
     - a range you give

An NGspice or system run is **data**: it has its own points. A SLiCAP
result, a filter or an expression is a **function**: it is evaluated at the
points you ask for. The two combine:

* A function used together with data is evaluated at the points of the
  data. Its variable must fit: a function of s or f with frequency data, a
  function of t with time data. This is how you plot a simulation against
  the expression that models it, or the difference between the two.
* Data of several runs combine only when they lie on the same points.
* A function applies to every run of stepped data.
* Whether the combination means something is your responsibility. The
  dialog checks the x variable only, not the units.

When a trace set uses functions only, a range row appears:
:guilabel:`Frequency:` or :guilabel:`Time:`, from, to, the number of points
(:guilabel:`no. pts`), and :guilabel:`log` or :guilabel:`lin`. The limits
take a number in SLiCAP notation (``1``, ``10k``, ``1M``) or the name of a
parameter. For a filter in time you give only from and to: its points are
its samples.

When a trace uses a system run, :guilabel:`X axis of the system run:`
chooses the x axis: time, the master tick, or the sample index of the
clock domain.

Python names for simulated signals
----------------------------------

NGspice names its vectors ``v(out)``, ``i(v1)`` or ``onoise_r1``. Those are
not Python names, so an expression cannot use them directly. The table
:guilabel:`Assign Python variables to the simulated signals` gives each of
them one: result ``AC1``, Python variable ``V_out``, simulated signal
``v(out)``. The expression then uses ``AC1.V_out``. The dialog writes the
table as ``variables={"AC1.V_out": "AC1.v(out)"}``.

You rarely fill this table yourself. Picking an NGspice signal with
:guilabel:`Insert Signal` adds the row, with a name derived from the vector:
``v(out)`` becomes ``V_out``. The name stays editable. The table is shown
only when the file has NGspice or system runs.

The traces table
----------------

Each row is one trace:

* :guilabel:`Y expression`: what the trace plots, for example
  ``dB(mag(AC1.V_out))``.
* :guilabel:`X expression`: what it is plotted against. The dialog fills it:
  ``frequency`` or ``time`` for a sweep, ``t`` for a function in time, the
  step parameter when the y expression reduces each run to one number. It
  follows the y expression until you type in it.
* :guilabel:`Y units`, :guilabel:`X units`: suggested where a convention
  says so (``dB``, ``Hz``, ``V`` for ``V_…``). Left empty, ``make_traces()``
  takes the units from the result when the file runs.
* :guilabel:`Label`: the legend text. For a trace of one SLiCAP result the
  dialog suggests the gain type, as ``plotSweep()`` does.
* :guilabel:`Color`: picked from a colour dialog. Empty means automatic.

:guilabel:`Add trace` and :guilabel:`Remove trace` add and remove rows. The
:guilabel:`Trace dictionary name` is the variable the set is assigned to,
``TR1`` by default. An axis selects a trace of the set by its label:
``TR1["gain"]``. Two traces with one label get ``"gain"`` and
``"gain (2)"``.

Expressions
-----------

An expression is evaluated by numpy on numbers when the file runs. It is
not a symbolic SymPy expression: ``pi`` is the number 3.14159…, and units
are not tracked. Every numpy function may be used, and these are added:

* ``mag``, ``abs``: magnitude.
* ``dB``: 20·log10 of a magnitude. ``dB_10`` gives 10·log10, for a power.
* ``phase``: phase in degrees, unwrapped. ``angle`` gives radians.
* ``delay``: group delay.
* ``real``, ``imag``, ``sqrt``, ``exp``, ``log``, ``log10``.

A complex signal without a function shows its magnitude.

A **goal function**, written in capitals, reduces a run to one number:
``MAX``, ``MIN``, ``MEAN``, ``RMS``, ``RMS_NOISE``, ``INT``, ``SUM``,
``Y_AT_X(y, x0)``, ``X_AT_MAX_Y``, ``X_AT_MIN_Y``, ``X_AT_NTH_Y(y, y0, n)``.
In a trace of a stepped result this gives one point per run: for example
the maximum gain against a component value.

The expression creator
~~~~~~~~~~~~~~~~~~~~~~

Each expression cell has a :guilabel:`…` button at its right edge. It opens
the expression creator for that cell. A double click on the cell edits the
text directly. The creator has four insert menus:

* :guilabel:`Insert Signal`: the signals of every result, one submenu per
  result.
* :guilabel:`Insert Circuit Parameter`: the parameters of the circuits. An
  expression may use them, for example to divide a power by a resistance.
* :guilabel:`Insert Function`: the functions listed above.
* :guilabel:`Insert Goal Function`: a goal function around the selected
  text. Select ``AC1.V_out`` and choose ``RMS`` to get ``RMS(AC1.V_out)``.

Measurements
------------

The :guilabel:`Measurements` tab makes single values. Each row is one
``sl.measure(...)`` statement:

* :guilabel:`Name`: the variable, ``MEAS1`` by default.
* :guilabel:`Expression`: an expression that gives one number, for example
  ``Y_AT_X(dB(mag(AC1.V_out)), 1e3)``.
* :guilabel:`Step value / run number`: for a stepped result, the run to
  measure: a step value such as ``C_c=18p``, or a run number such as ``2``.
* :guilabel:`Units`: the units of the value.

A measurement is a number with its units.

Writing the statements
----------------------

Below the tabs the dialog shows why the statement cannot be written yet,
for example a missing range, and a preview of what it writes.
:guilabel:`Add instruction` writes the trace set and the measurements.

Axes
====

:menuselection:`Instruction --> Create / Edit Axes…` makes an axis. The
:guilabel:`Axis variable name` is its variable, ``AX1`` by default. The
:guilabel:`Title` is placed above the axis. :guilabel:`Axis kind` chooses one
of four kinds:

* :guilabel:`Auto-create frequency/time sweep from SLiCAP results` writes
  ``sl.sweepAxis(...)``. Pick SLiCAP results and the quantity to plot, and
  give the sweep: from, to and the number of points. Labels, scales and
  colours follow from the results, as with ``plotSweep()``. The quantity is
  chosen in the :guilabel:`Quantity` cell of the y axis: ``mag``,
  ``dBmag``, ``phase``, ``delay`` for a transfer, ``onoise``, ``inoise`` for
  noise, ``time`` for a time response. ``param`` plots one parameter against
  a swept one, given as :guilabel:`Sweep parameter` and
  :guilabel:`Plot parameter`. No trace set is needed.
* :guilabel:`XY from traces` writes ``sl.traceAxis(...)``. The
  :guilabel:`Axis type` is ``lin``, ``semilogx``, ``semilogy`` or ``log``.
* :guilabel:`Polar from traces`: a polar plot of trace sets.
* :guilabel:`Pole-zero from SLiCAP results` writes ``sl.pzAxis(...)``, for
  results of ``doPZ``, ``doPoles`` and ``doZeros``.

:guilabel:`Trace sets on this axis` lists the trace sets of the file, each
with its traces. Tick a set to take all its traces, or tick single traces:
a magnitude and a phase in one set go to two axes. :guilabel:`Select all`
and :guilabel:`Deselect all` tick or clear everything. Traces are drawn in
the order of the list.

The label grid has a row for x and a row for y:

* :guilabel:`Quantity` and :guilabel:`Units` make the axis label. They are
  suggested from the selected traces. A value you type stays.
* :guilabel:`Scale factor` (``m``, ``k``, ``M``, …) scales the numbers on
  the axis. The trace data stays in base units, so the same trace can be
  placed on several axes with different scales.
* :guilabel:`Axis label` shows the resulting label, for example
  ``frequency [kHz]``.
* :guilabel:`From` and :guilabel:`To` fix the limits. Empty means
  automatic.

When the selected traces state different units, a warning says so. The
axis is still written.

Figures
=======

:menuselection:`Instruction --> Create / Edit Figures…` makes a figure:

* :guilabel:`Figure variable name`: its variable, ``FIG1`` by default.
* :guilabel:`File name`: the files ``img/<name>.svg`` and ``img/<name>.pdf``.
  The plot window shows this name in its title bar.
* :guilabel:`Title`: a heading drawn inside the image. It may hold LaTeX,
  such as ``$A_{f\infty}$``. Empty means no heading.
* :guilabel:`Rows` and :guilabel:`Columns`: the size of the grid.
  :guilabel:`Mosaic` shows the layout with one letter per axis, row by row:
  ``AA / B.`` is AX1 across the top row, AX2 below at the left, and an
  empty cell.

Each cell of :guilabel:`Axes on the figure` holds an axis, or nothing. The
drop-down also offers :guilabel:`Create new axis…`, which opens the Axes
dialog. The new axis lands in that cell. :guilabel:`Edit…` opens the Axes
dialog on the axis in the cell.

**A span** is the same axis in adjacent cells: AX1 in both cells of the top
row spans the full width. The cells of a span must form a rectangle.

**Sharing** is set with two grids of tick boxes:

* :guilabel:`Share x`: vertically adjacent ticked cells get one x axis. They
  have one scale and zoom together. Only the outer axis shows the tick
  labels and the axis label. This is the usual Bode stack.
* :guilabel:`Share y`: horizontally adjacent ticked cells get one y axis.

Three options complete the figure: :guilabel:`show` opens a plot window
when the file runs, :guilabel:`save in img/` writes the files, and
:guilabel:`A/B cursors` puts two cursors in the plot window.

Editing
=======

Each dialog has a selector at the top: :guilabel:`Select trace dictionary`,
:guilabel:`Select measurement`, :guilabel:`Edit existing` (axes) and
:guilabel:`Select figure`. It loads an existing object back into the dialog.
:guilabel:`Add instruction` then replaces that object on its own line. An
axis edited with :guilabel:`Edit…` in a cell of the Figures dialog is
replaced on its own line too. The rules are those of every dialog:
:ref:`gui-editing-an-existing-instruction`.

Two examples
============

**A Bode plot of a SLiCAP result.** Run the file with a ``doLaplace()``
result ``LAPLACE1``. In the Traces dialog, insert the signal
``LAPLACE1.laplace`` in the first row and wrap it as
``dB(mag(LAPLACE1.laplace))``. Add a second row
``phase(LAPLACE1.laplace)``. The range row appears: give 1 to 1M. Add the
trace set. In the Axes dialog, make AX1 with the first trace and AX2 with
the second, both ``semilogx``. In the Figures dialog, choose two rows, put
AX1 and AX2 in the cells and tick both under :guilabel:`Share x`.

The Axes dialog can do this in one step for a SLiCAP result: the kind
:guilabel:`Auto-create frequency/time sweep from SLiCAP results`, with the
quantity ``dBmag`` and then ``phase``.

**A model against a simulation.** An NGspice ``ac`` analysis ``AC1`` saves
``v(out)``, and ``LAPLACE1`` is the SLiCAP transfer of the same circuit.
Insert the signal ``v(out)`` of AC1: the assignment table names it
``V_out``. The trace

.. code-block:: text

   dB(mag(AC1.V_out)) - dB(mag(LAPLACE1.laplace))

plots their difference in dB. LAPLACE1 is evaluated at the frequencies of
AC1, so no range is needed.
