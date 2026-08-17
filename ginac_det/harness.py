#!/usr/bin/env python
"""Differential test + benchmark for slicap_det (C++/GiNaC) vs SLiCAP's
Python det(), per SLiCAP_GiNAC.md.

Builds MNA matrices from real circuits (docs/cir) via doMatrix, in two
regimes per circuit:
  - symbolic: doMatrix(cir)                      (sparse, fully symbolic)
  - numeric:  doMatrix(cir, pardefs='circuit', numeric=True)
              (numeric entries + Laplace variable — _eliminateVars regime)

For each matrix x method (ME, BS):
  1. run slicap_det, read its compute time (internal clock, excludes I/O)
  2. run Python det() on the identical rationalized matrix
  3. verify D_cpp == D_py: exact expand/cancel for small results, plus
     exact rational random-point evaluation (never string comparison)

Run from anywhere:  /home/anton/anton/bin/python harness.py [--timeout 120]
"""
import argparse
import json
import os
import random
import signal
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
CLI = os.path.join(HERE, "slicap_det")
CIR_DIR = os.path.join(REPO, "docs", "API", "cir")
WORK = os.path.join(HERE, "work")

CIRCUITS = [
    "myPassiveNetwork.cir",
    "ACcoupling.cir",
    "pzNetwork.cir",
    "Transimpedance.cir",
    "VampQ.cir",
    "BJTdiffAmp.cir",
    "balancedAmp.cir",
    "mainAmp.cir",
]

class Timeout(Exception):
    pass

def _alarm(signum, frame):
    raise Timeout()

def run_python_det(M, method, timeout):
    from SLiCAP.SLiCAPmath import det
    signal.signal(signal.SIGALRM, _alarm)
    signal.alarm(timeout)
    try:
        t0 = time.perf_counter()
        D = det(M, method=method)
        t = time.perf_counter() - t0
        return D, t
    except Timeout:
        return None, None
    finally:
        signal.alarm(0)

def export_matrix(M, path):
    import sympy as sp
    with open(path, "w") as f:
        f.write(f"{M.shape[0]}\n")
        for i in range(M.shape[0]):
            for j in range(M.shape[1]):
                f.write(str(M[i, j]).replace("**", "^") + "\n")

def run_cli(path, method, timeout):
    try:
        r = subprocess.run([CLI, "--method", method, path],
                           capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return None, None, "timeout"
    if r.returncode != 0:
        return None, None, r.stderr.strip()
    timing = json.loads(r.stderr.strip().splitlines()[-1])
    return r.stdout.strip(), timing, None

def verify(D_py, D_cpp_text, nsymbols_hint=None):
    """Exact verification; returns (ok, how)."""
    import sympy as sp
    # GiNaC prints its constants as Pi/E/I — map them back to sympy's,
    # otherwise sympify creates plain symbols and verification falsely fails
    D_cpp = sp.sympify(D_cpp_text.replace("^", "**"),
                       locals={"Pi": sp.pi, "E": sp.E, "I": sp.I})
    diff = D_py - D_cpp
    # cheap exact route first
    try:
        signal.signal(signal.SIGALRM, _alarm)
        signal.alarm(60)
        d = sp.expand(diff)
        if d == 0:
            return True, "expand"
        d = sp.cancel(d)
        if d == 0:
            return True, "cancel"
    except Timeout:
        pass
    finally:
        signal.alarm(0)
    # exact rational random-point evaluation (3 points)
    syms = list(diff.free_symbols)
    rng = random.Random(20260713)
    for _ in range(3):
        subs = {s: sp.Rational(rng.randint(2, 97), rng.randint(2, 97))
                for s in syms}
        val = sp.cancel(diff.xreplace(subs))
        if val != 0:
            return False, "point"
    return True, "3-point"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeout", type=int, default=120,
                    help="per-case timeout in seconds (each side)")
    args = ap.parse_args()

    os.makedirs(WORK, exist_ok=True)
    os.chdir(WORK)  # SLiCAP writes SLiCAP.ini + project dirs in cwd

    import sympy as sp
    import SLiCAP as sl
    from SLiCAP.SLiCAPmath import float2rational

    sl.initProject("ginac_det_benchmark")

    # makeCircuit reads netlists from the project's cir/ directory and
    # user libraries from lib/
    import glob
    import shutil
    os.makedirs("cir", exist_ok=True)
    os.makedirs("lib", exist_ok=True)
    for cir_name in CIRCUITS:
        src = os.path.join(CIR_DIR, cir_name)
        if os.path.exists(src):
            shutil.copy(src, os.path.join("cir", cir_name))
    for lib in glob.glob(os.path.join(REPO, "docs", "lib", "*.lib")):
        shutil.copy(lib, os.path.join("lib", os.path.basename(lib)))

    cases = []
    for cir_name in CIRCUITS:
        if not os.path.exists(os.path.join("cir", cir_name)):
            print(f"-- skip {cir_name}: not found")
            continue
        try:
            cir = sl.makeCircuit(cir_name)
        except Exception as e:
            print(f"-- skip {cir_name}: makeCircuit failed: {e}")
            continue
        for regime, kwargs in [("symbolic", {}),
                               ("numeric", dict(pardefs="circuit", numeric=True))]:
            try:
                instr = sl.doMatrix(cir, **kwargs)
                M = float2rational(sp.Matrix(instr.M))
            except Exception as e:
                print(f"-- skip {cir_name} [{regime}]: doMatrix failed: {e}")
                continue
            cases.append((cir_name.replace(".cir", ""), regime, M))

    results = []
    for name, regime, M in cases:
        dim = M.shape[0]
        fixture = os.path.join(WORK, f"{name}_{regime}.txt")
        export_matrix(M, fixture)
        for method in ("ME", "BS"):
            label = f"{name} [{regime}] {dim}x{dim} {method}"
            out, timing, err = run_cli(fixture, method, args.timeout)
            if err:
                print(f"FAIL {label}: cli: {err}")
                results.append(dict(name=name, regime=regime, dim=dim,
                                    method=method, error=f"cli: {err}"))
                continue
            D_py, t_py = run_python_det(M, method, args.timeout)
            if D_py is None:
                print(f"     {label}: cpp {timing['compute_s']:.4f}s, python TIMEOUT (>{args.timeout}s)")
                results.append(dict(name=name, regime=regime, dim=dim,
                                    method=method, t_cpp=timing["compute_s"],
                                    t_py=None, verified=None))
                continue
            ok, how = verify(D_py, out)
            t_cpp = timing["compute_s"]
            speedup = t_py / t_cpp if t_cpp > 0 else float("inf")
            status = "ok" if ok else "MISMATCH"
            print(f"{status:>4} {label}: cpp {t_cpp:.4f}s, py {t_py:.4f}s, "
                  f"speedup {speedup:.0f}x, verified via {how}")
            results.append(dict(name=name, regime=regime, dim=dim,
                                method=method, t_cpp=t_cpp, t_py=t_py,
                                speedup=speedup, verified=ok, how=how))

    with open(os.path.join(HERE, "results.json"), "w") as f:
        json.dump(results, f, indent=1)
    print(f"\n{len(results)} cases -> {os.path.join(HERE, 'results.json')}")
    bad = [r for r in results if r.get("verified") is False]
    if bad:
        print(f"MISMATCHES: {len(bad)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
