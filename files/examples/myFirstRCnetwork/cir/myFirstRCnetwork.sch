v 20220529 2
C -19200 55200 1 0 0 C.sym
{
T -18600 56600 5 10 0 1 0 0 1
device=C-slicap
T -18700 55700 5 8 1 1 0 0 1
refdes=C1
T -18700 55550 5 8 1 1 0 0 1
value={C}
}
C -19100 55800 1 90 0 R.sym
{
T -20300 56500 5 10 0 1 90 0 1
device=R-slicap
T -19650 56300 5 8 1 1 0 0 1
value={R}
T -19650 56450 5 8 1 1 0 0 1
refdes=R1
}
C -20000 55300 1 0 1 V.sym
{
T -20700 56500 5 10 0 1 0 6 1
device=V-slicap
T -20450 55800 5 8 1 0 0 6 1
value=0
T -20450 55950 5 8 1 1 0 6 1
refdes=V1
T -20450 55650 5 8 1 0 0 6 1
dc=0
T -20445 55500 5 8 1 0 0 6 1
dcvar=0
T -20445 55350 5 8 1 0 0 6 1
noise=0
}
N -19200 56100 -18900 56100 4
{
T -19200 56150 5 10 1 1 0 0 1
netname=out
}
C -20400 55000 1 0 0 0.sym
{
T -20000 55800 5 10 0 1 0 0 1
device=0-slicap
}
N -20200 55300 -18900 55300 4
C -21100 54400 1 0 0 parDef.sym
{
T -21000 54700 5 10 0 1 0 0 1
device=directive
T -21000 54800 5 8 1 1 0 0 1
refdes=A1
T -21000 54500 5 8 1 1 0 0 1
value=.param R=1k C={1/(2*pi*R*f_c)} f_c=1k
}
N -20200 56100 -20000 56100 4
C -21100 53800 1 0 0 detectorDef.sym
{
T -21000 54400 5 10 0 0 0 0 1
device=directive
T -21000 54200 5 8 1 1 0 0 1
refdes=A2
T -21000 53900 5 8 1 1 0 0 1
value=.detector V_out
}
C -19600 53800 1 0 0 sourceDef.sym
{
T -19500 54400 5 10 0 0 0 0 1
device=directive
T -19500 54200 5 8 1 1 0 0 1
refdes=A3
T -19500 53900 5 8 1 1 0 0 1
value=.source V1
}
