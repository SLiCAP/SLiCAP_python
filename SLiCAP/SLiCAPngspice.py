#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SLiCAP module for interfacing with NGspice.

"""
from __future__ import annotations
import SLiCAP.SLiCAPconfigure as ini
from SLiCAP.SLiCAPmath import _checkExpression, groupDelay
from SLiCAP.SLiCAPlex import (_scale_float, _replaceScaleFactors,
                              _SCALEFACTORS, _sympify)
from os     import system, remove
import subprocess
from sympy  import Symbol
from SLiCAP.SLiCAPtraces import (trace, dataset, make_traces,
                                 register_dataset_adapter,
                                 register_units_hint,
                                 _rename_signals)
from numpy  import array, sqrt, arctan, pi, unwrap, log10, linspace, geomspace
import numpy as np
import re
from shutil import copy2
from dataclasses import dataclass, field
from pathlib import Path

# =============================================================================
# Nutmeg raw-file parser
# =============================================================================

_BINARY_MARKER = b"Binary:"
_VALUES_MARKER  = b"Values:"


def _find_raw_marker(raw, marker, start):
    """Find *marker* on its own line at/after *start*, tolerant of LF and CRLF
    line endings (NGspice on Windows writes the raw header with CRLF, so a
    ``b"Binary:\\n"`` search would miss ``Binary:\\r\\n`` — the Windows-only
    "Missing trace data" bug).  Returns (marker_start, data_start), or (-1, -1)
    when absent; *data_start* is the first byte past the marker's line ending."""
    pos = start
    while True:
        i = raw.find(marker, pos)
        if i == -1:
            return -1, -1
        end = i + len(marker)
        if end < len(raw) and raw[end:end + 1] in (b"\r", b"\n"):
            if raw[end:end + 1] == b"\r":
                end += 1
            if raw[end:end + 1] == b"\n":
                end += 1
            return i, end
        pos = i + len(marker)


@dataclass
class Analysis:
    """One analysis block from an NGspice Nutmeg raw file.

    :param name:      Plot name as written by NGspice (e.g. ``"Transient Analysis"``).
    :param x_name:    Name of the independent variable (``"time"``, ``"frequency"``).
    :param x_data:    Independent variable array, shape (M,), always real.
    :param signals:   ``{signal_name: array}``; complex for AC / noise blocks.
    :param var_names: All variable names in file order (x first, then signals).
    """
    name:      str
    x_name:    str
    x_data:    np.ndarray
    signals:   dict
    var_names: list = field(default_factory=list)

    def is_complex(self) -> bool:
        """True when signal arrays are complex (AC / noise spectral density)."""
        return any(np.iscomplexobj(v) for v in self.signals.values())


class RawFile:
    """Static-method parser for NGspice Nutmeg raw files.

    Usage::

        analyses = RawFile.load("output.raw")   # list[Analysis]

    Supports binary and ASCII blocks; multiple analysis blocks per file.
    No Qt dependency — safe for CLI and notebook use.
    """

    @staticmethod
    def load(path) -> list:
        """Parse *path* and return all analysis blocks in file order.

        :param path: Path to the NGspice ``.raw`` file.
        :type path: str, pathlib.Path
        :return: List of :class:`Analysis` objects, one per analysis block.
        :rtype: list
        """
        raw = Path(path).read_bytes()
        analyses = []
        pos = 0
        while pos < len(raw):
            result = RawFile._parse_block(raw, pos)
            if result is None:
                break
            analysis, pos = result
            if analysis is not None:
                analyses.append(analysis)
        return analyses

    @staticmethod
    def _parse_block(raw, start):
        bi, bi_end = _find_raw_marker(raw, _BINARY_MARKER, start)
        vi, vi_end = _find_raw_marker(raw, _VALUES_MARKER, start)

        if bi == -1 and vi == -1:
            return None

        is_binary  = (bi != -1) and (vi == -1 or bi <= vi)
        marker_pos = bi if is_binary else vi
        marker_end = bi_end if is_binary else vi_end

        header_text = raw[start:marker_pos].decode("ascii", errors="replace")
        hdr = RawFile._parse_header(header_text)
        if not hdr:
            return None, marker_end

        plotname = hdr.get("plotname", "Unknown")
        flags    = hdr.get("flags", "real").lower()
        n_vars   = int(hdr.get("no. of variables", 0))
        n_pts    = int(hdr.get("no. of points", 0))
        var_info = hdr.get("variables", [])

        if n_vars == 0 or n_pts == 0:
            return None, marker_end

        is_complex = "complex" in flags

        if is_binary:
            return RawFile._read_binary(raw, marker_end, n_pts, n_vars,
                                        is_complex, plotname, var_info)
        return RawFile._read_ascii(raw, marker_end, n_pts, n_vars,
                                   is_complex, plotname, var_info)

    @staticmethod
    def _parse_header(text):
        hdr      = {}
        in_vars  = False
        var_list = []

        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue

            if in_vars:
                parts = stripped.split()
                if len(parts) >= 3:
                    var_list.append((parts[1], parts[2]))
                elif len(parts) == 2:
                    var_list.append((parts[1], ""))
                else:
                    in_vars = False
                continue

            if stripped.lower() == "variables:":
                in_vars = True
                continue

            if ":" in stripped:
                key, _, val = stripped.partition(":")
                key = key.strip().lower()
                val = val.strip()
                if key in ("no. of variables", "no. variables"):
                    try:
                        hdr["no. of variables"] = int(val)
                    except ValueError:
                        hdr["no. of variables"] = 0
                elif key in ("no. of points", "no. points"):
                    try:
                        hdr["no. of points"] = int(val)
                    except ValueError:
                        hdr["no. of points"] = 0
                else:
                    hdr[key] = val

        if var_list:
            hdr["variables"] = var_list
        return hdr

    @staticmethod
    def _read_binary(raw, data_start, n_pts, n_vars, is_complex, plotname, var_info):
        elem_bytes = 16 if is_complex else 8
        data_size  = n_pts * n_vars * elem_bytes
        chunk      = raw[data_start : data_start + data_size]

        if len(chunk) < data_size:
            return None, len(raw)

        dtype  = np.complex128 if is_complex else np.float64
        matrix = np.frombuffer(chunk, dtype=dtype).reshape(n_pts, n_vars)

        return RawFile._build_analysis(plotname, var_info, matrix, n_vars), \
               data_start + data_size

    @staticmethod
    def _read_ascii(raw, data_start, n_pts, n_vars, is_complex, plotname, var_info):
        next_block = raw.find(b"Title:", data_start)
        end   = next_block if next_block != -1 else len(raw)
        block = raw[data_start:end].decode("ascii", errors="replace")

        dtype  = np.complex128 if is_complex else np.float64
        matrix = np.zeros((n_pts, n_vars), dtype=dtype)
        pt     = -1
        col    = 0

        for line in block.splitlines():
            parts = line.split()
            if not parts:
                continue
            try:
                int(parts[0])
                pt  += 1
                col  = 0
                if pt >= n_pts:
                    break
                val_str = parts[1] if len(parts) > 1 else ""
            except ValueError:
                val_str = parts[0] if parts else ""

            if not val_str:
                continue
            try:
                if is_complex:
                    # NGspice ASCII complex is "real,imag" (comma-separated), NOT
                    # Python's "real+imagj" — complex(val_str) raises here and the
                    # value would be silently dropped as 0.  This is the Windows
                    # bug: that build writes ASCII raws (Linux writes binary), so
                    # a stepped AC there parsed as all-zeros.
                    re_s, _, im_s = val_str.partition(",")
                    val = complex(float(re_s), float(im_s) if im_s else 0.0)
                else:
                    val = float(val_str)
            except ValueError:
                continue
            if pt >= 0 and col < n_vars:
                matrix[pt, col] = val
            col += 1

        return RawFile._build_analysis(plotname, var_info, matrix, n_vars), end

    @staticmethod
    def _build_analysis(plotname, var_info, matrix, n_vars):
        all_names = [info[0] for info in var_info] if var_info \
                    else [f"var{i}" for i in range(n_vars)]

        # OP plots have no sweep axis — all variables are signals.
        if "operating point" in plotname.lower():
            signals = {}
            for j in range(n_vars):
                name = all_names[j] if j < len(all_names) else f"var{j}"
                signals[name] = matrix[:, j].copy()
            return Analysis(name=plotname, x_name="", x_data=np.array([]),
                            signals=signals, var_names=all_names)

        x_name = all_names[0] if all_names else ""
        x_data = matrix[:, 0].real.copy() if matrix.shape[1] > 0 else np.array([])

        signals = {}
        for j in range(1, n_vars):
            name = all_names[j] if j < len(all_names) else f"var{j}"
            signals[name] = matrix[:, j].copy()

        return Analysis(name=plotname, x_name=x_name, x_data=x_data,
                        signals=signals, var_names=all_names)


# =============================================================================

class MOS(object):
    """
    MOS Transistor.

    :param refDes: Reference designator used in SLiCAP circuit file
    :type refDes: str

    :param lib: path to library file, absolute or relative to python script.
    :type lib: str

    :param dev: Device name (as in library)
    :type dev: str


    MOS attributes:

    - *self*.refDes = refDes
    - *self*.lib = lib
    - *self*.dev = dev
    - *self*.modelDef = Text string with SLiCAP model definition for this device
    - *self*.parDefs = Dictionary with SLiCAP parameter definitions for this device
    - *self*.params = Dictionary with names and values of parameters provided by ngspice
    - *self*.errors = Relative difference between forward and reverse parameter measurement
    - *self*.step   = Step data for VG or ID, defaults to False

    """
    def __init__(self,refDes, lib, dev, W, L, M):
        self.refDes   = refDes
        self.lib      = lib
        self.dev      = dev
        self.W        = W
        self.L        = L
        self.M        = M
        self.modelDef = None
        self.parDefs  = None
        self.params   = {}
        self.errors   = {}
        self.step     = False

    def getOPid(self, ID, VD, VS, VB, f, step=None):
        """
        Returns operating point information of the device with the drain
        current as (swept) independent variable.

        :param W: Width of the device in [m]
        :type W: float

        :param L: Length of the device in [m]
        :type L: float

        :param M: Number of devices in parallel
        :type M: int

        :param ID: Drain current [A]
        :type ID: float

        :param VD: Drain voltage with respect to ground in [V]
        :type VD: float

        :param VS: Source voltage with respect to ground in [V]
        :type VS: float

        :param VB: Bulk voltage with respect to ground in [V]
        :type VB: float

        :param step: Step data for ID; list with start value, number of values
                     and stop value. Defaults to None
        """
        if not isinstance(step, list) or len(step) != 3:
            stepStart = '{ID}'
            stepNum   = '1'
            stepStep  = '0'
        else:
            stepStart = str(float(step[0]))
            stepNum   = str(int(step[1]))
            stepStep  = str(float(step[2]))
            self.step = True
        txt =  'MOS_OP_I\n'
        txt += '.param ID     = %s\n'%(ID)
        txt += '.param VD     = %s\n'%(VD)
        txt += '.param VS     = %s\n'%(VS)
        txt += '.param VB     = %s\n'%(VB)
        txt += '.param L      = %s\n'%(self.L)
        txt += '.param W      = %s\n'%(self.W)
        txt += '.param M      = %s\n'%(self.M)
        txt += '.param freq   = %s\n'%(f)
        txt += '.param num    = %s\n'%(stepNum)
        txt += '.param start  = %s\n'%(stepStart)
        txt += '.param delta  = %s\n'%(stepStep)
        txt += '.param select = 0\n\n'
        txt += '%s\n\n'%(self.lib)
        # MOS with voltage feedback loop for creating the gate-source voltage
        txt += 'M1_OP d1 g1 s1 b1 %s W={W} L={L} M={M}\n'%(self.dev)
        # LOOP and DC voltages
        txt += 'V5 s1 0 {VS}\nV6 b1 0 {VB}\nV7 d1 1 {VD}\nE1 g1 d1 1 0 100\nI1 0 1 {ID}\n'
        # MOS for parameter measurement
        txt += 'M1 d2 g2 s2 b2 %s W={W} L={L} M={M}\n'%(self.dev)
        # VGS copy
        txt += 'E2 g2 2 g1 0 1\n'
        with open('cir/MOS_OP_I.cir', 'r') as f:
            txt += f.read()
        with open('MOS_OP.cir', 'w') as f:
            f.write(txt)
        _run_ngspice([ini.ngspice, '-b', 'MOS_OP.cir', '-o', 'MOS_OP.log'])
        #remove('MOS_OP.cir')
        #remove('MOS_OP.log')
        self._getParams()
        self._makeParDefs()
        self._makeModelDef()
        self._determineAccuracy()

    def getOPvg(self, VG, VD, VS, VB, f, step=None):
        """
        Returns operating point information of the device with the gate
        voltage as (swept) independent variable.

        :param W: Width of the device in [m]
        :type W: float

        :param L: Length of the device in [m]
        :type L: float

        :param M: Number of devices in parallel
        :type M: int

        :param VG: Gate voltage with respect to ground in [V]
        :type VG: float

        :param VD: Drain voltage with respect to ground in [V]
        :type VD: float

        :param VS: Source voltage with respect to ground in [V]
        :type VS: float

        :param VB: Bulk voltage with respect to ground in [V]
        :type VB: float

        :param step: Step data for VG; list with start value, number of values
                     and stop value. Defaults to None
        """
        if not isinstance(step, list) or len(step) != 3:
            stepStart = '{VG}'
            stepNum   = '1'
            stepStep  = '0'
        else:
            stepStart = str(float(step[0]))
            stepNum   = str(int(step[1]))
            stepStep  = str(float(step[2]))
            self.step = True
        txt =  'MOS_OP_V\n'
        txt += '.param VG     = %s\n'%(VG)
        txt += '.param VD     = %s\n'%(VD)
        txt += '.param VS     = %s\n'%(VS)
        txt += '.param VB     = %s\n'%(VB)
        txt += '.param L      = %s\n'%(self.L)
        txt += '.param W      = %s\n'%(self.W)
        txt += '.param M      = %s\n'%(self.M)
        txt += '.param freq   = %s\n'%(f)
        txt += '.param num    = %s\n'%(stepNum)
        txt += '.param start  = %s\n'%(stepStart)
        txt += '.param delta  = %s\n'%(stepStep)
        txt += '.param select = 0\n\n'
        txt += '%s\n\n'%(self.lib)
        txt += '%s d g s b %s W={W} L={L} M={M}\n\n'%(self.refDes, self.dev)
        with open('cir/MOS_OP_V.cir', 'r') as f:
            txt += f.read()
        with open('MOS_OP.cir', 'w') as f:
            f.write(txt)
        _run_ngspice([ini.ngspice, '-b', 'MOS_OP.cir', '-o', 'MOS_OP.log'])
        remove('MOS_OP.cir')
        remove('MOS_OP.log')
        self._getParams()
        self._makeParDefs()
        self._makeModelDef()
        self._determineAccuracy()

    def _getParams(self):
        with open('MOS_OP.out', 'r') as f:
            lines = f.readlines()
        #remove('MOS_OP.out')
        names  = False
        values = False
        self.params = {}
        parnames = []
        i = 0
        for line in lines:
            fields = line.split()
            if len(fields):
                if names and fields[0] != 'Values:':
                    parnames.append(fields[1])
                if fields[0] == 'Variables:':
                    names = True
                elif fields[0] == 'Values:':
                    names = False
                    values = True
                if values:
                    if len(fields) == 2:
                        i = 0
                    if parnames[i] in self.params:
                        self.params[parnames[i]].append(float(fields[0]))
                        i += 1
                    elif fields[0] != 'Values:':
                        if self.step:
                            self.params[parnames[i]] = [float(fields[0])]
                            i += 1
                        else:
                            self.params[parnames[i]] = float(fields[0])
                            i += 1
        del self.params['yes']
        if self.step:
            for key in self.params:
                self.params[key] = array(self.params[key])

    def _makeParDefs(self):
        self.parDefs = {}
        self.parDefs[Symbol('gm_' + self.refDes)] = self.params['ggs']
        self.parDefs[Symbol('gb_' + self.refDes)] = self.params['gbs']
        self.parDefs[Symbol('go_' + self.refDes)] = self.params['gdd']
        self.parDefs[Symbol('cgs_' + self.refDes)] = (self.params['cgs'] + self.params['csg'])/2
        self.parDefs[Symbol('cgb_' + self.refDes)] = (self.params['cgb'] + self.params['cbg'])/2
        self.parDefs[Symbol('cdg_' + self.refDes)] = (self.params['cdg'] + self.params['cgd'])/2
        self.parDefs[Symbol('cdb_' + self.refDes)] = (self.params['cdb'] + self.params['cbd'])/2
        self.parDefs[Symbol('csb_' + self.refDes)] = (self.params['csb'] + self.params['cbs'])/2

    def _makeModelDef(self):
        txt = '.model %s M'%(self.refDes)
        txt += '\n+ gm=%s'%(self.params['ggs'])
        txt += '\n+ gb=%s'%(self.params['gbs'])
        txt += '\n+ go=%s'%(self.params['gdd'])
        txt += '\n+ cgs=%s'%((self.params['cgs'] + self.params['csg'])/2)
        txt += '\n+ cgb=%s'%((self.params['cgb'] + self.params['cbg'])/2)
        txt += '\n+ cdg=%s'%((self.params['cdg'] + self.params['cgd'])/2)
        txt += '\n+ cdb=%s'%((self.params['cdb'] + self.params['cbd'])/2)
        txt += '\n+ csb=%s'%((self.params['csb'] + self.params['cbs'])/2)
        self.modelDef = txt

    def _determineAccuracy(self):
        CGG = self.params['cgs'] + self.params['cgd'] + self.params['cgb']
        CDD = self.params['cds'] + self.params['cdg'] + self.params['cdb']
        CSS = self.params['csd'] + self.params['csg'] + self.params['csb']
        CBB = self.params['cbd'] + self.params['cbg'] + self.params['cbs']
        self.errors['cgg'] = (CGG-self.params['cgg'])/self.params['cgg']
        self.errors['cdd'] = (CDD-self.params['cdd'])/self.params['cdd']
        self.errors['css'] = (CSS-self.params['css'])/self.params['css']
        self.errors['cbb'] = (CBB-self.params['cbb'])/self.params['cbb']
        self.errors['cgs'] = ((self.params['cgs']-self.params['csg'])/(self.params['cgs']+self.params['csg']))
        self.errors['cgd'] = ((self.params['cgd']-self.params['cdg'])/(self.params['cgd']+self.params['cdg']))
        self.errors['cgb'] = ((self.params['cgb']-self.params['cbg'])/(self.params['cgb']+self.params['cbg']))
        self.errors['cbs'] = ((self.params['cbs']-self.params['csb'])/(self.params['cbs']+self.params['csb']))
        self.errors['cbd'] = ((self.params['cbd']-self.params['cdb'])/(self.params['cbd']+self.params['cdb']))

    def getSv_inoise(self, ID, VD, VS, VB, fmin, fmax, numDec):
        self.params = {}
        self.step   = None
        self.getOPid(ID, VD, VS, VB, sqrt(fmin*fmax))
        VGS = self.params['v(vgs)']
        if self.dev[0].lower() == 'p':
            VGS = -VGS
        IDS = self.params['i(ids)']
        print("Ids target  :", ID)
        print("Ids realized:", IDS, "\n")
        print("Vgs realized:", VGS, "\n")
        txt = "MOS_noise\n"
        txt += '%s\n\n'%(self.lib)
        txt += '.param L      = %s\n'%(self.L)
        txt += '.param W      = %s\n'%(self.W)
        txt += '.param M      = %s\n'%(self.M)
        txt += '.param VG     = %s\n'%(VGS + VS)
        txt += '.param VD     = %s\n'%(VD)
        txt += '.param VS     = %s\n'%(VS)
        txt += '.param VB     = %s\n'%(VB)
        txt += '%s d g s b %s W={W} L={L} M={M}\n\n'%(self.refDes, self.dev)
        txt += 'V1 dd 0  dc {VD}\n'
        txt += 'V2 g  0  dc {VG} ac 1\n'
        txt += 'V3 s  0  dc {VS}\n'
        txt += 'V4 b  0  dc {VB}\n'
        txt += 'L1 d  dd 1G\n'
        txt += '.end'
        with open('MOS_noise.cir', 'w') as f:
            f.write(txt)
        simCmd = 'noise V(d) V2 dec %s %s %s'%( str(numDec), str(fmin), str(fmax))
        namesDict = {'inoise': 'inoise_spectrum'}
        output = ngspice2traces('MOS_noise', simCmd, namesDict, stepCmd=None, traceType='onoise', squaredNoise=True)
        remove('MOS_noise.cir')
        remove('MOS_noise.csv')
        return output

