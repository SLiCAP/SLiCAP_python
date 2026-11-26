"""The system schematic dialect in the editor (SystemExtensionSpecs.md 9).

What differs for a system diagram beyond the dialect table
(dialects.SYSTEM): the blocks are function classes, placed from a class
or scaffolded (``add_circuit_actions``); a hierarchical block is its
diagram ``lib/<name>.system_sch`` (``subcircuit.schematic_subckt_def``
reads its ports and parameters); the wires carry typed signals, checked
on the drawing (``check_nets``), and the clock symbols show the
frequency of their node and the master tick (``clock_annotations``),
both installed on the scene by ``attach``; a function symbol follows
its class on load (``after_load``); the instruction menu writes the run
script and the system run (``add_instr_menu``). The symbol generation
and the wire rules live in system_symbols.py, without Qt.

Local only (.git/info/exclude) until the simulator is released; the
public editor reaches this module through ``dialects.SYSTEM`` only when
``SLiCAP.SLiCAPsystem`` is installed.
"""

import ast
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (QCheckBox, QDialog, QDialogButtonBox, QComboBox,
                               QFormLayout, QGroupBox, QLabel, QLineEdit,
                               QListWidget, QListWidgetItem, QMessageBox,
                               QPushButton, QRadioButton,
                               QSpinBox, QVBoxLayout, QWidget)

from . import project
from . import system_symbols as symbols
from .code_editor import CodeEditor
from .component_item import ComponentItem
from .sizing import chars


# ---- the hooks on the scene ------------------------------------------------------

def attach_scene(scene) -> None:
    """The hooks of the dialect that need no window: the clock labels
    (Specs 3.2, 10.4.9) and the editor of a signal source. The command-line
    loader (cli._load_scene) installs them too, so an image written by
    sl.makeCircuit carries the clock labels the editor shows at the moment
    of the export: for a sheet with a hierarchical block or a
    parameterised clock tree, those of the most recent run recorded then.
    Before 2026-11-21 only the editor installed them, and an exported sheet
    had no clock labels (Anton). The run record is a source of the image
    (provenance.results_drawn), so a newer run re-exports it at the next
    makeCircuit (Anton, 2026-11-21)."""
    scene.annotator = clock_annotations
    scene.component_editor = component_editor


def attach(panel) -> None:
    """Install the dialect on the panel's scene: the hooks of attach_scene,
    the wire check (Specs 9.3) and the extras of the Properties dialog. The
    implicit-casts setting is read from the panel's document properties at
    every check, so a loaded file brings its own."""
    scene = panel._scene
    attach_scene(scene)
    scene.net_check = lambda comps, wires: check_nets(
        comps, wires, panel._doc_props.implicit_casts)
    scene.properties_extra = lambda item: properties_extra(item, panel)


def component_editor(item):
    """The dialect's own editor of a block: the Signal dialog for a
    signal source (Specs 6.1.2: one symbol whose waveform selects the
    parameter fields); None for every other block."""
    if (item.model or item.symbol_name) == "Signal":
        return ("Define signal…", edit_signal)
    return None


def properties_extra(item, panel=None):
    """What the Properties dialog of a filter block gets (Specs 10.3.1,
    10.3.8): the button "Design..." that opens the design dialog on the
    file of its design, and the descent into the schematic of the
    circuit the design was made from, which the symbol records. The
    block has no parameters: the design is the file. The model is the
    design and is fixed: Design... changes it (Anton, 2026-11-19: a
    model typed as XT1 on an XT3 block named a design that did not
    exist, and the next load set it back). None for every other block."""
    if not symbols.is_design_block(item.symbol):
        return None
    design = item.symbol.name
    out = {"fixed": ("model",)}
    if panel is not None:
        out["actions"] = [("Design\u2026 (%s)" % design_file_of(panel, design),
                           lambda: _edit_filter(panel, item))]
    text = "Descend into the circuit of %s" % design
    rel = item.symbol.schematic
    if not rel:
        out["descend"] = (text, None, "The design has no circuit: its file makes "
                          "a prototype, not a doLaplace() of a schematic")
        return out
    path = Path(_project_root_of([item])) / rel
    out["descend"] = (text, path if path.is_file() else None,
                      str(rel) if path.is_file() else "Schematic not found: %s" % rel)
    return out


def check_nets(components, wires, implicit=True) -> list:
    """The rules the nets of the drawing break, as messages in the order
    of the nets: the pins on every net, with the types and
    directions from their symbols, against ``system_symbols.check_net``.
    The pins of a net are sorted by label so that the same state gives
    the same message, which the scene compares before and after a
    gesture. Was ``check_wire`` on the wire just drawn (REPLACED
    2026-11-19: a block moved onto a wire bypassed it)."""
    from .connectivity import _build_net_uf, _rpt
    uf = _build_net_uf(components, wires)
    pins = {}
    for comp in components:
        for name, pos in zip(comp.node_names(), comp.pin_scene_pos()):
            root = uf.find(_rpt(pos))
            pins.setdefault(root, []).append(("%s.%s" % (comp.instance_id, name),
                                              comp.symbol.pin_types.get(name),
                                              comp.symbol.pin_dirs.get(name)))
    out = []
    for root in sorted(pins):
        out += symbols.check_net(sorted(pins[root]), implicit)
    return out


def _si(value, unit) -> str:
    """``2.5e8, "Hz"`` -> ``"250 MHz"``."""
    from SLiCAP.SLiCAPlex import _eng_notation
    text = _eng_notation(value, 4)
    if text[-1:].isalpha():
        return "%s %s%s" % (text[:-1], text[-1], unit)
    return "%s %s" % (text, unit)


