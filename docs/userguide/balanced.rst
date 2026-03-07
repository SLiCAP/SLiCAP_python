===========================
Work with balanced circuits
===========================

.. image:: ../img/colorCode.svg

Balancing is a powerful design technique. Apply balancing to:

#. Create four-terminal networks from three-terminal networks using *anti-series* connection
#. Create odd transfer characteristics with voltage-limiting or current-limiting characteristics using *complementary-parallel* connection or *anti-series* connection of nonlinear devices, respectively.

The signal transfer of balanced circuits is often decomposed in a differential-mode, and a common-mode transfer. In many applications of balanced networks, the differential-mode voltages and currents are of interest, while common-mode voltages and currents are either zero, or should not affect the differential-mode transfer.

SLiCAP has a built-in method to convert nodal voltages and branch currents into differential voltages, differential currents, common-mode voltages, and common-mode currents (for theory see: `Structured Electronics Design <https://books.open.tudelft.nl/home/catalog/book/162>`_).

In a fully balanced network, differential-mode and common-mode quantities are orthogonal, and balanced circuits are decomposed into two independent network models: one modeling the differential-mode behavior and the other the common-mode behavior.

Using two independent network models helps to design the desired common-mode and differential-mode behavior with minimized network models.

Settings for CM and DM decompositon
===================================

SLiCAP balanced network decomposition is based upon pairing nodes, branches and parameters. 

The decomposition itself is initiated by setting the argument ``convtype`` in an `instruction <../reference/SLiCAPshell.html#general-instruction-format>`__ to:

#. **"all"**: SLiCAP decomposes paired node voltages and paired branch currents into pairs of common-mode and differential-mode voltages and currents. Convertion type ``all`` can only be used for displaying the matrix equations; performing analysis is not implemented.
#. **"dd"**: After the above decomposition, SLiCAP can perform all types of analysis using the differential-mode matrix equation.
#. **"dc"** SLiCAP returns the differential-mode to common-mode matrix equation. Generally this involves a non-square matrix.
#. **"cd"**: SLiCAP returns the common-mode to differential-mode matrix equation. Generally this involves a non-square matrix.
#. **"cc"** After the above decomposition, SLiCAP can perform all types of analysis using the common-mode matrix equation.

Pairing nodes, branches, and parameters
=======================================

The decomposition settings for balanced networks are stored in the file ``SLiCAP.ini`` in the project directory.

.. code-block:: text

    >>> import SLiCAP as sl
    >>> sl.ini.dump("balancing")
    
    BALANCING
    ---------
    ini.pair_ext               = ['P', 'N']
    ini.update_srcnames        = True
    ini.remove_param_pair_ext  = True

#. ``ini.pair_ext``: List with two strings. These strings (*pair extensions*) are the last part of node names, element reference designators, and parameter names of paired nodes, elements, and parameters, respectively. The first part of these names must be equal.

#. ``ini.update_srcnames``: True will update the names of noise sources and dcvar sources in the results of noise and dcvar analysis, respectively.

#. ``ini.remove_param_pair_ext``: True will remove the pair extensions from the parameter names after pairing. This is useful when using paired sub circuits. Local parameters of paired sub circuits are also paired: they obtain the same name, without pair extension. 

Create balanced circuits
========================

SLiCAP output displayed on this manual page, is generated with the script: ``balanced.py``, imported by ``Manual.py``.

.. literalinclude:: ../balanced.py
    :linenos:
    :lines: 1-12
    :lineno-start: 1

Balanced passive network
------------------------
    
.. literalinclude:: ../balanced.py
    :linenos:
    :lines: 14-20
    :lineno-start: 14

.. image:: /img/balancedNetwork.svg
    :width: 400px
    
.. admonition:: Important
    :class: note
    
    #. Notice the orientation of the components in both halves of the balanced circuit:
    
       Components of the two parts of a balanced circuit must have the same orientation in each part! This is particaluarly important for components that have a branch current in their MNA stamp.
       
    #. Notice the naming of components and nodes:
    
       Paired nodes and components of the two parts of a balanced circuit have the same name plus an individual pair extension! This is particaluarly important for components that have a branch current in their MNA stamp.

Matrix equation convtype=None
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
.. include:: ../sphinx/SLiCAPdata/eqn-noneM.rst

Matrix equation convtype='all'
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
.. include:: ../sphinx/SLiCAPdata/eqn-allM.rst

