v 20200319 2
C 2600 0 1 0 0 spE.sym
{
T 1500 1700 5 8 0 0 0 0 1
device=E-spice
T 3100 1200 5 8 1 1 0 0 1
refdes=E1
T 3100 1050 5 8 1 1 0 0 1
value=1
}
C 1400 800 1 0 0 spE.sym
{
T 300 2500 5 8 0 0 0 0 1
device=E-spice
T 1900 2000 5 8 1 1 0 0 1
refdes=E2
T 1900 1850 5 8 1 1 0 0 1
value=1
}
N 2600 1700 4200 1700 4
{
T 3800 1750 5 10 1 1 0 0 1
netname=out2
}
N 3800 1700 3800 900 4
N 2600 100 4200 100 4
{
T 3800 150 5 10 1 1 0 0 1
netname=out1
}
N 1400 1700 1000 1700 4
{
T 1300 1750 5 10 1 1 0 6 1
netname=in1
}
N 1400 900 1000 900 4
{
T 1300 950 5 10 1 1 0 6 1
netname=in2
}
C 1100 2100 1 0 0 spCommand.sym
{
T 1000 2400 5 6 0 0 0 0 1
device=directive
T 1000 2200 5 8 1 1 0 0 1
refdes=A?
T 1200 2200 5 8 1 1 0 0 1
value=.subckt nullor out1 out2 in1 in2
}
