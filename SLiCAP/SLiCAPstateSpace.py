from collections import namedtuple
import numpy as np
import sympy as sp
from sympy import QQ, EX
from sympy.polys.constructor import construct_domain
from sympy.polys.matrices import DomainMatrix
from sympy.polys.matrices.exceptions import DMNonInvertibleMatrixError
import SLiCAP.SLiCAPconfigure as ini


"""
State-space engine of SLiCAP.

Reduction of the first-order MNA pencil M = G + s*C (expanded stamps, see
SLiCAPmatrices._makeMatrices with method="state") to a state-space
realization, exact eigenvalues of the resulting A matrix, and the selection
of physical state variables. The mathematics is documented step by step in
the book notes MNA2state.tex (network theory chapter).

The circuit-level expansion of controlled sources that preceded the
matrix-level expansion was REMOVED on 2026-09-12 (Anton): superseded by
_makeMatrices(method="state") on 2026-09-09 (PZ.md, D1).
"""

# ---------------------------------------------------------------------
#  Exact linear algebra on rational matrices
# ---------------------------------------------------------------------
# sympy's Matrix.rank / columnspace / nullspace use a generic fraction-free
# row reduction on sympy Rationals: on a class-AB amplifier test project
# (22-row expanded matrix, 53-bit rational entries) one rank took 0.26 s
# against 0.008 s on DomainMatrix over QQ, same result (Anton, 2026-09-11).
# Matrix.inv already goes through DomainMatrix. Symbolic matrices (domain
# not ZZ/QQ) keep the generic path.

def _domainQQ(A):
    """
    Returns A as a DomainMatrix over QQ, or None when A is not rational.
    """
    if A.rows == 0 or A.cols == 0:
        return None
    d = DomainMatrix.from_Matrix(A)
    if d.domain.is_ZZ or d.domain.is_QQ:
        return d.convert_to(QQ)
    return None


def _rank(A):
    """
    Rank of the sympy matrix A (exact).
    """
    d = _domainQQ(A)
    return A.rank() if d is None else d.rank()


def _columnspace(A):
    """
    List of column vectors spanning the column space of A (exact).
    """
    d = _domainQQ(A)
    if d is None:
        return A.columnspace()
    B = d.columnspace().to_Matrix()
    return [B[:, j] for j in range(B.cols)]


def _nullspace(A):
    """
    List of column vectors spanning the null space of A (exact).
    """
    d = _domainQQ(A)
    if d is None:
        return A.nullspace()
    B = d.nullspace().to_Matrix()              # DomainMatrix: one basis vector per ROW
    return [B[j, :].T for j in range(B.rows)]


# ---------------------------------------------------------------------
#  The reduction works on DomainMatrix (Anton, 2026-10-15)
# ---------------------------------------------------------------------
# The elimination divides (Schur complements, null spaces, rref). On sympy
# expressions every division leaves an unreduced sum of fractions: the
# entries grow from round to round, and every rank decision needs a
# heuristic simplify() to recognise a zero (one rref of the symbolic G of
# VampQ: 244 s). In a DomainMatrix over the field of rational functions
# QQ(symbols, s) every entry is one reduced fraction p/q, kept reduced by
# every operation: the expressions stay compact, a zero is recognised
# exactly, and zeros are skipped (sparse storage). The same rref takes
# 0.1 s. The Laplace variable is not in the field: it occurs only in the
# right-hand side S(s) and in F(s), which are carried as lists of
# coefficient matrices [X0, X1, ...] for X0 + s X1 + ...; numeric matrices
# therefore stay over QQ. Minor expansion does not divide and gains nothing (det() stays as
# it is). Element values that are not rational functions of symbols, such
# as sqrt(L_1*L_2) of a unity coupling, would become an independent
# generator g and lose g**2 = L_1*L_2; the domain is then EX (sympy
# expressions with their own simplification), as before.

def _domain(*mats):
    """
    The field for the reduction of the matrices mats (free of the Laplace
    variable): QQ for numeric matrices, the rational functions of their
    symbols, or EX when an entry is not a rational function of symbols.
    """
    entries = [e for M in mats for e in M]
    K, _ = construct_domain(entries or [sp.Integer(0)], field=True)
    gens = getattr(K, "symbols", ())
    if K.is_EX or not all(g.is_Symbol or g is sp.pi for g in gens):
        return EX
    return K