def _run_ngspice(args, stdout_path=None, timeout=None):
    """Run ngspice as a direct child process so it can be reliably terminated.

    :param args: ngspice command and arguments as a list (run without a shell,
                 so the timeout kills ngspice itself, not just a shell wrapper).
    :param stdout_path: file to receive ngspice console output, or None to inherit.
    :param timeout: seconds before the job is killed, or None for no limit
                    (default; identical to the previous os.system behaviour).
    :return: True if ngspice completed, False if it timed out or could not run.
    """
    out = open(stdout_path, 'w') if stdout_path is not None else None
    try:
        # Windows: ngspice_con.exe is a console app, so each run pops up a
        # console window — visible, and slow to create/destroy (worst on the
        # parallel stepped runs). CREATE_NO_WINDOW suppresses it; the flag is
        # Windows-only, hence getattr → 0 elsewhere (Anton, Win10).
        subprocess.run(args, stdout=out, timeout=timeout,
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        return True
    except subprocess.TimeoutExpired:
        print("ERROR: NGspice exceeded the {} s time limit and was terminated.".format(timeout))
        return False
    except FileNotFoundError:
        print("ERROR: NGspice cannot be executed with: '{}'.".format(ini.ngspice))
        return False
    finally:
        if out is not None:
            out.close()


def ngspice2traces(cirFile, simCmd, namesDict, stepCmd=None, parList=None,
                   traceType='magPhase', squaredNoise=False, postProc=None,
                   saveLog=True, optDict=None, mode=None, timeout=None):
    """
    Creates a dictionary with values or traces from an ngspice run.

    :param cirFile: Name of the circuit file withouit '.cir' extension, located
                    in the cir folder.

    :type cirFile: str

    :param simCmd: ngspice instruction,

                   - ac dec 20 1 10meg
                   - tran 1n 10u
                   - dc Source Vstart Vstop Vincr [ Source2 Vstart2 Vstop2 Vincr2 ]
                   - noise V(out) Vs dec 10 1 10meg 1
                   - op

    :type simCmd: str

    :param stepCmd: Step instruction or None if no parameter stepping is performed:

                    Syntax: *<parname> <stepmethod> <firstvalue> (<lastvalue> <numberofvalues | listwithvalues>)*

                    - parname (*str*): name of the parameter (not a RefDes)
                    - stepmethod (*str*): lin, log or list

    :type stepCmd: str, nonetype

    :param namesDict: Dictionary with key-value pairs:

                      key: plot label (*str*)

                      value: nodal voltage, branch current or device parameter in ngspice notation

    :type namesDict: dict

    :param traceType: Type of traces for AC, noise, and FFT analysis:

                      - realImag: real and imaginary parts
                      - magPhase: magnitude and phse
                      - dBmagPhase: dB(magnitude) and phase
                      - onoise: output referred noise
                      - inoise: input referred noise

    :type traceType: str

    :param parList: List with parameter definitions, each item in the list must
                    be a tuple with the name and the value of a parameter. The
                    name must be a string, and the value a string, an integer,
                    a float, or a SPICE expression (between curly brackets).
                    The order of parameter definitions should be such that
                    SPICE can evaluate a numeric value for each parameter in a
                    non-recursive way.

                    :Example:

                    >>> params = [('R', '1k'), ('C', '1n'), ('tau', '{1/(R*C)}')]

    :type parList: list

    :param squaredNoise: - True: output in V^2/Hz, A^2/Hz, V^2 or A^2
                         - False: output in V/rt(Hz), A/rt(Hz), V or A

                         Defaults to True

    :type squaredNoise: Bool

    :param postProc: Post processing fuction for transient analysis:

                     - None

                       No post processing is performed

                     - FFT <vector> (<vector> ...)

                       Returns the Fast Fourier Transform of one or more vectors
                       obtained from a transient analysis. Curently only Hanning
                       windowing has been implemented.

                     - FOURIER <vector> (<vector> ...)

                       Lists the values of the first ten harmonics of one or
                       more vectors obtained from a transient analysis in the
                       simulation log file.

    :type postProc: str, NoneType

    :param saveLog: True | False, defaults to True. The log file is saved in the
                    txt folder in the project directory. The name is the circuit
                    file name with '.log' file extension.

    :type saveLog: Bool

    :param optDict: None (default) or a dictionary with NGspice options, The
                    keys are the NGspice option names and the values are 'None'
                    if the option requires no value, or the option value.

    :type optDict: NoneType, dict

    :param mode: NGspice simulation mode, defaults to 'ltpsa'

    :return: - In case of an "OP" instruction without parameter stepping:

               A dictionary with key-value pairs:

               - key: *str* Name of the variable
               - value: *float* Value of the parameter, voltage or current

             - In all other cases: a tuple (*dict*, *str1*, *str2*)

               - dict

                 - key: *str* Name of the variable
                 - value: SLiCAP.SLiCAPplots.trace object or single value

               - str1: name of the x-variable
               - str2: units if the x-variable

    :rtype: tuple: dict, (dict, str, str)
    """
    if ini.ngspice != "":
        if mode is None:
            mode = 'ltpsa'
        else:
            mode = mode.lower()
        labels = {}
        simType = simCmd.split()[0].lower()
        with open(ini.cir_path + cirFile + '.cir', 'r') as f:
            netlistlines = f.readlines()
        netlist = ""
        for line in netlistlines:
            if line.strip().upper() != ".END":
                netlist += line
        netlist += "** Python input section **"
        if parList is not None:
            for pardef in parList:
                if pardef is not None and len(pardef) == 2:
                    netlist += "\n.param " + str(pardef[0]) + "=" + str(pardef[1])
        if stepCmd is not None:
            stepFields = stepCmd.split()
            stepPar = stepFields[0]
            stepMethod = stepFields[1].lower()
            if stepMethod == 'list':
                try:
                    stepList = eval(re.findall(r'\[[\s,.+-eE0-9]*\]', stepCmd)[0])
                except (IndexError, ValueError, SyntaxError):
                    print('Error in step list.')
                    return
            else:
                try:
                    stepStart  = float(_checkExpression(stepFields[2]))
                except (IndexError, ValueError, TypeError):
                    print('Error: missing or error in stepstart value.')
                    return
                try:
                    stepStop  = float(_checkExpression(stepFields[3]))
                except (IndexError, ValueError, TypeError):
                    print('Error: missing or error in stepCmd stop value.')
                    return
                try:
                    stepNum  = int(_checkExpression(stepFields[4]))
                except (IndexError, ValueError, TypeError):
                    print('Error: missing or error in step number.')
                    return
            if stepMethod == 'lin':
                stepList = linspace(stepStart, stepStop, stepNum)
            elif stepMethod == 'log':
                stepList = geomspace(stepStart, stepStop, stepNum)
            for i in range(len(stepList)):
                cmdsection = ""
                traceNames = []
                if optDict is not None:
                    for opt, optVal in optDict.items():
                        cmdsection += '\n.option ' + opt + ' = ' + str(optVal)
                if stepPar.lower() == "temp":
                    cmdsection += '\n.option ' + stepPar + ' = ' + str(stepList[i])
                else:
                    cmdsection += '\n.param ' + stepPar + ' = ' + str(stepList[i])
                cmdsection += '\n.control\n'
                if simType == 'noise' and squaredNoise:
                    cmdsection += '\nset sqrnoise\n'
                cmdsection += simCmd + '\n'
                cmdsection += '\nset wr_vecnames\nset wr_singlescale\n'
                if simType == 'noise':
                    totalNoise = False
                    cmdsection += '\nsetplot noise1\n'
                for key in namesDict:
                    if namesDict[key].lower().split("_")[-1] != "total":
                        traceName = key + '_' + str(i)
                        labels[traceName] = key + ':' + stepPar + '=' + '{0: 8.2e}'.format(stepList[i])
                        # remove whitespace (compact label)
                        labels[traceName] = ''.join(labels[traceName].split())
                        cmdsection += 'let ' + traceName + ' = ' + namesDict[key] + '\n'
                        traceNames.append(traceName)
                    else:
                        totalNoise = True
                if simType == 'noise' and totalNoise:
                    cmdsection += '\nsetplot noise2\n'
                    for key in namesDict:
                        if namesDict[key].lower().split("_")[-1] == "total":
                            traceName = key + '_' + str(i)
                            labels[traceName] = key + ':' + stepPar + '=' + '{0: 8.2e}'.format(stepList[i])
                            # remove whitespace (compact label)
                            labels[traceName] = ''.join(labels[traceName].split())
                            cmdsection += 'let ' + traceName + ' = ' + namesDict[key] + '\n'
                            traceNames.append(traceName)
                if i > 0:
                    cmdsection += "\nset appendwrite"
                if postProc is not None:
                    cmdsection += postProc + '\n'
                cmdsection += '\nwrdata ' + ini.cir_path + cirFile  + '.csv'
                for name in traceNames:
                    cmdsection += ' ' + name
                cmdsection += '\n.endc\n'
                if i == 0:
                    netlist += '\n.end'
                simName = cirFile.replace("\\", "/").split("/")[-1]
                with open(ini.cir_path + cirFile + '_sim.sp', 'w') as f:
                    f.write(netlist + cmdsection)
                if not _run_ngspice([ini.ngspice, '-b', ini.cir_path + cirFile + '_sim.sp',
                                     '-D', 'ngbehavior=' + mode,
                                     '-o', ini.txt_path + simName + '_sim.log'],
                                    stdout_path=ini.txt_path + simName + '_sim.txt', timeout=timeout):
                    return None
        else:
            if optDict is not None:
                for opt, optVal in optDict.items():
                    netlist += '\n.option ' + opt
                    if optVal is not None:
                        netlist += ' = ' + str(optVal)
            netlist += '\n.control\nset wr_vecnames\nset wr_singlescale\n'
            if simType == 'noise' and squaredNoise:
                netlist += '\nset sqrnoise\n'
            netlist += simCmd + '\n'
            if simType == 'noise':
                totalNoise = False
                netlist += '\nsetplot noise1\n'
            for key in namesDict:
                if namesDict[key].lower().split("_")[-1] != "total":
                    netlist += 'let ' + key + ' = ' + namesDict[key] + '\n'
                else:
                    totalNoise = True
            if simType == 'noise' and totalNoise:
                netlist += '\nsetplot noise2\n'
                for key in namesDict:
                    if namesDict[key].lower().split("_")[-1] == "total":
                        netlist += 'let ' + key + ' = ' + namesDict[key] + '\n'
            if postProc is not None:
                netlist += postProc + '\n'
            netlist += 'wrdata ' + ini.cir_path + cirFile + '.csv'
            for key in namesDict:
                netlist += ' ' + key
            netlist += '\n.endc'
            netlist += '\n.end'
            simName = cirFile.replace("\\", "/").split("/")[-1]
            with open(ini.cir_path + cirFile + '_sim.sp', 'w') as f:
                f.write(netlist)
            if not _run_ngspice([ini.ngspice, '-b', ini.cir_path + cirFile + '_sim.sp',
                                 '-D', 'ngbehavior=' + mode,
                                 '-o', ini.txt_path + simName + '_sim.log'],
                                stdout_path=ini.txt_path + simName + '_sim.txt', timeout=timeout):
                return None
        try:
            with open(ini.cir_path + cirFile + '.csv', 'r') as f:
                txt = f.read()
            analysisType = simCmd.split()[0].upper()
            if analysisType == 'DC':
                lines = txt.splitlines()
                xVar = lines[0].split()[0]
                labels[xVar] = simCmd.split()[1]
            if analysisType == 'NOISE' and totalNoise:
                lines = txt.splitlines()
                xVar = lines[0].split()[0]
                labels[xVar] = simCmd.split()[1]
                analysisType = "OP"
            if labels:
                for key in labels:
                    txt = txt.replace(key + ' ', labels[key] + ' ')
            with open(ini.cir_path + cirFile + '.csv', 'w') as f:
                f.write(txt)
            fileName = cirFile.split('/')[-1]
            copy2(ini.cir_path + cirFile + '.csv', ini.csv_path + fileName + '.csv')
            traceDict = _processNGspiceResult(cirFile, analysisType, traceType, postProc)
            return traceDict
        except FileNotFoundError:
            try:
                simName = cirFile.replace("\\", "/").split("/")[-1]
                with open(ini.txt_path + simName + '_sim.log') as f:
                    for line in f.readlines():
                        print(line)
            except FileNotFoundError:
                print("ERROR: NGspice cannot be executed with: '{}'.".format(ini.ngspice))
    else:
        print("NGspice command not found in the [command] section of '{}'.".format(ini.home_path + "SLiCAP.ini"))

def _processNGspiceResult(cirFile, analysisType, traceType, postProc):
    # Read the CSV file
    traceDict = None
    with open(ini.cir_path + cirFile + '.csv', 'r') as f:
        lines = f.readlines()
    analysisType = analysisType.upper()
    if analysisType == 'DC' or analysisType == 'NOISE' or (analysisType == 'TRAN' and  (postProc is None or postProc.split()[0].upper() == "FOURIER")):
        traceDict = _makeDCTRNStraces(lines)
    elif analysisType.upper() == 'AC' or analysisType == 'TRAN':
        traceDict = _makeACtraces(lines, traceType)
    elif analysisType == "OP":
        traceDict = _makeOPtraces(lines)
    else:
        raise NotImplementedError()
    remove(ini.cir_path + cirFile + '.csv')
    return traceDict

def _makeOPtraces(lines):
    traceDict = {}
    varNames  = []
    stepPar   = None
    stepVals  = []
    step      = True
    for i in range(len(lines)):
        fields = lines[i].split()
        if i == 0:
            firstVar = fields[0]
            labels = [fields[j].strip() for j in range(1, len(fields))]
            for var in labels:
                try:
                    varName, parDef = var.split(":")
                    stepPar, stepVal = parDef.split("=")
                    varNames.append(varName)
                    traceDict[varName] = []
                except ValueError:
                    step = False
                    varNames.append(var)
                    traceDict[var] = []
        if step:
            if fields[0] == firstVar:
                var = fields[1].strip()
                varName, parDef = var.split(":")
                stepPar, stepVal = parDef.split("=")
            else:
                values = [eval(field) for field in fields]
                for j in range(1, len(values)):
                    traceDict[varNames[j-1]].append(values[j])
                stepVals.append(eval(stepVal))
        elif fields[0] != firstVar:
            try:
                values = [eval(fields[j]) for j in range(1, len(fields))]
                for j in range(1, len(fields)):
                    traceDict[varNames[j-1]].append(values[j-1])
            except NameError:
                print("Error in parsing NGspice results (often indicating 'nan' values). Check the log file for details.")
                return traceDict
    if step:
        for key in traceDict:
            traceDict[key] = trace([stepVals, traceDict[key]])
            traceDict[key].label = key
        traceDict = (traceDict, stepPar, "")
    else:
        for key in traceDict:
            traceDict[key] = traceDict[key][0]
    return traceDict

def _makeDCTRNStraces(lines):
    traceDict = {}
    for i in range(len(lines)):
        fields = lines[i].split()
        if i == 0:
            xVar = fields[0]
        if fields[0] == xVar:
            # We have a new trace
            labels = [fields[j] for j in range(1, len(fields))]
            for label in labels:
                traceDict[label] = [[],[]] # time, value
        else:
            for j in range(len(labels)):
                traceDict[labels[j]][0].append(eval(fields[0])) # time
                traceDict[labels[j]][1].append(eval(fields[j+1])) # value
    for key in traceDict:
        traceDict[key] = trace((traceDict[key][0], traceDict[key][1]))
        traceDict[key].label = key
    if xVar == "frequency":
        xUnits = "Hz"
    elif xVar == "time":
        xUnits = "s"
    else:
        xUnits = ""
    return traceDict, xVar, xUnits

def _makeACtraces(lines, traceType):
    reMagDict = {}
    imPhsDict = {}
    traceDict = {}
    for i in range(len(lines)):
        fields = lines[i].split()
        if i == 0:
            xVar = fields[0]
        if fields[0] == xVar:
            labels = [fields[j] for j in range(1, len(fields))]
            for label in labels:
                traceDict[label] = [[],[],[]] # frequency, real, imag
        else:
            for j in range(len(labels)):
                if j%2:
                    traceDict[labels[j]][2].append(eval(fields[j+1])) # imag
                else:
                    traceDict[labels[j]][0].append(eval(fields[0])) # frequency
                    traceDict[labels[j]][1].append(eval(fields[j+1])) # real
    for key in traceDict:
        freq = traceDict[key][0]
        real = array(traceDict[key][1])
        imag = array(traceDict[key][2])
        if traceType == 'realImag':
            reMagDict[key] = trace((freq, real))
            reMagDict[key].label = key
            imPhsDict[key] = trace((freq, imag))
            imPhsDict[key].label = key
        elif traceType == 'magPhase':
            reMagDict[key] = trace((freq, sqrt(real**2+imag**2)))
            reMagDict[key].label = key
            imPhsDict[key] = trace((freq, unwrap(arctan(imag/real), discont=pi/4, period=pi/2)*180/pi))
            imPhsDict[key].label = key
        elif traceType == 'dBmagPhase':
            reMagDict[key] = trace((freq, 10*log10(real**2+imag**2)))
            reMagDict[key].label = key
            imPhsDict[key] = trace((freq, unwrap(arctan(imag/real), discont=pi/4, period=pi/2)*180/pi))
            imPhsDict[key].label = key
    if xVar == "frequency":
        xUnits = "Hz"
    else:
        xUnits = ""
    return reMagDict, imPhsDict, xVar, xUnits

def selectTraces(traceDict, namesList):
    """
    This function returns a dictionary selected traces from a dictionary with traces.

    :param traceDict: A dictionary with key-value pairs:
                      - key: name of the trace
                      - value: a SLiCAP.SLiCAPplots.trace object holding trace (x, y) data and a trace label

    :param namesList: A list with names of traces (== keys in traceDict) that needs to be returned
    :return:          a dictionary with selected traces (sub of traceDict)
    :rtype:           dict
    """
    return {key: traceDict[key] for key in namesList if key in traceDict}


def NGspiceRaw2dict(raw_path, step_param=None, step_values=None):
    """
    Parse an NGspice Nutmeg raw file and return a unified result dictionary.

    The dictionary layout depends on the analysis type and whether stepping
    was used:

    **OP (no stepping)** — all values are Python floats::

        {"v(out)": 1.23, "i(v1)": -4.56e-3, ...}

    **Sweep (no stepping)** — 1-D numpy arrays::

        {"time": array, "v(out)": array, ...}          # transient
        {"frequency": array, "v(out)": array, ...}     # AC (complex arrays)

    **OP (stepped)** — 1-D arrays, one value per step::

        {"R1": array, "v(out)": array, ...}

    **Sweep (stepped)** — sweep variable 1-D, signals 2-D (n_steps × n_sweep)::

        {"frequency": array, "R1": array, "v(out)": 2-D array, ...}

    For AC analysis the signal arrays are ``dtype=complex128``.  Use the
    helpers in ``SLiCAPmath`` (``mag()``, ``dB()``, ``phase()``) for post-processing.

    :param raw_path: Path(s) to NGspice ``.raw`` file(s).  Pass a single
                     ``str``/``Path`` for a non-stepped run.  For stepped runs
                     pass the list of per-step raw-file paths returned by
                     the deck's control block; one ``Analysis`` block is read
                     from each file and the step files are deleted afterwards.
    :type raw_path: str, pathlib.Path, list

    :param step_param: Name of the stepped parameter (e.g. ``"R1"``).
    :type step_param: str, NoneType

    :param step_values: 1-D sequence of step parameter values.
    :type step_values: list, numpy.ndarray, NoneType

    :return: Result dictionary — structure depends on analysis type (see above).
    :rtype: dict
    """
    if isinstance(raw_path, list):
        analyses = []
        for p in raw_path:
            blocks = RawFile.load(p)
            if blocks:
                analyses.append(blocks[0])
            Path(p).unlink(missing_ok=True)
    else:
        analyses = RawFile.load(raw_path)
    if not analyses:
        return {}

    is_op        = all("operating point" in a.name.lower() for a in analyses)
    array_stepped = isinstance(step_param, list)
    stepped      = step_values is not None and len(analyses) > 1

    if not stepped:
        # Single analysis block — no stepping
        a = analyses[0]
        if is_op:
            return {name: float(np.real(arr[0])) for name, arr in a.signals.items()}
        result = {a.x_name: a.x_data}
        result.update(a.signals)
        return result

    a0     = analyses[0]
    n_runs = len(analyses)

    if array_stepped:
        # Array stepping — step_values shape (n_runs, n_params).
        # Step info stored as "run_1", "run_2", ... each holding a 1-D array
        # of parameter values for that run (in the order of step["params"]).
        step_values = np.asarray(step_values, dtype=float)
        run_keys    = [f"run_{i + 1}" for i in range(n_runs)]

        if is_op:
            result = {run_keys[i]: step_values[i] for i in range(n_runs)}
            for name in a0.signals:
                result[name] = np.array(
                    [float(np.real(a.signals[name][0]))
                     for a in analyses if name in a.signals]
                )
            return result

        result = {a0.x_name: a0.x_data}
        for i in range(n_runs):
            result[run_keys[i]] = step_values[i]
        for name in a0.signals:
            arrays = [a.signals[name] for a in analyses if name in a.signals]
            if arrays:
                result[name] = np.stack(arrays, axis=0)   # (n_runs, n_sweep)
        return result

    # Single-parameter stepping — step_values is 1-D
    step_values = np.asarray(step_values, dtype=float)
    step_key    = step_param if step_param is not None else "step_val"

    if is_op:
        result = {step_key: step_values}
        for name in a0.signals:
            result[name] = np.array(
                [float(np.real(a.signals[name][0]))
                 for a in analyses if name in a.signals]
            )
        return result

    result = {a0.x_name: a0.x_data, step_key: step_values}
    for name in a0.signals:
        arrays = [a.signals[name] for a in analyses if name in a.signals]
        if arrays:
            result[name] = np.stack(arrays, axis=0)   # (n_steps, n_sweep)
    return result


# =============================================================================
# New simulation API — raw-file based, for-loop stepping
# =============================================================================

def _no_stepping(reason, hint=""):
    """An incomplete step definition: report it and step nothing.

    ``(None, None)`` is what a caller already reads as "not stepped", so an
    incomplete definition takes the same route as ``step=None``.  Both places
    that ask whether a run is stepped then agree: ``_run_stepped`` (on the
    values) and ``_dict_to_instruction`` (on the parameter name).  Before
    this, a definition without a parameter name ran N IDENTICAL simulations
    and recorded no step data (Anton, 2026-07-29).

    It is reported rather than dropped silently: the caller asked for N runs
    and gets one, which changes what the traces mean.
    """
    print("Warning: " + reason + "; no stepping applied.")
    if hint:
        print("         " + hint)
    return None, None


_STEP_KEY_HINT = ('single-parameter stepping uses "param" (a name), the '
                  '"array" method uses "params" (a list of names).')


def _step_values(step):
    """Parse a step dict; return (param, vals) where:

    - Single-parameter methods (lin / log / list):
        param  → str (parameter name)
        vals   → 1-D ndarray of step values

    - Array method (multiple parameters, one set of values per run):
        param  → list[str] (parameter names)
        vals   → 2-D ndarray, shape (n_runs, n_params)

    Values may be numbers or strings with a SLiCAP scale factor ('5p', '2.2k').

    Returns (None, None) when *step* is None, and likewise - with a message -
    when the definition names no parameter or lacks its values: this is the
    ONE place the step dict is interpreted (:func:`_no_stepping`).
    """
    if step is None:
        return None, None
    method = step.get("method", "list").lower()
    if method not in ("lin", "log", "list", "array"):
        raise ValueError(
            f"step method must be 'lin', 'log', 'list', or 'array'; got {method!r}")

    # The parameter name(s): without one there is nothing to step.
    if method == "array":
        names = step.get("params")
        if isinstance(names, str):
            names = [names]
        if not names:
            return _no_stepping(
                'step method "array" without "params"',
                _STEP_KEY_HINT if step.get("param") else "")
    else:
        names = step.get("param")
        if not names:
            return _no_stepping(
                'step definition without "param"',
                _STEP_KEY_HINT if step.get("params") else "")

    # The values: also required, and missing ones used to raise a bare KeyError.
    if method in ("lin", "log"):
        missing = [k for k in ("start", "stop", "num") if step.get(k) is None]
        if missing:
            return _no_stepping('step method "{0}" without {1}'.format(
                method, ", ".join('"' + k + '"' for k in missing)))
    elif not step.get("values"):
        return _no_stepping('step method "{0}" without "values"'.format(method))

    if method == "lin":
        return names, np.linspace(_scale_float(step["start"]),
                                  _scale_float(step["stop"]),
                                  int(step["num"]))
    if method == "log":
        return names, np.geomspace(_scale_float(step["start"]),
                                   _scale_float(step["stop"]),
                                   int(step["num"]))
    if method == "list":
        return names, np.asarray([_scale_float(v) for v in step["values"]])
    vals = np.asarray([[_scale_float(v) for v in row]
                       if isinstance(row, (list, tuple))
                       else _scale_float(row)
                       for row in step["values"]])   # (n_runs, n_params)
    if vals.ndim == 1:
        vals = vals.reshape(-1, 1)       # single param passed as flat list
    return names, vals


def _control_block(analysis_cmd, raw_path, options=None, noise=False,
                   extra_saves=None, post_lines=None):
    """Build the .control ... .endc section for a SINGLE run; return ctrl_str.

    *extra_saves* is an optional list of additional NGspice save expressions
    (e.g. ``["@q1[gm]", "@q2[gm]"]``) needed for device operating-point
    parameters that ``save all`` does not include.

    *post_lines* are commands run AFTER the analysis and BEFORE the raw file
    is written — transient post-processing (``linearize``/``fft`` make the
    spectrum the current plot, so the write then stores the spectrum;
    ``fourier`` prints its harmonics table to stdout).
    """
    # Force binary raws: some ngspice builds (notably Windows) default to ASCII,
    # which is larger, slower to parse, and needs the "real,imag" complex path.
    # WHAT the simulator writes. An empty save list means everything
    # (Anton, 2026-08-01: the analysis call speaks NGspice, the Python names
    # are chosen afterwards in make_traces).
    lines = [".control", "set filetype=binary"]
    lines.append("save " + " ".join(extra_saves) if extra_saves else "save all")
    if noise:
        lines.append("set sqrnoise")
    if options:
        for k, v in options.items():
            lines.append(f"option {k} = {_deck_value(v, k)}"
                         if v is not None else f"option {k}")
    lines.append(analysis_cmd)
    if noise:
        # A noise run leaves TWO plots: <noiseN> with the spectral densities
        # and <noiseN+1> with the integrated noise, the latter current. The
        # spectra are therefore the PREVIOUS plot - not the absolute name
        # "noise1", which in a stepped run is always the FIRST run's spectra,
        # so every step wrote the same data (Anton, 2026-07-31: noise vs
        # temperature came out constant).
        lines.append("setplot previous")
    if post_lines:
        lines.extend(post_lines)
    lines.append(f"write {Path(raw_path).as_posix()}")
    lines.append(".endc")
    return "\n".join(lines)


def _ng_number(v) -> str:
    """Format a step value as an NGspice numeric literal."""
    return f"{float(v):.12g}"


def _stepped_control_block(analysis_cmd, raw_path, step_param, step_vals,
                           options=None, noise=False, extra_saves=None,
                           post_lines=None):
    """One ``.control`` block that sweeps one OR several parameters over
    *step_vals* in ONE NGspice process (the design-doc approach; see
    NGspice_simulator.md).  A counter (``dowhile``) walks per-parameter value
    arrays (``compose``); each run alters the parameters and re-runs, APPENDING
    its analysis to *raw_path* — ``RawFile.load`` reads the N appended blocks as
    the stepped result.  No per-step files, no N processes.

    Ordering matters (verified against ngspice):
      * a ``.param`` is set as a SCALAR *before* ``reset`` — ``alterparam P =
        $&x`` — the ``$&`` dereference that avoids the vector pitfall (SLNG.md);
      * ``TEMP`` is set *after* ``reset`` — ``option temp = $&x`` — the only
        order ngspice honours (``set temp`` before reset is ignored).

    *step_param* may be a str (single) or list (array/multi); *step_vals* is
    then 1-D or 2-D ``(n_runs, n_params)``.
    """
    if isinstance(step_param, list):
        params = list(step_param)
        rows   = [[step_vals[i][j] for j in range(len(params))]
                  for i in range(len(step_vals))]
    else:
        params = [step_param]
        rows   = [[v] for v in step_vals]
    n = len(rows)

    lines = [".control", "set filetype=binary", "set appendwrite"]
    for j, _p in enumerate(params):
        vs = " ".join(_ng_number(rows[i][j]) for i in range(n))
        lines.append(f"compose __a{j} values {vs}")
    lines += [f"let __n = {n}", "let __i = 0", "dowhile __i < __n"]

    temp_idx = None
    for j, p in enumerate(params):
        lines.append(f"  let __v{j} = __a{j}[__i]")
        if str(p).lower() == "temp":
            temp_idx = j                      # applied AFTER reset (below)
        else:
            lines.append(f"  alterparam {p} = $&__v{j}")
    lines.append("  reset")
    if temp_idx is not None:
        lines.append(f"  option temp = $&__v{temp_idx}")
    lines.append("  save " + " ".join(extra_saves) if extra_saves
                 else "  save all")
    if noise:
        lines.append("  set sqrnoise")
    if options:
        for k, v in options.items():
            lines.append(f"  option {k} = {_deck_value(v, k)}"
                         if v is not None else f"  option {k}")
    lines.append("  " + analysis_cmd)
    if noise:
        lines.append("  setplot previous")   # this run's spectra, not run 1's
    if post_lines:
        lines.extend("  " + pl for pl in post_lines)
    lines.append(f"  write {Path(raw_path).as_posix()}")
    lines.append("  let __i = __i + 1")
    lines.append("end")
    lines.append(".endc")
    return "\n".join(lines)


def _deck_number(value, what):
    """A NUMBER for NGspice input, or a ValueError naming the offender.

    For positions where NGspice needs a plain number and no expression is
    possible: the arguments of an analysis command, the fourier frequency.
    The value is read in SLiCAP notation - a scale factor is exactly ONE
    case-sensitive character - so the SPICE spellings are refused HERE rather
    than reaching the simulator, where '10K' or '1MEG' would silently mean
    something else or nothing at all (Anton, 2026-07-31).

    :param value: the value as the user wrote it.
    :type value: str, int, float

    :param what: what is being converted, for the error message ('fstop', …).
    :type what: str

    :return: the number as deck text.
    :rtype: str
    """
    text = _deck_expr(value, what)
    if text.startswith("{"):
        raise ValueError(
            "{0} = '{1}' must be a number here; it still contains a symbol "
            "({2}). An analysis argument cannot be resolved by NGspice from "
            "a .param.".format(what, value, text))
    return text


def _eng_repr(number):
    """A float as deck text, without an exponent Python would write as
    '1e+06': NGspice reads 'e' notation, but a plain repr keeps the deck
    readable for the user who opens it."""
    text = repr(float(number))
    return text[:-2] if text.endswith('.0') else text


#: Names sympy owns that are ordinary netlist identifiers are rescued by
#: SLiCAP's own parser (:data:`SLiCAP.SLiCAPlex._SYMPY_NAMES`); a deck value
#: is read with exactly the same rule as a SLiCAP value.
#: E and I were dropped from this list on 2026-08-19: they keep their
#: mathematical meaning everywhere in SLiCAP (Euler, imaginary unit), so a
#: current is named I_xx. An expression that still evaluates to a complex
#: number is refused below. 'lambda' cannot be rescued - it is a Python
#: keyword - so it is refused by name (Anton, 2026-08-16).


def _deck_expr(value, what):
    """SLiCAP text -> NGspice deck text: constants evaluated, symbols kept.

    ONE converter for everything that reaches a deck - component values,
    ``.param`` definitions, subcircuit defaults, stimulus arguments and the
    numeric arguments of an analysis. Scale factors are expanded, constants
    such as ``pi`` and ``sqrt(2)`` are evaluated, and anything that is not
    SLiCAP notation is refused HERE, where the message reaches the user, not
    in the NGspice log.

    NGspice's numparam parser knows neither SLiCAP's scale factors nor
    ``pi``: ``R1 1 0 {2*pi*1k}`` aborts the run, and an untranslated ``1M``
    is read as 1 milli - wrong by a factor of a million, silently. Both are
    removed by evaluating here. Complex results are refused: NGspice has no
    use for them.

    :param value: the value as the user wrote it, braces optional.
    :param what: what is being converted, for the error message.
    :return: deck text - a plain number, or ``{expression}`` when a symbol
             remains for NGspice to resolve from its own ``.param``.
    :rtype: str
    """
    import sympy as sp
    from SLiCAP.SLiCAPlex import _replaceScaleFactors
    text = str(value).strip()
    if text.startswith('{') and text.endswith('}'):
        text = text[1:-1].strip()      # the braces are netlist syntax, not maths

    def _refuse(why=""):
        raise ValueError(
            "{0} = '{1}' is not valid SLiCAP notation{2}. A scale factor is "
            "ONE case-sensitive character: {3}. NGspice spellings ('1MEG', "
            "'10K', '1kohm', '1uF', '1mil') are not accepted.".format(
                what, value, why, " ".join(sorted(_SCALEFACTORS))))

    if not text:
        return text
    try:
        evaluated = sp.N(_sympify(_replaceScaleFactors(text)))
    except BaseException:
        _refuse()
    if evaluated is None:
        _refuse()
    if evaluated.has(sp.I) or evaluated.is_real is False:
        _refuse(" (a complex or infinite value)")
    # A numeric result is written as a plain number: sympy would print
    # '1000.00000000000' for '1k', which is right but unreadable in a deck
    # the user opens. One that kept symbols goes in braces, which is how
    # NGspice resolves a parameter inside a netlist line.
    if evaluated.is_number:
        return _eng_repr(float(evaluated))
    return "{" + str(evaluated) + "}"


def _deck_value(value, what):
    """A VALUE for NGspice input (expressions allowed) - see :func:`_deck_expr`."""
    return _deck_expr(value, what)


def _apply_instr_params(netlist_text, params):
    """Apply per-instruction parameter definitions to the netlist text.

    *params* is an **ordered** list of ``(name, value)`` tuples (the
    ``params=`` argument of ``op/dc/ac/tran/noise``).  A name already defined
    in the netlist is replaced **in place** — NGspice honours the *first*
    definition it encounters, so appending a redefinition would be silently
    ignored.  A new name is appended as a ``.param`` line **in list order**,
    so each definition can be evaluated non-recursively (the same contract as
    the legacy ``ngspice2traces`` ``parList``).
    """
    for name, value in params or []:
        # _deck_value reads the SLiCAP notation and returns deck-ready text:
        # a plain number, or an expression in braces for NGspice to resolve.
        sval = _deck_value(value, name)
        pat = re.compile(
            r'\b' + re.escape(str(name)) + r'\s*=\s*(?:\{[^}]*\}|\S+)',
            re.IGNORECASE,
        )
        netlist_text, n = pat.subn(f'{name} = {sval}', netlist_text)
        if n == 0:
            netlist_text = (netlist_text.rstrip('\n')
                            + f'\n.param {name} = {sval}\n')
    return netlist_text


def _format_stimulus(stim):
    """Format one stimulus (a list ``[type, arg1, arg2, …]``) as the source
    tail of an NGspice source line: ``AC``/``DC`` → ``TYPE args``; function
    types (``SIN``/``PULSE``/``PWL``/``EXP``/…) → ``TYPE(args)``."""
    typ  = str(stim[0]).upper()
    args = " ".join(_deck_value(a, typ) for a in stim[1:])
    if typ in ("AC", "DC"):
        return f"{typ} {args}".strip()
    return f"{typ}({args})"


def _apply_stimuli(netlist_text, stimuli):
    """Rewrite independent-source lines with per-run stimuli (Anton,
    2026-07-16). *stimuli* = ``{refdes: [type, arg1, …]}``; the source keeps
    its refdes and two nodes, everything after is replaced. One stimulus per
    source (the GUI runs one analysis / one control section per instruction).
    Matching is case-insensitive; sources not listed keep their netlist line."""
    if not stimuli:
        return netlist_text
    keys = {str(k).upper(): v for k, v in stimuli.items()}
    lines = netlist_text.splitlines()
    for i, line in enumerate(lines):
        tok = line.split()
        if len(tok) >= 3 and tok[0].upper() in keys \
                and tok[0][0].upper() in ("V", "I"):
            stim = _format_stimulus(keys[tok[0].upper()])
            lines[i] = f"{tok[0]} {tok[1]} {tok[2]} {stim}"
    return "\n".join(lines)


def _sim_files(cirFile):
    """The file names of one NGspice run: the deck, the ngspice ``-o`` log and
    the captured console output.

    ONE owner for the naming convention: the deck is ``<cir_path>/<cirFile>.sp``
    and its siblings share that base name.  Callers that need to READ a run's
    output (the ``fourier`` table is parsed from the log) ask here instead of
    rebuilding the name, so the convention cannot drift again.

    :param cirFile: circuit file name without extension.
    :type cirFile: str

    :return: ``(deck, log, stdout)`` paths.
    :rtype: tuple
    """
    sim_path = Path(ini.cir_path + cirFile + '.sp')
    return (str(sim_path),
            str(sim_path.with_suffix('.log')),
            str(sim_path.with_suffix('.txt')))


def _run_raw(cirFile, control_section, behavior, timeout,
             instr_params=None, stimuli=None, savecurrents=False):
    """Append control_section to cirFile.cir, run NGspice; return True on success.

    Writes ONE self-contained ngspice deck ``<cir_path>/<cirFile>.sp``: the
    ``<cirFile>.cir`` netlist followed by the analysis ``.control`` section
    (which sits at the end and does not affect the netlist above it).  It is
    regenerated on every run and doubles as the GUI's "Export NGspice Netlist"
    file — one file is enough.  The sibling ``.log`` (ngspice ``-o``) and
    ``.txt`` (console) share its base name (:func:`_sim_files`).

    *instr_params*: ordered list of ``(name, value)`` tuples — per-instruction
    parameter definitions applied to the netlist before the run.
    """
    sim_file, log_file, stdout_file = _sim_files(cirFile)

    with open(ini.cir_path + cirFile + '.cir', 'r') as f:
        netlist = f.read()
    stripped = "\n".join(l for l in netlist.splitlines()
                         if l.strip().upper() != '.END')
    if instr_params:
        stripped = _apply_instr_params(stripped, instr_params)
    if stimuli:
        stripped = _apply_stimuli(stripped, stimuli)
    if savecurrents:
        # Device currents, including those inside subcircuits (@r.x1.r1[i]).
        # It must be set when the circuit is PARSED: "set savecurrents" in the
        # control section, after the circuit is loaded, does nothing (measured
        # 2026-08-01).
        stripped = stripped.rstrip("\n") + "\n.options savecurrents\n"
    with open(sim_file, 'w') as f:
        f.write(stripped + "\n" + control_section + "\n.end\n")
    args = [ini.ngspice, '-b', sim_file, '-o', log_file]
    if behavior:
        args += ['-D', f'ngbehavior={behavior}']
    return _run_ngspice(args, stdout_path=stdout_file, timeout=timeout)


def _clean_run_outputs(cirFile, raw_path, stepped):
    """Start-of-run cleanup: remove THIS circuit's transient outputs from the
    PREVIOUS run before this run produces anything.  So no run inherits stale
    leftovers (e.g. per-step files from a run with more steps), and everything
    left after a run belongs to that run — useful for debugging.  Only
    prior-run files are removed, up front, so the current data flow is never
    corrupted.

    A run only clears the raw files it will REGENERATE:
      * always the per-step raws (``<stem>_s*.raw``);
      * the base raw (``<stem>.raw`` / ``<stem>_op.raw``) ONLY when *stepped* is
        False — an unstepped run rewrites it, a stepped run does not.
    So an unstepped ``op`` run's ``<stem>_op.raw`` survives a later STEPPED op
    and any ``ac``/``tran``/… run — exactly what the bias annotation reads.
    """
    cir  = Path(ini.cir_path)
    base = Path(raw_path)
    # The run's own deck and outputs (_sim_files) plus the per-step files of
    # the pre-single-process era.  The log is REGENERATED by this run and is
    # read back for the fourier table, so a stale one must not survive.
    for pattern in (f"{cirFile}.sp",   f"{cirFile}.log",   f"{cirFile}.txt",
                    f"{cirFile}_s*.sp", f"{cirFile}_s*.log", f"{cirFile}_s*.txt"):
        for old in cir.glob(pattern):
            old.unlink(missing_ok=True)
    for old in base.parent.glob(base.stem + "_s*.raw"):   # per-step raws (regenerated)
        old.unlink(missing_ok=True)
    if not stepped:                                       # unstepped run rewrites the base raw
        base.unlink(missing_ok=True)


def _run_stepped(cirFile, analysis_cmd, raw_path, step_param, step_vals,
                 options=None, noise=False, extra_saves=None, behavior=None,
                 timeout=None, instr_params=None, post_lines=None,
                 stimuli=None, savecurrents=False):
    """Run NGspice and return a list of raw-file paths, or None on error.

    - Non-stepped: single run, returns ``[raw_path]``.
    - Stepped: ONE ngspice process sweeps every step value (see
      :func:`_stepped_control_block`) and APPENDS its N analyses to a single
      ``*_step.raw``, returned as a one-element list.  Both single-parameter
      and array/multi-parameter sweeps use this path -- ``alterparam`` (before
      ``reset``) for a ``.param``, ``option temp`` (after ``reset``, the ngspice
      temperature model, manual sec.1.3) for TEMP.  ``NGspiceRaw2dict`` reads
      the N-block raw for both single and array stepping.

    (Earlier this fanned out to N parallel subprocesses writing ``*_sN.raw``;
    ngspice's own control-section stepping does it in one process -- fewer
    files, no per-step netlist injection.)
    """
    base = Path(raw_path)

    # Clear this circuit's transient outputs from the previous run before this
    # one writes anything (see _clean_run_outputs): no run inherits stale
    # leftovers, everything left afterwards belongs to this run, and _op.raw
    # survives non-op runs for the bias annotation.
    _clean_run_outputs(cirFile, raw_path, step_vals is not None)

    if step_vals is None:
        ctrl = _control_block(analysis_cmd, str(base), options, noise,
                              extra_saves, post_lines)
        if not _run_raw(cirFile, ctrl, behavior, timeout,
                        instr_params=instr_params, stimuli=stimuli,
                    savecurrents=savecurrents):
            return None
        return [str(base)]

    # Every sweep -> ONE ngspice process: N analyses appended to one raw.
    stepped_raw = base.with_name(base.stem + "_step.raw")
    stepped_raw.unlink(missing_ok=True)              # fresh appendwrite target
    ctrl = _stepped_control_block(analysis_cmd, str(stepped_raw), step_param,
                                  list(step_vals), options, noise,
                                  extra_saves, post_lines)
    if not _run_raw(cirFile, ctrl, behavior, timeout,
                    instr_params=instr_params, stimuli=stimuli,
                    savecurrents=savecurrents):
        return None
    return [str(stepped_raw)]


def _get_output_vars(netlist: str) -> list[str]:
    """Parse an NGspice netlist text and return measurable signal names.

    Returns ``v(node)`` for every non-ground node and ``i(Vxxx)`` for every
    independent voltage source.  Used by the GUI to populate the "Select
    variable" dropdown in the Add Instruction dialog.
    """
    # Prefix → number of leading positional node tokens before model/value args
    _N_NODES = {
        'R': 2, 'C': 2, 'L': 2, 'D': 2, 'B': 2, 'V': 2, 'I': 2,
        'Q': 3, 'J': 3, 'Z': 3,
        'M': 4, 'E': 4, 'G': 4,
        'F': 2, 'H': 2, 'T': 4,
    }
    nodes: set[str] = set()
    vsources: list[str] = []

    # Join SPICE continuation lines ('+' prefix)
    lines: list[str] = []
    for raw in netlist.splitlines():
        s = raw.strip()
        if s.startswith('+') and lines:
            lines[-1] += ' ' + s[1:].strip()
        else:
            lines.append(s)

    for line in lines:
        if not line or line.startswith('*') or line.startswith('.'):
            continue
        tokens = line.split()
        if len(tokens) < 2:
            continue
        prefix = tokens[0][0].upper()
        n = _N_NODES.get(prefix, 2)
        for tok in tokens[1: 1 + n]:
            if '=' in tok or tok.startswith('{') or tok.startswith('"'):
                break
            if tok.lower() not in ('0', 'gnd'):
                nodes.add(tok)
        if prefix == 'V':
            vsources.append(tokens[0])

    result = [f"v({nd})" for nd in sorted(nodes, key=lambda x: (x.isdigit(), x.lower()))]
    result += [f"i({v})" for v in vsources]
    return result


#: NGspice's noise mechanisms per device kind, as they appear in the noise
#: plot: ``onoise_<refdes>_<mechanism>``. Verified against ngspice for R and
#: Q; other devices get their total only, and a mechanism can always be typed.
_NOISE_MECHANISMS = {
    'R': ("thermal", "1overf"),
    'Q': ("rb", "rc", "re", "ib", "ic", "1overf"),
}
#: Elements that contribute noise; C, L and the sources do not.
_NOISY_PREFIXES = "RQMDJ"


def _get_noise_vars(netlist: str, contributions: bool = False) -> list[str]:
    """Signal names a NOISE analysis produces, for the GUI's output-variable
    drop-down.

    A noise run does not deliver node voltages or branch currents but spectral
    densities (Anton, 2026-07-31: the drop-down offered ``v(out)`` and
    ``i(v1)``, which a noise result does not have). Always
    ``onoise_spectrum`` and ``inoise_spectrum``; with *contributions* also one
    total per noisy element - ``onoise_r1``, ``onoise_q1`` - and, where NGspice
    splits them, the separate mechanisms.

    :param netlist: NGspice netlist text.
    :type netlist: str

    :param contributions: include the per-source vectors, which NGspice
                          computes only for ``sl.noise(..., contributions=True)``.
    :type contributions: bool

    :return: signal names, totals first.
    :rtype: list
    """
    out = ["onoise_spectrum", "inoise_spectrum"]
    if not contributions:
        return out
    lines: list[str] = []
    for raw in netlist.splitlines():
        s = raw.strip()
        if s.startswith('+') and lines:
            lines[-1] += ' ' + s[1:].strip()
        else:
            lines.append(s)
    for line in lines:
        if not line or line[0] in '*.':
            continue
        refdes = line.split()[0]
        prefix = refdes[0].upper()
        if prefix not in _NOISY_PREFIXES:
            continue
        out.append("onoise_" + refdes.lower())
        for mechanism in _NOISE_MECHANISMS.get(prefix, ()):
            out.append("onoise_{0}_{1}".format(refdes.lower(), mechanism))
    return out


def _get_param_names(netlist: str) -> list[str]:
    """Parse an NGspice netlist text and return the ``.param`` names defined
    in it, in definition order (continuation lines joined).  Used by the GUI
    to populate the parameter dropdowns of the Add Instruction dialog.
    """
    lines: list[str] = []
    for raw in netlist.splitlines():
        s = raw.strip()
        if s.startswith('+') and lines:
            lines[-1] += ' ' + s[1:].strip()
        else:
            lines.append(s)
    names: list[str] = []
    for line in lines:
        if not line.lower().startswith('.param'):
            continue
        body = line[len('.param'):]
        for m in re.finditer(r'([A-Za-z_][A-Za-z_0-9]*)\s*=', body):
            if m.group(1) not in names:
                names.append(m.group(1))
    return names


def make_netlist(filename, title=None, force=False):
    """Generate a program netlist (``.cir``) from a schematic file.

    Calls the ``SLiCAP.schematic.cli`` tool in a subprocess (headless Qt).
    When *force* is False the subprocess is skipped if the ``.cir`` is
    already newer than the schematic and its style sidecar.
    The file extension determines which builder is used:

    - ``.spice_sch`` → NGspice plain netlist (no ``.control`` section)
    - ``.slicap_sch`` → SLiCAP netlist

    :param filename: Schematic filename **with extension**, relative to
                     ``ini.schematic_path`` (e.g. ``"VampQspice.spice_sch"``).
    :type filename: str

    :param title: Circuit title override.  Defaults to the title stored in the
                  schematic or, if empty, to the file stem.
    :type title: str, NoneType

    :returns: ``Path`` to the generated ``.cir`` file, or ``None`` on failure.
    :rtype: pathlib.Path, NoneType
    """
    import sys
    import subprocess

    sch_path = Path(ini.schematic_path) / filename
    if not sch_path.exists():
        print(f"make_netlist: schematic not found: {sch_path}")
        return None

    cir_path = Path(ini.cir_path) / (sch_path.stem + ".cir")

    # Skip the subprocess when the netlist is already current — the .cir is
    # newer than the schematic AND its style sidecar. Opening the NGspice
    # instruction dialog on an unchanged schematic then costs no cold
    # Python+Qt subprocess (Anton, 2026-07-16; mirrors make_schematic).
    if not force:
        try:
            src = sch_path.stat().st_mtime
            sidecar = sch_path.with_suffix(".ini")
            if sidecar.is_file():
                src = max(src, sidecar.stat().st_mtime)
            if cir_path.exists() and cir_path.stat().st_mtime >= src:
                return cir_path
        except OSError:
            pass

    title_args = ["--title", title] if title else []
    result = subprocess.run(
        [sys.executable, "-m", "SLiCAP.schematic.cli", "netlist",
         str(sch_path.resolve())] + title_args,
        capture_output=True, text=True,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),  # no console flash on Windows
    )
    if result.stdout:
        print(result.stdout, end="")
    if result.returncode != 0:
        print(f"make_netlist failed:\n{result.stderr or result.stdout}")
        return None

    return cir_path


