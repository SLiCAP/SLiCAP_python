#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SLiCAP scripts for determination of the frequency constants matrix.
"""
import sympy as sp
import SLiCAP.SLiCAPconfigure as ini

def _laplace2coeffs(M, var=ini.laplace):
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
    >>> from SLiCAP.SLiCAPfc import _laplace2coeffs
    >>> x = sp.Symbol("x")
    >>> test = sp.Matrix([[1+x,2*x],[x**2*9,1]])
    >>> _laplace2coeffs(test, var=x)
    [Matrix([
    [1, 0],
    [0, 1]]), Matrix([
    [1, 2],
    [0, 0]]), Matrix([
    [0, 0],
    [9, 0]])]
    """
    row,col = M.shape
    res=[sp.zeros(row,col)]
    for i in range(row):
        for j in range(col):
            dum = M[i,j]
            #makes a polynomial list with the 0th order coefficent at the end of the list
            dumpoly = sp.Poly(dum, var).all_coeffs()
            if len(dumpoly) > len(res):
                for k in range(len(res),len(dumpoly)):
                    res.append(sp.zeros(row,col))
            for k in range(len(dumpoly)):
                res[k][i,j] = dumpoly[-1-k]
    return res

def _nth2firstOrder(CM,q=sp.zeros(1,1)):
    """
    Returns the first order decomposition of an nth order system of differential equations

    .. math:: q=A_0x+sA_1x+s^2A_2x+...

    :param M: list of coefficient matrices
    :type M: list

    :param q: Vector of sources
    :type q: sympy matrix

    :return res: list of 2 coefficient matrices and the updated source vector
    :rtype:  list

    :Example:
    >>> import sympy as sp
    >>> from SLiCAP.SLiCAPfc import *
    >>> x=sp.Symbol("x")
    >>> test = sp.Matrix([[1+x,2*x],[x**2*9,1]])
    >>> res = _laplace2coeffs(test, var=x)
    >>> _nth2firstOrder(res)
    """
    order=len(CM)-1
    if order==1:
        newCM=CM.copy()
        newCM.append(q)
        return newCM
    dim=CM[0].shape[0]
    #The number of new variables is: (order-1)*dim:
    newVars=(order-1)*dim
    newq=sp.Matrix([q,sp.zeros(newVars,1)])
    G = sp.Matrix(sp.BlockMatrix([[CM[0], sp.zeros(dim,newVars)], [sp.zeros(newVars,dim), sp.eye(newVars)]]))
    firstOrder = sp.Matrix(sp.BlockMatrix(CM[1:]))
    newVarsblock = sp.Matrix(sp.BlockMatrix([-1*sp.eye(newVars), sp.zeros(newVars,dim)]))
    C = sp.Matrix(sp.BlockMatrix([[firstOrder],[newVarsblock]]))
    return (G,C,newq)

def _Matrix_num_den(M):
    """
    Returns the matrices Mnum, Mden for the matrix M

    :param M: Matrix to perform the num_den decomposition on
    :type M: sympy matrix

    :return Mnum: Numerator of each elements in M
    :rtype:  sympy matrix

    :return Mden: Denominator of each elements in M
    :rtype:  sympy matrix
    """
    row,col = M.shape
    Mnum = sp.zeros(row,col)
    Mden = sp.zeros(row,col)
    for i in range(row):
        for j in range(col):
            Mnum[i,j],Mden[i,j] = sp.fraction(sp.cancel(M[i,j]))
    return (Mnum,Mden)

def _addfractions(A, B):
    """
    Returns the numerator and denominator after adding the fractions A,B

    :param A: numerator and denominator of the fraction A
    :type A: tuple of sympy expressions

    :param B: numerator and denominator of the fraction B
    :type B: tuple of sympy expressions

    :return Cnum: Numerator of A + B
    :rtype:  sympy expression

    :return Cden: Denominator of A + B
    :rtype:  sympy expression
    """
    Anum,Aden=A
    Bnum,Bden=B
    Cnum = Anum*Bden+Aden*Bnum
    Cden = Aden*Bden
    return sp.fraction(sp.cancel(Cnum/Cden))

def _PAQeqLU(A):
    """
    Returns the matrices P,Q,L,U for the equation PAQ=LU

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
    rank = 0;
    ro=[*range(0,dim)] # row permutation vector
    co=[*range(0,dim)] # column permutation vector
    tmp_num,tmp_den = _Matrix_num_den(A)
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

def _ODtranspose(A):
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

def _UVsolve(A, B):
    """
    Returns the U, V matrices that place a system of equations into block diagaonal form where the starting system of equations are:

    .. math:: I=Gy+sCy

    and the resulting block diagonal system of equations become:

    .. math:: UI = UAVx + sUBVx

    .. math:: x=Vy

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
        P,Q,L,Up,rank = _PAQeqLU(zeroB)
        rankB.append(rank)
        U=L.inv()*P*U
        V = V*Q
        tmpA=U*A*V
        zeroA=sp.zeros(dim)
        zeroA[rankB[-1]:,:]=tmpA[rankB[-1]:,:]
        zeroA=_ODtranspose(zeroA)
        P,Q,L,Up,rankA = _PAQeqLU(zeroA)
        L=L.inv()*P
        L=_ODtranspose(L)
        Q=_ODtranspose(Q)
        U=Q*U
        V=V*L
        if not((rankB[-2]>rankB[-1]) and (rankB[-1]>0)):
            break
    tmpB=U*B*V
    rank = rankB[-1]
    zeroB=tmpB[0:rank,0:rank]
    tmpA=U*A*V
    zeroA=tmpA[0:rank,0:rank]
    tmpU = sp.Matrix.diag(zeroB.inv(),sp.eye(dim-rank))
    fc= sp.cancel(tmpU[0:rank,0:rank]*zeroA)
    U=tmpU*U
    return [U,V,fc]

def computeFC(M, var=ini.laplace):
    """
    Returns the frequency constant matrix fc

    :param M: Sympy matrix, where the Laplace variable 'var' is in the matrix
    :type M: sympy.Matrix

    :param var: Laplace variable
    :type var: sympy.Symbol

    :return: The frequency constant matrix
    :rtype:  sympy.Matrix
    """

    res    = _laplace2coeffs(M, var = var)
    res    = _nth2firstOrder(res)
    U,V,fc = _UVsolve(res[0],res[1])
    return fc