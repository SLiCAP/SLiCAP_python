Version 4
SymbolType CELL
LINE Normal -16 -32 0 -32
LINE Normal -16 32 0 32
LINE Normal 64 0 64 0 1
LINE Normal 64 0 80 0
LINE Normal 0 -48 64 0
LINE Normal 0 48 0 -48
LINE Normal 64 0 0 48
LINE Normal 32 24 32 48
TEXT 6 -32 Left 2 +
TEXT 6 32 Left 2 -
WINDOW 0 -15 -96 Left 2
WINDOW 3 -16 -63 Left 2
WINDOW 38 -15 -80 Left 2
SYMATTR Value svo={sigma_vo} sib={sigma_ib} sio={sigma_io} iib={I_b}
SYMATTR SpiceModel O_dcvar
SYMATTR Prefix X
SYMATTR Description Nullor with input bias and offset sources
PIN -16 -32 NONE 0
PINATTR PinName NC+
PINATTR SpiceOrder 1
PIN -16 32 NONE 0
PINATTR PinName NC-
PINATTR SpiceOrder 2
PIN 80 0 NONE 0
PINATTR PinName +
PINATTR SpiceOrder 3
PIN 32 48 NONE 0
PINATTR PinName -
PINATTR SpiceOrder 4
