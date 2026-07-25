# SLiCAP determinant in C++/GiNaC — benchmark experiment

**Purpose.** Measure the true C++ ceiling of SLiCAP's own symbolic
determinant algorithms before committing to a C++ engine. This experiment
*is* the measurement that decides the engine question in ACDE.md
("Client-server direction → Fast symbolic engine"): a CLI that computes the
symbolic determinant with GiNaC, differentially tested and benchmarked
against the Python implementation on identical matrices.

**Scope — deliberately narrow.** A copy of `SLiCAP.SLiCAPmath.det()` for
methods **"ME" and "BS" only**, which includes the pieces `det()` itself
applies for those two methods:

- `_detME` — recursive first-column minor expansion with zero-skipping
  ([SLiCAPmath.py:132]).
- `_detBS` — Bareiss fraction-free elimination with pivot swap
  ([SLiCAPmath.py:148]).
- `_eliminateVars` + `_find_numeric_entry` — numeric-pivot pre-elimination
  ([SLiCAPmath.py:72]), applied by `det()` for ME/BS when
  `ini.reduce_matrix` is set.
- `float2rational` analog — CLN exact rationals are GiNaC's native
  arithmetic; input floats are rationalized before computing.

No FC method, no sympy built-in fallbacks, no other SLiCAP functions.

**Status: BUILT AND MEASURED (2026-07-13)** — see "Results" below. Code in
`ginac_det/` (repo root, outside the SLiCAP package): `det_cli.cpp`,
`Makefile`, `harness.py`, `results.json`. Rerun:
`cd ginac_det && make && /home/anton/anton/bin/python harness.py`.