.. admonition:: Important
    
    After pairing, pair extensions in the vector with nodal voltages and branch currents have been replaced with ``_D`` and ``_C`` for differential-mode and common-mode, respectively.

Matrix equation convtype='dd'
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
.. include:: ../sphinx/SLiCAPdata/eqn-ddM.rst
    :class: note

``convtype='dd'`` gives the uppper-left matrix of the square matrix from ``convtype='all'``

Matrix equation convtype='dc'
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
.. include:: ../sphinx/SLiCAPdata/eqn-dcM.rst

``convtype='dc'`` gives the uppper-right matrix of the square matrix from ``convtype='all'``

Matrix equation convtype='cd'
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
.. include:: ../sphinx/SLiCAPdata/eqn-cdM.rst

``convtype='cd'`` gives the lower-left matrix of the square matrix from ``convtype='all'``

Matrix equation convtype='cc'
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
.. include:: ../sphinx/SLiCAPdata/eqn-ccM.rst

``convtype='cc'`` gives the lower-right matrix of the square matrix from ``convtype='all'``

Check common-mode and differential-mode orthogonality
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A circuit is fully balanced if the the matrices obtained with ``convtype='dc'`` and ``convtype='cd'`` are zero:

.. literalinclude:: ../balanced.py
    :linenos:
    :lines: 22-25
    :lineno-start: 22

This yields:

.. code-block:: text

    The CM-DM decomposition is orthogonal!
    
Get the conversion matrix
~~~~~~~~~~~~~~~~~~~~~~~~~

The MNA equation (``convtype=None``) has the form:

.. math::

   \mathbf{I_{n,b} = M \cdot D_{n,b}}

where :math:`\mathbf{I_{n,b}}` is the vector with independent nodal currents and branch voltages (independent sources), :math:`\mathbf{M}` is the MNA matrix, and :math:`\mathbf{D_{n,b}}` is the vector with unknown nodal voltages and branch currents. 
    
The matrix equation for ``convtype='all'`` is:

.. math::

    \mathbf{I_{d,c}} = \mathbf{M^{\prime} \cdot D_{d,c}}

where :math:`\mathbf{I_{d,c}}` is the vector with independent differential-mode and common-mode voltage and current sources, :math:`\mathbf{D_{d,c}}` the vector with unknown differential-mode and common-mode voltages and currents, and math:`\mathbf{M^{\prime}}` the converted MNA matrix.

The converted matrices are obtained as:

.. math::

    \begin{align}
    \mathbf{I_{d,c}}    &=\mathbf{A^T}\cdot\mathbf{I_{n,b}}\\
    \mathbf{M^{\prime}} &=\mathbf{A^T \cdot M \cdot A}\\
    \mathbf{D_{d,c}}    &=\mathbf{A^{-1} \cdot D_{n,b}}
    \end{align}
    
Where :math:`\mathbf{A}` is the conversion matrix, constricted such that:

.. math::

    \mathbf{D_{n,b} = A \cdot D_{d,c}}

For theory see: `Structured Electronics Design <https://books.open.tudelft.nl/home/catalog/book/162>`_.

for this example:

.. literalinclude:: ../balanced.py
    :linenos:
    :lines: 27-28
    :lineno-start: 27

This yields:

.. code-block:: text

    Matrix([[-1, 0, 0, 0, 0, 0.500000000000000, 0, 0, 0, 0, 0, 0], [1, 0, 0, 0, 0, 0.500000000000000, 0, 0, 0, 0, 0, 0], [0, -1, 0, 0, 0, 0, 0.500000000000000, 0, 0, 0, 0, 0], [0, 1, 0, 0, 0, 0, 0.500000000000000, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1], [0, 0, -0.500000000000000, 0, 0, 0, 0, 1, 0, 0, 0, 0], [0, 0, 0.500000000000000, 0, 0, 0, 0, 1, 0, 0, 0, 0], [0, 0, 0, -0.500000000000000, 0, 0, 0, 0, 1, 0, 0, 0], [0, 0, 0, 0.500000000000000, 0, 0, 0, 0, 1, 0, 0, 0], [0, 0, 0, 0, -0.500000000000000, 0, 0, 0, 0, 1, 0, 0], [0, 0, 0, 0, 0.500000000000000, 0, 0, 0, 0, 1, 0, 0]])
        
Typesetted:

