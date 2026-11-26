=====================
Files of a system run
=====================

.. image:: ../API/img/colorCode.svg

A system diagram ``sch/<stem>.system_sch`` is simulated by Python files that
SLiCAP writes into the project. This page lists them: where each file is,
what writes it and when it is written again.

The run script
==============

``<project root>/<stem>.py``

The run script describes the system of the diagram: its functions, their
connections, its clocks and its parameters. Two things write it:

- ``sl.makeCircuit("sch/<stem>.system_sch")`` in an instruction file;
- :menuselection:`File --> Export run script…` on the system sheet.

Each of them writes the file again. Do not edit it by hand: the next
``makeCircuit()`` replaces it. For the same reason an instruction file in the
project root cannot have this name. The instruction editor refuses to save
it under that name.

``sl.runSystem("<stem>", ...)`` imports the run script. Python then keeps its
compiled form (bytecode) in ``<project root>/__pycache__/<stem>.cpython-3XX.pyc``,
as for any imported module. Python renews it when the run script changes.

Filter designs
==============

``lib/<name>.py`` and its symbol ``lib/<name>.system_sym``

The filter design dialog writes a filter design as a Python file in ``lib/``.
A run executes the design files of the diagram. It does not import them, so
Python keeps no compiled form of them.

The tick program
================

``results/<stem>.tick.py``

At every run SLiCAP generates the program that computes one tick of the
system. It writes the source of that program to this file, for reading. The
run itself does not read the file: it compiles the program from memory. Every
run writes the file again.

The machine code
================

When numba is installed and every function of the system has kernels, the run
compiles the tick program to machine code (``runSystem(..., jit="auto")``,
the default). That machine code exists only in memory. It is not stored on
disk, so every run compiles it again, and the compile time is part of every
run. With ``jit=False`` the tick program runs as plain Python.

The results
===========

The results folder is ``results/`` of the project (``ini.results_path``). A run
writes:

- ``<stem>.signals.npz``: the stored signals of the run. Every run overwrites
  it.
- ``<stem>.state.npz``: the state at the end of the run. ``runSystem(...,
  resume=True)`` continues from it.
- ``<signal>.chunkNNN.npz``: the parts of a stored signal longer than 10
  million samples. The run keeps the last part in memory and writes the
  earlier parts to these files.

A stepped run (``runSystem(..., step=...)``) writes the state of each run
under the stem ``<stem>_s0``, ``<stem>_s1``, and so on. The signals of all
its runs are in the one file ``<stem>.signals.npz``.

While a run is going, the file ``<stem>.stop`` in the results folder asks it
to stop. The run checks for this file, removes it and ends after the current
block of ticks. Its state and signals are written as at a normal end.