def _dm(M, K):
    """
    The sympy matrix M as a DomainMatrix over K.
    """
    return DomainMatrix([[K.from_sympy(e) for e in M.row(i)] for i in range(M.rows)],
                        M.shape, K)


def _pivotBasis(A):
    """
    Returns (P, N) for a DomainMatrix A: a basis of the variables of A
    normalised on its pivots. P holds the unit columns at the pivot columns
    of the reduced row echelon form R of A, N the null space of A with a 1
    at one free column, 0 at the other free columns and minus the column of
    R at the pivots. [P N] is invertible, and the coordinates of x in this
    basis are R x (along P) and the free entries of x (along N).

    All bases of the reduction are chosen this way (Anton, 2026-10-15): a
    coordinate is then a network variable or a combination with the
    coefficients of R, e.g. the voltage across a floating capacitor, and
    the element values do not accumulate in the basis from round to round.
    The earlier choice, the rows of C themselves, carried the element values
    into every coordinate: correct, but unreadable symbolic matrices.
    """
    K = A.domain
    m, n = A.shape
    if m == 0 or n == 0:
        piv, R = (), []
    else:
        Rd, piv = A.rref()
        R = Rd.to_list()
    unit = lambda j: DomainMatrix([[K.one] if i == j else [K.zero] for i in range(n)], (n, 1), K)
    P = [unit(p) for p in piv]
    N = []
    for f in (j for j in range(n) if j not in piv):
        v = [K.zero]*n
        v[f] = K.one
        for i, p in enumerate(piv):
            v[p] = -R[i][f]
        N.append(DomainMatrix([[e] for e in v], (n, 1), K))
    return P, N


def _hstack(cols, rows, K):
    return DomainMatrix.hstack(*cols) if cols else DomainMatrix.zeros((rows, 0), K)


def _split(C):
    """
    Returns (U, V, r) for a DomainMatrix C with U C V = diag(C11, 0): V holds
    the unit columns at the pivot columns of C followed by its null space,
    U the unit rows at the pivot rows of C followed by its left null space
    (_pivotBasis); r = rank(C) and C11 is the invertible submatrix of C at
    those rows and columns.
    """
    n = C.shape[0]
    Vdyn, Valg = _pivotBasis(C)
    Udyn, Ualg = _pivotBasis(C.transpose())
    V = _hstack(Vdyn + Valg, n, C.domain)
    U = _hstack(Udyn + Ualg, n, C.domain).transpose()
    return U, V, len(Vdyn)


def _reduce(G, C):
    """
    Returns (A, P_in, P_out, D_map) of the descriptor system C x' = -G x + b:
    x' -> A z + P_in b for the states z, and x = P_out z + D_map b.

    Recursive index-1 elimination (Anton's proposal, verified and adopted
    2026-09-12, PZ.md "Recursive elimination"): split the variables on
    rank(C), eliminate the algebraic block by the Schur complement of G22.
    When G22 is singular its left null space gives constraints on the
    reactive variables (hidden constraints: the fixed reactances); these
    directions are eliminated as source-determined quantities, which is
    where derivatives of the sources enter, and the smaller system goes
    into the next round. The number of rounds is the index of the network.
    Derivatives of the sources that reach the dynamic block are moved into
    D_map by a change of state variables, so P_in is a constant matrix.

    D_map may contain the Laplace variable: an output that is the derivative
    of an input (the current through a voltage source with a capacitor
    across it) is improper, and is returned as such.

    The one-step alternative, the finite/infinite split of the pencil
    (_reducePencil), gives the same states and the same D_map (tests); it is
    kept as the cross-check. Measured on a test numerator matrix (22
    rows, index 3): pencil 3.7 s, this recursion 2.0 s; the state matrix of
    the recursion is also the better conditioned one (float eigenvalues).
    """
    s = ini.laplace
    n = G.rows
    K = _domain(G, C)
    eye, zero = DomainMatrix.eye(n, K), DomainMatrix.zeros((n, n), K)
    try:
        A, Pin, Pout, D = _eliminate(_dm(G, K), _dm(C, K), [eye], eye, [zero])
    except DMNonInvertibleMatrixError:
        raise sp.matrices.exceptions.NonInvertibleMatrixError(
            "the pencil (G, C) is singular: the network has no unique solution")
    Dfull = sp.zeros(n, n)
    for k, Dk in enumerate(D):
        Dfull += s**k*Dk.to_Matrix()
    return A.to_Matrix(), Pin.to_Matrix(), Pout.to_Matrix(), sp.expand(Dfull)


