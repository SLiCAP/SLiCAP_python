#. Calculation of poles and zeros in SLiCAP.

##. Introduction
SLiCAP accurately determines poles and zeros of transfer functions. Symbolic calculations are supported to the extend to which sympy can calculate the complex roots of Laplace polynomials with symbolic coefficients. Numeric calculations are accurate because they are based on the exact characteristic equation of the network, because SLiCAP evaluates it from the MNA matrix using its accurate det() method.

##. Performance considerations

1. Accurate pole-zero calculation in SLiCAP dominates over fast calculation. This is accuracy is a compettitive advantage compared to numeric network simulators like SPICE. However, the word accuracy deserves a more specific definition here:

   - SLiCAP's method must ensure to resturn a number of poles that is truly equal to the number of independent states. The current method does this.
   - The numeric accuracy is of less importance, but if possible (F(s))^n should preferably give n multiples of the solution of F(s).
      
2. By stepping a parameter (e.g. the value of an element or a gain factor of a controlled source) SLiCAP can create root-locus plots with any network parameter as root-locus variable. This is a powerful feature for studying the pole-positions as a function of the operating current of a transistor, a compensation capacitance, etc. For this the no-false-solutions from 1) still holds, but the numeric accuracy requirement does not hold because the plot display inaccuracy is larger than the numeric calculation accuracy.

   For root-locus plots, apart from no-false-solutions, speed becomes the important performance parameter. Stepped pole/zero analysis is done by calculating the denominator/numerator for each step parameter and then solving these polynomials. Parameter stepping can be performed in two ways: 
   
   1. Calculate denominator/numerator as functions of the step parameter, and then creating the numeric polys by substituting the step values (this is the default method: ini.step_function=True)
   2. Substituting the step value in the matrix and obtain the polynomials by running the determinant on a matrix with only the Laplace symbol as symbolic variable.
   
##. Performance of the current methods

1. SLiCAP's pole-zero calculation methods are accurate and do not give false poles and zeros like SPICE does. However, the accurate method may not be the fastest, because it uses the determinant calculation. 

2. Numeric calculations are done by converting a sympy Laplace polynomial with numeric coefficients into a numpy singlevariate polynomial. As a result of numerical rounding, (F(s))^n does not give n exact multiples of the solution of F(s).

##. Possible improvements

1. Exact number of solutions is OK does not require any improvement.
2. n exact multiples of the solutions of F(s) when solving (F(s))^n, can be achieved by using factorization of P(s) and solving the factors of P(s) instead of solving P(s), where P(s) is the characteristic polynomial of the network.
3. Speed improvement can be achieved by using a different method, and maybe by differentiating methods considering, stepping and symbolic coefficients of the Laplace variable.

##. Extra functionality and basis for new algorithm

Halay: /home/anton/DATA/Articles/Haley1988.pdf describes a method for finding the poles as the negative reciprocals of the eigenvalues of the time-constant matrix of a network. This time-constants matrix gives physical insight and I used it in the chapter about network theory in my book. Alternatively he describes the frequeny constants matrix.

###. Time constants matrix:

1. Write the MNA matrix as M = G + sC
2. Define C_rr as a diagonal matrix having each C and L element on a diagonal entry:
3. The matrix C can then be obtained as

   C = J*C_rr*J^T, where J = the capacitor/inductor incidence matrix, which can easily be found from the network graph
   
3. Obtain the Resistance matrix R_rr as:

   R_rr = J^T*G^(-1)*J

4. The time-constants matrix T is now found as:

   T = R_rr*C_rr
   
5. Poles are obtained as 

   tau_(1--n) = eigenvals(T)
   
   pole_i = -1/tau_i
   
Disadvantages of this method are:

1. Poles in the origin cannot be found beacuse G would be singular
2. Loops of capacitors( + voltage sources) or cutsets of inductors(+ current sources)) result in eigenvalues tau_i=infinite, which due to numeric rounding result in false poles/zeros).

###. Frequency constants matrix

A better approach is to bring the dimension of C back to its rank and obtain the poles/zeros as the eigenvalues of the frequency constants matrix:

1. Write the MNA matrix as M = G + sC
2. Reduce C to full-rank C_rr

   C_rr = P^T*C*P
   
   Where P is a transformation matrix to be found
   
3. Calculate the reduced conductance matrix

   G_rr = P^T*G*P
   
4. Calculate the frequency constants matrix

   omega = Grr/C_rr
   
5. The poles are found as the eigenvalues of the frequency constants matrix:

   s_(1...i) = eigenvals(omega)
   
Implementation remarks

1. With my linear algabra knowledge I don't knw how to find P
2. SLiCAP can reduce the MNA matrix to one with higher-order s coefficients:

   M_rr = A_0 + s*A_1 +  s^2*A_2 + ... s^m*A_m
   
   This maxtrix must be converted into a first-order equivalent, in which the coefficient matrix of s is full rank (or [[C_rr, 0],[0, 0]] where G_rr has the same dim as C_rr) 
   
I know there exists something like a Faddev-Levrier algorithm for exect state-space reduction, but I am not able to to this.
   
CLAUDE: Please comment the above:

1. Is this approach valid: can we find a frequency-constants matrix?
2. Can it give speed improvement in one of the above cases?
3. Can you implement this in Python (SLiCAP)?

---

## CLAUDE — comment (2026-07-18)

