============================
Schematic capture for SLiCAP
============================

.. ltspice:

-------
LTSpice
-------

A symbol set for schematic capture and netlist generation with LTSpice can be found in the ``LTspice/`` folder in the user install path (default ~/SLiCAP/).

The following table gives an overview of the available symbols. Model descriptions can be found in the `Device Models <../syntax/netlist.html#devices-and-built-in-models>`__ section.

    ========= ======================================================================= ====== =================================
    name      description                                                             models corresponding sub circuits
    ========= ======================================================================= ====== =================================
    SLABCD    Sub circuit of a two-port with T1 matrix parameters                            ABCD
    SLC       Linear capacitor                                                        C
    SLD       Small-signal diode model                                                D
    SLE       Voltage-controlled voltage source                                       E
    SLEZ      Voltage-controlled voltage source with series impedance                 EZ
    SLF       Current-controlled current source                                       F
    SLG       Voltage-controlled current source                                       G
    SLH       Current-controlled voltage source                                       H
    SLHZ      Current-controlled voltage source with series impedance                 HZ
    SLI       Independent current source                                              I
    SLJ       Small-signal model of a Junction FET                                    J
    SLL       Linear inductor                                                         L
    SLM       Small-signal model of a four-terminal MOS transistor                    M
    SLMD      Small-signal model of a MOS differential pair                           MD
    SLM_noise Equivalent-input noise sources of intrinsic MOS, EKV model                     NM18_noise, PM18_noise, J_noise
    SLN       Nullor                                                                  N
    SLN_noise Nullor with input noise sources                                                N_noise
    SLN_dcvar Nullor with input bias and offset sources (separate ground)                    N_dcvar
    SLO       Small-signal model of an operational amplifier                          OC, OV
    SLO_noise Nullor with input noise sources (opamp symbol)                                 O_noise
    SLO_dcvar Nullor with input bias and offset sources (opamp symbol)                       O_dcvar
    SLQ       Small-signal model of a bipolar transistor (BJT)                        QV, QL
    SLQD      Small-signal model of a BJT differential pair                           QD
    SLQ_noise Equivalent-input noise sources of intrinsic BJT, GP model                      Q_noise
    SLR       Linear resistor cannot have zero value                                  R
    SLR_r     Linear resistor can have zero value and tolerance                       r
    SLT       Ideal transformer (also works for DC!)                                  T
    SLXM      Sub circuit MOS, EKV model                                                     CMOS18N, CMOS18P
    SLXMD     Sub circuit differential pair MOS, horizontal, EKV model                       CMOS18ND, CMOS18PD
    SLXQ      Sub circuit BJT, GP model                                                      BJTV4, BJTL4
    SLXQD     Sub circuit differential pair BJT, horizontal, GP model                        BJTD
    SLV       Independent voltage source                                              V
    SLW       Ideal gyrator                                                           W
    ========= ======================================================================= ====== =================================

A graphic overview of the LTSpice symbols is shown below. Click on the figure to enlarge it.

.. figure:: ../img/devicesLTspice.svg
    :width: 800px
    :alt: SLiCAP symbols for LTSpice

SPICE directives
----------------

Parameter definitions ``.param``, model definitions ``.model``, library definitions ``.lib`` can be placed on a schematic page using **spice directives**. LTSpice also defines the coupling between inductors with the aid of spice directives.

.. gschem:

---------------------
gSchem and lepton-eda
---------------------

A symbol set for schematic capture and netlist generation with gSchem or lepton-eda can be found in the ``gSchem/symbols/`` folder and in the ``lepton-eda/symbols/`` folder in the user install path (default ~/SLiCAP/).

