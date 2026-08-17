"""Project panel and New-project dialog (SLNG.md, "project management").

The ProjectPanel is a left, full-height dock showing the open project
directory. Double-clicking a schematic (``.slicap_sch`` / ``.spice_sch``)
opens it in a canvas panel; any other file opens with the desktop's default
application. Caches, GUI-managed sidecars, and build helpers are hidden from
the tree (see _visible()).

The NewProjectDialog collects project name, directory, and author, writes the
GUI-managed ``main.py`` (see instr_file.py), and executes it once as a
subprocess with the project directory as working directory — that run creates
the project's directory structure, the project SLiCAP.ini, and compiles the
libraries (SLNG.md Q4/Q5)."""

import os
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QUrl, QSortFilterProxyModel, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QDockWidget, QTreeView, QFileSystemModel, QDialog, QFormLayout,
    QLineEdit, QPushButton, QHBoxLayout, QWidget, QDialogButtonBox,
    QFileDialog, QMessageBox, QApplication, QLabel, QVBoxLayout, QMenu,
)

import SLiCAP.SLiCAPconfigure as ini


def open_with_default_app(path) -> None:
    """Open *path* (a file or directory) with the desktop's default
    application, DETACHED and with the child's stdout/stderr sent to
    devnull — so third-party chatter (LibreOffice/GTK theme warnings, …)
    never leaks into SLiCAP's terminal (Anton, 2026-07-16). Falls back to
    QDesktopServices when the platform opener is unavailable."""
    path = str(path)
    try:
        if sys.platform.startswith("win"):
            os.startfile(path)                       # noqa: no stdio to leak
            return
        opener = "open" if sys.platform == "darwin" else "xdg-open"
        subprocess.Popen(
            [opener, path],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            start_new_session=True)                  # detach from our session
    except (OSError, FileNotFoundError):
        QDesktopServices.openUrl(QUrl.fromLocalFile(path))
from . import app_prefs
from .instr_file import write_main_py

_SCHEMATIC_SUFFIXES = ('.slicap_sch', '.spice_sch')

# Compound suffixes that must not be lumped with their plain suffix: a
# schematic sidecar .slicap_sch.ini is a different type key than a user
# .ini (Anton, 2026-07-11: exclusions are per type PER DIRECTORY).
_COMPOUND_SUFFIXES = ('.slicap_sch.ini', '.spice_sch.ini')


def type_key(name: str) -> str:
    """Type bucket of a file name: a compound suffix, the plain suffix, or
    — for suffix-less files like Makefile — the name itself."""
    for c in _COMPOUND_SUFFIXES:
        if name.endswith(c):
            return c
    suffix = Path(name).suffix
    return suffix if suffix else name


def file_excluded(name: str, excluded: set[str]) -> bool:
    """Exclusion entries may be type keys (".ini") or exact file names
    ("make.bat" — excluding by name must not hide every .bat file)."""
    return name in excluded or type_key(name) in excluded


def _bucket_of(path: str, root: str) -> str:
    """Project-relative directory a file lives in ('' = project root,
    'sch', 'tex/SLiCAPdata', …) — type exclusions are per directory at
    EVERY level (Anton, 2026-07-11)."""
    try:
        parts = Path(path).relative_to(root).parts
    except ValueError:
        return ""
    return "/".join(parts[:-1])


