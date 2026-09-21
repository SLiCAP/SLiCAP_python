============================
Schematic capture for SLiCAP
============================

.. image:: ../img/colorCode.svg

SLiCAP
======

Creation of SLiCAP schematics in discussed in the section: `Structured Electronic Design Environment <../../GUI/index.html>`_.


Below a list of elementary SLiCAP components. The **Symbol ID** is the first letter of the reference designator

See `SLiCAP netlist syntax <../syntax/netlist.html>`_ for more information.

========= ======================================================================= ========================================================================== 
Symbol ID description                                                             models 
========= ======================================================================= ========================================================================== 
C         Linear capacitor                                                        `C <../syntax/devices.html#c-capacitor>`_
D         Small-signal diode model                                                `D <../syntax/devices.html#d-diode>`_
E         Voltage-controlled voltage source                                       `E, EZ <../syntax/devices.html#e-voltage-controlled-voltage-source>`_
F         Current-controlled current source                                       `F <../syntax/devices.html#f-current-controlled-current-source>`_
G         Voltage-controlled current source                                       `G <../syntax/devices.html#g-voltage-controlled-current-source>`_
H         Current-controlled voltage source                                       `H, HZ <../syntax/devices.html#h-current-controlled-voltage-source>`_
I         Independent current source                                              `I <../syntax/devices.html#i-independent-current-source>`_
J         Small-signal model of a Junction FET                                    `J <../syntax/devices.html#j-junction-fet>`_
K         Coupling factor (between two inductors)                                 `K <../syntax/devices.html#k-coupling-factor>`_
L         Linear inductor                                                         `L <../syntax/devices.html#l-inductor>`_
M         Small-signal model of a four-terminal MOS transistor                    `M, MD <../syntax/devices.html#m-4-terminal-mos>`_
N         Nullor                                                                  `N <../syntax/devices.html#n-nullor>`_
O         Small-signal model of an operational amplifier                          `OC, OV <../syntax/devices.html#o-operational-amplifier>`_
Q         Small-signal model of a bipolar transistor (BJT)                        `QV, QL, QD <../syntax/devices.html#q-4-terminal-bjt>`_
R         Linear resistor cannot have zero value                                  `R, r <../syntax/devices.html#r-resistor>`_
T         Ideal transformer (also works for DC!)                                  `T <../syntax/devices.html#t-ideal-transformer>`_
V         Independent voltage source                                              `V <../syntax/devices.html#v-independent-voltage-source>`_
W         Gyrator                                                                 `W <../syntax/devices.html#w-gyrator>`_
X         Subcircuit                                                              `X <../syntax/devices.html#x-sub-circuit-call>`_
========= ======================================================================= ========================================================================== 

SLiCAP library
==============

SLiCAP comes with a library with device models and subcircuits.

Models of devices and sub circuits are located in the ``/lib`` sub directory of your SLiCAP installation folder. 

.. code-block:: python

    >>> sl.ini.main_lib_path
    
    '/USR/ENV/anton/lib/python3.12/site-packages/SLiCAP/files/lib/'

SLiCAP.lib: models and subcircuits
----------------------------------

The table below gives an overview of the contents of the SLiCAP.lib file. 

An **m** in the type column indicates a device model definition for a SLiCAP built-in model (**.model** directive). 

Model parameters for built-in models can be found in the `Device Models <../syntax/devices.html#devices-and-built-in-models>`__ section. 

An **s** in the type column indicates a sub circuit definition (**.subckt** ... **.ends**). Parameters that can be passed to these subcircuits are listed in the table.

The last four columns give the schematic symbol names that can be used for these devices in SLiCAP, KiCAD, gschem/Lepton-EDA, and LTspice

