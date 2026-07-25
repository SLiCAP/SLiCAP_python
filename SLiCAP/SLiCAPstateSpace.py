import copy
import numpy as np
import sympy as sp
import SLiCAP.SLiCAPconfigure as ini
from SLiCAP.SLiCAPmath import coeffsTransfer, _cancelPZ, float2rational
from SLiCAP.SLiCAPprotos import element

"""
General remarks
===============

1. State-space representation has not been implemented for models "EZ" and "HZ".
   From version 6 SLiCAP's built-in SLiCAPmodels.lib does no longer use these elements.
    
2. Only 'strictly proper' transfer functions can be written in state-space notation. 
   Hence, all transfer functions for element models E, F, G, and H, must be strictly 
   proper (order denominator >= order numerator).

   SLiCAP accepts non-proper transfer functions for concept design, but it cannot 
   derive the state-space representaion for it.

3. The circuit attribute .proper indicates if the circuit is strictly proper:
    
   - .proper = 0: not a proper circuit.
   - .proper = k: proper circuit, k = sum of degrees of denominator polynomials of 
                  controlled sources.

4. All controlled sources add an extra k rows and k columns to the MNA matrix and k rows 
   to the vectors Iv and Dv. The names of these independent variables are:
       
   - V_i_<refDes>, which are the state voltages of the i-th order of element <refDes>.
   
5. Currently, SLiCAP calculates the loop gain and the servo function from the 
   return difference expression. This way of working is not compatible with the 
   derivation of the state-space representation.
       
   - The best way of working would be to introduce the feedback matrix and find
     a state-space notation compatible with the asymptotic-gain model.
     
   - Another way of working is to create a differenial and common-mode detector 
     component that refers its output to the reference node. In this case the 
     numerator of transfer functions can be calculated using one single minor matrix. 
     This can be done using simple column modifications on the MNA matrix such that
     one the response is always a single output variable.
     
   - The servo functions will be evaluated from the loop gain. Zeros of the servo functions
     equal thos of the loop gain, Poles of the servo function are the solution of the 
     root-locus equation D_S(s) = D_L(s)-N_L(s) = 0, where D_S(s) is the denominator of the 
     servo function, D_L(s) the denominator polynomial of the loop gain and N_L(s) the 
     numerator of the loop gain polynomial. The order of D_S(s) is equal to the order of 
     D_L(s). By doing so, no state-space matrix is available for the servo function.
     
6. There are two possible ways for obtaining a first-order matrix in the differential form

   - Matrix expansion
   
     With matrix expansion we can build the full-rank state-space matrix.
     
   - Circuit expansion
   
     With circuit expansion we can build the time-constant matrix and the 
     full-rank state-space matrix.

Procedure of the matrix modification
====================================

Only if gainType != 'loopgain' or 'servo'

The procedure is as follows:
    
1. In _makeMatrices, determine k and set this property to instr.circuit.

2. Add k rows and k columns to the MNA matrix M and k rows to the vector D_v (all zeros)

3. For each controlled source modify the matrix stamp as shown in the book.
   
Procudure of circuit expansion
==============================

1. Built a dynamic block with the canonical form of the rational function
2. Add input and output controlled sources for the correct transfer type
   for each controlled source
   
"""   

def _expand_polys(circuit):
    cir = copy.deepcopy(circuit)
    for refdes, el in cir.elements.items():
        if ini.laplace in el.params["value"].free_symbols():
            if el.model == "E":
                cir.elements += _expand_es(el)
                del cir.elements[refdes]
            elif el.model == "F":
                cir.elements += _expand_fs(el)
                del cir.elements[refdes]
            elif el.model == "G":
                cir.elements += _expand_fs(el)
                del cir.elements[refdes]
            elif el.model == "H":
                cir.elements += _expand_hs(el)
                del cir.elements[refdes]
    return cir

def _expand_es(el):
    num_coeffs, den_coeffs = _get_coeffs(el)
    n_in                   = "q_0_{}".format(el.refDes)
    new_elements = _transfer_elements(el)
    # input g, output H
    g_in  = element()
    g_in.refDes  = "G_in_{}".format(el.refDes)
    g_in.nodes   = [n_in, "0", el.nodes[2], el.nodes[3]]
    g_in.model   = "g"
    g_in.type    = "G"
    g_in.params["value"] = sp.Rational(1)
        
    h_out = element()
    h_out.refDes  = "H_out_{}".format(el.refDes)
    h_out.nodes   = [el.nodes[0], el.nodes[1]]
    h_out.model   = "H"
    h_out.type    = "H"
    h_out.refs    = ["V_o_q_{}".format(el.refDes)]
    h_out.params["value"] = sp.Rational(1)
    
    new_elements[g_in.refDes] = g_in
    new_elements[h_out.refDes] = h_out
    return new_elements