def clock_annotations(components, wires) -> dict:
    """The derived labels of the clock symbols: on every clock node "f",
    its frequency, and "T", its period in master ticks when it is a
    domain; on the reference clock "Ts", the master tick (Specs 3.2,
    3.3). The component shows them in the form of the operating-point
    labels. The tree is the generator's (system_script.clock_tree) on
    the view of this one diagram: a node hangs on the net its input is
    wired to; a node whose output clocks a function is a domain. While
    no function is clocked, the end nodes count as domains and Ts and T
    are provisional, shown dimmed: the master tick the scheme would need
    (Anton, 2026-11-17). A node the tree does not reach, or with a
    non-integer factor, has no value (None)."""
    from . import system_script
    from .netlist import NetlistError
    out = {}
    root = _project_root_of(components)
    try:
        flat = system_script.flatten(components, wires, root, descend=False)
    except NetlistError:                  # a net with two names: no tree
        return out
    for cn in flat.nodes:
        out[cn.name] = {"f": None}
    for ck in flat.clocks:
        out[ck.name] = {"Ts": None}
    if _needs_run(components, flat):
        # the engine resolves it, the labels show the most recent run of
        # the sheet (Specs 10.4.9)
        scene = components[0].scene() if components else None
        path = getattr(scene, "file_path", None)
        record = run_clocks(root, Path(path).stem) if path else None
        return _run_labels(out, flat, record)
    tree, node_of_net, _problems, provisional = system_script.clock_tree(
        flat, provisional=True)
    if tree is None:
        return out

    def value(text):
        return (text, True) if provisional else text

    def ticks(node):
        n = tree.period(node)
        text = "%d tick%s" % (n, "" if n == 1 else "s")
        if tree.is_pacing(node):
            # an update clock: its period as a multiple of the hyperperiod
            # of the signal domains, or the reason the generator refuses it
            # (Specs 10.3.6)
            hp = _hyperperiod(tree)
            if hp is None:
                return value(text)
            if n % hp:
                return value(text + ", not a multiple of H")
            return value("%s = %d H" % (text, n // hp))
        return value(text)

    for cn in flat.nodes:
        # only a node the tree reached has a frequency; "its output net
        # has a clock" was the test and raised KeyError on a node whose
        # output was wired onto the reference net while its input was
        # free (Anton, 2026-11-19): the sheet did not load
        if node_of_net.get(cn.nets["out"]) == cn.name:
            out[cn.name] = {"f": _si(tree.frequency(cn.name), "Hz")}
            if cn.name in tree.domains:
                out[cn.name]["T"] = ticks(cn.name)
    for b in flat.functions:
        # a filter block whose update clock pin has no clock: its
        # coefficients are computed once, at the start (Anton, 2026-11-18)
        if (b.name in flat.designs and symbols.UPDATE_CLOCK in b.nets
                and b.nets[symbols.UPDATE_CLOCK] not in node_of_net):
            out[b.name] = {symbols.UPDATE_CLOCK: "once"}
    if tree.domains:
        ref = flat.clocks[0].name
        out[ref] = {"Ts": value(_si(tree.master_tick, "s"))}
        hp = _hyperperiod(tree)
        if hp is not None:
            # the hyperperiod of the signal domains, which the designer needs
            # to choose an update clock (Anton, 2026-11-17; Specs 10.3.6)
            out[ref]["H"] = value("%d tick%s" % (hp, "" if hp == 1 else "s"))
        if tree.ROOT in tree.domains:
            out[ref]["T"] = ticks(tree.ROOT)
    return out


def _needs_run(components, flat) -> bool:
    """Whether the one-diagram view cannot compute the clock tree, so the
    labels come from a run (Specs 10.4.9): a value of f_ref, m, d or
    phase in parameters, which the engine resolves; or a hierarchical
    block, whose child diagram holds the clocked functions and so the
    domains, the master tick and the hyperperiod (Anton, 2026-11-20:
    "only back annotation of the timing is missing" on a sheet of three
    blocks, which showed the provisional values of an empty tree)."""
    from . import system_script
    from .system_script import BLOCK_PREFIX, DRIVEN_CLOCK
    if any(b.comp.symbol_name == DRIVEN_CLOCK for b in flat.clocks):
        return True                      # the frequency is a signal: a run knows it
    if any(system_script._is_expression(b.params.get("f_ref")) for b in flat.clocks):
        return True
    if any(system_script._is_expression(b.params.get(key))
           for b in flat.nodes for key in ("m", "d", "phase")):
        return True
    return any(c.prefix == BLOCK_PREFIX for c in components)


def run_clocks(root, stem):
    """The clock values of the most recent run of the diagram *stem*
    that holds a ``clocks`` record, from the Design data manifest (Specs
    10.4.9: the engine is the one place that resolves a parameterised
    clock tree, and it records the tree only when every run of a
    stepped result shares it): ``{"master_tick", "hyperperiod",
    "clocks": {node: {"frequency", "period", "phase"}}}``, or None
    without such a run. The record (6.9.3) is read as the manifest
    stores a record: one entry per node with its fields as children."""
    from .design_data import read_manifest
    manifest = read_manifest(project.folder("results", root))
    sections = sorted((manifest.get("sections") or {}).values(),
                      key=lambda s: s.get("timestamp", 0), reverse=True)
    for section in sections:
        for var in section.get("variables", []):
            if var.get("kind") != "result" or var.get("dataType") != "system":
                continue
            attrs = {a.get("name"): a for a in var.get("attributes", [])}
            script = str(attrs.get("script", {}).get("value", ""))
            if Path(script).stem != stem or "clocks" not in attrs:
                continue
            try:
                clocks = {}
                for node in attrs["clocks"].get("attributes", []):
                    fields = {f.get("name"): f for f in node.get("attributes", [])}
                    clocks[node["name"]] = {
                        key: (float(fields[key]["value"])
                              if key in fields and fields[key].get("kind") == "number"
                              else None)
                        for key in ("frequency", "period", "phase")}
                return {"master_tick": float(attrs["master_tick"]["value"]),
                        "hyperperiod": int(float(attrs["hyperperiod"]["value"])),
                        "clocks": clocks}
            except (KeyError, ValueError, TypeError):
                return None
    return None


def _run_labels(out, flat, record):
    """The clock labels from a run record (``run_clocks``): "f" and "T"
    per node, "Ts", "H" and "T" on the reference; None values without a
    record, shown as "—" until a run."""
    if not record:
        return out
    clocks, hp = record["clocks"], record["hyperperiod"]

    def ticks(n):
        return "%d tick%s" % (n, "" if n == 1 else "s")

    for cn in flat.nodes:
        rec = clocks.get(cn.name)
        if rec is None or rec["frequency"] is None:
            continue
        out[cn.name] = {"f": _si(rec["frequency"], "Hz")}
        if rec["period"] is not None:
            n = int(rec["period"])
            text = ticks(n)
            if hp and n % hp == 0 and n != hp:
                text = "%s = %d H" % (text, n // hp)
            out[cn.name]["T"] = text
    for ck in flat.clocks:
        out[ck.name] = {"Ts": _si(record["master_tick"], "s"), "H": ticks(hp)}
        ref = clocks.get("ref")
        if ref is not None and ref["period"] is not None:
            out[ck.name]["T"] = ticks(int(ref["period"]))
    return out


def _hyperperiod(tree):
    """The hyperperiod of the signal domains, None while every domain is
    an update clock."""
    try:
        return tree.hyperperiod
    except ValueError:
        return None


def _project_root_of(components):
    scene = components[0].scene() if components else None
    path = getattr(scene, "file_path", None)
    return project.root_for(path) if path else project.project_root()


def after_load(panel) -> list:
    """Regenerate the symbol of every block whose declaration changed
    since the symbol was written (Specs 9.5: "the symbol is regenerated
    on the next load"), reload the placed blocks and tell the user to
    check their wiring. Returns the regenerated names. Two sources of
    a declaration: the function class of a function block and the
    system library for a fixed symbol whose pins moved (the signal
    clock of SIGNAL, 2026-11-18); a third, the parameter table of the
    child diagram of a hierarchical block (its parameters and defaults,
    Specs 10.4.6): the symbol's metadata is rewritten on its artwork
    when the table changed, a changed port list is reported for the
    user to re-place the block (2026-11-20). A filter block is not regenerated:
    its design is a library file and nothing runs on load (Specs
    10.3.2); a filter symbol of the 2026-11-18 form (the lines in the
    symbol, the design name and properties in the block's parameters)
    is moved ONCE to ``lib/<design>.py`` and a library entry
    (``_migrate_old_design``; REMOVE with the next release).
    Regeneration from the Design data was REPLACED (2026-11-18)."""
    from . import system_script
    from .system_script import BLOCK_PREFIX
    root = _project_root(panel)
    comps = [i for i in panel._scene.items()
             if isinstance(i, ComponentItem)
             and (i.prefix in symbols.BLOCK_PREFIXES
                  or i.prefix == BLOCK_PREFIX           # a hierarchical block
                  or i.symbol_name in system_script.CLOCKS + (system_script.CLOCK_NODE,))]
    if not comps:
        return []
    classes = {c.__name__: c for c in symbols.builtin_classes()}
    classes.update({c.__name__: c for c in symbols.project_classes(root)[0]})
    done, dropped, moved, reported = [], [], [], []
    for name in sorted({c.symbol_name for c in comps}):
        sym = panel._library.symbol(name)
        if sym is None:
            continue
        new = None
        if symbols.is_design_block(sym):
            for comp in comps:
                if comp.symbol_name == name and comp.model != sym.model:
                    _take_design_symbol(comp, sym)     # a block migrated before 2026-11-19
                    panel._dirty = True
            continue
        if symbols.is_old_design_block(sym):
            comp = next((c for c in comps if c.symbol_name == name), None)
            record = symbols.old_design_record(sym, comp.params if comp else None)
            new = _migrate_old_design(panel, root, record, symbols.design_controls(sym))
            if new is None:
                continue
            for comp in comps:
                if comp.symbol_name == name:
                    _take_design_symbol(comp, new)
            if (Path(root) / "lib" / (record["name"] + ".py")).is_file():
                moved.append("%s -> lib/%s.py" % (name, record["name"]))
            continue
        elif (name in symbols.FIXED_SYMBOLS.values()
              or name in system_script.CLOCKS + (system_script.CLOCK_NODE,)):
            # a fixed symbol of a class, or a clock symbol of the system
            # library (2026-11-20: CLK had the input f for a day, which went
            # to the symbol CLKF of its own)
            from .symbol_library import build_library, NO_BUNDLE
            fresh = build_library(panel._current_path, sch_type="system",
                                  overlay=NO_BUNDLE).symbol(name)
            if fresh is not None and list(fresh.nodes) != list(sym.nodes):
                panel._library.update_symbols(
                    build_library(panel._current_path, sch_type="system",
                                  overlay=NO_BUNDLE), [name])
                new = panel._library.symbol(name)
        elif (Path(root) / "lib" / (name + ".system_sch")).is_file():
            new = _refresh_block_symbol(panel, root, name, sym, reported)
        else:
            cls = classes.get(name)
            if cls is not None and not symbols.is_current(sym, cls):
                new = panel.adopt_symbol(name, symbols.symbol_svg(cls))
        if new is None:
            continue
        for comp in comps:
            if comp.symbol_name == name:
                comp.reload_symbol(new)
                dropped += _reconcile_params(comp, new)
        done.append(name)
    if done or moved or reported:
        panel._scene._sync_junctions()
        panel._dirty = bool(done or moved)
        text = ""
        if done:
            text = ("The declaration of %s changed. The symbols were regenerated; "
                    "check the wiring of these blocks and save."
                    % ", ".join(done))
        if reported:
            text += "\n\n" + "\n".join(reported)
        if dropped:
            text += ("\n\nParameters no longer declared were dropped; enter "
                     "their values under the new names:\n" + "\n".join(dropped))
        if moved:
            text += ("\n\nThe filter designs were moved to library files of the "
                     "sheet (System > Library...): %s. Save." % ", ".join(moved))
        QMessageBox.information(panel, "Symbols regenerated", text.strip())
    return done + [m.split(" -> ")[0] for m in moved]


def _refresh_block_symbol(panel, root, name, sym, reported):
    """The symbol of the hierarchical block *name* brought in step with
    its child diagram lib/<name>.system_sch: the parameters and their
    defaults are the child's parameter table (``schematic_subckt_def``).
    A changed table rewrites the symbol's metadata on its artwork and
    returns the new symbol; a changed port list is appended to
    *reported* for the user, who re-places the block; None when nothing
    changed or the child is not a block."""
    from .subcircuit import schematic_subckt_def, reskin_symbol_svg
    try:
        defn = schematic_subckt_def(Path(root) / "lib" / (name + ".system_sch"))
    except (ValueError, OSError):
        return None
    if list(defn.ports) != list(sym.nodes):
        reported.append("The ports of lib/%s.system_sch are %s, the block's pins "
                        "%s: place the block again (System > Place hierarchical "
                        "block...)." % (name, ", ".join(defn.ports), ", ".join(sym.nodes)))
        return None
    if ([(k, v) for k, v in defn.params]
            == [(k, sym.param_defaults.get(k, "")) for k in sym.params]):
        return None
    svg_text = reskin_symbol_svg(sym.g_xml, defn, {p: p for p in sym.nodes})
    return panel.adopt_symbol(name, svg_text)


def _take_design_symbol(comp, sym) -> None:
    """Give the block *comp* the regenerated symbol *sym* of its design:
    the artwork and pins, the model label, which is the design's name
    (the symbol's model; the old form set it to "Filter" and hid it,
    Anton, 2026-11-19: "can't we put the variable name there"), and no
    parameters (the design is the library file)."""
    comp.reload_symbol(sym)
    comp.model = sym.model
    comp.prop_display["model"] = (sym.model_show, False)
    comp.params = {k: v for k, v in comp.params.items() if k.startswith("_")}
    comp.update_labels()


def _migrate_old_design(panel, root, record, controls):
    """The one-time move of a filter design of the 2026-11-18 form
    (``old_design_record``) to the library form of Specs 10.3.1: the
    design file ``lib/<name>.py`` from the lines and the create
    properties (not written over an existing file), the new symbol from
    the old pins (nothing runs on load) and the library entry. An old
    symbol without lines gets the new symbol only, so its blocks keep
    their wiring, and a message: the design is defined through
    Properties -> Design…. Returns the new symbol. REMOVE with the next
    release."""
    from .system_script import design_file_text, IMPORT_DIRECTIVE
    name = record["name"]
    sym = panel.adopt_symbol(name, symbols.filter_symbol_svg(
        name, controls, "Filter %s" % name, record["schematic"]))
    if sym is None:
        return None
    if not record["lines"].strip() or not record["source"]:
        QMessageBox.warning(panel, "Filter design", (
            "The filter %s holds no design yet. Open the Properties of one of "
            "its blocks and press Design… to define it; its blocks keep their "
            "wiring." % name))
        return sym
    path = Path(root) / "lib" / (name + ".py")
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(design_file_text(
            name, record["lines"], record["source"], record["kind"] or "IIR",
            record["method"], record["length"] or 64, record["window"]),
            encoding="utf-8")
    panel._ensure_library_include(path, IMPORT_DIRECTIVE)
    return sym


def _reconcile_params(comp, symbol) -> list:
    """After a symbol regeneration: the block keeps the values of the
    parameters the class still declares, takes the defaults of new ones
    and drops the rest. Returns one line per block naming the dropped
    values, so the user can enter them again (the NCO's f0/fmin/fmax
    became f_c/df_min/df_max, Anton, 2026-11-17)."""
    old = dict(comp.params)
    if not symbol.params:
        # a symbol without declared parameters (SIGNAL): its values belong
        # to the dialect's editor, the Signal dialog, and stay (2026-11-18)
        comp.update_labels()
        return []
    comp.params = dict(symbol.param_defaults)
    for key in comp.params:
        if key in old:
            comp.params[key] = old[key]
    for key, value in old.items():
        if key.startswith("_"):
            comp.params[key] = value          # internal, never declared
    gone = {k: v for k, v in old.items()
            if k not in comp.params and not k.startswith("_")}
    comp.update_labels()
    if not gone:
        return []
    return ["%s: %s" % (comp.instance_id,
                        ", ".join("%s = %s" % kv for kv in gone.items()))]


# ---- the Circuit menu ----------------------------------------------------------

def add_circuit_actions(panel, menu) -> None:
    """The entries that place a function block: from an existing class, or
    from a new class written as a skeleton into the project's lib/."""
    act = QAction("Place &function…", panel)
    act.setToolTip("Place a block for a function class of SLiCAP or of this "
                   "project's lib/ folder; the symbol is generated from the class")
    act.triggered.connect(lambda: _on_place_function(panel))
    menu.addAction(act)
    act = QAction("New f&unction…", panel)
    act.setToolTip("Write the skeleton of a new function class into lib/<Name>.py "
                   "and place its block")
    act.triggered.connect(lambda: _on_new_function(panel))
    menu.addAction(act)


def add_instr_menu(panel, bar):
    """The Instruction menu of a system diagram, in the pattern of the
    NGspice one: the run-script step, ``sl.makeCircuit("sch/<name>
    .system_sch")``, which writes <root>/<name>.py, and the system run,
    ``R1 = sl.runSystem("<name>", ...)``, which the dialog composes."""
    menu = bar.addMenu("&Instruction")
    if panel._schematic_only:
        menu.setEnabled(False)
        return menu
    act = QAction("Create &run script…", panel)
    act.setToolTip('Add  sl.makeCircuit("<this diagram>")  to the instruction '
                   "file: it writes <project root>/<name>.py, the run script "
                   "the system run imports")
    act.triggered.connect(lambda: _on_create_run_script(panel))
    menu.addAction(act)
    act = QAction("Create / edit &system run…", panel)
    act.setToolTip("Add a run  R = sl.runSystem(...)  to the instruction file, "
                   "or edit one in place: the run length and the signals to store")
    act.triggered.connect(lambda: _on_system_run(panel))
    menu.addAction(act)
    act = QAction("Make &filter…", panel)
    act.setToolTip('Add  FLT1 = sl.makeFilter("lib/<design>.py", ...)  to the '
                   "instruction file: the filter for one sample period and one "
                   "set of parameter values, for its frequency and time traces "
                   "(Create / Edit Traces)")
    act.triggered.connect(lambda: _on_make_filter(panel))
    menu.addAction(act)
    panel._add_transfer_function_action(menu)
    return menu


def project_designs(root) -> list:
    """The filter designs of the project: ``(file, name)`` for every
    ``NAME = sl.createIIR(...)`` or ``sl.createFIR(...)`` in ``lib/*.py``,
    *file* relative to the project *root*. The files are read, not run
    (``instr_file.parse_calls``)."""
    from .instr_file import parse_calls
    out = []
    lib = Path(root) / "lib"
    for path in sorted(lib.glob("*.py")) if lib.is_dir() else []:
        try:
            calls = parse_calls(path.read_text(encoding="utf-8"))
        except OSError:
            continue
        for call in calls:
            if call["assigned"] and call["func"] in ("createIIR", "createFIR"):
                out.append(("lib/%s" % path.name, call["name"]))
    return out


def _on_make_filter(panel) -> None:
    """Instruction -> Make filter…: ``FLT1 = sl.makeFilter(...)``, the
    filter of a design script in lib/ for one sample period and one set of
    parameter values (Anton, 2026-11-25). The design is never defined a
    second time in the instruction file (Anton, 2026-11-24). The Traces
    dialog then offers its frequency and time traces."""
    import SLiCAP.SLiCAPconfigure as ini
    from . import app_prefs
    from .filter_dialog import MakeFilterDialog
    title = "Make filter"
    if panel._main_win is None or not _instructions_parse(panel, title):
        return
    root = _project_root(panel)
    designs = project_designs(root)
    if not designs:
        QMessageBox.information(panel, title,
                                "The project has no filter design in lib/ yet. "
                                "Make one with Design… in the Properties of a "
                                "filter block.")
        return
    editor = panel._main_win._instr_editor
    dlg = MakeFilterDialog(designs, editor.text(), root,
                           csv_dir=str(Path(root) / ini.csv_path),
                           preset=app_prefs.get_pardefs_preset(), parent=panel)
    if not dlg.exec():
        return
    editor.insert_snippet(dlg.generated_snippet())
    editor.show()
    editor.raise_()
    panel._status("Filter %s added to the instruction file."
                  % dlg._name.text().strip())


def _instructions_parse(panel, title) -> bool:
    """True when the instruction file parses; else say where it does not.
    The instruction entries read the file: unparsed, it shows no
    makeCircuit line and no runs, and a step would be added twice (a
    review, 2026-11-21: "Create the run script first" was shown for a file
    that had the line but a syntax error elsewhere)."""
    import ast
    try:
        ast.parse(panel._main_win._instr_editor.text())
    except SyntaxError as exc:
        QMessageBox.warning(panel, title,
                            "The instruction file does not parse (line %s: %s).\n\n"
                            "Correct it first: this step reads the file."
                            % (exc.lineno, exc.msg))
        return False
    return True


def _on_create_run_script(panel) -> None:
    from .instr_file import netlist_calls, quoted
    if panel._current_path is None or panel._main_win is None:
        return
    if not _instructions_parse(panel, "Create run script"):
        return
    editor = panel._main_win._instr_editor
    relpath = panel._schematic_relpath()
    text = editor.text()
    if relpath in netlist_calls(text):
        QMessageBox.information(panel, "Create run script",
                                "The instruction file already creates the run "
                                "script of\n    %s" % relpath)
        return
    line = "sl.makeCircuit(%s)" % quoted(relpath)
    # a position in the text as read: the editor adds the header after the
    # insert, in the same undo step (InstrEditor._seed_header, 2026-11-22)
    first = _first_run_position(text, panel._current_path.stem)
    if first is None:
        editor.insert_snippet(line)
    else:
        # a run of this diagram is already in the file (pasted from the
        # manual): the run script must be written before it runs (a review,
        # 2026-11-21: appended after it, the run found no script)
        editor.insert_at(first, line + "\n")
    editor.show()
    editor.raise_()
    panel._status("Run-script step added to the instruction file.")


def _first_run_position(text, stem):
    """The character position of the first top-level statement that runs
    the diagram *stem* (``NAME = sl.runSystem("<stem>", ...)``), or None."""
    import ast
    from .instr_file import _char_offset
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return None
    for stmt in tree.body:
        call = getattr(stmt, "value", None)
        if (isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute)
                and call.func.attr == "runSystem" and call.args
                and isinstance(call.args[0], ast.Constant)
                and Path(str(call.args[0].value)).stem == stem):
            return _char_offset(text, stmt.lineno, stmt.col_offset)
    return None


def _require_run_script(panel) -> bool:
    """True when the instruction file creates this diagram's run script;
    else explain. The file is checked, not the disk, as for the NGspice
    netlist step."""
    from .instr_file import netlist_calls
    if panel._main_win is None or not _instructions_parse(panel, "System run"):
        return False
    relpath = panel._schematic_relpath()
    if relpath in netlist_calls(panel._main_win._instr_editor.text()):
        return True
    QMessageBox.information(
        panel, "System run",
        "Create the run script first.\n\nThe instruction file has no\n"
        '    sl.makeCircuit("%s")\n'
        "line yet. Add it with Instruction -> Create run script…, then "
        "add the run." % relpath)
    return False


def _on_system_run(panel) -> None:
    if not panel._current_path or not panel._save_before_instruction():
        return
    if not _require_run_script(panel):
        return
    from . import system_script
    from .netlist import NetlistError
    items = panel._scene.items()
    comps = [i for i in items if isinstance(i, ComponentItem)]
    from .wire_item import WireItem
    wires = [i for i in items if isinstance(i, WireItem)]
    try:
        signals = system_script.signal_names(comps, wires, _project_root(panel))
    except NetlistError as exc:
        QMessageBox.critical(panel, "System run",
                             "The diagram cannot be run:\n\n" + "\n".join(exc.errors))
        return
    prev = getattr(panel, "_system_run_dlg", None)
    if prev is not None and prev.isVisible():
        prev.raise_()
        prev.activateWindow()
        return
    editor = panel._main_win._instr_editor
    existing = editor.text()            # parses: _require_run_script checked it
    instr_path = editor.path
    from .parameter_item import ParameterItem
    sheet = system_script.sheet_params([i for i in items if isinstance(i, ParameterItem)])
    import SLiCAP.SLiCAPconfigure as ini
    from . import app_prefs
    dlg = SystemRunDialog(panel._current_path.stem, signals, existing, panel,
                          sheet_params=sheet, csv_dir=ini.csv_path,
                          preset=app_prefs.get_pardefs_preset())
    dlg.setModal(False)

    def _accept():
        import ast
        from .instr_file import bound_names, place
        if panel._main_win is None:
            return
        stem = panel._current_path.stem

        def refuse(why):
            QMessageBox.warning(panel, "System run", why + ": nothing was changed.")

        # Everything is checked against the file as it is NOW (the dialog is
        # non-modal), and BEFORE anything is written: a refusal leaves the
        # file as it was, the header included (a review, 2026-11-21).
        if editor.path != instr_path:
            refuse("Another instruction file was opened while the dialog was open")
            return
        text = editor.text()
        try:
            ast.parse(text)
        except SyntaxError as exc:
            refuse("The instruction file does not parse (line %s: %s)" % (exc.lineno, exc.msg))
            return
        name = dlg.editing()
        if name is None:
            new = dlg.result_name()
            if new in bound_names(text):
                refuse("%s was assigned in the instruction file while the dialog "
                       "was open" % new)
                return
            editor.insert_snippet(dlg.generated_snippet(text))
            return
        # an edited run is replaced where it stands, by the rules of every
        # dialog (instr_file.place, 2026-11-25; the append-only editing was
        # REJECTED for the system run on 2026-11-21). It must still be this
        # diagram's run, unchanged since the dialog opened; otherwise
        # nothing changes: appending would give the double run, and another
        # statement of that name would be lost.
        now = _run_of(text, name, stem)
        if now is None:
            refuse("%s is no longer a run of %s in the instruction file" % (name, stem))
            return
        if now["dump"] != dlg._dump:
            refuse("%s was changed in the instruction file while the dialog was "
                   "open. Open the dialog again" % name)
            return
        # no field changed: the run stays as written, its layout and the
        # comments inside it included
        if not dlg.changed():
            return
        placement = place(text, dlg.generated_snippet(text), [name])
        if placement.problems:
            QMessageBox.warning(panel, "System run", placement.problems[0]
                                + "\n\nNothing was changed.")
            return
        editor.put(placement)

    dlg.accepted.connect(_accept)
    dlg.finished.connect(lambda *_: setattr(panel, "_system_run_dlg", None))
    panel._system_run_dlg = dlg
    dlg.show()
    dlg.raise_()
    dlg.activateWindow()


def _run_of(text, name, stem):
    """The definition of *name* in *text* (instr_file.definition_of) when it
    is a runSystem call of the diagram *stem*, else None."""
    from .instr_file import definition_of, literal
    entry = definition_of(text, name)
    if (entry is not None and entry["func"] == "runSystem" and entry["args"]
            and Path(str(literal(entry["args"][0], ""))).stem == stem):
        return entry
    return None


def _is_run_of(text, name, stem) -> bool:
    """Whether the definition of *name* that wins in *text* is a
    runSystem call of the diagram *stem*."""
    return _run_of(text, name, stem) is not None


class SystemRunDialog(QDialog):
    """The system run instruction: name, run length, stored signals,
    mode (Specs 6.3, 8.3), the parameter values of the run and a
    parameter step (10.4.7: ``params=`` over the sheet's parameter
    table, ``step=`` the step dictionary of the NGspice instruction,
    through the same StepWidget).

    Editing (Anton, 2026-11-21: "Fix the system run dialog so it edits
    R1"): "Edit existing:" lists the runs of THIS diagram in the
    instruction file. The dialog opens on the most recent one, prefills
    every field from it, and OK REPLACES its line in place
    (instr_file.place, InstrEditor.put: since 2026-11-25 the rules of every
    dialog). Its trace set stays. The append-only editing of the other instruction dialogs
    (SLNG.md, 2026-07-08: the regenerated line is appended, the later
    definition wins) was REJECTED for the system run the same day: the
    superseded runSystem line runs as well, so the system simulated twice
    and the second run overwrote the signals file. A new run under a name
    already in use is refused for the same reason."""

    def __init__(self, stem, signals, existing_text="", parent=None,
                 sheet_params=None, csv_dir="", preset="specs"):
        super().__init__(parent, Qt.Window)
        from .instr_file import parse_calls, bound_names
        from .traces_dialog import next_name
        from .step_widget import StepWidget
        self.setWindowTitle("System run")
        self.setMinimumWidth(chars(self, 60))
        self._stem = stem
        self._sheet = dict(sheet_params or {})
        self._existing = existing_text or ""
        form = QFormLayout(self)
        taken = bound_names(self._existing)
        self._taken = taken
        # the runs of THIS diagram, by the script argument ("osc" or
        # "osc.py"): another diagram's run would be re-targeted on OK. A
        # run counts when its definition wins (definition_of): a later
        # "R1 = None" or a chained target makes R1 no run to edit.
        names = []
        for c in parse_calls(self._existing):
            if c["func"] == "runSystem" and c["assigned"] and c["name"] not in names:
                names.append(c["name"])
        self._defined = [d for d in (_run_of(self._existing, n, stem) for n in names) if d]
        self._editing = None
        self._loaded_line = None     # the run line as loaded (changed())
        self._verbatim = {}          # modelled arguments the fields cannot show
        self._extras = []            # arguments the dialog does not model
        self._jit_true = False
        self._load = QComboBox()
        self._load.addItem("(new run)")
        self._load.addItems([c["name"] for c in self._defined])
        form.addRow("Edit existing:", self._load)
        self._name = QLineEdit(next_name("R", taken))
        form.addRow("Result name:", self._name)
        # the stored signals become a top-level trace set, TR1 = R1.traces,
        # where the Axes dialog finds every trace set (Specs 6.9.4); its name
        # is chosen in generated_snippet, from the file as it is at OK
        self._length = QLineEdit("10000")
        self._length.setToolTip("A number of master ticks, or an end time "
                                "in seconds with a unit, e.g. 2.5m")
        form.addRow("Run length:", self._length)
        self._unit = QComboBox()
        self._unit.addItems(["master ticks", "seconds"])
        form.addRow("", self._unit)
        self._signals = QListWidget()
        self._signals.setToolTip("The signals of the diagram: the labels of the "
                                 "wires, or <block>.<output> for a wire without a label")
        # {name: "block.output"} from signal_names, or a list of names: a
        # run may store a labelled output by its <block>.<output> as well,
        # which runSystem accepts
        self._refs = set(signals.values()) if isinstance(signals, dict) else set()
        for name in signals:
            item = QListWidgetItem(name)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            self._signals.addItem(item)
        form.addRow("Store:", self._signals)
        self._missing = QLabel("")
        self._missing.setWordWrap(True)
        self._missing.hide()
        form.addRow("", self._missing)
        self._kept = QLabel("")
        self._kept.setWordWrap(True)
        self._kept.hide()
        self._mode = QComboBox()
        self._mode.addItems(["compiled when possible", "plain Python"])
        form.addRow("Mode:", self._mode)
        self._resume = QCheckBox("Continue from the state file of the last run")
        form.addRow("", self._resume)
        # the values of the run: the parameter-source table of the SLiCAP
        # and NGspice dialogs, system (the sheet's table, read when the run
        # starts), specs or user per parameter, emitted as
        # params=sl.selectPars("<stem>", ...) (Specs 10.4.7; Anton,
        # 2026-11-19: "the same dialog and link to specifications"); one
        # field per parameter was the first form and was REPLACED
        from .par_source_table import ParSourceTable, CIRCUIT, SPECS, USER
        from .design_data_panel import find_spec_csvs
        spec_files = [p.name for p in find_spec_csvs(Path(csv_dir))] if csv_dir else []
        self._spec_files = spec_files
        self._pd = ParSourceTable(self._sheet, (), spec_files, csv_dir, preset,
                                  positions=(CIRCUIT, SPECS, USER),
                                  title="System parameters (params=)",
                                  labels={CIRCUIT: "system"})
        form.addRow(self._pd)
        self._step = StepWidget(list(self._sheet), key_style="ngspice",
                                methods=("lin", "log", "list"), offer_temp=False)
        form.addRow(self._step)
        form.addRow(self._kept)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._check)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)
        self._load.currentIndexChanged.connect(self._on_load_existing)
        if self._defined:
            self._load.setCurrentIndex(len(self._defined))   # the most recent run

    def editing(self):
        """The name of the run being edited in place, or None for a new run."""
        return self._editing

    def result_name(self) -> str:
        """The result name as Python reads it: identifiers are NFKC
        normalised, so "Rµ" (micro sign) IS "Rμ" (mu). Compared raw, a new
        run could redefine an existing one (a review, 2026-11-21)."""
        import unicodedata
        return unicodedata.normalize("NFKC", self._name.text().strip())

    def changed(self) -> bool:
        """Whether a field of the edited run differs from what was loaded."""
        return self._run_line() != self._loaded_line

    # the arguments of runSystem after the script, in the order of its
    # signature (SLiCAPsystem.runSystem), and those the fields show
    _RUN_ARGS = ("ticks", "t_end", "store", "resume", "jit", "results", "stem",
                 "params", "step")
    _MODELLED = ("ticks", "t_end", "store", "resume", "jit", "params", "step")

    def _set_fields_enabled(self, enabled: bool) -> None:
        for w in (self._length, self._unit, self._signals, self._mode,
                  self._resume, self._pd, self._step):
            w.setEnabled(enabled)

    def _on_load_existing(self, idx: int) -> None:
        """Prefill from a run of this diagram, or back to a new run.

        What the fields cannot show EXACTLY is kept as written, its field
        disabled, and a note names it (reviews of 2026-11-21: OK dropped or
        rewrote stem=, results=, jit=True, positional arguments, expressions,
        globals in params=, another spec variable, "all", a step method in
        capitals). A field takes a value only of its own type: anything else
        is kept, so the prefill cannot raise half-way (t_end="2.5m" did, and
        OK then wrote the defaults over the run)."""
        from .instr_file import literal, spec_var_name, quoted
        self._verbatim, self._extras, self._jit_true = {}, [], False
        self._script_src, self._dump = quoted(self._stem), None
        self._set_fields_enabled(True)
        self._pd.load_from_source(None)
        self._step.set_from_dict(None)
        if idx <= 0:
            self._editing = None
            self._name.setReadOnly(False)
            from .traces_dialog import next_name
            self._name.setText(next_name("R", self._taken))
            self._missing.hide()
            self._kept.hide()
            return
        entry = self._defined[idx - 1]
        self._script_src = entry["args"][0]      # "chain", "chain.py", "dir/chain.py"
        self._dump = entry["dump"]
        kw = dict(entry["kwargs"])
        for key, src in zip(self._RUN_ARGS, entry["args"][1:]):
            kw.setdefault(key, src)              # positional, by the signature
        self._extras = [(k, v) for k, v in kw.items() if k not in self._MODELLED]
        absent = object()

        def value(key, fits):
            """The literal of *key* when *fits* accepts it, None when absent;
            anything else is kept as written."""
            src = kw.get(key)
            if src is None:
                return None
            v = literal(src, absent)
            if v is None:
                return None
            if v is absent or not fits(v):
                self._verbatim[key] = src
                return None
            return v

        def number(v):
            return isinstance(v, (int, float)) and not isinstance(v, bool)

        self._editing = entry["name"]
        self._name.setText(entry["name"])
        self._name.setReadOnly(True)             # the edited run keeps its name
        # the run length
        t_end = value("t_end", lambda v: number(v) and v > 0)
        ticks = value("ticks", lambda v: number(v) and float(v).is_integer() and v >= 1)
        if "t_end" in self._verbatim or "ticks" in self._verbatim:
            key = "t_end" if "t_end" in self._verbatim else "ticks"
            self._unit.setCurrentIndex(1 if key == "t_end" else 0)
            self._length.setText(self._verbatim[key])
            self._length.setEnabled(False)
            self._unit.setEnabled(False)
        elif t_end is not None:
            self._unit.setCurrentIndex(1)
            self._length.setText(repr(float(t_end)))
        else:
            self._unit.setCurrentIndex(0)
            self._length.setText(str(int(ticks)) if ticks is not None else "10000")
        # the stored signals
        store = value("store", lambda v: isinstance(v, str) or (
            isinstance(v, (list, tuple)) and all(isinstance(n, str) for n in v)))
        if "store" in self._verbatim:
            self._signals.setEnabled(False)
        store = [store] if isinstance(store, str) else list(store or [])
        names = [self._signals.item(i).text() for i in range(self._signals.count())]
        for n in store:
            if n not in names and n in self._refs:
                item = QListWidgetItem(n)           # a labelled output by block.output
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                self._signals.addItem(item)
                names.append(n)
        for i in range(self._signals.count()):
            item = self._signals.item(i)
            item.setCheckState(Qt.CheckState.Checked if item.text() in store
                               else Qt.CheckState.Unchecked)
        missing = [n for n in store if n not in names]
        self._missing.setText("Not in the diagram any more, dropped on OK: "
                              + ", ".join(missing))
        self._missing.setVisible(bool(missing))
        # mode and continuation
        jit = value("jit", lambda v: v is True or v is False or v == "auto")
        self._jit_true = jit is True
        self._mode.setCurrentIndex(1 if jit is False else 0)
        self._mode.setEnabled("jit" not in self._verbatim)
        resume = value("resume", lambda v: v is True or v is False)
        self._resume.setChecked(resume is True)
        self._resume.setEnabled("resume" not in self._verbatim)
        # the parameter values: only the forms the dialog writes itself, and
        # only when the table then shows them exactly
        params = kw.get("params")
        if params is not None and literal(params, absent) is not None:
            spec_vars = {spec_var_name(f): f for f in self._spec_files}
            # the table writes selectPars("<this diagram>"): only a run of
            # exactly this script may take it, a run of "archive/osc.py"
            # would read another parameter table (a review, 2026-11-21)
            own = literal(self._script_src) == self._stem
            if own and _params_loadable(params, self._sheet, self._stem, spec_vars):
                self._pd.load_from_source(params)
                if not _params_shown(self._pd, params):
                    self._verbatim["params"] = params
            else:
                self._verbatim["params"] = params
            if "params" in self._verbatim:
                self._pd.load_from_source(None)
                self._pd.setEnabled(False)
        # the step: a dict in the widget's own terms
        step = value("step", lambda v: isinstance(v, dict) and v.get("method") in
                     ("lin", "log", "list"))
        if step is not None:
            self._step.set_from_dict(step)
            back = literal(self._step.dict_literal()) if self._step.isChecked() else None
            if back != step:
                # the widget cannot give it back exactly ("num": 3.0, "1m",
                # a limit by name): kept as written (a review, 2026-11-21)
                self._verbatim["step"] = kw["step"]
                self._step.set_from_dict(None)
        self._step.setEnabled("step" not in self._verbatim)
        kept = ["%s=%s" % (k, v) for k, v in self._verbatim.items()]
        kept += ["%s=%s" % kv for kv in self._extras]
        self._kept.setText("Kept as written: " + ", ".join(kept))
        self._kept.setVisible(bool(kept))
        self._loaded_line = self._run_line()

    def params_emission(self):
        """The ``params=`` value, ``sl.selectPars("<stem>", ...)``, or None
        when every parameter keeps the sheet's value."""
        from .instr_file import quoted
        if self._pd.mode() != "select":
            return None
        return self._pd.emission(quoted(self._stem))

    def stored(self) -> list:
        return [self._signals.item(i).text() for i in range(self._signals.count())
                if self._signals.item(i).checkState() == Qt.CheckState.Checked]

    def length_error(self) -> str:
        """Why the run length cannot be used, or "" when it can: a number,
        and at least one master tick. A time typed while the unit stands
        on master ticks ("100u") rounded to ticks=0 and the run stored
        nothing (Anton, 2026-11-17)."""
        from SLiCAP.SLiCAPlex import _scale_float
        if "t_end" in self._verbatim or "ticks" in self._verbatim:
            return ""                            # kept as written
        text = self._length.text().strip()
        try:
            length = _scale_float(text)
        except ValueError:
            return "Run length: not a number: %r" % text
        if self._unit.currentIndex() == 0 and int(round(length)) < 1:
            return ("Run length: %r is less than one master tick. Give a "
                    "number of ticks, or choose the unit seconds." % text)
        if self._unit.currentIndex() == 1 and length <= 0:
            return "Run length: %r is not a positive time." % text
        return ""

    def _check(self):
        import keyword
        name = self.result_name()
        if not name.isidentifier() or keyword.iskeyword(name):
            QMessageBox.warning(self, "System run", "Not a valid name: %r" % name)
            return
        if self._editing is None and name in self._taken:
            QMessageBox.warning(self, "System run",
                                "%s is already in use. To change that run, choose "
                                "it under Edit existing." % name)
            return
        error = self.length_error()
        if error:
            QMessageBox.warning(self, "System run", error)
            return
        if "step" not in self._verbatim and not self._step.is_valid():
            QMessageBox.warning(self, "System run", "The parameter step is incomplete.")
            return
        self._pd.show_reason()
        if "params" not in self._verbatim and not self._pd.is_valid():
            return
        self.accept()

    def _run_line(self) -> str:
        """The runSystem line the fields give (without its trace set and the
        load line of a spec file)."""
        from SLiCAP.SLiCAPlex import _scale_float
        from .instr_file import quoted
        kept = self._verbatim
        if "t_end" in kept:
            arg = "t_end=%s" % kept["t_end"]
        elif "ticks" in kept:
            arg = "ticks=%s" % kept["ticks"]
        else:
            length = _scale_float(self._length.text().strip())
            if self._unit.currentIndex() == 0:
                arg = "ticks=%d" % int(round(length))
            else:
                arg = "t_end=%r" % float(length)
        store = kept.get("store") or repr(self.stored())
        script = self._script_src if self._editing else quoted(self._stem)
        parts = [script, arg, "store=%s" % store]
        if "jit" in kept:
            parts.append("jit=%s" % kept["jit"])
        elif self._mode.currentIndex() == 1:
            parts.append("jit=False")
        elif self._jit_true:
            parts.append("jit=True")
        if "resume" in kept:
            parts.append("resume=%s" % kept["resume"])
        elif self._resume.isChecked():
            parts.append("resume=True")
        params = kept.get("params") or self.params_emission()
        if params:
            parts.append("params=%s" % params)
        step = kept.get("step") or self._step.dict_literal()
        if step:
            parts.append("step=%s" % step)
        parts += ["%s=%s" % kv for kv in self._extras]
        return "%s = sl.runSystem(%s)" % (self.result_name(), ", ".join(parts))

    def generated_snippet(self, text=None) -> str:
        """The run line (with the load line of a spec file before it and its
        trace set after it, when needed), for the instruction file *text*
        (default: the text at open; _accept passes the text at OK). An
        edited run keeps what the fields cannot show as written
        (_on_load_existing), its script argument included."""
        from .instr_file import (trace_set_of, bound_names, assigned_before,
                                 statement_range, quoted)
        from .traces_dialog import next_name
        text = self._existing if text is None else text
        kept = self._verbatim
        name = self.result_name()
        lines = [self._run_line()]
        # the trace set: the run's own when the file has one after it, else
        # a name free in the file as it is now (fixed at open, it could
        # rebind a TR written meanwhile: a review, 2026-11-21)
        has_set = self._editing is not None and trace_set_of(text, name) is not None
        if (self.stored() or "store" in kept) and not has_set:
            free = next_name("TR", bound_names(text) | self._taken | {name})
            lines.append("%s = %s.traces" % (free, name))
        # the spec CSV is loaded once per file into SPECS_<stem>, the load
        # line before its first reader (the NGspice dialog's convention). An
        # edited run stays where it is, so the line must come BEFORE it: a
        # definition further down is too late (a review, 2026-11-21).
        var = None if "params" in kept else self._pd.spec_var()
        if var:
            rng = statement_range(text, self._editing) if self._editing else None
            defined = assigned_before(text, var, rng[0] if rng is not None else len(text))
            if not defined:
                lines.insert(0, "%s = sl.csv2specs(%s)"
                             % (var, quoted(self._pd.spec_file())))
        return "\n".join(lines)


