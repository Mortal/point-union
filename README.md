By Mathias Rav, April 2016.
Licensed under the MIT license in case someone wants to use this in Matplotlib.

## Abstract

This project patches matplotlib to generate PDFs that render faster
when many overlapping markers are present.
Currently, only solid disk markers are supported.

## Motivation

When producing plots with many points (say, more than 10000),
the resulting PDF file can take a long time to render,
since the PDF viewer/renderer must redraw every point.

When many overlapping solid disks are present in the PDF,
faster rendering can be achieved by replacing the overlapping solid disks
by a single path representing the union of the disks.

## Solution

First, the PDF backend of matplotlib, method `draw_markers`, must be patched
with `backend_pdf.patch`. This adds an import of the `point_union` module
that, when present, changes the rendering to a single path, specified by the
function `compress_markers`.

The function `compress_markers` in `point_union.py` calls the C++ program
`union.cpp` (compiled with the included Makefile) to compute all circle-circle
intersections on the boundary of the union of the disks, as well as a list of
disks that do not intersect any other disk.
Then, a description of the union is computed by following circle-circle
intersections in a counter-clockwise fashion.

## Future work

* Ensure that the marker is indeed a solid, uniformly colored,
  fully opaque disk.
* Verify that the transformation juggling done in `compress_markers`
  works in general.
* Incorporate the `point_union` module into matplotlib.
* Incorporate `union.cpp` into matplotlib as a Python extension module
  so we don't have to invoke it as a subprocess.
* Move the circle-circle intersection traversal into the C++ code,
  since the Python implementation is a bit slow, and make the interface
  to the C++ code a bit nicer (for instance by making it aware of the
  transformations involved).
* Extend to non-disk markers.