def _indep_source_refs(cirFile):
    """Reference designators of the independent sources (V, I) in the program
    netlist ``<cirFile>.cir`` — used to populate ``circuit.indepVars``."""
    try:
        lines = (Path(ini.cir_path) / (cirFile + ".cir")).read_text(
            encoding="utf-8").splitlines()
    except OSError:
        return []
    refs = []
    for raw in lines[1:]:                       # skip the title line
        s = raw.strip()
        if not s or s[0] in "*.":
            continue
        if s[0].upper() in ("V", "I"):
            refs.append(s.split()[0])
    return refs


_PARDEF = re.compile(r'([A-Za-z_][A-Za-z_0-9]*)\s*=\s*(\{[^}]*\}|\S+)')


def _join_continuations(lines):
    """Netlist lines with the SPICE continuations folded in: a line starting
    with '+' continues the previous one.

    The schematic netlister writes a parameter block that way::

        .param
        + C_c={18p}
        + V_S={12}

    so a reader that takes one line at a time sees a ``.param`` with no
    definitions at all.
    """
    joined = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('+') and joined:
            joined[-1] = joined[-1] + ' ' + stripped[1:].strip()
        else:
            joined.append(stripped)
    return joined


def _netlist_par_defs(cirFile, instr_params=None):
    """Circuit parameters AS SIMULATED, as a SLiCAP ``parDefs`` dictionary.

    The ``.param`` definitions of ``<cirFile>.cir`` in file order, with the
    per-instruction ``params=`` overrides applied on top — the same
    precedence NGspice sees in the deck (:func:`_apply_instr_params`).  The
    values are read in SLiCAP notation ('1k', '2*R_a'), BEFORE the NGspice
    translation, so nothing has to be parsed back from '1Meg'.

    A definition in terms of other parameters is resolved with
    :func:`SLiCAP.SLiCAPmath.fullSubs`, so the caller gets numbers wherever
    the circuit is numeric.  A value NGspice can evaluate but SLiCAP cannot
    (``agauss(…)``) is left out rather than guessed.

    A STEPPED parameter keeps its netlist value here; its value per run
    belongs to the step data (``stepList`` / ``stepArray``), which overrides
    this in post-processing.

    :param cirFile: circuit file name without extension.
    :type cirFile: str

    :param instr_params: ordered list of ``(name, value)`` tuples, the
                         ``params=`` argument of the analysis.
    :type instr_params: list, NoneType

    :return: ``{sympy.Symbol: sympy expression or number}``
    :rtype: dict
    """
    import sympy as sp
    from SLiCAP.SLiCAPlex import _replaceScaleFactors
    from SLiCAP.SLiCAPmath import fullSubs

    definitions = {}
    try:
        lines = (Path(ini.cir_path) / (cirFile + ".cir")).read_text(
            encoding="utf-8").splitlines()
    except OSError:
        lines = []
    for line in _join_continuations(lines):
        if not line.lower().startswith('.param'):
            continue
        for name, value in _PARDEF.findall(line[len('.param'):]):
            definitions[name] = value
    for name, value in instr_params or []:
        definitions[str(name)] = str(value)

    par_defs = {}
    for name, text in definitions.items():
        text = str(text).strip()
        if text.startswith('{') and text.endswith('}'):
            text = text[1:-1].strip()
        try:
            par_defs[Symbol(name)] = _sympify(_replaceScaleFactors(text))
        except Exception:
            continue                       # not SLiCAP-evaluable: leave it out
    return {key: fullSubs(value, par_defs)
            for key, value in par_defs.items()}