# Polynomials in s with matrix coefficients: lists [X0, X1, ...] of
# DomainMatrix for X0 + s X1 + ...

def _padd(P, Q):
    """P + Q."""
    if len(P) < len(Q):
        P, Q = Q, P
    return [P[k] + Q[k] if k < len(Q) else P[k] for k in range(len(P))]


def _pmul(M, P):
    """The constant matrix M times P."""
    return [M*X for X in P]


def _ptrim(P):
    """P without zero coefficients of the highest powers (at least X0)."""
    while len(P) > 1 and P[-1].is_zero_matrix:
        P = P[:-1]
    return P


def _eliminate(G, C, S, E, F):
    """
    One round of the recursive elimination on (G + sC) z = S(s) b with the
    reconstruction x = E z + F(s) b of the original variables; recurses on
    the reduced system and returns (A, P_in, P_out, D_map) with D_map a
    polynomial in s (list of coefficients). G, C, E and the coefficients of
    S and F are DomainMatrix over one field K, free of s.
    """
    K = G.domain
    Z = lambda m, n: DomainMatrix.zeros((m, n), K)
    m = G.shape[0]
    n = S[0].shape[1]
    if m == 0:
        return Z(0, 0), Z(0, n), Z(n, 0), _ptrim(F)
    r = C.rank()
    if r == 0:                                   # algebraic only
        return Z(0, 0), Z(0, n), Z(n, 0), _ptrim(_padd(_pmul(E*G.inv(), S), F))
    U, V, r = _split(C)
    Gt, Ct, St = U*G*V, U*C*V, _pmul(U, S)
    E = E*V
    G11, G12, G21, G22 = Gt[:r, :r], Gt[:r, r:], Gt[r:, :r], Gt[r:, r:]
    C11 = Ct[:r, :r]
    S1, S2 = [X[:r, :] for X in St], [X[r:, :] for X in St]
    q = (m - r) - (G22.rank() if m - r else 0)
    if q == 0:
        # ---- G22 invertible: Schur complement, the index-1 step
        G22i = G22.inv() if m - r else Z(0, 0)
        C11i = C11.inv()
        A = -(C11i*(G11 - G12*G22i*G21))
        Bk = _ptrim(_pmul(C11i, _padd(S1, _pmul(-(G12*G22i), S2))))   # B0 + s B1 + ...
        # derivatives of the sources in the dynamic block: y1 = z + Q(s) b,
        # Q = Bhat_1 + s Bhat_2 + ... + s^(d-1) Bhat_d
        d = len(Bk) - 1
        Bhat = {}
        for k in range(d, 0, -1):
            Bhat[k] = Bk[k] + (A*Bhat[k + 1] if k + 1 <= d else Z(r, n))
        Pin = Bk[0] + (A*Bhat[1] if d >= 1 else Z(r, n))
        Q = [Bhat[k] for k in range(1, d + 1)] or [Z(r, n)]
        E1, E2 = E[:, :r], E[:, r:]
        Pout = E1 - E2*G22i*G21
        Dfull = _padd(_padd(_pmul(Pout, Q), _pmul(E2*G22i, S2)), F)
        return A, Pin, Pout, _ptrim(Dfull)
    # ---- G22 singular: hidden constraints on the reactive variables
    Wp, Wn = _pivotBasis(G22.transpose())
    W = _hstack(Wn, m - r, K).transpose()                           # q x (m-r), W G22 = 0
    Wc = _hstack(Wp, m - r, K).transpose()                          # the other equations
    Kc = W*G21                                                      # q x r
    if Kc.rank() < q:
        raise DMNonInvertibleMatrixError("singular pencil")
    Kp, Kn = _pivotBasis(Kc)
    Y1 = _hstack(Kn, r, K)                                          # free directions
    Y2 = _hstack(Kp, r, K)                                          # fixed directions
    v2 = _pmul((Kc*Y2).inv()*W, S2)                                 # they follow the sources
    Gn = DomainMatrix.vstack(DomainMatrix.hstack(G11*Y1, G12),
                             DomainMatrix.hstack(Wc*G21*Y1, Wc*G22))
    Cn = DomainMatrix.vstack(DomainMatrix.hstack(C11*Y1, Z(r, m - r)),
                             Z(Wc.shape[0], r - q + m - r))
    # (G11 + s C11) Y2 v2: the fixed reactances draw s C11 Y2 v2
    GCv = _padd(_pmul(G11*Y2, v2), [Z(r, n)] + _pmul(C11*Y2, v2))
    top = _padd(S1, [-X for X in GCv])
    bot = _padd(_pmul(Wc, S2), _pmul(-(Wc*G21*Y2), v2))
    Sn = _ptrim([DomainMatrix.vstack(t, b) for t, b in zip(_padd(top, [Z(r, n)]*len(bot)),
                                                          _padd(bot, [Z(Wc.shape[0], n)]*len(top)))])
    En = DomainMatrix.hstack(E[:, :r]*Y1, E[:, r:])
    Fn = _padd(F, _pmul(E[:, :r]*Y2, v2))
    return _eliminate(Gn, Cn, Sn, En, Fn)