The following table gives an overview of the available symbols. Model descriptions can be found in the `Device Models <../syntax/netlist.html#devices-and-built-in-models>`__ section. Please scroll the table to the left to see the associated sub circuits.

    ======== ======================================================================= ====== =================================
    name     description                                                             models corresponding sub circuits
    ======== ======================================================================= ====== =================================
    0        Node "0" reference or ground node symbol
    ABCD     Sub circuit of a two-port with T1 matrix parameters                            ABCD
    C        Linear capacitor                                                        C
    D        Small-signal diode model                                                D
    E        Voltage-controlled voltage source                                       E
    EZ       Voltage-controlled voltage source with series impedance                 EZ
    F        Current-controlled current source                                       F
    G        Voltage-controlled current source                                       G
    H        Current-controlled voltage source                                       H
    HZ       Current-controlled voltage source with series impedance                 HZ
    I        Independent current source                                              I
    J        Small-signal model of a Junction FET                                    J
    K        Coupling factor (between two inductors)                                 K
    L        Linear inductor                                                         L
    M        Small-signal model of a four-terminal MOS transistor                    M
    MD-H     Small-signal model of a MOS differential pair, horizontal               MD
    MD-V     Small-signal model of a MOS differential pair, vertical                 MD
    M_noise  Equivalent-input noise sources of intrinsic MOS, EKV model                     NM18_noise, PM18_noise, J_noise
    N        Nullor                                                                  N
    N_noise  Nullor with input noise sources                                                N_noise
    N_dcvar  Nullor with input bias and offset sources (separate ground)                    N_dcvar
    O        Small-signal model of an operational amplifier                          OC, OV
    O_noise  Nullor with input noise sources (opamp symbol)                                 O_noise
    O_dcvar  Nullor with input bias and offset sources (opamp symbol)                       O_dcvar
    Q        Small-signal model of a bipolar transistor (BJT)                        QV, QL
    QD-H     Small-signal model of a BJT differential pair, horizontal               QD
    QD-V     Small-signal model of a BJT differential pair, vertical                 QD
    Q_noise  Equivalent-input noise sources of intrinsic BJT, GP model                      Q_noise
    R        Linear resistor cannot have zero value                                  R
    R_r      Linear resistor can have zero value and tolerance                       r  
    T        Ideal transformer (also works for DC!)                                  T
    XM       Sub circuit MOS, EKV model saturation region only                              CMOS18N, CMOS18P
    XMD-H    Sub circuit differential pair MOS, horizontal, EKV model, sat.                 CMOS18ND, CMOS18PD
    XMD-V    Sub circuit differential pair MOS, vertical, EKV model, sat.                   CMOS18ND, CMOS18PD
    XMV      Sub circuit MOS, EKV model linear + saturation region                          CMOS18N_V, CMOS18N_P
    XQ       Sub circuit BJT, GP model, forward active region                               BJTV4, BJTL4
    XQD-H    Sub circuit differential pair BJT, horizontal, GP model, fwd. act.             BJTD
    XQD-V    Sub circuit differential pair BJT, vertical, GP model, fwd. act.               BJTD
    V        Independent voltage source                                              V
    W        Ideal gyrator                                                           W
    Z        Impedance can be defined with a Laplace rational                        Z
    include  Spice .include directive
    modelDef Spice .model directive
    parDef   Spice .param directive
    ======== ======================================================================= ====== =================================
    
A graphic overview of the gSchem symbols is shown below. Click on the figure to enlarge it.

.. figure:: ../img/devicesGschem.svg
    :width: 800px
    :alt: SLiCAP symbols for gSchem

Node names
----------

It is recommended to label the nets with names or numbers. This can be done by connecting a label to a net. Net '0' is the ground net; it is labeled as such by connecting the LTspice ground symbol to it. SLiCAP will use the node names as subscripts in the names of the nodal voltages. Hence, SLiCAP will name the voltage at node 'out' as 'V_out'. Do not use 'in' as netname; it conflicts with a MuPAD reserved name. It is recommended to use numbers and/or meaningful and short names.
    
SPICE directives
----------------

Parameter definitions ``.param``, model definitions ``.model``, library definitions ``.lib`` can be placed on a schematic page using the corresponding symbols.

--------------
SLiCAP library
--------------

SLiCAP comes with a library with device models and sub circuits.

