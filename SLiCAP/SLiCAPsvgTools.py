#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Cropps SVG images to drawing format
# Tested on SLiCAP schematics created with Kicad
# Author: Chiel van Diepen, Crownstone/Almende The Netherlands

# pip install svgelements

import os
import argparse
from xml.etree import ElementTree as ET
from svgelements import Path, Text, Circle, Line, Rect, Ellipse
import SLiCAP.SLiCAPconfigure as ini

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
            svg_element = Line(
                x1=attrib.get("x1", "0"),
                y1=attrib.get("y1", "0"),
                x2=attrib.get("x2", "0"),
                y2=attrib.get("y2", "0"),
                transform=attrib.get("transform", "")
            )
        elif tag == "text":
            svg_element = Text(
                x=attrib.get("x", "0"),
                y=attrib.get("y", "0"),
                text=element.text or "",
                font_size=attrib.get("font-size", "10"),
                transform=attrib.get("transform", "")
            )
        elif tag == "path":
            svg_element = Path(d=attrib.get("d", ""), transform=attrib.get("transform", ""))

        if svg_element:
            return svg_element.bbox()

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

    # Save the cropped SVG
    #output_path = os.path.splitext(input_path)[0] + "_cropped.svg"
    #tree.write(output_path)
    tree.write(input_path)
    #return output_path

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="Crop an SVG file by its bounding box.")
    parser.add_argument("input_svg", help="Path to the input SVG file.")
    args = parser.parse_args()
    output_file = _crop_svg(args.input_svg)
    print(f"Cropped SVG saved to {output_file}")