def _reducePencil(G, C):
    """
    Returns (A, P_in, P_out, D_map) of C x' = -G x + b from the finite /
    infinite split of the pencil (G, C); the states are the finite part.

    The one-step alternative to the recursive elimination of _reduce, kept
    as the cross-check (tests compare both) and for the book (2026-09-12).

    With T = (G + s0 C)^-1 C the finite eigenvalues are s0 - 1/mu for the
    nonzero eigenvalues mu of T; the infinite ones are its nilpotent part.
    T is raised to the power at which its rank stabilises; the states then
    span the range of that power, the fixed reactances its null space.
    """
    N = G.rows
    s = ini.laplace
    # Any s0 that is not a pole will do, and the result does not depend on
    # it (the state subspace is the pencil's deflating subspace; another s0
    # changes A by a similarity only). det(G + sC) has at most N roots, so
    # among N + 1 distinct candidates at least one is not a pole - a finite
    # fixed list was not a proof (Anton, 2026-09-10). 0 is tried first: it
    # needs no shift at all when G is invertible.
    for s0 in [sp.Integer(k) for k in range(N + 1)]:
        try:
            Ri = (G + s0*C).inv()
            break
        except sp.matrices.exceptions.NonInvertibleMatrixError:
            continue
    else:
        raise sp.matrices.exceptions.NonInvertibleMatrixError(
            "the pencil (G, C) is singular: the network has no unique solution")
    T  = Ri * C
    # Raise T until its rank no longer drops (Fitting decomposition): then
    # range(T^k) and null(T^k) are complementary whatever the index. The
    # index of a network with the standard elements is at most 2, but with
    # nullators/norators it was measured higher (VampOV, asymptotic gain).
    K, rk = T, _rank(T)
    for _ in range(N):
        K2, rk2 = K * T, None
        rk2 = _rank(K2)
        if rk2 == rk:
            break
        K, rk = K2, rk2
    Vs = _columnspace(K)                                       # states: range(T^k)
    Ws = _nullspace(K)                                         # fixed reactances + algebraic
    r  = len(Vs)
    X  = sp.Matrix.hstack(*(Vs + Ws)) if (Vs + Ws) else sp.eye(N)
    Xi = X.inv()
    Tt = Xi * T * X
    Bt = Xi * Ri                                               # maps b into the new basis
    # dynamic block
    if r:
        Tr  = Tt[:r, :r]
        Tri = Tr.inv()
        A   = s0*sp.eye(r) - Tri
        Pin = Tri * Bt[:r, :]
        Pout = X[:, :r]
    else:
        A, Pin, Pout = sp.zeros(0, 0), sp.zeros(0, N), sp.zeros(N, 0)
    # nilpotent block: (I + (s - s0) Nn)^-1 = sum_j (-(s - s0) Nn)^j, finite
    Nn  = Tt[r:, r:]
    m   = N - r
    Ser = sp.eye(m)
    Pw  = sp.eye(m)
    for _ in range(m):
        Pw = -(s - s0) * Pw * Nn
        if Pw == sp.zeros(m):
            break
        Ser = Ser + Pw
    Dfull = X[:, r:] * Ser * Bt[r:, :]
    return A, Pin, Pout, sp.expand(Dfull)


