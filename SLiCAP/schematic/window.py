from pathlib import Path
from datetime import date as _date

from PySide6.QtWidgets import (
    QMainWindow, QSplitter, QFileDialog, QMessageBox,
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence

from .canvas import SchematicScene, SchematicView
from .symbol_library import SymbolLibrary
from .schematic_data import DocumentProperties
from . import project

_SYMBOLS_SVG = Path(__file__).parent.parent / "files" / "symbols" / "slicap" / "Symbols.svg"
_SYMBOLS_DIR = _SYMBOLS_SVG.parent
_FILE_FILTER  = "SLiCAP Schematic (*.slicap_sch);;All Files (*)"
_NET_FILTER   = "SLiCAP Netlist (*.cir);;All Files (*)"


class MainWindow(QMainWindow):
    def __init__(self, config: str = "full", file: str | None = None):
        super().__init__()
        self._config = config
        self.setWindowTitle("SLiCAP Schematic Capture")
        self.resize(1200, 800)

        self._scene   = SchematicScene()
        self._build_library()                # system symbols only at startup
        self._view    = SchematicView(self._scene)
        self._current_path: Path | None = None
        self._doc_props = DocumentProperties.new()
        self._symbol_loop_name: str | None = None
        self._dirty: bool = False
        self._scene.data_changed.connect(lambda: setattr(self, '_dirty', True))

        self.setCentralWidget(self._view)

        self._build_menu()

        if file is not None:
            self._load_file(Path(file))

    # ── menu ─────────────────────────────────────────────────────────────────

    def _build_menu(self):
        bar = self.menuBar()
        file_menu = bar.addMenu("&File")

        act_new = QAction("&New", self)
        act_new.setShortcut(QKeySequence.New)
        act_new.triggered.connect(self._on_new)
        file_menu.addAction(act_new)

        act_open = QAction("&Open…", self)
        act_open.setShortcut(QKeySequence.Open)
        act_open.triggered.connect(self._on_open)
        file_menu.addAction(act_open)

        act_save = QAction("&Save", self)
        act_save.setShortcut(QKeySequence.Save)
        act_save.triggered.connect(self._on_save)
        file_menu.addAction(act_save)

        act_saveas = QAction("Save &As…", self)
        act_saveas.setShortcut(QKeySequence.SaveAs)
        act_saveas.triggered.connect(self._on_save_as)
        file_menu.addAction(act_saveas)

        file_menu.addSeparator()

        act_docprops = QAction("Document &Properties…", self)
        act_docprops.triggered.connect(self._on_doc_properties)
        file_menu.addAction(act_docprops)

        file_menu.addSeparator()

        act_export = QAction("&Export Netlist…", self)
        act_export.setShortcut("Ctrl+E")
        act_export.triggered.connect(self._on_export_netlist)
        file_menu.addAction(act_export)

        act_svg = QAction("Export &SVG…", self)
        act_svg.triggered.connect(self._on_export_svg)
        file_menu.addAction(act_svg)

        act_pdf = QAction("Export &PDF…", self)
        act_pdf.triggered.connect(self._on_export_pdf)
        file_menu.addAction(act_pdf)

        act_print = QAction("&Print…", self)
        act_print.setShortcut(QKeySequence.Print)
        act_print.triggered.connect(self._on_print)
        file_menu.addAction(act_print)

        file_menu.addSeparator()

        act_prefs = QAction("Pre&ferences…", self)
        act_prefs.triggered.connect(self._on_preferences)
        file_menu.addAction(act_prefs)

        self._build_edit_menu(bar)
        self._build_view_menu(bar)
        self._build_draw_menu(bar)
        self._build_place_menu(bar)
        self._build_tools_menu(bar)
        self._build_help_menu(bar)   # Help is always the last menu

    def _build_edit_menu(self, bar):
        menu = bar.addMenu("&Edit")

        act_undo = QAction("&Undo", self)
        act_undo.setShortcut(QKeySequence.Undo)
        act_undo.triggered.connect(lambda: self._scene.undo())
        menu.addAction(act_undo)

        act_redo = QAction("&Redo", self)
        act_redo.setShortcut(QKeySequence.Redo)
        act_redo.triggered.connect(lambda: self._scene.redo())
        menu.addAction(act_redo)

    def _build_view_menu(self, bar):
        menu = bar.addMenu("&View")

        act_fit = QAction("&Fit", self)
        act_fit.setShortcut("F")
        act_fit.triggered.connect(self._view.zoom_fit)
        menu.addAction(act_fit)

        menu.addSeparator()

        act_in = QAction("Zoom &In", self)
        act_in.setShortcut("+")
        act_in.triggered.connect(self._view.zoom_in)
        menu.addAction(act_in)

        act_out = QAction("Zoom &Out", self)
        act_out.setShortcut("-")
        act_out.triggered.connect(self._view.zoom_out)
        menu.addAction(act_out)

        act_reset = QAction("&Reset Zoom", self)
        act_reset.setShortcut("Ctrl+0")
        act_reset.triggered.connect(self._view.zoom_reset)
        menu.addAction(act_reset)

    def _build_draw_menu(self, bar):
        menu = bar.addMenu("&Draw")

        for label, kind, shortcut in [
            ("&Line",      "line",   ""),
            ("&Rectangle", "rect",   ""),
            ("&Circle",    "circle", ""),
        ]:
            act = QAction(label, self)
            if shortcut:
                act.setShortcut(shortcut)
            act.triggered.connect(lambda checked=False, k=kind: self._scene.start_drawing(k))
            menu.addAction(act)

        menu.addSeparator()

        act_text = QAction("&Text…", self)
        act_text.setShortcut("T")
        act_text.triggered.connect(self._on_place_text)
        menu.addAction(act_text)

        act_hyperlink = QAction("&Hyperlink…", self)
        act_hyperlink.triggered.connect(self._on_place_hyperlink)
        menu.addAction(act_hyperlink)

        from .latex_label import LATEX_AVAILABLE
        act_latex = QAction("La&TeX…", self)
        act_latex.triggered.connect(self._on_place_latex)
        act_latex.setEnabled(LATEX_AVAILABLE)
        if not LATEX_AVAILABLE:
            act_latex.setToolTip("Requires pdflatex and dvisvgm")
        menu.addAction(act_latex)

    def _build_tools_menu(self, bar):
        menu = bar.addMenu("&Tools")

        act_rename = QAction("&Rename Components…", self)
        act_rename.triggered.connect(self._on_rename_components)
        menu.addAction(act_rename)

        act_reload = QAction("&Load selected symbols from library", self)
        act_reload.triggered.connect(self._on_reload_symbols)
        menu.addAction(act_reload)

        act_update = QAction("&Update symbols from library", self)
        act_update.triggered.connect(self._on_update_symbols_from_library)
        menu.addAction(act_update)

    def _build_place_menu(self, bar):
        menu = bar.addMenu("&Place")

        act_comp = QAction("&Symbol…", self)
        act_comp.setShortcut("S")
        act_comp.triggered.connect(self._on_place_component)
        menu.addAction(act_comp)

        menu.addSeparator()

        act_wire = QAction("&Wire", self)
        act_wire.setShortcut("W")
        act_wire.triggered.connect(lambda: self._scene.start_wire_mode())
        menu.addAction(act_wire)

        act_label = QAction("Net &Label", self)
        act_label.setShortcut("L")
        act_label.triggered.connect(self._on_place_label)
        menu.addAction(act_label)

        act_junc = QAction("&Junction", self)
        act_junc.setShortcut("J")
        act_junc.triggered.connect(lambda: self._scene.start_junction_placement())
        menu.addAction(act_junc)

        act_border = QAction("Borde&r", self)
        act_border.setShortcut("B")
        act_border.triggered.connect(self._on_place_border)
        menu.addAction(act_border)

        act_lib = QAction("&Library…", self)
        act_lib.triggered.connect(self._on_place_library)
        menu.addAction(act_lib)

        act_subckt = QAction("Subcirc&uit…", self)
        act_subckt.triggered.connect(self._on_place_subcircuit)
        menu.addAction(act_subckt)

        act_img = QAction("&Image…", self)
        act_img.triggered.connect(self._on_place_image)
        menu.addAction(act_img)

        act_params = QAction("&Parameters…", self)
        act_params.triggered.connect(self._on_place_parameters)
        menu.addAction(act_params)

        act_analysis = QAction("Define src / det / lg ref…", self)
        act_analysis.triggered.connect(self._on_place_analysis)
        menu.addAction(act_analysis)

        menu.addSeparator()

        act_model = QAction("&Model definition…", self)
        act_model.triggered.connect(self._on_place_model_definition)
        menu.addAction(act_model)

        act_lib_link = QAction("Library &link…", self)
        act_lib_link.triggered.connect(self._on_place_library_link)
        menu.addAction(act_lib_link)

    def _build_help_menu(self, bar):
        menu = bar.addMenu("&Help")

        act_help = QAction("Show &HTML Documentation", self)
        act_help.setShortcut(QKeySequence.HelpContents)   # F1
        act_help.triggered.connect(self._on_show_documentation)
        menu.addAction(act_help)

        act_about = QAction("&About", self)
        act_about.triggered.connect(self._on_about)
        menu.addAction(act_about)

    # ── actions ───────────────────────────────────────────────────────────────

    def _on_place_border(self):
        from .border_dialog import BorderDialog
        from .border_item import BorderItem
        w, h, show = 400, 300, True
        for item in self._scene.items():
            if isinstance(item, BorderItem):
                w    = int(item.rect().width())
                h    = int(item.rect().height())
                show = item.show_in_export
                break
        dlg = BorderDialog(width=w, height=h, show_in_export=show, parent=self)
        if dlg.exec():
            self._scene.start_border_placement(
                dlg.border_width(), dlg.border_height(), dlg.show_in_export()
            )

    def _on_place_library(self):
        from PySide6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Library File", str(project.subdir("lib")),
            "Library Files (*.lib *.spi *.sp);;All Files (*)",
        )
        if path:
            self._scene.start_library_placement(path)

    def _on_place_library_link(self):
        from .library_link_dialog import LibraryLinkDialog
        dlg = LibraryLinkDialog(parent=self)
        if dlg.exec() and dlg.file_path():
            self._scene.start_library_placement(
                dlg.file_path(), dlg.directive(), dlg.simulator(), dlg.corner()
            )

    def _on_place_model_definition(self):
        from .model_dialog import ModelDialog
        dlg = ModelDialog(parent=self)
        if dlg.exec() and dlg.model_name() and dlg.model_type():
            self._scene.start_model_placement(
                dlg.model_name(), dlg.model_type(),
                dlg.simulator(), dlg.get_params(),
                dlg.preamble_path(),
                dlg.display_width(), dlg.display_height(),
            )

    def _on_place_subcircuit(self):
        """Place a subcircuit (.lib) as an X block: generate a default symbol,
        add the de-duplicated .lib include, and start placing the block."""
        from .place_subcircuit_dialog import PlaceSubcircuitDialog
        from .subcircuit import box_symbol_svg

        dlg = PlaceSubcircuitDialog(self)
        if not dlg.exec():
            return
        defn     = dlg.subckt_def()
        lib_path = Path(dlg.lib_path())

        # Generate (or refresh) the block symbol next to its .lib and load just
        # that symbol — so it never leaks into other (new) schematics, which stay
        # system-symbols-only until they place the block themselves. The chosen
        # pin placement is visual only; data-nodes keeps the .subckt order.
        svg_path = lib_path.with_name(f"{defn.name}.svg")
        svg_path.write_text(
            box_symbol_svg(defn, dlg.placement(), *dlg.extra_size()),
            encoding="utf-8",
        )
        self._library.add_bundle(svg_path)
        self._library.inject_into_component_item()
        svg = self._library.svg_bytes(defn.name)
        if svg is None:
            QMessageBox.critical(
                self, "Place subcircuit",
                f"Could not load the generated symbol for {defn.name}.",
            )
            return

        self._ensure_library_include(lib_path)
        self._scene.start_placement(defn.name, svg)

    def _ensure_library_include(self, lib_path: str):
        """Add a .lib include for lib_path unless one is already on the canvas."""
        from .library_item import LibraryItem
        target = str(Path(lib_path).resolve())
        for item in self._scene.items():
            if isinstance(item, LibraryItem) and \
                    str(Path(item.file_path).resolve()) == target:
                return
        pos = self._view.mapToScene(20, 20)
        self._scene.addItem(LibraryItem(str(lib_path), pos))

    def _on_place_image(self):
        from .image_dialog import ImageDialog
        dlg = ImageDialog(parent=self)
        if dlg.exec() and dlg.image_path():
            self._scene.start_image_placement(
                dlg.image_path(), dlg.image_width(), dlg.image_height()
            )

    def _on_place_latex(self):
        from .latex_fragment_dialog import LatexFragmentDialog
        dlg = LatexFragmentDialog(parent=self)
        if dlg.exec() and dlg.svg_bytes():
            self._scene.start_latex_placement(
                dlg.latex_code(), dlg.preamble_path(),
                dlg.display_width(), dlg.display_height(),
            )

    def _on_place_parameters(self):
        from .parameter_dialog import ParameterDialog
        dlg = ParameterDialog(parent=self)
        if dlg.exec() and dlg.svg_bytes():
            self._scene.start_parameter_placement(
                dlg.get_params(), dlg.preamble_path(),
                dlg.display_width(), dlg.display_height(),
            )

    def _on_place_analysis(self):
        from .analysis_dialog import AnalysisDialog
        dlg = AnalysisDialog(parent=self)
        if dlg.exec():
            self._scene.start_analysis_placement(
                dlg.get_source(), dlg.get_detector(), dlg.get_lgref()
            )

    def _on_rename_components(self):
        from .tools import rename_left_right_top_bottom
        self._scene._push_undo()
        n = rename_left_right_top_bottom(self._scene)
        if n == 0:
            self._scene._undo_stack.pop()  # nothing changed, discard the snapshot
        msg = f"{n} component{'s' if n != 1 else ''} renamed." if n else "All components already numbered correctly."
        QMessageBox.information(self, "Rename Components", msg)

    def _on_reload_symbols(self):
        """Refresh the selected symbols with the most recent library definitions.

        Replaces the schematic's cached (frozen) definition of each selected
        symbol — and every instance of it on the canvas — with the live version
        from the symbol library.  Pin positions may move, so connections can
        break; restoring them is left to the user (per the warning)."""
        from .component_item import ComponentItem
        selected = [i for i in self._scene.selectedItems() if isinstance(i, ComponentItem)]
        if not selected:
            QMessageBox.information(
                self, "Load symbols from library",
                "Select one or more component symbols on the canvas first.",
            )
            return
        names = sorted({i.symbol_name for i in selected})
        ret = QMessageBox.warning(
            self, "Load symbols from library",
            "The cached definition of the selected symbol(s):\n\n"
            f"    {', '.join(names)}\n\n"
            "and every instance of them on the canvas will be replaced with the "
            "most recent version from the symbol library.\n\n"
            "Pin positions may differ from the cached symbols, which can break "
            "existing wire connections — restoring them is up to you.\n\nProceed?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if ret != QMessageBox.Yes:
            return

        fresh = self._make_library(None)        # live, un-frozen definitions
        updated = self._library.update_symbols(fresh, names)
        if updated:
            self._library.inject_into_component_item()
            for item in self._scene.items():
                if isinstance(item, ComponentItem) and item.symbol_name in updated:
                    svg = self._library.svg_bytes(item.symbol_name)
                    if svg is not None:
                        item.reload_svg(svg)
            self._scene._sync_junctions()        # refresh pin/connection markers
            self._dirty = True

        missing = [n for n in names if n not in updated]
        if missing:
            QMessageBox.warning(
                self, "Load symbols from library",
                "These symbols were not found in the library and were left "
                f"unchanged:\n\n    {', '.join(missing)}",
            )
        elif updated:
            QMessageBox.information(
                self, "Load symbols from library",
                f"Reloaded {len(updated)} symbol"
                f"{'s' if len(updated) != 1 else ''} from the library.\n\n"
                "Save the schematic to persist the updated symbol cache.",
            )

    def _on_update_symbols_from_library(self):
        """Drop the whole frozen symbol cache and reload every symbol fresh from
        the system library.

        Unlike "Load selected symbols…", this rebuilds the active library without
        the schematic's frozen <name>.symbols overlay, refreshes every instance on
        the canvas, and deletes the on-disk cache (it is regenerated on save).
        Pin positions may move, so connections can break — restoring them is left
        to the user."""
        from .component_item import ComponentItem
        ret = QMessageBox.warning(
            self, "Update symbols from library",
            "This deletes the schematic's symbol cache and reloads every symbol "
            "from the system library, refreshing all instances on the canvas.\n\n"
            "Pin positions may differ from the cached symbols, which can break "
            "existing wire connections — restoring them is up to you.\n\nProceed?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if ret != QMessageBox.Yes:
            return

        # Rebuild the active library from the system (+ project lib/) symbols,
        # dropping the frozen overlay, and republish the metadata.
        self._build_library(None)
        for item in self._scene.items():
            if isinstance(item, ComponentItem):
                svg = self._library.svg_bytes(item.symbol_name)
                if svg is not None:
                    item.reload_svg(svg)
        self._scene._sync_junctions()

        # Delete the on-disk cache so it is regenerated from the live library on
        # the next save.
        cache = project.symbols_path()
        if cache is not None and cache.is_file():
            cache.unlink()
        self._dirty = True

        QMessageBox.information(
            self, "Update symbols from library",
            "All symbols reloaded from the system library.\n\n"
            "Save the schematic to regenerate its symbol cache.",
        )

    def _on_place_text(self):
        from .text_dialog import TextDialog
        dlg = TextDialog(parent=self)
        if dlg.exec():
            self._scene.start_text_placement(dlg.text())

    def _on_place_hyperlink(self):
        from .hyperlink_dialog import HyperlinkDialog
        dlg = HyperlinkDialog(parent=self)
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
            self._on_symbol_selected(self._symbol_loop_name)
            # Esc during placement reopens the dialog with the same symbol selected
            self._scene.placing_cancelled.connect(self._on_placement_esc)
        else:
            self._symbol_loop_name = None

    def _on_placement_esc(self):
        self._scene.placing_cancelled.disconnect(self._on_placement_esc)
        last = self._symbol_loop_name
        self._symbol_loop_name = None
        self._on_place_component(pre_select=last)

    def _on_symbol_selected(self, name: str):
        svg = self._library.svg_bytes(name)
        if svg is not None:
            self._scene.start_placement(name, svg)

    def _make_library(self, overlay_path=None) -> SymbolLibrary:
        """Construct a symbol library (system symbols, optionally overlaid by a
        schematic's frozen <name>.symbols) without publishing it as the active
        library.  Pass overlay_path=None to get the live, un-frozen definitions."""
        lib = SymbolLibrary(_SYMBOLS_SVG)
        if self._config == "full":
            # Load all additional SVGs from the system symbols directory.
            lib.add_user_library(_SYMBOLS_DIR, exclude_stems={"Symbols"})
        # User symbol libraries in the project's lib/ (always loaded regardless
        # of config); generated block symbols are excluded — they load on placement.
        libdir = project.subdir("lib")
        lib.add_user_library(libdir, exclude_stems={p.stem for p in libdir.glob("*.lib")})
        if overlay_path is not None:
            lib.add_bundle(overlay_path)
        return lib

    def _build_library(self, overlay_path=None):
        """(Re)build the active symbol library: system symbols, optionally
        overlaid by a schematic's frozen <name>.symbols (which overrides system
        symbols)."""
        lib = self._make_library(overlay_path)
        lib.inject_into_component_item()
        self._library = lib
        if hasattr(self, "_scene"):
            self._scene._library = lib

    def _on_new(self):
        self._scene.reset()
        self._scene.clear_history()
        self._current_path = None
        project.set_current(None)
        self._build_library()               # back to system symbols only
        import SLiCAP.schematic.config as _config
        _config.load(None)                  # new doc → global style defaults
        self._doc_props = DocumentProperties.new()
        self._dirty = False
        self.setWindowTitle("SLiCAP Schematic Capture")

    def _on_open(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Schematic", str(project.subdir("sch")), _FILE_FILTER
        )
        if path:
            self._load_file(Path(path))

    def _load_file(self, path: Path) -> bool:
        """Load a schematic file into this window.  Returns True on success.

        Note: project/config and the symbol-metadata dicts are process-global, so
        this repoints them at ``path``; each window re-establishes its own
        context when activated (see changeEvent)."""
        from .schematic_data import SchematicData
        try:
            data = SchematicData.load(path)
        except Exception as exc:
            QMessageBox.critical(self, "Open failed", str(exc))
            return False
        # Point sidecars at this schematic before loading, so any LaTeX rendered
        # while building the scene goes to (and is read from) <name>.cache, and
        # the schematic's own style (<name>.ini) is applied before items render.
        project.set_current(path)
        import SLiCAP.schematic.config as _config
        _config.load(project.ini_path())
        # Rebuild the library with this schematic's frozen symbols overlaid, so
        # it renders with the symbols it was drawn with (and user symbols win).
        self._build_library(project.symbols_path())
        self._scene.from_data(data, self._library)
        self._scene.clear_history()
        self._doc_props = data.properties
        self._current_path = path
        self._dirty = False
        self.setWindowTitle(f"SLiCAP — {path.name}")
        return True

    def open_subschematic(self, path: Path):
        """Open a subcircuit's schematic in a new editable window (descending the
        hierarchy).  Each window restores its own global context when activated
        (see changeEvent), since project/config and the symbol dicts are shared.

        If the schematic is already open in another window it is raised instead of
        opened twice — a subcircuit must be edited in one place at a time."""
        path = Path(path)
        if not path.is_file():
            QMessageBox.warning(self, "Descend into subcircuit",
                                f"Source schematic not found:\n{path}")
            return

        existing = self._window_showing(path)
        if existing is not None:
            QMessageBox.information(
                self, "Already open",
                f"“{path.name}” is already open.\n"
                "A subcircuit must be edited in one place at a time.",
            )
            existing.raise_()
            existing.activateWindow()
            return

        win = MainWindow()
        if not win._load_file(path):
            return
        win.show()
        win.raise_()
        win.activateWindow()
        self._children = getattr(self, "_children", [])
        self._children.append(win)

    @staticmethod
    def _window_showing(path: Path) -> "MainWindow | None":
        """A visible MainWindow currently editing ``path``, or None."""
        from PySide6.QtWidgets import QApplication
        target = Path(path).resolve()
        for w in QApplication.topLevelWidgets():
            if (isinstance(w, MainWindow) and w.isVisible()
                    and w._current_path is not None
                    and Path(w._current_path).resolve() == target):
                return w
        return None

    def changeEvent(self, event):
        # Re-establish this window's context when it becomes the active window:
        # project/config and the symbol-metadata dicts are process-global, so the
        # active editor must own them (keeps multiple open schematics consistent).
        from PySide6.QtCore import QEvent
        if event.type() == QEvent.ActivationChange and self.isActiveWindow():
            self._activate_context()
        super().changeEvent(event)

    def _activate_context(self) -> None:
        project.set_current(self._current_path)
        if self._current_path is not None:
            import SLiCAP.schematic.config as _config
            _config.load(project.ini_path())
        self._library.inject_into_component_item()

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
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Schematic", str(project.subdir("sch")), _FILE_FILTER
        )
        if not path:
            return
        p = Path(path)
        if p.suffix.lower() != ".slicap_sch":
            p = p.with_suffix(".slicap_sch")
        self._save_to(p)

    def _save_subcircuit(self):
        """Save the schematic as a SLiCAP subcircuit: write both <title>.slicap_sch
        and <title>.lib into a user-chosen directory (the 'Subcircuit' box in
        Document Properties is ticked)."""
        title = self._doc_props.title.strip()
        if not title:
            QMessageBox.warning(
                self, "No title",
                "Set a Title in Document Properties before saving as a subcircuit.",
            )
            return

        from .component_item import ComponentItem
        from .wire_item import WireItem
        from .parameter_item import ParameterItem
        from .netlist import build_subcircuit, schematic_ports
        from .create_subcircuit_dialog import CreateSubcircuitDialog

        items = self._scene.items()
        comps = [i for i in items if isinstance(i, ComponentItem)]
        wires = [i for i in items if isinstance(i, WireItem)]
        prms  = [i for i in items if isinstance(i, ParameterItem)]

        # Default node order: keep the previously chosen order for ports that
        # still exist, then append any newly added ports (clockwise default).
        present = schematic_ports(comps, wires)
        saved   = [p for p in self._doc_props.subcircuit_ports if p in present]
        ports_default = saved + [p for p in present if p not in saved]

        dlg = CreateSubcircuitDialog(
            title, ports_default, self._doc_props.subcircuit_params, self
        )
        if not dlg.exec():
            return

        self._doc_props.subcircuit_ports  = dlg.ports()
        self._doc_props.subcircuit_params = dlg.params()

        # Fixed project layout: editable source → sch/, compiled library → lib/.
        sch_path = project.subdir("sch") / f"{title}.slicap_sch"
        lib_path = project.subdir("lib") / f"{title}.lib"

        # Save the editable source first (this also migrates sidecars and clears
        # the dirty flag), then write the compiled library into lib/.
        self._save_to(sch_path)
        try:
            lib_text = build_subcircuit(
                comps, wires, title,
                self._doc_props.subcircuit_ports,
                self._doc_props.subcircuit_params,
                params_items=prms,
            )
            lib_path.write_text(lib_text, encoding="utf-8")
        except Exception as exc:
            QMessageBox.critical(self, "Subcircuit save failed", str(exc))
            return
        QMessageBox.information(
            self, "Subcircuit saved",
            f"Wrote:\n  sch/{sch_path.name}\n  lib/{lib_path.name}",
        )

    def _save_to(self, path: Path):
        self._doc_props.last_modified = _date.today().isoformat()
        data = self._scene.to_data()
        data.properties = self._doc_props
        try:
            data.save(path)
            self._current_path = path
            project.set_current(path)   # migrates session-temp cache → <name>.cache
            import SLiCAP.schematic.config as _config
            _config.write(project.ini_path())   # persist current style → <name>.ini
            used = {c.symbol_name for c in data.components}
            if used:                            # freeze the symbols this schematic uses
                self._library.write_bundle(used, project.symbols_path())
            self._dirty = False
            self.setWindowTitle(f"SLiCAP — {path.name}")
        except Exception as exc:
            QMessageBox.critical(self, "Save failed", str(exc))
            return
        self._current_path = path
        self.setWindowTitle(f"SLiCAP — {path.name}")

    def _on_doc_properties(self):
        from .document_properties_dialog import DocumentPropertiesDialog
        dlg = DocumentPropertiesDialog(self._doc_props, self)
        if dlg.exec():
            dlg.apply(self._doc_props)

    def _on_show_documentation(self):
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices
        # Try the locally built docs first (developer install), then fall back
        # to the installed SLiCAP docs, then to the online documentation.
        local = Path(__file__).parent.parent.parent.parent / "docs" / "_build" / "html" / "schematics" / "index.html"
        installed = Path(__file__).parent.parent / "docs" / "schematics" / "index.html"
        online = "https://slicap.github.io/SLiCAP_python/schematics/index.html"
        for path in (local, installed):
            if path.is_file():
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))
                return
        QDesktopServices.openUrl(QUrl(online))

    def _on_about(self):
        try:
            from PySide6 import __version__ as _pyside_version
        except Exception:
            _pyside_version = "?"
        QMessageBox.about(
            self,
            "About SLiCAP Schematic Capture",
            "<h3>SLiCAP Schematic Capture</h3>"
            "<p>A graphical schematic editor for "
            "<a href=\"https://www.slicap.org\">SLiCAP</a> and NGspice: draw a "
            "circuit once and use it both as a publication-quality figure and as "
            "a runnable netlist.</p>"
            "<p>Author: Anton Montagne</p>"
            f"<p>PySide6 {_pyside_version}</p>",
        )

    def _on_preferences(self):
        from .preferences_dialog import PreferencesDialog
        import SLiCAP.schematic.config as _config
        dlg = PreferencesDialog(self)
        if dlg.exec():
            dlg.save()                       # applies the new style live
            if self._current_path is not None:
                _config.write(project.ini_path())  # flush to disk: _activate_context reloads on focus-in
            self._scene.from_data(self._scene.to_data(), self._library)
            self._dirty = True               # style is part of the schematic now

    def _default_export_path(self, subdir: str, ext: str) -> str:
        """Default save path for an export: <schematic stem><ext> in *subdir*.

        Mirrors the .slicap_sch base name so exporting design.slicap_sch
        proposes design.cir / design.svg / design.pdf."""
        stem = self._current_path.stem if self._current_path else "schematic"
        return str(project.subdir(subdir) / f"{stem}{ext}")

    def _on_export_svg(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export SVG", self._default_export_path("img", ".svg"),
            "SVG (*.svg);;All Files (*)"
        )
        if not path:
            return
        p = Path(path)
        if p.suffix.lower() != ".svg":
            p = p.with_suffix(".svg")
        from .export import export_svg
        from .canvas import SchematicScene
        title = self._doc_props.title or (self._current_path.stem if self._current_path else "schematic")
        try:
            fresh = SchematicScene()
            fresh.from_data(self._scene.to_data(), self._library)
            export_svg(fresh, p, title)
        except Exception as exc:
            QMessageBox.critical(self, "Export SVG failed", str(exc))

    def _on_export_pdf(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export PDF", self._default_export_path("img", ".pdf"),
            "PDF (*.pdf);;All Files (*)"
        )
        if not path:
            return
        p = Path(path)
        if p.suffix.lower() != ".pdf":
            p = p.with_suffix(".pdf")
        from .export import export_pdf
        from .canvas import SchematicScene
        try:
            fresh = SchematicScene()
            fresh.from_data(self._scene.to_data(), self._library)
            export_pdf(fresh, p)
        except Exception as exc:
            QMessageBox.critical(self, "Export PDF failed", str(exc))

    def _on_print(self):
        from .export import print_scene
        from .canvas import SchematicScene
        fresh = SchematicScene()
        fresh.from_data(self._scene.to_data(), self._library)
        print_scene(fresh, self)

    def _on_export_netlist(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Netlist", self._default_export_path("cir", ".cir"), _NET_FILTER
        )
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
        items = self._scene.items()
        comps  = [i for i in items if isinstance(i, ComponentItem)]
        wires  = [i for i in items if isinstance(i, WireItem)]
        cmds   = [i for i in items if isinstance(i, (CommandItem, AnalysisItem))]
        libs   = [i for i in items if isinstance(i, LibraryItem)]
        prms   = [i for i in items if isinstance(i, ParameterItem)]
        models = [i for i in items if isinstance(i, ModelItem)]
        title = self._doc_props.title or (self._current_path.stem if self._current_path else "schematic")
        try:
            text = build_netlist(comps, wires, cmds, title, libs=libs, params=prms,
                                 model_defs=models)
        except NetlistError as exc:
            QMessageBox.critical(
                self, "Netlist not generated",
                "Unresolved “?” placeholders remain, so no netlist was written:\n\n"
                + "\n".join(exc.errors),
            )
            return
        try:
            p.write_text(text, encoding="utf-8")
        except Exception as exc:
            QMessageBox.critical(self, "Export failed", str(exc))

    # ── close / quit ─────────────────────────────────────────────────────────

    def closeEvent(self, event):
        if not self._dirty:
            event.accept()
            return

        dlg = QDialog(self)
        dlg.setWindowTitle("Unsaved changes")
        layout = QVBoxLayout(dlg)

        layout.addWidget(QLabel("Save changes to:"))
        fname = str(self._current_path) if self._current_path else ""
        name_edit = QLineEdit(fname)
        name_edit.setMinimumWidth(360)
        name_edit.setPlaceholderText("(choose a filename)")
        layout.addWidget(name_edit)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        discard_btn = QPushButton("Close without saving")
        cancel_btn  = QPushButton("Cancel")
        ok_btn      = QPushButton("OK")
        ok_btn.setDefault(True)
        btn_row.addWidget(discard_btn)
        btn_row.addStretch(1)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(ok_btn)
        layout.addLayout(btn_row)

        _action = {"v": None}   # "discard", "save", or None (cancel)
        discard_btn.clicked.connect(lambda: (_action.update({"v": "discard"}), dlg.accept()))
        cancel_btn.clicked.connect(dlg.reject)
        ok_btn.clicked.connect(lambda: (_action.update({"v": "save"}), dlg.accept()))

        if not dlg.exec():          # Cancel or window-close → stay in app
            event.ignore()
            return

        if _action["v"] == "discard":
            event.accept()
            return

        # "save" — save to the given path (or open Save As if blank)
        typed = name_edit.text().strip()
        if typed:
            p = Path(typed)
            if p.suffix.lower() != ".slicap_sch":
                p = p.with_suffix(".slicap_sch")
            self._save_to(p)
        else:
            self._on_save_as()

        if self._dirty:
            event.ignore()   # save was cancelled or failed
        else:
            event.accept()