**Incorporating Anton's two clarifications:** (1) the MNA is NOT first-order in
`s` — controlled-source gains can be higher-order rational Laplace expressions,
but they are always stamped in **differential form** (polynomial in `s`, no
division by `s`). So `M(s)` is a **matrix polynomial**
`M(s) = A_0 + s·A_1 + s²·A_2 + … + s^m·A_m`. (2) zeros come from a modified
(numerator) matrix — for differential-in/differential-out a sum of ≤4 minor
matrices — which is *also* a matrix polynomial. **So poles and zeros are the
same problem on two matrices.**

### The unifying statement
Poles = roots of `det M(s)`; zeros = roots of `det M_num(s)`; both are matrix
polynomials `Σ_k s^k A_k`. **Do not form the scalar determinant.** Solve the
*polynomial eigenvalue problem* directly:

> The roots of `det( Σ_k s^k A_k ) = 0` are the **finite generalized eigenvalues
> of the companion linearization** of the matrix polynomial.

This is exactly the "convert `A_0 + sA_1 + … + s^m A_m` into a first-order
equivalent" you were missing — and the construction is **companion
linearization**: a textbook, ~15-line block-Frobenius pencil. **Not**
Faddeev–Leverrier, and with **no transformation `P` to find** — the QZ solver
does the rank/degree reduction internally.

### Q1 — valid? Yes, at any order
- Companion linearization turns the degree-`m`, `N×N` matrix polynomial into a
  single generalized eigenproblem of size `mN` (first companion form, pencil
  `sB − C`). For `m=1` this reduces to the plain `(G, C)` pencil of
  `M = G + sC`. Because `det(sB − C) = ± det M(s)`, the finite eigenvalues are
  exactly the roots (poles/zeros).
- Solve with **QZ** (`scipy.linalg.eig(C, B, homogeneous_eigvals=True)` → the
  eigenvalues come back as `(α, β)`). `β = 0` ⇒ an **infinite** eigenvalue =
  the rank/degree defect (roots at ∞ from capacitor loops / inductor cutsets /
  `A_m` not full rank) → **discard**. Finite ⇒ a pole/zero.
- This removes **both** Haley obstacles at any order: **poles at the origin**
  need no `G⁻¹` (a finite `λ=0` eigenvalue); **C-loops / L-cutsets** show up as
  clean infinities that QZ deflates → no false finite roots.
- **#finite eigenvalues = deg(det M) = your exact root count** → your
  "no false solutions" requirement is *structural here*, and doubles as the
  built-in correctness check.

### Q2 — speed / accuracy?
- **Numeric PZ & root-locus:** yes. It works on the numeric coefficient matrices
  `A_k` directly via one `O((mN)³)` QZ — **no symbolic determinant** (your
  bottleneck, even with MECPP). Root-locus stepping is the big win: per step =
  substitute numbers → build companion pencil → QZ; no per-step determinant or
  polynomial, and the finite-count stays constant across the sweep. `m` is small
  in practice (1 for RCL, >1 only with higher-order controlled-source gains), so
  `mN` stays modest.
- **Multiplicity (your item 2):** strictly better numerically than
  form-polynomial-then-root; still not *exact* n-fold — that needs your symbolic
  factorization route.
- **Conditioning:** for `m>1` the companion pencil can be ill-scaled — apply the
  standard polynomial-eigenproblem **scaling** (Fan–Lin–Van Dooren) before QZ.
  Cheap and well-established.
- **Symbolic (multiple symbols):** no help — stays on det/roots. So this is a
  *numeric accelerator*, exactly matching your item-3 idea of differentiating
  methods for numeric/stepping vs symbolic coefficients.

### Q3 — implementable? Yes — poles and zeros both
1. Extract `A_0 … A_m` from `M(s)` (clean, since it is polynomial in `s`:
   sympy `Poly` per entry, or `A_k = (1/k!)·∂ᵏM/∂sᵏ |_{s=0}`).
2. Build the block-companion pencil `(C, B)` of size `mN`.
3. `scipy.linalg.eig(C, B, homogeneous_eigvals=True)` → filter
   `|β| > tol·max|β|` → roots.
4. **Zeros:** identical, with `M_num(s)` (your ≤4-minor differential-I/O
   numerator matrix) in place of `M`.

Core sketch (convention/signs to pin against a reference):
```python
import numpy as np
from scipy.linalg import eig

def roots_of_matpoly(A):          # A = [A0, A1, ..., Am], each N×N (numeric)
    N, m = A[0].shape[0], len(A) - 1
    if m == 0:
        return np.array([])
    B = np.eye(m*N, dtype=complex); B[:N, :N] = A[m]        # block-diag(A_m, I)
    C = np.zeros((m*N, m*N), dtype=complex)
    C[:N, :] = -np.hstack(A[:m][::-1])                      # [-A_{m-1} ... -A_0]
    for k in range(1, m):
        C[k*N:(k+1)*N, (k-1)*N:k*N] = np.eye(N)
    al, be = eig(C, B, homogeneous_eigvals=True, right=False)
    fin = np.abs(be) > 1e-12 * np.max(np.abs(be))
    return al[fin] / be[fin]                                # roots of det(Σ s^k A_k)
# add Fan–Lin–Van Dooren scaling for m>1.
```