.. include:: ../sphinx/SLiCAPdata/eqn-matA.rst

Balanced circuit with models
----------------------------

.. literalinclude:: ../balanced.py
    :linenos:
    :lines: 30-32
    :lineno-start: 30
    
.. image:: /img/balancedAmp.svg
    :width: 550px

.. admonition:: Important
    :class: note
    
    The scope of parameters defined in a (sub) circuit ``.model`` statement is the (sub) circuit in which they are defined.

n this example model parameters are defined in the main circuit. Hence, no extensions ``P`` or ``N`` wil be added to the parameter names:

.. literalinclude:: ../balanced.py
    :linenos:
    :lines: 33-34
    :lineno-start: 34 

.. code-block:: text

    {'value': A_0/(1 + s/(2*pi*f_p1)), 'zo': 1000}
    {'value': A_0/(1 + s/(2*pi*f_p1)), 'zo': 1000}
    
The matrix equation with ``convtype='all'``:

.. literalinclude:: ../balanced.py
    :linenos:
    :lines: 35-36
    :lineno-start: 35 
    
.. include:: ../sphinx/SLiCAPdata/eqn-VampAll.rst

Balanced circuit with sub circuits
----------------------------------

Below a balanced circuit built-up from two equal sub circuits.

.. image:: /img/BJTdiffAmp.svg
    :width: 400 px

The figure below shows the sub circuit diagram.

.. image:: /img/myBJTamp.svg
    :width: 450 px

.. literalinclude:: ../balanced.py  
    :linenos:
    :lines: 38-40
    :lineno-start: 38 
    
The scope of the model parameters is now limited to the sub circuit.

.. literalinclude:: ../balanced.py  
    :linenos:
    :lines: 42-44
    :lineno-start: 42  
  
Typesetted result:
  
.. include:: ../sphinx/SLiCAPdata/eqn-BJTampAllMF.rst

.. literalinclude:: ../balanced.py  
    :linenos:
    :lines: 45-50
    :lineno-start: 45
    
This yields:

.. code-block:: text

    [g_o_X1P, R_f_X1N, g_o_X1N, R_f_X1P, R_s, g_m_X1N, R_a, beta_AC_X1N, beta_AC_X1P, g_m_X1P]
    {}
    [g_o_X1P, R_f_X1N, g_o_X1N, R_f_X1P, R_s, g_m_X1N, R_a, beta_AC_X1N, beta_AC_X1P, g_m_X1P]
    {}

The default value of ``ini.remove_param_pair_ext`` is ``True``:

.. literalinclude:: ../balanced.py  
    :linenos:
    :lines: 51-59
    :lineno-start: 51
    
This yields:

.. code-block:: text

    [g_o_X1P, R_f_X1N, g_o_X1N, R_f_X1P, R_s, g_m_X1N, R_a, beta_AC_X1N, beta_AC_X1P, g_m_X1P]
    {}
    [g_m_X1, R_s, R_a, g_o_X1, R_f_X1, beta_AC_X1]
    {}

Typesetted result:

.. include:: ../sphinx/SLiCAPdata/eqn-BJTampAllMT.rst

Auto-rename detector
--------------------

With the conversion type set to ``dd``, ``dc``, ``cd``, or ``cc``, SLiCAP automatically redefines the differential voltage or current detector as the corresponding differential-mode or common-mode detector.

.. literalinclude:: ../balanced.py  
    :linenos:
    :lines: 61-64
    :lineno-start: 61
    
This prints:

.. code-block:: text

    Detector changed to: V_out_D

.. include:: ../sphinx/SLiCAPdata/eqn-AvddBJT.rst

.. literalinclude:: ../balanced.py  
    :linenos:
    :lines: 65
    :lineno-start: 65

This prints:
    
.. code-block:: text
    
    Detector changed to: V_out_C

.. include:: ../sphinx/SLiCAPdata/eqn-AvccBJT.rst

Balanced feedback
=================
    
.. image:: /img/balancedAmp.svg
    :width: 550px

.. literalinclude:: ../balanced.py  
    :linenos:
    :lines: 67-70
    :lineno-start: 67
    
Differential amplifier
----------------------

.. literalinclude:: ../balanced.py  
    :linenos:
    :lines: 72-75
    :lineno-start: 72

The table below shows all the poles of the circuit.
    
.. include:: ../sphinx/SLiCAPdata/table-polesVamp.rst

