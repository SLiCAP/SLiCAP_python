#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SLiCAP module with plot functions.
"""
import numpy as np
import sympy as sp
import matplotlib._pylab_helpers as plotHelp
import matplotlib.pyplot as plt
import SLiCAP.SLiCAPconfigure as ini
from random import randint
from SLiCAP.SLiCAPlex import _SCALEFACTORS
from SLiCAP.SLiCAPmath import _makeNumData, _dB_magFunc_f, _magFunc_f, _phaseFunc_f
from SLiCAP.SLiCAPmath import _delayFunc_f, _checkNumber, fullSubs

plt.ioff() # Turn off the interactive mode for plotting

class trace(object):
    """
    Trace prototype.

    Traces are plotted on axes, which are part of a figure.

    :param traceData: list with list array-like X and Y data of the trace.
    :type traceData: list

    :Example:

    >>> x_data = np.linspace(0, 2*np.pi, 50)
    >>> y_data = np.sin(x_data)
    >>> sin_trace = trace([x_data, y_data])
    """
    def __init__(self, traceData):
        self.xData = np.array(traceData[0])
        """
        Array-like data for the x-axis of the trace. On a polar axes this is
        the angle in radians.
        """

        self.yData = np.array(traceData[1])
        """
        Array-like data for the y-axis of the trace. On a polar axes this is
        the radius.
        """

        try:
            if len(self.xData) != len(self.yData):
                print('Error in plot data.')
        except:
            pass

        self.xName = 'x'
        """
        Heading (*str*) for the x column of a table. Defaults to 'x'.
        """

        self.yName = 'y'
        """
        Heading (*str*) for the y column of a table. Defaults to 'y'.
        """

        self.label = ''
        """
        Trace label (*str*) that will be displayed in legend box. Defaults to ''.
        """

        self.color = False
        """
        Trace color (*str*) in matplotlib format. Defaults to False.
        """

        self.marker = False
        """
        Marker type (*str*) in matplotlib format. Defaults to False.
        """

        self.markerColor = False
        """
        Marker color (*str*) in matplotlib format. Defaults to False.
        """

        self.markerFaceColor = 'none'
        """
        Marker face color (*str*) in matplotlib format. Defaults to 'none'.
        """

        self.markerSize = ini.marker_size
        """
        Marker size (*int*). Defaults to 7.
        """

        self.lineWidth = ini.line_width
        """
        Line width (*int*) in pixels. Defaults to 2.
        """

        self.lineType = ini.line_type
        """
        Line type (*str*) in matplotlib format. Defaults to '-'.
        """

    def makeTable(self):
        """
        Returns a table with trace data in CSV format.

        :return: table: CSV table with column headings and x-data and y-data in
                 columns
        :rtype: str

        :Example:

        >>> x_data = np.linspace(0, 2*np.pi, 10)
        >>> y_data = np.sin(x_data)
        >>> sin_trace = trace([x_data, y_data])
        >>> sin_trace.yName = 'sin(x)'
        >>> print(sin_trace.makeTable())
        x,sin(x)
          0.000000000000e+00,   0.000000000000e+00
          6.981317007977e-01,   6.427876096865e-01
          1.396263401595e+00,   9.848077530122e-01
          2.094395102393e+00,   8.660254037844e-01
          2.792526803191e+00,   3.420201433257e-01
          3.490658503989e+00,  -3.420201433257e-01
          4.188790204786e+00,  -8.660254037844e-01
          4.886921905584e+00,  -9.848077530122e-01
          5.585053606382e+00,  -6.427876096865e-01
          6.283185307180e+00,  -2.449293598295e-16
        """
        table = str(self.xName) + ',' + str(self.yName) + '\n'
        for i in range(len(self.xData)):
            table += '%20.12e,%20.12e'%(self.xData[i], self.yData[i]) + '\n'
        return table

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

        self.show = False
        """
        (*bool*) if 'True' the figure will be displayed with the method
        **SLiCAPplots.figure.plot()**. Defaults to [].
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
    def updateTracedict(self):
        """
        Updates the trace dictionary of the figure.
        """
        self.traceDict = {}
        for ax in self.axes:
            for axrow in ax:
                for trc in axrow.traces:
                    self.traceDict[trc.label] = trc
                
    def plot(self):
        """
        Creates the figure, and saves it to disck. It displays the figure if 
        SLiCAPplots.figure.show == True.
        """
        axes = np.array(self.axes)
        try:
            rows, cols = axes.shape
        except:
            print('Attribute of <figure>.axes must be a list of lists or a two-dimensional array.')
            return False
        axesList = []
        # Make a single list of plots to be plotted left -> right, then top -> bottom
        for i in range(rows):
            for j in range(cols):
                axesList.append(axes[i][j])
        if len(axesList) == 0:
            print('Error: no plot data available; plotting skipped.')
            return False
        # Define the matplotlib figure object
        fig = plt.figure(figsize = (self.axisWidth*cols, rows*self.axisHeight))
        # Create the axes with their plots
        for i in range(len(axesList)):
            if axesList[i] != "":
                ax = fig.add_subplot(rows, cols, i + 1, polar = axesList[i].polar)
                if axesList[i].xLabel:
                    try:
                        ax.set_xlabel(axesList[i].xLabel)
                    except:
                        pass
                if axesList[i].yLabel:
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
                    #try:
                    if axesList[i].xScaleFactor in list(_SCALEFACTORS.keys()):
                        scaleX = 10**eval(_SCALEFACTORS[axesList[i].xScaleFactor])
                    else:
                        scaleX = 1
                    if axesList[i].yScaleFactor in list(_SCALEFACTORS.keys()):
                        scaleY = 10**eval(_SCALEFACTORS[axesList[i].yScaleFactor])
                    else:
                        scaleY = 1
                    plt.plot(axesList[i].traces[j].xData/scaleX, 
                             axesList[i].traces[j].yData/scaleY, 
                             label = axesList[i].traces[j].label, 
                             linewidth = axesList[i].traces[j].lineWidth,
                             color = Color, marker = Marker, 
                             markeredgecolor = MarkerColor, 
                             markersize = axesList[i].traces[j].markerSize, 
                             markeredgewidth = 2, 
                             markerfacecolor = axesList[i].traces[j].markerFaceColor, 
                             linestyle = axesList[i].traces[j].lineType)
                    #except:
                    #    print("Error in plot data of '{0}'.".format(self.fileName))
                    if axesList[i].text:
                        X, Y, txt = axesList[i].text
                        plt.text(X, Y, txt, fontsize = ini.plot_fontsize)
                    # Set default font sizes and grid
                    defaultsPlot()
        # Save the figure"
        plt.savefig(ini.img_path + self.fileName + "." + self.fileType)
        if self.fileType.lower() != "pdf":
            plt.savefig(ini.img_path + self.fileName + ".pdf")
        if self.show:
            plt.show()
        self.updateTracedict()
        plt.close(fig)
        return

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

