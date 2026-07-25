"""Instruction-file boilerplate (see SLNG.md, "Instruction-file architecture").

Two files run a GUI project:

- ``main.py``  — GUI-managed. Sets up the project and runs the instruction file::

      import SLiCAP as sl
      sl.initProject("<project name>")
      import <instr_stem>          # executes the instruction file

- ``<instr_stem>.py`` — GUI-edited. The analysis content::

      import SLiCAP as sl
      cir = sl.makeCircuit("sch/design.slicap_sch")   # SLiCAP schematics only
      LAPLACE1 = sl.doLaplace(cir, ...)
      ...

``initProject`` lives ONLY in ``main.py`` so the instruction file stays
import-safe (importing it from another project must not reset the parent's
HTML/labels state). These helpers are pure text/​file operations — no Qt.
"""
import ast
import re
from pathlib import Path

_IMPORT_LINE = "import SLiCAP as sl"


def parse_calls(text: str) -> list[dict]:
    """Inventory of the ``sl.*`` calls defined in instruction-file *text*.

    Returns an ordered list of dicts::

        {"name": …, "func": …, "assigned": bool,
         "args": [src, …], "kwargs": {kw: src, …}}

    - Assignments ``NAME = sl.<func>(…)`` are keyed by the target name and
      get ``assigned=True`` (their value is reachable as a variable — the
      plot wizard's "from other plots" mode needs this).
    - Bare calls ``sl.plot*("fileName", …)`` are keyed by their first-argument
      string literal (the figure fileName).
    - Assignment targets and bare-call fileNames are SEPARATE namespaces: a
      figure named like a result variable (``sl.plot("TRAN1", …)`` next to
      ``TRAN1 = sl.tran(…)``) must not shadow the result.
    - Only the LAST definition of each name is kept (within its namespace) —
      instructions execute top-to-bottom, so the last one wins at runtime.
      This is what makes the append-only edit model work (SLNG.md): dialogs
      prefill from the parsed last definition and append the regenerated
      call.

    Unparseable text (the user is mid-edit) yields ``[]``.
    """
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []

    def _sl_call(node):
        if (isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "sl"):
            return node
        return None

    out: dict[tuple[bool, str], dict] = {}
    for stmt in tree.body:
        name = call = None
        assigned = False
        if (isinstance(stmt, ast.Assign) and len(stmt.targets) == 1
                and isinstance(stmt.targets[0], ast.Name)):
            call = _sl_call(stmt.value)
            name = stmt.targets[0].id
            assigned = call is not None
        elif isinstance(stmt, ast.Expr):
            call = _sl_call(stmt.value)
            if (call is not None and call.args
                    and isinstance(call.args[0], ast.Constant)
                    and isinstance(call.args[0].value, str)):
                name = call.args[0].value
        if call is None or name is None:
            continue
        out[(assigned, name)] = {
            "name":     name,
            "func":     call.func.attr,
            "assigned": assigned,
            "args":     [ast.get_source_segment(text, a) for a in call.args],
            "kwargs":   {kw.arg: ast.get_source_segment(text, kw.value)
                         for kw in call.keywords if kw.arg},
        }
    return list(out.values())


def next_result_name(base: str, text: str) -> str:
    """Next free result-variable name ``<base><N>`` for the instruction-file
    *text*: ``LAPLACE2`` if ``LAPLACE1`` is already assigned, else ``LAPLACE1``.
    """
    nums = [int(m.group(1))
            for m in re.finditer(r"\b" + re.escape(base) + r"(\d+)\s*=", text)]
    return f"{base}{max(nums, default=0) + 1}"


def _has_import(lines) -> bool:
    return any(l.strip() == _IMPORT_LINE for l in lines)


def _has_circuit(lines) -> bool:
    return any("makeCircuit(" in l for l in lines)


def ensure_header(text: str, sch_type: str, schematic_relpath: str | None) -> str:
    """Return *text* with the instruction-file header prepended if missing.

    Idempotent: adds ``import SLiCAP as sl`` if absent, and — for a SLiCAP
    schematic — ``cir = sl.makeCircuit("<schematic_relpath>")`` if no
    ``makeCircuit(...)`` line is present yet.  NGspice instruction files only get
    the import (they reference the netlist by stem, not a circuit object).
    """
    lines  = text.splitlines()
    prefix = []
    if not _has_import(lines):
        prefix.append(_IMPORT_LINE)
    if sch_type == "slicap" and schematic_relpath and not _has_circuit(lines):
        prefix.append(f'cir = sl.makeCircuit("{schematic_relpath}")')
    if not prefix:
        return text
    # Each header line is newline-terminated so the header is a complete block,
    # then the existing content follows.
    return "".join(line + "\n" for line in prefix) + text


def main_py_source(project_name: str, instr_stem: str | None = None,
                   author: str | None = None) -> str:
    """Source of the project ``main.py`` that sets up the project and runs the
    instruction file (omitted when *instr_stem* is None — project creation).

    *author* is only passed at project creation; later rewrites (instruction
    runs) omit it, which is harmless: initProject() persisted it in the
    project SLiCAP.ini and keeps the stored value when the kwarg is absent."""
    if author is not None:
        init_line = f'sl.initProject("{project_name}", author="{author}")'
    else:
        init_line = f'sl.initProject("{project_name}")'
    lines = [_IMPORT_LINE, init_line]
    if instr_stem:
        lines.append(f"import {instr_stem}")
        # Design-data manifest (SLNG.md): after the instruction file ran,
        # walk its namespace and index the results for the Design data
        # panel. Guarded — a manifest problem must never fail the run.
        lines += [
            "try:",
            "    from SLiCAP.schematic.design_data import write_manifest",
            f"    write_manifest(vars({instr_stem}), \"{instr_stem}.py\")",
            "except Exception as e:",
            "    print('Warning: design-data manifest not written:', e)",
        ]
    return "\n".join(lines) + "\n"


def write_main_py(project_root, project_name: str, instr_stem: str | None = None,
                  author: str | None = None) -> Path:
    """Write/refresh ``<project_root>/main.py``; return its path."""
    path = Path(project_root) / "main.py"
    path.write_text(main_py_source(project_name, instr_stem, author),
                    encoding="utf-8")
    return path