def _dict_to_instruction(result, cmd, cirFile, x_name, step,
                         step_param, step_vals, source=None, detector=None,
                         params=None):
    """Wrap an NGspice result dict + its settings into a SLiCAP ``instruction``
    object (see SLNG.md).

    The raw dict stays the transport format; this adapter is the single place
    that builds an instruction from it.  ``cmd`` is the ngspice analysis command
    (e.g. ``"op"`` or ``"ac dec 50 1e3 1e8"``): its first token becomes
    ``dataType`` and the rest ``simArgs``.  ``x_name`` is the sweep key
    (``"frequency"``/``"time"``/… or ``None`` for OP).
    """
    from SLiCAP.SLiCAPinstruction import instruction
    from SLiCAP.SLiCAPprotos import circuit as _circuit

    parts    = cmd.split()
    dataType = parts[0].lower()

    instr = instruction()
    instr.gainType = "vi"
    instr.dataType = dataType
    instr.simArgs  = parts[1:]
    instr.simParams = list(params) if params else []
    instr.lgRef    = None
    instr.source   = source
    instr.detector = detector

    result  = dict(result)                      # copy; step keys are popped out
    stepped = step is not None and step_param is not None
    instr.step = bool(stepped)

    if stepped and isinstance(step_param, list):        # array stepping
        run_keys = sorted((k for k in result if re.fullmatch(r"run_\d+", str(k))),
                          key=lambda s: int(s.split("_")[1]))
        instr.stepVars   = list(step_param)
        instr.stepMethod = "array"
        instr.stepArray  = np.array([result.pop(k) for k in run_keys])
    elif stepped:                                       # single-parameter stepping
        instr.stepVar    = step_param
        instr.stepMethod = step.get("method")
        instr.stepStart  = step.get("start")
        instr.stepStop   = step.get("stop")
        instr.stepNum    = step.get("num")
        instr.stepList   = result.pop(step_param,
                                      np.asarray(step_vals, dtype=float))

    cir           = _circuit()
    cir.title     = cirFile
    cir.indepVars = _indep_source_refs(cirFile)
    cir.dep_vars  = [k for k in result if k != x_name]
    # Parameter values as SIMULATED, in the same place the SLiCAP back end
    # keeps them (Anton, 2026-07-29), so post-processing can compute with a
    # circuit parameter without knowing which simulator produced the data.
    cir.parDefs   = _netlist_par_defs(cirFile, params)
    instr.circuit = cir

    setattr(instr, dataType, result)            # instr.op / instr.ac / ...
    instr.executed = True
    return instr


