#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This is to be used to find the frequency constant matrix (which is the inverse of the time constant matrix)
"""
import sympy as sp
from SLiCAP.SLiCAPini import ini
from SLiCAP.SLiCAPmatrices import makeMatrices,makeSrcVector
from SLiCAP.SLiCAPfc import addfractions, laplace2coeffs, nth2firstOrder, UVsolve, Matrix_num_den
def backsubstitute(U,b):
    """
    Returns the vector 'x' to the system of equations: Ux=b 
    where U must be Upper triangular.

    :param A: Upper Triangluar sympy matrix
    :type A: sympy matrix

    :param b: Inputs of the system of equations
    :type b: sympy symbol

    :return: x: where x a vector
    :rtype:  sympy matrix

    :Example:
    >>> a,b,c,d,e,f= sp.symbols("a,b,c,d,e,f")
    >>> U = sp.Matrix([[a, b, c],[0,d,e],[0,0,f]])
    >>> b1,b2,b3 = sp.symbols("b1,b2,b3")
    >>> b = sp.Matrix([[b1],[b2],[b3]])
    >>> x = backsubstitute(U,b)
    >>> print( sp.simplify(U * x - b ))
    Matrix([[0], [0], [0]])
    """
    if not U.is_upper :
        print("in backsubstitute(U,b), U is not upper triangluar. But will continue computation.")
    row = U.shape[0]
    x=sp.Matrix(b.copy())
    for i in range(row-1,0,-1):
        x[i]= sp.cancel(x[i]/U[i,i])
        # the type was removed when I used matrix splicing here:
        for k in range(i):
            x[k] = x[k] - U[k,i]*x[i]
    x[0] = x[0]/U[0,0]
    return sp.Matrix(x)

def backsubstituteND(U,b):
    """
    This function is the same as backsubstitute except it converts to num den first.
    Returns the vector 'x' to the system of equations: Ux=b 
    where U must be Upper triangular.

    :param A: Upper Triangluar sympy matrix
    :type A: sympy matrix

    :param b: Inputs of the system of equations
    :type b: sympy symbol

    :return: x: where x a vector
    :rtype:  sympy matrix

    :Example:
    >>> a,b,c,d,e,f= sp.symbols("a,b,c,d,e,f")
    >>> U = sp.Matrix([[a, b, c],[0,d,e],[0,0,f]])
    >>> b1,b2,b3 = sp.symbols("b1,b2,b3")
    >>> b = sp.Matrix([[b1],[b2],[b3]])
    >>> x = backsubstituteND(U,b)
    >>> print( sp.simplify(U * x - b ))
    Matrix([[0], [0], [0]])
    """
    if not U.is_upper :
        print("in backsubstitute(U,b), U is not upper triangluar. But will continue computation.")
    row = U.shape[0]
    xnum,xden=Matrix_num_den(b)
    Unum,Uden = Matrix_num_den(U)
    for i in range(row-1,0,-1):
        xnum[i],xden[i] = sp.fraction(sp.cancel(xnum[i]/xden[i]*Uden[i,i]/Unum[i,i]))
        # the type was removed when I used matrix splicing here:
        for k in range(i):
            xnum[k],xden[k] = addfractions((xnum[k],xden[k]),(-Unum[k,i]*xnum[i],Uden[k,i]*xden[i]))
    xnum[0] = xnum[0]*Uden[0,0]
    xden[0] = xden[0]*Unum[0,0]
    x = sp.Matrix([sp.cancel(xnum[i]/xden[i]) for i in range(row)])
    return x

def findA4(x,b):
    """
    Returns the Matrix A for A*x=b

    :param x: independent variables vector
    :type x: sympy matrix

    :param b: Solution vector after multiplying A by x
    :type b: sympy matrix

    :return: A: Matrix which solves A*x=b
    :rtype:  sympy matrix

    :Example:
    """
    rows=b.shape[0]
    cols=x.shape[0]
    A=sp.zeros(rows,cols)
    
    for i in range(rows):
        for j in range(cols):
            A[i,j] = sp.cancel(sp.collect(sp.expand(b[i]),x[j]).coeff(x[j]))
    return A

def Block2Bstatematrix(rank,q,A,B,var=ini.Laplace):
    """
    For The system of equations where y is unknown:
    q = A*y+s*B*y
    which has the form:
    q = |X Y|*y + s*|Q W|*y
        |0 U|       |0 S|
    where:
    U: is an upper triangular Matrix
    S: is a strictly upper triangular Matrix
    Q: is an invertible Matrix
    Then this Function will return B from the state space equation
        sy=Ay+B(s)u

    :param rank: This is the rank of the matrix B
    :type rank: int

    :param q: Input Vector
    :type q: sympy matrix

    :param A: the XYU matrix
    :type A: sympy matrix

    :param B: the QWS matrix
    :type B: sympy matrix

    :return: res: [Bres, known_ys] Bres is a sympy matrix and known_ys is the known y values.
    :rtype:  list
    """
    known_ys = backsubstitute( A[rank:,rank:]+var*B[rank:,rank:] , q[rank:] )
    dumq=sp.Matrix(q[0:rank])
    dumvar1=sp.Matrix(A[0:rank,rank:]*known_ys)
    dumvar2=sp.Matrix(B[0:rank,rank:]*known_ys)
    Bres=dumq-dumvar1-var*dumvar2
    return (Bres,known_ys)

def Block2CDstatematrix(rank,known_ys,V,xlen):
    """
    For The system of equations where y is unknown:
    q = A*y+s*B*y
    which has the form:
    q = |X Y|*y + s*|Q W|*y
        |0 U|       |0 S|
    where:
    U: is an upper triangular Matrix
    S: is a strictly upper triangular Matrix
    Q: is an invertible Matrix
    Then this Function will return C and D from the state space equation
        sy=Ay+B(s)u
        x =Cy+D(s)u

    :param rank: This is the rank of the matrix B
    :type rank: int

    :param known_ys: Known values of the y Vector
    :type known_ys: sympy matrix

    :param V: the matrix that relates y and x: x=Vy
    :type V: sympy matrix

    :param xlen: the length of the vector x
    :type xlen: int

    :return: res: [Cres, Dres] Cres and Dres are a sympy matrices
    :rtype:  list
    """
    Cres= V[:xlen,0:rank]
    Dres=V[:xlen,rank:]*known_ys
    return (Cres,Dres)

def Vector2srcCoeffMatrices(src,V,var=ini.Laplace):
    """
    For Vector 'V' that is a linear function of the 'src' vector
    and the laplace variable 'var' then this function decomposes V to get 
    the matrix Mres where: Mres*src=V. Then it returns the list of
    coefficent matrices of the laplace variable.

    :param src: This is a vector of sources
    :type src: sympy matrix

    :param V: The Vector V is a linear function of the 'src' vector
              and the laplace variable 'var'
    :type V: sympy matrix

    :param V: the matrix that relates y and x: x=Vy
    :type V: sympy matrix

    :param var: laplace variable
    :type var: sympy symbol

    :return: Mres: Mres is a list of Coefficent Matrices that correspond 
                   to the basis (s^0,...,s^n) where is the laplace variables
    :rtype:  list
    
    :Example:
    >>> Iv = sp.Matrix(sp.MatrixSymbol('Iv', 2, 1))
    >>> A = sp.Matrix(sp.MatrixSymbol('a', 2, 2))
    >>> B = sp.Matrix(sp.MatrixSymbol('b', 2, 2))
    >>> s = sp.Symbol("s")
    >>> ABmat = A+s*B+s**2*A*B
    >>> tot = (ABmat)*Iv
    >>> Vres = Vector2srcCoeffMatrices(Iv,tot,s)
    >>> res= sp.zeros(Vres[0].shape[0])
    >>> for i in range(len(Vres)):
    >>>    res = res + Vres[i]*s**i
    >>> sp.cancel(ABmat -(Vres))
    Matrix([
    [0, 0],
    [0, 0]])
    """
    # Seperate the sources from M
    Vs=findA4(src,V)
    # Create lists of coefficient matrices
    Vres=laplace2coeffs(Vs,var)
    return Vres

def Block2StateSpace(rank,vlen,q,G,C,V,u,var=ini.Laplace):
    """
    For The system of equations where y is unknown:
    q = G*y+s*C*y
    x = Vy
    which has the form:
    q = |X Y|*y + s*|Q W|*y
        |0 U|       |0 S|
    where:
    U: is an upper triangular Matrix
    S: is a strictly upper triangular Matrix
    Q: is an invertible Matrix
    Then this Function will return A, C and Bi's and Di's from the state space equation
        sy=Ay+B0u+sB1u+s^2B2u+...
        v =Cy+D0u+sD1u+s^2D2u+...
    """
    dim = G.shape[0]
    #If Q isn't an identity I need to invert:
    Qinv= sp.eye(dim-rank)
    dumQ=sp.Matrix(C[0:rank,0:rank])
    # Todo: add condition here to avoid inverting Q
    Qinv=sp.Matrix(C[0:rank,0:rank]).inv()
    U = sp.Matrix.diag(Qinv,sp.eye(dim-rank))
    A=-Qinv*sp.Matrix(G[0:rank,0:rank])
    Bres,known_ys = Block2Bstatematrix(rank,U*q,U*G,U*C,var)
    C,Dres = Block2CDstatematrix(rank,known_ys,V,vlen)
    B = Vector2srcCoeffMatrices(u,Bres,var)
    D = Vector2srcCoeffMatrices(u,Dres,var)
    return (A,B,C,D)

def MNA2StateSpace(M, q, src, var=ini.Laplace):
    """
    Returns the the state space representation of the MNA matrix:
        for q=(G+sC)v this function returns A,Bi,C,Di 
        where i is the i'th derivative of the sources
        from the equation:
        sy=Ay+B0u+sB1u+s^2B2u+...
        v =Cy+D0u+sD1u+s^2D2u+...

    :param M: MNA matrix ie my_circuit.allResults.M
    :type M: sympy matrix

    :param q: source vector
    :type q: sympy matrix

    :param src: SLiCAP source names; ie my_circuit.indepVars() or my_circuit.allResults.Iv
    :type src: list of sympy symbols

    :param var: laplace variable
    :type var: sympy symbol

    :return: res: [Ares,Bres,C,D] where A and C are sympy matrices 
                  and B and D are lists of sympy matrices
    :rtype:  list

    :Example:
    """
    rows,cols=M.shape
    A,B,newq    = nth2firstOrder(laplace2coeffs(M, var),q)
    U,V,fc = UVsolve(A,B)
    Ares=-fc #No changes needed here
    rank=fc.shape[0]
    Uq=U*newq
    UAV=sp.cancel(U*A*V)
    UBV=sp.cancel(U*B*V)
    _ , Bi, C, Di = Block2StateSpace(rank,rows,Uq,UAV,UBV,V,src,var)
    return [Ares,Bi,C,Di]

def getStateSpace(instr):
    """
    Returns the the state space representation of the 
    circuit defined in the instruction:
    
    :param instr: Instruction for the circuit
    :type instr: SLiCAP instruction

    :return: res: [A,B,C,D, src, Dv] where A and C are sympy matrices
                  and B and D are lists of sympy matrices
    :rtype:  list

    :Example:
    """
    M,Dv = makeMatrices(instr)
    cir = instr.circuit
    Iv = makeSrcVector(cir,{},'all',value='id',numeric=False)
    src = sp.Matrix([sp.Symbol(i) for i in instr.indepVars()])
    A,B,C,D = MNA2StateSpace(M, Iv, src)
    
    return (A,B,C,D,src,Dv)