def _expand_fs(el):
    num_coeffs, den_coeffs = _get_coeffs(el)
    new_elements = _transfer_elements(el)
    # input F, output F
    f_in  = element()
    f_in.refDes  = "F_in_{}".format(el.refDes)
    f_in.nodes   = [el.nodes[0], el.nodes[1]]
    f_in.model   = "F"
    f_in.type    = "F"
    f_in.refs    = el.refs
    f_in.params["value"] = sp.Rational(1)
        
    f_out = element()
    f_out.refDes  = "F_out_{}".format(el.refDes)
    f_out.nodes   = [el.nodes[0], el.nodes[1]]
    f_out.model   = "F"
    f_out.type    = "F"
    f_out.refs    = ["V_o_q_{}".format(el.refDes)]
    f_out.params["value"] = sp.Rational(1)
    return new_elements

def _expand_gs(el):
    num_coeffs, den_coeffs = _get_coeffs(el)
    n_in                   = "q_0_{}".format(el.refDes)
    new_elements = _transfer_elements(el)
    # input g, output F
    g_in  = element()
    g_in.refDes  = "G_in_{}".format(el.refDes)
    g_in.nodes   = [n_in, "0", el.nodes[2], el.nodes[3]]
    g_in.model   = "g"
    g_in.type    = "G"
    g_in.params["value"] = sp.Rational(1)
    g_in  = element()
        
    f_out = element()
    f_out.refDes  = "F_out_{}".format(el.refDes)
    f_out.nodes   = [el.nodes[0], el.nodes[1]]
    f_out.model   = "F"
    f_out.type    = "F"
    f_out.refs    = ["V_o_q_{}".format(el.refDes)]
    f_out.params["value"] = sp.Rational(1)
    return new_elements

def _expand_hs(el):
    new_elements = _transfer_elements(el)
    new_elements = _transfer_elements(el)
    # input F, output H
    f_in  = element()
    f_in.refDes  = "F_in_{}".format(el.refDes)
    f_in.nodes   = [el.nodes[0], el.nodes[1]]
    f_in.model   = "F"
    f_in.type    = "F"
    f_in.refs    = el.refs
    f_in.params["value"] = sp.Rational(1)
        
    h_out = element()
    h_out.refDes  = "H_out_{}".format(el.refDes)
    h_out.nodes   = [el.nodes[0], el.nodes[1]]
    h_out.model   = "H"
    h_out.type    = "H"
    h_out.refs    = ["V_o_q_{}".format(el.refDes)]
    h_out.params["value"] = sp.Rational(1)
    return new_elements

def _transfer_elements(el):
    new_elements           = {}
    num_coeffs, den_coeffs = _get_coeffs(el)
    n_in                   = "q_0_{}".format(el.refDes)
    n_out                  = "q_out_{}".format(el.refDes)
    for i in range(len(den_coeffs)):
        g_out_i        = element()
        g_out_i.refDes = "G_o_{}_{}".format(i, el.refDes)
        g_out_i.nodes  = [n_out, "0", "q_{}_{}".format(i, el.refDes), "0"]
        g_out_i.model  = "g"
        g_out_i.type   = "G"
        g_out_i.params["value"] = float2rational(num_coeffs[i])
        
        g_in_i  = element()
        g_in_i.refDes  = "G_i_{}_{}".format(i, el.refDes)
        g_in_i.nodes   = [n_in, "q_{}_{}".format(i, el.refDes), "0"]
        g_in_i.model   = "g"
        g_in_i.type    = "G"
        g_in_i.params["value"] = float2rational(den_coeffs[i])
        
        v_out  = element()
        v_out.refDes  = "V_o_q_{}".format(el.refDes)
        v_out.nodes   = ["0", n_out]
        v_out.model   = "V"
        v_out.type    = "V"
        v_out.params["value"] = sp.N(0)
        
        if i:
            g_q_i   = element()
            g_q_i.refDes  = "G_q_{}_{}".format(i, el.refDes)
            g_in_i.nodes  = ["q_{}_{}".format(i, el.refDes), "0", "q_{}_{}".format(i-1, el.refDes), "0"]
            g_q_i.model   = "g"
            g_q_i.type    = "G"
            g_q_i.params["value"] = sp.Rational(1)
            
            c_q_i   = element()
            c_q_i.refDes = "C_q_{}_{}".format(i, el.refDes)
            c_q_i.nodes  = ["q_{}_{}".format(i, el.refDes), "0"]
            c_q_i.model  = "C"
            c_q_i.type   = "C"
            c_q_i.params["value"] = sp.Rational(1)
        
    new_elements[g_out_i.refDes] = g_out_i
    new_elements[g_in_i.refDes]  = g_in_i
    new_elements[g_q_i.refDes]   = g_q_i
    new_elements[c_q_i.refDes]   = c_q_i
    return new_elements
    
