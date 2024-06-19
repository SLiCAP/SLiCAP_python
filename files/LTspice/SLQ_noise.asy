Version 4
SymbolType CELL
LINE Normal -80 16 -16 16
LINE Normal -16 16 0 16
LINE Normal -48 48 -48 16
LINE Normal -48 96 -48 64
LINE Normal -40 56 -56 56
CIRCLE Normal -32 8 -16 24
CIRCLE Normal -56 48 -40 64
TEXT -29 0 Left 2 vn
TEXT -75 56 Left 2 in
WINDOW 0 -31 48 Left 2
WINDOW 38 -32 64 Left 2
WINDOW 3 -32 83 Left 2
SYMATTR SpiceModel ?
SYMATTR Value IC={IC} VCE={VCE}
SYMATTR Prefix X
SYMATTR Description equivalent-input noise sources BJT
PIN -80 16 NONE 0
PINATTR PinName ext
PINATTR SpiceOrder 1
PIN -48 96 NONE 0
PINATTR PinName comm
PINATTR SpiceOrder 2
PIN 0 16 NONE 0
PINATTR PinName int
PINATTR SpiceOrder 3