def plotSweep(fileName, title, results, sweepStart, sweepStop, sweepNum, 
              sweepVar = 'auto', sweepScale = '', xVar = 'auto', xScale = '', 
              xUnits = '', xLim = [], yLim = [], axisType = 'auto', 
              funcType = 'auto', yVar = 'auto', yScale = '', yUnits = '',
              noiseSources = None, show = False):
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
        before sweeping, when ini.frequency == False, or ini.frequency== True, respectively.
      - dataType == 'time', 'impulse' or 'step': sweepVar = sympy.Symbol('t')

    The type of axis can be 'lin', 'log', 'semilogx', 'semilogy' or 'polar'.

    :param fileName: Name of the file for saving it to disk.
    :type fileName: str

    :param title: Title of the figure.
    :type title: str

    :param results: Results of the execution of an instruction, or a list with
                    SLiCAPprotos.allResults objects.
    :type results: list, SLiCAPprotos.allResults

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

    :return: fig
    :rtype: SLiCAPplots.figure
    """
    plotDataTypes = ['laplace', 'numer', 'denom', 'noise', 'step', 'impulse', 'time', 'params', None]
    funcTypes  = ['mag', 'dBmag', 'phase', 'delay', 'time', 'onoise', 'inoise', 'param']
    axisTypes  = ['lin', 'log', 'semilogx', 'semilogy', 'polar']
    freqTypes  = ['laplace', 'numer', 'denom', 'noise']
    timeTypes  = ['time', 'impulse', 'step']
    fig = figure(fileName)
    fig.show = show
    ax = axis(title)
    ax.polar = False
    if type(results) != list:
        results = [results]
    colNum = 0
    numColors = len(ini.default_colors)
    # first results defines the axis type and labels
    result = results[0]
    if result.dataType not in plotDataTypes:
        print("Error: cannot plot dataType '{0}' with 'plotSweep()'.".format(result.dataType))
        return fig
    if funcType == 'auto':
        if result.dataType == 'noise':
            funcType = 'onoise'
        elif result.dataType in freqTypes:
            funcType = 'mag'
        elif result.dataType in timeTypes:
            funcType = 'time'
    elif funcType == 'param':
        if sweepVar == 'auto':
            print("Error: undefined sweep variable.")
            return fig
        if yVar == 'auto':
            print("Error: missing parameter to be plotted.")
            return fig
        if xVar == 'auto':
            xVar = sweepVar
            xScale = sweepScale
    elif funcType not in funcTypes:
        print("Error: unknown funcType: '{0}'.".format(funcType))
        return fig
    if axisType == 'auto':
        if funcType == 'param':
            axisType = 'lin'
        elif funcType == 'mag' or result.dataType == 'noise':
            axisType = 'log'
        elif funcType == 'dBmag' or funcType == 'phase' or funcType == 'delay':
            axisType = 'semilogx'
        elif funcType == 'time':
            axisType = 'lin'
    elif axisType not in axisTypes:
        print("Error: unknown axisType: '{0}'.".format(axisType))
        return fig
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
                if funcType == 'mag':
                    if ax.polar:
                        radius = _magFunc_f(yData, x)
                        angle = _phaseFunc_f(yData, x)
                        if ini.hz:
                            angle = angle/180*np.pi
                        newTrace = trace([angle, radius])
                    else:
                        newTrace = trace([x, _magFunc_f(yData, x)])
                elif funcType == 'dBmag':
                    if ax.polar:
                        radius = _dB_magFunc_f(yData, x)
                        angle = _phaseFunc_f(yData, x)
                        if ini.hz:
                            angle = angle/180*np.pi
                        newTrace = trace([angle, radius])
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
                                y = _makeNumData(yData, ini.frequency, x)
                                noiseTrace = trace([x, y])
                                noiseTrace.color = ini.default_colors[colNum % numColors]
                                colNum += 1
                                noiseTrace.label = funcType + ': ' + srcName
                                ax.traces.append(noiseTrace)
                    else:
                        print("Error: cannot understand 'sources={0}'.".format(str(noiseSources)))
                        return fig
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
                    if funcType == 'mag':
                        if ax.polar:
                            radius = _magFunc_f(yData, x)
                            angle = _phaseFunc_f(yData, x)
                            if ini.hz:
                                angle = angle/180*np.pi
                            newTrace = trace([angle, radius])
                        else:
                            newTrace = trace([x, _magFunc_f(yData, x)])
                    elif funcType == 'dBmag':
                        if ax.polar:
                            radius = _dB_magFunc_f(yData, x)
                            angle = _phaseFunc_f(yData, x)
                            if ini.hz:
                                angle = angle/180*np.pi
                            newTrace = trace([angle, radius])
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
    fig.axes = [[ax]]
    fig.plot()
    return fig

def plotPZ(fileName, title, results, xmin = None, xmax = None, 
           ymin = None, ymax = None, xscale = '', yscale = '', show = False):
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
                    SLiCAPprotos.allResults objects. The data type of these
                    instructions should be 'poles', 'zeros' or 'pz'.
    :type results: list, SLiCAPprotos.allResults

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

    :return: fig
    :rtype: SLiCAPplots.figure
    """
    fig = figure(fileName)
    fig.show = show
    fig.axisWidth = fig.axisHeight
    pz = axis(title)
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
                return fig
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
    fig.axes = [[pz]]
    fig.plot()
    return fig