def physicalStates(A, Pin, Pout, Dfull, candidates):
    """
    Changes the state coordinates so that as many of them as possible are
    single physical quantities (Anton, 2026-09-11; PZ.md "Prescribed
    (physical) state variables"; MNA2state.tex section "Physical state
    variables").

    A candidate is a network quantity l x, with l a selection row vector on
    the network variables. It can serve as a state variable iff it depends
    on the states alone, i.e. l D_full = 0 for the full feedthrough map (the
    same as: l orthogonal to the annihilated subspace). Candidates are taken
    in the given order and kept when they pass and are independent, on the
    state subspace, of those already kept; every maximal set has the same
    size, the maximum number of single physical states. Coordinates that
    remain are the original ones, named x_k.

    :param candidates: list of (name, l) with l a 1 x n sympy row vector
    :return: (A', P_in', P_out', names) with Q A Q^-1, Q P_in, P_out Q^-1
             for Q = C_ph P_out, and the state names.
    """
    r = A.rows
    if r == 0:
        return A, Pin, Pout, []
    rows, names = [], []
    for name, l in candidates:
        if not (l*Dfull).applyfunc(sp.cancel).is_zero_matrix:
            continue                                  # feedthrough: not a state
        lp = l*Pout
        if lp.is_zero_matrix:
            continue
        if _rank(sp.Matrix.vstack(*(rows + [lp]))) == len(rows) + 1:
            rows.append(lp)
            names.append(name)
        if len(rows) == r:
            break
    for j in range(r):                                # completion: keep old coordinates
        if len(rows) == r:
            break
        e = sp.zeros(1, r)
        e[0, j] = 1
        if _rank(sp.Matrix.vstack(*(rows + [e]))) == len(rows) + 1:
            rows.append(e)
            names.append("x_%d" % (j + 1))
    Q = sp.Matrix.vstack(*rows)
    Qi = Q.inv()
    return Q*A*Qi, Q*Pin, Pout*Qi, names


# The field P (states -> network variables) was REMOVED on 2026-09-20: with
# every network variable an output it is always C (Anton). realize(), the
# output-selecting realization that had P = C only as a special case, had
# no callers and went with it.
StateSpace = namedtuple("StateSpace", ["A", "B", "C", "D", "x", "u", "y"])
"""
State-space realization: dx/dt = A x + B u, y = C x + D u, with the vectors
x (states), u (inputs) and y (outputs) as sympy symbols, and P the map from
the states to the network variables.
"""


def _balance(A):
    """
    Osborne balancing of the exact matrix A with powers of two: a diagonal
    similarity D A D^-1 that equalises the norms of the off-diagonal parts of
    each row and column. Exact (the scale factors are powers of 2), so the
    eigenvalues are unchanged; only the conditioning of the eigenvalue
    problem improves. Norm estimates in floats are good enough for the
    choice of the factors.
    """
    A = A.copy()
    n = A.rows
    for _ in range(50):
        changed = False
        for i in range(n):
            c = sum(abs(float(A[k, i])) for k in range(n) if k != i)
            r = sum(abs(float(A[i, k])) for k in range(n) if k != i)
            if c > 0 and r > 0:
                f = sp.Integer(2)**int(round(np.log2(np.sqrt(r/c))))
                if f != 1:
                    A[:, i] = A[:, i]*f
                    A[i, :] = A[i, :]/f
                    changed = True
        if not changed:
            break
    return A


