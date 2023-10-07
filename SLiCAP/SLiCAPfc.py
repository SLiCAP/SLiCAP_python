#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This is to be used to find the frequency constant matrix (which is the inverse of the time constant matrix)
"""
import sympy as sp
from SLiCAP.SLiCAPini import ini

def laplace2coeffs(M, var=ini.Laplace):
    """
    Returns a list of coefficient matrices where the list order
    corresponds to the order of the laplace variable for the
    coefficient matrix.

    :param M: Sympy matrix
    :type M: sympy.Matrix

    :param s: Sympy Symbol
    :type s: sympy.Matrix

    :return: res: List of sympy matrices
    :rtype:  list

    :Example:

    >>> import sympy as sp
    >>> from SLiCAP.SLiCAPfc import laplace2coeffs
    >>> x = sp.Symbol("x")
    >>> test = sp.Matrix([[1+x,2*x],[x**2*9,1]])
    >>> laplace2coeffs(test, var=x)
    [Matrix([
    [1, 0],
    [0, 1]]), Matrix([
    [1, 2],
    [0, 0]]), Matrix([
    [0, 0],
    [9, 0]])]
    """
    dim = M.shape[0]
    res=[sp.zeros(dim,dim)]
    for i in range(dim):
        for j in range(dim):
            dum = M[i,j]
            #makes a polynomial list with the 0th order coefficent at the end of the list
            dumpoly = sp.Poly(dum, var).all_coeffs()
            if len(dumpoly) > len(res):
                for k in range(len(res),len(dumpoly)):
                    res.append(sp.zeros(dim,dim))
            for k in range(len(dumpoly)):
                res[k][i,j] = dumpoly[-1-k]
    return res

def nth2firstOrder(CM):
    """
    Returns the first order decomposition of an nth order system of differential equations

    :param M: list of coefficient matricies
    :type M: list

    :return res: list of 2 coefficient matrices
    :rtype:  list

    :Example:
    >>> import sympy as sp
    >>> from SLiCAP.SLiCAPfc import *
    >>> x=sp.Symbol("x")
    >>> test = sp.Matrix([[1+x,2*x],[x**2*9,1]])
    >>> res = laplace2coeffs(test, var=x)
    >>> nth2firstOrder(res)
    """
    dim = CM[0].shape[0]
    order = len(CM) - 1
    if order == 0:
        G = CM[0]
        C = sp.zeros(dim)
    elif order == 1:
        G, C = CM
    else:
        #The number of new variables is: (order-1)*dim:
        newVars = (order - 1) * dim
        G = sp.Matrix([[CM[0], sp.zeros(dim, newVars)], [sp.zeros(newVars, dim), sp.eye(newVars)]])
        firstOrder = CM[1:]
        C = sp.Matrix([[sp.BlockMatrix(firstOrder)], [-1 * sp.eye(newVars), sp.zeros(newVars, dim)]])
    return [G, C]

def PAQeqLU(A):
    """
    Returns the matricies P,Q,L,U for the equation PAQ=LU

    :param A: Matrix to perform the LU decomposition on
    :type A: sympy matrix

    :return res: list of 4 matrices and the rank of the matrix P, Q, L, U, rank
    :rtype:  list

    :Example:
    >>> dim=4
    >>> Atest = sp.Matrix(sp.MatrixSymbol('A', dim, dim))
    >>> P, Q, L, U, rank = LUdecomp(Atest)
    >>> sp.simplify(L*U-Atest)
    Matrix([[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]])
    >>> Nothertest = sp.Matrix([[-794,0,778],[-336,0,0],[-1,0,0]])
    >>> P, Q, L, U, rank = LUdecomp(Nothertest)
    >>> sp.simplify(L*U-P*Nothertest*Q)
    Matrix([[0, 0, 0], [0, 0, 0], [0, 0, 0]])
    """
    dim=A.shape[0]
    D=A.copy
    rank = 0;
    ro=[*range(0,dim)] # row permutation vector
    co=[*range(0,dim)] # column permutation vector
    tmp_num=sp.zeros(dim)
    tmp_den=sp.zeros(dim)
    for i in range(dim):
        for j in range(dim):
            tmp_num[i,j],tmp_den[i,j] = sp.fraction(sp.cancel(A[i,j]))
    for k in range(dim):
        #### 1st Pivot row and column if diagonal is zero:
        if tmp_num[k,k] == 0:
            rp = 0
            cp = 0
            for i in range(k,dim):
                for j in range(k,dim):
                    if tmp_num[i,j]==0:
                        continue
                    rp=i
                    cp=j
            if(rp!=0 or cp!=0):
                ## Swqp Rows
                if(rp!=k) & (rp !=0):
                    tmp_num=tmp_num.elementary_row_op(op="n<->m", row1=k, row2=rp)
                    tmp_den=tmp_den.elementary_row_op(op="n<->m", row1=k, row2=rp)
                    ro[k], ro[rp] = ro[rp], ro[k]
                ## Swap Columns
                if(cp!=k) & (cp !=0):
                    tmp_num=tmp_num.elementary_col_op(op="n<->m", col1=k, col2=cp)
                    tmp_den=tmp_den.elementary_col_op(op="n<->m", col1=k, col2=cp)
                    co[k], co[cp] = co[cp], co[k]
            else:
                break ## All elements below k are zero; nothing left to do
        for i in range(k+1,dim):
            if(tmp_num[i,k]==0):
                continue
            ## divide two fractions
            dumnum=tmp_num[i,k]*tmp_den[k,k]
            dumden=tmp_den[i,k]*tmp_num[k,k]
            tmp_num[i,k],tmp_den[i,k] = sp.fraction(sp.cancel(dumnum/dumden))
        for i in range(k+1,dim):
            if(tmp_num[i,k]==0):
                continue
            for j in range(k+1,dim):
                if(tmp_num[k,j]==0):
                    continue
                # subtract two fractions
                dividend_num=tmp_num[i,j]*tmp_den[i,k]*tmp_den[k,j]-tmp_den[i,j]*tmp_num[i,k]*tmp_num[k,j]
                dividend_den=tmp_den[i,j]*tmp_den[i,k]*tmp_den[k,j]
                tmp_num[i,j],tmp_den[i,j] = sp.fraction(sp.cancel(dividend_num/dividend_den))
        rank = rank + 1
    P,Q,L,U=sp.zeros(dim),sp.zeros(dim),sp.zeros(dim),sp.zeros(dim)
    for i in range(0,dim):
        L[i,i]=1
        for j in range(0,i):
            L[i,j]=tmp_num[i,j]/tmp_den[i,j]
    for i in range(0,dim):
        for j in range(i,dim):
            U[i,j]=tmp_num[i,j]/tmp_den[i,j]

    for i in range(0,dim):
        P[ro[i],i]=1
        Q[i,co[i]]=1
    P=P.T
    Q=Q.T
    return [P,Q,L,U,rank]

def ODtranspose(A):
    """
    Returns the off diagonal transpose:

    :param A: Matrix to perform the off diagonal transpose on
    :type A: sympy matrix

    :return res: off diagonal transpose
    :type res: sympy matrix

    :Example:
    """
    res = A.copy() #wow! this .copy is really important!
    row = A.shape[0]
    col = row #should be square
    initc=col-1
    for r in range(0,row):
        for c in range(r,col):
            res[r,initc-c], res[c,initc-r] = res[c,initc-r], res[r,initc-c]
    return res

def UVsolve(A, B):
    """
    Returns the U, V, and X for UAV = XUBV
    equivalently: finds the UV for F = UAVx + sUBVx

    :param A: Matrix to perform the UV decomposition on
    :type A: sympy matrix

    :param B: Matrix to perform the UV decomposition on
    :type B: sympy matrix

    :return res: list of three matrices: U,V,fc where fc is the frequency
                 constant matrix
    :rtype:  list

    :Example:
    """

    dim = A.shape[0]
    rankB = [dim]
    U=sp.eye(dim)
    V=sp.eye(dim)
    rankA=dim
    while True:
        tmpB=U*B*V
        zeroB=sp.zeros(dim)
        zeroB[0:rankB[-1],0:rankB[-1]]=tmpB[0:rankB[-1],0:rankB[-1]]
        P,Q,L,Up,rank = PAQeqLU(zeroB)
        rankB.append(rank)
        U=L.inv()*P*U
        V = V*Q
        tmpA=U*A*V
        zeroA=sp.zeros(dim)
        zeroA[rankB[-1]:,:]=tmpA[rankB[-1]:,:]
        zeroA=ODtranspose(zeroA)
        P,Q,L,Up,rankA = PAQeqLU(zeroA)
        L=L.inv()*P
        L=ODtranspose(L)
        Q=ODtranspose(Q)
        U=Q*U
        V=V*L
        if not((rankB[-2]>rankB[-1]) and (rankB[-1]>0)):
            break
    tmpB=U*B*V
    zeroB=tmpB[0:rankB[-1],0:rankB[-1]]
    tmpA=U*A*V
    zeroA=tmpA[0:rankB[-1],0:rankB[-1]]
    fc=sp.cancel(zeroB.inv()*zeroA)
    return [U,V,fc]

def computeFC(M, var=ini.Laplace):
    """
    Returns the frequency constant matrix fc

    :param A: SLiCAP matrix, where the Laplace variable 'var' is in the matrix
    :type A: sympy matrix

    :param s: laplace variable
    :type s: sympy symbol

    :return: fc: where fc is the frequency constant matrix
    :rtype:  sympy matrix

    :Example:
    """

    res    = laplace2coeffs(M, var = var)
    res    = nth2firstOrder(res)
    U,V,fc = UVsolve(res[0],res[1])
    return fc

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
    dim=7
    Atest=sp.Matrix(sp.MatrixSymbol('A',dim,dim))
    print("\nNothertest: ", Atest)
    Atest=ODtranspose(Atest)
    print("\nODtranspose(Nothertest): ", Atest)
    ## Test Everything:
    g_m1,g_m2,c_i1,c_i2,r_o1,r_o2,s,R,R_L=sp.symbols("g_m1,g_m2,c_i1,c_i2,r_o1,r_o2,s,R,R_L")
    test=sp.Matrix([[0,	0,	0,	0,	0,	1,	0],
        [0,	-2,	0,	0,	g_m1,	g_m1,	0],
        [0,	0,	-2,	g_m2,	-g_m2,	0,	0],
        [0,	1,	0,	(c_i2*r_o1*s+1)/(2*r_o1),	-(c_i2*r_o1*s-1)/(2*r_o1),	0,	0],
        [0,	1,	-1,	-(c_i2*r_o1*s-1)/(2*r_o1),	((R*c_i2+R*c_i1)*r_o1*r_o2*s+(2*r_o1+R)*r_o2+R*r_o1)/(2*R*r_o1*r_o2),	(c_i1*s)/2,	-1/(2*r_o2)],
        [1,	0,	0,	0,	(c_i1*s)/2,	(c_i1*s)/2,	0],
        [0,	0,	1,	0,	-1/(2*r_o2),	0,	(2*r_o2+R_L)/(2*R_L*r_o2)]
    ]);
    res=laplace2coeffs(test,s)
    print("\nMatrix 2 Coeffs:",res)
    res=nth2firstOrder(res)
    print("\nMatrix 2 Coeffs:",res)
    U,V,fc=UVsolve(res[0],res[1])
    print("\nUAV: ", sp.simplify(U*res[0]*V) )
    print("\nUBV: ", sp.simplify(U*res[1]*V) )
    print("\nfc: ", fc)
    fctest,_=(sp.eye(fc.shape[0])*s+fc).det().as_numer_denom()
    testdet,_=test.det().as_numer_denom()
    print("\ndet fc: ", sp.simplify(fctest))
    print("\ndet sympy: ", sp.simplify(testdet))
    print("\ndet diff: ", sp.simplify(testdet+fctest))

    # test n-th order"
    CM = []
    for i in range(10):
        CM.append(sp.eye(2))
        print("Order:", i)
        G, C = nth2firstOrder(CM)