def _no_currents_in(analysis, savecurrents):
    """False, with a message, when device currents are asked for an analysis
    that cannot deliver them.

    The NGspice 42 manual, 15.7.3: savecurrents "is available only for op, dc
    and tran simulation, not for ac", and "cannot be used in AC simulations,
    because complex data are not supported. Vectors thus created will be empty
    after an AC simulation". Measured the same: ``@r1[i]`` comes back
    zero-length and the ``write`` then fails, so the run would end in "NGspice
    produced no raw file" rather than simply lacking the currents.
    """
    if savecurrents:
        print("Note: NGspice cannot write device currents in an {0} plot "
              "(manual 15.7.3: not supported for AC, the vectors come back "
              "empty and break the raw file); savecurrents is ignored "
              "here.".format(analysis))
    return False


def op(cirFile, save=None, step=None, params=None, options=None,
       behavior=None, timeout=None, stimuli=None, savecurrents=False):
    """
    Run an NGspice operating-point (``.op``) analysis.

    Without stepping returns ``{signal_name: float, ...}`` — all scalars.

    With stepping returns ``{"<param>": 1-D array, signal_name: 1-D array, ...}``.

    :param cirFile: Circuit filename without the ``.cir`` extension
                    (file must be in ``ini.cir_path``).
    :type cirFile: str

    :param save: NGspice vectors to write, as NGspice writes them:
                 ``["v(out)", "i(v1)"]``. ``None`` or an empty list saves the
                 default set - node voltages (including subcircuit nodes such
                 as ``v(x1.mid)``) and voltage-source branch currents.
                 A non-empty list saves ONLY what it lists (manual 15.6.1:
                 "If .SAVE lines are given, only those vectors specified are
                 saved"), so to add an internal device parameter to
                 everything else, list ``all`` with it:
                 ``save=["all", "@q1[gm]"]``.
                 Python names for these vectors are chosen afterwards, in
                 ``sl.make_traces(..., names={...})`` - the analysis call
                 speaks NGspice only.
    :type save: list, NoneType

    :param savecurrents: True adds ``.options savecurrents`` to the deck, so
                         the terminal currents of M, J, Q, D, R, C, L, B, F,
                         G, W, S and I devices are written as well, inside
                         subcircuits too (``i(@r3[i])``,
                         ``i(@r.x1.r1[i])`` - NGspice writes them with that
                         ``i(...)`` wrapper). Manual 15.7.3: op, dc and tran
                         only, NOT ac; and for MOS devices only a subset of
                         the current parameters unless the model-specific
                         options are used.
    :type savecurrents: bool

    :param step: Parameter step dict::

                     {"param": "R1", "method": "lin",
                      "start": 100, "stop": 1000, "num": 11}

                 ``"method"`` may be ``"lin"``, ``"log"``, or ``"list"``
                 (use ``"values": [...]`` instead of start/stop/num for list).
    :type step: dict, NoneType

    :param params: Per-instruction parameter definitions: **ordered** list of
                   ``(name, value)`` tuples.  A name already defined in the
                   netlist gets its value replaced in place (overriding the
                   schematic value for this run only); a new name is appended
                   as a ``.param`` line in list order.  Order the entries so
                   that every parameter is numerically evaluable in a
                   non-recursive way, e.g.
                   ``[("R", "1k"), ("C", "1n"), ("tau", "{1/(R*C)}")]``.
    :type params: list, NoneType

    :param options: NGspice ``.options`` key-value pairs, e.g. ``{"RELTOL": 1e-5}``.
    :type options: dict, NoneType

    :param behavior: NGspice compatibility mode (e.g. ``"ltpsa"``).
                     ``None`` = not set.
    :type behavior: str, NoneType

    :param timeout: Simulation time limit in seconds.  ``None`` = no limit.
    :type timeout: float, NoneType

    :return: Result dictionary.
    :rtype: dict
    """
    if ini.ngspice == "":
        print("NGspice not configured.")
        return {}
    _ensure_netlist(cirFile)
    step_param, step_vals = _step_values(step)
    # The op raw gets its OWN file name so operating-point data survives
    # later ac/tran/... runs of the same circuit (which overwrite
    # <cirFile>.raw) — the schematic back-annotation reads it after a run.
    raw_path = ini.cir_path + cirFile + '_op.raw'
    # Device operating-point params (e.g. @q1[gm]) need an explicit save directive.
    extra_saves = list(save or [])
    raw_paths = _run_stepped(cirFile, "op", raw_path, step_param, step_vals,
                             options=options, extra_saves=extra_saves or None,
                             behavior=behavior, timeout=timeout,
                             instr_params=params, stimuli=stimuli,
                             savecurrents=savecurrents)
    if raw_paths is None:
        return {}
    raw_arg = raw_paths if len(raw_paths) > 1 else raw_paths[0]
    try:
        result = NGspiceRaw2dict(raw_arg, step_param, step_vals)
    except FileNotFoundError:
        print(f"ERROR: NGspice produced no raw file ({raw_path}).")
        return {}
    step_key = ({f"run_{i + 1}" for i in range(len(step_vals))}
                if isinstance(step_param, list)
                else (step_param if step_param else None))
    return _dict_to_instruction(result, "op", cirFile, None, step,
                                step_param, step_vals, params=params)