def _params_loadable(src, sheet, stem, spec_vars) -> bool:
    """Whether a ``params=`` source has a form the parameter table shows
    COMPLETELY (ParSourceTable.load_from_source), the forms the dialog
    writes itself: a dict or a list of pairs of literal values, or
    sl.selectPars("<this diagram>"[, SPECS_<a spec file of the project>],
    circuit=[...], specs=[...], user={...}) with literal values. Every name
    must have a row, a parameter of the sheet. Anything else is kept as
    written (reviews of 2026-11-21: a global such as T, another spec
    variable, another diagram, "all" and "circuit" were rewritten or
    dropped on OK). _params_shown checks the table after loading."""
    import ast
    from .instr_file import literal
    rows = set(sheet or {})
    absent = object()
    v = literal(src, absent)
    if v is not absent:
        if isinstance(v, dict):
            return bool(v) and set(map(str, v)) <= rows
        if isinstance(v, (list, tuple)):
            return bool(v) and all(isinstance(p, (list, tuple)) and len(p) == 2
                                   and str(p[0]) in rows for p in v)
        return False
    try:
        node = ast.parse(str(src).strip(), mode="eval").body
    except SyntaxError:
        return False
    if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name) and node.func.value.id == "sl"
            and node.func.attr == "selectPars" and 1 <= len(node.args) <= 2
            and isinstance(node.args[0], ast.Constant) and node.args[0].value == stem):
        return False
    if len(node.args) == 2 and not (isinstance(node.args[1], ast.Name)
                                    and node.args[1].id in spec_vars):
        return False
    for kw in node.keywords:
        try:
            value = ast.literal_eval(kw.value)
        except (ValueError, SyntaxError):
            return False
        if kw.arg in ("circuit", "specs"):
            if not (isinstance(value, (list, tuple)) and set(map(str, value)) <= rows):
                return False
        elif kw.arg == "user":
            if not (isinstance(value, dict) and set(map(str, value)) <= rows):
                return False
        else:
            return False
    return True