The table below shows all the zeros of the differential voltage transfer.

.. include:: ../sphinx/SLiCAPdata/table-zerosVamp.rst

The table below shows all the observable and controllable poles and zeros of the differential voltage transfer.

.. include:: ../sphinx/SLiCAPdata/table-poleszerosVamp.rst

Differential-mode circuit
-------------------------

.. literalinclude:: ../balanced.py  
    :linenos:
    :lines: 77-78
    :lineno-start: 77

The observable and controllable poles and zeros of the voltage transfer of the differential-mode equivalent circuit:
    
.. include:: ../sphinx/SLiCAPdata/table-poleszerosVampdd.rst

.. literalinclude:: ../balanced.py  
    :linenos:
    :lines: 80-98
    :lineno-start: 80

Bode plots of the feedback transfers of the differential-mode equivalent circuit.
    
.. image:: /img/Vamp_dd_fb_dB.svg
    :width: 500px
    
.. image:: /img/Vamp_dd_fb_phs.svg
    :width: 500px

Common-mode circuit
-------------------

.. literalinclude:: ../balanced.py  
    :linenos:
    :lines: 100-101
    :lineno-start: 100

The observable and controllable poles and zeros of the voltage transfer of the common-mode equivalent circuit:
    
.. include:: ../sphinx/SLiCAPdata/table-poleszerosVampcc.rst

.. literalinclude:: ../balanced.py  
    :linenos:
    :lines: 103-121
    :lineno-start: 103

Bode plots of the feedback transfers of the common-mode equivalent circuit.
    
.. image:: /img/Vamp_cc_fb_dB.svg
    :width: 500px
    
.. image:: /img/Vamp_cc_fb_phs.svg
    :width: 500px

Balanced noise
==============

.. image:: /img/balancedNoisyNetwork.svg
    :width: 600px

.. literalinclude:: ../balanced.py  
    :linenos:
    :lines: 123-124
    :lineno-start: 123

Differential output noise
-------------------------

.. literalinclude:: ../balanced.py  
    :linenos:
    :lines: 126-127
    :lineno-start: 126
    
.. include:: ../sphinx/SLiCAPdata/eqn-DMnoise.rst

Common-mode ouput noise
-----------------------

.. include:: ../sphinx/SLiCAPdata/eqn-CMnoise.rst

Output noise of the differential-mode equivalent circuit
--------------------------------------------------------

.. literalinclude:: ../balanced.py  
    :linenos:
    :lines: 132-144
    :lineno-start: 132
    
The console output:

.. code-block:: text

    Detector changed to: V_out_D
    Difference onoise full circuit and DM equivalent network: 0
    Noise sources:
    I1 : S_i
    V1N : S_vb
    V1P : S_va
    I_noise_R1N : 4*T*k/R_a
    I_noise_R1P : 4*T*k/R_a
    I_noise_R2N : 4*T*k/R_b
    I_noise_R2P : 4*T*k/R_b
    I_noise_R3 : 4*T*k/R_c
    Differential-mode noise sources contribution to DM onoise:
    V1_D : S_va + S_vb
    I_noise_R1_D : 2*T*k/R_a
    I_noise_R2_D : 2*T*k/R_b

Output noise of the common-mode equivalent circuit
--------------------------------------------------

.. literalinclude:: ../balanced.py  
    :linenos:
    :lines: 146-158
    :lineno-start: 146
    
The console output:

.. code-block:: text

    Detector changed to: V_out_C
    Difference onoise full circuit and CM equivalent network: 0
    Noise sources:
    I1 : S_i
    V1N : S_vb
    V1P : S_va
    I_noise_R1N : 4*T*k/R_a
    I_noise_R1P : 4*T*k/R_a
    I_noise_R2N : 4*T*k/R_b
    I_noise_R2P : 4*T*k/R_b
    I_noise_R3 : 4*T*k/R_c
    Common-mode noise sources contribution to CM onoise:
    I1 : S_i
    V1_C : S_va/4 + S_vb/4
    I_noise_R1_C : 8*T*k/R_a
    I_noise_R2_C : 8*T*k/R_b
    I_noise_R3 : 4*T*k/R_c

Balanced dcvar
==============

.. literalinclude:: ../balanced.py  
    :linenos:
    :lines: 160-161
    :lineno-start: 160
    
.. image:: /img/balancedAmpDCvar.svg
    :width: 800px

Differential output dc variance
-------------------------------