def dc(cirFile, source, start, stop, incr, save=None,
       step=None, params=None, options=None, behavior=None, timeout=None,
       stimuli=None, savecurrents=False):
    """
    Run an NGspice DC sweep analysis.

    :param cirFile: Circuit filename without the ``.cir`` extension.
    :type cirFile: str

    :param source: Source name to sweep (e.g. ``"V1"``), or ``"TEMP"`` for a
                   temperature sweep.
    :type source: str

    :param start: Sweep start value.
    :type start: float, int

    :param stop: Sweep stop value.
    :type stop: float, int

    :param incr: Sweep increment.
    :type incr: float, int

    :param names: ``{user_key: ngspice_expr}``.  ``None`` returns all signals.
    :type names: dict, NoneType

    :param step: Parameter step dict (see :func:`op`).
    :type step: dict, NoneType

    :param params: Per-instruction parameter definitions — ordered list of
                   ``(name, value)`` tuples (see :func:`op`).
    :type params: list, NoneType

    :param options: NGspice ``.options`` dict.
    :type options: dict, NoneType

    :param behavior: NGspice compatibility mode.
    :type behavior: str, NoneType

    :param timeout: Simulation time limit in seconds.
    :type timeout: float, NoneType

    :return: Result dictionary with sweep variable and signal arrays.
    :rtype: dict
    """
    if ini.ngspice == "":
        print("NGspice not configured.")
        return {}
    _ensure_netlist(cirFile)
    cmd = (f"dc {source} {_deck_number(start, 'start')} "
           f"{_deck_number(stop, 'stop')} "
           f"{_deck_number(incr, 'incr')}")
    step_param, step_vals = _step_values(step)
    raw_path = ini.cir_path + cirFile + '.raw'
    raw_paths = _run_stepped(cirFile, cmd, raw_path, step_param, step_vals,
                             options=options, behavior=behavior, timeout=timeout,
                             instr_params=params, stimuli=stimuli,
                             extra_saves=list(save or []),
                             savecurrents=savecurrents)
    if raw_paths is None:
        return {}
    raw_arg = raw_paths if len(raw_paths) > 1 else raw_paths[0]
    try:
        result = NGspiceRaw2dict(raw_arg, step_param, step_vals)
    except FileNotFoundError:
        print(f"ERROR: NGspice produced no raw file ({raw_path}).")
        return {}
    step_key = ({f"run_{i + 1}" for i in range(len(step_vals))}
                if isinstance(step_param, list)
                else (step_param if step_param else None))
    x_name   = next(iter(result)) if result else None
    return _dict_to_instruction(result, cmd, cirFile, x_name, step,
                                step_param, step_vals, params=params)


def ac(cirFile, method, n, fstart, fstop, save=None,
       step=None, params=None, options=None, behavior=None, timeout=None,
       stimuli=None, savecurrents=False):
    """
    Run an NGspice AC sweep analysis.

    Signal arrays in the result dict are ``dtype=complex128``.  Use
    :func:`~SLiCAP.SLiCAPmath.mag`, :func:`~SLiCAP.SLiCAPmath.dB`,
    :func:`~SLiCAP.SLiCAPmath.phase`, and :func:`~SLiCAP.SLiCAPmath.delay`
    for post-processing.

    :param cirFile: Circuit filename without the ``.cir`` extension.
    :type cirFile: str

    :param method: Frequency sweep type: ``"dec"`` (per decade),
                   ``"oct"`` (per octave), or ``"lin"`` (linear).
    :type method: str

    :param n: Points per decade / octave, or total points for ``"lin"``.
    :type n: int

    :param fstart: Start frequency [Hz].
    :type fstart: float, int

    :param fstop: Stop frequency [Hz].
    :type fstop: float, int

    :param names: ``{user_key: ngspice_expr}``.  ``None`` returns all signals.
    :type names: dict, NoneType

    :param step: Parameter step dict (see :func:`op`).
    :type step: dict, NoneType

    :param params: Per-instruction parameter definitions — ordered list of
                   ``(name, value)`` tuples (see :func:`op`).
    :type params: list, NoneType

    :param options: NGspice ``.options`` dict.
    :type options: dict, NoneType

    :param behavior: NGspice compatibility mode.
    :type behavior: str, NoneType

    :param timeout: Simulation time limit in seconds.
    :type timeout: float, NoneType

    :return: Result dictionary; ``"frequency"`` key holds the 1-D frequency array.
    :rtype: dict
    """
    if ini.ngspice == "":
        print("NGspice not configured.")
        return {}
    _ensure_netlist(cirFile)
    cmd = (f"ac {method} {_deck_number(n, 'n')} "
           f"{_deck_number(fstart, 'fstart')} "
           f"{_deck_number(fstop, 'fstop')}")
    step_param, step_vals = _step_values(step)
    savecurrents = _no_currents_in("AC", savecurrents)
    raw_path = ini.cir_path + cirFile + '.raw'
    raw_paths = _run_stepped(cirFile, cmd, raw_path, step_param, step_vals,
                             options=options, behavior=behavior, timeout=timeout,
                             instr_params=params, stimuli=stimuli,
                             extra_saves=list(save or []),
                             savecurrents=savecurrents)
    if raw_paths is None:
        return {}
    raw_arg = raw_paths if len(raw_paths) > 1 else raw_paths[0]
    try:
        result = NGspiceRaw2dict(raw_arg, step_param, step_vals)
    except FileNotFoundError:
        print(f"ERROR: NGspice produced no raw file ({raw_path}).")
        return {}
    step_key = ({f"run_{i + 1}" for i in range(len(step_vals))}
                if isinstance(step_param, list)
                else (step_param if step_param else None))
    return _dict_to_instruction(result, cmd, cirFile, "frequency", step,
                                step_param, step_vals, params=params)


def _ensure_netlist(cirFile):
    """Regenerate ``cir/<cirFile>.cir`` from the saved schematic when the
    schematic file is NEWER — the sims run the .cir as-is, and without this
    a stimulus edited in the GUI after the last netlist export would
    silently not reach the simulation (Anton, 2026-07-12). No-op when no
    schematic exists (hand-written netlists) or the .cir is up to date."""
    cir = Path(ini.cir_path) / (cirFile + ".cir")
    for ext in (".spice_sch", ".slicap_sch"):
        sch = Path(ini.schematic_path) / (cirFile + ext)
        if sch.is_file():
            if not cir.is_file() or sch.stat().st_mtime > cir.stat().st_mtime:
                make_netlist(cirFile + ext)
            return


def _fourier_post_args(fourier):
    """Normalize the ``fourier=`` argument: value or {"freq":…, "nfreqs":…}
    → (freq_text, nfreqs)."""
    if isinstance(fourier, dict):
        freq = fourier.get("freq")
        nfreqs = int(fourier.get("nfreqs", 10))
    else:
        freq, nfreqs = fourier, 10
    return _deck_number(freq, "fourier frequency"), nfreqs