def _params_shown(table, src) -> bool:
    """Whether the parameter table, after load_from_source(src), holds
    every name of *src* in the position *src* gives it, and the spec file
    *src* names: the table drops what it cannot take, silently."""
    import ast
    from .instr_file import literal
    from .par_source_table import CIRCUIT, SPECS, USER
    v = literal(src)
    if isinstance(v, dict):
        return all(table.position(str(n)) == USER for n in v)
    if isinstance(v, (list, tuple)):
        return all(table.position(str(p[0])) == USER for p in v)
    node = ast.parse(str(src).strip(), mode="eval").body
    if len(node.args) == 2 and table.spec_var() != node.args[1].id:
        return False
    where = {"circuit": CIRCUIT, "specs": SPECS, "user": USER}
    for kw in node.keywords:
        names = ast.literal_eval(kw.value)
        if any(table.position(str(n)) != where[kw.arg] for n in names):
            return False
    return True


def _project_root(panel):
    path = getattr(panel, "_current_path", None)
    return project.root_for(path) if path else project.project_root()


def _place_class(panel, cls) -> None:
    """Generate (or refresh) the symbol of *cls* in the project's lib/ and
    start placing it."""
    svg_text = symbols.symbol_svg(cls)
    sym = panel.adopt_symbol(cls.__name__, svg_text)
    if sym is None:
        QMessageBox.critical(panel, "Place function",
                             "Could not load the symbol of %s." % cls.__name__)
        return
    panel._scene.start_placement(sym.name, panel._library.svg_bytes(sym.name))