def _get_coeffs(el):
    num, den   = el.params['value'].as_numer_denom()
    num_coeffs = sp.Poly(num, ini.laplace).all_coeffs()
    den_coeffs = sp.Poly(den, ini.laplace).all_coeffs()
    for i in range(len(den_coeffs) - len(num_coeffs)):
        num_coeffs = [0] + num_coeffs
    return num_coeffs, den_coeffs

# =====================================================================
#  Pure matrix core (variable = ini.laplace, no SLiCAP objects)
# =====================================================================


def _reduce(G, C):
    """Descriptor pencil (G, C) with full I/O -> A, P_in (rxN), P_out (Nxr), D (NxN)."""
    N = G.rows
    if C.rank() == N:                                          # C invertible: proper already
        Ci = C.inv()
        return -Ci * G, Ci, sp.eye(N), sp.zeros(N)
    Vdyn  = sp.Matrix.hstack(*C.T.columnspace())               # rowspace(C)
    Valg  = sp.Matrix.hstack(*C.nullspace())                   # null(C)
    Udyn  = sp.Matrix.vstack(*[v.T for v in C.columnspace()])  # colspace(C)
    Ualg  = sp.Matrix.vstack(*[v.T for v in C.T.nullspace()])  # leftnull(C)
    V, U  = Vdyn.row_join(Valg), Udyn.col_join(Ualg)
    r     = Vdyn.cols
    Gt    = U * G * V
    G11, G12, G21, G22 = Gt[:r, :r], Gt[:r, r:], Gt[r:, :r], Gt[r:, r:]
    C11   = (U * C * V)[:r, :r]
    C11i, G22i = C11.inv(), G22.inv()
    A     = -C11i * (G11 - G12 * G22i * G21)
    Pin   = C11i * (Udyn - G12 * G22i * Ualg)
    Pout  = Vdyn - Valg * G22i * G21
    Dfull = Valg * G22i * Ualg
    return A, Pin, Pout, Dfull

def mna_to_state(G, C):
    """
    MNA matrix M(ini.laplace) -> system realization (A, P_in, P_out, D_map)
    over the original circuit variables (companion blocks folded in).
 
    Source-/detector-agnostic: select a transfer afterwards with state_transfer().
    """
    A, Pin_full, Pout_full, Dfull = _reduce(G, C)
    
    # Extract the scalar number of states (rows of A)
    n = A.shape[0]  
    
    # Calculate the companion block factor (order of the system)
    # Total original variables divided by states per block
    N = G.shape[0]
    m = N // n      
    
    return (A,
            Pin_full[:, :n],              # n is now an integer
            Pout_full[(m - 1) * n:, :],   # correctly offsets to the last block
            Dfull[(m - 1) * n:, :n])

def _row(P, detP, detN):
    row = P[detP, :]
    return row if detN is None else row - P[detN, :]

def state_transfer(ss, Iv, detP, detN=None):
    """Select the source(Iv) -> detector(detP[,detN]) transfer: -> (A, B, C, D)."""
    A, Pin, Pout, Dmap = ss
    return A, Pin * Iv, _row(Pout, detP, detN), _row(Dmap, detP, detN) * Iv

def _np(M):
    return np.array(M.evalf().tolist(), dtype=complex)

def transfer_gpz(A, B, C, D):
    """Transfer (A,B,C,D) -> (gain, poles, zeros).  poles/zeros are numpy arrays."""
    r         = A.rows
    poles     = np.linalg.eigvals(_np(A))
    # transmission zeros = finite generalized eigenvalues of the Rosenbrock pencil
    from scipy.linalg import eig
    P         = np.block([[_np(A), _np(B)], [_np(C), _np(D)]])
    Q         = np.zeros((r + 1, r + 1), dtype=complex)
    Q[:r, :r] = np.eye(r)
    al, be    = eig(P, Q, right=False, homogeneous_eigvals=True)
    fin       = np.abs(be) > 1e-9 * np.max(np.abs(be)) if be.size else be.astype(bool)
    zeros     = al[fin] / be[fin]
    # gain = lowest-order coefficient ratio (reuse coeffsTransfer)
    s         = ini.laplace
    H         = sp.cancel((C * (s * sp.eye(r) - A).inv() * B + D)[0])
    gain      = coeffsTransfer(H, s)[0]
    return gain, poles, zeros

