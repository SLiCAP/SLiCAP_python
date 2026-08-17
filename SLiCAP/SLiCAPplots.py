#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SLiCAP module with plot functions.
"""
import numpy as np
import sympy as sp
import matplotlib._pylab_helpers as plotHelp
import matplotlib.pyplot as plt
from matplotlib import get_backend
import SLiCAP.SLiCAPconfigure as ini
from random import randint
from SLiCAP.SLiCAPlex import _SCALEFACTORS
from SLiCAP.SLiCAPmath import _makeNumData, _dB_magFunc_f, _magFunc_f, _phaseFunc_f
from SLiCAP.SLiCAPmath import _delayFunc_f, _checkNumber, fullSubs
# The trace class lives in SLiCAPtraces (data layer); it is re-exported
# here so that 'from SLiCAP.SLiCAPplots import trace' keeps working.
# _gain_colors lives in SLiCAPtraces: a colour is a TRACE attribute and
# make_traces assigns it, so the map must not exist twice.
from SLiCAP.SLiCAPtraces import (trace, register_units_hint,
                                 _gain_colors)

plt.ioff() # Turn off the interactive mode for plotting

class axis(object):
    """
    Axis prototype.

    :param title: Title of the axis. The title will be placed on top of the axis.
    :type title: str
    """

    def __init__(self, title):
        self.title = title
        """
        Title (*str*) of the axis, will be placed on top of the axis
        """

        self.xLabel = False
        """
        Label (*str*) for the x-axis, e.g. 'frequency [Hz]'. Defaults to False.
        """

        self.yLabel = False
        """
        Label (*str*) for the x-axis, e.g. 'voltage [V]'. Defaults to False.
        """

        self.xScale = 'lin'
        """
        Scale (*str*) for the x-axis can be 'lin' or 'log'. Defaults to 'lin'.
        """

        self.yScale = 'lin'
        """
        Scale (*str*) for the y-axis can be 'lin' or 'log'. Defaults to 'lin'.
        """

        self.xLim = []
        """
        Limits (*list*) for the x-scale: [<xMin>, <xMax>]. Defaults to [].
        """

        self.yLim = []
        """
        Limits (*list*) for the y-scale: [<yMin>, <yMax>]. Defaults to [].
        """

        self.traces = []
        """
        List with **SLiCAPplots.trace** objects to be plotted on this axis:
        [<trace1>(,<trace2>,...,<traceN>)]. Defaults to [].
        """

        self.text = [0, 0, '']
        """
        Text (*[int, int, str]*) with relative plot position: [<xPos>, <yPos>, <text>].
        Defaults to [0, 0, ''].
        """

        self.polar = False
        """
        (*bool*) True if a polar axis is required. Defaults to False.
        """

        self.square = False
        """
        (*bool*) True keeps the axis BOX square in a multi-axis figure -
        SLiCAP's pole-zero convention (axis width = axis height), which is
        what makes a root locus readable. Set by :func:`pzAxis`. Defaults
        to False.
        """

        self.point_snap = False
        """
        (*bool*) True replaces the A/B cursors with a point-snap cursor:
        a click snaps to the nearest data point and shows its x-y value -
        vertical A/B lines mean nothing on a scatter plot. Set by
        :func:`pzAxis`. Defaults to False.
        """

        self.xScaleFactor = ''
        """
        Scale factor (*str*) for the x-scale; e.g. M for 1E6. Defaults to ''.
        """
        self.yScaleFactor = ''
        """
        Scale factor (*str*) for the y-scale; e.g. M for 1E6. Defaults to ''.
        """
        return

    def makeTraceDict(self):
        """
        Returns a dict with data of all the traces on the axis.

        :return: dictionary with key-value pairs:

                 - key: *str* label of the trace
                 - value: *SLiCAPplots.trace* trace object

        :rtype: dict
        """
        traceDict = {}
        for trc in self.traces:
            traceDict[trc.label] = trc
        return traceDict

class figure(object):
    """
    Prototype SLiCAP figure object.

    :param fileName: Name of the file for saving the figure.
    :type fileName: str
    """
    def __init__(self, fileName):

        self.fileType = ini.plot_file_type
        """
        Graphic file type (*str*) for saving the figure. Defaults to fileName
        """

        self.axisHeight = ini.axis_height
        """
        Relative height (*int, float*) of a single axis. Defaults to ini.axis_height.

        To do: absolute measures in inch or cm.
        """

        self.axisWidth = ini.axis_width
        """
        Relative width (*int, float*) of a single axis. Defaults to ini.axis_width.

        To do: absolute measures in inch or cm.
        """

        self.axes = []
        """
        List with **SLiCAPplots.axis** objects to be plotted on this figure.
        Defaults to [].
        """

        self.shareX = 'none'
        """
        (*str*) Axes sharing ONE x axis: 'none' (default), 'col' (down each
        column), 'row' (across each row) or 'all'. Sharing axes keep the same
        range and zoom together, the tick labels and the x label are drawn on
        the outer axis only, and the gap between them is closed, so a
        magnitude-over-phase pair reads as one plot with a single frequency
        axis. Only the FIRST axis of such a stack shows its title: with the
        gap closed there is no room for the others.
        """

        self.shareY = 'none'
        """
        (*str*) Axes sharing ONE y axis: 'none' (default), 'row' (across each
        row), 'col' (down each column) or 'all'. See shareX; here the y tick
        labels and y label are drawn on the outer axis only.
        """

        self.show = False
        """
        (*bool*) if 'True' the figure will be displayed with the method
        **SLiCAPplots.figure.plot()**. Defaults to [].
        """
        
        self.save = True
        """
        (*bool*) if 'True' the figure will be saved to the img folder in pdf and in svg format
        Defaults to True.
        """

        self.fileName = fileName
        """
        File name of the figure.
        """
        
        self.traceDict = {}
        """
        Dictionary with key-value pairs:

        - key: label of the trace
        - value: trace object
        """

        self.cursors = True
        """
        (*bool*) If True and show=True, attach interactive A/B cursors to each
        non-polar axis and a nearest-point cursor to each polar axis.
        The cursors stay inactive until enabled from the figure toolbar.
        Silently ignored when the active backend is non-interactive.
        Defaults to True.
        """
    def updateTracedict(self):
        """
        Updates the trace dictionary of the figure.
        """
        self.traceDict = {}
        for row in self.axes:
            for ax in row:
                # empty grid cells are the empty string, and one axis object
                # may occupy several cells (a span): both are skipped here
                if isinstance(ax, str) or ax is None:
                    continue
                for trc in ax.traces:
                    self.traceDict[trc.label] = trc
                
    def make_mpl_figure(self):
        """Build and return the matplotlib Figure without saving or closing it.

        Called by :meth:`plot` internally; also called by the GUI waveform dock
        to embed the figure in a ``FigureCanvasQTAgg`` widget.

        :return: live matplotlib Figure, or False on error.
        :rtype: matplotlib.figure.Figure or bool
        """
        axes = np.array(self.axes)
        try:
            rows, cols = axes.shape
        except:
            print('Attribute of <figure>.axes must be a list of lists or a two-dimensional array.')
            return False
        # One entry per axis, left -> right, then top -> bottom. An axis
        # object placed in several ADJACENT cells spans them (TRACES.md
        # 6.1); an empty cell is the empty string. The spans are the axis'
        # bounding box, which must be solidly filled by that same object -
        # two non-adjacent cells holding one axis are ambiguous (span, or
        # two copies) and are refused.
        axesList = []
        spans = []
        for i in range(rows):
            for j in range(cols):
                cell = axes[i][j]
                if isinstance(cell, str) or cell is None:
                    continue
                if any(cell is placed for placed in axesList):
                    continue
                cells = [(r, c) for r in range(rows) for c in range(cols)
                         if axes[r][c] is cell]
                r0 = min(r for r, _ in cells)
                r1 = max(r for r, _ in cells)
                c0 = min(c for _, c in cells)
                c1 = max(c for _, c in cells)
                if len(cells) != (r1 - r0 + 1) * (c1 - c0 + 1):
                    print("Error: axis '{0}' occupies cells that do not form "
                          "a rectangle; use a copy of the axis for a second "
                          "position.".format(getattr(cell, 'title', '')))
                    return False
                axesList.append(cell)
                spans.append((r0, r1, c0, c1))
        if len(axesList) == 0:
            print('Error: no plot data available; plotting skipped.')
            return False
        # Axis sharing: axes of one group get ONE common x (or y) axis -
        # same range, zoom together, outer tick labels only, and no gap in
        # between (TRACES.md, Anton 2026-07-29). Polar axes never share.
        shareX = getattr(self, 'shareX', 'none')
        shareY = getattr(self, 'shareY', 'none')
        explicitX = isinstance(shareX, (list, tuple))
        explicitY = isinstance(shareY, (list, tuple))
        modeX = 'group' if explicitX else str(shareX).lower()
        modeY = 'group' if explicitY else str(shareY).lower()
        if not explicitX:
            _report_useless_sharing(modeX, 'shareX', rows, cols)
        if not explicitY:
            _report_useless_sharing(modeY, 'shareY', rows, cols)

        def _quantity(axobj, which):
            label = axobj.xLabel if which == 'x' else axobj.yLabel
            return label if isinstance(label, str) and label else ''

        def _key(i, which):
            """Share-group key of axesList[i], or None (not shared).

            Sharing only makes sense between axes plotting the SAME quantity:
            'col' once welded a unit-step response to the pole-zero axis
            below it, putting seconds on an Re [Hz] scale (Anton, 2026-08-03,
            the six-view figure). Positional modes are therefore split by the
            axis LABEL. An explicit group - shareX=[[axMag, axPhase]] - is
            the user's own statement and is honoured as given.
            """
            axobj = axesList[i]
            if axobj == '' or axobj.polar:
                return None
            mode = modeX if which == 'x' else modeY
            groups = shareX if which == 'x' else shareY
            if mode == 'group':
                for g, members in enumerate(groups):
                    try:
                        if any(m is axobj for m in members):
                            return ('g', g)
                    except TypeError:
                        pass
                return None
            r0, r1, c0, c1 = spans[i]
            q = _quantity(axobj, which)
            if mode == 'all':
                return ('all', q)
            if mode == 'col':
                return ('col', c0, q)
            if mode == 'row':
                return ('row', r0, q)
            return None

        xkey = [_key(i, 'x') for i in range(len(axesList))]
        ykey = [_key(i, 'y') for i in range(len(axesList))]

        def _note_mixed(name, mode, keys):
            """Say WHERE a positional share split on unlike quantities."""
            if mode not in ('col', 'row', 'all'):
                return
            seen = {}
            for k in keys:
                if k is not None:
                    seen.setdefault(k[:-1], set()).add(k[-1])
            for pos, quantities in seen.items():
                if len(quantities) < 2:
                    continue
                where = ('the figure' if pos[0] == 'all'
                         else "{0} {1}".format(pos[0], pos[1] + 1))
                print("Note: {0}='{1}': {2} mixes quantities ({3}); only "
                      "axes plotting the same quantity share, and the gap "
                      "between unlike axes stays open.".format(
                          name, mode, where,
                          ", ".join(sorted(q or '(no label)'
                                           for q in quantities))))
        _note_mixed('shareX', modeX, xkey)
        _note_mixed('shareY', modeY, ykey)
        if explicitX or explicitY:
            for name, groups, which in (('shareX', shareX, 'x'),
                                        ('shareY', shareY, 'y')):
                if not isinstance(groups, (list, tuple)):
                    continue
                for g, members in enumerate(groups):
                    quantities = {_quantity(m, which) for m in members
                                  if getattr(m, 'polar', False) is False}
                    if len(quantities) > 1:
                        print("Note: {0} group {1} mixes quantities ({2}); "
                              "shared as asked.".format(
                                  name, g + 1,
                                  ", ".join(sorted(q or '(no label)'
                                                   for q in quantities))))

        # ── the grid: ONE gridspec, with room for titles and x labels ─────
        # Gap closing is NOT done here: nested per-column gridspecs could not
        # close a Bode pair sitting under a full-width span (Anton,
        # 2026-08-03, fig4) and left the open lanes with matplotlib's
        # too-tight default spacing (fig3). Shared stacks are closed AFTER
        # layout by repositioning their boxes - see _close_shared_stacks -
        # which works under any span.
        fig = plt.figure(figsize = (self.axisWidth*cols, rows*self.axisHeight))
        gridkw = {}
        if rows > 1:                     # room for a title above an x label
            gridkw['hspace'] = getattr(ini, 'subplot_hspace', 0.45)
        if cols > 1:
            gridkw['wspace'] = getattr(ini, 'subplot_wspace', 0.3)
        grid = fig.add_gridspec(rows, cols, **gridkw)
        _spec = lambda r0, r1, c0, c1: grid[r0:r1 + 1, c0:c1 + 1]
        closed_x_axes = set()
        closed_y_axes = set()
        _xGroups = {}     # group key -> list of (mpl axes, r0, r1, c0, c1)
        _yGroups = {}
        # Window title: the SLiCAP figure name instead of "Figure 1" etc.
        # (no-op for non-interactive backends)
        if self.fileName:
            try:
                fig.canvas.manager.set_window_title(self.fileName)
            except Exception:
                pass
        # Create the axes with their plots
        for i in range(len(axesList)):
            if axesList[i] != "":
                r0, r1, c0, c1 = spans[i]
                polar = axesList[i].polar
                kw = {}
                xKey = xkey[i]
                yKey = ykey[i]
                if xKey is not None and _xGroups.get(xKey):
                    kw['sharex'] = _xGroups[xKey][0][0]
                if yKey is not None and _yGroups.get(yKey):
                    kw['sharey'] = _yGroups[yKey][0][0]
                ax = fig.add_subplot(_spec(r0, r1, c0, c1),
                                     polar = polar, **kw)
                if getattr(axesList[i], 'square', False) and len(axesList) > 1:
                    # pole-zero axes keep a SQUARE box in a grid (Anton,
                    # 2026-08-03); a single-axis figure is already sized
                    # square by plotPZ itself, so it is left alone
                    try:
                        ax.set_box_aspect(1)
                    except Exception:
                        pass
                ax._slicap_point_snap = getattr(axesList[i], 'point_snap',
                                                False)
                if xKey is not None:
                    _xGroups.setdefault(xKey, []).append((ax, r0, r1, c0, c1))
                if yKey is not None:
                    _yGroups.setdefault(yKey, []).append((ax, r0, r1, c0, c1))
                if polar:
                    # A polar plot has no x and y axis, so it gets NO axis
                    # labels at all (Anton, 2026-08-03); the angle ticks are
                    # degrees, the radial ticks sit at 135 deg - away from a
                    # gain contour, which starts at 0 deg and dives into the
                    # lower half - and the radial QUANTITY is told by the
                    # cursor read-out, which stashes the label here.
                    try:
                        ax.set_rlabel_position(135)
                    except Exception:
                        pass
                    ax._slicap_radial = axesList[i].yLabel or ''
                if axesList[i].xLabel and not polar:
                    try:
                        ax.set_xlabel(axesList[i].xLabel)
                    except:
                        pass
                if axesList[i].yLabel and not polar:
                    try:
                        ax.set_ylabel(axesList[i].yLabel)
                    except:
                        pass
                if axesList[i].title:
                    try:
                        ax.set_title(axesList[i].title)
                    except:
                        pass
                if axesList[i].xScale:
                    try:
                         ax.set_xscale(axesList[i].xScale)
                    except:
                        pass
                if axesList[i].yScale:
                    try:
                         ax.set_yscale(axesList[i].yScale)
                    except:
                        pass
                if len(axesList[i].xLim) == 2:
                    try:
                        ax.set_xlim(axesList[i].xLim[0], axesList[i].xLim[1])
                    except:
                        pass
                if len(axesList[i].yLim) == 2:
                    try:
                        ax.set_ylim(axesList[i].yLim[0], axesList[i].yLim[1])
                    except:
                        pass
                if len(axesList[i].traces) == 0:
                    print('Error: Missing trace data for plotting!')
                    return False

                for j in range(len(axesList[i].traces)):
                    if axesList[i].traces[j].color:
                        Color = axesList[i].traces[j].color
                    else:
                        Color = ini.default_colors[j % len(ini.default_colors)]
                    if axesList[i].traces[j].marker:
                        Marker = axesList[i].traces[j].marker
                    else:
                        Marker = ini.default_markers[j % len(ini.default_markers)]
                    if axesList[i].traces[j].markerColor:
                        MarkerColor = axesList[i].traces[j].markerColor
                    else:
                        MarkerColor = ini.default_colors[j % len(ini.default_colors)]
                    if axesList[i].xScaleFactor in list(_SCALEFACTORS.keys()):
                        scaleX = 10**eval(_SCALEFACTORS[axesList[i].xScaleFactor])
                    else:
                        scaleX = 1
                    if axesList[i].yScaleFactor in list(_SCALEFACTORS.keys()):
                        scaleY = 10**eval(_SCALEFACTORS[axesList[i].yScaleFactor])
                    else:
                        scaleY = 1
                    _line, = plt.plot(axesList[i].traces[j].xData/scaleX,
                             axesList[i].traces[j].yData/scaleY,
                             label = axesList[i].traces[j].label,
                             linewidth = axesList[i].traces[j].lineWidth,
                             color = Color, marker = Marker,
                             markeredgecolor = MarkerColor,
                             markersize = axesList[i].traces[j].markerSize,
                             markeredgewidth = 2,
                             markerfacecolor = axesList[i].traces[j].markerFaceColor,
                             linestyle = axesList[i].traces[j].lineType)
                    if getattr(axesList[i].traces[j], 'polarParam',
                               None) is not None:
                        # the contour parameter travels with the LINE, so
                        # the polar cursor can name the frequency of a point
                        _line._slicap_param = axesList[i].traces[j].polarParam
                    if axesList[i].text:
                        X, Y, txt = axesList[i].text
                        plt.text(X, Y, txt, fontsize = ini.plot_fontsize)
                    # Set default font sizes and grid
                    defaultsPlot()
        # ── gap closing: reposition each shared CONTIGUOUS stack ─────────
        # A closed group reads as one plot: the members' boxes are moved so
        # the gaps vanish, their heights stretched to reclaim the gap space.
        # Only a contiguous run in one column (row) can close; a group with
        # something unshared in between - a polar axis, an unticked cell -
        # keeps scale-and-zoom linkage but stays apart.
        def _close_stack(members, vertical):
            span_sorted = sorted(members, key=lambda m: m[1 if vertical else 3])
            for a, b in zip(span_sorted, span_sorted[1:]):
                if vertical and (b[1] != a[2] + 1 or b[3] != a[3]
                                 or b[4] != a[4]):
                    return False
                if not vertical and (b[3] != a[4] + 1 or b[1] != a[1]
                                     or b[2] != a[2]):
                    return False
            boxes = [m[0] for m in span_sorted]
            positions = [b.get_position() for b in boxes]
            if vertical:
                top = positions[0].y1
                bottom = positions[-1].y0
                total = sum(pos.height for pos in positions)
                if total <= 0:
                    return False
                stretch = (top - bottom) / total
                y = top
                for b, pos in zip(boxes, positions):
                    h = pos.height * stretch
                    b.set_position([pos.x0, y - h, pos.width, h])
                    y -= h
            else:
                left = positions[0].x0
                right = positions[-1].x1
                total = sum(pos.width for pos in positions)
                if total <= 0:
                    return False
                stretch = (right - left) / total
                x = left
                for b, pos in zip(boxes, positions):
                    w = pos.width * stretch
                    b.set_position([x, pos.y0, w, pos.height])
                    x += w
            return True

        for members in _xGroups.values():
            if len(members) >= 2 and _close_stack(members, vertical=True):
                closed_x_axes.update(m[0] for m in members)
        for members in _yGroups.values():
            if len(members) >= 2 and _close_stack(members, vertical=False):
                closed_y_axes.update(m[0] for m in members)

        # ── shared axes: draw ONE axis for the group ─────────────────────
        # Tick labels and the axis label go on the outer axis only; with the
        # gap closed a title would land inside the plot above it, so only the
        # first axis of a shared stack keeps its title.
        _dropped = []
        for members in _xGroups.values():
            if len(members) < 2:
                continue
            if not all(m[0] in closed_x_axes for m in members):
                continue          # scales are shared, but the gap is open:
                                  # every axis keeps its ticks and title
            bottom = max(m[2] for m in members)          # largest end row
            top    = min(m[1] for m in members)          # smallest start row
            for mpl_ax, r0, r1, c0, c1 in members:
                if r1 != bottom:
                    mpl_ax.tick_params(labelbottom=False)
                    mpl_ax.set_xlabel('')
                if r0 != top and mpl_ax.get_title():
                    _dropped.append(mpl_ax.get_title())
                    mpl_ax.set_title('')
        for members in _yGroups.values():
            if len(members) < 2:
                continue
            if not all(m[0] in closed_y_axes for m in members):
                continue
            left = min(m[3] for m in members)            # smallest start col
            for mpl_ax, r0, r1, c0, c1 in members:
                if c0 != left:
                    mpl_ax.tick_params(labelleft=False)
                    mpl_ax.set_ylabel('')
        if _dropped:
            print("Note: shared x axis, no room for the title(s) of: "
                  + ", ".join(_dropped)
                  + "; only the first axis of a stack shows its title.")
        return fig

    def plot(self):
        """
        Creates the figure, and saves it to disk. It displays the figure if
        SLiCAPplots.figure.show == True.

        Showing does NOT block: the script continues (so all instructions of
        a run execute) and the process waits once, at exit, until every open
        figure has been closed.
        """
        fig = self.make_mpl_figure()
        if fig is False:
            return False
        # Save the figure
        if self.save:
            plt.savefig(ini.img_path + self.fileName + "." + self.fileType)
            if self.fileType.lower() != "pdf":
                plt.savefig(ini.img_path + self.fileName + ".pdf")
        if self.show:
            if self.cursors:
                for mpl_ax in fig.axes:
                    if mpl_ax.name == 'polar':
                        enable_polar_cursor(mpl_ax)
                    elif getattr(mpl_ax, '_slicap_point_snap', False):
                        enable_pz_cursor(mpl_ax)
                    else:
                        enable_ab_cursors(mpl_ax)
            _show_nonblocking()
        self.updateTracedict()
        if not self.show:
            plt.close(fig)
        return

_atexit_show_registered = False

def _report_useless_sharing(mode, name, rows, cols):
    """Say so when a sharing setting cannot do anything on THIS grid.

    'col' shares down a column, so it needs more than one row; 'row' shares
    across a row, so it needs more than one column. A 1 x 2 figure with
    shareX='col' looks exactly like no sharing at all, silently (Anton,
    2026-08-03).
    """
    if mode == 'col' and rows < 2:
        what, fix = 'a column holds one axis', "stack them in one column"
    elif mode == 'row' and cols < 2:
        what, fix = 'a row holds one axis', "put them side by side"
    elif mode == 'all' and rows * cols < 2:
        what, fix = 'there is one axis', "add another axis"
    else:
        return
    print("Note: {0}='{1}' does nothing on a {2} x {3} figure: {4}. "
          "Use '{5}', or {6}.".format(name, mode, rows, cols, what,
                                      'row' if mode == 'col' else 'col', fix))


def _show_nonblocking():
    """Show all open figures without blocking the running script.

    The process blocks ONCE, at exit, until the user has closed every figure
    window — so an instruction file executes all its instructions before any
    figure has to be closed, and the figures stay on screen afterwards.
    Harmless with non-interactive backends (matplotlib turns show into a
    warning there)."""
    global _atexit_show_registered
    plt.show(block=False)
    try:
        plt.pause(0.05)                    # let the window render
    except Exception:
        pass                               # non-interactive backend
    if not _atexit_show_registered:
        import atexit
        atexit.register(_block_until_figures_closed)
        _atexit_show_registered = True

# Printed to stdout the instant the script has finished executing but figures
# keep the process alive (see _block_until_figures_closed). The GUI instruction
# runner watches for this line to tell "run finished, only showing plots" apart
# from "still computing", so a new run is allowed while old plots stay open. It
# is emitted only under the GUI runner (SLICAP_GUI_RUN) and is swallowed there,
# never shown in the log.
_SCRIPT_DONE_SENTINEL = "\x1e__SLiCAP_SCRIPT_DONE__"

def _block_until_figures_closed():
    if plt.get_fignums():
        import os
        if os.environ.get("SLICAP_GUI_RUN"):
            print(_SCRIPT_DONE_SENTINEL, flush=True)
        plt.show(block=True)

def defaultsPlot():
    """
    Applies default settings for plots.
    """
    figures = [manager.canvas.figure for manager in plotHelp.Gcf.get_all_fig_managers()]
    for fig in figures:
        plt.tight_layout()
        for i in range(len(fig.axes)):
            fig.axes[i].title.set_fontsize(ini.plot_fontsize)
            fig.axes[i].grid(visible=True, which='major', color='0.5',linestyle='-')
            fig.axes[i].grid(visible=True, which='minor', color='0.5',linestyle=':')
            fig.axes[i].tick_params(axis="both", labelsize=ini.plot_fontsize)
            t = fig.axes[i].xaxis.get_offset_text()
            t.set_fontsize(ini.plot_fontsize)
            t = fig.axes[i].yaxis.get_offset_text()
            t.set_fontsize(ini.plot_fontsize)
            try:
                fig.axes[i].xaxis.label.set_fontsize(ini.plot_fontsize)
                fig.axes[i].yaxis.label.set_fontsize(ini.plot_fontsize)
            except:
                pass
            try:
                leg = fig.axes[i].legend(loc = ini.legend_loc,
                                borderpad = 0.2,
                                labelspacing = 0,
                                handletextpad = 0.2,
                                handlelength = 1,
                                scatterpoints = 1,
                                numpoints = 1)
                for t in leg.get_texts():
                    t.set_fontsize(ini.plot_fontsize)
            except:
                pass
    return

_INTERACTIVE_BACKENDS = {
    'qtagg', 'qt5agg', 'qt4agg', 'tkagg', 'wxagg',
    'gtk3agg', 'gtk4agg', 'macosx', 'webagg',
}

def fit_text_to_axis(text_artist, ax, base_fontsize, floor=5.5):
    """Shrink *text_artist* until it fits inside *ax*; return the size used.

    The A/B read-out lists a block per axis of a shared stack, so a Bode pair
    with five transfers is fifteen lines: at the configured font size the box
    grew past the bottom of the plot and the last entries were unreadable
    The font is reduced only as far as needed and never
    below *floor* - past that the box is simply large, which is better than
    silently cut off.

    :param text_artist: the annotation to fit.
    :type text_artist: matplotlib.text.Text

    :param ax: the axis it must stay inside.
    :type ax: matplotlib.axes.Axes

    :param base_fontsize: the size to use when it fits (ini.cursor_fontsize).
    :type base_fontsize: float

    :return: the font size that was set.
    :rtype: float
    """
    try:
        text_artist.set_fontsize(base_fontsize)
        renderer = ax.figure.canvas.get_renderer()
        box  = text_artist.get_window_extent(renderer)
        room = ax.get_window_extent(renderer).height * 0.98
        if box.height > room > 0:
            text_artist.set_fontsize(max(floor,
                                         base_fontsize * room / box.height))
    except Exception:
        pass
    return text_artist.get_fontsize()


def enable_ab_cursors(ax, readout_fn=None):
    """Attach A/B dual vertical cursors to *ax*.

    Left-click sets cursor A (blue dashed), right-click sets cursor B (red
    dashed).  When both cursors are placed:

    - A text annotation box appears in the upper-left corner of the plot
      showing x_A, x_B, ΔX and, for every data trace, y_A, y_B, ΔY.
    - The same text is printed to stdout immediately (flushed), so it appears
      in the log panel without waiting for the plot window to close.

    Pass a custom *readout_fn(x_a, x_b)* to add extra processing on top.

    Silent no-op when the active backend is non-interactive (Agg, PDF, SVG, …).

    :param ax: Matplotlib Axes to attach cursors to.
    :type ax: matplotlib.axes.Axes

    :param readout_fn: Optional extra callback ``f(x_a, x_b)`` called after
                       the built-in annotation update.
    :type readout_fn: callable or None
    """
    if get_backend().lower() not in _INTERACTIVE_BACKENDS:
        return

    cursor_a = ax.axvline(x=ax.get_xlim()[0], color='blue', linewidth=1,
                          linestyle='--', alpha=0.7)
    cursor_b = ax.axvline(x=ax.get_xlim()[0], color='red', linewidth=1,
                          linestyle='--', alpha=0.7)
    cursor_a.set_visible(False)
    cursor_b.set_visible(False)
    state = {'x_a': None, 'x_b': None}
    _cursor_active = [False]

    # ── in-plot annotation box ────────────────────────────────────────────────
    # A FIGURE artist, not an axis artist: axes are painted in order, so an
    # axis-owned box that overhangs its axis is covered by the NEXT axis - in
    # a shared Bode stack the read-out slid "behind" the lower plot (Anton,
    # 2026-08-03). Figure text draws after every axis; the transform keeps
    # the positioning in this axis' coordinates, so nothing else changes.
    _ann = ax.figure.text(
        0.01, 0.99, '',
        transform=ax.transAxes,
        va='top', ha='left',
        fontsize=ini.cursor_fontsize, fontfamily='monospace',
        bbox=dict(boxstyle='round,pad=0.5', facecolor=ini.cursor_bgcolor,
                  edgecolor='#888888', alpha=0.92, linewidth=0.8),
        visible=False, zorder=20,
    )

    # ── crosshair lines and annotation ───────────────────────────────────────
    _crosshair_active = [False]
    _ch_v = ax.axvline(x=ax.get_xlim()[0], color='green', linewidth=0.8,
                       linestyle='-', alpha=0.5)
    _ch_h = ax.axhline(y=ax.get_ylim()[0], color='green', linewidth=0.8,
                       linestyle='-', alpha=0.5)
    _ch_v.set_visible(False)
    _ch_h.set_visible(False)
    _ch_ann = ax.figure.text(  # figure-level for the same reason as _ann
        0.99, 0.99, '',
        transform=ax.transAxes,
        va='top', ha='right',
        fontsize=ini.cursor_fontsize, fontfamily='monospace',
        bbox=dict(boxstyle='round,pad=0.5', facecolor=ini.cursor_bgcolor,
                  edgecolor='green', alpha=0.92, linewidth=0.8),
        visible=False, zorder=20,
    )

    # ── toolbar toggle buttons ────────────────────────────────────────────────
    def _clear_cursors():
        cursor_a.set_visible(False)
        cursor_b.set_visible(False)
        _ann.set_visible(False)
        state['x_a'] = None
        state['x_b'] = None
        _placed[0] = False
        ax.figure.canvas.draw_idle()

    def _clear_crosshair():
        _ch_v.set_visible(False)
        _ch_h.set_visible(False)
        _ch_ann.set_visible(False)
        ax.figure.canvas.draw_idle()

    _draw_cid = [None]

    # This axis' switches, registered on the FIGURE: the toolbar belongs to
    # the figure, not to an axis, so a multi-axis figure gets ONE pair of
    # buttons that drives every axis (Anton, 2026-07-29).
    def _set_cursor_active(checked):
        _cursor_active[0] = checked
        if not checked:
            _clear_cursors()

    def _set_crosshair_active(checked):
        _crosshair_active[0] = checked
        if not checked:
            _clear_crosshair()

    _mpl_fig = ax.figure
    if not hasattr(_mpl_fig, '_slicap_cursor_switches'):
        _mpl_fig._slicap_cursor_switches = []
    _mpl_fig._slicap_cursor_switches.append((_set_cursor_active,
                                             _set_crosshair_active))

    def _add_toolbar_buttons():
        try:
            if getattr(_mpl_fig, '_slicap_cursor_buttons', False):
                return                      # already added for this figure
            # Try canvas.toolbar first, then manager.toolbar
            toolbar = _mpl_fig.canvas.toolbar
            if toolbar is None:
                try:
                    toolbar = _mpl_fig.canvas.manager.toolbar
                except Exception:
                    pass
            if toolbar is None or not hasattr(toolbar, 'addAction'):
                for set_cur, _set_ch in _mpl_fig._slicap_cursor_switches:
                    set_cur(True)
                return
            # Use the same Qt binding that matplotlib itself uses.
            # PyQt6 moved QAction from QtWidgets to QtGui.
            from matplotlib.backends.qt_compat import QtWidgets, QtGui
            QAction = getattr(QtWidgets, 'QAction', None) or QtGui.QAction
            _act_cur = QAction('Cursors', toolbar)
            _act_cur.setCheckable(True)
            _act_cur.setChecked(False)
            _act_cur.setToolTip('A/B cursors — left-click: A, right-click: B')

            _act_ch = QAction('Crosshair', toolbar)
            _act_ch.setCheckable(True)
            _act_ch.setChecked(False)
            _act_ch.setToolTip('Crosshair — follows mouse, shows values on all traces')

            def _on_cursor_toggle(checked):
                if checked and _act_ch.isChecked():
                    _act_ch.setChecked(False)
                for set_cur, _set_ch in _mpl_fig._slicap_cursor_switches:
                    set_cur(checked)

            def _on_ch_toggle(checked):
                if checked and _act_cur.isChecked():
                    _act_cur.setChecked(False)
                for _set_cur, set_ch in _mpl_fig._slicap_cursor_switches:
                    set_ch(checked)

            _act_cur.toggled.connect(_on_cursor_toggle)
            _act_ch.toggled.connect(_on_ch_toggle)
            toolbar.addSeparator()
            toolbar.addAction(_act_cur)
            toolbar.addAction(_act_ch)
            _mpl_fig._slicap_cursor_buttons = True
        except Exception as e:
            print(f'[SLiCAP] cursor toolbar setup failed: {e}')
            # no Qt toolbar — cursors always active
            for set_cur, _set_ch in _mpl_fig._slicap_cursor_switches:
                set_cur(True)

    def _on_first_draw(event):
        ax.figure.canvas.mpl_disconnect(_draw_cid[0])
        _add_toolbar_buttons()

    _draw_cid[0] = ax.figure.canvas.mpl_connect('draw_event', _on_first_draw)

    # ── readout text builder ──────────────────────────────────────────────────
    def _build_text(x_a, x_b, axes_list=None):
        """Read-out text: the x values once, then a block per axis.

        *axes_list* defaults to this axis alone. Axes that share one x axis
        pass the whole group, so the shared x values and ΔX are shown ONCE
        and every axis contributes its own traces (Anton, 2026-07-29)."""
        rows = []
        if x_a is not None:
            rows.append(f"A : {x_a:.6g}")
        if x_b is not None:
            rows.append(f"B : {x_b:.6g}")
        if x_a is not None and x_b is not None:
            rows.append(f"ΔX: {x_b - x_a:+.6g}")
        rows.append("─" * 26)
        axes_list = axes_list or [ax]
        for k, one_ax in enumerate(axes_list):
            if len(axes_list) > 1:
                # name the block: the y label says what the axis holds
                head = one_ax.get_ylabel() or one_ax.get_title() or f"axis {k + 1}"
                if k:
                    rows.append("")
                rows.append(head)
            for line in one_ax.lines:
                xd = line.get_xdata()
                yd = line.get_ydata()
                if len(xd) < 2:
                    continue
                lbl = line.get_label() or "trace"
                if lbl.startswith('_'):
                    continue
                parts = []
                if x_a is not None:
                    ya = float(np.interp(x_a, xd, np.real(yd)))
                    parts.append(f"A={ya:.6g}")
                if x_b is not None:
                    yb = float(np.interp(x_b, xd, np.real(yd)))
                    parts.append(f"B={yb:.6g}")
                if x_a is not None and x_b is not None:
                    ya2 = float(np.interp(x_a, xd, np.real(yd)))
                    yb2 = float(np.interp(x_b, xd, np.real(yd)))
                    parts.append(f"Δ={yb2 - ya2:+.6g}")
                rows.append(("  " if len(axes_list) > 1 else "") + lbl)
                rows.append("  " + "  ".join(parts))
        return '\n'.join(rows)

    def _shared_axes():
        """The axes sharing this x axis, in figure order; [] when alone."""
        try:
            siblings = ax.get_shared_x_axes().get_siblings(ax)
        except Exception:
            return []
        if len(siblings) < 2:
            return []
        order = list(ax.figure.axes)
        return sorted((s for s in siblings if s in order), key=order.index)

    # ── cursor linkage across axes sharing one x axis ────────────────────────
    # Axes that share an x axis (figure.shareX) show A and B at the SAME x:
    # setting a cursor in the magnitude plot sets it in the phase plot too,
    # each with its own y read-out (Anton, 2026-07-29).
    def _apply_cursors(x_a, x_b, show_text=True):
        """Place this axis' cursors at the given x values; no broadcast.

        *show_text* False hides this axis' read-out: for a group of axes
        sharing one x axis there is ONE read-out, on the axis last clicked,
        listing every axis of the group."""
        if x_a is not None:
            cursor_a.set_xdata([x_a, x_a])
            cursor_a.set_visible(True)
            state['x_a'] = x_a
        if x_b is not None:
            cursor_b.set_xdata([x_b, x_b])
            cursor_b.set_visible(True)
            state['x_b'] = x_b
        if not show_text:
            _ann.set_visible(False)
        elif state['x_a'] is not None or state['x_b'] is not None:
            _ann.set_text(_build_text(state['x_a'], state['x_b'],
                                      _shared_axes()))
            _ann.set_visible(True)
            _reposition_annotation()
        ax.figure.canvas.draw_idle()

    def _broadcast(x_a, x_b):
        """Send the cursor x values to the axes sharing this x axis."""
        try:
            siblings = ax.get_shared_x_axes().get_siblings(ax)
        except Exception:
            return
        setters = getattr(ax.figure, '_slicap_cursor_setters', {})
        for sibling in siblings:
            if sibling is ax:
                continue
            setter = setters.get(sibling)
            if setter is not None:
                setter(x_a, x_b, False)      # one read-out for the group

    if not hasattr(_mpl_fig, '_slicap_cursor_setters'):
        _mpl_fig._slicap_cursor_setters = {}
    _mpl_fig._slicap_cursor_setters[ax] = _apply_cursors

    # ── best-corner auto-placement (fires only on first show) ─────────────────
    _placed = [False]   # True once the user has manually dragged the annotation

    def _reposition_annotation():
        if _placed[0]:
            return
        fit_text_to_axis(_ann, ax, ini.cursor_fontsize)
        try:
            ax.figure.canvas.draw()
            renderer = ax.figure.canvas.get_renderer()
            ann_bbox = _ann.get_window_extent(renderer)
            ax_win   = ax.get_window_extent(renderer)
            aw = min(ann_bbox.width  / ax_win.width,  0.95)
            ah = min(ann_bbox.height / ax_win.height, 0.95)
        except Exception:
            aw, ah = 0.35, 0.40

        candidates = [
            (0.01, 0.99, 'top',    'left',  (0.0,    aw), (1 - ah, 1.0)),
            (0.99, 0.99, 'top',    'right', (1 - aw, 1.0),(1 - ah, 1.0)),
            (0.01, 0.01, 'bottom', 'left',  (0.0,    aw), (0.0,    ah)),
            (0.99, 0.01, 'bottom', 'right', (1 - aw, 1.0),(0.0,    ah)),
        ]
        xlim, ylim = ax.get_xlim(), ax.get_ylim()
        pts_ax = []
        for line in ax.lines:
            xd = np.asarray(line.get_xdata())
            yd = np.real(line.get_ydata())
            if len(xd) < 2 or (line.get_label() or '').startswith('_'):
                continue
            mask = ((xd >= min(xlim)) & (xd <= max(xlim)) &
                    (yd >= min(ylim)) & (yd <= max(ylim)))
            if not mask.any():
                continue
            disp = ax.transData.transform(np.column_stack([xd[mask], yd[mask]]))
            pts_ax.append(ax.transAxes.inverted().transform(disp))

        best, best_n = candidates[0], float('inf')
        for cand in candidates:
            x0, x1 = cand[4]
            y0, y1 = cand[5]
            n = sum(
                int(np.sum((p[:, 0] >= x0) & (p[:, 0] <= x1) &
                           (p[:, 1] >= y0) & (p[:, 1] <= y1)))
                for p in pts_ax
            )
            if n < best_n:
                best_n, best = n, cand

        _ann.set_position((best[0], best[1]))
        _ann.set_va(best[2])
        _ann.set_ha(best[3])

    # ── draggable annotation: the shared implementation ───────────────────
    _hit = _make_annotation_draggable(
        _ann, ax,
        on_dragged=lambda: _placed.__setitem__(0, True))

    def _on_press(event):
        if not _cursor_active[0]:
            return
        try:
            if ax.figure.canvas.toolbar.mode != '':
                return
        except Exception:
            pass
        if event.inaxes is not ax or event.xdata is None:
            return
        if _hit(event):
            return                    # dragging the box, not setting a cursor
        if event.button == 1:
            cursor_a.set_xdata([event.xdata, event.xdata])
            cursor_a.set_visible(True)
            state['x_a'] = event.xdata
        elif event.button == 3:
            cursor_b.set_xdata([event.xdata, event.xdata])
            cursor_b.set_visible(True)
            state['x_b'] = event.xdata
        if state['x_a'] is not None or state['x_b'] is not None:
            text = _build_text(state['x_a'], state['x_b'], _shared_axes())
            _ann.set_text(text)
            _ann.set_visible(True)
            _reposition_annotation()
            if readout_fn is not None and state['x_a'] is not None and state['x_b'] is not None:
                readout_fn(state['x_a'], state['x_b'])
        _broadcast(state['x_a'], state['x_b'])
        ax.figure.canvas.draw_idle()

    def _on_motion(event):
        if not _crosshair_active[0]:
            return
        if event.inaxes is not ax or event.xdata is None:
            _ch_v.set_visible(False)
            _ch_h.set_visible(False)
            _ch_ann.set_visible(False)
            ax.figure.canvas.draw_idle()
            return

        x = event.xdata
        best_y = event.ydata
        best_dist = float('inf')
        for line in ax.lines:
            xd = np.asarray(line.get_xdata())
            yd = np.real(np.asarray(line.get_ydata()))
            if len(xd) < 2 or (line.get_label() or '').startswith('_'):
                continue
            xmin, xmax = float(np.min(xd)), float(np.max(xd))
            if not (xmin <= x <= xmax):
                continue
            yi = float(np.interp(x, xd, yd))
            if abs(yi - event.ydata) < best_dist:
                best_dist = abs(yi - event.ydata)
                best_y = yi

        _ch_v.set_xdata([x, x])
        _ch_h.set_ydata([best_y, best_y])
        _ch_v.set_visible(True)
        _ch_h.set_visible(True)

        rows = [f"x : {x:.6g}", "─" * 22]
        for line in ax.lines:
            xd = np.asarray(line.get_xdata())
            yd = np.real(np.asarray(line.get_ydata()))
            if len(xd) < 2 or (line.get_label() or '').startswith('_'):
                continue
            xmin, xmax = float(np.min(xd)), float(np.max(xd))
            if not (xmin <= x <= xmax):
                continue
            yi = float(np.interp(x, xd, yd))
            rows.append(f"{line.get_label() or 'trace'}: {yi:.6g}")
        _ch_ann.set_text('\n'.join(rows))
        _ch_ann.set_visible(True)
        ax.figure.canvas.draw_idle()

    ax.figure.canvas.mpl_connect('button_press_event', _on_press)
    ax.figure.canvas.mpl_connect('motion_notify_event', _on_motion)


def polar_readout(line, idx, theta, r, radial_label=""):
    """The text a polar-cursor click shows for point *idx* of *line*.

    A designer reads a polar gain plot by asking WHERE on the contour a
    point sits, so the first line is the sweep value - the frequency the
    renderer stashed on the line (``_slicap_param``). What it used to print
    was ``idx=157``, which says nothing, and it went to
    the console, flooding the log panel.

    :param line: the matplotlib line that was hit.
    :param idx: index of the snapped point.
    :param theta: its angle in radians.
    :param r: its radius.
    :param radial_label: the axis' radial label, e.g. 'magnitude [dB]';
                         its bracket names the radius units.
    :return: the read-out text.
    :rtype: str
    """
    label = line.get_label() or "trace"
    rows = [label]
    param = getattr(line, '_slicap_param', None)
    if param is not None:
        name, units, values = param
        values = np.asarray(values)
        if 0 <= idx < len(values):
            rows.append("{0} = {1:.5g} {2}".format(name, values[idx], units))
    r_units = ""
    if "[" in radial_label and radial_label.endswith("]"):
        r_units = " " + radial_label[radial_label.index("[") + 1:-1]
    rows.append("|H| = {0:.5g}{1}".format(r, r_units))
    rows.append("angle = {0:.2f} deg".format(np.degrees(theta)))
    return "\n".join(rows)


def _make_annotation_draggable(ann, ax, on_dragged=None):
    """Make the read-out box *ann* draggable with the mouse.

    ONE implementation for every cursor read-out - A/B, polar and
    pole-zero (Anton, 2026-08-03: the polar box was fixed while the A/B box
    could be dragged). Returns a ``hit(event)`` predicate the caller's click
    handler must consult, so a press ON the box starts a drag instead of
    moving the cursor under it.

    :param ann: the annotation (a figure text in ax.transAxes coordinates).
    :param ax: the axis whose coordinate frame the annotation uses.
    :param on_dragged: called once when a drag completes (the A/B cursor
                       uses it to freeze its automatic placement).
    :return: hit(event) -> bool.
    """
    drag = {'on': False, 'moved': False,
            'x0': 0.0, 'y0': 0.0, 'ax0': 0.0, 'ay0': 0.0}

    def hit(event):
        if not ann.get_visible():
            return False
        try:
            renderer = ax.figure.canvas.get_renderer()
            return ann.get_window_extent(renderer).contains(event.x, event.y)
        except Exception:
            return False

    def on_press(event):
        try:
            if ax.figure.canvas.toolbar.mode != '':
                return
        except Exception:
            pass
        if hit(event):
            drag['on'] = True
            drag['moved'] = False
            drag['x0'] = event.x
            drag['y0'] = event.y
            pos = ann.get_position()
            drag['ax0'], drag['ay0'] = pos[0], pos[1]

    def on_motion(event):
        if not drag['on']:
            return
        try:
            win = ax.get_window_extent(ax.figure.canvas.get_renderer())
            ann.set_position((drag['ax0'] + (event.x - drag['x0']) / win.width,
                              drag['ay0'] + (event.y - drag['y0'])
                              / win.height))
            drag['moved'] = True
            ax.figure.canvas.draw_idle()
        except Exception:
            pass

    def on_release(_event):
        if drag['on'] and drag['moved'] and on_dragged is not None:
            on_dragged()
        drag['on'] = False

    canvas = ax.figure.canvas
    canvas.mpl_connect('button_press_event', on_press)
    canvas.mpl_connect('motion_notify_event', on_motion)
    canvas.mpl_connect('button_release_event', on_release)
    return hit


def pz_readout(line, x, y, xlabel="", ylabel=""):
    """The text a point-snap click shows: the point's x-y value.

    Vertical A/B cursors mean nothing on a scatter plot;
    a pole or zero is a POINT, so the read-out names it and gives both
    coordinates in the axis units (the brackets of 'Re [Hz]' / 'Im [Hz]').

    :param line: the matplotlib line that was hit.
    :param x: the point's x value (already in axis units).
    :param y: the point's y value.
    :param xlabel: the axis x label, its bracket holding the units.
    :param ylabel: the axis y label.
    :return: the read-out text.
    :rtype: str
    """
    def name_and_units(label, fallback):
        if "[" in label and label.endswith("]"):
            return (label[:label.index("[")].strip() or fallback,
                    " " + label[label.index("[") + 1:-1])
        return (label.strip() or fallback, "")

    x_name, x_units = name_and_units(xlabel, "x")
    y_name, y_units = name_and_units(ylabel, "y")
    return "\n".join([line.get_label() or "point",
                      "{0} = {1:.5g}{2}".format(x_name, x, x_units),
                      "{0} = {1:.5g}{2}".format(y_name, y, y_units)])


def enable_pz_cursor(ax):
    r"""Attach a point-snap cursor to a scatter *ax* (pole-zero plot).

    A click snaps to the nearest data point of any trace and shows its
    coordinates on the figure. Distances are measured in AXIS fractions, so
    a root locus with \|Re\| >> \|Im\| still snaps to what the eye is near.

    Silent no-op when the active backend is non-interactive.

    :param ax: matplotlib Axes to attach the cursor to.
    :type ax: matplotlib.axes.Axes
    """
    if get_backend().lower() not in _INTERACTIVE_BACKENDS:
        return

    # FILLED, deliberately: an open circle on a pole-zero plot reads as a
    # ZERO (Anton, 2026-08-03)
    marker, = ax.plot([], [], 'ko', markersize=8, zorder=10)
    _ann = ax.figure.text(
        0.02, 0.98, '',
        transform=ax.transAxes,
        va='top', ha='left',
        fontsize=ini.cursor_fontsize, fontfamily='monospace',
        bbox=dict(boxstyle='round,pad=0.5', facecolor=ini.cursor_bgcolor,
                  edgecolor='#888888', alpha=0.92, linewidth=0.8),
        visible=False, zorder=20,
    )

    _hit = _make_annotation_draggable(_ann, ax)

    def _on_click(event):
        if _hit(event):
            return                    # dragging the box, not snapping
        if event.inaxes is not ax or event.xdata is None:
            return
        x0, x1 = ax.get_xlim()
        y0, y1 = ax.get_ylim()
        sx = (x1 - x0) or 1.0
        sy = (y1 - y0) or 1.0
        best = None
        best_dist = np.inf
        for line in ax.lines:
            if line is marker:
                continue
            xd = np.asarray(line.get_xdata(), dtype=float)
            yd = np.asarray(line.get_ydata(), dtype=float)
            if len(xd) == 0:
                continue
            dists = (((xd - event.xdata) / sx) ** 2
                     + ((yd - event.ydata) / sy) ** 2)
            i = int(np.argmin(dists))
            if dists[i] < best_dist:
                best_dist = dists[i]
                best = (line, xd[i], yd[i])
        if best is None:
            return
        line, x, y = best
        marker.set_data([x], [y])
        _ann.set_text(pz_readout(line, x, y, ax.get_xlabel(),
                                 ax.get_ylabel()))
        _ann.set_visible(True)
        ax.figure.canvas.draw_idle()

    ax.figure.canvas.mpl_connect('button_press_event', _on_click)


def enable_polar_cursor(ax):
    """Attach a nearest-point cursor to a polar *ax*.

    A mouse click snaps to the closest data point on any trace and shows a
    read-out ON THE FIGURE - the sweep value (frequency) of the point, the
    radius in the axis' units, and the angle in degrees. Clicking empty
    space hides it.

    Silent no-op when the active backend is non-interactive.

    :param ax: Polar matplotlib Axes to attach the cursor to.
    :type ax: matplotlib.axes.Axes
    """
    if get_backend().lower() not in _INTERACTIVE_BACKENDS:
        return

    marker, = ax.plot([], [], 'ko', markersize=8, zorder=10)
    # a FIGURE artist, like the A/B read-out: it may overhang the axis, and
    # figure text draws above every axis
    _ann = ax.figure.text(
        0.02, 0.98, '',
        transform=ax.transAxes,
        va='top', ha='left',
        fontsize=ini.cursor_fontsize, fontfamily='monospace',
        bbox=dict(boxstyle='round,pad=0.5', facecolor=ini.cursor_bgcolor,
                  edgecolor='#888888', alpha=0.92, linewidth=0.8),
        visible=False, zorder=20,
    )

    _hit = _make_annotation_draggable(_ann, ax)

    def _on_click(event):
        if _hit(event):
            return                    # dragging the box, not snapping
        if event.inaxes is not ax or event.xdata is None:
            return
        theta_click, r_click = event.xdata, event.ydata
        best = None
        best_dist = np.inf
        for line in ax.lines:
            if line is marker:
                continue
            xd = np.asarray(line.get_xdata())   # angle (radians)
            yd = np.asarray(line.get_ydata())   # radius
            if len(xd) == 0:
                continue
            dists = (xd - theta_click) ** 2 + (yd - r_click) ** 2
            i = int(np.argmin(dists))
            if dists[i] < best_dist:
                best_dist = dists[i]
                best = (line, i, xd[i], yd[i])
        if best is None:
            return
        line, idx, theta, r = best
        marker.set_data([theta], [r])
        _ann.set_text(polar_readout(line, idx, theta, r,
                                    getattr(ax, '_slicap_radial', '')))
        _ann.set_visible(True)
        ax.figure.canvas.draw_idle()

    ax.figure.canvas.mpl_connect('button_press_event', _on_click)

def _undefined_params(yData, fileName):
    """True if *yData* still contains parameters other than the sweep
    symbols (Laplace variable, frequency, time) — plotting would fail on
    them. Tells the user which parameters and how to fix it (SLNG.md,
    Anton 2026-07-11: forgotten pardefs='circuit' must give a warning,
    not a crash or a silently missing plot)."""
    if not isinstance(yData, sp.Basic):
        return False
    extra = yData.atoms(sp.Symbol) - {ini.laplace, ini.frequency,
                                      sp.Symbol('t')}
    if extra:
        print("Error: plot '{0}': undefined parameter(s): {1}. Substitute "
              "the circuit parameters in the instruction first, e.g. with "
              "pardefs='circuit'.".format(
                  fileName, ', '.join(sorted(str(s) for s in extra))))
        return True
    return False

_PLOT_DATA_TYPES = ['laplace', 'numer', 'denom', 'noise', 'step', 'impulse',
                    'time', 'params', None]
_FUNC_TYPES      = ['mag', 'dBmag', 'phase', 'delay', 'time', 'onoise',
                    'inoise', 'param']
_AXIS_TYPES      = ['lin', 'log', 'semilogx', 'semilogy', 'polar']
_FREQ_TYPES      = ['laplace', 'numer', 'denom', 'noise']
_TIME_TYPES      = ['time', 'impulse', 'step']


def sweepData(results, sweepStart, sweepStop, sweepNum, sweepMethod='auto',
              sweepVar='auto'):
    """
    Evaluates a SLiCAP result over a sweep and returns the numbers as a
    :class:`SLiCAPtraces.dataset`, ready for
    :func:`SLiCAPtraces.make_traces` and :func:`SLiCAPtraces.measure`.

    A SLiCAP result is SYMBOLIC - `laplace` is an expression in *s* - so it
    has no sweep of its own; NGspice hands over numbers, SLiCAP hands over a
    formula. This function supplies the missing sweep, which is why the traces
    dialog asks for start / stop / points 

    It lives here, with the rest of the plot machinery, and it DEPENDS on
    SLiCAPtraces rather than the other way round: producers -> traces ->
    plots.

    The signals are the result's own attributes, which are already Python
    identifiers, so no name mapping is needed:

    - *laplace*, *numer*, *denom*: COMPLEX arrays, s replaced by 2*pi*j*f
      (``ini.hz``) or j*omega, so ``dB(...)``, ``phase(...)``, ``delay(...)``
      and magnitude-by-default all work on them;
    - *noise*: ``onoise`` and ``inoise`` (V^2/Hz), plus one signal per noise
      source from ``onoiseTerms`` / ``inoiseTerms``, named
      ``onoise_<source>`` - the symbolic counterpart of NGspice's
      ``onoise_r1``;
    - *time*, *impulse*, *step*: real arrays over *t*.

    A stepped result carries one expression per run, so its signals become
    2-D (n_runs, n_sweep) and ``step_params`` holds the step values - exactly
    like a stepped NGspice sweep. The circuit's numeric parameter definitions
    become ``dataset.params``.

    Trace data stays in BASE UNITS (Hz, s, V): scaling belongs to the axis,
    never to the trace, so this function has no
    counterpart of ``plotSweep``'s *sweepScale*.

    :param results: result of one SLiCAP instruction.
    :type results: SLiCAPinstruction.instruction

    :param sweepStart: start of the sweep; SLiCAP notation ('10', '1M').
    :type sweepStart: str, float, int

    :param sweepStop: end of the sweep.
    :type sweepStop: str, float, int

    :param sweepNum: number of points.
    :type sweepNum: str, int

    :param sweepMethod: 'lin' or 'log'; 'auto' takes 'log' for a frequency
                        sweep and 'lin' for a time sweep.
    :type sweepMethod: str

    :param sweepVar: name of the swept parameter for ``dataType='params'``;
                     'auto' for the frequency or time sweep of the other data
                     types.
    :type sweepVar: str

    :return: the evaluated data, or None when the result cannot be swept.
    :rtype: SLiCAPtraces.dataset, NoneType

    :Example:

    >>> D   = sl.sweepData(LAPLACE1, 10, "1M", 200)
    >>> TR  = sl.make_traces(D, [{"y": "dB(laplace)"}])
    >>> A_0 = sl.measure(D, "Y_AT_X(dB(laplace), 1e3)", units="dB")
    """
    from SLiCAP.SLiCAPtraces import dataset
    from SLiCAP.SLiCAPmath import _makeNumData, _freq_response, fullSubs
    from SLiCAP.SLiCAPlex import _scale_float

    if isinstance(results, list):
        print("Error: sweepData() takes ONE result; combining results is what "
              "an axis does (TRACES.md phase 7).")
        return None
    dataType = getattr(results, "dataType", None)
    if dataType not in _PLOT_DATA_TYPES or dataType is None:
        print("Error: cannot sweep dataType '{0}'.".format(dataType))
        return None
    try:
        start = _scale_float(sweepStart)
        stop  = _scale_float(sweepStop)
        num   = int(_scale_float(sweepNum))
    except (ValueError, TypeError):
        print("Error: the sweep needs numbers in SLiCAP notation "
              "('10', '1M'); got {0}, {1}, {2}.".format(sweepStart, sweepStop,
                                                        sweepNum))
        return None
    if sweepMethod == 'auto':
        sweepMethod = 'lin' if dataType in _TIME_TYPES else 'log'
    if sweepMethod == 'log':
        if start <= 0 or stop <= 0:
            print("Error: a logarithmic sweep needs positive limits.")
            return None
        x = np.geomspace(start, stop, num)
    else:
        x = np.linspace(start, stop, num)

    # the abscissa of a time-domain result is 't', SLiCAP's own symbol - NOT
    # 'time', which is the name of the RESULT ATTRIBUTE (result.time) and
    # would collide with it in an expression
    x_name = 't' if dataType in _TIME_TYPES else 'frequency'
    x_var  = sp.Symbol('t') if dataType in _TIME_TYPES else ini.frequency

    def _numeric(expression):
        """One expression -> one array over the sweep."""
        if dataType in _FREQ_TYPES and dataType != 'noise':
            response = _freq_response(expression, x)
            if response is not None:
                return response                     # complex, fast path
            data = sp.N(expression)
            if ini.hz:
                data = data.xreplace({ini.laplace: 2*sp.pi*sp.I*ini.frequency})
            else:
                data = data.xreplace({ini.laplace: sp.I*ini.frequency})
            return np.asarray(_makeNumData(data, ini.frequency, x,
                                           normalize=False), dtype=complex)
        return np.asarray(_makeNumData(sp.N(expression), x_var, x,
                                       normalize=False), dtype=float)

    def _attribute(name):
        """The result attribute as a list of expressions, one per run."""
        value = getattr(results, name, None)
        if value is None or (isinstance(value, list) and not value):
            return []
        return value if isinstance(value, list) else [value]

    wanted = {'laplace': ['laplace'], 'numer': ['numer'], 'denom': ['denom'],
              'time': ['time'], 'impulse': ['impulse'], 'step': ['stepResp'],
              'noise': ['onoise', 'inoise']}.get(dataType, [])
    signals = {}
    for name in wanted:
        runs = _attribute(name)
        if not runs:
            continue
        arrays = [_numeric(expression) for expression in runs]
        signals[name] = arrays[0] if len(arrays) == 1 else np.array(arrays)
    if dataType == 'noise':
        # per-source contributions: the symbolic counterpart of NGspice's
        # onoise_r1 (Anton, 2026-08-01)
        for attribute, prefix in (("onoiseTerms", "onoise"),
                                  ("inoiseTerms", "inoise")):
            terms = getattr(results, attribute, None) or {}
            for source, expression in terms.items():
                name = "{0}_{1}".format(prefix, str(source))
                name = "".join(c if (c.isalnum() or c == "_") else "_"
                               for c in name)
                runs = expression if isinstance(expression, list) else [expression]
                arrays = [_numeric(one) for one in runs]
                signals[name] = arrays[0] if len(arrays) == 1 else np.array(arrays)
    if not signals:
        print("Error: result '{0}' holds no data to sweep.".format(dataType))
        return None

    step_params = {}
    if getattr(results, "step", False):
        if getattr(results, "stepVar", None) is not None:
            step_params[str(results.stepVar)] = np.asarray(
                results.stepList, dtype=float)
        elif getattr(results, "stepVars", None):
            rows = np.asarray(results.stepArray, dtype=float)
            for j, name in enumerate([str(v) for v in results.stepVars]):
                if j < rows.shape[0]:
                    step_params[name] = rows[j]

    params = {}
    for symbol, value in (getattr(getattr(results, "circuit", None),
                                  "parDefs", None) or {}).items():
        try:
            params[str(symbol)] = float(sp.N(fullSubs(value,
                                                      results.circuit.parDefs)))
        except (TypeError, ValueError):
            continue
    # What only the RESULT knows: a transfer is detector units over source
    # units, noise is squared detector units per Hz. The naming conventions
    # cannot answer these (Anton, 2026-08-02).
    units = {x_name: ("s" if dataType in _TIME_TYPES
                      else ("Hz" if ini.hz else "rad/s"))}
    for name in signals:
        found = _slicap_units_hint(name, results)
        if found:
            units[name] = found
    return dataset(x_name=x_name, x_data=x, signals=signals,
                   step_params=step_params, params=params, units=units,
                   gain_type=getattr(results, "gainType", None))


def _slicap_units_hint(name, result=None):
    """Units of the signals :func:`sweepData` writes.

    The name alone cannot say them: ``onoise`` is V^2/Hz for a voltage
    detector and A^2/Hz for a current one, and a transfer is detector units
    over source units. They are read from the result, exactly as the axis
    labels of :func:`plotSweep` read them (Anton, 2026-07-30: units are
    stated, and suggested only where something KNOWS them).
    """
    if result is None:
        return None
    det = getattr(result, "detUnits", "") or ""
    src = getattr(result, "srcUnits", "") or ""
    if name in ("laplace", "numer", "denom"):
        return "{0}/{1}".format(det, src) if det and src else det or None
    if name in ("time", "impulse", "stepResp"):
        return det or None
    if name == "onoise" or name.startswith("onoise_"):
        return "{0}^2/Hz".format(det) if det else None
    if name == "inoise" or name.startswith("inoise_"):
        return "{0}^2/Hz".format(src) if src else None
    return None


register_units_hint(_slicap_units_hint)


def plot_defaults(result, funcType = 'auto', axisType = 'auto',
                  sweepVar = 'auto', yVar = 'auto'):
    """
    Resolves the presentation defaults that follow from a SLiCAP result.

    This is the "no user programming required" behaviour of
    :func:`plotSweep` made queryable: which function is plotted, on which
    type of axis, with which axis scales. :func:`plotSweep` uses it, and a
    GUI can call it to PRE-FILL its fields from the selected result instead
    of presenting empty ones.

    Error messages are printed here, exactly as :func:`plotSweep` printed
    them, and None is returned.

    :param result: instruction result object.
    :type result: SLiCAPinstruction.instruction

    :param funcType: requested function type, or 'auto' to derive it from
                     the result's dataType. Defaults to 'auto'.
    :type funcType: str

    :param axisType: requested axis type, or 'auto' to derive it from the
                     function type. Defaults to 'auto'.
    :type axisType: str

    :param sweepVar: name of the sweep variable; only checked for
                     funcType='param'. Defaults to 'auto'.
    :type sweepVar: str

    :param yVar: parameter plotted along the y axis; only checked for
                 funcType='param'. Defaults to 'auto'.
    :type yVar: str

    :return: dictionary with the resolved settings, or None on error:

             - dataType:   the result's data type
             - funcType:   resolved function type
             - axisType:   resolved axis type
             - xAxisScale: 'lin' or 'log' for the x axis
             - yAxisScale: 'lin' or 'log' for the y axis
             - polar:      True for a polar axis
             - funcTypes:  the selectable function types
             - axisTypes:  the selectable axis types

    :rtype: dict, NoneType
    """
    dataType = result.dataType
    if dataType not in _PLOT_DATA_TYPES:
        print("Error: cannot plot dataType '{0}' with 'plotSweep()'.".format(dataType))
        return None
    if funcType == 'auto':
        if dataType == 'noise':
            funcType = 'onoise'
        elif dataType in _FREQ_TYPES:
            funcType = 'mag'
        elif dataType in _TIME_TYPES:
            funcType = 'time'
    elif funcType == 'param':
        if sweepVar == 'auto':
            print("Error: undefined sweep variable.")
            return None
        if yVar == 'auto':
            print("Error: missing parameter to be plotted.")
            return None
    elif funcType not in _FUNC_TYPES:
        print("Error: unknown funcType: '{0}'.".format(funcType))
        return None
    if axisType == 'auto':
        if funcType == 'param':
            axisType = 'lin'
        elif funcType == 'mag' or dataType == 'noise':
            axisType = 'log'
        elif funcType == 'dBmag' or funcType == 'phase' or funcType == 'delay':
            axisType = 'semilogx'
        elif funcType == 'time':
            axisType = 'lin'
    elif axisType not in _AXIS_TYPES:
        print("Error: unknown axisType: '{0}'.".format(axisType))
        return None
    scales = {'lin':      ('lin', 'lin', False),
              'log':      ('log', 'log', False),
              'semilogx': ('log', 'lin', False),
              'semilogy': ('lin', 'log', False),
              'polar':    ('lin', 'lin', True)}
    xAxisScale, yAxisScale, polar = scales.get(axisType, ('lin', 'lin', False))
    return {'dataType':   dataType,
            'funcType':   funcType,
            'axisType':   axisType,
            'xAxisScale': xAxisScale,
            'yAxisScale': yAxisScale,
            'polar':      polar,
            'funcTypes':  list(_FUNC_TYPES),
            'axisTypes':  list(_AXIS_TYPES)}


# Two routes into an axis stay side by side: automatic axes from results
# (here) and composed axes from trace dictionaries (traceAxis). sweepAxis was
# removed from the public API on 2026-08-02 ("one route into an axis") and
# REINSTATED on 2026-08-03: Anton's GUI walkthrough showed the trace route is
# right for expressions and post-processing but MORE work for the standard
# SLiCAP plot, which is the common case.
def sweepAxis(title, results, sweepStart, sweepStop, sweepNum,
              sweepVar = 'auto', sweepScale = '', xVar = 'auto', xScale = '',
              xUnits = '', xLim = [], yLim = [], axisType = 'auto',
              funcType = 'auto', yVar = 'auto', yScale = '', yUnits = '',
              noiseSources = None, name = '', traces = None):
    """
    Creates an axis with traces of a swept (and optionally stepped) SLiCAP
    result, WITHOUT creating a figure - the fully AUTOMATIC route: funcType,
    axis scales, labels and gain colours all follow from the result, exactly
    as :func:`plotSweep` has always done (plotSweep is this function plus the
    figure).

    *traces* adds ready trace objects to the same axis - a trace, a trace
    dictionary, or a list of either, as :func:`traceAxis` takes them - so a
    measured NGspice curve can sit beside the SLiCAP transfers. The axis
    scale factors apply to them identically: trace data is in base units on
    both routes.

    This is :func:`plotSweep` without the figure: same arguments, same
    automatic behaviour - funcType, sweep variable, axis type, units, axis
    labels, trace labels and colours all follow from the result - but it
    returns the :class:`axis` object, so it can be placed on a figure of any
    layout with :func:`makeFigure`; a magnitude and a phase axis on one
    figure, for instance.

    :param title: Title of the axis.
    :type title: str

    :param name: Name used in warning messages only; :func:`plotSweep`
                 passes the figure file name. Defaults to ''.
    :type name: str

    For all other arguments see :func:`plotSweep`.

    :return: axis object, or False when the result cannot be plotted.
    :rtype: SLiCAPplots.axis, bool
    """
    freqTypes  = _FREQ_TYPES
    timeTypes  = _TIME_TYPES
    ax = axis(title)
    ax.polar = False
    if type(results) != list:
        results = [results]
    colNum = 0
    numColors = len(ini.default_colors)
    # first results defines the axis type and labels
    result = results[0]
    # Which function, on which type of axis, with which scales: everything
    # that follows from the result itself (see plot_defaults).
    defaults = plot_defaults(result, funcType=funcType, axisType=axisType,
                             sweepVar=sweepVar, yVar=yVar)
    if defaults is None:
        return False
    funcType  = defaults['funcType']
    axisType  = defaults['axisType']
    ax.xScale = defaults['xAxisScale']
    ax.yScale = defaults['yAxisScale']
    ax.polar  = defaults['polar']
    if funcType == 'param' and xVar == 'auto':
        xVar = sweepVar
        xScale = sweepScale
    if not ax.polar:
        if funcType == 'param' and xVar != sweepVar:
            ax.xScaleFactor = xScale
        else:
            ax.xScaleFactor = sweepScale
    ax.yScaleFactor = yScale
    ax.xLim = xLim
    ax.yLim = yLim
    ax.traces = []
    # Create the axis labels
    # For parameter plots: the parameter names with units and scalefactors
    if funcType == 'param':
        ax.xLabel = '$' + sp.latex(sp.Symbol(xVar)) + '$ [' + xScale + xUnits + ']'
        if type(yVar) != list:
            yVar = [yVar]
        names = '$'
        for i in range(len(yVar)):
            names += sp.latex(sp.Symbol(yVar[i])) + '\\,'
        names += '$'
        ax.yLabel =  names + ' [' + yScale + yUnits + ']'
    # For time frequency plots we use frequency 'Hz' or 'rad/s' along the x-axis
    elif result.dataType in freqTypes:
        if result.dataType == 'noise':
            if funcType == 'onoise':
                yUnits = result.detUnits
            if funcType == 'inoise':
                yUnits = result.srcUnits
            ax.xLabel = 'frequency [' + sweepScale + 'Hz]'
        elif ini.hz == True:
            ax.xLabel = 'frequency [' + sweepScale + 'Hz]'
        else:
            ax.xLabel = 'frequency [' + sweepScale + 'rad/s]'
    # For time plots we use time along the x-axis
    elif funcType in timeTypes:
        ax.xLabel = 'time [' + sweepScale + 's]'
        if yUnits == '':
            yUnits = result.detUnits
    # Create the y-label for other than parameter plots
    if funcType == 'mag':
        ax.yLabel = 'magnitude [' + yScale + yUnits + ']'
    elif funcType == 'dBmag':
        ax.yLabel = 'magnitude [' + yScale + 'dB]'
    elif funcType == 'phase':
        if ini.hz == True:
            ax.yLabel = 'phase [' + yScale + 'deg]'
        else:
            ax.yLabel = 'phase [' + yScale + 'rad]'
    elif funcType == 'delay':
        ax.yLabel = 'group delay [' + yScale + 's]'
    elif funcType == 'time':
        ax.yLabel = '[' + yScale + yUnits + ']'
    elif funcType == 'onoise':
        ax.yLabel = 'spectral density [$\\left(' + yScale + yUnits +'\\right)^2/Hz$]'
    elif funcType == 'inoise':
        ax.yLabel = 'spectral density [$\\left(' + yScale + yUnits +'\\right)^2/Hz$]'
    # Create the sweep, lin or log depending on the x-axis type
    try:
        xScaleFactor = 10**int(_SCALEFACTORS[sweepScale])
    except:
        xScaleFactor = 1.
    if ax.xScale == 'log' or ax.xScale == 'semilogx' or ax.polar == True:
        x = np.geomspace(float(_checkNumber(sweepStart))*xScaleFactor, 
                         float(_checkNumber(sweepStop))*xScaleFactor, 
                         int(_checkNumber(sweepNum)))
    elif ax.xScale == 'lin' or ax.xScale == 'semilogy':
        x = np.linspace(float(_checkNumber(sweepStart))*xScaleFactor, 
                        float(_checkNumber(sweepStop))*xScaleFactor, 
                        int(_checkNumber(sweepNum)))
    # Create the plot:
    # Create the plot data for param plots, only one simulation result alowed
    # Other simulation results are simply ignored (plots would become messy).
    if funcType == 'param':
        for j in range(len(yVar)):
            xData, yData = stepParams(result, xVar, yVar[j], sweepVar, x)
            if type(xData) == dict:
                keys = list(xData.keys())
                for i in range(len(keys)):
                    newTrace = trace([xData[keys[i]], yData[keys[i]]])
                    newTrace.label = '$%s: %s$ = %8.1e'%(sp.latex(sp.Symbol(yVar[j])), 
                                                         sp.latex(result.stepVar), 
                                                         result.stepList[i])
                    newTrace.color = ini.default_colors[colNum % numColors]
                    colNum += 1
                    ax.traces.append(newTrace)
            else:
                newTrace = trace([xData, yData])
                newTrace.label = '$' + sp.latex(sp.Symbol(yVar[j])) + '$'
                newTrace.color = ini.default_colors[colNum % numColors]
                colNum += 1
                ax.traces.append(newTrace)
    else:
        same_types = False
        if len(results) > 1:
            gain_types = list(set([result.gainType for result in results]))
            if len(gain_types) == 1:
                same_types = True 
        for result in results:
            if not result.step:
                if result.dataType == 'numer':
                    yData = result.numer
                    yLabel = 'numer: '
                elif result.dataType == 'denom':
                    yData = result.denom
                    yLabel = 'denom: '
                elif result.dataType == 'laplace':
                    yData = result.laplace
                    yLabel = ''
                elif result.dataType == 'time':
                    yData = result.time
                    yLabel = '$' + sp.latex(sp.Symbol(result.detLabel)) + '$'
                elif result.dataType == 'step':
                    yData = result.stepResp
                    yLabel = '$' + sp.latex(sp.Symbol(result.detLabel)) + '$'
                elif result.dataType == 'impulse':
                    yData = result.impulse
                    yLabel = '$' + sp.latex(sp.Symbol(result.detLabel)) + '$'
                if result.dataType != 'noise' and _undefined_params(yData,
                                                                    name):
                    continue
                if funcType == 'mag':
                    if ax.polar:
                        radius = _magFunc_f(yData, x)
                        angle = _phaseFunc_f(yData, x)
                        if ini.hz:
                            angle = angle/180*np.pi
                        newTrace = trace([angle, radius])
                        # the sweep value per point: a polar curve is a
                        # CONTOUR over frequency, and the cursor must say
                        # WHERE on it a point sits (Anton, 2026-08-03 -
                        # 'idx=157' said nothing)
                        newTrace.polarParam = ('f' if ini.hz else 'w',
                                               'Hz' if ini.hz else 'rad/s', x)
                    else:
                        newTrace = trace([x, _magFunc_f(yData, x)])
                elif funcType == 'dBmag':
                    if ax.polar:
                        radius = _dB_magFunc_f(yData, x)
                        angle = _phaseFunc_f(yData, x)
                        if ini.hz:
                            angle = angle/180*np.pi
                        newTrace = trace([angle, radius])
                        # the sweep value per point: a polar curve is a
                        # CONTOUR over frequency, and the cursor must say
                        # WHERE on it a point sits (Anton, 2026-08-03 -
                        # 'idx=157' said nothing)
                        newTrace.polarParam = ('f' if ini.hz else 'w',
                                               'Hz' if ini.hz else 'rad/s', x)
                    else:
                        newTrace = trace([x, _dB_magFunc_f(yData, x)])
                elif funcType == 'phase':
                    if not ax.polar:
                        newTrace = trace([x, _phaseFunc_f(yData, x)])
                elif funcType == 'delay':
                    if not ax.polar:
                        newTrace = trace([x, _delayFunc_f(yData, x)])
                elif funcType == 'time':
                    if not ax.polar:
                        y = _makeNumData(yData, sp.Symbol('t'), x, normalize=False)
                        newTrace = trace([x, y])
                if result.dataType != 'noise':
                    newTrace.label = result.label
                    if newTrace.label == '':
                        if result.gainType == 'vi':
                            newTrace.label = result.detLabel
                        else:
                            newTrace.label = result.gainType
                    ylabel = result.label
                    if ylabel == '':
                        if result.gainType == 'vi':
                            yLabel = '$' + sp.latex(sp.Symbol(result.detLabel)) + '$'
                        else:
                            yLabel = result.gainType
                    if result.label == '':
                        if result.gainType != 'vi' and same_types == False:
                            try:
                                newTrace.color = _gain_colors()[result.gainType]
                            except:
                                newTrace.color = ini.default_colors[colNum % numColors]
                                colNum += 1
                    else:
                        newTrace.color = ini.default_colors[colNum % numColors]
                        colNum += 1
                    try:
                        ax.traces.append(newTrace)
                    except:
                        print("Warning: found invalid trace.")
                else:
                    keys = list(result.onoiseTerms.keys())
                    if noiseSources == None:
                        if funcType == 'onoise':
                            yData = sp.N(result.onoise)
                        elif funcType == 'inoise':
                            yData = sp.N(result.inoise)
                        if _undefined_params(yData, name):
                            continue
                        y = _makeNumData(yData, ini.frequency, x)
                        newTrace = trace([x, y])
                        newTrace.label = funcType
                        ax.traces.append(newTrace)
                    elif noiseSources == 'all':
                        for srcName in keys:
                            if funcType == 'onoise':
                                yData = sp.simplify(sp.N(result.onoiseTerms[srcName]))
                            elif funcType == 'inoise':
                                yData = sp.simplify(sp.N(result.inoiseTerms[srcName]))
                            if _undefined_params(yData, name):
                                continue
                            y = _makeNumData(yData, ini.frequency, x)
                            noiseTrace = trace([x, y])
                            noiseTrace.color = ini.default_colors[colNum % numColors]
                            colNum += 1
                            noiseTrace.label = funcType + ': ' + srcName
                            ax.traces.append(noiseTrace)
                    elif noiseSources in keys:
                        if funcType == 'onoise':
                            yData = sp.simplify(sp.N(result.onoiseTerms[noiseSources]))
                        elif funcType == 'inoise':
                            yData = sp.simplify(sp.N(result.inoiseTerms[noiseSources]))
                        if _undefined_params(yData, name):
                            continue
                        y = _makeNumData(yData, ini.frequency, x)
                        noiseTrace = trace([x, y])
                        noiseTrace.color = ini.default_colors[colNum % numColors]
                        colNum += 1
                        noiseTrace.label = funcType + ': ' + noiseSources
                        ax.traces.append(noiseTrace)
                    elif type(noiseSources) == list:
                        for srcName in noiseSources:
                            if srcName in keys:
                                if funcType == 'onoise':
                                    yData = sp.simplify(sp.N(result.onoiseTerms[srcName]))
                                elif funcType == 'inoise':
                                    yData = sp.simplify(sp.N(result.inoiseTerms[srcName]))
                                if _undefined_params(yData, name):
                                    continue
                                y = _makeNumData(yData, ini.frequency, x)
                                noiseTrace = trace([x, y])
                                noiseTrace.color = ini.default_colors[colNum % numColors]
                                colNum += 1
                                noiseTrace.label = funcType + ': ' + srcName
                                ax.traces.append(noiseTrace)
                    else:
                        print("Error: cannot understand 'sources={0}'.".format(str(noiseSources)))
                        return False
            else:
                if result.stepMethod != 'array':
                    stepNum = len(result.stepList)
                else:
                    stepNum = len(result.stepArray[0])
                for i in range(stepNum):
                    if result.dataType == 'numer':
                        yData = result.numer[i]
                        yLabel = 'numer: '
                    elif result.dataType == 'denom':
                        yData = result.denom[i]
                        yLabel = 'denom: '
                    elif result.dataType == 'laplace':
                        yData = result.laplace[i]
                        yLabel = ''
                    elif result.dataType == 'time':
                        yData = result.time[i]
                    elif result.dataType == 'step':
                        yData = result.stepResp[i]
                    elif result.dataType == 'impulse':
                        yData = result.impulse[i]
                    elif result.dataType == 'noise':
                        if funcType == 'onoise':
                            yData = result.onoise[i]
                        elif funcType == 'inoise':
                            yData = result.inoise[i]
                    if result.gainType == 'vi':
                        if result.dataType == 'noise':
                            yLabel = funcType
                        else:
                            yLabel = result.label
                            if yLabel == '':
                                yLabel += '$' + sp.latex(sp.Symbol(result.detLabel)) + '$'
                    else:
                        yLabel = result.label
                        if yLabel == '':
                            try:
                                yLabel += result.gainType
                            except:
                                print("Warning: missing trace label.")
                    if result.stepMethod == 'array':
                        yLabel += ', run: %s'%(i+1)
                    else:
                        yLabel += ', %s = %8.1e'%(result.stepVar, result.stepList[i])
                    if _undefined_params(yData, name):
                        break        # same params in every step: warn once
                    if funcType == 'mag':
                        if ax.polar:
                            radius = _magFunc_f(yData, x)
                            angle = _phaseFunc_f(yData, x)
                            if ini.hz:
                                angle = angle/180*np.pi
                            newTrace = trace([angle, radius])
                            # the sweep value per point: a polar curve is a
                            # CONTOUR over frequency, and the cursor must say
                            # WHERE on it a point sits (Anton, 2026-08-03 -
                            # 'idx=157' said nothing)
                            newTrace.polarParam = ('f' if ini.hz else 'w',
                                                   'Hz' if ini.hz else 'rad/s', x)
                        else:
                            newTrace = trace([x, _magFunc_f(yData, x)])
                    elif funcType == 'dBmag':
                        if ax.polar:
                            radius = _dB_magFunc_f(yData, x)
                            angle = _phaseFunc_f(yData, x)
                            if ini.hz:
                                angle = angle/180*np.pi
                            newTrace = trace([angle, radius])
                            # the sweep value per point: a polar curve is a
                            # CONTOUR over frequency, and the cursor must say
                            # WHERE on it a point sits (Anton, 2026-08-03 -
                            # 'idx=157' said nothing)
                            newTrace.polarParam = ('f' if ini.hz else 'w',
                                                   'Hz' if ini.hz else 'rad/s', x)
                        else:
                            newTrace = trace([x, _dB_magFunc_f(yData, x)])
                    elif funcType == 'phase':
                        if not ax.polar:
                            newTrace = trace([x, _phaseFunc_f(yData, x)])
                    elif funcType == 'delay':
                        if not ax.polar:
                            newTrace = trace([x, _delayFunc_f(yData, x)])
                    elif funcType == 'time':
                        if not ax.polar:
                            y = _makeNumData(yData, sp.Symbol('t'), x, normalize=False)
                            newTrace = trace([x, y])
                    elif funcType == 'onoise' or funcType == 'inoise':
                        if not ax.polar:
                            y = _makeNumData(yData, ini.frequency, x)
                            newTrace = trace([x, y])
                    newTrace.color = ini.default_colors[colNum % numColors]
                    colNum += 1
                    newTrace.label = yLabel
                    try:
                        ax.traces.append(newTrace)
                    except:
                        pass
    # Extra traces on the SAME axis - e.g. a measured NGspice curve beside
    # the SLiCAP transfers (Anton, 2026-08-03: traces are added at AXIS
    # level, never at figure level - the figure only places axes). Trace
    # data is in base units on both routes, so the axis scale factors set
    # above (sweepScale/yScale) apply to these traces identically at render
    # time; that is what makes mixing the two sources correct.
    for _key, value in _trace_items(traces) if traces is not None else []:
        if isinstance(value, trace):
            ax.traces.append(value)
        elif type(value) is list:
            extra = trace(value)
            extra.label = _key
            ax.traces.append(extra)
    return ax

def plotSweep(fileName, title, results, sweepStart, sweepStop, sweepNum,
              sweepVar = 'auto', sweepScale = '', xVar = 'auto', xScale = '',
              xUnits = '', xLim = [], yLim = [], axisType = 'auto',
              funcType = 'auto', yVar = 'auto', yScale = '', yUnits = '',
              noiseSources = None, show = False, save = True, cursors = True):
    """
    Plots a function by sweeping one variable and optionally stepping another.

    The function to be plotted depends on the arguments 'yVar' and 'funcType':

    - If funcType == 'params', the variable 'yVar' must be the name of a circuit
      parameter, or a list with circuit parameters.
    - If funcType == 'auto', the default function that will be plotted depends
      on the data type of the instruction:

      - data type == 'noise': funcType = 'onoise'
      - data type == 'laplace', 'numer' or 'denom': funcType = 'mag'
      - data type == 'time', 'impulse' or 'step': funcType = 'time'

    The variable plotted along the x-axis defaults to the sweep variable. However,
    for multivariate functions obtained with data type 'params', the x variable
    can be choosen from all circuit parameters.

    - If sweepVar == 'auto', the sweep variable will be determined from the data type:

      - data type == 'noise', 'laplace', 'numer' or 'denom': sweepVar = ini.frequency
        for data types 'laplace', 'numer' or 'denom' the laplace variable will
        be replaced with sympy.i*ini.frequency or with 2*sympy.pi*sympy.i*ini.frequency
        before sweeping, when ini.hz == False, or ini.hz== True, respectively.
      - dataType == 'time', 'impulse' or 'step': sweepVar = sympy.Symbol('t')

    The type of axis can be 'lin', 'log', 'semilogx', 'semilogy' or 'polar'.

    :param fileName: Name of the file for saving it to disk.
    :type fileName: str

    :param title: Title of the figure.
    :type title: str

    :param results: Results of the execution of an instruction, or a list with
                    SLiCAPinstruction.instruction objects.
    :type results: list, SLiCAPinstruction.instruction

    :param sweepStart: Start value of the sweep parameter
    :type sweepStart: float, int, str

    :param sweepStop: Stop value of the sweep parameter
    :type sweepStop: float, int, str

    :param sweepNum: Number of points of the sweep parameter
    :type sweepNum: int

    :param sweepVar: Name of the sweep variable
    :type sweepVar: sympy.Symbol, str

    :param sweepScale: Scale factor of the sweep variable. Both the start and
                       the stop value will be multiplied with a factor that
                       corresponds with this scale factor.
    :type sweepScale: str

    :param xVar: Name of the variable to be plotted along the x axis
    :type xvar: str, sympy.Symbol

    :param xScale: Scale factor of the x axis variable.
    :type xScale: str

    :param xUnits: Units of the x axis variable.
    :type xUnits: str

    :param xLim: Limits for the x-axis scale: [<xmin>, <xmax>]
    :type xLim: list

    :param axisType: Type of axis: 'lin', 'log', 'semilogx', 'semilogy' or 'polar'.
    :type axisType: str

    :param funcType: Type of function can be: 'mag', 'dBmag', 'phase', 'delay',
                     'time', 'onoise', 'inoise' or 'param'.
    :type funcType: str

    :param yVar: if funcType = param, yVar should be the name of a circuit
                 parameter or list with names of circuit parameters. In other
                 cases yVar should be 'auto'.
    :type yVar: str, list

    :param yScale: Scale factor of the y axis variable.
    :type yScale: str

    :param yUnits: Units of the y axis variable.
    :type yUnits: str

    :param yLim: Limits for the y-axis scale: [<ymin>, <ymax>]
    :type yLim: list

    :param noiseSources: Noise sources of which the contribution to the detector-
                         referred noise (funcType = 'onoise') or the source-
                         referred noise (funcType = 'inoise') should be plotted.
                         Can be 'all', a list with names of noise sources or an
                         ID of a noise source.
    :type noiseSources: list, str

    :param show: If 'True' the plot will be shown in the workspace.
    :type show: bool

    :param save: If 'True' the plot will be saved to the img folder in both pdf and svg format. Defaults to True.
    :type save: bool

    :param cursors: If 'True', the shown figure's toolbar offers A/B cursors
                    and a crosshair (inactive until enabled there). Defaults
                    to True.
    :type cursors: bool

    :return: fig
    :rtype: SLiCAPplots.figure
    """
    fig = figure(fileName)
    fig.show = show
    fig.save = save
    fig.cursors = cursors
    ax = sweepAxis(title, results, sweepStart, sweepStop, sweepNum,
                   sweepVar=sweepVar, sweepScale=sweepScale, xVar=xVar,
                   xScale=xScale, xUnits=xUnits, xLim=xLim, yLim=yLim,
                   axisType=axisType, funcType=funcType, yVar=yVar,
                   yScale=yScale, yUnits=yUnits, noiseSources=noiseSources,
                   name=fileName)
    if ax is False:
        return fig
    fig.axes = [[ax]]
    fig.plot()
    return fig

def pzAxis(title, results, xmin = None, xmax = None, ymin = None,
           ymax = None, xscale = '', yscale = ''):
    """
    Creates a pole-zero scatter axis, WITHOUT creating a figure.

    This is :func:`plotPZ` without the figure: same arguments and the same
    automatic behaviour, returning the :class:`axis` object so that it can
    be placed on a figure of any layout with :func:`makeFigure`.

    Note that :func:`plotPZ` also makes its figure square
    (``axisWidth = axisHeight``); that is a figure property, so a pole-zero
    axis placed on a shared figure keeps that figure's aspect ratio.

    For the arguments see :func:`plotPZ`.

    :return: axis object, or False when the result cannot be plotted.
    :rtype: SLiCAPplots.axis, bool
    """
    pz = axis(title)
    # SLiCAP's pole-zero conventions (Anton, 2026-08-03): the box stays
    # SQUARE in a composed figure (axis width = axis height, the root-locus
    # look), and the cursor snaps to POINTS instead of drawing A/B lines.
    pz.square = True
    pz.point_snap = True
    pz.xScale = 'lin'
    pz.yScale = 'lin'
    try:
        xScaleFactor = 10**int(_SCALEFACTORS[xscale])
    except:
        xScaleFactor = 1.
    try:
        yScaleFactor = 10**int(_SCALEFACTORS[yscale])
    except:
        yScaleFactor = 1.
    if ini.hz == True:
        pz.xLabel = 'Re [' + xscale + 'Hz]'
        pz.yLabel = 'Im [' + yscale + 'Hz]'
    else:
        pz.xLabel = 'Re [' + xscale + 'rad/s]'
        pz.yLabel = 'Im [' + yscale + 'rad/s]'
    pzTraces = []
    if xmin != None and xmax != None:
        pz.xLim = [float(_checkNumber(xmin)), float(_checkNumber(xmax))]
    if ymin != None and xmax != None:
        pz.yLim = [float(_checkNumber(ymin)), float(_checkNumber(ymax))]
    if type(results) != list:
        results = [results]
    colNum = 0
    numColors = len(ini.default_colors)
    same_types = False
    if len(results) > 1:
        gain_types = list(set([result.gainType for result in results]))
        if len(gain_types) == 1:
            same_types = True
    for result in results:
        if not result.step:
            if result.dataType == 'poles' or result.dataType == 'pz':
                if ini.hz == True:
                    polesTrace = trace([np.real(result.poles)/2/np.pi/xScaleFactor, 
                                        np.imag(result.poles)/2/np.pi/yScaleFactor])
                else:
                    polesTrace = trace([np.real(result.poles)/xScaleFactor, 
                                        np.imag(result.poles)/yScaleFactor])
                if not same_types:
                    try:
                        polesTrace.markerColor = _gain_colors()[result.gainType]
                    except:
                        polesTrace.markerColor = ini.default_colors[colNum % numColors]
                        colNum += 1
                else:
                    polesTrace.markerColor = ini.default_colors[colNum % numColors]
                    colNum += 1                    
                polesTrace.color = ''
                polesTrace.marker = 'x'
                polesTrace.lineWidth = '0'
                if result.label == '':
                    polesTrace.label = 'poles ' + result.gainType
                else:
                    polesTrace.label = 'poles ' + result.label
                pzTraces.append(polesTrace)
            if result.dataType == 'zeros' or result.dataType == 'pz':
                if ini.hz == True:
                    zerosTrace = trace([np.real(result.zeros)/2/np.pi/xScaleFactor, 
                                        np.imag(result.zeros)/2/np.pi/yScaleFactor])
                else:
                    zerosTrace = trace([np.real(result.zeros)/xScaleFactor, 
                                        np.imag(result.zeros)/yScaleFactor])
                zerosTrace.color = ''
                if not same_types:
                    try:
                        zerosTrace.markerColor = _gain_colors()[result.gainType]
                    except:
                        zerosTrace.markerColor = ini.default_colors[colNum % numColors]
                        colNum += 1
                else:
                    zerosTrace.markerColor = ini.default_colors[colNum % numColors]
                    colNum += 1                    
                zerosTrace.color = ''
                zerosTrace.marker = 'o'
                zerosTrace.lineWidth = '0'
                if result.label == '':
                    zerosTrace.label = 'zeros ' + result.gainType
                else:
                    zerosTrace.label = 'zeros ' + result.label
                pzTraces.append(zerosTrace)
            if result.dataType != 'poles' and result.dataType != 'zeros' and result.dataType != 'pz':
                print("Error: wrong data type '{0}' for 'plotPZ()'.".format(result.dataType))
                return False
        else:
            poles = result.poles
            if len(poles) != 0:
                # start of root locus
                if ini.hz == True:
                    polesTrace = trace([np.real(result.poles[0])/2/np.pi/xScaleFactor, 
                                        np.imag(result.poles[0])/2/np.pi/yScaleFactor])
                else:
                    polesTrace = trace([np.real(result.poles[0])/xScaleFactor, 
                                        np.imag(result.poles[0])/yScaleFactor])
                try:
                    polesTrace.markerColor = _gain_colors()[result.gainType]
                except:
                    polesTrace.markerColor = ini.default_colors[colNum % numColors]
                    colNum += 1
                polesTrace.color = ''
                polesTrace.marker = 'x'
                polesTrace.lineWidth = '0'
                if result.label == '':
                    polesTrace.label = 'poles ' + result.gainType
                else:
                    polesTrace.label = 'poles ' + result.label
                if result.stepMethod == 'array':
                    polesTrace.label += ', run: 1'
                else:
                    polesTrace.label += ', %s = %8.1e'%(result.stepVar, result.stepList[0])
                pzTraces.append(polesTrace)
                # end of root locus
                if ini.hz == True:
                    polesTrace = trace([np.real(result.poles[-1])/2/np.pi/xScaleFactor, 
                                        np.imag(result.poles[-1])/2/np.pi/yScaleFactor])
                else:
                    polesTrace = trace([np.real(result.poles[-1]/xScaleFactor), 
                                        np.imag(result.poles[-1])/yScaleFactor])
                if not same_types:
                    try:
                        polesTrace.markerColor = _gain_colors()[result.gainType]
                    except:
                        polesTrace.markerColor = ini.default_colors[colNum % numColors]
                        colNum += 1
                else:
                    polesTrace.markerColor = ini.default_colors[colNum % numColors]
                    colNum += 1
                polesTrace.color = ''
                polesTrace.marker = '+'
                polesTrace.markerSize = int(np.sqrt(2)*ini.marker_size)
                polesTrace.lineWidth = '0'
                if result.label == '':
                    polesTrace.label = 'poles ' + result.gainType
                else:
                    polesTrace.label = 'poles ' + result.label
                if result.stepMethod == 'array':
                    polesTrace.label += ', run: %s'%(len(poles))
                else:
                    polesTrace.label += ', %s = %8.1e'%(result.stepVar, result.stepList[-1])
                pzTraces.append(polesTrace)
                # root locus
                allPoles = np.array([])
                for i in range(len(poles)):
                    allPoles = np.concatenate((allPoles, poles[i]), axis = None)
                if ini.hz == True:
                    polesTrace = trace([np.real(allPoles)/2/np.pi/xScaleFactor, 
                                        np.imag(allPoles)/2/np.pi/yScaleFactor])
                else:
                    polesTrace = trace([np.real(allPoles)/xScaleFactor, 
                                        np.imag(allPoles)/yScaleFactor])
                if not same_types:
                    try:
                        polesTrace.markerColor = _gain_colors()[result.gainType]
                    except:
                        polesTrace.markerColor = ini.default_colors[colNum % numColors]
                        colNum += 1
                else:
                    polesTrace.markerColor = ini.default_colors[colNum % numColors]
                    colNum += 1    
                polesTrace.color = ''
                polesTrace.marker = '.'
                polesTrace.lineWidth = '0'
                polesTrace.markerSize = ini.line_width
                if result.label == '':
                    polesTrace.label = 'poles ' + result.gainType
                else:
                    polesTrace.label = 'poles ' + result.label
                if result.stepMethod == 'array':
                    polesTrace.label += ', run: 1 ... %s'%(len(poles))
                else:
                    polesTrace.label += ', %s = %8.1e ... %8.1e'%(result.stepVar, 
                                                                  result.stepList[0], 
                                                                  result.stepList[-1])
                pzTraces.append(polesTrace)
            zeros = result.zeros
            if len(zeros) != 0:
                # start of zeros locus
                if ini.hz == True:
                    zerosTrace = trace([np.real(result.zeros[0])/2/np.pi/xScaleFactor, 
                                        np.imag(result.zeros[0])/2/np.pi/yScaleFactor])
                else:
                    zerosTrace = trace([np.real(result.zeros[0])/xScaleFactor, 
                                        np.imag(result.zeros[0])/yScaleFactor])
                if not same_types:
                    try:
                        zerosTrace.markerColor = _gain_colors()[result.gainType]
                    except:
                        zerosTrace.markerColor = ini.default_colors[colNum % numColors]
                        colNum += 1
                else:
                    zerosTrace.markerColor = ini.default_colors[colNum % numColors]
                    colNum += 1
                zerosTrace.color = ''
                zerosTrace.marker = 'o'
                zerosTrace.lineWidth = '0'
                zerosTrace.markerSize = str(ini.marker_size)
                if result.label == '':
                    zerosTrace.label = 'zeros ' + result.gainType
                else:
                    zerosTrace.label = 'zeros ' + result.label
                if result.stepMethod == 'array':
                    zerosTrace.label += ', run: 1'
                else:
                    zerosTrace.label += ', %s = %8.1e'%(result.stepVar, result.stepList[0])
                pzTraces.append(zerosTrace)
                # end of zeros locus
                if ini.hz == True:
                    zerosTrace = trace([np.real(result.zeros[-1])/2/np.pi/xScaleFactor, 
                                        np.imag(result.zeros[-1])/2/np.pi/yScaleFactor])
                else:
                    zerosTrace = trace([np.real(result.zeros[-1])/xScaleFactor, 
                                        np.imag(result.zeros[-1])/yScaleFactor])
                if not same_types:
                    try:
                        zerosTrace.markerColor = _gain_colors()[result.gainType]
                    except:
                        zerosTrace.markerColor = ini.default_colors[colNum % numColors]
                        colNum += 1
                else:
                    zerosTrace.markerColor = ini.default_colors[colNum % numColors]
                    colNum += 1
                    
                zerosTrace.color = ''
                zerosTrace.marker = 's'
                zerosTrace.lineWidth = '0'
                zerosTrace.markerSize = str(ini.marker_size)
                if result.label == '':
                    zerosTrace.label = 'zeros ' + result.gainType
                else:
                    zerosTrace.label = 'zeros ' + result.label
                if result.stepMethod == 'array':
                    zerosTrace.label += ', run: %s'%(len(zeros))
                else:
                    zerosTrace.label += ', %s = %8.1e'%(result.stepVar, result.stepList[-1])
                pzTraces.append(zerosTrace)
                # zeros locus
                allZeros = np.array([])
                for i in range(len(zeros)):
                    allZeros = np.concatenate((allZeros, result.zeros[i]), axis = None)
                if ini.hz == True:
                    zerosTrace = trace([np.real(allZeros)/2/np.pi/xScaleFactor, 
                                        np.imag(allZeros)/2/np.pi/yScaleFactor])
                else:
                    zerosTrace = trace([np.real(allZeros)/xScaleFactor, 
                                        np.imag(allZeros)/yScaleFactor])
                if not same_types:
                    try:
                        zerosTrace.markerColor = _gain_colors()[result.gainType]
                    except:
                        zerosTrace.markerColor = ini.default_colors[colNum % numColors]
                        colNum += 1
                else:
                    zerosTrace.markerColor = ini.default_colors[colNum % numColors]
                    colNum += 1
                zerosTrace.marker = '.'
                zerosTrace.lineWidth = '0'
                zerosTrace.markerSize = str(ini.line_width)
                if result.label == '':
                    zerosTrace.label = 'zeros ' + result.gainType
                else:
                    zerosTrace.label = 'zeros ' + result.label
                if result.stepMethod == 'array':
                    zerosTrace.label += ', run: 1 ... %s'%(len(zeros))
                else:
                    zerosTrace.label += ', %s = %8.1e ... %8.1e'%(result.stepVar, 
                                                                  result.stepList[0], 
                                                                  result.stepList[-1])
                pzTraces.append(zerosTrace)
        colNum += 1
    pz.traces = pzTraces
    return pz

def plotPZ(fileName, title, results, xmin = None, xmax = None, 
           ymin = None, ymax = None, xscale = '', yscale = '', show = False, save = True):
    """
    Creates a pole-zero scatter plot.

    If parameter stepping of the instruction is enabled, a root locus is drawn
    with the parameter as root locus variable.

    In such cases special begin end endpoint markers are used:

    - poles begin of root locus: 'x'
    - poles end of root locus: '+'
    - zeros begin of root locus: 'o'
    - zeros end of root locus: 'square'

    The root locus itself is drawn with dots for each position of a pole or zero.

    Results of multiple analysis can be combined in one plot by putting them in
    a list.

    The type of the axis is 'lin'.

    :param fileName: Name of the file for saving it to disk.
    :type fileName: str

    :param title: Title of the figure.
    :type title: str

    :param results: Results of the execution of an instruction, or a list with
                    SLiCAPinstruction.instruction objects. The data type of these
                    instructions should be 'poles', 'zeros' or 'pz'.
    :type results: list, SLiCAPinstruction.instruction

    :param xmin: Minimum value of the x axis; defaults to None.
    :type xmin: int, float, str

    :param xmax: Maximum value of the x axis; defaults to None.
    :type xmax: int, float, str

    :param ymin: Minimum value of the y axis; defaults to None.
    :type ymin: int, float, str

    :param ymax: Maximum value of the y axis; defaults to None.
    :type ymax: int, float, str

    :param xscale: x axis scale factor; defaults to ''.
    :type xscale: str

    :param yscale: y axis scale factor; defaults to ''.
    :type yscale: str

    :param show: If 'True' the plot will be shown in the workspace. Defaults to False.
    :type show: bool

    :param save: If 'True' the plot will be saved to the img folder in both pdf and svg format. Defaults to True.
    :type show: bool

    :return: fig
    :rtype: SLiCAPplots.figure
    """
    fig = figure(fileName)
    fig.show = show
    fig.save = save
    fig.axisWidth = fig.axisHeight
    pz = pzAxis(title, results, xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax,
                xscale=xscale, yscale=yscale)
    if pz is False:
        return fig
    fig.axes = [[pz]]
    fig.plot()
    return fig

def _trace_items(plotData):
    """(label, value) pairs from whatever *plotData* holds.

    An axis COMBINES trace sets (TRACES.md phase 7: "plotSweep() and plotPZ()
    can combine outputs of different runs. This functionality goes to the
    creation of axes"), so a list of trace dictionaries is accepted beside
    the single dictionary that :func:`plot` has always taken; the GUI emits
    ``[TR1, TR2]``. Order is kept - it is the drawing order.
    """
    if isinstance(plotData, dict):
        return list(plotData.items())
    if isinstance(plotData, trace):
        return [(plotData.label, plotData)]
    if isinstance(plotData, (list, tuple)):
        items = []
        for part in plotData:
            if isinstance(part, dict):
                items += list(part.items())
            elif isinstance(part, trace):
                items.append((part.label, part))
            else:
                raise TypeError("Error: Expected a dictionary with traces or "
                                "a trace object.")
        return items
    raise TypeError("Error: Expected a dictionary with traces, a trace "
                    "object, or a list of either.")


def traceAxis(title, axisType, plotData, xName = '', xScale = '',
              xUnits = '', yName = '', yScale = '', yUnits = '', xLim = [],
              yLim = []):
    """
    Creates an axis holding ready traces, WITHOUT creating a figure.

    This is :func:`plot` without the figure: *plotData* is a dictionary with
    trace objects or [xData, yData] lists, exactly as for :func:`plot`, OR a
    LIST of such dictionaries - an axis combines trace sets, e.g.
    ``[TR1, TR2]``, in drawing order. It returns the :class:`axis` object, so
    it can be placed on a figure of any layout with :func:`makeFigure`.

    For the arguments see :func:`plot`.

    :return: axis object, or False for an unknown axis type.
    :rtype: SLiCAPplots.axis, bool
    """
    colNum = 0
    numColors = len(ini.default_colors)
    ax = axis(title)
    colNum = 0
    numColors = len(ini.default_colors)
    if axisType == 'lin':
        ax.xScale = 'lin'
        ax.yScale = 'lin'
    elif axisType == 'log':
        ax.xScale = 'log'
        ax.yScale = 'log'
    elif axisType == 'semilogx':
        ax.xScale = 'log'
        ax.yScale = 'lin'
    elif axisType == 'semilogy':
        ax.xScale = 'lin'
        ax.yScale = 'log'
    elif axisType == 'polar':
        ax.polar = True
        ax.yScale = 'lin'
    else:
        print("Error: unknown axis type '{0}'.".format(axisType))
        return False
    ax.xScaleFactor = xScale
    ax.yScaleFactor = yScale
    ax.xLim = xLim
    ax.yLim = yLim
    ax.traces = []
    # Create the axis labels
    if xName !="" or xScale != "" or xUnits != "":
        ax.xLabel = xName + ' [' + xScale + xUnits + ']'
    if yName != "" or yScale != "" or yUnits != "":
        ax.yLabel = yName + ' [' + yScale + yUnits + ']'
    for key, value in _trace_items(plotData):
        if type(value) is list:
            newTrace = trace(value)
            newTrace.label = key
            newTrace.color = ini.default_colors[colNum % numColors]
            colNum += 1
        elif isinstance(value, trace):
            newTrace = value
        else:
            raise TypeError("Error: Expected a list with x data and y data, or a trace.")
        if newTrace:
            ax.traces.append(newTrace)
    return ax

def plot(fileName, title, axisType, plotData, xName = '', xScale = '',
         xUnits = '', yName = '', yScale = '', yUnits = '', xLim = [],
         yLim = [], show = False, save = True, cursors = True):
    """
    Plots x-y data, or multiple pairs of x-y data.

    :param fileName: Name of the file for saving it to disk.
    :type fileName: str

    :param title: Title of the figure.
    :type title: str

    :param axisType: Type of axis: 'lin', 'log', 'semilogx', 'semilogy' or 'polar'.
    :type axisType: str

    :param plotData: dictionary with key-value pairs or dictionary with traces

                     - key: *str* label for the trace
                     - value:

                       #. *list* [<xData>, <yData>]

                          - xData: *list*: x values
                          - yData: *list*: y values

                       #. *SLiCAPplots.trace* object

    :type plotData: dict, SLiCAPplots.trace

    :param xName: Name of the variable to be plotted along the x axis. Defaults to ''.
    :type xName: str

    :param xScale: Scale factor of the x axis variable. Defaults to ''.
    :type xScale: str

    :param xUnits: Units of the x axis variable. Defaults to ''.
    :type xUnits: str

    :param xLim: Limits for the x-axis scale: [<xmin>, <xmax>]
    :type xLim: list

    :param yName:  Name of the variable to be plotted along the y axis. Defaults to ''.
    :type funcType: str, sympy.Symbol

    :param yScale: Scale factor of the y axis variable. Defaults to ''.
    :type yScale: str

    :param yUnits: Units of the y axis variable. Defaults to ''.
    :type yUnits: str

    :param yLim: Limits for the y-axis scale: [<ymin>, <ymax>]
    :type yLim: list

    :param show: If 'True' the plot will be shown in the workspace.
    :type show: bool

    :param save: If 'True' the plot will be saved to the img folder in both pdf and svg format. Defaults to True.
    :type save: bool

    :param cursors: If 'True', the shown figure's toolbar offers A/B cursors
                    and a crosshair (inactive until enabled there). Defaults
                    to True.
    :type cursors: bool

    :return: fig
    :rtype: SLiCAPplots.figure
    """
    fig = figure(fileName)
    fig.show = show
    fig.save = save
    fig.cursors = cursors
    ax = traceAxis(title, axisType, plotData, xName=xName, xScale=xScale,
                   xUnits=xUnits, yName=yName, yScale=yScale, yUnits=yUnits,
                   xLim=xLim, yLim=yLim)
    if ax is False:
        return fig
    fig.axes = [[ax]]
    fig.plot()
    return fig

def stepParams(results, xVar, yVar, sVar, sweepList):
    """
    Returns parameter values as a result of sweeping and stepping parameters.

    Called by **SLiCAPplots.plotSweep()** in cases in which funcType = 'param'.

    - If parameter stepping is enabled it returns a tuple with two dictionaries:

        #. {stepVal[j]: [xVal[i] for i in range(len(sweepValues))], ...}
        #. {stepVal[j]: [yVal[i] for i in range(len(sweepValues))], ...}

    - If parameter stepping is disabled it returns a tuple with two lists:

        #. [xVal[i] for i in range(len(sweepValues))]
        #. [yVal[i] for i in range(len(sweepValues))]

    :param results: Results of the execution of an instruction with data type 'params'.
    :type results: SLiCAPinstruction.instruction

    :param xVar: Name of the parameter to be plotted along the x axis
    :type xvar: str

    :param yVar: Name of the parameter to be plotted along the y axis
    :type yvar: str

    :param sVar: Name of the sweep parameter
    :type svar: str

    :param sweepList: Array-like sweep values.
    :type sweepList: list, numpy.array

    :return: parameter values as a result of sweeping and stepping parameters.
    :rtype: tuple
    """
    parNames = list(results.circuit.parDefs.keys()) + results.circuit.params
    errors = 0
    xValues = {}
    yValues = {}
    # check the input
    if xVar == None:
         print("Error: missing x variable.")
         errors +=1
    elif sp.Symbol(xVar) not in parNames:
        print("Error: unknown parameter: '{0}' for 'x variable'.".format(xVar))
        errors += 1
    if sVar == None:
         sVar = xVar
    elif sp.Symbol(xVar) not in parNames:
        print("Error: unknown parameter: '{0}' for sweep variable.".format(xVar))
        errors += 1
    if yVar == None:
         print("Error: missing y variable.")
         errors +=1
    elif sp.Symbol(yVar) not in parNames:
        print("Error: unknown parameter: '{0}' for y variable.".format(yVar))
        errors += 1
    if errors == 0 and results.step:
        if results.stepMethod.lower() == 'lin':
            p = np.linspace(results.stepStart, results.stepStop, num = results.stepNum)
        elif results.stepMethod.lower() == 'log':
            p = np.geomspace(results.stepStart, results.stepStop, num = results.stepNum)
        elif results.stepMethod == 'list':
            p = results.stepList
        else:
            print("Error: dataType 'params' not implemented for stepMethod '", 
                  str(results.stepMethod), "'." )
            errors += 1
    if errors == 0:
        substitutions = {}
        if results.step:
            for parName in list(results.circuit.parDefs.keys()):
                if parName != sp.Symbol(sVar) and parName != results.stepVar:
                    substitutions[parName] = results.circuit.parDefs[parName]
        else:
            for parName in list(results.circuit.parDefs.keys()):
                if parName != sp.Symbol(sVar) :
                    substitutions[parName] = results.circuit.parDefs[parName]
        # Obtain the y-variable as a function of the sweep and the step variable:
        if yVar != sVar:
            f = sp.N(fullSubs(results.circuit.parDefs[sp.Symbol(yVar)], substitutions))
        # Obtain the x-variable as a function of the sweep and the step variable:
        if xVar != sVar:
            g = sp.N(fullSubs(results.circuit.parDefs[sp.Symbol(xVar)], substitutions))
        if results.step:
            for parValue in p:
                if yVar != sVar:
                    y = sp.N(f.subs(results.stepVar, parValue))
                    try:
                        yfunc = sp.lambdify(sp.Symbol(sVar), y, ini.lambdify)
                        yValues[parValue] = yfunc(sweepList)
                    except:
                        yValues[parValue] = [y.subs(sp.Symbol(sVar), 
                                                    sweepList[i]) for i in range(len(sweepList))]
                else:
                    yValues[parValue] = sweepList
                if xVar != sVar:
                    x = g.subs(results.stepVar, parValue)
                    try:
                        xfunc = sp.lambdify(sp.Symbol(sVar), x, ini.lambdify)
                        xValues[parValue] = xfunc(sweepList)
                    except:
                        xValues[parValue] = [x.subs(sp.Symbol(sVar), 
                                                    sweepList[i]) for i in range(len(sweepList))]
                else:
                    xValues[parValue] = sweepList
        else:
            if yVar != sVar:
                try:
                    y = sp.lambdify(sp.Symbol(sVar), f, ini.lambdify)
                    yValues = y(sweepList)
                except:
                    yValues = [f.subs(sp.Symbol(sVar), 
                                      sweepList[i]) for i in range(len(sweepList))]
            else:
                yValues = sweepList
            if xVar != sVar:
                try:
                    x = sp.lambdify(sp.Symbol(sVar), g, ini.lambdify)
                    xValues = x(sweepList)
                except:
                    xValues = [g.subs(sp.Symbol(sVar), 
                                      sweepList[i]) for i in range(len(sweepList))]
            else:
                xValues = sweepList
    return (xValues, yValues)

def makeFigure(axes, fileName, show = False, save = True, cursors = True,
               axisWidth = None, axisHeight = None, shareX = 'none',
               shareY = 'none'):
    """
    Creates a figure from a grid of axis objects and plots it.

    *axes* is a list of lists: one list per row, one entry per column. An
    entry is an :class:`axis` object, or the empty string for an empty cell.
    An axis object placed in several ADJACENT cells spans them; the occupied
    cells must form a solid rectangle. A single axis may also be passed.

    :Example:

    >>> D       = sl.sweepData(LAPLACE1, 1, "1M", 500)
    >>> axMag   = sl.traceAxis("Magnitude", "semilogx",
    ...                        sl.make_traces(D, [{"y": "dB(laplace)"}]),
    ...                        xName="frequency", xUnits="Hz",
    ...                        yName="magnitude", yUnits="dB")
    >>> axPhase = sl.traceAxis("Phase", "semilogx",
    ...                        sl.make_traces(D, [{"y": "phase(laplace)"}]),
    ...                        xName="frequency", xUnits="Hz",
    ...                        yName="phase", yUnits="deg")
    >>> fig     = sl.makeFigure([[axMag], [axPhase]], "bode", show=True)

    >>> # axMag spans both columns of the top row:
    >>> fig = sl.makeFigure([[axMag, axMag], [axPhase, axPZ]], "views")

    :param axes: grid of axis objects (list of lists), or a single axis.
    :type axes: list, SLiCAPplots.axis

    :param fileName: Name of the file for saving it to disk.
    :type fileName: str

    :param show: If True the figure will be shown in the workspace. Defaults
                 to False.
    :type show: bool

    :param save: If True the figure is saved in the img folder. Defaults to
                 True.
    :type save: bool

    :param cursors: If True, the shown figure offers A/B cursors. Defaults
                    to True.
    :type cursors: bool

    :param axisWidth: Width of ONE grid cell in inches; the figure is
                      axisWidth*columns wide. Defaults to None:
                      ini.axis_width.
    :type axisWidth: float, int, NoneType

    :param axisHeight: Height of ONE grid cell in inches; the figure is
                       axisHeight*rows high. Defaults to None:
                       ini.axis_height.
    :type axisHeight: float, int, NoneType

    :param shareX: Axes that share ONE x axis: 'none' (default), 'col'
                   (down each column), 'row' (across each row), 'all', or a
                   LIST of axis-object groups - ``shareX=[[axMag, axPhase]]``
                   - sharing exactly those axes wherever they sit.
                   A positional mode shares only axes plotting the SAME
                   quantity (judged by the axis label), so a column may hold
                   a Bode stack above a pole-zero plot and only the stack
                   shares ('col' once welded a unit-step
                   response to the Re axis below it).
                   Shared axes keep the same range and zoom together. Where a
                   whole column (row) is one share group its gap is closed:
                   tick labels and the x label on the outer axis only, no
                   space in between, only the first title shown - the closed
                   Bode look. Elsewhere the scales are shared but every axis
                   keeps its gap, ticks and title. Polar axes never share.
    :type shareX: str, list

    :param shareY: Axes that share ONE y axis: 'none' (default), 'row',
                   'col', 'all' or a list of groups. As shareX, for the y
                   axis.
    :type shareY: str, list

    :Example:

    >>> BODE = sl.makeFigure([[axMag], [axPhase]], "bode", shareX="col")

    :return: fig
    :rtype: SLiCAPplots.figure
    """
    if isinstance(axes, axis):
        axes = [[axes]]
    elif axes and not isinstance(axes[0], list):
        axes = [list(axes)]
    fig = figure(fileName)
    fig.show = show
    fig.save = save
    fig.cursors = cursors
    # per-figure override of the ini cell size: a 3 x 2 composition usually
    # wants smaller cells than a single plot
    if axisWidth is not None:
        fig.axisWidth = axisWidth
    if axisHeight is not None:
        fig.axisHeight = axisHeight
    fig.shareX = shareX
    fig.shareY = shareY
    fig.axes = [list(row) for row in axes]
    fig.plot()
    return fig

def traces2fig(traceDict, figObject, axis = [0, 0]):
    """
    Adds traces generated from another application to an existing figure.

    :param traceDict: Dictionary with key-value pairs:

             - key: *str*: label of the trace
             - value: *SLiCAPplots.trace* trace object

    :type traceDict: dict

    :param figObject: figure object to which the traces must be added
    :type figObject: SLiCAPplots.figure

    :param axis: List with x position and y position of the axis to which the
                 traces must be added. Defaults to [0, 0]
    :type axis: list

    :return: Updated figure object
    :rtype: SLiCAPplots.figure
    """
    for label in list(traceDict.keys()):
        figObject.axes[axis[0]][axis[1]].traces.append(traceDict[label])
    return figObject

def fig2traces(figObject, names=None):
    """
    Returns the traces of an existing figure, for reuse in another plot.

    Every figure carries a trace dictionary that is updated when the figure
    is plotted (plotSweep(), plot() and plotPZ() all do this, also with
    show=False and save=False). This function makes those traces available
    as input for plot(), so traces from any figure — including traces that
    were generated inside plotSweep() — can be combined in a new figure.

    :param figObject: Figure of which the traces must be returned.
    :type figObject: SLiCAPplots.figure

    :param names: Label, or list of labels, of the traces to be returned.
                  If None (default), all traces of the figure are returned.
    :type names: str, list, NoneType

    :return: Dictionary with key-value pairs:

             - key: *str*: label of the trace
             - value: *SLiCAPplots.trace* trace object

    :rtype: dict
    """
    if names is None:
        return dict(figObject.traceDict)
    if type(names) == str:
        names = [names]
    traceDict = {}
    for name in names:
        if name in figObject.traceDict:
            traceDict[name] = figObject.traceDict[name]
        else:
            print("Warning: no trace '{0}' in figure '{1}'.".format(
                name, figObject.fileName))
    return traceDict

def LTspiceData2Traces(txtFile):
    """
    Generates a dictionary with traces (key = label, value = trace object) from
    LTspice plot data (saved as .txt file).

    :param txtFile: Name of the text file stored in the ini.txt_path directory
    :type txtFile: str

    :return: Dictionary with key-value pairs:

             - key: *str*: label of the trace
             - value: *SLiCAPplots.trace* trace object

    :rtype: dict
    """
    try:
        f = open(ini.txt_path + txtFile, 'r', encoding='utf-8', errors='replace')
        lines = f.readlines()
        f.close()
    except:
        print('Error: could not find LTspice trace data:', ini.txt_path + txtFile)
        return {}
    traceDict = {}
    # Check for parameter stepping
    if len(lines) > 2 and lines[1].split()[0] == 'Step':
        start = 1
    else:
        start = 0
        label = None
    xData = []
    yData = []
    label = None
    traceNum = 0
    for i in range(start, len(lines)):
        lineData = lines[i].split()
        if len(lineData) > 2 and ' '.join(lineData[0:2]) == 'Step Information:':
            if label != None:
                newTrace = trace([xData, yData])
                newTrace.label = label
                traceDict[label] = newTrace
                xData = []
                yData = []
                traceNum += 1
            label = lineData[2]
        elif len(lineData) == 2:
            try:
                xData.append(eval(lineData[0]))
                yData.append(eval(lineData[1]))
            except:
                if label != None:
                    newTrace = trace([xData, yData])
                    newTrace.label = label
                    newTrace.color = ini.default_colors[0]
                    traceDict[label] = newTrace
                label = lineData[1]
    newTrace = trace([xData, yData])
    newTrace.label = label
    traceDict[label] = newTrace
    return traceDict

def LTspiceAC2SLiCAPtraces(fileName, dB=False, color='c'):
    """
    This function converts the results of a single-run LTspice AC analysis
    into two traces (mag, phase) that can be added to SLiCAP plots.
    Stepping is not (yet) supported.

    :param fileName: Name of the file. The file should be located in
                     the ditectory given in *ini.txt_path*.
    :type fileName:  str

    :param dB: True if the trace magnitude should be in dB, else False.
               Default value = False
    :type dB: bool

    :param color: Matplotlib color name. Valid names can be found at:
                  https://matplotlib.org/stable/gallery/color/named_colors.html
                  Default value is cyan (c); this does not correspond with one
                  of the standard gain colors of the asymptotic-gain model.
    :type color:  str

    :return: a list with two trace dicts, magnitude and phase, respectively.
    :rtype: list

    :Example:

    >>> LTmag, LTphase = LTspiceAC2SLiCAPtraces('LTspiceACdata.txt')
    """
    try:
        f = open(ini.txt_path + fileName, 'r', encoding='utf-8', errors='replace')
        lines = f.readlines()
        f.close()
    except:
        print('Cannot find: ', fileName)
        lines = []
    freqs = []
    mag   = []
    phase = []
    for i in range(len(lines)):
        if i != 0:
            line = lines[i].split()
            if ini.hz:
                freqs.append(eval(line[0]))
            else:
                freqs.append(eval(line[0])*2*np.pi)
            dBmag, deg = line[1].split(',')
            dBmag = eval(dBmag[1:-2])
            deg = eval(deg[0:-2])
            if not dB:
                mag.append(10**(dBmag/20))
            else:
                mag.append(dBmag)
            if ini.hz:
                phase.append(deg)
            else:
                phase.append(np.pi*deg/180)
    LTmag = trace([freqs, mag])
    LTmag.label = 'LTmag'
    LTmag.color = color
    LTphase = trace([freqs, phase])
    LTphase.label = 'LTphase'
    LTphase.color = color
    traces = [{'LTmag': LTmag}, {'LTphase': LTphase}]
    return traces

def csv2traces(csvFile):
    """
    Generates a dictionary with traces (key = label, value = trace object) from
    data from a csv file. The CSV file should have the following structure:

    x0_label, y0_label, x1_label, y1_label, ...
    x0_0    , y0_0    , x1_0    , y1_0    , ...
    x0_1    , y0_1    , x1_1    , y1_1    , ...
    ...     , ...     , ...     , ...     , ...

    The traces will be named  with their y label.

    :param csvFile: name of the csv file (in the ini.csv_path directory)
    :type csvFile: str

    :return: dictionary with key-value pairs:

             - key: *str*: label of the trace
             - value: *SLiCAPplots.trace* trace object

    :rtype: dict
    """
    try:
        f = open(ini.csv_path + csvFile)
        lines = f.readlines()
        f.close()
    except:
        print('Error: could not find CSV trace data:', ini.csv_path + csvFile)
        return {}
    traceDict = {}
    labels = []
    for i in range(len(lines)):
        data = lines[i].split(',')
        if len(data) % 2 != 0:
            print("Error: expected an even number of columns in csv file:", 
                  ini.csv_path + csvFile)
            return traceDict
        elif i == 0:
            for j in range(int(len(data)/2)):
                labels.append(data[2*j+1])
                traceDict[data[2*j+1]] = trace([[], []])
                traceDict[data[2*j+1]].xData = []
                traceDict[data[2*j+1]].yData = []
        else:
            for j in range(len(labels)):
                xData = eval(data[2*j])
                yData = eval(data[2*j+1])
                traceDict[labels[j]].xData.append(xData)
                traceDict[labels[j]].yData.append(yData)
    for label in labels:
        traceDict[label].xData = np.array(traceDict[label].xData)
        traceDict[label].yData = np.array(traceDict[label].yData)
        traceDict[label].label = label
    return traceDict

def Cadence2traces(csvFile, absx = False, logx = False, absy = False, logy = False, selection=['all'], assignID=True):
    """
    Generates a dictionary with traces (key = label, value = trace object) from
    data from a csv file generated in Cadence.
    :param csvFile: name of the csv file (in the ini.csv_path directory)
    :type csvFile: str
    :param absx: if 'True', it applies the absolute (abs) function to the indpendent variable data (xData)
    :type absx: bool
    :param logx: if 'True', it applies the logarithm in base 10 (log10) function to the independent variable data (xData)
    :type logx: bool
    :param absy: if 'True', it applies the absolute (abs) function to the dependent variable data (yData)
    :type absy: bool
    :param logy: if 'True', it applies the logarithm in base 10 (log10) function to the dependent variable data (yData)
    :type logy: bool
    :param selection: if:

                      - selection=['all']: Selects all traces in the dictionary and does not replace any label
                      - selection=['all',("Var1","Variable"),("Var2","Variable2")]: selects all traces and replaces all character strings mentioned in the first element of the tuples (e.g. "Var1" and "Var2") with the strings in the second element of the tuples ("Variable" and "Variable2").
                      - selection=[('Var1 (SweepVar=1e-06) Y',"New Label"),('Var2 (SweepVar=1e-06) Y',"")]: selects only the traces that are explicitly mentioned in the first element of the tuple (e.g. 'Var1 (SweepVar=1e-06) Y' and 'Var2 (SweepVar=1e-06) Y') and replaces its label with the second element of the tuple unless it is "".

    :type selection: list of tuples
    :param assignID: if 'True', it generates an ID for each processed trace to avoid overwriting when merging dictionaries.
    :type assignID: bool
    :return: dictionary with key-value pairs:
             - key: *str*: label of the trace
             - value: *SLiCAPplots.trace* trace object

    :rtype: dict
    """
    try:
        f = open(ini.csv_path + csvFile)
        lines = f.readlines()
        f.close()
    except:
        print('Error: could not find CSV trace data:', ini.csv_path + csvFile)
        return {}
    traceDict = {}
    labels = []
    if assignID:
        ID_dict=" (ID:"+str(randint(0,100)) + ")"
    else:
        ID_dict=""
    last_raw_x=lines[-1].split(',')[1::2]
    for element in last_raw_x:
        try:
            limiter=eval(element)
            break
        except:
            pass
    for i in range(len(lines)):
        if i==0 and lines[0][0]=='"':
            data = lines[i][1:-1].split('","')
        else:
            data = lines[i].split(',')
        if len(data) % 2 != 0:
            print("Error: expected an even number of columns in csv file:", ini.csv_path + csvFile)
            return traceDict
        elif i == 0:
            for j in range(int(len(data)/2)):
                labels.append(data[2*j+1])
                traceDict[data[2*j+1]] = trace([[], []])
                traceDict[data[2*j+1]].xData = []
                traceDict[data[2*j+1]].yData = []
        else:
            for j in range(len(labels)):
                try:
                    xData = eval(data[2*j])
                except:
                    xData = limiter
                if absx:
                    xData = abs(xData)
                if logx:
                    try:
                        xData = np.log10(xData)
                    except:
                        print("Could not calculate the log10 of the xData of:", ini.csv_path + csvFile)
                try:
                    yData = eval(data[2*j+1])
                except:
                    yData = 0
                if absy:
                    yData = abs(yData)
                if logy:
                    try:
                        yData = np.log10(yData)
                    except:
                        print("Could not calculate the log10 of the yData of:", ini.csv_path + csvFile)
                traceDict[labels[j]].xData.append(xData)
                traceDict[labels[j]].yData.append(yData)
    for label in labels:
            traceDict[label].xData = np.array(traceDict[label].xData)
            traceDict[label].yData = np.array(traceDict[label].yData)
            traceDict[label].label = label
    keys=list(traceDict.keys())
    traceDict[keys[-1]].label=traceDict[keys[-1]].label.replace("\n","")
    traceDict_ready={}
    if selection[0]=='all':
        selection=selection[1:]
        unzipped_replacements = list(map(list, zip(*selection)))
        for key in keys:
            idx_rpl=0
            try:
                for replacement in unzipped_replacements[0]:
                    traceDict[key+str(ID_dict)].label=traceDict[key+str(ID_dict)].label.replace(replacement,unzipped_replacements[1][idx_rpl])
                    idx_rpl+=1
            except:
                pass
            traceDict_ready[key+str(ID_dict)]=traceDict[key]
        return traceDict_ready
    else:
        try:
            unzipped_replacements = list(map(list, zip(*selection)))
        except:
            print('Error: invalid input for "selection" parameter')
        for key in keys:
            if (key in unzipped_replacements[0]) or (key.rstrip("\n") in unzipped_replacements[0]):
                try:
                    idx_rpl=unzipped_replacements[0].index(key)
                except:
                    idx_rpl=unzipped_replacements[0].index(key.rstrip("\n"))
                if unzipped_replacements[1][idx_rpl] != '':
                    traceDict[key].label=traceDict[key].label.replace(unzipped_replacements[0][idx_rpl],unzipped_replacements[1][idx_rpl])
                traceDict_ready[key+str(ID_dict)]=traceDict[key]
    return traceDict_ready

def addTraces(figObj, traceDict):
    """
    Adds the traces in the dictionary 'traceDict' to the figure object 'figObj'.

    :param figObj: SLiCAP figure object to which the traces will be added.
    :type csvFile: SLiCAP figure object

    :param traceDict: dictionary with traces (result from csv2traces)
    :type traceDict: dict

    :return: updated figure object (traces addad)
    :rtype: SLiCAP figure object
    """
    for key in traceDict.keys():
        figObj.axes[0][0].traces.append(traceDict[key])
    return figObj

if __name__=='__main__':
    ini.img_path = ''
    x = np.linspace(0, 2*np.pi, endpoint = True)
    y1 = np.sin(x)
    y2 = np.cos(x)
    sine = trace([x, y1])
    sine.label = 'sine'
    sine.color = ''
    sine.lineWidth = '0'
    sine.marker = '.'
    sine.markerFaceColor = 'r'
    sine.markerColor = 'r'
    cosine = trace([x, y2])
    cosine.label = 'cosine'
    cosine.color = ''
    cosine.marker = 'x'
    cosine.markerColor = 'b'
    sincos = axis('sine and cosine')
    sincos.text = [3.14, 0.1, '$blah_9^{14}$']
    sincos.polar = False
    sincos.xScale = 'lin'
    sincos.yScale = 'lin'
    sincos.traces = [sine, cosine]
    testFig = figure('testFig')
    testFig.axes = [[sincos, ""],["",sincos]]
    testFig.show = True
    testFig.plot()
    plt.show()
    testFig.plot()
    plt.show()