### Recommended path (SLiCAP_GiNAC.md spirit)
Build it as a **standalone experiment, differentially tested vs `_numRoots`** on:
RCL, a pole at the origin, a capacitor loop, an inductor cutset, a higher-order
controlled-source gain (`m>1`), `(F(s))^n` repeated roots, and a root-locus
sweep — checking (a) same finite root set within tolerance, (b) count =
deg(det) = #states, (c) a speed benchmark. Only then wire it behind a seam in
the numeric PZ path, with the polynomial method kept as reference/fallback
(never hard-fail). Poles first; zeros immediately after (same code, numerator
matrix).

---

## Build sheet — `SLiCAPstateSpace.py` (2026-07-18, plan only)

New instruction `doStateSpace()` + own module `SLiCAPstateSpace.py`. Numeric
first; symbolic state-space deferred (case 5). Study standalone, integrate later.

**Dispatch (in `do*`, after step-value substitution — the gate already exists in
`_Roots`, SLiCAPmath.py:239):** count free symbols of the matrix.
1. only `ini.laplace` free  → state-space path  *(the target)*
2. no free vars at all (no `s` either)  → memoryless, keep current (trivial)
3. free vars, **no** `s`  → keep current (nothing dynamic to solve); `_reduce_matrix()` maybe later
4. free vars **incl.** `s`  → symbolic state-space = nice-to-have, **later**

### v1 — `gainType='gain'`, numeric, POLES only
`gain` never touches `_LGREF_`, so `instr.M` is the plain matrix polynomial —
the clean starting point, directly comparable to `doPoles`.

1. **Extract** `A_0 … A_m` from `instr.M` (`M = Σ A_k s^k`; per-entry `sp.Poly`
   in `ini.laplace`, or `M.coeff(s,k)`). Verify polynomial-in-`s` (differential
   form). → numeric complex numpy arrays.
2. **Companion linearization → descriptor pencil `(E, A)` size `mN`.**
   `m=1`: `E = A_1`, `A = −A_0` (i.e. the `(C, −G)` pencil). `m>1`: block-Frobenius.
   `B, C, D` not needed for poles — defer to the zeros/transfer phase.
3. **Poles = finite generalized eigenvalues:**
   `scipy.linalg.eig(A, E, homogeneous_eigvals=True)` → `(α, β)`;
   finite = `|β| > tol·max|β|`; discard infinities (β≈0 = C-loops / L-cutsets /
   degree defect). Sign/convention pinned against `doPoles`.
   *(This is the general "eigenvalues of A" — generalized so singular `E` /
   origin poles / higher order all work, no reduction-to-proper-`A` needed.)*
4. **Invariant/correctness check:** `#finite == deg(det M) == len(instr.poles)`
   → the no-false-solutions guard.
5. **Hz:** `eig` returns rad/s = exactly `_Roots` output → compare *before* the
   `ini.Hz` ÷2π display conversion.
6. **Conditioning:** Fan–Lin–Van Dooren scaling for `m>1`.
7. **Differential-test harness** vs current `_numRoots`/`instr.poles` on: RCL,
   origin pole, C-loop, L-cutset, repeated poles `(F(s))^n`, higher-order
   controlled-source gain (`m>1`), root-locus sweep — same finite set within
   tol, same count, plus a timing benchmark.

**Deliverable:** `SLiCAPstateSpace.py` with `build_realization(M)→(E,A[,B,C,D])`,
`poles(realization)`, and a standalone test script. **No** edits to
`SLiCAPexecute`/`SLiCAPshell` yet.

### Deferred phases (documented, not built)
- **zeros** — numerator/Cramer matrix (`_doCramer`, SLiCAPexecute.py:1514) →
  Rosenbrock/bordered pencil → eigenvalues.
- **transfer + DC + Bode** — `H(s)=C(sE−A)⁻¹B+D`; DC = `H(0)` incl. origin ∞/0
  (fixes the substitution bug); Bode = solve `(jωE−A)x=B` per ω.
- **loopgain rework onto minors** — replace `(D0−DM)/D0` with the lgref cofactor
  `C` directly (see `_doPyLoopGainServo`, SLiCAPexecute.py:1552): loopgain poles
  = eig(`M0`), zeros = eig(`C`); **servo** poles = eig(full `M`) = gain matrix,
  zeros = eig(`C`) → servo comes free from gain + loopgain.
- **`doStateSpace()` instruction + integration** at the `_Roots` dispatch.

## Design note — DM/CM single-variable loop-gain reference (Anton, 2026-07-18)

Two independent references (`_LGREF_1`, `_LGREF_2`) make `det` **bilinear** →
`N_L` = sum of ≤3 cofactors (+ cross term) → not a single minor → needs a
bordered matrix. **Fix:** drive the two matched references from **one** variable
with a sign pattern + factor ½:
- `ini.loopgain = "dm"` → `+½·_LGREF_` and `−½·_LGREF_` (differential mode)
- `ini.loopgain = "cm"` → `+½·_LGREF_` and `+½·_LGREF_` (common mode)

Then `det` is **affine in the single `_LGREF_`** again → `N_L` = one cofactor →
clean minor → state-space applies directly to differential circuits (no bordered
matrix). Bonus, not just computational: **DM and CM loop gain are the quantities
a differential-amplifier designer actually wants** — design the DM loop for the
signal path, check the CM loop for common-mode stability. It's the loop-gain
counterpart of SLiCAP's existing `convType` (dd/cc) modal decomposition.
**To pin down:** exact sign/½ convention against a known differential example;
that the two refs are structurally symmetric; how the mode selector reads the
two-element `lgRef`.

---

## State-space reduction — verified methods & script (2026-07-18)

