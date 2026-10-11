"""Set one LaTeX scale for every schematic and poster under a folder.

Every .slicap_sch, .spice_sch and .slicap_poster below ROOT gets the LaTeX
scale SCALE (%) in its style sidecar (<file>.ini), and every LaTeX item in
it (fragment, parameter or model table, analysis or library block) is put
on Default, so that it follows that scale. At 100 % LaTeX is drawn at its
natural 10 pt size in a drawing at 2 units per mm (see the manual,
Preferences, "LaTeX scales").

Without --apply the script only lists what it would change. With --apply it
first writes a backup of all files it reads to ROOT/latex_scale_backup.tar.gz.
Close the schematic editor first: it rewrites the sidecar of an open
schematic when it saves.

Usage:
    python set_latex_scale.py ROOT [--scale 150] [--apply]
"""
import argparse
import json
import os
import tarfile
from pathlib import Path

PATTERNS = ("*.slicap_sch", "*.spice_sch", "*.slicap_poster")
KEYS = ("libs", "latex_fragments", "parameters", "analysis_items", "model_defs")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("root", type=Path, help="folder to search, recursively")
    ap.add_argument("--scale", type=float, default=150.0, help="LaTeX scale in %% (default 150)")
    ap.add_argument("--apply", action="store_true", help="write the changes (default: dry run)")
    args = ap.parse_args()

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    from SLiCAP.schematic.config import Style, LATEX_SCALE_VERSION

    root = args.root.resolve()
    files = sorted(p for pat in PATTERNS for p in root.rglob(pat)
                   if "/build/" not in p.as_posix())
    if not files:
        print("No schematics or posters found under", root)
        return

    if args.apply:
        backup = root / "latex_scale_backup.tar.gz"
        with tarfile.open(backup, "w:gz") as tar:
            for f in files:
                tar.add(f, arcname=str(f.relative_to(root)))
                ini = f.parent / (f.name + ".ini")
                if ini.is_file():
                    tar.add(ini, arcname=str(ini.relative_to(root)))
        print("Backup -->", backup)

    scale = f"{args.scale:g}"
    for f in files:
        try:
            data = json.loads(f.read_text())
        except ValueError as e:
            print("SKIP (not readable):", f, "-", e)
            continue
        n = 0
        for key in KEYS:
            for item in data.get(key) or []:
                if isinstance(item, dict) and item.get("latex_scale") != "default":
                    item["latex_scale"] = "default"
                    n += 1
        ini = f.parent / (f.name + ".ini")
        print(f"{n:3d} items to Default - {f.relative_to(root)}"
              + ("" if ini.is_file() else " (no sidecar: uses the default style)"))
        if not args.apply:
            continue
        if n:
            f.write_text(json.dumps(data, indent=2))
        if ini.is_file():
            style = Style(ini)              # converts older settings
            cfg = style._cfg
            if not cfg.has_section("rendering"):
                cfg.add_section("rendering")
            cfg["rendering"]["latex_scale"] = scale
            cfg["rendering"]["latex_scale_version"] = LATEX_SCALE_VERSION
            style.write(ini)
    print(len(files), "files,", "changed" if args.apply else "dry run, nothing written",
          "- LaTeX scale", scale, "%")


if __name__ == "__main__":
    main()