class _ProjectFilter(QSortFilterProxyModel):
    """The user's view preferences (SLNG.md "Design data panel" spec +
    Anton's 2026-07-11 live-check refinement): ONE exclusion model — the
    formerly hard-coded hidden machinery is just the default exclusion
    set. Directory exclusions match by name at any depth (highest
    precedence: an excluded directory hides its whole subtree); file-type
    exclusions apply per top-level directory. Dot-files stay hidden
    unconditionally."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._root = ""
        self._view = app_prefs.get_project_view()

    def set_view(self, root: str, view: dict) -> None:
        self._root = os.path.normpath(str(root)) if root else ""
        self._view = view
        self.invalidateFilter()

    def filterAcceptsRow(self, row, parent):
        src = self.sourceModel()
        idx = src.index(row, 0, parent)
        name, is_dir = src.fileName(idx), src.isDir(idx)
        if name.startswith('.'):
            return False
        if is_dir:
            rel = ""
            try:
                rel = "/".join(
                    Path(src.filePath(idx)).relative_to(self._root).parts)
            except ValueError:
                pass
            return not app_prefs.dir_excluded(
                name, self._view.get("excluded_dirs", ()), rel)
        bucket = _bucket_of(src.filePath(idx), self._root)
        return not file_excluded(
            name, app_prefs.excluded_types_for(self._view, bucket))


class ProjectPanel(QDockWidget):
    """Dock with a filtered file tree of the open project directory."""

    configure_requested = Signal()      # footer link / context "Configure…"
    reload_settings_requested = Signal()  # "Reload project settings" button

    def __init__(self, main_win):
        super().__init__("Project", main_win)
        self._main_win = main_win
        self.setObjectName("project_panel")
        self._root: str = ""
        self._model = QFileSystemModel(self)
        self._proxy = _ProjectFilter(self)
        self._proxy.setSourceModel(self._model)
        self._tree = QTreeView(self)
        self._tree.setModel(self._proxy)
        self._tree.setHeaderHidden(True)
        self._tree.setMinimumWidth(120)
        # Only the name column; size/type/date add noise at panel width.
        for col in range(1, self._model.columnCount()):
            self._tree.hideColumn(col)
        self._tree.doubleClicked.connect(self._on_double_click)
        self._tree.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu)
        self._tree.customContextMenuRequested.connect(self._on_context_menu)
        body = QWidget()
        lay = QVBoxLayout(body)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self._tree)
        # No-silent-truncation footer: counts what the view preferences
        # hide at the project's top level, links to the Preferences dialog.
        self._footer = QLabel("")
        self._footer.setContentsMargins(6, 2, 6, 2)
        self._footer.setWordWrap(True)
        self._footer.linkActivated.connect(
            lambda *_: self.configure_requested.emit())
        self._footer.hide()
        lay.addWidget(self._footer)
        # No dedicated edit-project-config button: the project SLiCAP.ini is
        # reachable in the file tree itself (Anton, 2026-07-15).
        self.setWidget(body)

    def set_root(self, path) -> None:
        path = str(path)
        self._root = path
        self._model.setRootPath(path)
        self.refresh_filters()
        self._tree.setRootIndex(self._proxy.mapFromSource(self._model.index(path)))
        self.setWindowTitle("Project")

    def refresh_filters(self) -> None:
        """Re-apply the view preferences and update the hidden-count footer."""
        view = app_prefs.get_project_view()
        self._proxy.set_view(self._root, view)
        self._footer.hide()
        if not self._root or not os.path.isdir(self._root):
            return
        hidden = self._count_hidden(view)
        if hidden:
            self._footer.setText(
                f'{hidden} entr{"ies" if hidden != 1 else "y"} hidden '
                f'(view preferences) — <a href="prefs">configure…</a>')
            self._footer.show()

    def _count_hidden(self, view: dict, cap: int = 20000) -> int:
        """Entries the preferences hide, across the project tree (excluded
        directories count as one entry each; their contents are pruned).
        Dot-files are unconditional, not preference-hidden, so not counted."""
        excluded_dirs = view.get("excluded_dirs", ())
        hidden = seen = 0
        for cur, dirs, files in os.walk(self._root):
            bucket = _bucket_of(os.path.join(cur, "x"), self._root)
            keep = []
            for d in dirs:
                if d.startswith('.'):
                    continue
                rel_d = f"{bucket}/{d}" if bucket else d
                if app_prefs.dir_excluded(d, excluded_dirs, rel_d):
                    hidden += 1
                else:
                    keep.append(d)
            dirs[:] = keep
            excl = app_prefs.excluded_types_for(view, bucket)
            for f in files:
                if not f.startswith('.') and file_excluded(f, excl):
                    hidden += 1
            seen += len(dirs) + len(files)
            if seen > cap:
                break
        return hidden

    def _path_at(self, pos) -> Path | None:
        index = self._tree.indexAt(pos)
        if not index.isValid():
            return None
        return Path(self._model.filePath(self._proxy.mapToSource(index)))

    def _file_actions(self, path: Path | None) -> list:
        """(label, callback) for the file-management part of the context
        menu. Raw file ops are delegated to the OS file manager (rename/
        copy/undo/drag-drop); only soft-delete is in-app (Anton, 2026-07-15).
        'Open in file manager' is meaningful for a DIRECTORY only (Anton) —
        folders + empty space (→ project root); a file gets Move to trash."""
        if path is None or path.is_dir():
            return [("Open in file manager",
                     lambda: self._open_in_file_manager(path))]
        if path.is_file():
            return [("Move to trash…", lambda: self._move_to_trash(path))]
        return []

    def _on_context_menu(self, pos) -> None:
        menu = QMenu(self)
        for label, cb in self._file_actions(self._path_at(pos)):
            menu.addAction(label, cb)
        menu.addSeparator()
        menu.addAction("Configure view…",
                       lambda: self.configure_requested.emit())
        # Manual override for the automatic ini watcher (Anton, 2026-07-15:
        # context menu, not an always-visible button) — needed only where
        # file events fail (network mounts, inotify limits, save races).
        menu.addAction("Reload project settings",
                       lambda: self.reload_settings_requested.emit())
        menu.exec(self._tree.viewport().mapToGlobal(pos))

    def _open_in_file_manager(self, path: Path | None) -> None:
        """Open the OS file manager at *path* (a directory) or, when nothing
        is under the cursor, the project root. Only offered for directories
        (Anton). All raw file management (add, rename, cut/paste, drag-drop,
        undo) lives here, in the tool the user already knows."""
        folder = str(path) if path is not None else self._root
        if folder and os.path.isdir(folder):
            open_with_default_app(folder)

    def _find_references(self, path: Path) -> list:
        """Text files in the project that mention *path*'s name — a
        lightweight, index-free reference check so soft-delete can warn
        before breaking a link (spec CSV, netlist, library, …). A full
        dependency graph is an ACDE Phase-2 (project index) concern."""
        name = path.name
        scan_ext = {".py", ".cir", ".net", ".slicap_sch", ".spice_sch",
                    ".sch", ".tex", ".rst", ".csv", ".lib"}
        refs = []
        root = Path(self._root)
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if not d.startswith(".")]
            for fn in filenames:
                p = Path(dirpath) / fn
                if p == path or p.suffix.lower() not in scan_ext:
                    continue
                try:
                    if name in p.read_text(encoding="utf-8",
                                           errors="ignore"):
                        refs.append(str(p.relative_to(root)))
                except OSError:
                    pass
                if len(refs) >= 20:
                    return refs
        return refs

    def _move_to_trash(self, path: Path) -> None:
        from PySide6.QtCore import QFile
        refs = self._find_references(path)
        msg = f"Move “{path.name}” to the trash?"
        if refs:
            shown = "\n  ".join(refs[:10])
            more = f"\n  … and {len(refs) - 10} more" if len(refs) > 10 else ""
            msg += ("\n\nWarning — this file is referenced by:\n  "
                    + shown + more +
                    "\n\nDeleting it may break those references.")
        ret = QMessageBox.question(
            self, "Move to trash", msg,
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if ret != QMessageBox.Yes:
            return
        if not QFile.moveToTrash(str(path)):
            QMessageBox.warning(
                self, "Move to trash",
                f"Could not move “{path.name}” to the trash.")

    def _on_double_click(self, index) -> None:
        src = self._proxy.mapToSource(index)
        self.open_path(Path(self._model.filePath(src)))

    def open_path(self, path: Path) -> None:
        """Schematics open in a canvas panel, Python files in the
        instruction editor; everything else opens with the desktop's
        default application."""
        if path.is_dir():
            return
        suffix = path.suffix.lower()
        if suffix in _SCHEMATIC_SUFFIXES:
            self._main_win.load_file(path)
        elif suffix == ".py":
            self._main_win.open_instruction_file(path)
        else:
            open_with_default_app(path)


class NewProjectDialog(QDialog):
    """Collects name/directory/author and creates the project (SLNG.md Q4–Q6).

    After ``exec()`` returns Accepted, ``project_dir`` holds the created
    project directory."""

    def __init__(self, parent=None, directory: str | None = None):
        super().__init__(parent)
        self.setWindowTitle("New SLiCAP Project")
        self.setMinimumWidth(420)
        self.project_dir: str | None = None

        layout = QFormLayout(self)
        self._name = QLineEdit(self)
        layout.addRow("Project name:", self._name)

        self._dir = QLineEdit(directory or "", self)
        browse = QPushButton("Browse…", self)
        browse.clicked.connect(self._on_browse)
        row = QWidget(self)
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 0, 0, 0)
        h.addWidget(self._dir)
        h.addWidget(browse)
        layout.addRow("Project directory:", row)

        self._author = QLineEdit(ini.author, self)
        layout.addRow("Author:", self._author)

        buttons = QDialogButtonBox(self)
        create = buttons.addButton("Create project",
                                   QDialogButtonBox.ButtonRole.AcceptRole)
        buttons.addButton(QDialogButtonBox.StandardButton.Cancel)
        create.setDefault(True)
        buttons.accepted.connect(self._on_create)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _on_browse(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self, "Select Project Directory", self._dir.text() or os.getcwd())
        if folder:
            self._dir.setText(folder)

    def _on_create(self) -> None:
        name = self._name.text().strip()
        folder = self._dir.text().strip()
        if not name or not folder:
            QMessageBox.warning(self, "New project",
                                "Please enter a project name and directory.")
            return
        folder = Path(folder)
        try:
            folder.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            QMessageBox.warning(self, "New project",
                                f"Cannot create directory:\n{e}")
            return
        # Q6: a non-empty directory is allowed after confirmation — project
        # creation never overwrites existing files (main.py excepted: it is
        # GUI-managed by design, see instr_file.py).
        if any(folder.iterdir()):
            ret = QMessageBox.question(
                self, "New project",
                f"The directory is not empty:\n{folder}\n\n"
                "Create the project here? Existing files are kept; "
                "main.py is (re)written.",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if ret != QMessageBox.Yes:
                return
        author = self._author.text().strip() or None
        main_py = write_main_py(folder, name, author=author)
        # Q5: run the generated main.py once, as a subprocess with the project
        # directory as cwd — initProject() builds the structure there.
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            proc = subprocess.run([sys.executable, main_py.name],
                                  cwd=str(folder), capture_output=True,
                                  text=True, timeout=300)
        except (OSError, subprocess.TimeoutExpired) as e:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(self, "New project",
                                 f"Could not run main.py:\n{e}")
            return
        finally:
            if QApplication.overrideCursor() is not None:
                QApplication.restoreOverrideCursor()
        if proc.returncode != 0:
            tail = "\n".join((proc.stderr or proc.stdout or "").splitlines()[-15:])
            QMessageBox.critical(self, "New project",
                                 f"Project creation failed:\n\n{tail}")
            return
        self.project_dir = str(folder)
        self.accept()