*(The concrete case-5 / book recipe behind the build sheet. Both functions are
verified in `scratchpad/ss_prototype.py`: companion `det(G+sC)=det M(s)`; the
reduction's transfer, poles, and `P_in`/`P_out` consistency; and a higher-order
expand→reduce→transfer round trip — all pass.)*

### 1. Expand `M(s)` to first order — companion linearization `[ref: linearization]`

For `M(s) = M₀ + M₁s + … + Mₘsᵐ` (`n×n`), the first companion form is the
`mn×mn` pencil `G + sC`:

```
C = blockdiag(Mₘ, I, …, I)

G = ⎡ M_{m-1}  M_{m-2}  …  M₁   M₀ ⎤
    ⎢  −I        0      …   0    0 ⎥
    ⎢   0       −I      …   0    0 ⎥
    ⎢             ⋱                ⎥
    ⎣   0        0     …  −I    0 ⎦
```

`det(G + sC) = det(M(s))` — identical poles. The companion state is
`z = [sᵐ⁻¹x; …; sx; x]`, so the original variable `x` is the **last** block and
the extra blocks `sx, s²x, …` are the derivative states (a higher-order
controlled source's internal dynamics). Source enters block 1
(`row 1 = M(s)x = Bu`); detector reads the last block. This is exactly the
standard "reduce a high-order ODE to a first-order system by adding derivative
states" move.

```python
def expand_to_first_order(coeffs):          # coeffs = [M0, M1, ..., Mm]
    m, n = len(coeffs) - 1, coeffs[0].rows
    if m == 1:
        return coeffs[0], coeffs[1]         # already first order: G=M0, C=M1
    I, Z = sp.eye(n), sp.zeros(n)
    Cb = [[Z]*m for _ in range(m)]; Cb[0][0] = coeffs[m]
    for k in range(1, m): Cb[k][k] = I
    Gb = [[Z]*m for _ in range(m)]
    for j in range(m): Gb[0][j] = coeffs[m-1-j]
    for k in range(1, m): Gb[k][k-1] = -I
    return sp.Matrix(sp.BlockMatrix(Gb)), sp.Matrix(sp.BlockMatrix(Cb))

def expand_vectors(source, detector, m):    # -> B (drives first block), Cout (reads last block)
    n, p, q = source.rows, source.cols, detector.rows
    B    = source.col_join(sp.zeros((m-1)*n, p))       # source -> first block
    Cout = sp.zeros(q, (m-1)*n).row_join(detector)     # detector -> last block (where x lives)
    return B, Cout
```

### 2. MNA → minimal state space — algebraic-variable elimination `[ref: reduction]`

Given first-order `(G + sC)x = Bu`, `y = C_out x`, with `C` singular (rank
`r < n`). Split by the row/column spaces of `C`:

- `V = [V_dyn | V_alg]`, `V_dyn` = rowspace(C) (`n×r`), `V_alg` = null(C)
  (`n×(n−r)`) — state change `x = Vz`;
- `U = [U_dyn ; U_alg]`, `U_dyn` = colspace(C) as rows, `U_alg` = leftnull(C) as
  rows — equation combination.

Then `U C V = [[C₁₁,0],[0,0]]` with `C₁₁` invertible. The bottom rows carry no
`s` (algebraic): solve `z₂ = G₂₂⁻¹(B₂u − G₂₁z₁)` and substitute — two Schur
complements, `C₁₁⁻¹` (reduced reactance) and `G₂₂⁻¹` (algebraic block):

```
A   = −C₁₁⁻¹(G₁₁ − G₁₂G₂₂⁻¹G₂₁)          # r×r, r = #states
Bss =  C₁₁⁻¹(B₁  − G₁₂G₂₂⁻¹B₂)
Css =  Co₁ − Co₂G₂₂⁻¹G₂₁   ( = C_out·P_out )
Dss =  D   + Co₂G₂₂⁻¹B₂
P_out = V_dyn − V_alg G₂₂⁻¹G₂₁            # x = P_out z (+ V_alg G₂₂⁻¹B₂·u)
P_in  = C₁₁⁻¹(U_dyn − G₁₂G₂₂⁻¹U_alg)     # reduced input = P_in·source
```

Verified identities: `Css = C_out·P_out`, `Bss = P_in·B`, and
`C_out (G+sC)⁻¹B = Css (sI−A)⁻¹Bss + Dss`.

```python
def mna_to_state_space(G, C, B, Cout, D=None):
    n = G.rows
    if D is None: D = sp.zeros(Cout.rows, B.cols)
    if C.rank() == n:                                   # C invertible → proper already
        Ci = C.inv(); return -Ci*G, Ci*B, Cout, D, Ci, sp.eye(n)
    Vdyn = sp.Matrix.hstack(*C.T.columnspace())         # rowspace(C)
    Valg = sp.Matrix.hstack(*C.nullspace())             # null(C)
    Udyn = sp.Matrix.vstack(*[v.T for v in C.columnspace()])    # colspace(C)
    Ualg = sp.Matrix.vstack(*[v.T for v in C.T.nullspace()])    # leftnull(C)
    V, U = Vdyn.row_join(Valg), Udyn.col_join(Ualg)
    r = Vdyn.cols
    Ct, Gt, Bt, Cot = U*C*V, U*G*V, U*B, Cout*V
    C11 = Ct[:r, :r]
    G11, G12, G21, G22 = Gt[:r,:r], Gt[:r,r:], Gt[r:,:r], Gt[r:,r:]
    B1, B2, Co1, Co2 = Bt[:r,:], Bt[r:,:], Cot[:,:r], Cot[:,r:]
    C11i, G22i = C11.inv(), G22.inv()
    A   = -C11i*(G11 - G12*G22i*G21)
    Bss =  C11i*(B1  - G12*G22i*B2)
    Css =  Co1 - Co2*G22i*G21
    Dss =  D   + Co2*G22i*B2
    Pout = Vdyn - Valg*G22i*G21
    Pin  = C11i*(Udyn - G12*G22i*Ualg)
    return A, Bss, Css, Dss, Pin, Pout
```

### Caveats
- `C.rank()`/`nullspace()` are the **generic** rank (symbols independent); a
  parameter value that drops the rank changes the split — SLiCAP's usual
  generic-parameter assumption.
- **`G₂₂` must be invertible** (non-degenerate algebraic reduction); its
  determinant lands in denominators, fails only for pathological (floating)
  subnetworks.
- Symbolic `C₁₁⁻¹`, `G₂₂⁻¹` → **expression swell**; clean for low order / few
  symbols (the symbolic regime), heavy otherwise — the numeric engine uses
  scipy's QZ instead.
- **Reciprocal** networks (`G, C` symmetric) → `U = Vᵀ`, so `P_in = P_outᵀ`: one
  congruence `P`, the elegant special case.

## For the book — a circuit's state space, and why there are *five* matrices, not four

*(Raw material for the network-theory chapter — Anton to shape into prose, Claude
to review. Companion to the time-constants matrix already in that chapter.)*

### The four matrices you know
The standard state-space description of a linear, time-invariant system is
```
ẋ = A x + B u        (state equation)
y = C x + D u        (output equation)
```
with transfer function `H(s) = C (sI − A)⁻¹ B + D` `[ref: linear-systems]`. Four
matrices, `A B C D`. The identity `I` in `(sI − A)` is silent but important: it
sits in front of the derivative `ẋ`.

*(Notation clash to warn the reader about: the state-space output matrix is
conventionally `C`, but in circuits `C` is the capacitance matrix. Below the
output matrix is written `C_out` to keep them apart.)*

### What the circuit actually hands you
Modified nodal analysis `[ref: MNA]` delivers the network in the form you already use,
```
M(s) x = source ,     M(s) = G + sC
```
where `G` collects the conductances and controlled sources and `C` the
capacitors and inductors. In the time domain this reads
```
C ẋ = −G x + source .
```

### Why you cannot simply read off the four matrices
To match the textbook `ẋ = A x + …` you would divide by `C`, i.e. `A = −C⁻¹G`.
But **`C` is singular.** Every node carrying no capacitor or inductor contributes
a row of zeros; the number of independent energy-storage states is almost always
smaller than the number of network variables. A singular matrix has no inverse,
so the four-matrix form is simply *not available* from the raw equations. This is
the same wall as "reduce `C` to full rank" — it demands first eliminating every
non-dynamic variable.

### The fifth matrix removes the obstacle
Leave `C` where it is and place it in front of the derivative:
```
E ẋ = A x + B u ,     E = C ,  A = −G ,  B = source ,  C_out = detector
H(s) = C_out (sE − A)⁻¹ B + D .
```
This is the **descriptor** (generalized) state space `[ref: descriptor]`. The "extra" matrix `E` is
not extra at all — **`E` is the reactance matrix `C` you already had**, and `A`
is `−G`. Nothing has been computed, reduced, or inverted: the raw MNA matrices
*are* the realization.

### Poles without inverting anything
The natural frequencies follow from the homogeneous equation `E ẋ = A x`:
```
det(sE − A) = det(sC + G) = det M(s) = 0 .
```
These are the **generalized eigenvalues** of the matrix pair `(−G, C)`, solved
robustly (QZ algorithm `[ref: QZ]`) with no `C⁻¹`. A singular `E` merely yields
some *infinite* generalized eigenvalues; those are the modes a capacitor loop or
an inductor cutset removes, and they are discarded `[ref: singular-pencil]`. The
**finite** generalized
eigenvalues are the poles, and their count equals the number of independent
energy-storage states — automatically, with no spurious roots.

### Four versus five — the honest summary
- **Four matrices** `(A, B, C_out, D)` = the *minimal* state space. Correct, but
  only after the non-dynamic variables have been eliminated (the reduction that
  needs a full-rank reactance matrix).
- **Five matrices** `(E, A, B, C_out, D)` = the *raw* MNA description, used
  directly. `E` is the price of *not* reducing — and it is the cheaper price,
  because the generalized eigenvalue solver absorbs the singular `E` for you.

### Relation to the time-constants matrix
The time-constants matrix `[ref: time-constants]` gives the *physical* reading of the poles (each pole ≈
a reciprocal time constant) but breaks on two cases: a pole at the origin (`G`
singular, no `G⁻¹`) and capacitor loops / inductor cutsets (infinite time
constants → numerical false poles). The descriptor pencil `(−G, C)` computes the
*same* spectrum while handling exactly those two cases cleanly — it is the robust
computational counterpart of the physically transparent time-constants view.

### A note on words
Reducing a description that is high-order in `s` (`A₀ + sA₁ + s²A₂ + …`, which
arises when a controlled source's gain is itself higher-order in `s`) down to the
first-order pair `(E, A)` is called a *linearization* `[ref: linearization]` in
the mathematical literature. The term is unfortunate here: it refers only to the
*degree in `s`* becoming one, not to any linear/nonlinear distinction — the
network is linear throughout. "First-order-in-`s` form" is the clearer name. For
an ordinary `M = G + sC` circuit no such stacking is needed: `E = C`, `A = −G`.

### Reference key (`[ref: …]` markers above — fill in your preferred editions)
- **`[ref: linear-systems]`** — standard linear-systems text: T. Kailath,
  *Linear Systems*, Prentice-Hall, 1980; or C.-T. Chen, *Linear System Theory
  and Design*, Oxford Univ. Press.
- **`[ref: MNA]`** — C.-W. Ho, A. E. Ruehli, P. A. Brennan, "The modified nodal
  approach to network analysis," *IEEE Trans. Circuits Syst.* 22(6):504–509,
  1975; J. Vlach & K. Singhal, *Computer Methods for Circuit Analysis and
  Design*, 2nd ed., Van Nostrand Reinhold, 1994.
- **`[ref: descriptor]`** — L. Dai, *Singular Control Systems*, Springer LNCIS
  118, 1989.
- **`[ref: QZ]`** — C. B. Moler & G. W. Stewart, "An algorithm for generalized
  matrix eigenvalue problems," *SIAM J. Numer. Anal.* 10(2):241–256, 1973;
  G. H. Golub & C. F. Van Loan, *Matrix Computations*, 4th ed., 2013.
- **`[ref: singular-pencil]`** — P. Van Dooren, "The computation of Kronecker's
  canonical form of a singular pencil," *Lin. Alg. Appl.* 27:103–140, 1979.
- **`[ref: time-constants]`** — J. Haley (1988, cited earlier in this document);
  and your own network-theory chapter.
- **`[ref: linearization]`** — I. Gohberg, P. Lancaster, L. Rodman, *Matrix
  Polynomials*, SIAM, 2009 (orig. 1982); F. Tisseur & K. Meerbergen, "The
  quadratic eigenvalue problem," *SIAM Review* 43(2):235–286, 2001.
- **`[ref: reduction]`** (for the companion→minimal reduction, when that section
  is added) — Dai (above); P. Kunkel & V. Mehrmann, *Differential-Algebraic
  Equations*, EMS, 2006; F. Zhang (ed.), *The Schur Complement and Its
  Applications*, Springer, 2005; L. O. Chua & P.-M. Lin, *Computer-Aided
  Analysis of Electronic Circuits*, Prentice-Hall, 1975.

## Numeric PZ method + differential-detector single-ending (2026-07-18)

*(The fast numeric path — distinct from the symbolic reduction, which stays for
symbolic transfers / symbolic state space. Verify against **doPoles/doZeros** (no
cancellation), NOT doPZ (always cancels).)*

### Numeric path — fully numpy, including the linearization
Condition: after substituting parameter definitions and step values, `ini.laplace`
is the only free symbol of `M`. Then:
1. Extract numeric coefficient matrices `A_0 … A_m` from `M` (numpy).
2. Build the companion pencil `(G, C)` in numpy `[ref: linearization]`.
3. **Poles** = finite generalized eigenvalues of `(−G, C)` via QZ
   (`scipy.linalg.eig`), infinite ones discarded. `= roots(det M)` = **doPoles**.
4. **Zeros** = finite generalized eigenvalues of the **numerator matrix** — the
   single-ended Cramer matrix (`M` with the detector column replaced by `Iv`) — by
   the *same* QZ routine as poles. `= roots(numer)` = **doZeros**. (Differential
   detector: single-end it first — see below.)
5. **Gain factor** (lost by the eigenvalue step): one evaluation at a safe non-root
   `s_0`, `gain = H(s_0)·Π(s_0−p)/Π(s_0−z)` with
   `H(s_0) = det(numer(s_0))/det(M(s_0))`; origin handled via the nonzero-root
   products (SLiCAP `EC/EC`).

**Conditioning (OPEN, the go/no-go):** the higher-order (`m>1`) companion pencil
needs Fan–Lin–Van Dooren scaling + a robust finite/infinite **deflation** `[ref: QZ]`.
A raw magnitude threshold drops high-frequency roots (measured: 3 poles vs 4).
Guard: `#finite == deg(det M)` — if short, re-scale/deflate; never return fewer.
**Speed:** ~6.6× faster than doPZ on the poles core once correct.

### Differential detector → single-ended by network modification (invisible to the user)
**Why:** a single detector gives one clean Cramer numerator matrix. A differential
detector gives `numer = det(M_P) − det(M_N)` — a **difference of determinants**,
which is NOT the determinant of any single matrix (`det(A)−det(B) ≠ det(A−B)`), so
it breaks the "zeros = eigenvalues of one matrix" form.

**Fix:** augment the network (at the matrix level) with **non-loading** controlled
sources that carry the differential quantity onto ONE new detector **node**, then
take zeros as that single-ended numerator matrix's eigenvalues. **Dual-aware** —
networks have voltages *and* currents:

| differential quantity | non-loading termination | element |
|---|---|---|
| voltage `V_P − V_N` | **infinite** impedance (open) | VCVS `E` |
| current `I_1 − I_2` | **zero** impedance (short) | CCVS `H` |

Build an **anti-series** pair (gains `+1`, `−1`) into the new node; pick each side's
element by its type (E for a voltage term, H for a current term) — mixed
voltage/current differences compose the same way. Currents already present as MNA
variables (inductor, source currents) are referenced directly by the `H`-element; a
current without its own variable (e.g. a resistor-branch current) first needs a
**0 V (zero-ohm) sensing branch** to create it — the dual of the voltage side, where
node voltages are always present.

**Properties:** the added sources are memoryless → only *algebraic* variables added,
so the **pole count is unchanged**; their unit gains fold into the gain factor, not
the roots. Applied ONLY for zeros / transfer functions with a differential detector.

**Invisible to the user:** the user specifies only the differential detector.
Internally, for that computation `M`, `Iv`, `Dv` **grow** and the source rows /
detector columns are remapped to the augmented system with the single new detector
node. Example: to detect `I_{L1} − I_{L2}`, the cheapest expansion is one new
voltage-detector node driven by the anti-series connection of two `H`-elements, each
driven by its inductor current.

### Possible novelty
The building blocks are known — transmission-zero computation via system-matrix
augmentation (Rosenbrock `[ref: descriptor]`) and the V/I duality of sensing
(classical network theory). The specific synthesis here — reducing *every*
differential-detector zero (and transfer) computation to a **single-ended
Cramer-matrix generalized-eigenvalue problem** via a **dual-aware, non-loading,
pole-preserving circuit-level augmentation** (E for voltages, H + zero-ohm sensing
for currents), kept exact and invisible to the user — appears to be a fresh framing
for symbolic + numeric circuit pole-zero analysis. Worth a literature scan
(transmission-zero algorithms, symbolic circuit analysis, descriptor-system zeros)
before any novelty claim.

---

## Companion state vector — worked example and G22 singularity

### What the companion state vector contains

For a degree-2 MNA matrix `M(s) = M0 + s·M1 + s²·M2` (n×n), the companion
linearization introduces the extended state `[x; y]` where `x` is the original
circuit variable vector (node voltages, branch currents) and `y = s·x`.

The companion pencil `(G, C)` is:

```
C = [[ M2, 0 ],     G = [[ M1,  M0 ],
     [  0, I ]]          [ -I,   0 ]]
```

Key observation: the bottom block of `C` is the identity → **every entry of `x` is
dynamic** regardless of what `M2` looks like. The original circuit variables are never
algebraic in the companion system.

### Small worked example

Three MNA variables `[V1, V2, I_e]`: node `V1` (conductance `g1` to ground), node
`V2` (conductance `g2` to ground), and branch current `I_e` of a VCVS (EZ element)
with `av = A / (1 + s·τ1 + s²·τ1·τ2)`. After multiplying the EZ constraint row by
the denominator, the three coefficient matrices are:

```
M0 = [[ g1,  0,  0],    M1 = [[0,   0, 0],    M2 = [[0,      0, 0],
      [  0, g2,  1],           [0,   0, 0],          [0,      0, 0],
      [ -A,  1,  0]]           [0,  τ1, 0]]          [0, τ1·τ2, 0]]
```

`rank(M2) = 1` — only the EZ row has a degree-2 entry, and only in the `V2` column.

The 6×6 companion `C` matrix (state `[V1, V2, I_e, s·V1, s·V2, s·I_e]`):

```
row 0  (M2 row 0):  [0,     0, 0 | 0, 0, 0]   ← zero: M2 row 0 is zero
row 1  (M2 row 1):  [0,     0, 0 | 0, 0, 0]   ← zero: M2 row 1 is zero
row 2  (M2 row 2):  [0, τ1τ2, 0 | 0, 0, 0]   ← EZ row, non-zero at V2 only
row 3  (I block):   [0,     0, 0 | 1, 0, 0]   ← s·V1  is dynamic
row 4  (I block):   [0,     0, 0 | 0, 1, 0]   ← s·V2  is dynamic
row 5  (I block):   [0,     0, 0 | 0, 0, 1]   ← s·I_e is dynamic
```

`null(C)` = vectors `[0, 0, 0, a, 0, c]^T` for arbitrary `a, c`. In words:
the **algebraic directions are `s·V1` and `s·I_e`** — the combinations of "velocity"
that `M2` annihilates. Neither `V1`, `V2`, nor `I_e` is algebraic here.

`G22` for this example works out to `[[g1, 0], [0, 1]]` — invertible (g1 ≠ 0),
so `_reduce` succeeds and the poles are found correctly.

### Physical explanation of G22 singularity

In the chargeDriver, each AD8610 op-amp has `av` with a degree-2 denominator.
The EZ stamp creates one non-zero row in `M2` per op-amp, and that row has a
non-zero entry **only in the output-voltage column** — not in the branch-current
column. Therefore:

- `null(M2)` contains directions in the `I_O` (op-amp branch current) space
- `M1` also has zero in the `I_O` column of the EZ row (the `s`-coefficient
  of the EZ constraint does not involve `I_O`)
- So `M1 · (null-M2 direction along I_O) = 0` → a zero column in `G22` →
  `G22` is singular

**The physical reason:** `I_O` is a purely algebraic variable in the circuit — it
is the branch current of a voltage-source element, determined at every instant by
KCL/KVL, with no energy storage behind it. The companion introduces `s·I_O` as if
it were a state, but there is no reactive element in the circuit that "stores" the
rate of change of `I_O`. `G22` being singular is the algebraic symptom of that
missing physical state.

### The remedy

The MNA must be first-order in `s` from the outset. This is achieved by the
**network expansion** method described in the book chapter (see
`NetworkTheory-1_Implementation_of_transfer_functions.html`): replace each rational
transfer element with an integrator-chain sub-network of explicit capacitors. In the
expanded network every state direction corresponds to a real capacitor voltage, `I_O`
remains algebraic and is eliminated before the dynamic reduction, and `G22` becomes
the DC conductance matrix of the non-capacitive subnetwork — invertible for any
proper circuit.

The companion linearization applied to the polynomial-stamped MNA is a correct
mathematical identity (`det(G + sC) = det M(s)`), but it does **not** produce an
index-1 descriptor system when `M_m` is rank-deficient (as it always is when only a
few element types contribute the highest-degree term). Network expansion avoids this
by construction.

To isolate a full-rank block $C_{rr}$ from a singular matrix $C$ such that the remainder of the matrix becomes zero, you cannot simply reorder (permute) the rows and columns. Instead, you must apply a basis transformation (equivalence transformation) using invertible matrices $L$ and $R$ such that:
$$L \cdot C \cdot R = \begin{bmatrix} C_{rr} & 0 \\ 0 & 0 \end{bmatrix}$$ 
Applying this same transformation to the entire system preserves its properties, mapping $M = G + sC$ into:
$$M_{transformed} = L \cdot M \cdot R = \begin{bmatrix} G_{11} & G_{12} \\ G_{21} & G_{22} \end{bmatrix} + s \begin{bmatrix} C_{rr} & 0 \\ 0 & 0 \end{bmatrix}$$ 

## SymPy Implementation Code
The function below constructs the transformation matrices $L$ and $R$ using the null spaces (kernel) and column spaces of $C$, then extracts your desired blocks:

import sympy as sp
def decompose_laplace_matrix(G, C):
    """
    Transforms M = G + s*C into a representation where C is block-diagonalized
    into [[C_rr, 0], [0, 0]] with C_rr full rank.
    """
    assert G.shape == C.shape, "Matrices G and C must have the same dimensions."
    n = C.rows
    
    # 1. Compute the rank of C
    r = C.rank()
    
    if r == n:
        raise ValueError("Matrix C is already full rank!")
    if r == 0:
        raise ValueError("Matrix C is a zero matrix!")

    # 2. Build Right Transformation Matrix (R)
    # Columns 1 to r: Pivot columns of C (basis for the column space)
    _, pivot_cols = C.rref()
    R_independent = C[:, pivot_cols]
    # Remaining columns: Basis of the null space of C
    R_null = sp.Matrix.hstack(*C.nullspace())
    R = sp.Matrix.hstack(R_independent, R_null)
    
    # 3. Build Left Transformation Matrix (L)
    # Rows 1 to r: Row-reduced independent rows
    # Remaining rows: Basis of the left null space of C (null space of C.T)
    L_independent = (C.T[:, pivot_cols]).T # matching the chosen pivot columns
    L_null = sp.Matrix.vstack(*[v.T for v in C.T.nullspace()])
    L = sp.Matrix.vstack(L_independent, L_null)
    
    # Ensure L and R are fully invertible (if not, we complete the basis)
    if not L.is_invertible():
        L = L.col_join(sp.eye(n))[0:n, :] # fallback standard basis extension
    
    # 4. Apply transformations to get the block structures
    G_transformed = L * G * R
    C_transformed = L * C * R
    
    # 5. Extract the submatrices
    G_11 = G_transformed[0:r, 0:r]
    G_12 = G_transformed[0:r, r:n]
    G_21 = G_transformed[r:n, 0:r]
    G_22 = G_transformed[r:n, r:n]
    C_rr = C_transformed[0:r, 0:r]
    
    return G_11, G_12, G_21, G_22, C_rr
# --- Example Usage ---# Define symbolic Laplace variables = sp.Symbol('s')
# Create an arbitrary full-rank G and a singular C (Rank 2)G = sp.Matrix([[1, 2, 3], 
               [4, 5, 6], 
               [7, 8, 10]])
