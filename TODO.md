# SLiCAP GUI — Active TODOs

Curated, actionable items. The full historical design log stays in `SLNG.md`;
this file is the short list of what's still open. Last curated: 2026-07-16.

Status key: `[ ]` open · `[~]` in progress · `[?]` needs a decision from Anton

---

## >>> FOCUS NOW: B (needed before pushing to GitHub) <<<

## Pre-push checklist (Anton, 2026-07-16)

- [ ] **1. Lots of testing** — Anton (drawing many schematics this weekend).
- [ ] **2. Docs + rewrite `manual.py`** for using SLiCAP schematics — Anton's
  content; I can assist/draft.
- [x] **3. Dependencies** — AST inventory vs pyproject (SLNG.md). Added `sphinx`,
  `reportlab`, `cairosvg` (PDF export/print); `h5py` as `[hdf5]` optional extra;
  removed dead `windows_tools`/`pywin32`. PySide6-Addons still needed (print/pdf).
  RST test CI-safe. Requirements now match the code.
- [ ] **4. CI → PyPI**: workflow YAML is Anton's (I don't touch `.github/`).
  Tests are CI-safe now.

## B. App / config  — **PRIORITY, pre-push**

- [x] **NGspice-installed check + deprecate the other-app search** — DONE
  2026-07-16 (SLNG.md). Removed the interactive/full-drive Windows search
  (`input()` + walk + timeout would hang a GUI first-run); detection is now
  non-interactive (`shutil.which` + OS-standard-location probe: `C:\Spice64\bin`
  console/gui, macOS Homebrew, Linux `/usr/bin`). Runtime check `_check_ngspice`
  + **"Locate NGspice…"** file-picker (writes `[commands] ngspice`) wired at
  **New NGspice Schematic** and the **NGspice instruction dialog**.
  Verify live: the warning + Locate flow on a machine without NGspice.
- [ ] **Stop persisting html/label state in the project `SLiCAP.ini`** — "big
  TODO" cleanup (not blocking the push).
- [ ] **Manual/doc updates**: reserved `~/SLiCAP/` dir migration; update doc
  references pointing at `~/SLiCAP.ini`; `sub2rm`-in-formatter; an
  `initProject(html=…)` skip-HTML argument.

## A. RST preview + snippets — WORKS (Anton verified the math flow)

- [ ] Live-verify the remaining snippet kinds when convenient (flow with math OK).
- [low] **Offline-math speedup** (imgmath ~9s) — **very low priority** (Anton).
- [ ] Background build to remove the ~1s online freeze — nice-to-have.
- [ ] **MyST / HTML / plain-text snippet targets** — each is one more
  `SnippetTarget` (+ menu line). When wanted.

## C. NGspice roadmap — DEFERRED until Anton's manual pass

Anton: first wants to **run everything that's in the current manual**; goal
functions and noise weighting filters not yet verified. ("Convergence" = the
SLiCAP↔NGspice feature roadmap, not a simulation timeout.)
- [x] Item 3 = **FFT / Fourier** — DONE (built 2026-07-12). Not a separate tab:
  it's transient **Post-processing** (Transient tab dropdown: None / FFT / Fourier
  + window + harmonics) → `sl.tran(..., fft=…, fourier=…)`. Verify vs the manual
  during the pass.
- [ ] Item 4 = **table-result + goal functions** (stepped analysis; noise
  weighting filters) — the genuinely open one. Revisit after the manual pass.
- [ ] `goal_bandwidth` fix; result-object unification — low priority.

## D. Strategic

- [ ] **Market validation** (deep-research) before external use — keep in mind.

## E. New functionality (lower priority)

- [ ] **Custom plots** — NOT missing/broken: "Create / edit plot…" is on the
  main-window Instruction menu (`plot_dialog.py`). Anton: this needs a GUI
  definition from his side (new functionality) → lower priority.
- [ ] Stimuli widget / snippet dialog — Anton is doing live verification himself
  (drawing many schematics this weekend).