_FILTER_ENTRY = "__filter__"        # the list entry of the designed filter


class PlaceFunctionDialog(QDialog):
    """Choose what to place: a function class, the built-in ones and the
    project's own, or a filter designed from a Laplace result of the
    Design data, the entry "Filter" (Specs 10.3; Anton, 2026-11-17:
    filter design is part of placing a function). OK on that entry
    opens the ``FilterDesignDialog``."""

    def __init__(self, root, parent=None):
        super().__init__(parent, Qt.Window)
        self.setWindowTitle("Place function")
        self.setMinimumWidth(chars(self, 70))
        self._classes = {}
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel("Function (the symbol is generated from it):"))
        self._list = QListWidget()
        lay.addWidget(self._list, 1)
        self._info = QLabel("")
        self._info.setWordWrap(True)
        lay.addWidget(self._info)
        head = QListWidgetItem("-- Design --")
        head.setFlags(Qt.ItemFlag.NoItemFlags)
        self._list.addItem(head)
        self._filter_item = QListWidgetItem(
            "%-12s %s" % ("Filter", "IIR or FIR filter from a Laplace transfer "
                          "function, any order"))
        self._filter_item.setData(Qt.ItemDataRole.UserRole, _FILTER_ENTRY)
        self._list.addItem(self._filter_item)
        own, problems = symbols.project_classes(root)
        self._fill("This project (lib/)", own)
        self._fill("SLiCAP", symbols.builtin_classes())
        if problems:
            lay.addWidget(QLabel("Not loadable from lib/:\n  " + "\n  ".join(problems)))
        self._list.currentItemChanged.connect(self._show)
        self._list.itemDoubleClicked.connect(lambda _: self.accept())
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        lay.addWidget(buttons)

    def _fill(self, title, classes):
        if not classes:
            return
        head = QListWidgetItem("-- %s --" % title)
        head.setFlags(Qt.ItemFlag.NoItemFlags)
        self._list.addItem(head)
        for cls in classes:
            d = symbols.declaration(cls)
            item = QListWidgetItem("%-12s %s" % (d["name"], d["doc"]))
            item.setData(Qt.ItemDataRole.UserRole, d["name"])
            self._classes[d["name"]] = cls
            self._list.addItem(item)

    def filter_selected(self) -> bool:
        item = self._list.currentItem()
        return item is not None and item.data(Qt.ItemDataRole.UserRole) == _FILTER_ENTRY

    def _show(self, item, _previous=None):
        if self.filter_selected():
            self._info.setText("A filter of any order, realised as second-order "
                               "sections in one block; the free symbols of the "
                               "transfer become its parameter pins. OK opens the "
                               "filter design dialog.")
            return
        cls = self.selected_class() if item else None
        if cls is None:
            self._info.setText("")
            return
        d = symbols.declaration(cls)
        self._info.setText(
            "%s function. Inputs: %s. Outputs: %s.%s Parameters: %s."
            % (d["kind"].capitalize(), ", ".join(d["inputs"]) or "none",
               ", ".join(d["outputs"]) or "none",
               " Clock pin." if d["kind"] == "clocked" else "",
               ", ".join(k for k, _ in d["params"]) or "none"))

    def selected_class(self):
        item = self._list.currentItem()
        if item is None:
            return None
        return self._classes.get(item.data(Qt.ItemDataRole.UserRole))


