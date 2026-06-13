#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Cropps SVG images to drawing format and creates a white background
# Tested on SLiCAP schematics created with Kicad
# Author: Chiel van Diepen, Crownstone/Almende The Netherlands
# Modified by Claude, adding a white background

import os
import argparse
from xml.etree import ElementTree as ET
from svgelements import Path, Text, Circle, Line, Rect, Ellipse, Polyline, Polygon
import SLiCAP.SLiCAPconfigure as ini

def _stroke_halfwidth(attrib):
    """Half the element's stroke width — how far a centered stroke paints beyond
    the geometric outline on each side.  Zero when the element has no stroke."""
    stroke = attrib.get("stroke", "none")
    if stroke in ("none", ""):
        return 0.0
    try:
        return float(attrib.get("stroke-width", "1")) / 2.0
    except (TypeError, ValueError):
        return 0.0


def _text_bbox(element, attrib):
    """Estimate a <text> element's bounding box (xmin, ymin, xmax, ymax).

    svgelements.Text.bbox() returns only the anchor point — it carries no font
    metrics — so a label's glyph extent is estimated here from its font size,
    character count, text-anchor and dominant-baseline.  The estimate is
    deliberately generous (≈0.6 em average advance) so a label is never clipped
    by a computed bounding box.
    """
    try:
        x = float(attrib.get("x", "0"))
        y = float(attrib.get("y", "0"))
        font_size = float(attrib.get("font-size", "10"))
    except (TypeError, ValueError):
        return None

    width = len(element.text or "") * 0.6 * font_size
    anchor = attrib.get("text-anchor", "start")
    if anchor == "middle":
        x0, x1 = x - width / 2.0, x + width / 2.0
    elif anchor == "end":
        x0, x1 = x - width, x
    else:
        x0, x1 = x, x + width

    # Vertical extent is intentionally renderer-agnostic.  dominant-baseline is
    # honoured inconsistently across SVG renderers — notably Qt's QSvgRenderer
    # effectively ignores "middle" and draws on the alphabetic baseline, so the
    # glyphs of a y-anchored label rise ~0.8·em above y.  Covering 0.9·em above
    # and 0.5·em below the anchor brackets both the alphabetic and the
    # middle-baseline placement, so the box never clips the text either way.
    y0, y1 = y - 0.9 * font_size, y + 0.5 * font_size

    return (x0, y0, x1, y1)


def _calculate_element_bbox(element):

    tag = element.tag.split("}")[-1]
    attrib = element.attrib
    svg_element = None

    try:
        if tag == "rect":
            svg_element = Rect(
                x=attrib.get("x", "0"),
                y=attrib.get("y", "0"),
                width=attrib.get("width", "0"),
                height=attrib.get("height", "0"),
                transform=attrib.get("transform", "")
            )
        elif tag == "circle":
            svg_element = Circle(
                cx=attrib.get("cx", "0"),
                cy=attrib.get("cy", "0"),
                r=attrib.get("r", "0"),
                transform=attrib.get("transform", "")
            )
        elif tag == "ellipse":
            svg_element = Ellipse(
                cx=attrib.get("cx", "0"),
                cy=attrib.get("cy", "0"),
                rx=attrib.get("rx", "0"),
                ry=attrib.get("ry", "0"),
                transform=attrib.get("transform", "")
            )
        elif tag == "line":
            # svgelements.Line takes start/end points positionally; the x1/y1/x2/y2
            # keywords are silently ignored, yielding an empty (crashing) line.
            svg_element = Line(
                (float(attrib.get("x1", "0")), float(attrib.get("y1", "0"))),
                (float(attrib.get("x2", "0")), float(attrib.get("y2", "0"))),
                transform=attrib.get("transform", "")
            )
        elif tag in ("polyline", "polygon"):
            cls = Polyline if tag == "polyline" else Polygon
            svg_element = cls(
                points=attrib.get("points", ""),
                transform=attrib.get("transform", "")
            )
        elif tag == "text":
            return _text_bbox(element, attrib)
        elif tag == "path":
            svg_element = Path(d=attrib.get("d", ""), transform=attrib.get("transform", ""))

        if svg_element:
            bbox = svg_element.bbox()
            if bbox:
                # A centered stroke paints half its width beyond the outline.
                hw = _stroke_halfwidth(attrib)
                if hw:
                    x1, y1, x2, y2 = bbox
                    bbox = (x1 - hw, y1 - hw, x2 + hw, y2 + hw)
            return bbox

    except Exception as e:
        print(f"Error calculating bounding box for {tag}: {e}")

    return None

def _calculate_svg_bbox(svg_root):
    """Calculate the bounding box of all visible elements in the SVG."""
    min_x, min_y, max_x, max_y = float("inf"), float("inf"), float("-inf"), float("-inf")

    for element in svg_root.iter():
        bbox = _calculate_element_bbox(element)
        if bbox:
            x1, y1, x2, y2 = bbox
            min_x, min_y = min(min_x, x1), min(min_y, y1)
            max_x, max_y = max(max_x, x2), max(max_y, y2)

    # Return None if no valid elements were found
    if min_x == float("inf") or min_y == float("inf"):
        return None

    return min_x, min_y, max_x, max_y

def _crop_svg(input_path):
    """Crop the SVG file by adjusting its viewBox and dimensions."""
    tree = ET.parse(input_path)
    root = tree.getroot()

    # Calculate the bounding box
    bbox = _calculate_svg_bbox(root)
    if not bbox:
        raise ValueError("No visible elements found to crop.")

    min_x, min_y, max_x, max_y = bbox

    # Add margin around the image
    
    min_x -= ini.svg_margin
    min_y -= ini.svg_margin
    max_x += ini.svg_margin
    max_y += ini.svg_margin
    
    width, height = max(0, max_x - min_x), max(0, max_y - min_y)

    # Update the viewBox and dimensions
    root.set("viewBox", f"{min_x} {min_y} {width} {height}")
    root.set("width", f"{width}mm")
    root.set("height", f"{height}mm")

    # Insert white background rectangle as first child
    ns  = root.tag.split("}")[0].lstrip("{") if "}" in root.tag else ""
    tag = f"{{{ns}}}rect" if ns else "rect"
    bg  = ET.Element(tag, attrib={
         "x": str(min_x), "y": str(min_y),
         "width": str(width), "height": str(height),
         "fill": "white"
    })
    root.insert(0, bg)
    tree.write(input_path)

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="Crop an SVG file by its bounding box.")
    parser.add_argument("input_svg", help="Path to the input SVG file.")
    args = parser.parse_args()
    output_file = _crop_svg(args.input_svg)
    print(f"Cropped SVG saved to {output_file}")