Models of devices and sub circuits are located in the ``/lib`` sub directory of your SLiCAP installation folder. You can adapt these models to your needs, and
save them under a **different** name in your project directory or in the lib directory and call them from your circuit or schematic with the ``.lib`` spice directive. 

slicap.lib
----------

The table below gives an overview of the slicap.lib file. 

An 'm' in the type column indicates a device model definition for a SLiCAP built-in model(**.model** directive). Model parameters for built-in models can be found in the `Device Models <../syntax/netlist.html#devices-and-built-in-models>`__ section. 

An 's' in the type column indicates a sub circuit definition (**.subckt** ... **.ends**). Please scroll the table to the left to see the associated schematic symbols.

    =========== =============================================== ==== ====================== ============ =============
    name        description                                     type parameters             gschem       LTspice
    =========== =============================================== ==== ====================== ============ =============
    AD8610      Voltage-feedback opamp                          m                           O            SLO
    AD8610_A0   As above, but DC gain symbolic                  m    A0	                    O            SLO
    AD8065      Voltage-feedback opamp                          m                           O            SLO
    AD8065_A0   As above, but DC gain symbolic                  m    A0	                    O            SLO
    OPA211      Voltage-feedback opamp	                        m                           O            SLO
    OPA211_A0   As above, but DC gain symbolic	                m    A0	                    O            SLO
    OPA300      Voltage-feedback opamp	                        m                           O            SLO
    OPA300_A0   As above, but DC gain symbolic	                m    A0	                    O            SLO
    OPA627      Voltage-feedback opamp	                        m                           O            SLO
    OPA627_A0   As above, but DC gain symbolic	                m    A0	                    O            SLO
    NDD03N80Z   Power NMOS                                      m                           M            SLM
    ABCD        Two-port with transmission-1 parameters	        s    A, B, C, D  	        ABCD         SLABCD
    N_noise     Nullor with equivalent-input noise sources      s    si, sv	                N_noise      SLN_noise
    N_dcvar     Nullor with equivalent-input bias and offset    s    sib, sio, svo, iib	    N_dcvar      SLN_dcvar
    O_noise     Nullor with equivalent-input noise sources      s    si, sv	                O_noise      SLO_noise
    O_dcvar     Nullor with equivalent-input bias and offset    s    sib, sio, svo, iib	    O_dcvar      SLO_dcvar
    CMOS18N     NMOS CMOS 180nm EKV model                       s    ID, L, W               XM           SLXM
    CMOS18N_V   NMOS CMOS 180nm EKV model, voltage-controlled   s    VD, VG, VS, W, L	    XMV          SLXM_V
    CMOS18ND    NMOS diff-pair CMOS 180nm EKV model             s    ID, L, W	            XMD-H, XMD-V SLXMD
    CMOS18P     PMOS CMOS 180nm EKV model                       s    ID, L, W	            XM           SLXM
    CMOS18P_V   PMOS CMOS 180nm EKV model, voltage-controlled   s    VD, VG, VS, W, L	    XMV          SLXM_V
    CMOS18PD    PMOS diff-pair CMOS 180nm EKV model             s    ID, L, W	            XMD-H, XMD-V SLXMD
    BJTV4       Vertical Bipolar Junction Transistor            s    IC, VCE	            XQ           SLXQ
    BJTL4       Lateral Bipolar Junction Transistor             s    IC, VCE	            XQ           SLXQ
    BJTD        Differential-pair BJT                           s    IC, VCE	            XQD-H, XQD-V SLXQD
    NM18_noise  NMOS 180nm equivalent-input noise EKV model     s    ID, IG, W, L	        M_noise      SLM_noise
    NM18_noise  PMOS 180nm equivalent-input noise EKV model     s    ID, IG, W, L	        M_noise      SLM_noise
    J_noise     MOS/JFET equivalent-input noise sources         s    ID, IG, W, L	        M_noise      SLM_noise
    Q_noise     BJT equivalent-input noise sources, r_b=0       s    IC, VCE	            Q_noise      SLQ_noise
    =========== =============================================== ==== ====================== ============ =============