def _parse_fourier_log(txt_path):
    """Parse NGspice ``fourier`` output (the batch-mode ``-o`` log file)
    into a result dict.

    Per analysed vector the table columns become arrays; THD becomes a
    scalar. The harmonic/frequency columns are identical for every vector
    (same fundamental) and are stored once::

        {"harmonic": arr, "frequency": arr,
         "mag(V_out)": arr, "phase(V_out)": arr,
         "norm_mag(V_out)": arr, "norm_phase(V_out)": arr,
         "thd(V_out)": float, ...}
    """
    import re as _re
    try:
        text = Path(txt_path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {}
    out = {}
    table_parts = []
    blocks = _re.split(r"Fourier analysis for\s+", text)[1:]
    for block in blocks:
        lines = block.splitlines()
        name = lines[0].rstrip(": \t")
        thd = None
        m = _re.search(r"THD:\s*([0-9.eE+-]+)\s*%", block)
        if m:
            thd = float(m.group(1))
        rows = []
        last_row_line = 0
        for i, line in enumerate(lines):
            f = line.split()
            if len(f) >= 6:
                try:
                    rows.append([float(v) for v in f[:6]])
                    last_row_line = i
                except ValueError:
                    continue
        if not rows:
            continue
        # Verbatim table text (header through the last numeric row) — for
        # human reading, report pasting and the design-data viewer
        # (Anton, 2026-07-12); the arrays below are the machine access.
        table_parts.append("Fourier analysis for "
                           + "\n".join(lines[:last_row_line + 1]).rstrip())
        cols = np.array(rows).T
        out.setdefault("harmonic", cols[0])
        out.setdefault("frequency", cols[1])
        out[f"mag({name})"] = cols[2]
        out[f"phase({name})"] = cols[3]
        out[f"norm_mag({name})"] = cols[4]
        out[f"norm_phase({name})"] = cols[5]
        if thd is not None:
            out[f"thd({name})"] = thd
    if table_parts:
        out["table"] = "\n\n".join(table_parts)
    return out


def tran(cirFile, tstep, tstop, tstart=0, save=None,
         step=None, params=None, options=None, behavior=None, timeout=None,
         fourier=None, fft=None, stimuli=None, savecurrents=False):
    """
    Run an NGspice transient analysis, optionally with Fourier/FFT
    post-processing (the legacy ``ngspice2traces`` ``postProc`` semantics,
    structured).

    ``fourier=<fundamental>`` (SLiCAP notation, e.g. ``"100k"``, or
    ``{"freq": "100k", "nfreqs": 10}``) runs NGspice ``fourier`` after the
    transient: the returned instruction still holds the TIME traces
    (``dataType 'tran'``), and the harmonics table (magnitude/phase/
    normalized per harmonic + THD per signal) is attached as the
    ``instr.fourier`` dict.

    ``fft=True`` (or ``{"window": "hanning", "order": 8}`` — NGspice
    ``specwindow``/``specwindoworder``) linearizes the transient and takes
    its FFT: the returned instruction is FREQUENCY-domain (``dataType
    'fft'``, complex arrays + ``"frequency"``), plotting like an ``ac``
    result.

    Both post-processing options REQUIRE ``names`` (the analysed vectors
    are created with ``let`` from the names entries, so derived
    expressions like ``"v(1)-v(2)"`` work).

    :param cirFile: Circuit filename without the ``.cir`` extension.
    :type cirFile: str

    :param tstep: Suggested internal time step.
    :type tstep: float, int

    :param tstop: End time.
    :type tstop: float, int

    :param tstart: Start time (default 0); data before this time is discarded.
    :type tstart: float, int

    :param names: ``{user_key: ngspice_expr}``.  ``None`` returns all signals.
    :type names: dict, NoneType

    :param step: Parameter step dict (see :func:`op`).
    :type step: dict, NoneType

    :param params: Per-instruction parameter definitions — ordered list of
                   ``(name, value)`` tuples (see :func:`op`).
    :type params: list, NoneType

    :param options: NGspice ``.options`` dict.
    :type options: dict, NoneType

    :param behavior: NGspice compatibility mode.
    :type behavior: str, NoneType

    :param timeout: Simulation time limit in seconds.
    :type timeout: float, NoneType

    :return: Result dictionary; ``"time"`` key holds the 1-D time array.
    :rtype: dict
    """
    if ini.ngspice == "":
        print("NGspice not configured.")
        return {}
    _ensure_netlist(cirFile)
    cmd = (f"tran {_deck_number(tstep, 'tstep')} "
           f"{_deck_number(tstop, 'tstop')} "
           f"{_deck_number(tstart, 'tstart')}")
    step_param, step_vals = _step_values(step)

    # Post-processing control lines. ``let`` creates the analysed vectors
    # under the USER keys, so derived expressions work; after ``fft`` the
    # spectrum is the current plot and the raw write stores the SPECTRUM.
    post_lines = []
    if step_param is not None and not fft:
        # Stepped transient runs have ADAPTIVE time steps: each step would
        # produce a different number of points and the (n_steps, n_sweep)
        # stack fails (Anton, 2026-07-12 — the sine stimulus exposed it).
        # linearize interpolates every run onto the common tstep grid.
        post_lines.append("linearize")
    # fourier / fft transform the vectors the run SAVES, named as NGspice
    # names them (Anton, 2026-08-01: the analysis call speaks NGspice; the
    # Python names are chosen later, in make_traces). Without a save list
    # there is nothing to name, so the analysed vectors must be listed.
    analysed = list(save or [])
    if (fourier is not None or fft) and not analysed:
        print("ERROR: fourier= / fft= needs save=[...] naming the vectors to "
              "transform, e.g. save=[\"v(out)\"].")
        return {}
    if fourier is not None:
        if step_param is not None:
            print("ERROR: fourier= is not supported for stepped runs "
                  "(use fft= or run per step value).")
            return {}
        freq_text, nfreqs = _fourier_post_args(fourier)
        post_lines.append(f"set nfreqs={nfreqs}")
        post_lines.append(f"fourier {freq_text} " + " ".join(analysed))
    if fft:
        window = "hanning"
        order = None
        if isinstance(fft, dict):
            window = fft.get("window", window)
            order = fft.get("order")
        post_lines.append("linearize")
        post_lines.append(f"set specwindow={window}")
        if order is not None:
            post_lines.append(f"set specwindoworder={int(order)}")
        post_lines.append("fft " + " ".join(analysed))

    raw_path = ini.cir_path + cirFile + '.raw'
    raw_paths = _run_stepped(cirFile, cmd, raw_path, step_param, step_vals,
                             options=options, behavior=behavior, timeout=timeout,
                             instr_params=params, post_lines=post_lines or None, stimuli=stimuli,
                             extra_saves=list(save or []),
                             savecurrents=savecurrents)
    if raw_paths is None:
        return {}
    raw_arg = raw_paths if len(raw_paths) > 1 else raw_paths[0]
    try:
        result = NGspiceRaw2dict(raw_arg, step_param, step_vals)
    except FileNotFoundError:
        print(f"ERROR: NGspice produced no raw file ({raw_path}).")
        return {}
    step_key = ({f"run_{i + 1}" for i in range(len(step_vals))}
                if isinstance(step_param, list)
                else (step_param if step_param else None))
    x_name = "frequency" if fft else "time"
    if fft:
        # Frequency-domain result: its own dataType; simArgs keep the tran
        # provenance.
        instr = _dict_to_instruction(result,
                                     f"fft {_deck_number(tstep, 'tstep')}"
                                     f" {_deck_number(tstop, 'tstop')}"
                                     f" {_deck_number(tstart, 'tstart')}",
                                     cirFile, "frequency", step,
                                     step_param, step_vals, params=params)
        if fourier is not None:
            instr.fourier = _parse_fourier_log(_sim_files(cirFile)[1])
        return instr
    instr = _dict_to_instruction(result, cmd, cirFile, "time", step,
                                step_param, step_vals, params=params)
    if fourier is not None:
        # Harmonics table from the run's log, attached alongside the
        # time-domain result (one run: waveform for plotting, table for
        # the design-data panel / report snippets).
        instr.fourier = _parse_fourier_log(_sim_files(cirFile)[1])
    return instr


def noise(cirFile, output, input_src, method, n, fstart, fstop, save=None,
          step=None, params=None, options=None, behavior=None, timeout=None,
          stimuli=None, contributions=False, savecurrents=False):
    """
    Run an NGspice noise analysis.  Results stored as V²/Hz PSD
    (``set sqrnoise`` is always active).

    Use ``dB(np.sqrt(result["S_u"]))`` or ``dB(result["S_u"], power=True)``
    for a dB spectral density plot.

    :param cirFile: Circuit filename without the ``.cir`` extension.
    :type cirFile: str

    :param output: Output node expression, e.g. ``"V(out)"``.
    :type output: str

    :param input_src: Input noise source name, e.g. ``"V1"``.
    :type input_src: str

    :param method: Frequency sweep type: ``"dec"``, ``"oct"``, or ``"lin"``.
    :type method: str

    :param n: Points per decade / octave, or total points for ``"lin"``.
    :type n: int

    :param fstart: Start frequency [Hz].
    :type fstart: float, int

    :param fstop: Stop frequency [Hz].
    :type fstop: float, int

    :param names: ``{user_key: ngspice_expr}``.  ``None`` returns all signals.
                  Typical: ``{"S_u": "onoise_spectrum"}``.
    :type names: dict, NoneType

    :param step: Parameter step dict (see :func:`op`).
    :type step: dict, NoneType

    :param params: Per-instruction parameter definitions — ordered list of
                   ``(name, value)`` tuples (see :func:`op`).
    :type params: list, NoneType

    :param options: NGspice ``.options`` dict.
    :type options: dict, NoneType

    :param behavior: NGspice compatibility mode.
    :type behavior: str, NoneType

    :param timeout: Simulation time limit in seconds.
    :type timeout: float, NoneType

    :return: Result dictionary; ``"frequency"`` key holds the 1-D frequency array.
             Noise signal arrays are real (V²/Hz).
    :rtype: dict
    """
    if ini.ngspice == "":
        print("NGspice not configured.")
        return {}
    _ensure_netlist(cirFile)
    cmd = (f"noise {output} {input_src} {method} {n} "
           f"{_deck_number(fstart, 'fstart')} "
           f"{_deck_number(fstop, 'fstop')}")
    if contributions:
        # the summary interval: its VALUE only spaces NGspice's printed
        # summaries, but giving it at all is what makes NGspice compute the
        # per-source vectors, which is what we are after
        cmd += " 1"
    step_param, step_vals = _step_values(step)
    savecurrents = _no_currents_in("noise", savecurrents)
    raw_path = ini.cir_path + cirFile + '.raw'
    raw_paths = _run_stepped(cirFile, cmd, raw_path, step_param, step_vals,
                             options=options, noise=True, behavior=behavior,
                             timeout=timeout, instr_params=params, stimuli=stimuli,
                                savecurrents=savecurrents,
                             extra_saves=list(save or []))
    if raw_paths is None:
        return {}
    raw_arg = raw_paths if len(raw_paths) > 1 else raw_paths[0]
    try:
        result = NGspiceRaw2dict(raw_arg, step_param, step_vals)
    except FileNotFoundError:
        print(f"ERROR: NGspice produced no raw file ({raw_path}).")
        return {}
    step_key = ({f"run_{i + 1}" for i in range(len(step_vals))}
                if isinstance(step_param, list)
                else (step_param if step_param else None))
    return _dict_to_instruction(result, cmd, cirFile, "frequency", step,
                                step_param, step_vals,
                                source=input_src, detector=output,
                                params=params)


def ngspice_control(cirFile, control, params=None, stimuli=None,
                    behavior=None, timeout=None):
    """
    Run NGspice with a USER-SUPPLIED control section — full-control / raw
    mode.

    *control* is inserted VERBATIM as the ``.control … .endc`` block,
    replacing SLiCAP's auto-generated control. You are driving NGspice
    directly: SLiCAP does **not** parse a result object and shows nothing in
    the design-data panel. Read any output yourself, e.g. with
    :func:`NGspiceRaw2dict` on a raw file your control writes. The
    schematic-derived netlist (components, models, ``params`` and ``stimuli``
    overrides) is still SLiCAP's; only the control block is yours.

    :param cirFile: Circuit filename without the ``.cir`` extension.
    :type cirFile: str

    :param control: Path to a control-section text file, or the control text
                    itself. Text without ``.control`` is wrapped in
                    ``.control … .endc`` automatically.
    :type control: str

    :param params: Per-instruction parameter definitions — ordered list of
                   ``(name, value)`` tuples (see :func:`op`).
    :type params: list, NoneType

    :param stimuli: Per-run source stimuli ``{refdes: [type, arg1, …]}``
                    (see :func:`op`).
    :type stimuli: dict, NoneType

    :param behavior: NGspice compatibility mode. ``None`` = not set.
    :type behavior: str, NoneType

    :param timeout: Simulation time limit in seconds. ``None`` = no limit.
    :type timeout: float, NoneType

    :return: ``True`` on a successful NGspice run, else ``False``.
    :rtype: bool
    """
    if ini.ngspice == "":
        print("NGspice not configured.")
        return False
    _ensure_netlist(cirFile)
    text = str(control)
    try:
        if Path(text).is_file():
            text = Path(text).read_text(encoding="utf-8")
    except OSError:
        pass                                    # long/multi-line = inline text
    if ".control" not in text.lower():
        text = ".control\n" + text.strip() + "\n.endc"
    ok = _run_raw(cirFile, text, behavior, timeout,
                  instr_params=params, stimuli=stimuli)
    if not ok:
        print("NGspice control-section run failed.")
    return ok


# =============================================================================
# HDF5 storage — save / load / delete
# =============================================================================

def save(filepath, **kwargs):
    """
    Save one or more result dicts to an HDF5 file.

    Each keyword argument becomes a top-level group named after the argument.
    If the group already exists it is silently overwritten.  The file is created
    if it does not exist; other existing groups are left untouched.

    Supported value types inside a result dict:

    - ``numpy.ndarray`` (any shape, real or complex) → HDF5 dataset.
    - ``float`` / ``int`` (OP scalar) → 0-D HDF5 dataset.

    :param filepath: Path to the HDF5 file (``*.h5``).
    :type filepath: str, pathlib.Path

    :param kwargs: Result dicts to store, e.g.
                   ``save("r.h5", AC1=ac_result, TRAN1=tran_result)``.
    :type kwargs: dict

    :raises TypeError: If a value in kwargs is not a dict.
    :raises ImportError: If h5py is not installed.

    Example::

        sim.save("results.h5", AC1=AC1, NOISE1=NOISE1)
    """
    try:
        import h5py
    except ImportError:
        raise ImportError("h5py is required for save/load/delete. "
                          "Install it with: pip install h5py")
    with h5py.File(filepath, 'a') as hf:
        for key, result in kwargs.items():
            if not isinstance(result, dict):
                raise TypeError(
                    f"save() expects dict values; "
                    f"got {type(result).__name__!r} for key {key!r}")
            if key in hf:
                del hf[key]
            grp = hf.create_group(key)
            for name, val in result.items():
                if isinstance(val, np.ndarray):
                    grp.create_dataset(name, data=val)
                else:
                    grp.create_dataset(name, data=float(val))


def load(filepath, key):
    """
    Load one result dict from an HDF5 file.

    :param filepath: Path to the HDF5 file.
    :type filepath: str, pathlib.Path

    :param key: Group name to load (the kwarg name used in :func:`save`).
    :type key: str

    :return: Result dictionary — numpy arrays for signals and sweep variables,
             Python floats for OP scalars (0-D datasets).
    :rtype: dict

    :raises KeyError: If *key* is not present in the file.
    :raises ImportError: If h5py is not installed.

    Example::

        AC1 = sim.load("results.h5", "AC1")
    """
    try:
        import h5py
    except ImportError:
        raise ImportError("h5py is required for save/load/delete. "
                          "Install it with: pip install h5py")
    with h5py.File(filepath, 'r') as hf:
        if key not in hf:
            raise KeyError(f"{key!r} not found in {filepath!r}. "
                           f"Available: {list(hf.keys())}")
        grp = hf[key]
        result = {}
        for name, ds in grp.items():
            arr = ds[()]
            result[name] = float(arr) if arr.shape == () else arr
    return result


def delete(filepath, key):
    """
    Remove one result group from an HDF5 file.

    :param filepath: Path to the HDF5 file.
    :type filepath: str, pathlib.Path

    :param key: Group name to remove.
    :type key: str

    :raises KeyError: If *key* is not present in the file.
    :raises ImportError: If h5py is not installed.

    Example::

        sim.delete("results.h5", "AC1")
    """
    try:
        import h5py
    except ImportError:
        raise ImportError("h5py is required for save/load/delete. "
                          "Install it with: pip install h5py")
    with h5py.File(filepath, 'a') as hf:
        if key not in hf:
            raise KeyError(f"{key!r} not found in {filepath!r}. "
                           f"Available: {list(hf.keys())}")
        del hf[key]


# =============================================================================
# Matplotlib plotting helpers
# =============================================================================

def _ensure_2d(arr):
    """Return *arr* as (n_traces, n_points); 1-D input gets a leading axis."""
    a = np.asarray(arr)
    return a[np.newaxis, :] if a.ndim == 1 else a


def bode(title, freq, mag_dB, phase_deg, labels=None, filename=None):
    """
    Create a two-subplot Bode plot: magnitude [dB] on top, phase [°] below,
    both on a shared logarithmic frequency axis.

    *mag_dB* and *phase_deg* may be 1-D (single trace) or 2-D
    (shape ``(n_traces, n_freq)`` for stepped results).  Use
    :func:`~SLiCAP.SLiCAPmath.dB` and :func:`~SLiCAP.SLiCAPmath.phase`
    to compute these from a complex AC result.

    :param title: Figure title.
    :type title: str

    :param freq: Frequency array [Hz], 1-D.
    :type freq: numpy.ndarray

    :param mag_dB: Magnitude in dB — 1-D or 2-D.
    :type mag_dB: numpy.ndarray

    :param phase_deg: Phase in degrees — same shape as *mag_dB*.
    :type phase_deg: numpy.ndarray

    :param labels: Legend strings, one per trace.  ``None`` → no legend.
    :type labels: list, NoneType

    :param filename: Save the figure to this path (SVG / PDF / PNG …) and
                     close it.  ``None`` → figure returned open for
                     interactive display or further customisation.
    :type filename: str, NoneType

    :return: The matplotlib Figure object.
    :rtype: matplotlib.figure.Figure

    Example::

        gain_dB   = dB(AC1["V_out"] / AC1["V_in"])
        phase_deg = phase(AC1["V_out"] / AC1["V_in"])
        labels    = [f"R1 = {v:.0f} Ω" for v in AC1["step_R1"]]
        sim.bode("Gain and phase", AC1["frequency"], gain_dB, phase_deg,
                 labels=labels, filename="bode.svg")
    """
    import matplotlib.pyplot as plt
    import matplotlib.ticker as ticker

    fig, (ax_m, ax_p) = plt.subplots(2, 1, sharex=True, figsize=(8, 6))
    fig.suptitle(title)

    freq  = np.asarray(freq, dtype=float)
    mag2d = _ensure_2d(np.real(mag_dB))
    ph2d  = _ensure_2d(np.real(phase_deg))

    for i, (m_row, p_row) in enumerate(zip(mag2d, ph2d)):
        lbl = labels[i] if labels and i < len(labels) else None
        ax_m.semilogx(freq, m_row, label=lbl)
        ax_p.semilogx(freq, p_row, label=lbl)

    ax_m.set_ylabel("Magnitude (dB)")
    ax_p.set_ylabel("Phase (°)")
    ax_p.set_xlabel("Frequency (Hz)")
    ax_p.xaxis.set_major_formatter(ticker.EngFormatter(unit="Hz"))
    ax_m.grid(True, which="both", linestyle=":")
    ax_p.grid(True, which="both", linestyle=":")
    if labels:
        ax_m.legend(fontsize="small")

    fig.tight_layout()
    if filename:
        fig.savefig(filename)
        plt.close(fig)
    return fig


def plot_noise(title, freq, S_u, S_w=None, rms_u=None, rms_w=None,
               labels=None, filename=None):
    """
    Plot noise amplitude spectral density (V/√Hz) on a log-log scale.

    *S_u* and *S_w* are **power** spectral densities [V²/Hz] — the function
    converts them to amplitude spectral density [V/√Hz] by taking the square
    root.  Weighted curves are drawn as dashed lines.

    :param title: Figure title.
    :type title: str

    :param freq: Frequency array [Hz], 1-D.
    :type freq: numpy.ndarray

    :param S_u: Unweighted noise PSD [V²/Hz] — 1-D or 2-D.
    :type S_u: numpy.ndarray

    :param S_w: Weighted noise PSD [V²/Hz], same shape as *S_u*.
                ``None`` → not plotted.
    :type S_w: numpy.ndarray, NoneType

    :param rms_u: Unweighted RMS noise [V] — shown as a text annotation.
    :type rms_u: float, NoneType

    :param rms_w: Weighted RMS noise [V] — shown as a text annotation.
    :type rms_w: float, NoneType

    :param labels: Legend strings, one per trace.  ``None`` → auto-labels
                   (``"unweighted"`` / ``"weighted"`` when *S_w* is given).
    :type labels: list, NoneType

    :param filename: Save path.  ``None`` → figure returned open.
    :type filename: str, NoneType

    :return: The matplotlib Figure object.
    :rtype: matplotlib.figure.Figure

    Example::

        wf = noiseWeighting({"din_a": {}})
        rms_u, rms_w, S_w = weightedRMS(NOISE1["S_u"], NOISE1["frequency"], wf)
        sim.plot_noise("Output noise", NOISE1["frequency"], NOISE1["S_u"],
                       S_w=S_w, rms_u=rms_u, rms_w=rms_w)
    """
    import matplotlib.pyplot as plt
    import matplotlib.ticker as ticker

    fig, ax = plt.subplots(figsize=(8, 5))
    fig.suptitle(title)

    freq  = np.asarray(freq, dtype=float)
    su2d  = _ensure_2d(np.real(S_u))
    n_traces = su2d.shape[0]

    for i, row in enumerate(su2d):
        if labels and i < len(labels):
            lbl = labels[i]
        else:
            lbl = "unweighted" if S_w is not None else None
        ax.loglog(freq, np.sqrt(np.abs(row)), label=lbl)

    if S_w is not None:
        sw2d = _ensure_2d(np.real(S_w))
        for i, row in enumerate(sw2d):
            if labels and i < len(labels):
                lbl = labels[i] + " (weighted)"
            else:
                lbl = "weighted"
            ax.loglog(freq, np.sqrt(np.abs(row)), linestyle="--", label=lbl)

    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("Noise ASD (V/√Hz)")
    ax.xaxis.set_major_formatter(ticker.EngFormatter(unit="Hz"))
    ax.grid(True, which="both", linestyle=":")

    annots = []
    if rms_u is not None:
        annots.append(f"RMS unweighted = {rms_u:.3g} V")
    if rms_w is not None:
        annots.append(f"RMS weighted   = {rms_w:.3g} V")
    if annots:
        ax.text(0.02, 0.02, "\n".join(annots),
                transform=ax.transAxes, fontsize="small",
                verticalalignment="bottom",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.7))

    if S_w is not None or labels:
        ax.legend(fontsize="small")

    fig.tight_layout()
    if filename:
        fig.savefig(filename)
        plt.close(fig)
    return fig