class FilterDesignDialog(QDialog):
    """The design of a filter block (Specs 10.3.1): the text of its
    design file ``lib/<name>.py``, a complete instruction file that
    assigns the design to the block's name with ``createIIR()`` or
    ``createFIR()``.

    A design from a CIRCUIT is a schematic of the project, the
    parameter-source table of the SLiCAP instruction dialog for its
    parameters and the method: the dialog composes the makeCircuit,
    csv2specs, doLaplace and create lines. A row left undefined is not
    substituted and becomes a pin of the block; the rows on circuit,
    specs or user are substituted when the file runs (Anton,
    2026-11-19: "only parameters that have no value can be passed as
    filter design parameters"). The source and detector come from the
    schematic's own definitions; a schematic without them is refused. A
    design from a PROTOTYPE is the one line of the Transfer function
    dialog with a create line. The text stays editable. OK writes the
    file, runs it in a child process and places the block
    (``_place_filter``) or redefines it (``_redefine_filter``). On a
    block, a new name makes a new design for that block alone
    (``_switch_filter``), as Save as of a subcircuit: a copied XT3 block
    becomes XT1 (Anton, 2026-11-19).

    "Copy from:" an instruction file's transfer, with its makeCircuit
    and doLaplace lines, was the previous form and was REPLACED by the
    circuit and the table (Anton, 2026-11-19): the copied line carried
    the instruction's own pardefs ('circuit' substituted the global T, so
    the block lost its T pin). The design as an instruction line of the
    instruction file (step 7) and the lines in the block's symbol with
    IIR/FIR fields in this dialog (step 9, 2026-11-18) were REPLACED by
    the library file (Anton, 2026-11-19). The box shows no example text
    when empty: Anton took a grey example for a suggestion he could not
    accept (2026-11-19)."""

    METHODS = ("bilinear", "zoh", "foh", "impulse", "euler", "backward_diff", "FIR")
    # a non-stationary filter steps exactly over the tick: the input held
    # (zoh, a DAC) or linear between the samples (foh, a sampled analog
    # signal, no half-tick lag; Anton, 2026-11-20)
    METHODS_NON_STATIONARY = ("zoh", "foh")

    def __init__(self, root, parent=None, name=None, text="", taken=(),
                 csv_dir=None, preset=None):
        super().__init__(parent, Qt.Window)
        self.setWindowTitle("Filter design")
        self.setMinimumWidth(chars(self, 72))
        self._root = Path(root)
        self._original = name
        self._taken = set(taken) - {name}
        self._circuit = None                   # (rel path, data) of the chosen circuit
        self._composing = False
        if csv_dir is None:
            import SLiCAP.SLiCAPconfigure as ini
            csv_dir = str(self._root / ini.csv_path)
        if preset is None:
            from . import app_prefs
            preset = app_prefs.get_pardefs_preset()
        self._csv_dir, self._preset = csv_dir, preset
        form = QFormLayout(self)
        self._form = form
        self._fname = QLineEdit(name or _next_design_name(taken))
        self._fname.textEdited.connect(self._compose)
        form.addRow("Block name:", self._fname)
        self._cir = QComboBox()
        self._cir.addItem("none: a prototype, or a file written by hand")
        self._schematics = circuit_schematics(self._root)
        for rel in self._schematics:
            self._cir.addItem(rel)
        self._cir.activated.connect(self._choose_circuit)
        form.addRow("Circuit:", self._cir)
        self._proto = QPushButton("Prototype\u2026")
        self._proto.setToolTip("A classic family, one section by f_0 and Q, or a "
                               "typed expression: the Transfer function dialog")
        self._proto.clicked.connect(self._take_prototype)
        form.addRow("Or a prototype:", self._proto)
        self._pd = None
        self._pd_row = QWidget()
        self._pd_box = QVBoxLayout(self._pd_row)
        self._pd_box.setContentsMargins(0, 0, 0, 0)
        form.addRow(self._pd_row)
        self._pd_row.hide()
        self._method = QComboBox()
        self._method.addItems(self.METHODS)
        self._method.currentIndexChanged.connect(self._compose)
        form.addRow("Method:", self._method)
        # the kind of the coefficients (Specs 15.3): stationary, a digital
        # filter with fixed numbers for its own sample period; non-stationary,
        # the implementation of an analog filter, following the actual clock
        self._kind = QComboBox()
        self._kind.addItems(["stationary", "non-stationary"])
        self._kind.setToolTip("stationary: fixed coefficients, a digital filter; "
                              "non-stationary: the coefficients follow the actual "
                              "clock, the implementation of an analog filter")
        self._kind.currentIndexChanged.connect(self._kind_changed)
        form.addRow("Coefficients:", self._kind)
        self._ts = QLineEdit()
        self._ts.setPlaceholderText("required: a value (10n) or the name of a parameter pin")
        self._ts.setToolTip("The sample period a stationary filter is designed "
                            "for: a value in seconds, SLiCAP notation (10n), or "
                            "the name of a parameter pin of the block, which a "
                            "constant or a parent block sets in the run")
        self._ts.textEdited.connect(self._compose)
        form.addRow("Sample period:", self._ts)
        self._text = CodeEditor(text)
        self._text.setPlaceholderText("choose a circuit, or press Prototype\u2026")
        self._text.setMinimumHeight(chars(self, 8))
        form.addRow("Design file:", self._text)
        hint = QLabel("The text is the design file lib/<name>.py, run by the run "
                      "script at the start of every run. Its last line makes the "
                      "design: sl.createIIR(H, method=..., name=...) or "
                      "sl.createFIR(H, length=64, window=\"hamming\", name=...), "
                      "with stationary=False for coefficients that follow the "
                      "clock and Ts=... for a stationary filter's own sample "
                      "period, a value or the name of a parameter pin. A "
                      "parameter left undefined in the table is not "
                      "substituted and becomes a pin of the block. OK runs the "
                      "file once now."
                      + (" The same name redefines every %s block. A new name "
                         "makes a new design for this block only." % name
                         if name else ""))
        hint.setWordWrap(True)
        form.addRow(hint)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._check)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)
        if text:
            self._read_back(text)

    # -- the circuit and its table ------------------------------------------

    def _choose_circuit(self, index):
        """The circuit at *index* of the list: build it, show its table,
        compose the text. Index 0, a failure or a schematic without
        source and detector leaves no circuit."""
        rel = self._schematics[index - 1] if 0 < index <= len(self._schematics) else None
        self._set_circuit(rel)
        if self._circuit is not None:
            self._compose()

    def _set_circuit(self, rel) -> None:
        self._circuit = None
        if self._pd is not None:
            self._pd_box.removeWidget(self._pd)
            self._pd.deleteLater()
            self._pd = None
        self._pd_row.hide()
        if rel is None:
            self._cir.setCurrentIndex(0)
            return
        try:
            data = circuit_data(self._root, rel)
        except (Exception, SystemExit) as exc:
            QMessageBox.critical(self, "Filter design",
                                 "The circuit could not be built from %s:\n\n%s"
                                 % (rel, exc))
            self._cir.setCurrentIndex(0)
            return
        if not _defined(data["source"]) or not _defined(data["detector"]):
            QMessageBox.warning(self, "Filter design",
                                "%s defines no source and detector. Add them to the "
                                "schematic: the design is its transfer from the "
                                "source to the detector." % rel)
            self._cir.setCurrentIndex(0)
            return
        from .par_source_table import ParSourceTable
        from .design_data_panel import find_spec_csvs
        spec_files = [p.name for p in find_spec_csvs(Path(self._csv_dir))]
        self._pd = ParSourceTable(data["par_defs"], data["undefined_params"],
                                  spec_files, self._csv_dir, self._preset)
        self._pd.changed.connect(self._compose)
        self._pd_box.addWidget(self._pd)
        self._pd_row.show()
        self._circuit = (rel, data)
        self._cir.setCurrentText(rel)

    def stationary(self) -> bool:
        return self._kind.currentIndex() == 0

    def sample_period(self):
        """The typed sample period: a float, the name of a parameter pin
        (an identifier) or None when empty; raises ValueError for a
        text that is neither."""
        from SLiCAP.SLiCAPlex import _scale_float
        text = self._ts.text().strip()
        if not text:
            return None
        if text.isidentifier():
            return text
        try:
            value = float(_scale_float(text))
        except (TypeError, ValueError):
            raise ValueError("Sample period: %r is not a number and not the name "
                             "of a parameter" % text) from None
        return value

    def _kind_changed(self, *_):
        """The method list follows the kind: every method of the sections
        for a stationary filter, zoh or foh for a non-stationary one."""
        methods = self.METHODS if self.stationary() else self.METHODS_NON_STATIONARY
        current = self._method.currentText()
        self._method.blockSignals(True)
        self._method.clear()
        self._method.addItems(methods)
        self._method.setCurrentText(current if current in methods else methods[0])
        self._method.blockSignals(False)
        self._ts.setEnabled(self.stationary())
        self._compose()

    def _create_args(self):
        """``(kind, method, stationary, Ts)`` for ``design_file_text``."""
        method = self._method.currentText()
        try:
            ts = self.sample_period() if self.stationary() else None
        except ValueError:
            ts = None
        return ("FIR" if method == "FIR" else "IIR", method, self.stationary(), ts)

    def _compose(self, *_):
        """Rewrite the text from the circuit, the table and the method.
        Without a circuit, a prototype or a hand-written text, only the
        create line is rewritten from the method, the kind and the
        sample period (``with_create_line``): the dialog owns that line
        in every case (Anton, 2026-11-20: the typed period was lost for
        a prototype)."""
        if self._composing:
            return
        if self._circuit is None:
            from .system_script import with_create_line
            kind, method, stationary, ts = self._create_args()
            text = with_create_line(self._text.text(), self.name(), kind,
                                    method, stationary=stationary, Ts=ts)
            if text is not None and text != self._text.text():
                self._text.setPlainText(text)
            return
        from .system_script import design_file_text
        from .instr_file import quoted
        rel, _data = self._circuit
        cir_var = Path(rel).stem
        if not cir_var.isidentifier():
            cir_var = "cir"
        lines = ["%s = sl.makeCircuit(%s)" % (cir_var, quoted(rel))]
        var = self._pd.spec_var()
        if var:
            lines.append("%s = sl.csv2specs(%s)"
                         % (var, quoted(self._pd.spec_file())))
        pardefs = self._pd.emission(cir_var)
        lines.append("H = sl.doLaplace(%s%s)" % (
            cir_var, ", pardefs=%s" % pardefs if pardefs is not None else ""))
        kind, method, stationary, ts = self._create_args()
        self._text.setPlainText(design_file_text(
            self.name(), "\n".join(lines), "H", kind, method,
            stationary=stationary, Ts=ts))

    def _read_back(self, text) -> None:
        """The circuit, the table and the method from the text of an
        existing design file, for Design...: its makeCircuit, doLaplace
        and create lines (instr_file.parse_calls). A file of another
        shape shows its text with no circuit."""
        from .instr_file import parse_calls
        self._composing = True
        try:
            calls = parse_calls(text)
            make = next((c for c in calls if c["func"] == "makeCircuit" and c["args"]), None)
            if make is not None:
                try:
                    rel = ast.literal_eval(make["args"][0])
                except (ValueError, SyntaxError):
                    rel = None
                if isinstance(rel, str) and rel in self._schematics:
                    self._set_circuit(rel)
                    lap = next((c for c in calls if c["func"] == "doLaplace"), None)
                    if self._pd is not None and lap is not None:
                        self._pd.load_from_source(lap["kwargs"].get("pardefs"))
            create = next((c for c in calls if c["func"] in ("createIIR", "createFIR")), None)
            if create is not None:
                def lit(key, default):
                    try:
                        return ast.literal_eval(create["kwargs"].get(key, repr(default)))
                    except (ValueError, SyntaxError):
                        return default
                self._kind.setCurrentIndex(0 if lit("stationary", True) else 1)
                self._kind_changed()                 # the method list of the kind
                if create["func"] == "createFIR":
                    self._method.setCurrentText("FIR")
                else:
                    method = lit("method", "")
                    if self._method.findText(method) >= 0:
                        self._method.setCurrentText(method)
                ts = lit("Ts", None)
                self._ts.setText("" if ts is None else
                                 ts if isinstance(ts, str) else repr(float(ts)))
        finally:
            self._composing = False
        self._text.setPlainText(text)             # the file's own text, as it is

    def _take_prototype(self):
        from .transfer_function_dialog import TransferFunctionDialog
        from .system_script import design_file_text
        dlg = TransferFunctionDialog(self._text.text(), self)
        if dlg.exec():
            line = dlg.generated_snippet()
            self._set_circuit(None)
            kind, method, stationary, ts = self._create_args()
            self._text.setPlainText(design_file_text(
                self.name(), line, line.split("=", 1)[0].strip(), kind, method,
                stationary=stationary, Ts=ts))

    # -- the result ------------------------------------------------------------

    def name(self) -> str:
        return self._fname.text().strip()

    def text(self) -> str:
        return self._text.text().strip() + "\n"

    def circuit(self):
        """The project-relative schematic of the design, or None."""
        return self._circuit[0] if self._circuit else None

    def error(self) -> str:
        """Why the fields cannot define a design, or ""."""
        from .instr_file import bound_names
        name = self.name()
        if not name.isidentifier():
            return "Not a valid block name: %r" % name
        if name in self._taken:
            return ("%s is already a design or symbol of this sheet. Pick "
                    "another name, or open Design\u2026 of an %s block to "
                    "change that design." % (name, name))
        if not self._text.text().strip():
            return "Give the design file: the instructions that make the design."
        if self.stationary():
            try:
                if self.sample_period() is None:
                    return ("Sample period: a stationary filter is designed for "
                            "its own sample period; give it.")
            except ValueError as exc:
                return str(exc)
        if name not in bound_names(self._text.text()):
            return ("The file does not assign %s; its last line is %s = "
                    "sl.createIIR(...) or sl.createFIR(...)." % (name, name))
        return ""

    def _check(self):
        error = self.error()
        if error:
            QMessageBox.warning(self, "Filter design", error)
            return
        self.accept()


