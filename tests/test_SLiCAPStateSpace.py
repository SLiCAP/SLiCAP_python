#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This is to be used to find the frequency constant matrix (which is the inverse of the time constant matrix)
"""
import sympy as sp
from SLiCAP.SLiCAPini import ini
from SLiCAP.SLiCAPmatrices import makeMatrices,makeSrcVector

from SLiCAPfc import UVsolve,nth2firstOrder,laplace2coeffs
from SLiCAPStateSpace import backsubstitute, Block2StateSpace, backsubstituteND, findA4

dim = 5
U = sp.Matrix(sp.MatrixSymbol('a', dim, dim)).upper_triangular()
b = sp.Matrix(sp.MatrixSymbol('a', dim, 1))
x = backsubstitute(U,b)
print("Backsubstitution x Result: ", x)
print("Backsubstitution Result: ", sp.simplify(U * x - b ))
x = backsubstituteND(U,b)
print("Backsubstitution x Result: ", x)
print("Backsubstitution Result: ", sp.simplify(U * x - b ))
### Test Block2StateSpace
"""
has the form:
q = |X Y|*y + s*|Q W|*y
    |0 U|       |0 S|
"""
rank = 2
dim = 5
X = sp.Matrix(sp.MatrixSymbol('x', rank, rank))
Q = sp.Matrix(sp.MatrixSymbol('q', rank, rank))
Y = sp.Matrix(sp.MatrixSymbol('y', rank,dim-rank))
W = sp.Matrix(sp.MatrixSymbol('w', rank,dim-rank))
U = sp.Matrix(sp.MatrixSymbol('u', dim-rank, dim-rank)).upper_triangular()
S = sp.Matrix(sp.MatrixSymbol('s', dim-rank, dim-rank)).upper_triangular()
S = S - S.diag(list([S[i,i] for i in range(dim-rank)]))
Zs = sp.zeros(dim-rank,rank)
G = sp.Matrix(sp.BlockMatrix([[X,Y],[Zs,U]]))
C = sp.Matrix(sp.BlockMatrix([[Q,W],[Zs,S]]))
Iv= sp.Matrix(sp.MatrixSymbol('Iv', dim, 1))
V = sp.eye(dim,dim)
sL = ini.Laplace
testIv=sp.Matrix(Iv[rank:])
xsols = backsubstitute(U+S*sL,testIv)
print("Backsubstitution xsols Result: ", sp.cancel((U+S*sL) * xsols - testIv))
print("x sols: ",sp.Matrix([sp.collect(i,sL) for i in xsols]))
print("laplace Coefficient Matrices: ",laplace2coeffs(xsols,sL))
A,B,Cres,D = Block2StateSpace(rank,dim,Iv,G,C,V,Iv,sL)
Blaplace=sp.zeros(B[0].shape[0],B[0].shape[1])
for i in range(len(B)):
    Blaplace = Blaplace + sL**i*B[i]
Dlaplace=sp.zeros(D[0].shape[0],D[0].shape[1])
for i in range(len(D)):
    Dlaplace = Dlaplace + sL**i*D[i]
ysol=sp.cancel((sL*sp.eye(A.shape[0])-A).inv()*Blaplace*Iv)
print("Ysol Check:",sp.cancel(sL*ysol-A*ysol-Blaplace*Iv))
xsol=sp.cancel(Cres*ysol+Dlaplace*Iv)
ysolxsols=V*sp.Matrix(sp.BlockMatrix([[ysol],[xsols]]))
print("V*y-(C*ysol+D*Iv): ",sp.cancel(xsol-ysolxsols))
testres=Iv-(G*xsol+sL*C*xsol)
print("result: ",sp.cancel(testres))
    
