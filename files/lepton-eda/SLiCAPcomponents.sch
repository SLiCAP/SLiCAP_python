v 20200319 2
C -51700 80700 1 0 0 0.sym
{
T -51300 81250 5 6 0 0 0 0 1
device=0-slicap
}
C -45800 80900 1 0 0 C.sym
{
T -45650 82175 5 6 0 0 0 0 1
device=C-slicap
T -45250 81500 5 8 1 1 0 0 1
refdes=C1
T -45250 81350 5 8 1 0 0 0 1
value={C}
T -45247 81192 5 8 1 0 0 0 1
vinit=0
}
C -44100 81000 1 0 0 D.sym
{
T -44100 82200 5 6 0 0 0 0 1
device=D-spice
T -43800 81350 5 8 1 1 0 0 1
model-name=?
T -43800 81500 5 8 1 1 0 0 1
refdes=D1
T -43800 81200 5 8 1 1 0 0 1
params=?
}
C -43000 80900 1 0 0 E.sym
{
T -44100 82600 5 8 0 0 0 0 1
device=E-slicap
T -42500 82100 5 8 1 1 0 0 1
refdes=E1
T -42500 81950 5 8 1 1 0 0 1
value=?
}
C -41500 80900 1 0 0 EZ.sym
{
T -42200 82450 5 6 0 0 0 0 1
device=EZ-slicap
T -41150 82100 5 8 1 1 0 0 1
refdes=E2
T -41150 81950 5 8 1 1 0 0 1
value=?
T -40456 81945 5 8 1 1 0 0 1
zo=?
}
C -39500 80900 1 0 0 F.sym
{
T -40200 82500 5 6 0 0 0 0 1
device=F-slicap
T -39050 82100 5 8 1 1 0 0 1
refdes=F1
T -39050 81950 5 8 1 1 0 0 1
value=?
}
C -38000 80900 1 0 0 G.sym
{
T -38700 82500 5 6 0 0 0 0 1
device=G-slicap
T -37550 82100 5 8 1 1 0 0 1
refdes=G1
T -37550 81950 5 8 1 1 0 0 1
value=?
}
C -36500 80900 1 0 0 G_g.sym
{
T -37200 82500 5 6 0 0 0 0 1
device=G-slicap
T -36050 82100 5 8 1 1 0 0 1
refdes=G2
T -36050 81950 5 8 1 1 0 0 1
value=?
}
C -35000 80900 1 0 0 H.sym
{
T -35700 82500 5 6 0 0 0 0 1
device=H-slicap
T -34550 82100 5 8 1 1 0 0 1
refdes=H1
T -34550 81950 5 8 1 1 0 0 1
value=?
}
C -33500 80900 1 0 0 HZ.sym
{
T -33150 82100 5 8 1 1 0 0 1
refdes=H2
T -33150 81950 5 8 1 0 0 0 1
value=?
T -32450 81950 5 8 1 0 0 0 1
zo=?
T -34243 82500 5 6 0 0 0 0 1
device=HZ-slicap
}
C -49700 79500 1 0 0 I.sym
{
T -49600 80850 5 8 0 0 0 0 1
device=I-slicap
T -49100 80175 5 8 1 1 0 0 1
refdes=I1
T -49100 79600 5 8 1 0 0 0 1
noise=0
T -49100 79750 5 8 1 0 0 0 1
dcvar=0
T -49100 79900 5 8 1 0 0 0 1
dc=0
T -49100 80050 5 8 1 0 0 0 1
value=0
}
C -51600 78400 1 0 0 include.sym
{
T -51500 79000 5 6 0 0 0 0 1
device=directive
T -51500 78800 5 8 1 1 0 0 1
refdes=A1
T -51500 78500 5 8 1 1 0 0 1
file=?
}
C -40500 79500 1 0 0 J.sym
{
T -41100 80700 5 6 0 0 0 0 1
device=J-slicap
T -39875 79975 5 8 1 1 0 0 1
refdes=J1
T -39900 79800 5 8 1 1 0 0 1
model-name=?
T -39900 79650 5 8 1 1 0 0 1
params=?
}
C -46500 77700 1 0 0 K.sym
{
T -46550 78500 5 6 0 0 0 0 1
device=K-slicap
T -46275 77950 5 8 1 1 0 0 1
value=?
T -46275 78100 5 8 1 1 0 0 1
refdes=K1
T -46455 77695 5 8 1 1 0 3 1
ref1=L?
T -45948 77695 5 8 1 1 0 3 1
ref2=L?
}
C -47000 81000 1 0 0 L.sym
{
T -47150 82200 5 6 0 0 0 0 1
device=L-slicap
T -46750 81400 5 8 1 0 0 0 1
value=?
T -46750 81550 5 8 1 1 0 0 1
refdes=L1
T -46743 81219 5 8 1 0 0 0 1
iinit=?
}
C -38000 79500 1 0 0 M.sym
{
T -38600 81050 5 10 0 0 0 0 1
device=M-slicap
T -37400 80300 5 8 1 1 0 0 1
refdes=M1
T -37400 80150 5 8 1 1 0 0 1
model-name=?
T -37400 80000 5 8 1 1 0 0 1
params=?
}
C -43900 76900 1 0 0 M_noise.sym
{
T -44350 78150 5 6 0 0 0 0 1
device=M_noise-slicap
T -43300 77600 5 8 1 1 0 0 1
refdes=X4
T -43300 77300 5 8 1 0 0 0 1
ID={ID}
T -43300 76850 5 8 1 0 0 0 1
L={L}
T -43300 77000 5 8 1 0 0 0 1
W={W}
T -43300 77450 5 8 1 1 0 0 1
model-name=?
T -43300 77150 5 8 1 0 0 0 1
IG={IG}
}
C -36000 79600 1 0 0 MD-H.sym
{
T -36600 80650 5 6 0 0 0 0 1
device=MD-H-slicap
T -35500 79400 5 8 1 1 0 0 1
refdes=M3
T -35500 79250 5 8 1 1 0 0 1
model-type=?
T -35500 79100 5 8 1 1 0 0 1
params=?
}
C -37000 78700 1 0 0 MD-V.sym
{
T -37600 80650 5 6 0 0 0 0 1
device=MD-V-slicap
T -36400 79600 5 8 1 1 0 0 1
refdes=M2
T -36400 79450 5 8 1 1 0 0 1
model-name=?
T -36408 79292 5 8 1 1 0 0 1
params=?
}
C -51600 77700 1 0 0 modelDef.sym
{
T -51500 78300 5 6 0 0 0 0 1
device=directive
T -51500 78100 5 8 1 1 0 0 1
refdes=A2
T -51500 77800 5 8 1 1 0 0 1
value=.model < modelName> < modelType > < param=value ... >
}
C -28500 80900 1 0 0 N.sym
{
T -29200 82375 5 6 0 0 0 0 1
device=N-slicap
T -28000 81950 5 8 1 1 0 0 1
refdes=N1
}
C -42000 76500 1 0 0 N_dcvar.sym
{
T -43000 79300 5 10 0 0 0 0 1
device=N_dcvar-slicap
T -41050 78550 5 8 1 1 0 0 1
refdes=X5
T -41050 78400 5 8 1 0 0 0 1
svo={sigma_vo}
T -41050 78250 5 8 1 0 0 0 1
sib={sigma_ib}
T -41050 78100 5 8 1 0 0 0 1
sio={sigma_io}
T -41050 77950 5 8 1 0 0 0 1
iib={I_b}
}
C -40000 76800 1 0 0 N_noise.sym
{
T -40450 78700 5 6 0 0 0 0 1
device=N_noise-slicap
T -39400 78250 5 8 1 1 0 0 1
refdes=X7
T -39400 78100 5 8 1 0 0 0 1
sv={S_v}
T -39400 77950 5 8 1 0 0 0 1
si={S_i}
}
C -38000 76800 1 0 0 O.sym
{
T -38600 78550 5 6 0 0 0 0 1
device=O-slicap
T -37500 78150 5 8 1 1 0 0 1
refdes=O1
T -37500 78000 5 8 1 1 0 0 1
model-name=?
T -37508 77842 5 8 1 1 0 0 1
params=?
}
C -36000 76800 1 0 0 O_dcvar.sym
{
T -36600 78650 5 6 0 0 0 0 1
device=O_dcvar-slicap
T -35700 78050 5 8 1 1 0 0 1
refdes=X8
T -35150 78050 5 8 1 0 0 0 1
svo={sigma_vo}
T -35150 77900 5 8 1 0 0 0 1
sib={sigma_ib}
T -35150 77750 5 8 1 0 0 0 1
sio={sigma_io}
T -35150 77600 5 8 1 0 0 0 1
iib={I_b}
T -35758 77342 5 8 1 1 0 0 1
model-name=O_dcvar
}
C -33500 76800 1 0 0 O_noise.sym
{
T -34100 78400 5 6 0 0 0 0 1
device=O_noise-slicap
T -32700 77900 5 8 1 1 0 0 1
refdes=X10
T -32700 77750 5 8 1 0 0 0 1
sv={S_v}
T -32700 77600 5 8 1 0 0 0 1
si={S_i}
T -32445 78017 5 6 0 1 0 0 1
model-name=O_noise
}
C -51600 76900 1 0 0 parDef.sym
{
T -51500 77500 5 10 0 0 0 0 1
device=directive
T -51500 77300 5 8 1 1 0 0 1
refdes=A3
T -51500 77000 5 8 1 1 0 0 1
value=.param < param=value ... >
}
C -45400 77000 1 0 0 Q_noise.sym
{
T -45850 78200 5 6 0 0 0 0 1
device=Q_noise-slicap
T -44850 77550 5 8 1 1 0 0 1
refdes=X2
T -44850 77250 5 8 1 0 0 0 1
IC={IC}
T -44850 77100 5 8 1 0 0 0 1
VCE={VCE}
T -44850 77400 5 8 1 1 0 0 1
model-name=?
}
C -47000 79500 1 0 0 QD-H.sym
{
T -47500 80600 5 6 0 0 0 0 1
device=QD-H-slicap
T -46500 79300 5 8 1 1 0 0 1
refdes=Q2
T -46500 79150 5 8 1 1 0 0 1
model-name=?
T -46500 79000 5 8 1 1 0 0 1
params=?
}
C -45000 78700 1 0 0 QD-V.sym
{
T -45550 80675 5 6 0 0 0 0 1
device=QD-V-slicap
T -44250 79650 5 8 1 1 180 0 1
refdes=Q3
T -44350 79500 5 8 1 1 180 0 1
model-name=?
T -44421 79242 5 8 1 1 0 0 1
params=?
}
C -51300 80900 1 0 0 R.sym
{
T -51150 82550 5 8 0 0 0 0 1
device=R-slicap
T -50775 81700 5 8 1 1 0 0 1
refdes=R1
T -50775 81575 5 8 1 0 0 0 1
value=?
T -50775 81425 5 8 1 0 0 0 1
dcvar=0
T -50775 81275 5 8 1 0 0 0 1
noisetemp=0
T -50775 81125 5 8 1 0 0 0 1
noiseflow=0
}
C -31500 80900 1 0 0 T.sym
{
T -32200 82550 5 6 0 0 0 0 1
device=T-slicap
T -31000 82200 5 8 1 1 0 0 1
refdes=T1
T -31000 82050 5 8 1 1 0 0 1
value=?
}
C -51200 79500 1 0 0 V.sym
{
T -51200 80750 5 6 0 0 0 0 1
device=V-slicap
T -50700 80050 5 8 1 0 0 0 1
value=0
T -50700 80200 5 8 1 1 0 0 1
refdes=V1
T -50700 79900 5 8 1 0 0 0 1
dc=0
T -50705 79750 5 8 1 0 0 0 1
dcvar=0
T -50705 79600 5 8 1 0 0 0 1
noise=0
}
C -30000 80900 1 0 0 W.sym
{
T -30700 82350 5 6 0 0 0 0 1
device=W-slicap
T -29500 82050 5 8 1 1 0 0 1
value=?
T -29500 82200 5 8 1 1 0 0 1
refdes=W1
}
C -39500 79500 1 0 0 XJ.sym
{
T -40050 81000 5 10 0 0 0 0 1
device=J-slicap
T -38900 80100 5 8 1 1 0 0 1
refdes=X6
T -38900 79950 5 8 1 1 0 0 1
model-name=?
T -38905 79795 5 8 1 0 0 0 1
ID=?
T -38905 79595 5 8 1 0 0 0 1
VDS=?
}
C -34000 79500 1 0 0 XM.sym
{
T -34425 80750 5 6 0 0 0 0 1
device=XM-slicap
T -33400 79650 5 8 1 1 0 0 1
refdes=X9
T -33000 79650 5 8 1 1 0 0 1
model-name=?
T -32650 79500 5 8 1 0 0 0 1
W={W}
T -31950 79500 5 8 1 0 0 0 1
L={L}
T -33400 79500 5 8 1 0 0 0 1
ID={ID}
}
C -28000 79600 1 0 0 XMD-H.sym
{
T -28600 80800 5 6 0 0 0 0 1
device=XMD-H-slicap
T -28100 79400 5 8 1 1 0 0 1
refdes=X13
T -27600 79400 5 8 1 1 0 0 1
model-name=?
T -28105 79245 5 8 1 0 0 0 1
ID={ID}
T -27405 79245 5 8 1 0 0 0 1
W={W}
T -26755 79245 5 8 1 0 0 0 1
L={L}
}
C -26000 78700 1 0 0 XMD-V.sym
{
T -26800 80800 5 6 0 0 0 0 1
device=XMD-V-slicap
T -25400 79750 5 8 1 1 0 0 1
refdes=X14
T -25400 79600 5 8 1 1 0 0 1
model-name=?
T -25400 79450 5 8 1 0 0 0 1
ID={ID}
T -25400 79300 5 8 1 0 0 0 1
W={W}
T -25400 79150 5 8 1 0 0 0 1
L={L}
}
C -31500 79500 1 0 0 XMV.sym
{
T -32300 80900 5 8 0 0 0 0 1
device=XMV-slicap
T -30900 79700 5 8 1 1 0 0 1
refdes=X11
T -30500 79700 5 8 1 1 0 0 1
model-name=?
T -30900 79400 5 8 1 0 0 0 1
W={W}
T -30100 79400 5 8 1 0 0 0 1
L={L}
T -30100 79550 5 8 1 0 0 0 1
VG={VG}
T -30900 79550 5 8 1 0 0 0 1
VD={VD}
T -29300 79550 5 8 1 0 0 0 1
VS={VS}
}
C -44000 79500 1 0 0 XQD-H.sym
{
T -44450 80700 5 6 0 0 0 0 1
device=XQD-H-slicap
T -44000 79350 5 8 1 1 0 0 1
refdes=X1
T -43600 79350 5 8 1 1 0 0 1
model-name=?
T -44000 79200 5 8 1 0 0 0 1
IC={IC}
T -43300 79200 5 8 1 0 0 0 1
VCE={VCE}
}
C -42000 78700 1 0 0 XQD-V.sym
{
T -43300 81200 5 8 0 1 0 0 1
device=XQD-V-slicap
T -41400 79650 5 8 1 1 0 0 1
refdes=X3
T -41400 79500 5 8 1 1 0 0 1
model-name=?
T -41400 79350 5 8 1 1 0 0 1
IC=IC={IC}
T -41400 79200 5 8 1 1 0 0 1
VCE=VCE={VCE}
}
C -48300 80900 1 0 0 Z.sym
{
T -48100 82150 5 6 0 0 0 0 1
device=Z-slicap
T -47850 81300 5 8 1 1 0 0 1
value=?
T -47850 81450 5 8 1 1 0 0 1
refdes=Z1
}
C -49800 80900 1 0 0 R_r.sym
{
T -49550 82300 5 6 0 0 0 0 1
device=R-slicap
T -49250 81700 5 8 1 1 0 0 1
refdes=R2
T -49250 81575 5 8 1 1 0 0 1
value=value=?
T -49250 81425 5 8 1 1 0 0 1
dcvar=dcvar=0
T -49250 81275 5 8 1 1 0 0 1
noisetemp=noisetemp=0
T -49250 81125 5 8 1 1 0 0 1
noiseflow=noiseflow=0
}
C -27000 80800 1 0 0 ABCD.sym
{
T -27600 83100 5 6 0 0 0 0 1
device=twoPort-slicap
T -26750 82700 5 8 1 1 0 0 1
refdes=X12
T -26250 82700 5 8 1 0 0 0 1
A={A}
T -26250 82500 5 8 1 0 0 0 1
B={B}
T -26250 82300 5 8 1 0 0 0 1
C={C}
T -26250 82100 5 8 1 0 0 0 1
D={D}
}
C -48000 79500 1 0 0 Q.sym
{
T -48500 80800 5 6 0 0 0 0 1
device=Q-slicap
T -47400 79700 5 8 1 1 0 0 1
refdes=Q1
T -47400 79550 5 8 1 1 0 0 1
model-name=?
T -47400 79400 5 8 1 1 0 0 1
params=?
}
