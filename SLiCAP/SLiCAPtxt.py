#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SLiCAP module with the TXT formatter.

The TXT formatter produces plain-text snippets saved in the project's
``txt/`` folder (``sl.ini.txt_path``). Together with
``LaTeXformatter.file()`` (``\\lstinputlisting``) this makes terminal-style
output — pole-zero listings, servo-bandwidth results, phase margins, or any
captured print output — reportable in LaTeX documents (SLNG.md, "LaTeX
formatter GUI", 2026-07-15).

:example:

>>> import SLiCAP as sl
>>> sl.initProject("txt formatter")
>>> txt = sl.TXTformatter()
>>> txt.pz(sl.doPZ(cir, pardefs="circuit")).save("pzlist")
>>> ltx = sl.LaTeXformatter()
>>> ltx.file(sl.ini.txt_path + "pzlist.txt").save("pzlist")
"""
import io
from contextlib import redirect_stdout

import SLiCAP.SLiCAPconfigure as ini
from SLiCAP.SLiCAPprotos import _BaseFormatter, Snippet
from SLiCAP.SLiCAPmath import listPZ, phaseMargin, findServoBandwidth


def _laplace_of(obj):
    """Accepts an executed instruction (uses its .laplace) or a sympy
    expression, and returns the expression."""
    return getattr(obj, "laplace", obj)


class TXTformatter(_BaseFormatter):
    """
    Plain-text formatter. The methods return text snippets; ``save(name)``
    writes ``<name>.txt`` in the project's ``txt/`` folder.
    """

    def __init__(self):
        super().__init__()
        self.format = "txt"
        self.snippet = None

    def text(self, text):
        """
        The basic method: wraps any string as a text snippet — e.g. output
        captured from the terminal or composed by a script.

        :param text: Content of the snippet.
        :type text: str

        :return: SLiCAP Snippet object
        :rtype: SLiCAP.SLiCAPprotos.Snippet
        """
        if not isinstance(text, str):
            text = str(text)
        if not text.endswith("\n"):
            text += "\n"
        return Snippet(text, self.format)

    def output(self, func, *args, **kwargs):
        """
        Captures everything *func(\\*args, \\*\\*kwargs)* prints to stdout
        and wraps it as a text snippet (redirected terminal output).

        :param func: Callable whose printed output is the snippet content.

        :return: SLiCAP Snippet object
        :rtype: SLiCAP.SLiCAPprotos.Snippet
        """
        buf = io.StringIO()
        with redirect_stdout(buf):
            func(*args, **kwargs)
        return self.text(buf.getvalue())

    def pz(self, resultObject):
        """
        Text snippet with the pole-zero listing of *resultObject*
        (the output of ``listPZ()``).

        :param resultObject: SLiCAP execution result of a poles, zeros, or
                             pz analysis.
        :type resultObject: SLiCAP.SLiCAPinstruction.instruction

        :return: SLiCAP Snippet object
        :rtype: SLiCAP.SLiCAPprotos.Snippet
        """
        return self.output(listPZ, resultObject)

    def servoBandwidth(self, loopgain):
        """
        Text snippet with the ``findServoBandwidth()`` results for
        *loopgain* (an executed loop-gain instruction or a sympy
        expression).

        :return: SLiCAP Snippet object
        :rtype: SLiCAP.SLiCAPprotos.Snippet
        """
        result = findServoBandwidth(_laplace_of(loopgain))
        unit = "Hz" if ini.hz else "rad/s"
        lines = ["Servo bandwidth analysis:", ""]
        if result.get("mbv") is not None:
            lines.append("mid-band loop gain value  : {:12.2e}".format(
                float(result["mbv"])))
            lines.append("lowest mid-band frequency : {:12.2e} {}".format(
                float(result["mbf"]), unit))
        if result.get("hpf") is not None:
            lines.append("high-pass intersection    : {:12.2e} {}  "
                         "(order {})".format(float(result["hpf"]), unit,
                                             int(result["hpo"])))
        if result.get("lpf") is not None:
            lines.append("low-pass intersection     : {:12.2e} {}  "
                         "(order {})".format(float(result["lpf"]), unit,
                                             int(result["lpo"])))
        return self.text("\n".join(lines))

    def phaseMargin(self, loopgain):
        """
        Text snippet with the phase margin and unity-gain frequency of
        *loopgain* (an executed loop-gain instruction or a sympy
        expression).

        :return: SLiCAP Snippet object
        :rtype: SLiCAP.SLiCAPprotos.Snippet
        """
        mrgn, freq = phaseMargin(_laplace_of(loopgain))
        p_unit = "deg" if ini.hz else "rad"
        f_unit = "Hz" if ini.hz else "rad/s"
        if mrgn is None or freq is None:
            body = ("Phase margin: could not determine the unity-gain "
                    "frequency.")
        else:
            body = ("Phase margin          : {:8.2f} {}\n"
                    "Unity-gain frequency  : {:12.2e} {}").format(
                        float(mrgn), p_unit, float(freq), f_unit)
        return self.text(body)
