Version 4
SymbolType CELL
LINE Normal 32 16 32 40
LINE Normal 32 96 32 72
LINE Normal -80 16 -16 16
LINE Normal -80 96 -16 96
LINE Normal -64 0 -64 112 1
LINE Normal -64 112 48 112 1
LINE Normal 48 112 48 0 1
LINE Normal 48 0 -64 0 1
LINE Normal 32 16 64 16
LINE Normal 32 96 64 96
LINE Normal -16 16 0 16
LINE Normal 0 16 0 32
LINE Normal -16 96 0 96
LINE Normal 0 96 0 80
LINE Normal -8 40 -8 72
LINE Normal 8 40 8 72
LINE Normal -48 48 -48 16
LINE Normal -48 96 -48 64
LINE Normal -40 56 -56 56
CIRCLE Normal 24 40 40 56
CIRCLE Normal 24 56 40 72
CIRCLE Normal -32 8 -16 24
CIRCLE Normal -56 48 -40 64
ARC Normal -8 48 8 32 16 40 -16 40
ARC Normal 8 64 -8 80 -16 72 16 72
TEXT 51 26 Left 2 +
WINDOW 0 0 -64 Left 2
WINDOW 38 0 -48 Left 2
WINDOW 3 0 -32 Left 2
WINDOW 123 0 -16 Left 2
SYMATTR SpiceModel N_noise
SYMATTR Value si={S_i} sv={S_v}
SYMATTR Prefix X
SYMATTR Description Nullor with equivalent-input noise sources
PIN -80 16 NONE 0
PINATTR PinName NC+
PINATTR SpiceOrder 1
PIN -80 96 NONE 0
PINATTR PinName NC-
PINATTR SpiceOrder 2
PIN 64 16 NONE 0
PINATTR PinName +
PINATTR SpiceOrder 3
PIN 64 96 NONE 0
PINATTR PinName -
PINATTR SpiceOrder 4
