"""Make the icon files of SLiCAP from SLiCAP/files/icons/slicap.svg.

Writes next to the SVG:

- slicap_<n>.png for n = 16, 24, 32, 48, 64, 128 and 256: the window icon
  of the GUI (SLiCAP.schematic.main.app_icon) and the logo of the HTML
  report (copied by hand to SLiCAP/files/sphinx/_static/html_logo.png);
- slicap.ico: all these sizes in one Windows icon file.

Qt renders the SVG, Pillow writes the ICO. Run it after every edit of the
SVG:

    python tools/make_icons.py
"""
import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ICONS = Path(__file__).resolve().parent.parent / "SLiCAP" / "files" / "icons"
SIZES = (16, 24, 32, 48, 64, 128, 256)


def main() -> int:
    from PySide6.QtCore import QByteArray, QRectF, Qt
    from PySide6.QtGui import QImage, QPainter
    from PySide6.QtSvg import QSvgRenderer
    from PySide6.QtWidgets import QApplication
    from PIL import Image

    app = QApplication.instance() or QApplication([])
    renderer = QSvgRenderer(QByteArray((ICONS / "slicap.svg").read_bytes()))
    if not renderer.isValid():
        print("slicap.svg is not a valid SVG", file=sys.stderr)
        return 1
    for size in SIZES:
        image = QImage(size, size, QImage.Format.Format_ARGB32)
        image.fill(Qt.GlobalColor.transparent)
        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        renderer.render(painter, QRectF(0, 0, size, size))
        painter.end()
        image.save(str(ICONS / ("slicap_%d.png" % size)))
    # every size from its own render, not scaled down from the largest
    images = [Image.open(ICONS / ("slicap_%d.png" % s)) for s in SIZES]
    images[-1].save(ICONS / "slicap.ico", sizes=[(s, s) for s in SIZES],
                    append_images=images[:-1])
    del app
    print("written: %s, slicap.ico" % ", ".join("slicap_%d.png" % s for s in SIZES))
    return 0


if __name__ == "__main__":
    sys.exit(main())
