Version 4
SymbolType CELL
LINE Normal 112 -80 112 -56
LINE Normal 112 0 112 -24
LINE Normal 0 -80 64 -80
LINE Normal 0 0 64 0
LINE Normal 112 -80 144 -80
LINE Normal 112 0 144 0
LINE Normal 64 -80 80 -80
LINE Normal 80 -80 80 -64
LINE Normal 64 0 80 0
LINE Normal 80 0 80 -16
LINE Normal 72 -56 72 -24
LINE Normal 88 -56 88 -24
LINE Normal 32 -48 32 -80
LINE Normal 32 0 32 -32
LINE Normal 40 -40 24 -40
LINE Normal 56 -96 56 -112
LINE Normal 16 -104 48 -104
LINE Normal 16 -80 16 -104
LINE Normal 96 -104 64 -104
LINE Normal 96 32 96 -104
LINE Normal 16 16 16 0
LINE Normal 48 16 16 16
LINE Normal 56 24 56 8
LINE Normal 96 16 64 16
LINE Normal 65 -116 48 -116
LINE Normal 62 -115 65 -116
LINE Normal 62 -117 62 -115
LINE Normal 65 -116 62 -117
LINE Normal 65 4 48 4
LINE Normal 62 5 65 4
LINE Normal 62 3 62 5
LINE Normal 65 4 62 3
CIRCLE Normal 104 -56 120 -40
CIRCLE Normal 104 -40 120 -24
CIRCLE Normal 48 -88 64 -72
CIRCLE Normal 24 -48 40 -32
CIRCLE Normal 48 8 64 24
CIRCLE Normal 48 -112 64 -96
ARC Normal 72 -48 88 -64 96 -56 64 -56
ARC Normal 88 -32 72 -16 64 -24 96 -24
TEXT 37 -24 Left 2 io
TEXT 49 -64 Left 2 vo
TEXT 52 33 Left 2 iib
TEXT 71 -116 Left 2 iib
TEXT 128 -69 Left 2 +
WINDOW 3 112 -144 Left 2
WINDOW 123 112 -128 Left 2
WINDOW 39 112 -112 Left 2
WINDOW 40 112 -96 Left 2
WINDOW 0 113 -176 Left 2
WINDOW 38 113 -160 Left 2
SYMATTR Value svo={sigma_vo} sib={sigma_ib} sio={sigma_io} iib={I_b}
SYMATTR SpiceModel N_dcvar
SYMATTR Prefix X
SYMATTR Description Nullor with input bias and offset sources
PIN 0 -80 NONE 0
PINATTR PinName NC+
PINATTR SpiceOrder 1
PIN 0 0 NONE 0
PINATTR PinName NC-
PINATTR SpiceOrder 2
PIN 144 -80 NONE 0
PINATTR PinName +
PINATTR SpiceOrder 3
PIN 144 0 NONE 0
PINATTR PinName -
PINATTR SpiceOrder 4
PIN 96 32 NONE 8
PINATTR PinName common
PINATTR SpiceOrder 5
