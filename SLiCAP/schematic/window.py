import importlib
import re
import os
from pathlib import Path
from datetime import date as _date

from PySide6.QtWidgets import (
    QMainWindow, QDockWidget, QWidget, QFileDialog, QMessageBox,
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QMenuBar,
)
from PySide6.QtCore import Qt, QEvent, QTimer
from PySide6.QtGui import QAction, QKeySequence

import SLiCAP.SLiCAPconfigure as ini
from .canvas import SchematicScene, SchematicView
from .symbol_library import SymbolLibrary
from .schematic_data import DocumentProperties
from . import project

_SLICAP_SVG        = Path(__file__).parent.parent / "files" / "symbols" / "slicap"  / "Symbols.svg"
_SLICAP_DIR        = _SLICAP_SVG.parent
_NGSPICE_SVG       = Path(__file__).parent.parent / "files" / "symbols" / "ngspice" / "Symbols.svg"

_FILTER_SLICAP      = "SLiCAP Schematic (*.slicap_sch)"
_FILTER_NGSPICE     = "NGspice Schematic (*.spice_sch)"
_FILE_FILTER        = f"{_FILTER_SLICAP};;{_FILTER_NGSPICE};;All Files (*)"
_NET_FILTER_SLICAP  = "SLiCAP Netlist (*.cir);;All Files (*)"
_NET_FILTER_NGSPICE = "NGspice Netlist (*.sp);;All Files (*)"


# ---------------------------------------------------------------------------
# NGspice availability — external SPICE tools are deprecated except NGspice;
# check it is present before drawing NGspice circuits / defining simulations.
# ---------------------------------------------------------------------------

def _ngspice_available() -> bool:
    """True when the configured ``ngspice`` command exists and is runnable."""
    import os
    import shutil
    import SLiCAP.SLiCAPconfigure as ini
    cmd = (getattr(ini, "ngspice", "") or "").strip()
    if not cmd:
        return False
    return bool(shutil.which(cmd)) or os.path.isfile(cmd)


def _locate_ngspice(parent) -> bool:
    """File-pick the NGspice executable and save it to the main config; return
    True once a runnable command is configured."""
    import os
    import SLiCAP.SLiCAPconfigure as ini
    start = ""
    for cand in ini._ngspice_std_locations():
        if os.path.isdir(os.path.dirname(cand)):
            start = os.path.dirname(cand)
            break
    fn, _ = QFileDialog.getOpenFileName(
        parent, "Locate the NGspice executable", start,
        "NGspice (ngspice*);;All files (*)")
    if not fn:
        return False
    cfg = ini._read_main_config()
    if not cfg.has_section("commands"):
        cfg.add_section("commands")
    cfg.set("commands", "ngspice", fn)
    ini._write_main_config(cfg)
    ini.ngspice = fn                     # live update for this GUI process
    return _ngspice_available()


def _check_ngspice(parent) -> bool:
    """Return True to proceed. When NGspice is not available, warn and offer to
    locate it, continue without it, or cancel the action."""
    if _ngspice_available():
        return True
    box = QMessageBox(
        QMessageBox.Icon.Warning, "NGspice not found",
        "NGspice was not found. You can still draw the schematic and define "
        "instructions, but running an NGspice simulation needs the 'ngspice' "
        "command.\n\nNGspice is often not on the PATH — on Windows it is an "
        "unpacked zip (typically C:\\Spice64\\bin\\ngspice_con.exe). Locate it "
        "now, or set it later via File → Edit main configuration file.",
        parent=parent)
    b_locate = box.addButton("Locate NGspice…",
                             QMessageBox.ButtonRole.ActionRole)
    b_cont = box.addButton("Continue anyway", QMessageBox.ButtonRole.AcceptRole)
    box.addButton(QMessageBox.StandardButton.Cancel)
    box.exec()
    clicked = box.clickedButton()
    if clicked is b_locate:
        return _locate_ngspice(parent) or _check_ngspice(parent)
    return clicked is b_cont


# ---------------------------------------------------------------------------
# CanvasPanel — one schematic canvas with its own embedded menu bar
# ---------------------------------------------------------------------------

def instruction_run_context(instr_path, schematic_path=None,
                            schematic_project=""):
    """Where an instruction file runs, and under which project name.

    The project is the one the INSTRUCTION FILE lives in - never whichever
    schematic happens to be open. It used to come from the open schematic
    (``project.project_root()``, derived from the app-wide current
    schematic), so running a file belonging to another project wrote
    ``main.py`` into the OLD project and ran it there; ``main.py`` then
    imported a module that was not next to it and the run died with
    ``ModuleNotFoundError`` (Anton, 2026-08-03). ``main.py`` imports the
    instruction file, so it belongs beside it, and that settles the working
    directory too.

    The schematic's project NAME is used only when that schematic belongs to
    the same project; otherwise the file's own stem names the project.
    """
    root = project.root_for(instr_path)
    if schematic_path is not None and schematic_project:
        try:
            same = project.root_for(schematic_path).resolve() == root.resolve()
        except OSError:
            same = False
        if same:
            return root, schematic_project
    return root, Path(instr_path).stem