.. literalinclude:: ../balanced.py  
    :linenos:
    :lines: 163-164
    :lineno-start: 163
    
.. include:: ../sphinx/SLiCAPdata/eqn-DMvar.rst

Common-mode ouput dc variance
-----------------------------

.. literalinclude:: ../balanced.py  
    :linenos:
    :lines: 166-167
    :lineno-start: 166

.. include:: ../sphinx/SLiCAPdata/eqn-CMvar.rst

Output dc variance of the differential-mode equivalent circuit
--------------------------------------------------------------

.. literalinclude:: ../balanced.py  
    :linenos:
    :lines: 169-181
    :lineno-start: 169   
     
The console output:

.. code-block:: text

    Detector changed to: V_out_D
    Difference ovar full circuit and DM equivalent network: 0
    DCvar sources:
    V1N : 0
    V1P : 0
    Ib_X1N : sigma_ib**2*(R_a*R_b - 2*R_a*R_s - R_b*R_s)**2/R_b**2
    Vm_X1N : 0
    Io_X1N : sigma_io**2*(R_a*R_b + 2*R_a*R_s + R_b*R_s)**2/R_b**2
    Vo_X1N : sigma_vo**2*(2*R_a + R_b)**2/R_b**2
    Ib_X1P : sigma_ib**2*(R_a*R_b - 2*R_a*R_s - R_b*R_s)**2/R_b**2
    Vm_X1P : 0
    Io_X1P : sigma_io**2*(R_a*R_b + 2*R_a*R_s + R_b*R_s)**2/R_b**2
    Vo_X1P : sigma_vo**2*(2*R_a + R_b)**2/R_b**2
    I_dcvar_R1N : 0
    I_dcvar_R1P : 0
    I_dcvar_R2N : I_b**2*R_a**2*sigma_R**2
    V_dcvar_Lot_1 : 0
    I_dcvar_R2P : I_b**2*R_a**2*sigma_R**2
    Differential-mode dc variance sources contribution to DM onoise:
    V1_D : 0
    Ib_X1_D : 2*sigma_ib**2*(R_a*R_b - 2*R_a*R_s - R_b*R_s)**2/R_b**2
    Vm_X1_D : 0
    Io_X1_D : 2*sigma_io**2*(R_a*R_b + 2*R_a*R_s + R_b*R_s)**2/R_b**2
    Vo_X1_D : 2*sigma_vo**2*(2*R_a + R_b)**2/R_b**2
    I_dcvar_R1_D : 0
    I_dcvar_R2_D : 2*I_b**2*R_a**2*sigma_R**2

Output dc variance of the common-mode equivalent circuit
--------------------------------------------------------

.. literalinclude:: ../balanced.py  
    :linenos:
    :lines: 183-195
    :lineno-start: 183
    
The console output:

.. code-block:: text

    Detector changed to: V_out_C
    Difference ovar full circuit and CM equivalent network: 0
    DC variance sources:
    V1N : 0
    V1P : 0
    Ib_X1N : sigma_ib**2*(R_a - R_s)**2/4
    Vm_X1N : 0
    Io_X1N : sigma_io**2*(R_a + R_s)**2/4
    Vo_X1N : sigma_vo**2/4
    Ib_X1P : sigma_ib**2*(R_a - R_s)**2/4
    Vm_X1P : 0
    Io_X1P : sigma_io**2*(R_a + R_s)**2/4
    Vo_X1P : sigma_vo**2/4
    I_dcvar_R1N : 0
    I_dcvar_R1P : 0
    I_dcvar_R2N : I_b**2*R_a**2*sigma_R**2/4
    V_dcvar_Lot_1 : I_b**2*R_a**2*sigma_L**2
    I_dcvar_R2P : I_b**2*R_a**2*sigma_R**2/4
    Common-mode dc variance sources contribution to CM dc variance:
    V1_C : 0
    Ib_X1_C : sigma_ib**2*(R_a - R_s)**2/2
    Vm_X1_C : 0
    Io_X1_C : sigma_io**2*(R_a + R_s)**2/2
    Vo_X1_C : sigma_vo**2/2
    I_dcvar_R1_C : 0
    I_dcvar_R2_C : I_b**2*R_a**2*sigma_R**2/2
    V_dcvar_Lot_1 : I_b**2*R_a**2*sigma_L**2
        
.. image:: /img/colorCode.svg
