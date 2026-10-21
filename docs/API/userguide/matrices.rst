==============================
SLiCAP circuit matrix equation
==============================

.. image:: /API/img/colorCode.svg

One of the first steps in the execution of each instruction is the construction of the MNA matrix equation (MNA: Modified Nodal Analysis). The matrix equation depends on the transfer type and the conversion type. 

Every instruction returns the MNA matrix equation. The instruction ``doMatrix()`` returns the matrix equation without evaluating anything. It is the fastest way to obtain this equation.

The default settings of the transfer type and the conversion type in the ``doMatrix()`` are both ``None``.

Settings for transfer types will be discussed in `Work with feedback circuits <feedback.html>`_.

Settings for conversion types will be discussed in `Work with balanced circuits <balanced.html>`_.

.. image:: /API/img/colorCode.svg
   
SLiCAP output dispalyed on this manual page, is generated with the script: ``matrix.py``, imported by ``Manual.py``.

.. literalinclude:: ../matrix.py
    :linenos:
    :lines: 1-7
    :lineno-start: 1

Obtain the matrix equation of the circuit
=========================================

.. literalinclude:: ../matrix.py
    :linenos:
    :lines: 9-20
    :lineno-start: 9

The result is shown below:

.. image:: /API/img/Transimpedance.svg
    :scale: 80 %

.. code-block:: text

    Matrix([[0], [I_s], [0]])
    Matrix([[0, 1, 0], [0, C_s*s + 1/R_t, -1/R_t], [1, -1/R_t, 1/R_t]])
    Matrix([[I_N1], [V_1], [V_out]])
    
Naming of the dependent variables
=================================

Nodal voltages are named as ``V_<node_name>``, where ``node_name`` is the name of the node.

Branch currents are named as ``I_<ref_des>``, where ``ref_des`` is the reference designator of the branch element. 
    
Reactive elements and the time-constant matrix
==============================================

With ``method="tc"``, ``doMatrix()`` returns the first-order MNA matrix
:math:`\mathbf{M} = \mathbf{G} + s\mathbf{C}`, in which controlled sources
with a Laplace rational transfer are expanded into integrator chains, as with
``method="state"``. In addition it returns the reactive elements of the
network:

- ``.Nr``: the incidence matrix of the reactive elements, one column per
  reactance and one row per network variable: the incidence vector of a
  capacitor (:math:`+1` at its first node, :math:`-1` at its second), the unit
  vector of the current of an inductor, and the unit vector of an integrator
  variable of an expanded controlled source;
- ``.Cr``: the matrix of their values: :math:`C` for a capacitor, :math:`-L`
  for an inductor, :math:`-M` off the diagonal for a mutual inductance, and
  :math:`1` for an integrator variable;
- ``.reactances``: the names of the columns: the reference designators of the
  capacitors and the inductors, then the names of the integrator variables,
  each in netlist order;
- ``.Rr``: the resistance matrix
  :math:`\mathbf{R}_\mathrm{r} = \mathbf{N}_\mathrm{r}^T\mathbf{G}^{-1}\mathbf{N}_\mathrm{r}`,
  with :math:`\mathbf{G}` the matrix :math:`\mathbf{M}` at :math:`s=0`: the DC
  transfers between the ports of the reactive elements, with the capacitors
  replaced with current sources and the inductors with voltage sources. It is
  ``None`` if the network has no DC solution.

The coefficient matrix of :math:`s` is
:math:`\mathbf{C} = \mathbf{N}_\mathrm{r}\mathbf{C}_\mathrm{r}\mathbf{N}_\mathrm{r}^T`,
and the time-constant matrix follows as
:math:`\mathbf{T}_\mathrm{r} = \mathbf{R}_\mathrm{r}\mathbf{C}_\mathrm{r}`
when :math:`\mathbf{G}` is invertible:

.. code-block:: python

    import SLiCAP as sl
    res = sl.doMatrix(cir, method="tc")
    Tr  = res.Rr * res.Cr                      # time-constant matrix

The entries of ``.Cr`` for integrator variables have no physical meaning:
the time constants of an expanded transfer are in the coefficients of its
chain. ``method="tc"`` is only available for ``doMatrix()``, without a
conversion type and without stepping. A network with an improper transfer
(numerator order above denominator order) has no first-order form: then
``.Nr``, ``.Cr``, ``.reactances`` and ``.Rr`` are ``None``.

Display the matrix equation on HTML pages and in LaTeX documents
================================================================

With the aid of the report module `Creating reports <reports.html>`_, the matrix equation can be displayed on HTML pages or in LaTeX documents. 

Below the script for generating the rst snippet for this help file.

.. literalinclude:: ../matrix.py
    :linenos:
    :lines: 22-25
    :lineno-start: 22
    
The result is shown below.

.. include:: ../sphinx/SLiCAPdata/eqn-matrix-trimp.rst

.. image:: /API/img/colorCode.svg