# =====================================================================
#  SLiCAP-facing instruction
# =====================================================================
def doStateSpace(result):
    """
    State-space pole/zero/gain analysis from a doMatrix() result.

    Reduces result.M to a minimal state space, selects the transfer from the
    result's source (result.Iv) to its detector, and stores:
        result.poles, result.zeros           (numpy arrays, solutions in s)
        result.DCvalue = transfer gain        (TEMPORARY, see module note)
        result.stateSpace = (A, B, C, D, P_in, P_out)   (the realization)

    Returns a copy of the passed result; the original is not modified.
    """
    from SLiCAP.SLiCAPexecute import _makeDetPos, _makeAllMatrices   # reuse; lazy = no cycle
    out = copy.deepcopy(result)
    # doMatrix leaves Iv as the value-based RHS; rebuild M/Iv/Dv with the
    # gainType-governed transfer source vector (unit excitation at the source).
    if out.gainType not in ('gain', 'asymptotic', 'direct'):
        out.gainType = 'gain'
    _makeAllMatrices(out)
    detP, detN         = _makeDetPos(out)                      # detector positions (differential-aware)
    # Rationalize float entries before descriptor reduction so that SymPy's
    # rank/nullspace/columnspace use exact arithmetic (same pattern as det() in SLiCAPmath).
    ss                 = mna_to_state(float2rational(out.M))
    A, B, C, D         = state_transfer(ss, out.Iv, detP, detN)
    gain, poles, zeros = transfer_gpz(A, B, C, D)
    out.stateSpace     = (A, B, C, D, ss[1], ss[2])            # A, B, C, D, P_in, P_out
    poles, zeros       = _cancelPZ(list(poles), list(zeros))   # pz behaviour (doPZ cancels)
    out.poles, out.zeros, out.DCvalue = poles, zeros, gain
    out.dataType = 'pz'                                        # reuse the pz display path
    return out

# =====================================================================
#  Self-verification (differential-test the core against the transfer)
# =====================================================================
if __name__ == "__main__":
    s = ini.laplace

    def _H_true(M, Iv, detP, detN):
        d = sp.zeros(1, M.rows); d[0, detP] = 1
        if detN is not None:
            d[0, detN] -= 1
        return sp.cancel((d * M.inv() * Iv)[0])

    def _cx(a):
        return sorted([complex(x) for x in a], key=lambda z: (round(z.real, 9), round(z.imag, 9)))

    def _check(M, Iv, detP, detN, label):
        A, B, C, D = state_transfer(mna_to_state(M), Iv, detP, detN)
        gain, poles, zeros = transfer_gpz(A, B, C, D)
        H = _H_true(M, Iv, detP, detN); num, den = H.as_numer_denom()
        g_ref = coeffsTransfer(H, s)[0]
        p_ref = [complex(sp.N(r)) for r in sp.roots(sp.Poly(den, s)).keys() for _ in range(sp.roots(sp.Poly(den, s))[r])]
        z_ref = [complex(sp.N(r)) for r in sp.roots(sp.Poly(num, s)).keys() for _ in range(sp.roots(sp.Poly(num, s))[r])]
        okg = sp.simplify(gain - g_ref) == 0
        okp = len(_cx(poles)) == len(_cx(p_ref)) and all(abs(a - b) < 1e-7 for a, b in zip(_cx(poles), _cx(p_ref)))
        okz = len(_cx(zeros)) == len(_cx(z_ref)) and all(abs(a - b) < 1e-7 for a, b in zip(_cx(zeros), _cx(z_ref)))
        print(f"{label:32s} gain:{okg}  poles:{okp}  zeros:{okz}")
        return okg and okp and okz

    Cm = sp.Matrix([[2, 1, 0], [1, 1, 0], [1, 0, 0]])
    Gm = sp.Matrix([[3, 0, 1], [0, 4, 2], [1, 2, 5]])
    ok1 = _check(Gm + s * Cm, sp.Matrix([1, 0, 0]), 2, None, "first-order, single-ended")
    ok2 = _check(Gm + s * Cm, sp.Matrix([1, 0, -1]), 0, 1, "first-order, differential I/O")
    M0 = sp.Matrix([[2, 1], [0, 3]]); M1 = sp.Matrix([[1, 0], [1, 2]]); M2 = sp.Matrix([[1, 0], [0, 0]])
    ok3 = _check(M0 + s * M1 + s**2 * M2, sp.Matrix([1, -1]), 0, 1, "higher-order, differential I/O")
    print("\nALL PASS:", ok1 and ok2 and ok3)