def _next_design_name(taken) -> str:
    taken = set(taken)
    n = 1
    while "FILTER%d" % n in taken:
        n += 1
    return "FILTER%d" % n


def circuit_schematics(root) -> list:
    """The SLiCAP schematics of the project (sch/ and lib/,
    ``project.project_schematics``) as paths relative to *root*: what
    the filter design dialog offers as the circuit of a design."""
    from .dialects import SLICAP
    out = []
    for path in project.project_schematics(root):
        if path.suffix == SLICAP.sch_ext:
            out.append(path.relative_to(root).as_posix())
    return out


def _defined(ref) -> bool:
    """Whether a source or detector of a circuit is set: the pair
    ``[name, None]`` or ``[name, name]``, not ``[None, None]`` or None."""
    return bool(ref) and any(r is not None for r in ref)


def circuit_data(root, rel) -> dict:
    """``window.circuit_data``: the circuit built from the schematic
    *rel* of the project at *root*, for the parameter-source table of
    the filter design dialog. Here so that a test can replace it."""
    from .window import circuit_data as _circuit_data
    return _circuit_data(root, rel)


def _on_place_function(panel) -> None:
    root = _project_root(panel)
    dlg = PlaceFunctionDialog(root, panel)
    if not dlg.exec():
        return
    if dlg.filter_selected():
        # the design has a dialog of its own, opened by OK on the entry
        # "Filter" (Anton, 2026-11-18)
        design = FilterDesignDialog(root, panel, taken=panel._library.names)
        if design.exec():
            _place_filter(panel, design.name(), design.text())
    elif dlg.selected_class() is not None:
        _place_class(panel, dlg.selected_class())


def _filter_doc(name, found) -> str:
    """The description of a filter symbol from the probe's report: the
    kind, the method or the taps and window, the parameters."""
    if found.get("kind") == "FIR":
        how = "%s taps, %s" % (found.get("length"), found.get("window"))
    elif not found.get("stationary", True):
        how = "non-stationary, %s" % (found.get("method") or "zoh")
    else:
        how = found.get("method")
    if found.get("Ts") and found.get("stationary", True):
        ts = found["Ts"]
        how = "%s, Ts %s" % (how, ts if isinstance(ts, str) else _si(float(ts), "s"))
    controls = list(found.get("params", []))
    return "%s filter %s (%s)%s" % (
        found.get("kind", "IIR"), name, how,
        ", parameters " + ", ".join(controls) if controls else "")


def design_file_of(panel, name):
    """The library file of the sheet that assigns the design *name*
    (``instr_file.bound_names`` on each entry of the library block),
    relative to the project root, or ``lib/<name>.py`` when no entry
    does: the file Design… opens and the dialog writes."""
    from .instr_file import bound_names
    from .system_script import library_files
    root = _project_root(panel)
    block = panel._scene.library_block()
    for file in library_files([block] if block else []):
        try:
            text = (root / file).read_text(encoding="utf-8")
        except OSError:
            continue
        if name in bound_names(text):
            return file
    return "lib/%s.py" % name


def _define_filter(panel, name, text, file=None):
    """Write the design *text* to the library *file* of *name*
    (``lib/<name>.py`` by default), run it (``probe_design``), write
    the block's symbol from what it reports (the parameter pins) and from
    the text (the schematic for the descent, ``design_schematic``) and
    list the file in the sheet's library block. Returns the loaded symbol, or None after a message
    (the file keeps the text: the user corrects it in the dialog)."""
    from .netlist import NetlistError
    from .system_script import probe_design, design_schematic, IMPORT_DIRECTIVE
    root = _project_root(panel)
    file = file or "lib/%s.py" % name
    path = root / file
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    try:
        found = probe_design(root, file, name)
    except NetlistError as exc:
        QMessageBox.critical(panel, "Filter design", "\n".join(exc.errors))
        return None
    controls = list(found.get("params", []))
    sym = panel.adopt_symbol(name, symbols.filter_symbol_svg(
        name, controls, _filter_doc(name, found), design_schematic(text) or ""))
    if sym is None:
        QMessageBox.critical(panel, "Filter design",
                             "Could not load the symbol of %s." % name)
        return None
    panel._ensure_library_include(path, IMPORT_DIRECTIVE)
    return sym


def _place_filter(panel, name, text) -> None:
    """Define the design *name* from *text* and start placing its block
    (Specs 10.3.3; filter design is part of placing a function, Anton,
    2026-11-17)."""
    sym = _define_filter(panel, name, text)
    if sym is not None:
        panel._scene.start_placement(sym.name, panel._library.svg_bytes(sym.name))


def _edit_filter(panel, item) -> None:
    """Design... of the Properties dialog of a filter block: the design
    dialog on the file of its design; OK rewrites the file and
    redefines every block of that design."""
    name = item.symbol.name
    file = design_file_of(panel, name)
    try:
        text = (_project_root(panel) / file).read_text(encoding="utf-8")
    except OSError:
        text = ""
    dlg = FilterDesignDialog(_project_root(panel), panel, name=name, text=text,
                             taken=panel._library.names)
    if not dlg.exec():
        return
    if dlg.name() == name:
        _redefine_filter(panel, name, dlg.text(), file)
    else:
        _switch_filter(panel, item, dlg.name(), dlg.text())


def _switch_filter(panel, item, name, text) -> None:
    """Make the new design *name* from *text* (its file lib/<name>.py,
    symbol and library entry) and give it to the block *item* alone;
    the other blocks of the old design stay. The wiring is kept, which
    the user checks when the pins differ."""
    old = item.symbol
    sym = _define_filter(panel, name, text)
    if sym is None:
        return
    _take_design_symbol(item, sym)
    panel._scene._sync_junctions()
    panel._dirty = True
    if list(old.nodes) != list(sym.nodes):
        QMessageBox.information(
            panel, "Filter design",
            "The pins of %s differ from those of %s: %s. Check the wiring of "
            "%s and save." % (name, old.name, ", ".join(sym.nodes), item.instance_id))
    panel._status("%s is now the design %s." % (item.instance_id, name))


def _redefine_filter(panel, name, text, file=None) -> None:
    """Rewrite the design file of *name*, regenerate its symbol and
    reload every block under it; the blocks keep their wiring, which
    the user checks when the pins changed."""
    old = panel._library.symbol(name)
    sym = _define_filter(panel, name, text, file)
    if sym is None:
        return
    for comp in panel._scene.items():
        if isinstance(comp, ComponentItem) and comp.symbol_name == name:
            _take_design_symbol(comp, sym)
    panel._scene._sync_junctions()
    panel._dirty = True
    if old is not None and list(old.nodes) != list(sym.nodes):
        QMessageBox.information(
            panel, "Filter design",
            "The pins of %s changed: %s. Check the wiring of its blocks and save."
            % (name, ", ".join(sym.nodes)))
    panel._status("Design %s redefined." % name)