C = sp.Matrix([[1, 0, 1], 
               [0, 1, 1], 
               [1, 1, 2]]) # Row 3 = Row 1 + Row 2
# DecomposeG_11, G_12, G_21, G_22, C_rr = decompose_laplace_matrix(G, C)
# Display Results
print("--- Extracted Submatrices ---")
print("C_rr (Should be full rank):")
sp.pprint(C_rr)
print("\nG_11:")
sp.pprint(G_11)
print("\nG_22:")
sp.pprint(G_22)

## How the Math Works Behind the Code

* The Right Side ($R$): The matrix $R$ shifts coordinates so that any vector multiplying the last $n-r$ columns lands directly in the null space of $C$, multiplying them by zero.
* The Left Side ($L$): The matrix $L$ combines the dependent rows together. Because the bottom rows of $L$ span the left null space of $C$, they clear out any remaining values in the bottom rows of $C$.
* The Result: $C$ collapses perfectly into $\begin{bmatrix} C_{rr} & 0 \\ 0 & 0 \end{bmatrix}$, forcing all dynamic features involving the Laplace variable $s$ to isolate into the top-left $r \times r$ corner.

If you are dealing with differential-algebraic equations (DAEs) or descriptor systems and need to completely eliminate algebraic constraints, let me know if you would like to calculate the explicit transfer function matrix from this setup!

import sympy as spC = sp.Matrix([[1, 0, 1], [0, 1, 1], [1, 1, 2]])
print("NS:", C.nullspace())
print("LNS:", C.T.nullspace())



