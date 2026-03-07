.. csv-table:: Expanded netlist element data
    :header: "ID", "Nodes", "Refs", "Model", "Param", "Symbolic", "Numeric"
    :widths: auto

    "R1", "4 in ", "", "R", "value", :math:`R_{s}`, :math:`50`
    "", "", "", "", "noisetemp", :math:`0`, :math:`0`
    "", "", "", "", "noiseflow", :math:`0`, :math:`0`
    "", "", "", "", "dcvar", :math:`0`, :math:`0`
    "", "", "", "", "dcvarlot", :math:`0`, :math:`0`
    "R2", "1 0 ", "", "R", "value", :math:`R_{a}`, :math:`R_{a}`
    "", "", "", "", "noisetemp", :math:`0`, :math:`0`
    "", "", "", "", "noiseflow", :math:`0`, :math:`0`
    "", "", "", "", "dcvar", :math:`0`, :math:`0`
    "", "", "", "", "dcvarlot", :math:`0`, :math:`0`
    "R3", "2 1 ", "", "R", "value", :math:`R_{a} \left(A_{1} - 1\right)`, :math:`R_{a} \left(A_{1} - 1\right)`
    "", "", "", "", "noisetemp", :math:`0`, :math:`0`
    "", "", "", "", "noiseflow", :math:`0`, :math:`0`
    "", "", "", "", "dcvar", :math:`0`, :math:`0`
    "", "", "", "", "dcvarlot", :math:`0`, :math:`0`
    "R4", "in out ", "", "R", "value", :math:`R_{f}`, :math:`R_{f}`
    "", "", "", "", "noisetemp", :math:`0`, :math:`0`
    "", "", "", "", "noiseflow", :math:`0`, :math:`0`
    "", "", "", "", "dcvar", :math:`0`, :math:`0`
    "", "", "", "", "dcvarlot", :math:`0`, :math:`0`
    "R5", "2 3 ", "", "R", "value", :math:`R_{b}`, :math:`R_{b}`
    "", "", "", "", "noisetemp", :math:`0`, :math:`0`
    "", "", "", "", "noiseflow", :math:`0`, :math:`0`
    "", "", "", "", "dcvar", :math:`0`, :math:`0`
    "", "", "", "", "dcvarlot", :math:`0`, :math:`0`
    "R6", "3 out ", "", "R", "value", :math:`A_{2} R_{b}`, :math:`A_{2} R_{b}`
    "", "", "", "", "noisetemp", :math:`0`, :math:`0`
    "", "", "", "", "noiseflow", :math:`0`, :math:`0`
    "", "", "", "", "dcvar", :math:`0`, :math:`0`
    "", "", "", "", "dcvarlot", :math:`0`, :math:`0`
    "V1", "4 0 ", "", "V", "value", :math:`0`, :math:`0`
    "", "", "", "", "noise", :math:`0`, :math:`0`
    "", "", "", "", "dc", :math:`0`, :math:`0`
    "", "", "", "", "dcvar", :math:`0`, :math:`0`
    "E_O1", "2 0 in 1 ", "", "EZ", "value", :math:`\frac{A_{0}}{1 + \frac{0.5 s}{\pi p_{1}}}`, :math:`\frac{A_{0}}{1 + \frac{0.1592 s}{p_{1}}}`
    "", "", "", "", "zo", :math:`R_{o}`, :math:`R_{o}`
    "Gd_O1", "in 1 in 1 ", "", "g", "value", :math:`0`, :math:`0`
    "Gc1_O1", "in 0 in 0 ", "", "g", "value", :math:`0`, :math:`0`
    "Gc2_O1", "1 0 1 0 ", "", "g", "value", :math:`0`, :math:`0`
    "Cd_O1", "in 1 ", "", "C", "value", :math:`0`, :math:`0`
    "", "", "", "", "vinit", :math:`0`, :math:`0`
    "Cc1_O1", "in 0 ", "", "C", "value", :math:`0`, :math:`0`
    "", "", "", "", "vinit", :math:`0`, :math:`0`
    "Cc2_O1", "1 0 ", "", "C", "value", :math:`0`, :math:`0`
    "", "", "", "", "vinit", :math:`0`, :math:`0`
    "E_O2", "out 0 0 3 ", "", "EZ", "value", :math:`\frac{A_{0}}{1 + \frac{0.5 s}{\pi p_{1}}}`, :math:`\frac{A_{0}}{1 + \frac{0.1592 s}{p_{1}}}`
    "", "", "", "", "zo", :math:`R_{o}`, :math:`R_{o}`
    "Gd_O2", "0 3 0 3 ", "", "g", "value", :math:`0`, :math:`0`
    "Gc1_O2", "0 0 0 0 ", "", "g", "value", :math:`0`, :math:`0`
    "Gc2_O2", "3 0 3 0 ", "", "g", "value", :math:`0`, :math:`0`
    "Cd_O2", "0 3 ", "", "C", "value", :math:`0`, :math:`0`
    "", "", "", "", "vinit", :math:`0`, :math:`0`
    "Cc1_O2", "0 0 ", "", "C", "value", :math:`0`, :math:`0`
    "", "", "", "", "vinit", :math:`0`, :math:`0`
    "Cc2_O2", "3 0 ", "", "C", "value", :math:`0`, :math:`0`
    "", "", "", "", "vinit", :math:`0`, :math:`0`