================= ======================================================= ==== ================================ ====== ============== ================== ===============
name              description                                             type parameters                       SLiCAP KiCAD          gschem/Lepton-EDA  LTspice
================= ======================================================= ==== ================================ ====== ============== ================== ===============
AD8610            Voltage-feedback opamp                                  m                                     OM     O              O                  SLO
AD8610_A0         As above, but DC gain symbolic                          m    A0                               OM     O              O                  SLO
AD8065            Voltage-feedback opamp                                  m                                     OM     O              O                  SLO
AD8065_A0         As above, but DC gain symbolic                          m    A0                               OM     O              O                  SLO
OPA209            Voltage-feedback opamp                                  m                                     OM     O              O                  SLO
OPA209_A0         As above, but DC gain symbolic                          m    A0                               OM     O              O                  SLO
OPA211            Voltage-feedback opamp                                  m                                     OM     O              O                  SLO
OPA211_A0         As above, but DC gain symbolic                          m    A0                               OM     O              O                  SLO
OPA300            Voltage-feedback opamp                                  m                                     OM     O              O                  SLO
OPA300_A0         As above, but DC gain symbolic                          m    A0                               OM     O              O                  SLO
OPA627            Voltage-feedback opamp                                  m                                     OM     O              O                  SLO
OPA627_A0         As above, but DC gain symbolic                          m    A0                               OM     O              O                  SLO
NDD03N80Z         Power NMOS                                              m                                     M      M              M                  SLM
STD7N80K5         Power NMOS                                              m                                     M      M              M                  SLM
ABCD              Two-port with transmission-1 parameters                 s    A, B, C, D                                             ABCD               SLABCD
N_noise           Nullor with equivalent-input noise sources              s    si, sv                           Nnoise N_noise        N_noise            SLN_noise
N_dcvar           Nullor with equivalent-input bias and offset            s    sib, sio, svo, iib               Ndcvar N_dcvar        N_dcvar            SLN_dcvar
O_noise           Nullor with equivalent-input noise sources              s    si, sv                           Onoise O_noise        O_noise            SLO_noise
O_dcvar           Nullor with equivalent-input bias and offset            s    sib, sio, svo, iib               Odcvar O_dcvar        O_dcvar            SLO_dcvar
CMOS18N           NMOS CMOS 180nm EKV model                               s    ID, L, W                         MX     XM             XM                 SLXM
CMOS18N_V         NMOS CMOS 180nm EKV model, voltage-controlled           s    VD, VG, VS, W, L                 MXV    XMV            XMV                SLXM_V
CMOS18ND          NMOS diff-pair CMOS 180nm EKV model                     s    ID, L, W                         MDX    XMD            XMD-H, XMD-V       SLXMD
CMOS18P           PMOS CMOS 180nm EKV model                               s    ID, L, W                         MX     XM             XM                 SLXM
CMOS18P_V         PMOS CMOS 180nm EKV model, voltage-controlled           s    VD, VG, VS, W, L                 MXV    XMV            XMV                SLXM_V
CMOS18PD          PMOS diff-pair CMOS 180nm EKV model                     s    ID, L, W                         MDX    XMD            XMD-H, XMD-V       SLXMD
CMOS18PN          P-N complementary parallel CMOS 180nm EKV model         s    W_N, L_N, ID_N, W_P, L_P, ID_P   MPNX   XMPN           XMPN               SLXMPN
BJTV4             Vertical Bipolar Junction Transistor                    s    IC, VCE                          QX     XQ             XQ                 SLXQ
BJTL4             Lateral Bipolar Junction Transistor                     s    IC, VCE                          QX     XQ             XQ                 SLXQ
BJTD              Differential-pair BJT                                   s    IC, VCE                          QDX    XQD            XQD-H, XQD-V       SLXQD
NM18_noise        NMOS 180nm equivalent-input noise EKV model             s    ID, IG, W, L                     Mnoise M_noise        M_noise            SLM_noise
PM18_noise        PMOS 180nm equivalent-input noise EKV model             s    ID, IG, W, L                     Mnoise M_noise        M_noise            SLM_noise
NM18_noisyNullor  Nullor with NMOS 180nm equivalent-input noise EKV model s    ID, IG, W, L                            XM_noisyNullor XM_noisyNullor     SLM_noisyNullor
PM18_noisyNullor  Nullor with PMOS 180nm equivalent-input noise EKV model s    ID, IG, W, L                            XM_noisyNullor XM_noisyNullor     SLM_noisyNullor
J_noise           MOS/JFET equivalent-input noise sources                 s    ID, IG, W, L                     Jnoise J_noise        M_noise            SLM_noise        
Q_noise           BJT equivalent-input noise sources, r_b=0               s    IC, VCE                          Qnoise Q_noise        Q_noise            SLQ_noise
================= ======================================================= ==== ================================ ====== ============== ================== ===============

Wide table: slide below the table!

.. image:: /API/img/colorCode.svg
