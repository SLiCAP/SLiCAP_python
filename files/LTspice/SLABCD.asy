Version 4
SymbolType CELL
LINE Normal -80 16 -48 16
LINE Normal -80 96 -48 96
LINE Normal -64 0 -64 112 1
LINE Normal -64 112 48 112 1
LINE Normal 48 112 48 0 1
LINE Normal 48 0 -64 0 1
LINE Normal 32 16 64 16
LINE Normal 32 96 64 96
TEXT -48 52 Center 2 Vi
TEXT 32 52 Center 2 Vo
TEXT -48 28 Center 2 +
TEXT 32 28 Center 2 +
TEXT -48 80 Center 2 -
TEXT 32 80 Center 2 -
WINDOW 0 -64 -48 Left 2
WINDOW 38 -8 132 Center 2
WINDOW 3 -64 -32 Left 2
SYMATTR SpiceModel ABCD
SYMATTR Value at={A_T} bt={B_T} ct={C_T} dt={D_T}
SYMATTR Prefix X
SYMATTR Description ABCD matrix
PIN 64 16 NONE 0
PINATTR PinName +
PINATTR SpiceOrder 1
PIN 64 96 NONE 0
PINATTR PinName -
PINATTR SpiceOrder 2
PIN -80 16 NONE 0
PINATTR PinName NC+
PINATTR SpiceOrder 3
PIN -80 96 NONE 0
PINATTR PinName NC-
PINATTR SpiceOrder 4