def plot(title, x, y, xlabel="", ylabel="", labels=None,
         logx=False, logy=False, filename=None):
    """
    Generic x-y plot with optional log scales on either axis.

    *y* may be 1-D (single trace) or 2-D (shape ``(n_traces, n_points)``
    for stepped results).

    :param title: Figure title.
    :type title: str

    :param x: X-axis data, 1-D.
    :type x: numpy.ndarray

    :param y: Y-axis data — 1-D or 2-D.
    :type y: numpy.ndarray

    :param xlabel: X-axis label string.
    :type xlabel: str

    :param ylabel: Y-axis label string.
    :type ylabel: str

    :param labels: Legend strings, one per trace.  ``None`` → no legend.
    :type labels: list, NoneType

    :param logx: Use a logarithmic x-axis (default ``False``).
    :type logx: bool

    :param logy: Use a logarithmic y-axis (default ``False``).
    :type logy: bool

    :param filename: Save path.  ``None`` → figure returned open.
    :type filename: str, NoneType

    :return: The matplotlib Figure object.
    :rtype: matplotlib.figure.Figure

    Example::

        # DC sweep — V(out) vs. V1 for several R1 values
        labels = [f"R1 = {v:.0f} Ω" for v in DC1["step_R1"]]
        sim.plot("DC transfer", DC1["v-sweep"], DC1["V_out"],
                 xlabel="V1 (V)", ylabel="V(out) (V)", labels=labels)
    """
    import matplotlib.pyplot as plt
    import matplotlib.ticker as ticker

    fig, ax = plt.subplots(figsize=(8, 5))
    fig.suptitle(title)

    x   = np.asarray(x, dtype=float)
    y2d = _ensure_2d(np.real(y))

    if logx and logy:
        plot_fn = ax.loglog
    elif logx:
        plot_fn = ax.semilogx
    elif logy:
        plot_fn = ax.semilogy
    else:
        plot_fn = ax.plot

    for i, y_row in enumerate(y2d):
        lbl = labels[i] if labels and i < len(labels) else None
        plot_fn(x, y_row, label=lbl)

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    if logx:
        ax.xaxis.set_major_formatter(ticker.EngFormatter())
    ax.grid(True, which=("both" if (logx or logy) else "major"), linestyle=":")
    if labels:
        ax.legend(fontsize="small")

    fig.tight_layout()
    if filename:
        fig.savefig(filename)
        plt.close(fig)
    return fig


def show():
    """Display all open matplotlib figures.

    Calls ``matplotlib.pyplot.show()``.  In a script this blocks until all
    figure windows are closed; in a Jupyter notebook it renders inline.
    """
    import matplotlib.pyplot as plt
    plt.show()


def instr2dataset(instr, x_key=None, y_keys=None):
    """Convert an NGspice result *instruction* into a
    :class:`~SLiCAP.SLiCAPtraces.dataset`.

    This is the NGspice PRODUCER ADAPTER: it states the provenance of the
    numbers - which key is the sweep variable, which columns are step
    parameters - and hands them to the backend-neutral post-processing layer
    It is registered with
    :func:`~SLiCAP.SLiCAPtraces.register_dataset_adapter`, so
    :func:`~SLiCAP.SLiCAPtraces.make_traces` also accepts the result object
    itself.

    :param instr: instruction returned by an NGspice analysis function.
    :type instr: SLiCAPinstruction.instruction

    :param x_key: sweep variable; None auto-derives it (the sweep variable
                  for AC/TRAN/DC/NOISE, the step variable for a stepped OP).
    :type x_key: str, NoneType

    :param y_keys: signals to keep; None keeps the dependent variables.
    :type y_keys: list, NoneType

    :return: dataset, or None when the result holds no traceable data (an
             un-stepped operating point is a set of scalars).
    :rtype: SLiCAPtraces.dataset, NoneType

    :Example:

    >>> TR = sl.tran("amp", "1n", "1u", names={"V_out": "v(out)"})
    >>> D  = sl.instr2dataset(TR)
    >>> T  = sl.make_traces(D, [{"y": "V_out * 2", "label": "twice"}])
    """
    data = getattr(instr, instr.dataType, None)
    if not isinstance(data, dict) or not data:
        return None
    dep_vars = list(instr.circuit.dep_vars) if instr.circuit else []

    # Step column(s): one value per run.
    step_params = {}
    if instr.step:
        if instr.stepVar is not None and instr.stepList is not None:
            step_params[str(instr.stepVar)] = np.asarray(instr.stepList)
        elif instr.stepArray is not None and len(instr.stepArray):
            # stepArray holds one ROW per run, with the value of every step
            # parameter; the dataset wants one entry PER PARAMETER with its
            # value per run, so the array is transposed here (TRACES.md
            # phase 4 - before this the columns were labelled run_1, run_2,
            # which made the labeller index a run as if it were a parameter)
            rows = np.asarray(instr.stepArray)
            names = [str(v) for v in (instr.stepVars or [])]
            for j, name in enumerate(names):
                if j < rows.shape[1]:
                    step_params[name] = rows[:, j]

    # Auto-derive the x-axis key from the result dict.
    run_abscissa = False
    if x_key is None:
        sweep_keys = [k for k in data if k not in dep_vars]
        if sweep_keys:
            x_key = sweep_keys[0]                 # AC/TRAN/DC/NOISE sweep
        elif instr.step and instr.stepVar is not None:
            x_key = str(instr.stepVar)            # stepped OP: x = step values
        elif step_params:
            # stepped OP with several step parameters: no single parameter
            # to put on the abscissa, so the RUN NUMBER is the abscissa and
            # run_table() carries the values (TRACES.md section 3)
            x_key = "run"
            run_abscissa = True
        else:
            return None                           # un-stepped OP scalars

    if run_abscissa:
        n_runs = max(len(np.atleast_1d(v)) for v in step_params.values())
        x_data = np.arange(1, n_runs + 1)
    else:
        x_data = np.asarray(data[x_key]) if x_key in data else None
    if x_data is None and x_key in step_params:
        # stepped OP: the step column IS the abscissa, not a step parameter
        x_data = step_params.pop(x_key)
    if y_keys is None:
        y_keys = dep_vars or [k for k in data if k != x_key]
    signals = {k: data[k] for k in y_keys if k in data and k != x_key}
    # NGspice's own spellings: v(out) is a voltage, i(v1) a current, the
    # noise spectra are squared (the decks set sqrnoise). The units travel
    # with the data so a trace knows them whatever axis shows it
    # (Anton, 2026-08-02).
    units = {}
    for name in list(signals) + ([x_key] if x_key else []):
        found = (_NG_SWEEP_UNITS.get(str(name).lower())
                 or _ngspice_units_hint(name, instr))
        if found:
            units[name] = found
    return dataset(x_name=x_key, x_data=x_data, signals=signals,
                   step_params=step_params,
                   params=_numeric_par_defs(instr), units=units)


def _numeric_par_defs(instr):
    """``{name: float}`` of the result's circuit parameters.

    The producer resolves the SYMBOLIC definitions (``instr.circuit.parDefs``,
    sympy) into numbers here, because the post-processing layer is
    backend-neutral and knows nothing about sympy (TRACES.md section 2).
    Parameters that are not numeric after substitution are left out: an
    expression cannot compute with them.
    """
    par_defs = getattr(getattr(instr, "circuit", None), "parDefs", None) or {}
    numeric = {}
    for key, value in par_defs.items():
        try:
            numeric[str(key)] = float(value)
        except (TypeError, ValueError):
            continue
    return numeric


def _ngspice_dataset_adapter(obj):
    """Registered converter: an NGspice result object -> dataset."""
    from SLiCAP.SLiCAPinstruction import instruction as _instruction
    if not isinstance(obj, _instruction):
        return None
    return instr2dataset(obj)


# What NGspice sweeps, in its own spelling - VERIFIED against runs, not
# assumed: a voltage sweep writes the abscissa as `v(v-sweep)` (so the v(...)
# rule already answers it) and a temperature sweep as `temp-sweep`, in
# degrees Celsius (`option temp`).
_NG_SWEEP_UNITS = {"frequency": "Hz", "time": "s", "temp-sweep": "degC"}


def _ngspice_units_hint(name, result=None):
    """Units of NGspice's own vector spellings.

    ``v(out)`` is a voltage and ``i(v1)`` a current because NGspice says so -
    the producer, not the neutral layer, knows this (TRACES.md phase 7).
    Noise comes back SQUARED: the decks set ``sqrnoise``, which the manual
    (variable ``sqrnoise``) defines as "V^2/Hz or A^2/Hz". The input-referred
    spectrum follows the INPUT SOURCE - a current source makes it A^2/Hz -
    and an internal device parameter (``@q1[gm]``) gets nothing: only the
    device model knows what it is.
    """
    lower = str(name).lower()
    if re.fullmatch(r"v\(.+\)", lower):
        return "V"
    if re.fullmatch(r"i\(.+\)", lower):
        return "A"
    if lower == "onoise_spectrum" or lower.startswith("onoise_"):
        return "V^2/Hz"
    if lower == "inoise_spectrum" or lower.startswith("inoise_"):
        source = str(getattr(result, "source", "") or "")
        return "A^2/Hz" if source[:1].lower() == "i" else "V^2/Hz"
    return None


register_units_hint(_ngspice_units_hint)


register_dataset_adapter(_ngspice_dataset_adapter)