def plot(fileName, title, axisType, plotData, xName = '', xScale = '', 
         xUnits = '', yName = '', yScale = '', yUnits = '', xLim = [] , 
         yLim = [], show = False):
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

    :return: fig
    :rtype: SLiCAPplots.figure
    """
    fig = figure(fileName)
    fig.show = show
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
        return fig
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
    for key in plotData.keys():
        if type(plotData[key]) is list:
            newTrace = trace(plotData[key])
            newTrace.label = key
            newTrace.color = ini.default_colors[colNum % numColors]
            colNum += 1
        else:
            type_str = str(type(plotData[key]))
            if type_str == "<class 'SLiCAP.SLiCAPplots.trace'>":
                newTrace = plotData[key]
            else:
                raise TypeError("Error: Expected a list with x data and y data, or a trace.")
                newTrace = False
        if newTrace:
            ax.traces.append(newTrace)
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
    :type results: SLiCAPprotos.allResults

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
        figObject.axes[axis[0]][axis[0]].traces.append(traceDict[label])
    return figObject

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

def _gain_colors():
    # Compact notation for plotting
    gain_colors               = {}
    gain_colors["ideal"]      = ini.gain_colors_ideal
    gain_colors["gain"]       = ini.gain_colors_gain
    gain_colors["asymptotic"] = ini.gain_colors_asymptotic
    gain_colors["loopgain"]   = ini.gain_colors_loopgain
    gain_colors["direct"]     = ini.gain_colors_direct
    gain_colors["servo"]      = ini.gain_colors_servo
    gain_colors["vi"]         = ini.gain_colors_vi
    return gain_colors

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
