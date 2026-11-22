"""The schematic dialects: ONE table of what differs between them.

A schematic of the editor has a dialect, named by its file extension
(``.slicap_sch``, ``.spice_sch``, ``.system_sch``): the symbol library it
draws from, the extensions of its subcircuit packages and symbol files,
the netlist (or script) its export writes, and the label the GUI shows.
Everything that depends on the dialect reads it from this table, so a
dialect is added by one row (Anton, 2026-11-16: the forty places that
said "if NGspice, else SLiCAP" were REPLACED by lookups here).

A dialect may depend on an optional module: ``available()`` is False
when that module is not installed. The GUI then shows the dialect's menu
entry greyed out, and a file of that dialect does not open. The editor
itself works without the module.

The poster is not a dialect: it is a drawing without a circuit, kept
apart in ``project.doc_type()`` as before.
"""

from dataclasses import dataclass
from importlib.util import find_spec
from pathlib import Path

_SYMBOLS = Path(__file__).parent.parent / "files" / "symbols"


@dataclass(frozen=True)
class Dialect:
    name: str            # the type key the editor passes around
    label: str           # shown in menus, dock titles and messages
    sch_ext: str         # the schematic file
    lib_ext: "str | None"  # the subcircuit library (package) file; None when a
                           # hierarchical block is its diagram alone (SYSTEM: the
                           # ports and parameters are the diagram's document
                           # properties, nothing runs a netlist; Anton, 2026-11-19,
                           # the .system_lib declaration was REMOVED as a second
                           # authority)
    sym_ext: str         # a symbol library file (plain SVG inside)
    legacy_sym: str      # the pre-2026-09-25 project symbol file suffix
    net_ext: str         # the file the export writes for a circuit
    net_dir: str         # its project folder ("" = the project root)
    net_label: str       # what that file is called in the GUI
    block_label: str = "subcircuit"   # what a hierarchical package is called
    menu_title: str = "Circuit"       # the menu of the sheet's own entries
    models: bool = True  # SPICE-like: libraries, model definitions, analyses
    module: str = ""     # optional module the dialect needs
    # An "expressions" flag that kept the parameters of a system block out
    # of the LaTeX label path was tried and REVERTED (Anton, 2026-11-17):
    # every value renders as LaTeX, numeric or not; the preference that
    # disables LaTeX rendering is the one switch.

    @property
    def symbols_file(self) -> Path:
        """The system symbol library of the dialect."""
        return _SYMBOLS / self.name / ("Symbols" + self.sym_ext)

    def available(self) -> bool:
        """Whether the dialect can be used in this installation."""
        if not self.module:
            return True
        try:
            return find_spec(self.module) is not None
        except (ImportError, ValueError):
            return False

    def sch_filter(self) -> str:
        return "%s Schematic (*%s)" % (self.label, self.sch_ext)

    def sym_filter(self) -> str:
        return "%s symbols (*%s)" % (self.label, self.sym_ext)

    def lib_filter(self) -> str:
        return "%s subcircuit library (*%s)" % (self.label, self.lib_ext)


SLICAP = Dialect("slicap", "SLiCAP", ".slicap_sch", ".slicap_lib",
                 ".slicap_sym", "_slicap_symbol.svg",
                 ".slicap_cir", "cir", "Netlist")
NGSPICE = Dialect("ngspice", "NGspice", ".spice_sch", ".spice_lib",
                  ".spice_sym", "_spice_symbol.svg",
                  ".spice_cir", "cir", "Netlist")
SYSTEM = Dialect("system", "System", ".system_sch", None,
                 ".system_sym", "_system_symbol.svg",
                 ".py", "", "Run script", block_label="hierarchical block",
                 models=False, module="SLiCAP.SLiCAPsystem",
                 menu_title="System")

DIALECTS = (SLICAP, NGSPICE, SYSTEM)
_BY_NAME = {d.name: d for d in DIALECTS}
_BY_SCH = {d.sch_ext: d for d in DIALECTS}
_BY_LIB = {d.lib_ext: d for d in DIALECTS if d.lib_ext}
_BY_SYM = {d.sym_ext: d for d in DIALECTS}


def by_name(name) -> Dialect:
    """The dialect of a type key. An unknown key, None included, is the
    SLiCAP dialect, which every two-way decision fell back to before."""
    return _BY_NAME.get(name, SLICAP)


def of_path(path) -> Dialect:
    """The dialect of a schematic, library or symbol file by its suffix;
    SLiCAP when the suffix names none."""
    suffix = Path(path).suffix.lower()
    return _BY_SCH.get(suffix) or _BY_LIB.get(suffix) or _BY_SYM.get(suffix) or SLICAP


def is_schematic(path) -> bool:
    """Whether *path* has the schematic extension of a dialect."""
    return Path(path).suffix.lower() in _BY_SCH


def sch_suffixes() -> tuple:
    return tuple(d.sch_ext for d in DIALECTS)


def lib_suffixes() -> tuple:
    return tuple(d.lib_ext for d in DIALECTS if d.lib_ext)


def sym_suffixes() -> tuple:
    return tuple(d.sym_ext for d in DIALECTS)


def available() -> tuple:
    """The dialects this installation can use, in menu order."""
    return tuple(d for d in DIALECTS if d.available())