class CanvasPanel(QWidget):
    """A schematic canvas (SLiCAP or NGspice) with its own embedded menu bar.

    The menu bar lives INSIDE this widget so it is visible whether the panel
    is docked or floating.  The instruction editor and log panel are shared
    resources owned by MainWindow; CanvasPanel delegates run/stop and
    instruction-loading to its ``main_win`` reference."""

    def __init__(self, sch_type: str, config: str | None = None,
                 main_win: "MainWindow | None" = None,
                 schematic_only: bool = False):
        super().__init__()
        self._sch_type   = sch_type
        self._config     = config
        self._main_win   = main_win
        self._schematic_only = schematic_only

        self._scene: SchematicScene | None = None
        self._view:  SchematicView  | None = None
        self._current_path: Path | None = None
        self._doc_props = DocumentProperties.new()
        self._dirty = False
        self._library = None
        self._symbol_loop_name: str | None = None
        # This panel's own drawing style — a new schematic starts from the
        # style.ini defaults; _load_file replaces it with the file's sidecar
        # style.  Items resolve it through the scene (config.style_of), so
        # open schematics never share style state.
        from .config import Style
        self._style: Style = Style()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Always create an embedded menu bar for the canvas. In schematic-only
        # mode the MainWindow's menuBar() is hidden, but the CanvasPanel's
        # internal menu provides the editing commands and should remain visible.
        self._menu_bar = QMenuBar(self)
        try:
            self._menu_bar.setNativeMenuBar(False)
        except Exception:
            pass
        layout.addWidget(self._menu_bar)
        self._menu_bar.setVisible(True)
        # Using a panel's menu makes it the active context even when keyboard
        # focus stays elsewhere (see _activate_context).
        self._menu_bar.installEventFilter(self)

        self._init_canvas(sch_type)
        self._build_library()
        self._build_menu()

    # -- canvas init ----------------------------------------------------------

    def _init_canvas(self, sch_type: str) -> None:
        if self._view is not None:
            self.layout().removeWidget(self._view)
            self._view.deleteLater()
        self._sch_type = sch_type
        self._scene = SchematicScene()
        self._scene.style = self._style
        self._scene.sch_type = sch_type   # "slicap" | "ngspice"; the library editor reads it
        self._view  = SchematicView(self._scene)
        self._scene.data_changed.connect(lambda: setattr(self, '_dirty', True))
        # The scene's double-click edit of an analysis block uses the same
        # candidate lists as Place → Define src / det / lg ref.
        self._scene.analysis_candidates = self._analysis_candidates
        self.layout().addWidget(self._view)
        # Focus given to the panel lands on the canvas, so the panel-scoped
        # editor shortcuts (W, F, …) work without an extra click.
        self.setFocusProxy(self._view)

    # -- per-file context -------------------------------------------------------

    def _activate_context(self) -> None:
        """Make this panel's file the app-wide current schematic.

        Repoints the per-file project sidecars (LaTeX render cache, log
        tee).  The drawing STYLE is deliberately not involved: each panel
        owns its Style object (``self._style``, shared with its scene), so
        style state never follows focus and cannot leak between open
        schematics.
        """
        if project.current() != self._current_path:
            project.set_current(self._current_path)

    def eventFilter(self, obj, event):
        if (obj is self._menu_bar
                and event.type() == QEvent.Type.MouseButtonPress):
            self._activate_context()
        return super().eventFilter(obj, event)

    # -- menu building --------------------------------------------------------

    def _shortcut(self, act, keys) -> None:
        """Bind *keys* to *act*, scoped to this panel (canvas and children).

        A window-scoped shortcut would become ambiguous — and therefore dead —
        as soon as a second schematic panel is open in the same main window.
        """
        act.setShortcut(keys)
        act.setShortcutContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.addAction(act)
        self._shortcut_actions.append(act)

    def _build_menu(self):
        if self._menu_bar is None:
            return
        # De-register shortcut actions from a previous build; the menu bar is
        # cleared below, but actions added to the panel itself would otherwise
        # accumulate and make their own shortcuts ambiguous.
        for act in getattr(self, "_shortcut_actions", []):
            self.removeAction(act)
        self._shortcut_actions = []
        self._menu_bar.clear()
        self._build_file_menu()
        self._build_edit_menu()
        self._build_view_menu()
        self._build_draw_menu()
        self._build_place_menu()
        self._build_tools_menu()
        if self._sch_type == 'ngspice':
            self._build_ngspice_instr_menu()
        else:
            self._build_slicap_instr_menu()

    def _build_file_menu(self):
        # Only actions on THIS schematic; creating/opening schematics and
        # project handling live on the main window's File menu (SLNG.md,
        # "separate the two File menus").
        menu = self._menu_bar.addMenu("&File")

        act = QAction("&Save schematic", self)
        act.triggered.connect(self._on_save)
        self._shortcut(act, QKeySequence.Save)
        menu.addAction(act)

        act = QAction("Save schematic &as…", self)
        act.triggered.connect(self._on_save_as)
        self._shortcut(act, QKeySequence.SaveAs)
        menu.addAction(act)
        menu.addSeparator()

        act = QAction("Schematic &properties…", self)
        act.triggered.connect(self._on_doc_properties)
        menu.addAction(act)
        menu.addSeparator()

        act = QAction("&Export netlist…", self)
        act.triggered.connect(self._on_export_netlist)
        self._shortcut(act, "Ctrl+E")
        menu.addAction(act)

        act = QAction("Export &SVG…", self)
        act.triggered.connect(self._on_export_svg)
        menu.addAction(act)

        act = QAction("Export &PDF…", self)
        act.triggered.connect(self._on_export_pdf)
        menu.addAction(act)

        act = QAction("Print s&chematic…", self)
        act.triggered.connect(self._on_print)
        self._shortcut(act, QKeySequence.Print)
        menu.addAction(act)
        menu.addSeparator()

        act = QAction("Schematic &drawing preferences…", self)
        act.triggered.connect(self._on_preferences)
        menu.addAction(act)

    def _build_edit_menu(self):
        menu = self._menu_bar.addMenu("&Edit")
        act = QAction("&Undo", self)
        act.triggered.connect(lambda: self._scene.undo())
        self._shortcut(act, QKeySequence.Undo)
        menu.addAction(act)
        act = QAction("&Redo", self)
        act.triggered.connect(lambda: self._scene.redo())
        self._shortcut(act, QKeySequence.Redo)
        menu.addAction(act)

    def _build_view_menu(self):
        menu = self._menu_bar.addMenu("&View")
        act = QAction("&Fit", self)
        act.triggered.connect(self._view.zoom_fit)
        self._shortcut(act, "F")
        menu.addAction(act)
        menu.addSeparator()
        act = QAction("Zoom &In", self)
        act.triggered.connect(self._view.zoom_in)
        self._shortcut(act, "+")
        menu.addAction(act)
        act = QAction("Zoom &Out", self)
        act.triggered.connect(self._view.zoom_out)
        self._shortcut(act, "-")
        menu.addAction(act)
        act = QAction("&Reset Zoom", self)
        act.triggered.connect(self._view.zoom_reset)
        self._shortcut(act, "Ctrl+0")
        menu.addAction(act)

    def _build_draw_menu(self):
        menu = self._menu_bar.addMenu("&Draw")
        for label, kind in [("&Line", "line"), ("&Rectangle", "rect"), ("&Circle", "circle")]:
            act = QAction(label, self)
            act.triggered.connect(lambda checked=False, k=kind: self._scene.start_drawing(k))
            menu.addAction(act)
        menu.addSeparator()
        act = QAction("&Text…", self)
        act.triggered.connect(self._on_place_text)
        self._shortcut(act, "T")
        menu.addAction(act)
        act = QAction("&Hyperlink…", self)
        act.triggered.connect(self._on_place_hyperlink)
        menu.addAction(act)
        from .latex_label import LATEX_INSTALLED
        act = QAction("La&TeX…", self)
        act.triggered.connect(self._on_place_latex)
        act.setEnabled(LATEX_INSTALLED)
        if not LATEX_INSTALLED:
            act.setToolTip("Requires pdflatex and dvisvgm")
        menu.addAction(act)

    def _build_place_menu(self):
        menu = self._menu_bar.addMenu("&Place")
        act = QAction("&Symbol…", self)
        act.triggered.connect(self._on_place_component)
        self._shortcut(act, "S")
        menu.addAction(act)
        menu.addSeparator()
        act = QAction("&Wire", self)
        act.triggered.connect(lambda: self._scene.start_wire_mode())
        self._shortcut(act, "W")
        menu.addAction(act)
        act = QAction("Net &Label", self)
        act.triggered.connect(self._on_place_label)
        self._shortcut(act, "L")
        menu.addAction(act)
        act = QAction("&Junction", self)
        act.triggered.connect(lambda: self._scene.start_junction_placement())
        self._shortcut(act, "J")
        menu.addAction(act)
        act = QAction("Borde&r", self)
        act.triggered.connect(self._on_place_border)
        self._shortcut(act, "B")
        menu.addAction(act)
        act = QAction("&Library…", self)
        act.triggered.connect(self._on_place_library)
        menu.addAction(act)
        # "NEW subcircuit symbol": the dialog CREATES (or re-assigns) the
        # block symbol and places the first instance; after that the symbol
        # is a palette citizen of the project like any component (Anton,
        # 2026-08-04).
        act = QAction("New s&ubcircuit symbol…", self)
        act.triggered.connect(self._on_place_subcircuit)
        menu.addAction(act)
        act = QAction("&Image…", self)
        act.triggered.connect(self._on_place_image)
        menu.addAction(act)
        act = QAction("&Parameters…", self)
        act.triggered.connect(self._on_place_parameters)
        menu.addAction(act)
        act = QAction("Define src / det / lg ref…", self)
        act.triggered.connect(self._on_place_analysis)
        menu.addAction(act)
        menu.addSeparator()
        act = QAction("&Model definition…", self)
        act.triggered.connect(self._on_place_model_definition)
        menu.addAction(act)

    def _build_tools_menu(self):
        menu = self._menu_bar.addMenu("&Tools")
        act = QAction("&Rename Components…", self)
        act.triggered.connect(self._on_rename_components)
        menu.addAction(act)
        act = QAction("&Load selected symbols from library", self)
        act.triggered.connect(self._on_reload_symbols)
        menu.addAction(act)
        act = QAction("&Update symbols from library", self)
        act.triggered.connect(self._on_update_symbols_from_library)
        menu.addAction(act)

    def _build_slicap_instr_menu(self):
        menu = self._menu_bar.addMenu("&Instruction")
        if self._schematic_only:
            menu.setEnabled(False)
            return
        act = QAction("Create circuit &object…", self)
        act.setToolTip("Add  <name> = sl.makeCircuit(\"<this schematic>\")  "
                       "to the instruction file")
        act.triggered.connect(self._on_slicap_create_circuit)
        menu.addAction(act)
        act = QAction("Create / edit &SLiCAP instruction…", self)
        act.triggered.connect(self._on_slicap_add_instruction)
        menu.addAction(act)
        # Run/Stop live on the MAIN-window Instruction menu only (Anton,
        # 2026-07-16: they don't belong on the schematic editor).

    def _build_ngspice_instr_menu(self):
        menu = self._menu_bar.addMenu("&Instruction")
        if self._schematic_only:
            menu.setEnabled(False)
            return
        act = QAction("Create / edit &NGspice instruction…", self)
        act.triggered.connect(self._on_ngspice_add_instruction)
        menu.addAction(act)
        act = QAction("Create / edit NGspice &control section…", self)
        act.triggered.connect(self._on_ngspice_add_control)
        menu.addAction(act)
        # Run/Stop live on the MAIN-window Instruction menu only.

    # -- library --------------------------------------------------------------

    def _make_library(self, overlay_path=None) -> SymbolLibrary:
        """The library for this panel - built by the ONE shared builder, so
        the editor and the netlister cannot offer different symbols
        (symbol_library.build_library; Anton, 2026-08-03)."""
        from .symbol_library import build_library
        path = self._current_path
        if path is None:                      # a fresh, unsaved schematic
            path = project.project_root() / "sch" / "untitled"
        return build_library(path, sch_type=self._sch_type,
                             config=self._config, overlay=overlay_path)

    def _build_library(self, overlay_path=None):
        lib = self._make_library(overlay_path)
        self._library = lib
        if self._scene is not None:
            self._scene._library = lib

    # -- file I/O -------------------------------------------------------------

    def _load_file(self, path: Path) -> bool:
        from .schematic_data import SchematicData
        try:
            data = SchematicData.load(path)
        except Exception as exc:
            QMessageBox.critical(self, "Open failed", str(exc))
            return False
        sch_type = 'ngspice' if path.suffix.lower() == '.spice_sch' else 'slicap'
        self._init_canvas(sch_type)
        self._current_path = path
        project.set_current(path)                 # log tee + old-sidecar migration
        from .config import Style
        self._style = Style(project.ini_path_for(path))   # the file's own style
        self._scene.style = self._style
        self._scene.cache_dir = project.cache_path_for(path)
        self._build_library(project.symbols_path_for(path))
        missing = self._scene.from_data(data, self._library)
        if missing:
            QMessageBox.warning(
                self, "Missing symbols",
                "No symbol definition was found for:\n\n    {0}\n\n"
                "Those components are NOT on the canvas and will be missing "
                "from the netlist. Check the symbol libraries and this "
                "schematic's .symbols cache.".format(
                    ", ".join(sorted(set(missing)))))
        self._scene.clear_history()
        self._doc_props = data.properties
        self._current_path = path
        self._dirty = False
        self._set_dock_title(path.name)
        self._build_menu()
        # The instruction editor and log panel are shared between all open
        # schematics, so loading a schematic does NOT load a per-schematic
        # instruction file (Anton, 2026-07-09): the editor starts blank; an
        # existing instruction file is loaded with its Open… button, and new
        # instructions are appended to whatever is loaded.
        from PySide6.QtCore import QTimer
        QTimer.singleShot(100, self._view.zoom_fit)
        return True

    # -- save -----------------------------------------------------------------

    def _on_save(self):
        if self._doc_props.is_subcircuit:
            self._save_subcircuit()
        elif self._current_path is None:
            self._on_save_as()
        else:
            self._save_to(self._current_path)

    def _on_save_as(self):
        if self._doc_props.is_subcircuit:
            self._save_subcircuit()
            return
        ext  = ".spice_sch" if self._sch_type == 'ngspice' else ".slicap_sch"
        filt = (_FILTER_NGSPICE if self._sch_type == 'ngspice' else _FILTER_SLICAP) + ";;All Files (*)"
        start_dir = (project.subdir_for(self._current_path, "sch")
                     if self._current_path else project.subdir("sch"))
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Schematic", str(start_dir), filt)
        if not path:
            return
        p = Path(path)
        if p.suffix.lower() != ext:
            p = p.with_suffix(ext)
        self._save_to(p)

    def _save_subcircuit(self):
        title = self._doc_props.title.strip()
        if not title:
            QMessageBox.warning(self, "No title",
                                "Set a Title in Schematic Properties before saving as a subcircuit.")
            return
        from .component_item import ComponentItem
        from .wire_item import WireItem
        from .parameter_item import ParameterItem
        from .library_item import LibraryItem
        from .netlist import build_subcircuit, schematic_ports
        from .create_subcircuit_dialog import CreateSubcircuitDialog
        items = self._scene.items()
        comps = [i for i in items if isinstance(i, ComponentItem)]
        wires = [i for i in items if isinstance(i, WireItem)]
        prms  = [i for i in items if isinstance(i, ParameterItem)]
        slibs = [i for i in items if isinstance(i, LibraryItem)]
        present       = schematic_ports(comps, wires)
        saved         = [p for p in self._doc_props.subcircuit_ports if p in present]
        ports_default = saved + [p for p in present if p not in saved]
        dlg = CreateSubcircuitDialog(title, ports_default, self._doc_props.subcircuit_params, self)
        if not dlg.exec():
            return
        self._doc_props.subcircuit_ports  = dlg.ports()
        self._doc_props.subcircuit_params = dlg.params()
        base    = self._current_path
        is_ng   = self._sch_type == 'ngspice'
        sch_ext = ".spice_sch" if is_ng else ".slicap_sch"
        lib_ext = ".spice_lib" if is_ng else ".slicap_lib"
        # The subcircuit package lives in lib/: the .lib, the block symbol
        # AND the schematic, which is also LOADED from there (descend, pin
        # placement) — one self-contained folder per subcircuit that survives
        # being copied into another project (Anton, 2026-08-05).
        libdir = (project.subdir_for(base, "lib") if base
                  else project.subdir("lib"))
        sch_path = libdir / f"{title}{sch_ext}"
        lib_path = libdir / f"{title}{lib_ext}"
        self._save_to(sch_path)
        try:
            if is_ng:
                from .ngspice_netlist import build_ngspice_subckt
                lib_text = build_ngspice_subckt(comps, wires, title,
                                                self._doc_props.subcircuit_ports,
                                                self._doc_props.subcircuit_params,
                                                params_items=prms, libs=slibs)
            else:
                lib_text = build_subcircuit(comps, wires, title,
                                            self._doc_props.subcircuit_ports,
                                            self._doc_props.subcircuit_params,
                                            params_items=prms, libs=slibs)
            lib_path.write_text(lib_text, encoding="utf-8")
        except Exception as exc:
            QMessageBox.critical(self, "Subcircuit save failed", str(exc))
            return
        QMessageBox.information(self, "Subcircuit saved",
                                f"Wrote:\n  lib/{sch_path.name}\n  lib/{lib_path.name}")

    def _save_to(self, path: Path):
        self._doc_props.last_modified = _date.today().isoformat()
        data = self._scene.to_data()
        data.properties = self._doc_props
        try:
            data.save(path)
            self._current_path = path
            project.set_current(path)          # log tee + old-sidecar migration
            # Persist THIS panel's sidecars next to THIS file — never the
            # globally "current" one, so save-all loops cannot mix schematics.
            self._style.write(project.ini_path_for(path))
            self._scene.cache_dir = project.cache_path_for(path)
            # GC the render cache: entries no current label/table uses are
            # dropped, so edited-away definitions do not accumulate.
            from .latex_label import sweep_cache
            sweep_cache(self._scene.cache_dir)
            used = {c.symbol_name for c in data.components}
            if used:
                self._library.write_bundle(used, project.symbols_path_for(path))
            self._dirty = False
        except Exception as exc:
            QMessageBox.critical(self, "Save failed", str(exc))
            return
        self._set_dock_title(path.name)

    def _set_dock_title(self, title: str) -> None:
        """Set the enclosing canvas dock's title. The dock shows the schematic
        file name once there is one (consistent with the Instructions and Log
        panels); a new, unsaved schematic keeps its 'SLiCAP'/'NGspice' label."""
        p = self.parent()
        while p is not None:
            if isinstance(p, QDockWidget):
                p.setWindowTitle(title)
                break
            p = p.parent()

    def _ensure_saved(self) -> bool:
        if self._current_path is not None:
            return True
        self._on_save()
        return self._current_path is not None

    # -- closable-panel protocol (dirty-check on close) -----------------------

    def panel_dirty(self) -> bool:
        return self._dirty

    def panel_name(self) -> str:
        return str(self._current_path) if self._current_path else "(unsaved schematic)"

    def panel_save(self) -> bool:
        """Save the schematic. Return True if saved, False if the user
        cancelled the Save dialog."""
        self._on_save()
        return not self._dirty

    # -- misc dialogs ---------------------------------------------------------

    def _on_doc_properties(self):
        from .document_properties_dialog import DocumentPropertiesDialog
        dlg = DocumentPropertiesDialog(self._doc_props, self)
        if dlg.exec():
            dlg.apply(self._doc_props)

    def refresh_op_annotations(self) -> None:
        """Load this circuit's most recent UNSTEPPED operating-point results
        (<stem>_op.raw, written by sl.op()) into the scene's op store and
        refresh the bias annotations.  NGspice schematics only; stepped op
        runs write *_op_sN.raw and are deliberately excluded."""
        if self._sch_type != 'ngspice' or self._current_path is None:
            return
        raw = (project.subdir_for(self._current_path, "cir")
               / f"{self._current_path.stem}_op.raw")
        if not raw.is_file():
            return
        from .raw_file import RawFile
        try:
            analyses = RawFile.load(raw)
        except Exception:
            return
        for a in analyses:
            if "operating point" not in a.name.lower():
                continue
            results = {}
            if getattr(a, "x_data", None) is not None and a.x_data.size == 1:
                results[a.x_name.lower()] = float(a.x_data[0].real)
            for k, v in a.signals.items():
                if v.size == 1:
                    results[k.lower()] = float(v[0].real)
            if results:
                # The .cir the raw was produced from names the nets.
                cir = raw.with_name(f"{self._current_path.stem}.cir")
                try:
                    netlist_text = cir.read_text(encoding="utf-8",
                                                 errors="replace")
                except OSError:
                    netlist_text = None
                self._scene.set_op_results(results, netlist_text)
                # Fresh results: live-update any open subcircuit views
                # borrowing this panel's run (order-independent descend).
                self._refresh_borrowing_children()
            return

    def _on_preferences(self):
        from .preferences_dialog import PreferencesDialog
        # The dialog edits and persists THIS panel's style object.
        dlg = PreferencesDialog(self._style, self)
        if dlg.exec():
            self._style.apply_parser(dlg.result_parser())
            if self._current_path is not None:
                self._style.write(project.ini_path_for(self._current_path))
            # Rebuilding re-derives everything from the new style, including
            # the parameter-table/model sizes (natural size × scale pref).
            self._scene.from_data(self._scene.to_data(), self._library)
            self._dirty = True

    def _default_export_path(self, subdir: str, ext: str) -> str:
        if self._current_path is not None:
            return str(project.subdir_for(self._current_path, subdir)
                       / f"{self._current_path.stem}{ext}")
        return str(project.subdir(subdir) / f"schematic{ext}")

    # -- export ---------------------------------------------------------------

    def _on_export_svg(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export SVG", self._default_export_path("img", ".svg"), "SVG (*.svg);;All Files (*)")
        if not path:
            return
        p = Path(path)
        if p.suffix.lower() != ".svg":
            p = p.with_suffix(".svg")
        from .export import export_svg
        title = self._doc_props.title or (self._current_path.stem if self._current_path else "schematic")
        try:
            # Export the LIVE scene: it carries the panel's style, its
            # render cache AND the op results — a rebuilt scene exported
            # with the default style and placeholder annotations
            # (Anton, 2026-07-12). The SVG builder emits item geometry
            # only, so selection state cannot leak into the output.
            export_svg(self._scene, p, title)
        except Exception as exc:
            QMessageBox.critical(self, "Export SVG failed", str(exc))

    def _on_export_pdf(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export PDF", self._default_export_path("img", ".pdf"), "PDF (*.pdf);;All Files (*)")
        if not path:
            return
        p = Path(path)
        if p.suffix.lower() != ".pdf":
            p = p.with_suffix(".pdf")
        from .export import export_pdf
        try:
            export_pdf(self._scene, p)
        except Exception as exc:
            QMessageBox.critical(self, "Export PDF failed", str(exc))

    def _on_print(self):
        from .export import print_scene
        print_scene(self._scene, self)

    def _on_export_netlist(self):
        if self._sch_type == 'ngspice':
            self._export_ngspice_netlist()
        else:
            self._export_slicap_netlist()

    def _export_slicap_netlist(self):
        if not self._ensure_saved():
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Netlist", self._default_export_path("cir", ".cir"), _NET_FILTER_SLICAP)
        if not path:
            return
        p = Path(path)
        if p.suffix.lower() != ".cir":
            p = p.with_suffix(".cir")
        from .component_item import ComponentItem
        from .wire_item import WireItem
        from .command_item import CommandItem
        from .analysis_item import AnalysisItem
        from .library_item import LibraryItem
        from .parameter_item import ParameterItem
        from .model_item import ModelItem
        from .netlist import build_netlist, NetlistError
        items  = self._scene.items()
        comps  = [i for i in items if isinstance(i, ComponentItem)]
        wires  = [i for i in items if isinstance(i, WireItem)]
        cmds   = [i for i in items if isinstance(i, (CommandItem, AnalysisItem))]
        libs   = [i for i in items if isinstance(i, LibraryItem)]
        prms   = [i for i in items if isinstance(i, ParameterItem)]
        models = [i for i in items if isinstance(i, ModelItem)]
        title  = self._doc_props.title or self._current_path.stem
        try:
            text = build_netlist(comps, wires, cmds, title, libs=libs, params=prms, model_defs=models)
        except NetlistError as exc:
            QMessageBox.critical(self, "Netlist not generated",
                                 "Unresolved “?” placeholders remain:\n\n" + "\n".join(exc.errors))
            return
        try:
            p.write_text(text, encoding="utf-8")
        except Exception as exc:
            QMessageBox.critical(self, "Export failed", str(exc))

    def _export_ngspice_netlist(self):
        if not self._ensure_saved():
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export NGspice Netlist", self._default_export_path("cir", ".sp"), _NET_FILTER_NGSPICE)
        if not path:
            return
        p = Path(path)
        if p.suffix.lower() != ".sp":
            p = p.with_suffix(".sp")
        from .component_item import ComponentItem
        from .wire_item import WireItem
        from .library_item import LibraryItem
        from .parameter_item import ParameterItem
        from .ngspice_netlist import build_ngspice_netlist
        from .netlist import NetlistError
        items = self._scene.items()
        comps = [i for i in items if isinstance(i, ComponentItem)]
        wires = [i for i in items if isinstance(i, WireItem)]
        libs  = [i for i in items if isinstance(i, LibraryItem)]
        prms  = [i for i in items if isinstance(i, ParameterItem)]
        title = self._doc_props.title or self._current_path.stem
        try:
            text = build_ngspice_netlist(comps, wires, title, libs=libs, params=prms,
                                         control_section=self._doc_props.control_section)
        except NetlistError as exc:
            QMessageBox.critical(self, "Netlist not generated",
                                 "Unresolved “?” placeholders remain:\n\n" + "\n".join(exc.errors))
            return
        try:
            p.write_text(text, encoding="utf-8")
        except Exception as exc:
            QMessageBox.critical(self, "Export failed", str(exc))

    # -- place actions --------------------------------------------------------

    def _on_place_border(self):
        from .border_dialog import BorderDialog
        from .border_item import BorderItem
        kwargs = {}
        for item in self._scene.items():
            if isinstance(item, BorderItem):
                kwargs = dict(width=item.rect().width(),
                              height=item.rect().height(),
                              show_in_export=item.show_in_export,
                              fixed_w=item.fixed_w, fixed_h=item.fixed_h,
                              line_color=item.line_color,
                              line_width=item.line_width,
                              bg_color=item.bg_color,
                              bg_alpha=item.bg_alpha)
                break
        dlg = BorderDialog(parent=self, **kwargs)
        if dlg.exec():
            self._scene.start_border_placement(dlg.border_properties())

    def _on_place_library(self):
        """Open the Add / Edit libraries editor for the schematic's one library
        block (create it if none)."""
        from .library_dialog import LibraryDialog
        block   = self._scene.library_block()
        entries = list(block.entries) if block else []
        show    = block.show_on_schematic if block else True
        dlg = LibraryDialog(entries=entries, sch_type=self._sch_type,
                            show=show, parent=self)
        if dlg.exec():
            self._scene._push_undo()
            pos = self._view.mapToScene(20, 20)
            self._scene.apply_library_block(dlg.entries(),
                                            dlg.show_on_schematic(), pos)

    def _on_place_model_definition(self):
        from .model_dialog import ModelDialog
        from .model_item import ModelItem
        dlg = ModelDialog(style=self._style, parent=self)
        if not (dlg.exec() and dlg.model_name() and dlg.model_type()):
            return
        # Entering the name of an EXISTING model edits that definition in
        # place (the route back to a hidden one), like the library link.
        existing = next((i for i in self._scene.items()
                         if isinstance(i, ModelItem)
                         and i.model_name == dlg.model_name()), None)
        if existing is not None:
            self._scene._push_undo()
            existing.prepareGeometryChange()
            existing.model_type    = dlg.model_type()
            existing.simulator     = dlg.simulator()
            existing.params        = dlg.get_params()
            existing.preamble_path = dlg.preamble_path()
            existing.set_show(dlg.show_on_schematic())
            existing._load_renderer()
            existing.update()
        elif dlg.show_on_schematic():
            self._scene.start_model_placement(dlg.model_name(), dlg.model_type(),
                                              dlg.simulator(), dlg.get_params(),
                                              dlg.preamble_path())
        else:
            self._scene._push_undo()
            self._scene.addItem(ModelItem(dlg.model_name(), dlg.model_type(),
                                          dlg.simulator(), dlg.get_params(),
                                          dlg.preamble_path(), show=False))

    def _on_place_subcircuit(self):
        from .place_subcircuit_dialog import PlaceSubcircuitDialog
        from .subcircuit import box_symbol_svg, reskin_symbol_svg
        dlg = PlaceSubcircuitDialog(self, sch_type=self._sch_type,
                                    library=self._library)
        if not dlg.exec():
            return
        defn     = dlg.subckt_def()
        from .subcircuit import ensure_in_project_lib
        libdir = (project.subdir_for(self._current_path, "lib")
                  if self._current_path else project.subdir("lib"))
        # a .lib browsed outside the project is COPIED in: the include and
        # the symbol are referenced relatively, so the project must hold them
        lib_path = ensure_in_project_lib(dlg.lib_path(), libdir)
        sym_suffix = "_spice_symbol.svg" if self._sch_type == 'ngspice' else "_slicap_symbol.svg"
        svg_path = lib_path.with_name(f"{defn.name}{sym_suffix}")
        source = dlg._reskin_source()
        if source is not None:
            # an existing symbol's artwork, re-skinned as this subcircuit
            svg_text = reskin_symbol_svg(self._library.symbol(source).g_xml,
                                         defn, dlg.mapping())
        else:
            svg_text = box_symbol_svg(defn, dlg.placement(),
                                      *dlg.extra_size())
        svg_path.write_text(svg_text, encoding="utf-8")
        self._library.add_bundle(svg_path)
        svg = self._library.svg_bytes(defn.name)
        if svg is None:
            QMessageBox.critical(self, "Place subcircuit", f"Could not load symbol for {defn.name}.")
            return
        self._ensure_library_include(lib_path)
        self._scene.start_placement(defn.name, svg)

    def _ensure_library_include(self, lib_path):
        """Ensure the schematic's library block references lib_path (a symbol was
        loaded from it), adding a '.lib' entry if it is not already listed."""
        target_name = Path(lib_path).name
        block   = self._scene.library_block()
        entries = list(block.entries) if block else []
        for e in entries:
            f = e.get("file")
            if f and Path(f).name == target_name:
                return
        # Store a project-relative path ("lib/<file>") so the .include/.lib
        # travels with the project — ngspice/SLiCAP resolve it from the run dir.
        entries.append({"directive": "lib", "file": f"lib/{target_name}", "corner": ""})
        self._scene._push_undo()
        self._scene.apply_library_block(
            entries, block.show_on_schematic if block else True,
            self._view.mapToScene(20, 20))

    def _on_place_image(self):
        from .image_dialog import ImageDialog
        dlg = ImageDialog(style=self._style, parent=self)
        if dlg.exec() and dlg.image_path():
            self._scene.start_image_placement(dlg.image_path(), dlg.image_width(), dlg.image_height())

    def _on_place_latex(self):
        from .latex_fragment_dialog import LatexFragmentDialog
        dlg = LatexFragmentDialog(style=self._style, parent=self)
        if dlg.exec() and dlg.svg_bytes():
            self._scene.start_latex_placement(dlg.latex_code(), dlg.preamble_path(),
                                              dlg.display_width(), dlg.display_height())

    def _on_place_parameters(self):
        # ONE parameter table per schematic (Anton, 2026-07-12): the menu
        # always opens THE table, prefilled — visible or hidden — so a hidden
        # table stays reachable.
        from .parameter_dialog import ParameterDialog
        from .parameter_item import ParameterItem
        existing = next((i for i in self._scene.items()
                         if isinstance(i, ParameterItem)), None)
        dlg = ParameterDialog(
            params=existing.params if existing else None,
            preamble_path=existing.preamble_path if existing else "",
            show=existing.show_on_schematic if existing else True,
            edit_mode=existing is not None,
            style=self._style, parent=self)
        if not dlg.exec():
            return
        if existing is not None:
            self._scene._push_undo()
            existing.prepareGeometryChange()
            existing.params        = dlg.get_params()
            existing.preamble_path = dlg.preamble_path()
            existing.set_show(dlg.show_on_schematic())
            existing._load_renderer()
            existing.update()
        elif dlg.show_on_schematic():
            self._scene.start_parameter_placement(dlg.get_params(),
                                                  dlg.preamble_path())
        else:
            # hidden: nothing to position — add directly (netlisted, not
            # drawn); re-showing later runs through this same dialog
            self._scene._push_undo()
            self._scene.addItem(ParameterItem(dlg.get_params(),
                                              dlg.preamble_path(), show=False))

    def _analysis_candidates(self) -> dict:
        """Candidate reference lists for the .source/.detector/.lgref dialog,
        taken from the **expanded** circuit — loop-gain references such as
        ``E_O1`` only exist after model expansion (``cir.controlled``).
        Returns empty lists when the schematic cannot be built (yet); the
        dialog then falls back to free typing."""
        if self._current_path is None or self._sch_type != 'slicap':
            return {}
        self._status("Parsing circuit…")
        try:
            from SLiCAP.SLiCAPshell import makeCircuit
            cir = makeCircuit(str(self._current_path))
            dep = [str(d) for d in cir.depVars()]
            return dict(
                sources=sorted(cir.indepVars),
                det_v_refs=sorted(d[2:] for d in dep if d.startswith("V_")),
                det_i_refs=sorted(d[2:] for d in dep if d.startswith("I_")),
                lgrefs=sorted(cir.controlled),
            )
        except (Exception, SystemExit):
            return {}
        finally:
            self._status("")

    def _on_place_analysis(self):
        from .analysis_dialog import AnalysisDialog
        from .analysis_item import AnalysisItem
        # Add / Edit (Anton, 2026-07-11): when the block is already defined
        # the dialog shows its values and edits in place — also the only
        # route to a HIDDEN block, which cannot be double-clicked.
        existing = next((i for i in self._scene.items()
                         if isinstance(i, AnalysisItem)), None)
        if existing is not None:
            dlg = AnalysisDialog(parent=self,
                                 source=existing.source,
                                 detector=existing.detector,
                                 lgref=existing.lgref,
                                 show=existing.show_on_schematic,
                                 **self._analysis_candidates())
            if dlg.exec():
                self._scene._push_undo()
                existing.source   = dlg.get_source()
                existing.detector = dlg.get_detector()
                existing.lgref    = dlg.get_lgref()
                existing.set_show(dlg.show_on_schematic())
                existing.update_text()
            return
        dlg = AnalysisDialog(parent=self, **self._analysis_candidates())
        if dlg.exec():
            if dlg.show_on_schematic():
                self._scene.start_analysis_placement(
                    dlg.get_source(), dlg.get_detector(), dlg.get_lgref())
            else:
                # hidden: nothing to position — add directly (netlisted,
                # not drawn); re-showing later keeps the stored position
                self._scene._push_undo()
                self._scene.addItem(AnalysisItem(
                    dlg.get_source(), dlg.get_detector(), dlg.get_lgref(),
                    show=False))

    def _on_place_text(self):
        from .text_dialog import TextDialog
        dlg = TextDialog(style=self._style, parent=self)
        if dlg.exec():
            self._scene.start_text_placement(dlg.text())

    def _on_place_hyperlink(self):
        from .hyperlink_dialog import HyperlinkDialog
        dlg = HyperlinkDialog(style=self._style, parent=self)
        if dlg.exec():
            self._scene.start_hyperlink_placement(dlg.url(), dlg.label())

    def _on_place_label(self):
        from .wire_item import WireItem
        wires = [i for i in self._scene.selectedItems() if isinstance(i, WireItem)]
        if wires:
            self._scene._open_net_label(wires[0])

    def _on_place_component(self, pre_select: str | None = None):
        from .place_symbol_dialog import PlaceSymbolDialog
        dlg = PlaceSymbolDialog(self._library, self, pre_select=pre_select)
        if dlg.exec() and dlg.selected_name():
            self._symbol_loop_name = dlg.selected_name()
            svg = self._library.svg_bytes(self._symbol_loop_name)
            if svg is not None:
                self._scene.start_placement(self._symbol_loop_name, svg)
            self._scene.placing_cancelled.connect(self._on_placement_esc)
        else:
            self._symbol_loop_name = None

    def _on_placement_esc(self):
        self._scene.placing_cancelled.disconnect(self._on_placement_esc)
        last = self._symbol_loop_name
        self._symbol_loop_name = None
        self._on_place_component(pre_select=last)

    # -- tools ----------------------------------------------------------------

    def _on_rename_components(self):
        from .tools import rename_left_right_top_bottom
        self._scene._push_undo()
        n = rename_left_right_top_bottom(self._scene)
        if n == 0:
            self._scene._undo_stack.pop()
        msg = f"{n} component{'s' if n != 1 else ''} renamed." if n else "All components already numbered correctly."
        QMessageBox.information(self, "Rename Components", msg)

    def _on_reload_symbols(self):
        from .component_item import ComponentItem
        selected = [i for i in self._scene.selectedItems() if isinstance(i, ComponentItem)]
        if not selected:
            QMessageBox.information(self, "Load symbols from library", "Select one or more symbols first.")
            return
        names = sorted({i.symbol_name for i in selected})
        if QMessageBox.warning(self, "Load symbols from library",
                               f"Replace {', '.join(names)} with the library version?  Wire connections may break.",
                               QMessageBox.Yes | QMessageBox.No, QMessageBox.No) != QMessageBox.Yes:
            return
        # NO_BUNDLE, not None: None would re-overlay this schematic's own
        # frozen bundle, so the "fresh" library carried the same stale symbol
        # the user is replacing and the reload silently changed nothing
        # (Anton, 2026-08-05).
        from .symbol_library import NO_BUNDLE
        fresh   = self._make_library(NO_BUNDLE)
        updated = self._library.update_symbols(fresh, names)
        if updated:
            for item in self._scene.items():
                if isinstance(item, ComponentItem) and item.symbol_name in updated:
                    sym = self._library.symbol(item.symbol_name)
                    if sym is not None:
                        item.reload_symbol(sym)
            self._scene._sync_junctions()
            self._dirty = True
        missing = [n for n in names if n not in updated]
        if missing:
            QMessageBox.warning(self, "Load symbols from library", f"Not found in library:\n\n    {', '.join(missing)}")

    def _on_update_symbols_from_library(self):
        from .component_item import ComponentItem
        if QMessageBox.warning(self, "Update symbols from library",
                               "Reload all symbols from the system library?  Wire connections may break.",
                               QMessageBox.Yes | QMessageBox.No, QMessageBox.No) != QMessageBox.Yes:
            return
        from .symbol_library import NO_BUNDLE
        self._build_library(NO_BUNDLE)
        for item in self._scene.items():
            if isinstance(item, ComponentItem):
                sym = self._library.symbol(item.symbol_name)
                if sym is not None:
                    item.reload_symbol(sym)
        self._scene._sync_junctions()
        cache = (project.symbols_path_for(self._current_path)
                 if self._current_path else None)
        if cache is not None and cache.is_file():
            cache.unlink()
        self._dirty = True
        QMessageBox.information(self, "Update symbols from library", "All symbols reloaded. Save to persist.")

    # -- instruction actions --------------------------------------------------

    def _schematic_relpath(self) -> str:
        """This schematic, relative to its project root - how an instruction
        file refers to it."""
        return os.path.relpath(str(self._current_path),
                               project.root_for(self._current_path))

    def _on_slicap_create_circuit(self):
        """Instruction -> Create circuit object: append
        ``<name> = sl.makeCircuit("<this schematic>")`` to the instruction
        file.

        Creating the circuit object is DECOUPLED from creating an instruction
        (Anton, 2026-08-16): the file - not whichever tab is active - decides
        which circuit objects exist. A name already in use is never rebound
        silently, and the line is APPENDED, so instructions already in the
        file keep their meaning.
        """
        from PySide6.QtWidgets import QInputDialog
        from .instr_file import circuit_objects, assigned_names
        if self._current_path is None or self._main_win is None:
            return
        editor = self._main_win._instr_editor
        text = editor.text()
        relpath = self._schematic_relpath()
        existing = circuit_objects(text)

        same = [c["name"] for c in existing if c["path"] == relpath]
        if same:
            if QMessageBox.question(
                    self, "Circuit object",
                    "This schematic already has a circuit object: "
                    "{0}.\n\nCreate a SECOND one under a different name?"
                    .format(", ".join(same)),
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No) != QMessageBox.Yes:
                return

        default = re.sub(r"\W", "_", Path(self._current_path).stem)
        if not default or default[0].isdigit():
            default = "cir_" + default
        taken = assigned_names(text)
        name = default
        n = 2
        while name in taken:
            name, n = f"{default}{n}", n + 1

        name, ok = QInputDialog.getText(
            self, "Create circuit object",
            "Variable name for the circuit object of\n{0}:".format(relpath),
            text=name)
        if not ok:
            return
        name = name.strip()
        if not name.isidentifier():
            QMessageBox.warning(self, "Create circuit object",
                                f"'{name}' is not a valid Python name.")
            return
        if name in taken:
            owner = next((c for c in existing if c["name"] == name), None)
            if owner is None:
                QMessageBox.warning(
                    self, "Name in use",
                    f"'{name}' is already used in the instruction file for "
                    "something else. Choose another name.")
                return
            if QMessageBox.warning(
                    self, "Name in use",
                    "'{0}' is now the circuit of\n    {1}\n\nRe-using it "
                    "for\n    {2}\nrebinds the name: instructions added "
                    "AFTER this point will use the new circuit, those above "
                    "keep the old one.\n\nContinue?".format(
                        name, owner["path"], relpath),
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No) != QMessageBox.Yes:
                return

        editor.ensure_header('slicap')
        editor.insert_snippet(f'{name} = sl.makeCircuit("{relpath}")')
        editor.show()
        editor.raise_()
        self._status(f"Circuit object '{name}' added to the instruction file.")

    def _circuit_data(self, path: str) -> dict:
        """Signal and parameter lists of the circuit built from *path*
        (project-relative), cached per run of the dialog."""
        from SLiCAP.SLiCAPshell import makeCircuit
        cache = getattr(self, "_cir_data_cache", None)
        if cache is None:
            cache = self._cir_data_cache = {}
        if path in cache:
            return cache[path]
        full = project.root_for(self._current_path) / path
        cir = makeCircuit(str(full))
        data = {
            "sources":   sorted(cir.indepVars),
            "detectors": sorted(cir.depVars()),
            "lgrefs":    sorted(cir.controlled),
            "par_defs":  {str(k): str(v) for k, v in cir.parDefs.items()},
            "undefined_params": sorted(
                str(p) for p in (cir.params if isinstance(cir.params, list)
                                 else cir.params.keys())),
        }
        cache[path] = data
        return data

    def _on_slicap_add_instruction(self):
        """Compose an instruction for a circuit object of THIS schematic.

        The GUI only ever authors for the ACTIVE schematic (Anton,
        2026-08-16): the circuit it addresses is built from the drawing in
        front of you, so what the dialog offers and what the call references
        can never belong to different circuits.  The rest of the instruction
        file is read for NAME CONFLICTS only - never to address or modify
        instructions of another schematic.  The file itself stays
        project-level and multi-schematic; hand-editing is unrestricted.
        """
        from .instr_file import circuit_objects
        if self._current_path is None or self._main_win is None:
            return
        existing = self._main_win._instr_editor.text()
        relpath = self._schematic_relpath()
        mine = [c for c in circuit_objects(existing) if c["path"] == relpath]
        if not mine:
            QMessageBox.information(
                self, "SLiCAP instruction",
                "This schematic has no circuit object yet.\n\n"
                "Use  Instruction -> Create circuit object…  first: an "
                "instruction is always composed for a circuit object of the "
                "schematic you are editing.")
            return

        self._status("Parsing circuit…")
        try:
            data = self._circuit_data(relpath)
        except (Exception, SystemExit) as exc:
            self._status("")
            QMessageBox.critical(
                self, "SLiCAP instruction",
                "The circuit could not be built from the schematic:\n\n"
                f"{exc}\n\nFix the schematic (or its netlist) and try again.")
            return
        self._status("")

        from .slicap_analysis_dialog import SLiCAPAnalysisDialog
        dlg = SLiCAPAnalysisDialog(cir_var=mine[0]["name"],
                                   sources=data["sources"],
                                   detectors=data["detectors"],
                                   lgrefs=data["lgrefs"],
                                   par_defs=data["par_defs"],
                                   undefined_params=data["undefined_params"],
                                   existing_text=existing, parent=self,
                                   circuits=mine)
        if dlg.exec() and self._main_win:
            snippet = dlg.generated_snippet()
            if snippet:
                self._main_win._instr_editor.ensure_header('slicap')
                self._main_win._instr_editor.insert_snippet(snippet)

    def _on_ngspice_add_instruction(self):
        if not self._current_path:
            return
        if not _check_ngspice(self):
            return
        cir_stem = self._current_path.stem
        self._status("Building netlist…")
        err = None
        netlist_text = None
        try:
            from SLiCAP.SLiCAPngspice import (make_netlist, _get_output_vars,
                                              _get_param_names,
                                              _indep_source_refs)
            cir_path = make_netlist(self._current_path.name)
            if cir_path is None:
                err = "netlist generation failed (see the log panel)"
            else:
                netlist_text = cir_path.read_text(encoding="utf-8")
        except (Exception, SystemExit) as exc:
            err = str(exc) or exc.__class__.__name__
        finally:
            self._status("")
        if netlist_text is None:
            QMessageBox.critical(
                self, "NGspice instruction",
                "The netlist could not be generated from the schematic:\n\n"
                f"{err}\n\nFix the schematic and try again.")
            return
        output_vars = _get_output_vars(netlist_text)
        from SLiCAP.SLiCAPngspice import _get_noise_vars
        noise_vars  = _get_noise_vars(netlist_text, contributions=True)
        param_names = _get_param_names(netlist_text)
        sources     = _indep_source_refs(cir_stem)
        existing = self._main_win._instr_editor.text() if self._main_win else ""
        # Non-modal so the window can be moved freely: an application-modal
        # dialog with a transient parent is rendered as an *attached* (centered,
        # unmovable) sheet under GNOME/Mutter. Kept referenced while open; the
        # snippet is inserted when the user accepts (Anton, 2026-07-16).
        prev = getattr(self, "_ngspice_instr_dlg", None)
        if prev is not None and prev.isVisible():
            prev.raise_()
            prev.activateWindow()
            return
        from .ngspice_analysis_dialog import NGspiceAnalysisDialog
        dlg = NGspiceAnalysisDialog(cir_stem, output_vars=output_vars,
                                    noise_vars=noise_vars,
                                    param_names=param_names,
                                    existing_text=existing, sources=sources,
                                    parent=self)
        dlg.setModal(False)

        def _accept():
            if not self._main_win:
                return
            snippet = dlg.generated_snippet()
            if snippet:
                self._main_win._instr_editor.ensure_header('ngspice')
                self._main_win._instr_editor.insert_snippet(snippet)

        dlg.accepted.connect(_accept)
        dlg.finished.connect(lambda *_: setattr(self, "_ngspice_instr_dlg", None))
        self._ngspice_instr_dlg = dlg
        dlg.show()
        dlg.raise_()
        dlg.activateWindow()

    def _on_ngspice_add_control(self):
        """Create / edit an NGspice control-section instruction (raw mode,
        item 5). No netlist build needed — the runner regenerates it; the
        dialog only picks a control-section text file."""
        if not self._current_path or not self._main_win:
            return
        import SLiCAP.SLiCAPconfigure as ini
        from .ngspice_control_dialog import NGspiceControlDialog
        # parent=None keeps the modal picker freely movable (a parented modal is
        # a frozen, centered sheet under GNOME/Mutter — Anton, 2026-07-16).
        dlg = NGspiceControlDialog(self._current_path.stem,
                                   control_dir=os.path.join(os.getcwd(),
                                                            ini.txt_path),
                                   parent=None)
        if dlg.exec():
            snippet = dlg.generated_snippet()
            if snippet:
                self._main_win._instr_editor.ensure_header('ngspice')
                self._main_win._instr_editor.insert_snippet(snippet)

    def _status(self, msg: str):
        if self._main_win:
            if msg:
                self._main_win.statusBar().showMessage(msg)
            else:
                self._main_win.statusBar().clearMessage()

    # -- subschematic descent -------------------------------------------------

    def open_subschematic(self, path: Path, from_item=None):
        path = Path(path)
        if not path.is_file():
            QMessageBox.warning(self, "Descend into subcircuit", f"Schematic not found:\n{path}")
            return
        if self._main_win is not None:
            child = self._main_win.load_file(path)
        else:
            win = MainWindow()
            child = win.load_file(path)
            win.show()
        if child is not None and from_item is not None:
            # Remember WHO this view borrows from — also when the parent has
            # no op results yet, so a run done AFTER descending live-updates
            # the open view (order must not matter, Anton 2026-08-05).
            child._op_source = (self, from_item.instance_id)
            self._hand_down_op_context(child, from_item.instance_id, path)

    def _hand_down_op_context(self, child, instance_id: str,
                              sch_path: Path) -> None:
        """Give the descended-into panel the parent run's op values for THIS
        instance (definition/instance rule, Anton 2026-08-05: one editable
        view per subcircuit; the annotation context follows the instance the
        user descended from — the last descent wins).

        On any failure — parent has no results, the library cannot be
        parsed, the instance is absent from the netlist the run used — a
        previously BORROWED context on the child is cleared (its values
        belonged to another situation; blank is honest, wrong is not).  A
        child's OWN run results (op_prefix is None) are left alone."""
        from .subcircuit import parse_subckt, instance_port_map
        parent = self._scene
        cs = child._scene

        def _fail(reason=None):
            if reason:
                print(f"Note: no operating-point context for "
                      f"{instance_id}: {reason}")
            if cs is not None and cs.op_prefix:
                cs.adopt_op_context(None, None, None, None)

        if not parent.op_results:
            return _fail()
        is_ng = sch_path.suffix.lower() == ".spice_sch"
        lib_ext = ".spice_lib" if is_ng else ".slicap_lib"
        lib_path = sch_path.with_suffix(lib_ext)
        if not lib_path.is_file():      # legacy layout: schematic in sch/
            lib_path = project.subdir_for(sch_path, "lib") / (sch_path.stem
                                                              + lib_ext)
        try:
            defn = parse_subckt(lib_path)
            lib_text = Path(lib_path).read_text(encoding="utf-8",
                                                errors="replace")
        except Exception as exc:
            return _fail(exc)
        port_nets = instance_port_map(parent.op_netlist, parent.op_prefix,
                                      parent.op_port_nets, instance_id,
                                      defn.ports)
        if port_nets is None:
            return _fail("instance not found in the netlist the op run "
                         "used (re-run the analysis).")
        inst = instance_id.lower()
        prefix = f"{parent.op_prefix}.{inst}" if parent.op_prefix else inst
        cs.adopt_op_context(parent.op_results, lib_text, prefix, port_nets)
        child._set_dock_title(f"{sch_path.name} ({instance_id})")

    def _refresh_borrowing_children(self, _seen=None) -> None:
        """Live-update every open subcircuit view that borrows THIS panel's
        op run (called after fresh results are installed).  Cascades one
        level per borrowed hop so nested descents refresh too; the *seen*
        set is a cycle guard (hierarchy loop detection is still planned)."""
        if self._main_win is None:
            return
        seen = _seen if _seen is not None else set()
        if id(self) in seen:
            return
        seen.add(id(self))
        for dock in list(self._main_win._canvas_docks):
            try:
                child = dock.widget()
                src = getattr(child, "_op_source", None)
                if not src or src[0] is not self:
                    continue
                if child._current_path is None:
                    continue
                self._hand_down_op_context(child, src[1],
                                           child._current_path)
                child._refresh_borrowing_children(seen)
            except RuntimeError:
                continue    # dock/panel already deleted on the C++ side


# ---------------------------------------------------------------------------
# MainWindow — outer shell with shared instruction / log panels
# ---------------------------------------------------------------------------

class MainWindow(QMainWindow):
    """Outer application window.

    Hosts any number of CanvasPanel dock widgets (one per schematic) in the
    top dock area, plus a single shared InstrEditor and LogPanel at the bottom.
    Each CanvasPanel carries its own embedded menu bar."""

    def __init__(self, config: str | None = None, file: str | None = None,
                 schematic_only: bool = False):
        super().__init__()
        self.setWindowTitle("Structured Electronic Design Environment")
        self.resize(1400, 900)
        self._canvas_docks: list[QDockWidget] = []
        # Follow keyboard focus into a schematic panel: its file becomes the
        # current context (per-file style config, sidecars, log tee).
        self._context_panel = None
        from PySide6.QtWidgets import QApplication
        _app = QApplication.instance()
        if _app is not None:
            _app.focusChanged.connect(self._on_focus_changed)
        self._schematic_only = schematic_only
        # Session capture mode. Governs the symbol library used for new
        # schematics AND which schematic type may be created/opened:
        #   'basic'  → SLiCAP, basic symbols only  (NGspice disabled)
        #   'slicap' → SLiCAP, full libraries      (NGspice disabled)
        #   'ngspice'→ NGspice symbols             (SLiCAP disabled)
        #   None     → both types allowed (full NumSymCAD environment)
        self._config = config

        # Shared simulation actions
        self._act_run = QAction("▶ Run", self)
        self._act_run.setShortcut(QKeySequence("F5"))
        self._act_run.triggered.connect(self._on_instr_run)

        self._act_stop = QAction("■ Stop", self)
        self._act_stop.setShortcut(QKeySequence("F6"))
        self._act_stop.setEnabled(False)
        self._act_stop.triggered.connect(self._on_instr_stop)

        self._run_start: float = 0.0
        self._instr_editor = None
        self._log_panel = None
        self._project_panel = None
        self._design_panel = None
        # Allow nested dock splits (rows inside a column etc.) — without
        # this, Qt cannot re-create arrangements like "panels below the
        # schematics" by dragging (Anton live finding, 2026-07-11).
        self.setDockNestingEnabled(True)
        # Corner policy is static and must hold in the WELCOME state too
        # (Anton live findings): the side areas own their corners so BOTH
        # side panels are full height — left for the Project panel, right
        # for the Design data panel (otherwise the canvas claims the
        # top-right corner when the first schematic opens and the Design
        # data pane gets squeezed below it).
        self.setCorner(Qt.Corner.TopLeftCorner,
                       Qt.DockWidgetArea.LeftDockWidgetArea)
        self.setCorner(Qt.Corner.BottomLeftCorner,
                       Qt.DockWidgetArea.LeftDockWidgetArea)
        self.setCorner(Qt.Corner.TopRightCorner,
                       Qt.DockWidgetArea.RightDockWidgetArea)
        self.setCorner(Qt.Corner.BottomRightCorner,
                       Qt.DockWidgetArea.RightDockWidgetArea)
        # Startup dock arrangement, captured once the default layout has
        # settled; View → "Reset panel layout" restores it.
        self._default_layout = None

        if not self._schematic_only:
            # Shared bottom panels
            from .log_panel import LogPanel
            from .instr_editor import InstrEditor

            self._instr_editor = InstrEditor(self)
            self._instr_editor.setObjectName("instr_editor_panel")
            self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self._instr_editor)

            self._log_panel = LogPanel(self)
            self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self._log_panel)
            self.splitDockWidget(self._instr_editor, self._log_panel, Qt.Orientation.Horizontal)

            # Project panel: left, full height (see _apply_default_dock_sizes
            # corner assignment); hidden until a project is opened.
            from .project_panel import ProjectPanel
            self._project_panel = ProjectPanel(self)
            self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self._project_panel)
            self._project_panel.hide()
            self._project_panel.configure_requested.connect(
                self._on_preferences)
            self._project_panel.reload_settings_requested.connect(
                self._reload_ini_forced)

            # Design data panel: right dock mirroring the project panel.
            # VISIBILITY is the user's (View menu); the CONTENT stays empty
            # until a run makes variables available (Anton, 2026-07-11) —
            # the panel is never shown or hidden programmatically.
            from .design_data_panel import DesignDataPanel
            self._design_panel = DesignDataPanel(self)
            self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea,
                               self._design_panel)
            # Target width for the Design-data (variable) panel: 1.5x its
            # narrow natural width, established once at first show and then
            # RESTORED when a schematic opens (else the canvas squeezes it —
            # Anton, 2026-07-16). Mirrors the project-panel keep/restore.
            self._design_panel_w = None
            self._design_panel.configure_requested.connect(
                self._on_preferences)
            # A run's variables become available when the MANIFEST is
            # written — the runner process itself may stay alive for as
            # long as its show=True figures are open.
            self._design_panel.manifest_updated.connect(
                self._on_manifest_updated)

            self._instr_editor.run_requested.connect(self._on_instr_run)
            self._instr_editor.stop_requested.connect(self._on_instr_stop)

            # Closing the Instructions or Log dock prompts to save its content,
            # then hides it (both are singletons — created once, reopenable).
            self._install_panel_close(self._instr_editor)
            self._install_panel_close(self._log_panel)

        from .run_instr import InstrRunner
        self._instr_runner = InstrRunner(self)
        if not self._schematic_only:
            self._instr_runner.line_ready.connect(self._log_panel.append_line)
        self._instr_runner.finished.connect(self._on_instr_finished)

        # Build the main window menu bar first; some platforms require the
        # menu subsystem to be initialised for embedded QMenuBar widgets to
        # render correctly.
        self._build_menu()
        # Schematic-only mode differs from the full GUI only in the absence of
        # the Instruction/Log docks and a disabled Instruction menu; the startup
        # path (welcome screen, canvas hosted in a dock) is otherwise identical.
        self._show_welcome()
        # A canvas is shown only when a file is given. `config` selects the
        # capture mode (symbol set + permitted type); the user creates or opens
        # a schematic via the File menu, which honours that mode.
        if file is not None:
            self.load_file(Path(file))

    def showEvent(self, event):
        super().showEvent(event)
        # Widen the Design-data panel to 1.5x once, after the first layout
        # pass has given it its natural width (Anton, 2026-07-16).
        if not getattr(self, "_design_w_done", False):
            self._design_w_done = True
            QTimer.singleShot(
                0, lambda: self._ensure_design_panel_width(widen=True))

    def _ensure_design_panel_width(self, widen: bool = False) -> None:
        dp = getattr(self, "_design_panel", None)
        if dp is None or not dp.isVisible():
            return
        if widen and self._design_panel_w is None:
            self._design_panel_w = max(int(dp.width() * 1.5), 260)
        if self._design_panel_w:
            self.resizeDocks([dp], [self._design_panel_w],
                             Qt.Orientation.Horizontal)

    def _allows_type(self, sch_type: str) -> bool:
        """Whether the session capture mode permits *sch_type* ('slicap'/'ngspice')."""
        if self._config in ('basic', 'slicap'):
            return sch_type == 'slicap'
        if self._config == 'ngspice':
            return sch_type == 'ngspice'
        return True                        # None → both types allowed

    def _open_filter(self) -> str:
        """File-open dialog filter, constrained to the session capture mode."""
        if self._config in ('basic', 'slicap'):
            return _FILTER_SLICAP + ";;All Files (*)"
        if self._config == 'ngspice':
            return _FILTER_NGSPICE + ";;All Files (*)"
        return _FILE_FILTER

    def _build_menu(self):
        bar = self.menuBar()
        # Prefer an embedded menu bar rather than the desktop-native menu
        # integration so the menu appears inside the window on GNOME/Ubuntu.
        try:
            bar.setNativeMenuBar(False)
        except Exception:
            pass
        bar.setVisible(True)
        bar.show()
        m = bar.addMenu("&File")
        self._file_menu = m
        # Project handling (SLNG.md Q4/Q6–Q10); not available in the
        # single-schematic editor.
        for label, handler in (("New &project…",            self._on_new_project),
                               ("Select pro&ject folder…",  self._on_open_project),
                               ("Sa&ve project",            self._on_save_project),
                               ("&Close project",           self._on_close_project)):
            act = QAction(label, self)
            act.triggered.connect(handler)
            act.setEnabled(not self._schematic_only)
            m.addAction(act)
        # Schematic actions: a schematic belongs to a project, so these are
        # hidden until a project is open (Anton, 2026-07-16) — in the
        # standalone schematic editor (schematic_only) they are the whole
        # app and stay visible. Kept as a group (separator + 3 actions) that
        # shows/hides together via _refresh_file_menu().
        self._sch_menu_sep = m.addSeparator()
        act_new_sl = QAction("New &SLiCAP Schematic", self)
        act_new_sl.triggered.connect(lambda: self.add_canvas_panel('slicap', config=self._config))
        act_new_sl.setEnabled(self._allows_type('slicap'))
        m.addAction(act_new_sl)
        act_new_ng = QAction("New &NGspice Schematic", self)
        act_new_ng.triggered.connect(self._on_new_ngspice_schematic)
        act_new_ng.setEnabled(self._allows_type('ngspice'))
        m.addAction(act_new_ng)
        act_open = QAction("&Open schematic…", self)
        act_open.setShortcut(QKeySequence.Open)
        act_open.triggered.connect(self._on_open)
        m.addAction(act_open)
        # Instruction-file actions live here too (Anton, 2026-08-05): the
        # File menu is the canonical home for file-level actions; the
        # panel's Open…/Save buttons stay as proximity shortcuts.  Same
        # project gating as the schematic actions — an instruction file
        # without a project root has nowhere sensible to run.
        act_new_instr = QAction("New &Instruction file", self)
        act_new_instr.triggered.connect(self._on_new_instruction_file)
        act_new_instr.setEnabled(not self._schematic_only)
        m.addAction(act_new_instr)
        act_open_instr = QAction("Open instruction &file…", self)
        act_open_instr.triggered.connect(self._on_open_instruction_file)
        act_open_instr.setEnabled(not self._schematic_only)
        m.addAction(act_open_instr)
        self._sch_menu_actions = [act_new_sl, act_new_ng, act_open,
                                  act_new_instr, act_open_instr]
        m.addSeparator()
        act = QAction("P&references…", self)
        act.triggered.connect(self._on_preferences)
        act.setEnabled(not self._schematic_only)
        m.addAction(act)
        act = QAction("Edit &main configuration file", self)
        act.triggered.connect(self._on_edit_main_config)
        act.setEnabled(not self._schematic_only)
        m.addAction(act)
        m.addSeparator()
        act = QAction("E&xit", self)
        act.setShortcut(QKeySequence.Quit)
        act.triggered.connect(self.close)
        m.addAction(act)

        instr_menu = bar.addMenu("&Instruction")
        act = QAction("Create / Edit &Traces and Measurements…", self)
        act.triggered.connect(self._on_create_traces)
        instr_menu.addAction(act)
        act = QAction("Create / Edit &Axes…", self)
        act.triggered.connect(self._on_create_axes)
        instr_menu.addAction(act)
        act = QAction("Create / Edit &Figures…", self)
        act.triggered.connect(self._on_create_figure)
        instr_menu.addAction(act)
        # One generic snippet dialog per output format (add a SnippetTarget +
        # a line here for MyST / HTML / plain text later).
        from .snippet_dialog import LATEX_TARGET, RST_TARGET
        for accel_label, target in (("Create &LaTeX snippet…", LATEX_TARGET),
                                    ("Create &RST (Sphinx) snippet…", RST_TARGET)):
            act = QAction(accel_label, self)
            act.triggered.connect(
                lambda _=False, t=target: self._on_create_snippet(t))
            instr_menu.addAction(act)
        act = QAction("Create / Edit &specifications…", self)
        act.triggered.connect(self._on_edit_specifications)
        instr_menu.addAction(act)
        instr_menu.addSeparator()
        instr_menu.addAction(self._act_run)
        instr_menu.addAction(self._act_stop)
        # The Instruction menu needs a project (it composes instructions for a
        # circuit) and is greyed until one is open - like the schematic
        # entries in File (Anton, 2026-08-16). It is also placed AFTER View,
        # so the bar reads File - View - Instruction - Help.
        self._instr_menu = instr_menu
        if self._schematic_only:
            instr_menu.setEnabled(False)

        # View menu: checkable show/hide toggles for the singleton bottom panels
        # (schematic canvases are always visible, so they are not listed here).
        # Disabled in schematic-only mode, like the Instruction menu.
        view_menu = bar.addMenu("&View")
        if self._schematic_only:
            for label in ("Instructions", "Log"):
                act = QAction(label, self)
                act.setCheckable(True)
                view_menu.addAction(act)
            view_menu.setEnabled(False)
        else:
            for dock, label in ((self._project_panel, "Project"),
                                (self._design_panel, "Design data"),
                                (self._instr_editor, "Instructions"),
                                (self._log_panel, "Log")):
                act = dock.toggleViewAction()
                act.setText(label)
                view_menu.addAction(act)
            view_menu.addSeparator()
            act = QAction("Reset panel layout", self)
            act.triggered.connect(self._on_reset_layout)
            view_menu.addAction(act)

        # Order the bar File - View - Instruction - Help: Instruction is
        # re-inserted after View (it was created earlier so its actions could
        # be built alongside the File menu).
        bar.removeAction(instr_menu.menuAction())
        bar.addMenu(instr_menu)

        h = bar.addMenu("&Help")
        act = QAction("Show &HTML Documentation", self)
        act.setShortcut(QKeySequence.HelpContents)
        act.triggered.connect(self._on_show_documentation)
        h.addAction(act)
        act = QAction("Check for &updates…", self)
        act.triggered.connect(self._on_check_updates)
        h.addAction(act)
        act = QAction("&About", self)
        act.triggered.connect(self._on_about)
        h.addAction(act)

        self._refresh_file_menu()          # hide schematic actions until a project

    def _project_is_open(self) -> bool:
        return (self._project_panel is not None
                and bool(getattr(self._project_panel, "_root", "")))

    def _refresh_file_menu(self) -> None:
        """Enable the schematic/instruction group only when a project is open
        (or in the standalone schematic editor).

        The entries stay VISIBLE and are greyed out (Anton, 2026-08-16): a
        user then sees what becomes available once a project is created or
        selected, instead of a menu that changes shape."""
        enabled = self._schematic_only or self._project_is_open()
        if getattr(self, "_sch_menu_sep", None) is not None:
            self._sch_menu_sep.setVisible(True)
        for act in getattr(self, "_sch_menu_actions", []):
            act.setVisible(True)
            act.setEnabled(enabled)
        # The whole Instruction menu needs a project too; in the standalone
        # schematic editor it stays disabled regardless.
        if getattr(self, "_instr_menu", None) is not None:
            self._instr_menu.setEnabled(enabled and not self._schematic_only)

    def _on_show_documentation(self):
        """Help -> Documentation: the INSTALLED documentation.

        It must work WITHOUT an internet connection (Anton, 2026-08-16), so
        the local copy shipped with the package is opened, never a web page
        when one is present. ``ini.install_path`` points at whatever SLiCAP
        was imported from - site-packages for an installed user, the source
        tree for a checkout - so one path covers both. Only when that copy is
        missing does it fall back to the web, and then to slicap.org (not the
        github.io mirror).
        """
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices
        docs = (Path(ini.install_path) / "SLiCAP" / "docs" / "html"
                / "index.html")
        if docs.is_file():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(docs)))
            return
        QDesktopServices.openUrl(QUrl("https://slicap.org"))

    def _on_check_updates(self):
        from PySide6.QtWidgets import QApplication
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            latest = ini.check_for_updates()
        finally:
            QApplication.restoreOverrideCursor()
        installed = ini.install_version
        if latest == "Unknown":
            QMessageBox.warning(
                self, "Check for updates",
                "Could not reach GitHub to check for updates.\n"
                "Please check your internet connection and try again.")
        elif latest == installed:
            QMessageBox.information(
                self, "Check for updates",
                f"SLiCAP {installed} is up to date.")
        else:
            QMessageBox.information(
                self, "Check for updates",
                f"<p>SLiCAP {latest} is available "
                f"(installed: {installed}).</p>"
                '<p>Get it from <a href="https://github.com/SLiCAP/'
                'SLiCAP_python">github.com/SLiCAP/SLiCAP_python</a>.</p>')

    def _on_about(self):
        try:
            from PySide6 import __version__ as _pyside_version
        except Exception:
            _pyside_version = "?"
        latest = ini.latest_version or "Unknown"
        if latest == "Unknown":
            latest += " (use Help → Check for updates…)"
        QMessageBox.about(self, "About SLiCAP Schematic Capture",
                          "<h3>SLiCAP Schematic Capture</h3>"
                          "<p>Author: Anton Montagne</p>"
                          f"<p>SLiCAP {ini.install_version}<br>"
                          f"Latest known release: {latest}<br>"
                          f"PySide6 {_pyside_version}</p>")

    def _show_welcome(self):
        # Hints match what the File menu currently offers: project actions
        # before a project is open, schematic actions after (Anton,
        # 2026-07-16).
        if self._project_is_open() or self._schematic_only:
            hints = ("File → New SLiCAP Schematic<br>"
                     "File → New NGspice Schematic<br>"
                     "File → Open schematic…")
        else:
            hints = ("File → New project…<br>"
                     "File → Select project folder…")
        lbl = QLabel(
            "<div style='text-align:center;'>"
            "<span style='font-size:20pt; font-weight:bold; color:#666;'>"
            "Structured Electronic Design</span><br>"
            "<span style='font-size:12pt; color:#888;'>"
            "A systems engineering approach to circuit design<br>"
            "Specification and project management for SLiCAP and NGspice"
            "</span><br><br>"
            "<span style='font-size:14pt; color:#888;'>" + hints + "</span>"
            "</div>")
        lbl.setAlignment(Qt.AlignCenter)
        self.setCentralWidget(lbl)

    # -- canvas panel management ----------------------------------------------

    def _on_new_ngspice_schematic(self):
        """New NGspice Schematic — check NGspice is available first (running a
        simulation needs it), letting the user locate it or continue anyway."""
        if _check_ngspice(self):
            self.add_canvas_panel('ngspice', config=self._config)

    def add_canvas_panel(self, sch_type: str, config: str | None = None) -> CanvasPanel:
        panel = CanvasPanel(
            sch_type,
            config=config,
            main_win=self,
            schematic_only=self._schematic_only,
        )
        label = "NGspice" if sch_type == 'ngspice' else "SLiCAP"
        dock  = QDockWidget(label, self)
        dock.setWidget(panel)
        dock.setObjectName(f"canvas_dock_{len(self._canvas_docks)}")
        dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable |
            QDockWidget.DockWidgetFeature.DockWidgetFloatable |
            QDockWidget.DockWidgetFeature.DockWidgetClosable
        )
        # Closing a canvas dock closes just that schematic (with a dirty check).
        # Defer via QTimer so the dock's own closeEvent returns before it is
        # removed.
        def _dock_close(event, win=self, d=dock):
            event.ignore()
            QTimer.singleShot(0, lambda: win._close_canvas_dock(d))
        dock.closeEvent = _dock_close
        # Schematics open as tabs so each keeps full width. The anchor is the
        # most recently opened schematic that is still docked; floating ones
        # are ignored (tabifying onto a floating dock leaves the new panel
        # floating over the main window).
        anchor = next((d for d in reversed(self._canvas_docks)
                       if not d.isFloating()), None)
        if anchor is not None:
            self.tabifyDockWidget(anchor, dock)
            # Raise after the tab bar is realised so the new schematic is the
            # active tab.
            QTimer.singleShot(0, dock.raise_)
        else:
            self.addDockWidget(Qt.DockWidgetArea.TopDockWidgetArea, dock)
            if not self._canvas_docks:
                # Remember the project panel width: replacing the central
                # widget redistributes the freed width into the left dock
                # area, ballooning the panel (live-GUI finding).
                keep = (self._project_panel.width()
                        if self._project_panel is not None
                        and self._project_panel.isVisible() else None)
                spacer = QWidget()
                # Height 0 hides the spacer; its WIDTH must stay flexible —
                # QMainWindow exchanges separator-drag space through the
                # central widget, so a 0×0-max spacer froze the project
                # panel's width the moment a schematic opened.
                spacer.setFixedHeight(0)
                self.setCentralWidget(spacer)
                QTimer.singleShot(0, self._apply_default_dock_sizes)
                if keep is not None:
                    # The first layout pass after setCentralWidget() gives the
                    # canvas column its preferred width, squeezing the panel;
                    # restore AFTER that pass (chained zero-timers run once
                    # the posted LayoutRequest has been processed).
                    restore = lambda: self.resizeDocks(
                        [self._project_panel], [keep],
                        Qt.Orientation.Horizontal)
                    QTimer.singleShot(0, lambda: QTimer.singleShot(0, restore))
                # The Design-data panel (right) is squeezed the same way;
                # restore its target width after the same layout pass.
                QTimer.singleShot(
                    0, lambda: QTimer.singleShot(
                        0, self._ensure_design_panel_width))
        self._canvas_docks.append(dock)
        return panel

    def load_file(self, path: Path) -> CanvasPanel:
        path = Path(path)
        # An already-open schematic is ACTIVATED, never opened twice - the
        # old decision, restored for the docked-panel layout (Anton,
        # 2026-08-04: "we just activate the tab that shows it"). Two editors
        # on one file would silently fight over saves. Done HERE so every
        # open path gets it: descend, the project panel, File -> Open.
        for dock in self._canvas_docks:
            panel = dock.widget()
            if not isinstance(panel, CanvasPanel):
                continue
            current = getattr(panel, "_current_path", None)
            try:
                same = (current is not None
                        and Path(current).resolve() == path.resolve())
            except OSError:
                same = False
            if same:
                dock.show()
                dock.raise_()                 # the tab that shows it
                panel.setFocus()
                return panel
        sch_type = 'ngspice' if path.suffix.lower() == '.spice_sch' else 'slicap'
        # Honour the session capture mode so the symbol palette stays consistent
        # (basic mode → basic palette); the schematic's own symbols still load
        # via its frozen symbol bundle.
        panel = self.add_canvas_panel(sch_type, config=self._config)
        panel._load_file(path)
        return panel

    def _apply_default_dock_sizes(self) -> None:
        # Corner policy (project panel full height) is set in __init__ so it
        # also holds in the welcome state, before any canvas dock exists.
        h = self.height()
        if self._schematic_only:
            return
        if self._canvas_docks:
            self.resizeDocks([self._canvas_docks[0]], [int(h * 0.65)], Qt.Orientation.Vertical)
        self.resizeDocks([self._instr_editor], [int(h * 0.35)], Qt.Orientation.Vertical)
        w = self.width()
        if self._project_panel is not None and self._project_panel.isVisible():
            w -= self._project_panel.width()
        self.resizeDocks([self._instr_editor, self._log_panel], [w // 2, w // 2], Qt.Orientation.Horizontal)
        # Capture the settled default arrangement once, for View → Reset
        # panel layout (after the pending resize/restore timers ran).
        if self._default_layout is None:
            QTimer.singleShot(0, lambda: QTimer.singleShot(
                0, self._capture_default_layout))

    def _capture_default_layout(self) -> None:
        if self._default_layout is None:
            self._default_layout = self.saveState()

    def _on_reset_layout(self) -> None:
        """View → Reset panel layout: dragging can create dock arrangements
        that are hard to undo by hand — restore the startup layout."""
        if self._default_layout is not None:
            self.restoreState(self._default_layout)
        else:
            self._apply_default_dock_sizes()

    # -- file handlers --------------------------------------------------------

    def _on_open(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Schematic", str(project.subdir("sch")), self._open_filter())
        if path:
            self.load_file(Path(path))

    # -- project management (SLNG.md Q4/Q6–Q10) --------------------------------

    def _on_new_project(self):
        from .project_panel import NewProjectDialog
        dlg = NewProjectDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.project_dir:
            self._open_project(dlg.project_dir)

    def _on_open_project(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Select SLiCAP Project Folder", os.getcwd())
        if not folder:
            return
        # Q7: SLiCAP.ini marks a project; without it, offer the New-project
        # flow for this directory.
        if not (Path(folder) / "SLiCAP.ini").exists():
            ret = QMessageBox.question(
                self, "Select project folder",
                f"No SLiCAP project found in:\n{folder}\n\nCreate one here?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if ret != QMessageBox.Yes:
                return
            from .project_panel import NewProjectDialog
            dlg = NewProjectDialog(self, directory=folder)
            if dlg.exec() != QDialog.DialogCode.Accepted or not dlg.project_dir:
                return
            folder = dlg.project_dir
        self._open_project(folder)

    def open_instruction_file(self, path) -> None:
        """Open *path* in the shared instruction editor (project-tree
        double-click on a .py file, Anton 2026-08-05).  Unsaved editor
        content prompts first; the panel is raised so the load is visible."""
        if self._instr_editor is None:
            return
        if not self._instr_editor.maybe_save():
            return
        self._instr_editor.load(Path(path))
        self._instr_editor.show()
        self._instr_editor.raise_()

    def _on_new_instruction_file(self) -> None:
        """File → New Instruction file: an explicit fresh buffer (named at
        first Save; Run also asks for a name first)."""
        if self._instr_editor is None:
            return
        if not self._instr_editor.maybe_save():
            return
        self._instr_editor.unload()
        self._instr_editor.show()
        self._instr_editor.raise_()

    def _on_open_instruction_file(self) -> None:
        """File → Open instruction file…: same dialog as the panel button."""
        if self._instr_editor is None:
            return
        self._instr_editor.show()
        self._instr_editor.raise_()
        self._instr_editor.open_dialog()

    def _open_project(self, folder) -> None:
        """Switch the application to the project in *folder*.

        One project at a time (Q8): applies Save-project semantics to the
        current one (prompt per dirty panel), closes all its schematics, then
        re-initialises SLiCAP for the new project directory."""
        if (getattr(self, "_instr_editor", None) is not None
                and not self._instr_editor.maybe_save()):
            return                         # user cancelled the instr prompt
        if not self._close_project_panels():
            return                         # user cancelled a save prompt
        os.chdir(str(folder))
        project.set_app_root(folder)       # project_root() before any schematic opens
        importlib.reload(ini)
        import SLiCAP as sl
        # An EXISTING project keeps its own name, author and report state;
        # loadProject only reads it, compiles the libraries and creates
        # missing directories (Anton, 2026-08-16). initProject here used to
        # rewrite the project's title to "GUI".
        sl.loadProject()
        self._watch_ini_files()
        if self._project_panel is not None:
            self._project_panel.set_root(folder)
            self._project_panel.show()
            # Without an explicit width the dock opens at the tree's size
            # hint, which long filenames blow up to half the window.
            QTimer.singleShot(0, lambda: self.resizeDocks(
                [self._project_panel], [280], Qt.Orientation.Horizontal))
        if getattr(self, "_design_panel", None) is not None:
            # Resets the panel's session — it stays hidden and empty until
            # a script has been RUN in this session (Anton, 2026-07-11:
            # variables are shown only when they are actually available).
            self._design_panel.set_project_root(folder)
        if getattr(self, "_log_panel", None) is not None:
            # The log follows the same reset-on-project-switch rule as every
            # other panel: a new project starts with an empty session log
            # (Anton, 2026-08-05 — it was the one panel that kept the old
            # project's content).
            self._log_panel.clear()
        if getattr(self, "_instr_editor", None) is not None:
            # Same rule for the instruction editor: it kept the OLD
            # project's file, so Open… started in the old project's folder
            # ("takes the wrong path", Anton 2026-08-05).  Unloading also
            # re-anchors the Open… dialog at the new project root.
            self._instr_editor.unload()
        # Title stays the plain product name regardless of the open project
        # (Anton, 2026-07-16: no project-name suffix).
        self.setWindowTitle("Structured Electronic Design Environment")
        self._refresh_file_menu()          # reveal the New/Open-schematic group
        if not self._canvas_docks:         # still on the welcome screen
            self._show_welcome()           # → schematic hints now apply

    # ── configuration-file watching ────────────────────────────────────────
    # The ini files are the source of truth; the loaded ini module is a
    # CACHE of them. Editing a SLiCAP.ini (File → Edit …, project tree, or
    # any external editor) must invalidate that cache, otherwise settings
    # like [gui] sch_scale only apply after a project re-open (Anton, live
    # 2026-07-15: print at 100 % ignored an edited sch_scale). Instruction
    # RUNS are unaffected either way — they are fresh-import subprocesses.

    def _watch_ini_files(self):
        """(Re)arm the file watcher on the project and main SLiCAP.ini."""
        import hashlib
        from PySide6.QtCore import QFileSystemWatcher
        if getattr(self, "_ini_watcher", None) is None:
            self._ini_watcher = QFileSystemWatcher(self)
            self._ini_watcher.fileChanged.connect(self._on_ini_changed)
        paths = [str(Path.cwd() / "SLiCAP.ini"), ini.main_config_path()]
        old = self._ini_watcher.files()
        if old:
            self._ini_watcher.removePaths(old)
        self._ini_hashes = {}
        for p in paths:
            if os.path.isfile(p):
                self._ini_watcher.addPath(p)
                with open(p, "rb") as f:
                    self._ini_hashes[p] = hashlib.sha256(f.read()).hexdigest()

    def _on_ini_changed(self, path):
        # editors replace files (write + rename): debounce, then re-arm
        QTimer.singleShot(300, lambda: self._reload_ini_if_changed(path))

    def _reload_ini_forced(self):
        """Project panel → Reload project settings: unconditional reload."""
        importlib.reload(ini)
        self._watch_ini_files()
        self.statusBar().showMessage("Project settings reloaded.", 5000)

    def _reload_ini_if_changed(self, path):
        """Reload the settings cache when an ini file's CONTENT changed.
        The hash check breaks the write→event→reload→write loop: reloading
        rewrites the ini files (canonical form), which fires the watcher
        again with unchanged content."""
        import hashlib
        if not os.path.isfile(path):
            return
        with open(path, "rb") as f:
            digest = hashlib.sha256(f.read()).hexdigest()
        if self._ini_hashes.get(path) == digest:
            self._watch_ini_files()      # re-arm (rename drops the path)
            return
        importlib.reload(ini)
        self._watch_ini_files()          # re-arm + store post-write hashes
        self.statusBar().showMessage(
            f"Settings reloaded from {os.path.basename(path)} "
            f"({os.path.dirname(path) or '.'})", 5000)

    # A duplicate of CanvasPanel.refresh_op_annotations lived here on
    # MainWindow: dead code (it referenced panel attributes MainWindow
    # does not have and had no callers). REMOVED 2026-08-05.

    def _on_preferences(self):
        """File → Preferences… (also reachable from both panels' footers and
        context menus). Applying refreshes the filtered panels."""
        from .app_preferences_dialog import AppPreferencesDialog
        root = (self._project_panel._root
                if self._project_panel is not None
                and self._project_panel._root else None)
        dlg = AppPreferencesDialog(project_root=root, parent=self)
        if dlg.exec():
            dlg.apply()
            if self._project_panel is not None:
                self._project_panel.refresh_filters()
            if getattr(self, "_design_panel", None) is not None:
                self._design_panel.refresh()

    def _open_config_file(self, path):
        """Open a SLiCAP.ini in the system's default text editor, after the
        syntax-critical warning (SLNG.md, SLiCAP configuration 2026-07-15).
        A GUI ini editor is a later, low-priority option."""
        import os
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices
        ret = QMessageBox.warning(
            self, "Edit configuration file",
            "You are about to edit a SLiCAP configuration file directly:\n\n"
            f"{path}\n\n"
            "The syntax is critical — errors can cause malfunctioning of "
            "SLiCAP. Please consult the SLiCAP manual (slicap.org) before "
            "changing settings.\n\nOpen the file in your text editor?",
            QMessageBox.Open | QMessageBox.Cancel, QMessageBox.Cancel)
        if ret != QMessageBox.Open:
            return
        if not os.path.isfile(path):
            QMessageBox.critical(self, "File not found",
                                 f"Configuration file not found:\n{path}")
            return
        # detached launch: the editor's stderr must not leak into our
        # terminal (Anton, 2026-07-16)
        from .project_panel import open_with_default_app
        open_with_default_app(path)

    def _on_edit_main_config(self):
        """File → Edit main configuration file (ini.main_config_path())."""
        import SLiCAP.SLiCAPconfigure as ini
        self._open_config_file(ini.main_config_path())

    # The old plot wizard (plot_dialog.py) was RETIRED and DELETED on
    # 2026-08-03 with its bridges (ngspice_instr2traces, ngspice_dict2traces,
    # goal=/trace_type= on make_traces), after Anton walked through the
    # replacements: Traces and Measurements -> Axes (with the automatic
    # sweepAxis kind) -> Figures. Only the SCRIPT API keeps compatibility
    # (ngspice2traces, plotSweep, plot, plotPZ).

    def _on_create_traces(self):
        """Instruction -> Create / Edit Traces… (TRACES.md phase 6).

        A named trace set from ONE simulation result: the DATA layer of
        Figure -> Axes -> Traces. Emits one assignment, so append-only
        editing keeps working."""
        if self._instr_editor is None:
            return
        import SLiCAP.SLiCAPconfigure as ini
        from .traces_dialog import TracesDialog
        dlg = TracesDialog(existing_text=self._instr_editor.text(),
                           results_dir=ini.results_path, parent=self)
        if dlg.exec():
            snippet = dlg.generated_snippet()
            if snippet:
                self._instr_editor.insert_snippet(snippet)

    def _on_create_axes(self):
        """Instruction -> Create / Edit Axes… (TRACES.md phase 7).

        The PRESENTATION layer of Figure -> Axes -> Traces: trace sets get an
        axis type, labels, scale factors and units, or a SLiCAP result gets a
        pole-zero axis. Emits one assignment, so append-only editing keeps
        working."""
        if self._instr_editor is None:
            return
        import SLiCAP.SLiCAPconfigure as ini
        from .axes_dialog import AxesDialog
        dlg = AxesDialog(existing_text=self._instr_editor.text(),
                         results_dir=ini.results_path, parent=self)
        if dlg.exec():
            snippet = dlg.generated_snippet()
            if snippet:
                self._instr_editor.insert_snippet(snippet)

    def _on_create_figure(self):
        """Instruction -> Create / Edit Figures… (TRACES.md phase 7).

        Places axes on a canvas: a grid of cells, a span written as the same
        axis repeated in adjacent cells. Emits one assignment per object -
        an axis made from a cell comes before the figure that uses it."""
        if self._instr_editor is None:
            return
        import SLiCAP.SLiCAPconfigure as ini
        from .figure_dialog import FigureDialog
        dlg = FigureDialog(existing_text=self._instr_editor.text(),
                           results_dir=ini.results_path, parent=self)
        if dlg.exec():
            snippet = dlg.generated_snippet()
            if snippet:
                self._instr_editor.insert_snippet(snippet)

    def _on_create_snippet(self, target):
        """Instruction → Create <format> snippet… — one generic dialog per
        output format (SnippetTarget). Emits append-only formatter calls; the
        snippet self-carries the idempotent formatter/txt init lines."""
        if self._instr_editor is None:
            return
        import SLiCAP.SLiCAPconfigure as ini
        from .snippet_dialog import SnippetDialog
        dlg = SnippetDialog(target, instr_text=self._instr_editor.text(),
                            csv_dir=os.path.join(os.getcwd(), ini.csv_path),
                            parent=self)
        if dlg.exec():
            snippet = dlg.generated_snippet()
            if snippet:
                self._instr_editor.insert_snippet(snippet)

    def _on_edit_specifications(self):
        """Instruction → Create / Edit specifications… A pure CSV editor
        (SLNG.md 2026-07-15): writes csv/<name>.csv, emits nothing into the
        instruction file. Specs are viewed in the Design-data panel."""
        import SLiCAP.SLiCAPconfigure as ini
        csv_dir = os.path.join(os.getcwd(), ini.csv_path)
        os.makedirs(csv_dir, exist_ok=True)
        from .specifications_dialog import SpecificationsDialog
        dlg = SpecificationsDialog(csv_dir=csv_dir, parent=self)
        dlg.exec()

    def _on_save_project(self):
        """Q9: save every open panel with unsaved content."""
        for panel in self._dirty_panels():
            if not panel.panel_save():     # Save-As cancelled → stop
                QMessageBox.warning(self, "Save project",
                                    f"“{panel.panel_name()}” was not saved.")
                return

    def _on_close_project(self):
        """Q10: back to the welcome state; the application stays open."""
        if not self._close_project_panels():
            return
        if self._project_panel is not None:
            self._project_panel.hide()
            self._project_panel._root = ""     # no project open
        if getattr(self, "_design_panel", None) is not None:
            # clear the content; visibility stays whatever the user chose
            self._design_panel.set_project_root(None)
        self.setWindowTitle("Structured Electronic Design Environment")
        self._refresh_file_menu()          # hide the New/Open-schematic group

    def _close_project_panels(self) -> bool:
        """Save-or-discard every dirty panel, then close all schematics and
        unload the instruction editor. Returns False if the user cancelled."""
        for panel in self._dirty_panels():
            if not self._confirm_close_panel(panel):
                return False
        for dock in list(self._canvas_docks):
            self._canvas_docks.remove(dock)
            self.removeDockWidget(dock)
            dock.deleteLater()
        self._context_panel = None
        if self._instr_editor is not None:
            self._instr_editor.unload()
        self._show_welcome()
        return True

    # -- simulation -----------------------------------------------------------

    def _active_canvas_panel(self) -> "CanvasPanel | None":
        focused = self.focusWidget()
        while focused is not None:
            if isinstance(focused, CanvasPanel):
                return focused
            focused = focused.parent()
        if self._canvas_docks:
            w = self._canvas_docks[-1].widget()
            if isinstance(w, CanvasPanel):
                return w
        return None

    def _on_instr_run(self):
        if self._schematic_only or self._instr_runner.is_running():
            return
        active = self._active_canvas_panel()
        if active is not None and not active._ensure_saved():
            return
        # Unsaved schematic edits are not in the netlists the instructions
        # regenerate from the files on disk — warn before running.
        dirty = [d.widget() for d in self._canvas_docks
                 if isinstance(d.widget(), CanvasPanel)
                 and d.widget().panel_dirty()]
        if dirty:
            names = "\n".join("  • " + Path(p.panel_name()).name
                              for p in dirty)
            box = QMessageBox(QMessageBox.Icon.Warning,
                              "Unsaved schematic changes",
                              "These schematics have unsaved changes — the "
                              "run would use the outdated netlists on "
                              f"disk:\n\n{names}\n\nSave them and run?",
                              parent=self)
            b_save = box.addButton("Save all && run",
                                   QMessageBox.ButtonRole.AcceptRole)
            b_anyway = box.addButton("Run anyway",
                                     QMessageBox.ButtonRole.DestructiveRole)
            box.addButton(QMessageBox.StandardButton.Cancel)
            box.setDefaultButton(b_save)
            box.exec()
            clicked = box.clickedButton()
            if clicked is b_save:
                for p in dirty:
                    if not p.panel_save():
                        return
            elif clicked is not b_anyway:
                return
        if self._instr_editor.path is None:
            # Fresh buffer — ask where to store it (Save-As); cancel aborts.
            if not self._instr_editor.panel_save():
                return
        if not self._instr_editor.save():
            return
        p = self._instr_editor.path
        # Generate the project main.py (initProject + import the instruction file)
        # and run THAT — keeps initProject out of the instruction file so the file
        # stays import-safe (see SLNG.md, "Instruction-file architecture").
        from . import instr_file
        p = Path(p)
        proj_root, project_name = instruction_run_context(
            p,
            schematic_path=(active._current_path if active is not None
                            else None),
            schematic_project=(active._doc_props.project
                               if active is not None else ""))
        main_path = instr_file.write_main_py(proj_root, project_name, p.stem)
        self._last_instr_source = f"{p.stem}.py"
        import time
        self._run_start = time.monotonic()
        self._log_panel.show()
        self.statusBar().showMessage("Running instructions…")
        self._instr_editor.set_running(True)
        self._act_run.setEnabled(False)
        self._act_stop.setEnabled(True)
        self._instr_runner.run(main_path, cwd=proj_root)

    def _on_instr_stop(self):
        self._instr_runner.stop()

    def _on_manifest_updated(self):
        """The manifest changed while a run is active: the running script's
        section is now available (session semantics — only GUI runs count)."""
        if (self._instr_runner.is_running()
                and getattr(self, "_last_instr_source", None)):
            self._design_panel.mark_run(self._last_instr_source)
        # The manifest is written when the SCRIPT finishes; the process may
        # stay alive while show=True figures are open. The op raw exists by
        # now too — refresh the bias annotations here as well, so they do
        # not wait for the figures to be closed (Anton, live 2026-07-12).
        self._refresh_all_op_annotations()

    def _refresh_all_op_annotations(self) -> None:
        for dock in self._canvas_docks:
            panel = dock.widget()
            if isinstance(panel, CanvasPanel):
                panel.refresh_op_annotations()

    def _on_instr_finished(self, rc: int):
        if self._schematic_only:
            return
        self._instr_editor.set_running(False)
        self._act_run.setEnabled(True)
        self._act_stop.setEnabled(False)
        self.statusBar().showMessage("Instructions complete" if rc == 0 else f"Instructions failed (exit {rc})")
        # The run (also a failed one) may have rewritten the manifest; the
        # just-run script's variables are now actually available. Content
        # only — the panel's visibility belongs to the user (View menu).
        if (getattr(self, "_design_panel", None) is not None
                and getattr(self, "_last_instr_source", None)):
            self._design_panel.mark_run(self._last_instr_source)
        # Bias back-annotation: an op instruction may have refreshed
        # <cir>_op.raw — reload each NGspice panel's operating-point values
        # (fallback; the manifest watcher normally did this already while
        # the figures were still open).
        self._refresh_all_op_annotations()

    # -- close ----------------------------------------------------------------

    def _close_canvas_dock(self, dock: QDockWidget) -> None:
        """Close a single canvas dock after a dirty-check.

        Only that schematic is removed; the other open canvases stay put.
        Closing the last remaining canvas returns to the welcome screen; the
        application only quits via its own close button or File → Exit. In
        schematic-only mode the process exists to edit one schematic, so
        closing the last canvas still quits."""
        if dock not in self._canvas_docks:
            return
        panel = dock.widget()
        if isinstance(panel, CanvasPanel) and panel.panel_dirty():
            if not self._confirm_close_panel(panel):
                return
        # Drop it from the list before any close so the app-level closeEvent
        # dirty-check does not prompt again for this same schematic.
        self._canvas_docks.remove(dock)
        self.removeDockWidget(dock)
        dock.deleteLater()
        if panel is self._context_panel:
            self._context_panel = None
        if not self._canvas_docks:
            if self._schematic_only:
                self.close()
            else:
                self._show_welcome()

    def _install_panel_close(self, panel) -> None:
        """Route a singleton dock's close button through the dirty-check, then
        hide it (default QDockWidget close hides rather than destroys, so the
        panel persists and can be shown again)."""
        def handler(event, win=self, p=panel):
            if p.panel_dirty() and not win._confirm_close_panel(p):
                event.ignore()
                return
            event.accept()
        panel.closeEvent = handler

    def _confirm_close_panel(self, panel) -> bool:
        """Prompt to save or discard one dirty panel (schematic, instruction, or
        log) before closing it.

        Returns True if the close should proceed (saved or discarded), False if
        the user cancelled or a requested save did not complete."""
        ret = QMessageBox.question(
            self, "Unsaved changes",
            f"“{panel.panel_name()}” has unsaved changes.\n\nSave before closing?",
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
            QMessageBox.Save)
        if ret == QMessageBox.Cancel:
            return False
        if ret == QMessageBox.Save:
            return panel.panel_save()   # Save-As cancelled → False → abort
        return True                     # Discard

    def _on_focus_changed(self, _old, now):
        """Switch the per-file context to the panel that received focus."""
        w = now
        while w is not None:
            if isinstance(w, CanvasPanel):
                if w is not self._context_panel:
                    self._context_panel = w
                    w._activate_context()
                return
            w = w.parentWidget()

    def _dirty_panels(self) -> list:
        """Every currently-open panel with unsaved content, canvases first."""
        panels = [d.widget() for d in self._canvas_docks
                  if isinstance(d.widget(), CanvasPanel)]
        panels += [p for p in (self._instr_editor, self._log_panel) if p is not None]
        return [p for p in panels if p.panel_dirty()]

    def closeEvent(self, event):
        # Quitting the app prompts to save every dirty panel; any Cancel aborts.
        for panel in self._dirty_panels():
            if not self._confirm_close_panel(panel):
                event.ignore()
                return
        event.accept()