def _eigExact(A, dps=30):
    """
    Eigenvalues of the exact (rational) matrix A as a numpy array of complex
    floats: exact balancing, then the QR algorithm of mpmath at dps digits.

    Decided with Anton (2026-09-12, PZ.md "Recursive elimination"): the
    float image of A fed to LAPACK was off by 1e-3 on the zeros of some
    numerator matrices (a non-normal state basis); the eigenvalues of the
    exact matrix at 30 digits are accurate to 1e-12 at a few tenths of a
    second for 14 states, and they remain EIGENVALUES, so coinciding poles
    are resolved instead of split by a polynomial root finder. The
    alternative, the exact characteristic polynomial with numpy roots, was
    measured equally accurate and much faster but is companion-matrix root
    finding again: REJECTED for that reason.
    """
    import mpmath as mp
    if A.rows == 1:                                  # mpmath returns a tuple here
        return np.array([complex(A[0, 0])], dtype=complex)
    Ab = _balance(A)
    n = Ab.rows
    with mp.workdps(dps):
        Mm = mp.matrix([[mp.mpf(int(sp.Rational(e).p))/mp.mpf(int(sp.Rational(e).q))
                         for e in Ab.row(i)] for i in range(n)])
        E = mp.eig(Mm, left=False, right=False)
        return np.array([complex(z) for z in E], dtype=complex)


def _rootsExact(M, s=None):
    """
    Finite roots of det(M(s)) for a first-order numeric matrix M = G + s C:
    the states are sorted exactly by _reduce, the eigenvalues are computed in
    floats. Returns a numpy array (empty for a constant determinant), or
    None when det(M) is identically zero.
    """
    if s is None:
        s = ini.laplace
    G, C = M.subs(s, 0), M.diff(s)
    if _rank(C) == 0:
        return np.array([], dtype=complex)
    try:
        A = _reduce(G, C)[0]
    except sp.matrices.exceptions.NonInvertibleMatrixError:
        return None
    if A.rows == 0:
        return np.array([], dtype=complex)
    roots = _eigExact(A)
    # Roots at the origin are a structural fact and are made EXACT: the
    # algebraic multiplicity of the zero eigenvalue is r - rank(A^k) at the
    # power where the rank stabilises (exact rationals, cheap on the
    # reduced matrix). In floats eig() returns 1e-17 instead of 0, and
    # _cancelPZ's relative tolerance cannot pair two near-zeros - the
    # determinant path gets an exact 0.0 from an exactly zero constant
    # coefficient, and the two paths must agree (found on the coupled
    # inductors, 2026-09-11).
    K, rk = A, _rank(A)
    for _ in range(A.rows):
        K2 = K * A
        rk2 = _rank(K2)
        if rk2 == rk:
            break
        K, rk = K2, rk2
    n0 = A.rows - rk
    if n0:
        order = np.argsort(np.abs(roots))
        roots[order[:n0]] = 0.0
    return _realizeUnpaired(roots)


def _realizeUnpaired(roots, rel=1e-6):
    """
    Roots of a real matrix come in conjugate pairs or are real. A root with
    an imaginary part but WITHOUT a conjugate partner is a rounding residue
    of the eigenvalue computation (Anton, 2026-09-20): when its imaginary
    part is smaller than *rel* times its real part it is made real; when it
    is larger, the residue is serious and a warning is printed, the root is
    kept as it is. Two roots are partners when they are each other's
    conjugate to within *rel* of their magnitude.
    """
    roots = np.array(roots, dtype=complex)
    for i, z in enumerate(roots):
        if z.imag == 0:
            continue
        scale = max(abs(z), 1e-300)
        paired = any(j != i and abs(w - np.conj(z)) <= rel * scale
                     for j, w in enumerate(roots))
        if paired:
            continue
        if abs(z.imag) <= rel * abs(z.real):
            roots[i] = complex(z.real, 0.0)
        else:
            print("Warning: root %s has an imaginary part without a "
                  "conjugate partner: serious rounding error." % z)
    return roots


# =====================================================================
#  Self-verification (differential-test the core against the transfer)
# =====================================================================
if __name__ == "__main__":
    s = sp.Symbol("s")

    Ri, Ro, Ra, Rb , gm, Ci, Co, Cr = sp.symbols("Ri Ro Ra Rb gm Ci Co Cr", positive=True)
    G = sp.Matrix([[1/Ri, 0, 0],
                [gm, 1/Ro+1/Ra, -1/Ra],
                [0, -1/Ra, 1/Rb]])         
    C = sp.Matrix([[Ci + Cr, -Cr, 0],
                [0, Co + Cr, 0],
                [0, 0, 0]])   

    A, P_in, P_out, D_Full = _reduce(G, C)
    print(A)
    A.eigenvals()