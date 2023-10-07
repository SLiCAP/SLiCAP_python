#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This is to be used to find the frequency constant matrix (which is the inverse of the time constant matrix)
"""
import sympy as sp
from SLiCAP.SLiCAPini import ini
from SLiCAP.SLiCAPmatrices import makeMatrices,makeSrcVector

from SLiCAPfclink import backsubstitute,UVsolve,nth2firstOrder,findA4,laplace2coeffs



if __name__ == "__main__":
    import time
    x=sp.Symbol("x")
    y=sp.Symbol("y")
    test=sp.Matrix([[6+x,2*x],[x**2*9,45*y]])
    res=laplace2coeffs(test,x)
    print("\nlaplace2coeffs: ", res)
    res1=nth2firstOrder(res)
    print("\nnth2firstOrder: ", res1)
    dim=2
    Atest=sp.Matrix(sp.MatrixSymbol('A',dim,dim))
    start = time.time()
    P,Q,L,U,rank = PAQeqLU(Atest)
    stop = time.time()
    print("LU: ",sp.simplify(L*U-Atest), "time: ",stop-start)
    start = time.time()
    L, U ,_ = Atest.LUdecomposition()
    stop = time.time()
    print("\nsympy LU: ",sp.simplify(L*U-Atest), "time: ",stop-start)
    Nothertest=sp.Matrix([[-794,0,778],[-336,0,0],[-1,0,0]])
    P,Q,L,U,rank = PAQeqLU(Nothertest)
    print("LU: ",sp.simplify(L*U-P*Nothertest*Q))
    dim=10
    Atest=sp.Matrix(sp.MatrixSymbol('A',dim,dim))
    print("\nNothertest: ", Atest)
    Atest=ODtranspose(Atest)
    print("\nODtranspose(Nothertest): ", Atest)