class NewFunctionDialog(QDialog):
    """The declaration of a new function class: name, kind, pins, order."""

    def __init__(self, root, parent=None):
        super().__init__(parent, Qt.Window)
        self.setWindowTitle("New function")
        self.setMinimumWidth(chars(self, 60))
        self._root = Path(root)
        form = QFormLayout(self)
        self._name = QLineEdit()
        self._name.setPlaceholderText("ClassName, also the file lib/ClassName.py")
        form.addRow("Name:", self._name)
        self._kind = QComboBox()
        self._kind.addItems(["clocked", "algebraic"])
        form.addRow("Kind:", self._kind)
        self._inputs = QLineEdit("x")
        form.addRow("Inputs:", self._inputs)
        self._outputs = QLineEdit("y")
        form.addRow("Outputs:", self._outputs)
        self._params = QLineEdit()
        self._params.setPlaceholderText("constructor parameters, e.g. k, n")
        form.addRow("Parameters:", self._params)
        self._order = QSpinBox()
        self._order.setRange(0, 100000)
        self._order.setValue(1)
        form.addRow("State length (clocked):", self._order)
        self._kind.currentTextChanged.connect(
            lambda text: self._order.setEnabled(text == "clocked"))
        note = QLabel("Pins and parameters are names separated by spaces or "
                      "commas. The file gets the kernels with the right "
                      "signatures; the arithmetic is written in an editor.")
        note.setWordWrap(True)
        form.addRow(note)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._check)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    @staticmethod
    def _names(text):
        return [t for t in text.replace(",", " ").split() if t]

    def _check(self):
        name = self._name.text().strip()
        names = (self._names(self._inputs.text()) + self._names(self._outputs.text())
                 + self._names(self._params.text()))
        bad = [n for n in [name] + names if not n.isidentifier()]
        if not name or bad:
            QMessageBox.warning(self, "New function",
                                "Not a valid Python name: %s" % ", ".join(bad or ["(empty)"]))
            return
        if (self._root / "lib" / (name + ".py")).exists():
            QMessageBox.warning(self, "New function",
                                "lib/%s.py exists already. Place it, or choose "
                                "another name." % name)
            return
        if not self._names(self._outputs.text()):
            QMessageBox.warning(self, "New function", "A function needs an output.")
            return
        self.accept()

    def write(self) -> Path:
        """Write lib/<Name>.py and return its path."""
        name = self._name.text().strip()
        kind = self._kind.currentText()
        text = symbols.scaffold(name, kind, self._names(self._inputs.text()),
                                self._names(self._outputs.text()),
                                self._order.value() if kind == "clocked" else 0,
                                self._names(self._params.text()))
        libdir = self._root / "lib"
        libdir.mkdir(parents=True, exist_ok=True)
        path = libdir / (name + ".py")
        path.write_text(text, encoding="utf-8")
        return path


def _on_new_function(panel) -> None:
    root = _project_root(panel)
    dlg = NewFunctionDialog(root, panel)
    if not dlg.exec():
        return
    path = dlg.write()
    cls = symbols.class_named(path.stem, root)
    if cls is None:
        QMessageBox.critical(panel, "New function",
                             "lib/%s was written but could not be imported." % path.name)
        return
    panel._status("Wrote lib/%s: fill in the kernels in an editor." % path.name)
    _place_class(panel, cls)


# ---- the hierarchical block: its diagram lib/<name>.system_sch alone ----------
# The declaration file lib/<name>.system_lib with a .subckt line, read by
# the Place dialog and written by Save as hierarchical block, was REMOVED
# (Anton, 2026-11-19): a second authority for the ports and parameters,
# which the diagram's document properties hold (subcircuit.
# schematic_subckt_def); the run script never read it, it flattens the
# diagram. Dialect.lib_ext None states it.


# ---- the signal source -------------------------------------------------------------

_SIGNAL_FIXED = ("waveform", "offset", "delay")     # the symbol's own parameters
# one of the two, chosen with a radio button (Anton, 2026-11-17)
_SIGNAL_EITHER = {"noise": ("sigma", "density"), "pwl": ("points", "path")}
_SIGNAL_HELP = {
    "step": "offset before the delay, offset + amplitude from then on",
    "ramp": "offset + slope * (t - delay)",
    "sine": "amplitude * sin(2 pi frequency (t - delay) + phase), phase in degrees",
    "square": "+amplitude for the duty part of every period, -amplitude for the rest",
    "triangle": "between -amplitude and +amplitude, rising from zero",
    "chirp": "a sine whose frequency rises from f_start to f_end in duration seconds",
    "noise": "white noise: the level as sigma (RMS per sample) or density (V^2/Hz), "
             "gaussian or uniform, the same seed gives the same sequence",
    "pwl": "piecewise linear through points, (t, y) pairs, or a text file "
           "(time in column 0, the value in the given column); the run ends "
           "at the last point",
}


def edit_signal(item, parent=None, on_accept=None) -> bool:
    """Open the Signal dialog for the signal source *item* and, on OK,
    write the waveform and its parameters into it and redraw its labels.
    ONE entry point for the Properties dialog's button and the canvas
    (a double-click on a parameter label). *on_accept* is called after OK
    and before the item changes: the scene records its undo step there.
    Returns True when the item changed."""
    dlg = SignalDialog(item.params, item.prop_display,
                       title="Signal - %s" % item.instance_id, parent=parent)
    if not dlg.exec():
        return False
    if on_accept is not None:
        on_accept()
    dlg.apply()
    item._save_label_offsets()
    item.update_labels()
    return True


class SignalDialog(QDialog):
    """The waveform of a signal source and its parameters: the fields of
    the chosen waveform from ``WAVEFORMS``, offset and delay for all.
    Values are texts in SLiCAP notation ("10k"), written into the
    block's parameters by ``apply()``; the parameters of the other
    waveforms are removed."""

    def __init__(self, params, prop_display=None, title="Signal", parent=None):
        super().__init__(parent, Qt.Window)
        from SLiCAP.SLiCAPsystem import WAVEFORMS
        from PySide6.QtWidgets import QStackedWidget, QWidget, QPushButton, QHBoxLayout
        self._params = params
        self._prop_display = prop_display
        self._table = WAVEFORMS
        self.setWindowTitle(title)
        self.setMinimumWidth(chars(self, 56))
        form = QFormLayout(self)
        self._waveform = QComboBox()
        self._waveform.addItems(list(WAVEFORMS))
        form.addRow("Waveform:", self._waveform)
        self._help = QLabel("")
        self._help.setWordWrap(True)
        form.addRow("", self._help)
        self._offset = QLineEdit(params.get("offset", "0"))
        form.addRow("Offset:", self._offset)
        self._delay = QLineEdit(params.get("delay", "0"))
        self._delay.setToolTip("time [s] at which the waveform starts")
        form.addRow("Delay [s]:", self._delay)
        from PySide6.QtWidgets import QRadioButton, QButtonGroup
        self._stack = QStackedWidget()
        self._edits = {}
        self._choice = {}             # waveform -> {key: QRadioButton}
        for name, fields in WAVEFORMS.items():
            page = QWidget()
            grid = QFormLayout(page)
            grid.setContentsMargins(0, 0, 0, 0)
            edits = {}
            either = _SIGNAL_EITHER.get(name, ())
            group = QButtonGroup(page)
            radios = {}
            for key, default in fields.items():
                if name == "noise" and key == "distribution":
                    w = QComboBox()
                    w.addItems(["gaussian", "uniform"])
                    w.setCurrentText(params.get(key, default))
                    field = w
                elif name == "pwl" and key == "path":
                    w = QLineEdit(params.get(key, ""))
                    field = QWidget()
                    lay = QHBoxLayout(field)
                    lay.setContentsMargins(0, 0, 0, 0)
                    lay.addWidget(w, 1)
                    btn = QPushButton("Browse…")
                    btn.clicked.connect(lambda _=False, e=w: self._browse(e))
                    lay.addWidget(btn)
                else:
                    w = QLineEdit(params.get(key, "" if default is None
                                             else str(default)))
                    if default is None and key not in either:
                        w.setPlaceholderText("required")
                    field = w
                if key in either:
                    radio = QRadioButton(key + ":")
                    group.addButton(radio)
                    radios[key] = radio
                    radio.toggled.connect(field.setEnabled)
                    grid.addRow(radio, field)
                else:
                    grid.addRow(key + ":", field)
                edits[key] = w
            if radios:
                # the one that has a value, else the first
                chosen = next((k for k in either if params.get(k, "").strip()), either[0])
                for key, radio in radios.items():
                    radio.setChecked(key == chosen)
                    edits[key].setEnabled(key == chosen)
            self._choice[name] = radios
            self._edits[name] = edits
            self._stack.addWidget(page)
        form.addRow(self._stack)
        self._waveform.currentIndexChanged.connect(self._stack.setCurrentIndex)
        self._waveform.currentTextChanged.connect(
            lambda name: self._help.setText(_SIGNAL_HELP.get(name, "")))
        current = params.get("waveform", "").strip()
        self._waveform.setCurrentText(current if current in WAVEFORMS else "sine")
        self._help.setText(_SIGNAL_HELP.get(self._waveform.currentText(), ""))
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._check)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def _browse(self, edit):
        from PySide6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(self, "Signal file", edit.text(),
                                              "Text files (*.txt *.csv *.dat);;All files (*)")
        if path:
            edit.setText(path)

    def values(self) -> dict:
        """The parameters as the block gets them: waveform, offset, delay
        and the non-empty fields of the waveform."""
        name = self._waveform.currentText()
        out = {"waveform": name, "offset": self._offset.text().strip() or "0",
               "delay": self._delay.text().strip() or "0"}
        radios = self._choice.get(name, {})
        for key, w in self._edits[name].items():
            if key in radios and not radios[key].isChecked():
                continue                          # the other one of the two
            text = w.currentText() if isinstance(w, QComboBox) else w.text().strip()
            if text:
                out[key] = text
        return out

    def _check(self):
        v = self.values()
        name = v["waveform"]
        fields = self._table[name]
        radios = self._choice.get(name, {})
        chosen = [k for k, r in radios.items() if r.isChecked()]
        missing = [k for k, d in fields.items() if d is None and k not in v
                   and (k in chosen or k not in radios)]
        if missing:
            QMessageBox.warning(self, "Signal", "%s: missing %s."
                                % (name, ", ".join(missing)))
            return
        self.accept()

    def apply(self) -> None:
        """Write the values into the block's parameters; the parameters of
        the other waveforms go. A new parameter shows its name and value
        on the canvas, as the symbol's own parameters do."""
        v = self.values()
        others = {k for fields in self._table.values() for k in fields}
        for key in list(self._params):
            if key in others and key not in v:
                del self._params[key]
                if self._prop_display is not None:
                    self._prop_display.pop(key, None)
        for key, text in v.items():
            self._params[key] = text
            if self._prop_display is not None and key not in self._prop_display:
                self._prop_display[key] = (True, True)