**Regime insight (Anton, 2026-07-13) — encoded in the fixture set:** in
network theory the matrices are sparse and **simplification is the dominant
cost**, so minor expansion — "slow" in general-purpose symbolic math — wins
here; division-free and Gaussian-style eliminations lose because a readable
expression is required at the end. `_eliminateVars` is effective when there
is a lot of numeric input combined with the Laplace variable. The harness
therefore benchmarks each circuit in two regimes: fully **symbolic** (sparse,
ME's home turf) and **numeric + Laplace** (`pardefs='circuit',
numeric=True`, the `_eliminateVars` regime).

---

## Prior work (2023, previous computer): `/home/anton/DATA/SLiCAP/GiNaC/`

- **`det.cpp`** (Sep 2023) — ME is already ported: `minor_matrix` +
  `laplace_expansion` (zero-skipping, `expand()` per level, final
  `normal()`), i.e. `_detME` + the `dim<=2` base cases of `det()`. Three
  hardcoded test matrices from real SLiCAP circuits: M1 7×7 fully symbolic,
  M2 52×52 semi-numeric (floats + `s`), M3 27×27 semi-numeric. Per-matrix
  `clock()` timing.
- **`det2.cpp`, `det_cw.cpp`** — earlier variants (reference only).
- **`run`** — the build recipe:
  `g++ -o det.exe det.cpp $(pkg-config --cflags --libs ginac)`.
- **`matrixtest.txt`** — the same matrices in Maxima syntax (cross-check
  material).
- **`flexBison/`** — an expression-tokenizer trial; superseded: GiNaC's
  built-in `parser` with a symtab does the job.

Reused: the ME port skeleton, the build recipe, the test matrices (as
initial fixtures). New in this round: BS, pre-elimination, rationalization
(the 2023 matrices compute on floats), and — the main addition — **text
I/O instead of hardcoded matrices**, so the harness can feed arbitrary
matrices from live SLiCAP.

---

## Deliverables

### 1. C++ CLI: `slicap_det`

```
slicap_det [--method ME|BS] [--no-reduce] [--timing] < matrix.txt
```

- Reads a matrix (stdin or file), computes the symbolic determinant with a
  faithful copy of the Python algorithms, prints the expression on stdout.
- `--no-reduce` skips `_eliminateVars` (to time the pre-elimination's
  contribution separately).
- `--timing` reports **parse, compute, and print times separately** (JSON
  on stderr). Only the compute time enters the speedup comparison — the
  text round-trip will not exist in a later pybind11 integration.

### 2. I/O contract (also a first prototype of the engine-seam serialization)

Input (text): line 1 = dimension `n`; then `n²` entries, row-major, one per
line, in sympy `str()` syntax.

- Harness converts `**` → `^` on export; GiNaC parser symtab auto-creates
  symbols and maps `pi` → `Pi` (and `I` → GiNaC `I`, defensively — MNA
  entries are real rational functions in practice).
- Floats are rationalized **on the Python side before export**
  (`float2rational`), so both implementations compute on *identical* exact
  input — otherwise speed and correctness comparisons are polluted.
- Output: GiNaC's default print; the Python side parses it with
  `parse_expr(..., transformations=(..., convert_xor))` so `^` is accepted
  directly.

### 3. Python harness

- **Fixtures:** MNA matrices from real circuits via `_makeMatrices` on the
  example/manual projects — a size range, both fully symbolic and
  numeric-with-`s`; plus the three 2023 matrices as smoke tests.
- **Differential test (correctness):** `sp.simplify(D_cpp - D_py) == 0`
  for every fixture × {ME, BS} × {reduce, no-reduce}. **Never string
  comparison** — GiNaC's `normal()` shapes results differently from sympy
  while being mathematically identical.
- **Benchmark:** compute-time scaling curve (per matrix size), C++ vs
  Python `det()` on the same machine and matrices; ME vs BS; with/without
  pre-elimination.

---

## Algorithm port map (sympy → GiNaC)

| Python (SLiCAPmath) | GiNaC |
|---|---|
| `sp.expand(e)` | `e.expand()` |
| `sp.factor(a/b)` in `_detBS` (exact Bareiss division) | exact polynomial division: `divide()` (fallback `normal()`) |
| final `sp.simplify(D)` in `_detBS` | `normal(D)` (rational normal form) |
| `sp.Rational` / `float2rational` | CLN exact rationals (`cl_RA`); rationalize parsed floats |
| `M.minor_submatrix(r, c)` | `minor_matrix()` from det.cpp (2023) |
| `e.is_number` in `_find_numeric_entry` | "contains no `symbol`" helper — **note:** sympy's `is_number` is true for `2*pi`; the helper must match that (treat `Pi` as numeric), not `is_a<numeric>` |
| `e.is_zero` / `!= 0` | `e.is_zero()` |

Estimated size: ~150 lines algorithms (ME half exists) + ~150 lines
parse/print/timing + Makefile; harness ~150 lines Python.

---

## Benchmark protocol & decision criterion

1. Correctness first: all differential tests green before any timing is
   quoted.
2. Time **compute only** (internal clocks), median of repeated runs;
   record the scaling curve, not a single point.
3. Interpret per the ACDE.md plan:
   - **Large speedup (order ≥10×) on the dominant sizes** → the sympy
     expression arithmetic is confirmed as the constant-factor bottleneck;
     proceed toward the engine behind the `det()`/ILT/roots seam (pybind11,
     per-dataType migration, Python stays the reference implementation).
   - **Small speedup (≲2–3×)** → the time is going elsewhere (`simplify`,
     `sp.Poly` conversions, expression printing, …); profile the chain
     before writing any more C++.
   - Either way the I/O layer survives as the first engine-seam
     serialization prototype.

## Results (2026-07-13)

**Correctness: 32/32 cases mathematically identical** to Python `det()`
(8 circuits from `docs/cir` × {symbolic, numeric+s} × {ME, BS}, verified by
exact `expand`/`cancel` of the difference — after fixing a harness
round-trip bug: GiNaC prints π as `Pi`, which `sympify` must map back to
`sp.pi` or verification falsely fails with numerically identical results).

**Speed (compute time only, CLI-internal clock, GiNaC 1.8.7, -O2):**

| case (selected) | dim | Python | C++ | speedup |
|---|---|---|---|---|
| balancedAmp symbolic, ME | 12 | 0.47 s | 6.5 ms | 73× |
| BJTdiffAmp symbolic, ME | 14 | 0.17 s | 2.4 ms | 70× |
| VampQ symbolic, ME | 10 | 0.13 s | 1.9 ms | 68× |
| pzNetwork symbolic, ME | 9 | 15 ms | 0.1 ms | 103× |
| VampQ symbolic, BS | 10 | 66 s | 1.2 s | 55× |
| balancedAmp numeric, BS | 12 | 0.46 s | 2.5 ms | 185× |
| BJTdiffAmp numeric, ME | 14 | 6.7 ms | 2.9 ms | 2× |

Full data: `ginac_det/results.json`. Ranges: ME 2–123×, BS 6–185×.

**Interpretation (per the decision criterion below):**

1. **The engine question is answered: well above the ≥10× threshold.**
   On fully symbolic matrices — the regime that hurts in daily SLiCAP use —
   ME runs at a consistent **~70–120×**; sympy's pure-Python expression
   arithmetic is confirmed as a constant-factor bottleneck that GiNaC
   removes wholesale.
2. **Anton's regime insight is confirmed in both languages.** ME beats BS
   by orders of magnitude on sparse symbolic network matrices (VampQ
   symbolic: ME 1.9 ms vs BS 1.2 s in C++; 0.13 s vs 66 s in Python) —
   BS's cost is the simplification/exact division, and that cost does NOT
   vanish in C++ (GiNaC `normal()` is where BS's C++ time goes). The
   algorithm choice matters more than the language; the language then
   multiplies the good algorithm by ~100.
3. **Where Python is already fast, C++ gains little** (BJTdiffAmp numeric
   ME: 2×): in the numeric+Laplace regime `_eliminateVars` collapses the
   problem before expression arithmetic can dominate — consistent with the
   insight that elimination is effective exactly there. The speedup lands
   where the pain is, not where it isn't.

**Findings for the Python reference (flagged, not changed):**

- `_detBS`'s zero-pivot search loops `range(k+1, dim-1)` — it never
  inspects the LAST row, and its "singular" early return (`if m == dim-1`)
  is unreachable inside that range. A matrix needing the last row as pivot
  row would divide by zero / misbehave identically-by-design in the C++
  copy (kept verbatim for comparability). Worth a look in
  `SLiCAPmath.py:154`.

## Integration: det(method="MECPP") (built 2026-07-13)

Design decided with Anton (2026-07-13): the engine is integrated as a new
`det()` method **"MECPP"**, calling the executable via subprocess — treated
exactly like ngspice: an optional external tool.

- **Subprocess is load-bearing twice:** (a) *licensing firewall* — SLiCAP is
  MIT, GiNaC/CLN are GPL; a linked pybind11 extension would be a derived
  work, a separately built executable called at arm's length is mere
  aggregation; (b) *no Python-ABI coupling* — one binary serves any Python.
- **Configuration** rides the existing external-tool mechanism:
  `~/SLiCAP.ini [commands] slicap_det`, auto-detected via `shutil.which` at
  config (re)generation, exposed as `ini.slicap_det`, shown in `ini.dump()`.
  `make install` puts the binary in `~/.local/bin`.
- **Fallback, never failure:** `det(method="MECPP")` runs the binary if
  configured and protocol-compatible (`--version` → "slicap_det protocol
  1", checked once per process); otherwise it warns once and computes with
  the Python `"ME"` — same result, slower. SLiCAP works out of the box
  everywhere; speed is opt-in via `[math] numer/denom = MECPP`.
- **Symbol hygiene — the wire carries no user names (fixed 2026-07-13):**
  first live run (ASMPT-11/Iamp.py, loop-gain analysis) hit a GiNaC lexer
  error on the internal symbol `_LGREF_1` (leading underscore). Fix at the
  wire-format level, Python-side only: every symbol is aliased to
  `sym0, sym1, …` on export and the aliases are mapped back to the
  ORIGINAL sympy symbol objects on import — arbitrary names become
  transportable, assumptions survive exactly, and collisions are
  impossible (simultaneous xreplace). GiNaC's `Pi/E/I` map back to sympy's
  constants. Engine failures now include the CLI's first stderr line in
  the fallback warning. Regression: `test_mecpp_unlexable_symbol_names`.
- **"BS" removed** (2026-07-13, Anton): it was used nowhere in SLiCAP's
  production path (only `ini.numer`/`ini.denom`, default "ME", reach
  `det()`; "BS" appeared only in `__main__` scaffolding). `_detBS` is
  deleted; `method="BS"` redirects to `"ME"` with a one-time deprecation
  warning for compatibility. This also moots the pivot-search bug above.
- **Tests:** `tests/test_mecpp.py` — MECPP≡ME differential (incl. pi
  round-trip and symbol identity), numeric/zero edge cases, BS redirect,
  and fallback-without-binary. All pass; e2e `doLaplace` results identical
  on VampQ and balancedAmp.

### End-to-end finding: det() is no longer the doLaplace bottleneck

With MECPP active, `doLaplace` on VampQ improves only 1.0–1.3× despite the
70× faster determinant. Profile (VampQ, `_doPyLaplace`): **92% of the time
is `normalizeRational` → `coeffsTransfer` → ten `sp.simplify` calls** (~2 s
each under the profiler); both determinants are noise. Anton's thesis —
"simplification is the most time-consuming action" — measured at the
instruction level. Consequences:

- A test suite dominated by `doLaplace`-family instructions will NOT drop
  dramatically from MECPP alone; suites heavy in `doPoles/doZeros/doPZ/
  doDenom` (det-dominated) should gain much more.
- **The next optimisation target is `coeffsTransfer`'s per-coefficient
  `sp.simplify`** — candidates: a cheaper sympy normal form
  (`cancel`/`factor_terms` instead of full `simplify`), or routing the
  rational-function normalization through the same GiNaC engine
  (`normal()` is exactly this operation, at C++ speed). Measure per the
  whole-chain doctrine before choosing.

### The ultimate test (Anton, 2026-07-13): full suite, cumulative changes

`SLiCAP_python_tests/SLiCAPtest.sh`, modifications cumulative:

| step | total | saved |
|---|---|---|
| original | 630 s | — |
| ME → MECPP | 559 s | 71 s (~11% was Python det time) |
| − normalizeRational in doLaplace | 530 s | 29 s |
| − normalizeRational in all functions | 502 s | 57 s total (~9% was normalization) |

**20% overall.** Conclusions:

- The det hotspot is closed (71 s → ~0); its value grows with circuit size.
- normalizeRational costs 57 s/suite — but removing it changes the FORM of
  user-visible results, so the keepable version is **lazy normalization**
  (normalize at presentation/consumption time only, per the
  "beautify once, at the end" engine rule) and/or a **cheaper normal form**
  (`cancel`/`factor_terms`, or GiNaC `normal()` = engine round two, upper
  bound now known: 57 s).
- The remaining 502 s is a distribution, not a bottleneck: next step is a
  profile of the slowest suite scripts to rank it (ilt, roots, other
  simplify sites, HTML/LaTeX generation, plotting, ngspice runs).

**Decision (Anton, 2026-07-13): normalization moves to presentation/
consumption time.** normalizeRational originally served two purposes:
(1) numeric safety for plotting/lambdify (unnormalized exact-rational
coefficients grow too large), (2) readable transfer functions on display.
Purpose (1) already lives at the consumption seam — the plot path
normalizes for itself (`normalizeRational(sp.N(yFunc), xVar)`,
SLiCAPmath.py ~918) before its own lambdify, which is why the full suite
ran green with compute-time normalization removed. Purpose (2) becomes a
user-invoked step before the html/LaTeX/RST formatters, and the GUI will
offer normalization before displaying results (hook recorded in SLNG.md).
Compute-time normalizeRational calls stay removed (57 s/suite). Anton also
removed the last "BS" references from the test files.

### Profile of the remaining cost (ASMPT-11, 2026-07-13)

Anton's candidates: `ilt()` (confirmed) and `fullSubs()` (refuted).
cProfile of the full ASMPT-11 project (575 s under the profiler, ~200 s+
real; MECPP active):

| cost center | cum. share | mechanism |
|---|---|---|
| plotSweep → `_magFunc_f`/`_makeNumData` | ~57% | `sp.N` on whole symbolic trees (259 s) and `as_real_imag` inside evalf of `Abs(...)` — arbitrary-precision evaluation of complex expressions per plot |
| `ilt` (104 calls) | ~29% | `as_real_imag` + `rewrite(cos).simplify().trigsimp()` on residue sums whose roots AND residues are already plain complex numbers |
| matplotlib `savefig` | ~6% | irreducible rendering |
| `det` via MECPP (161 calls) | 1.7% | closed; ~59 ms/call is mostly process spawn — shrinks further only with a persistent engine, not worth it at this share |
| `fullSubs` (4164 calls) | 0.4% | not a target — but it has a latent defect: `type(x) == isinstance(...)` (SLiCAPmath.py:710) compares a type to a bool (always False), forcing a str→sympify round-trip per parameter |

**Both top costs are the same disease: symbolic-domain work on numeric
data.** Fixes are pure Python, no engine work:

1. **Plot path**: replace `sp.N(tree)` + lambdify with one `sp.Poly`
   coefficient extraction, per-coefficient floats (with scaling — this is
   where the "numbers too large" protection lives, cheaply), then numpy
   `polyval` over the frequency array. Est.: ~57% → ~0.
2. **`ilt` numeric path**: pair conjugate roots, emit
   `2·e^{σt}(Re(c)·cos(ωt) − Im(c)·sin(ωt))` directly from numeric
   residues — no `as_real_imag`, no trigsimp. Est.: ~29% → small.

Together they bound a further ~4–5× on plot/time-heavy projects.

### Built: both numeric fast paths (2026-07-13, approved by Anton)

1. **Plot path** — `_rational_coeffs_numeric()` + `_freq_response()`
   (SLiCAPmath.py): the rational function's coefficients are extracted
   once with `sp.Poly`, exactly scaled by their common largest magnitude
   (the scale cancels in num/den, so the float conversion cannot
   overflow — this is the "numbers too large" protection at coefficient
   level), then evaluated with numpy `polyval` at `2πj·f` / `j·f`.
   `_magFunc_f`, `_dB_magFunc_f`, `_phaseFunc_f`, `_delayFunc_f` all try
   this first; their former symbolic route remains as the fallback for
   non-rational expressions (delay lines) and symbolic coefficients.
2. **`ilt` numeric path** — `_ilt_numeric_simple()`: for all-simple poles
   the real time function is assembled directly from numeric residues,
   `exp(σt)·(Re c·cos ωt − Im c·sin ωt)` summed over ALL roots (conjugate
   pairs add up correctly by construction — no pairing logic, no
   `as_real_imag`, no `rewrite(cos).simplify().trigsimp()`). Spurious
   imaginary parts on real roots are chopped at 1e-10 relative to the
   root scale. Repeated poles (e.g. `integrate=True` on a function with a
   pole at 0) and non-finite float residues fall back to the former
   symbolic residue path, kept verbatim.
3. **`fullSubs`** — the always-False fast-path comparison
   (`type(x) == isinstance(...)`) removed; behavior strictly preserved
   (every value keeps the string round-trip + non-integer-rational →
   Float(15) rule).

**Verification:** `tests/test_fast_numeric.py` — the replaced
implementations are copied verbatim into the tests as references; new
paths agree to machine precision (≤3e-14) on fixtures including high-Q
pairs, pole-at-origin via `integrate`, repeated-pole fallback, huge
coefficient spread, and the symbolic/non-rational fallbacks. 25/25 green
(incl. MECPP suite).

**Live-round fixes (chargeDriver.py, Anton 2026-07-13):**

1. `phaseMargin()` calls `_phaseFunc_f` with a **scalar** frequency; the
   fast path's unconditional `np.unwrap` raised on 0-d input (the old
   code's unwrap sat in a silent try/except). Fixed: unwrap only for
   sweeps. Regression test: `test_phase_at_scalar_frequency` +
   `test_phase_margin_end_to_end`.
2. The presentation-seam normalization in `eqn2html` crashed on a Routh
   **Matrix** (`coeffsTransfer` → `as_numer_denom`). Fixed at the
   chokepoint: `normalizeRational()` returns input that is not a rational
   function of the variable unchanged — a presentation step must pass
   everything else through. `_rational_coeffs_numeric` also guards
   `is_Matrix`. Regression test:
   `test_normalize_rational_passes_through_nonrational`.

**Acceptance (wall-clock, error-free):**

| project | before | after |
|---|---|---|
| HVCdriver | ~20 s | **6.9 s** |
| ASMPT-11 (full project) | 200 s+ (Anton) | **87.6 s** |

Combined with the earlier MECPP + normalization rounds, ASMPT-11 is now
~2.4× faster than its pre-MECPP state.

**Suite result (Anton, 2026-07-13): 351 s** — the full day's journey:

| configuration | `SLiCAPtest.sh` |
|---|---|
| original (morning) | 630 s |
| + MECPP determinant engine | 559 s |
| + normalization moved to presentation time | 502 s |
| + plot-path and ilt numeric fast paths | **351 s** |

**1.8× suite-wide, 44% removed.** The remaining 351 s is expected to be
dominated by matplotlib rendering, ngspice simulations, HTML/report
generation, and residual per-project sympy — i.e. approaching the floor
for this workload; a further round needs a fresh profile and would show
diminishing returns.

**Isolated C++ contribution (Anton, 2026-07-13):** the same suite with
`numer/denom = ME` (everything else identical): **411 s vs 351 s** — the
engine is worth 60 s (~15%) in the fast configuration; ASMPT-11 alone:
107 s (ME) vs 80 s (MECPP).

### Found & fixed via the ME run: uncancelled common factors in ilt

ASMPT-12 crashed under ME (`LinAlgError: Array must not contain infs or
NaNs` in `ilt`'s root finding) — historically bypassed with method "BS".
Diagnosis (2026-07-13): ME and MECPP results are **mathematically
identical** (verified by `cancel(diff) == 0` on the failing instruction);
the difference is FORM. The ME num/den carried an exact common polynomial
factor that sympy's division does not cancel (den degree 18 vs 17, LC
differing by ~50×); with compute-time normalization removed, that factor
reached `ilt`, where (a) `coeff/LC` overflowed float64 for detector
`V_in` → crash, and (b) for `V_position` it produced 33 time-function
terms instead of 17 (spurious near-cancelling pole/zero pairs). MECPP
passed only because GiNaC's output form happens to auto-cancel in
sympy's division — luck, not correctness.

Fix at the correct level, in `ilt`'s numeric branch: (1) `sp.cancel` the
exact common factors before coefficient extraction (exact rational GCD,
cheap at these degrees); (2) scale root finding by the **largest**
coefficient magnitude instead of the leading one — roots are
scale-invariant, and LC-relative ratios can overflow float64 (the
residue formula keeps gainD). Both methods now produce the identical
17-term result on ASMPT-12; the full script runs clean under ME (3.3 s)
and MECPP (3.0 s). Regression:
`test_ilt_cancels_common_factors_and_survives_huge_lc_spread`. 29/29
tests green.

**Root cause (Anton, 2026-07-13, verified in the netlist):** SLiCAP's
network matrices are in differential form, so matrix entries — and hence
the main determinant — are always **polynomials**. The only source of
rational functions is `gainType="vi"`: there the result is not a ratio
of two matrix determinants but **Cramer's rule with the excitation
vector substituted**, and source values may be rational in s (ASMPT-12:
`V1 value = pos/(s·(1+1.1448·s·τᵢ+0.642·s²·τᵢ²)·(…)·(…))`, denominator
degree 6). The numerator "determinant" is then a rational function;
forming numer/denom cross-multiplies and the source's denominator becomes
an exact common factor of the compound num/den. Consequences:

- Cancelling in `ilt` is **exact and safe** — exact rational GCD on the
  exact coefficients the float2rational discipline guarantees;
  value-preserving everywhere except the removable points themselves,
  and a removable pole/zero pair is not a system pole. This is nothing
  like approximation-based simplification: zero information is lost.
- Placement at the numeric consumption point (not compute time) is
  deliberate: symbolic gcd at compute time would re-import the
  normalizeRational cost. `doPZ` already defends via `_cancelPZ`; the
  plot path is numerically immune (a common factor divides out at every
  point of the jω axis).

## Platform coverage (status 2026-07-13)

**The engine source SHIPS with the package (added 2026-07-13, Anton):**
canonical location `SLiCAP/files/ginac_det/` (`det_cli.cpp`, `Makefile`,
`README.md` with per-platform build + activation instructions) — included
in every pip install via the existing `SLiCAP/files` MANIFEST rule, so
any user can build the engine from their installed copy. The repo-root
`ginac_det/` remains the dev/benchmark harness and compiles from the
canonical source (single source of truth). The pip package itself stays
pure Python (MIT); the GPL engine is built by the user or downloaded as
a release binary — the open-core split in packaging form.

SLiCAP works on all platforms regardless — no binary means Python-speed
`ME` via the fallback. The engine itself:

- **Linux**: built, verified, in daily use (`libginac-dev`, `make install`).
- **macOS**: expected to build as-is (GiNaC/CLN in Homebrew, pkg-config
  Makefile, no OS-specific code) — unverified until run on a Mac.
- **Windows**: builds under **MSYS2/MinGW only** (CLN does not build with
  MSVC); GiNaC is packaged in MSYS2. Produces a normal `slicap_det.exe`;
  the Python side (subprocess/which/config) is already platform-neutral.
  Unverified.

Cross-platform correctness is exact, not approximate: CLN is exact
rational arithmetic, so engine results are identical expressions on every
platform; the differential harness verifies a new platform in minutes.

"Works everywhere without compiling" = the already-planned CI step:
statically linked release binaries (Linux x86_64, macOS x86_64 + arm64,
Windows/MinGW) attached to GitHub releases — do when MECPP has earned it;
this is also the distribution shape of the paid tier.

## Rules carried over from ACDE.md / SLNG.md

- The Python `det()` remains the executable specification; the C++ copy
  never becomes the only implementation of anything.
- This is an experiment: it lives outside the SLiCAP package (no packaging,
  no user-facing surface) until the engine decision is taken.
- Differential testing discipline is non-negotiable for any C++ result
  that could ever reach a user.
