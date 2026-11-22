"""Help > Create shortcut (Anton, 2026-11-20): a shortcut that starts the
SLiCAP GUI from the launcher of the system, with the icon of SLiCAP.

- Windows: SLiCAP.lnk in the start menu and on the desktop, written by
  PowerShell through WScript.Shell, which every Windows has. It starts
  pythonw.exe, so no console window opens. In an Anaconda environment it
  starts through conda's cwp.py, which activates the environment first, as
  Anaconda's own shortcuts do. The shortcut carries the application id of
  the running GUI (APP_ID), so that a pinned SLiCAP and the running one
  share one taskbar button. WScript.Shell cannot write that property:
  PowerShell compiles a few lines of C# (Add-Type, also offline) that
  write it through the property store of the shortcut. Without it a
  pinned SLiCAP got a second button when it started (Anton, 2026-11-20,
  Windows 10).
- Linux: slicap.desktop in ~/.local/share/applications (XDG_DATA_HOME),
  which puts SLiCAP in the applications overview. StartupWMClass matches
  the window class that main.setup_application() gives every window.
- Other systems: none; the GUI does not offer the entry (available()).

The environment (Anton, 2026-11-20: "It is important that SLiCAP always
starts from the correct Python environment"): the shortcut names the
Python that runs the GUI now, by its own path. That path is never
resolved: the python of a virtual environment is a link, and only under
its own name does it start in that environment. In conda on Windows the
shortcut starts through cwp.py of the base installation, with the base
Python, which has the menuinst module that cwp.py imports. cwp.py puts the
folders of the environment first on PATH and starts its pythonw.exe, as
Anaconda's own shortcuts do. Started from another environment, Help >
Create shortcut replaces the shortcut with one for that environment.

This module has no Qt: the GUI calls create_shortcut() and shows
pin_hint().
"""
from __future__ import annotations

import base64
import os
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple

from .child_process import NO_WINDOW

APP_ID = "SLiCAP.SLiCAP"     # the Windows application id of the running GUI
WM_CLASS = "SLiCAP"          # the application name: the window class on X11
DESKTOP_ID = "slicap"        # slicap.desktop, and the application id on Wayland
MODULE = "SLiCAP.schematic.main"


class ShortcutError(Exception):
    """The shortcut could not be made. The message says why."""


class Created(NamedTuple):
    """The files written, and what did not work in them while the shortcut
    itself works (on Windows: the application id)."""
    paths: list
    warnings: list


def icons_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "files" / "icons"


def available() -> bool:
    """True on the systems this module makes a shortcut for."""
    return sys.platform == "win32" or sys.platform.startswith("linux")


def create_shortcut() -> Created:
    """Make the shortcut of this system."""
    if sys.platform == "win32":
        return _windows()
    if sys.platform.startswith("linux"):
        return Created([_linux()], [])
    raise ShortcutError("Creating a shortcut is not available on this system.")


def pin_hint() -> str:
    """Where the shortcut is, and how to keep SLiCAP in the taskbar or dock."""
    if sys.platform == "win32":
        return ("SLiCAP is now in the start menu and on the desktop.\n\n"
                "To keep it in the taskbar, right-click SLiCAP in the start "
                "menu and choose Pin to taskbar.")
    return ("SLiCAP is now in the applications overview.\n\n"
            "To keep it in the dock, right-click it there and choose Add to "
            "Favorites (Pin to Dash in some versions).")


# ── Windows ───────────────────────────────────────────────────────────────

# The values come in through environment variables, so that no path needs
# quoting, and the script itself goes in encoded (-EncodedCommand), so that
# its lines need none either. A line "NOID <reason>" reports a shortcut
# without the application id; the shortcut itself works.
_POWERSHELL = r"""
$ErrorActionPreference = 'Stop'
$withId = $true
try {
    Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;

namespace SLiCAPShortcut {
    [StructLayout(LayoutKind.Sequential, Pack = 4)]
    public struct PropertyKey {
        public Guid FormatId;
        public uint PropertyId;
    }

    [StructLayout(LayoutKind.Explicit, Size = 24)]
    public struct PropVariant {
        [FieldOffset(0)] public ushort VarType;
        [FieldOffset(8)] public IntPtr Pointer;
    }

    [ComImport, Guid("886D8EEB-8CF2-4446-8D02-CDBA1DBDCF99"),
     InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    public interface IPropertyStore {
        [PreserveSig] int GetCount(out uint count);
        [PreserveSig] int GetAt(uint index, out PropertyKey key);
        [PreserveSig] int GetValue(ref PropertyKey key, out PropVariant value);
        [PreserveSig] int SetValue(ref PropertyKey key, ref PropVariant value);
        [PreserveSig] int Commit();
    }

    public static class Link {
        [DllImport("shell32.dll", CharSet = CharSet.Unicode, PreserveSig = false)]
        static extern void SHGetPropertyStoreFromParsingName(
            string path, IntPtr bindContext, int flags, ref Guid iid,
            [MarshalAs(UnmanagedType.Interface)] out IPropertyStore store);

        public static void SetAppId(string path, string appId) {
            Guid iid = typeof(IPropertyStore).GUID;
            IPropertyStore store;
            SHGetPropertyStoreFromParsingName(path, IntPtr.Zero, 2, ref iid, out store);
            try {
                PropertyKey key = new PropertyKey();
                key.FormatId = new Guid("9F4C2855-9F79-4B39-A8D0-E1D42DE1D5F3");
                key.PropertyId = 5;
                PropVariant value = new PropVariant();
                value.VarType = 31;
                value.Pointer = Marshal.StringToCoTaskMemUni(appId);
                try {
                    Marshal.ThrowExceptionForHR(store.SetValue(ref key, ref value));
                    Marshal.ThrowExceptionForHR(store.Commit());
                } finally {
                    Marshal.FreeCoTaskMem(value.Pointer);
                }
            } finally {
                Marshal.ReleaseComObject(store);
            }
        }
    }
}
'@
} catch {
    $withId = $false
    Write-Output ('NOID ' + $_.Exception.Message)
}
$shell = New-Object -ComObject WScript.Shell
foreach ($folder in [Environment]::GetFolderPath('Programs'), [Environment]::GetFolderPath('Desktop')) {
    $path = Join-Path $folder 'SLiCAP.lnk'
    $link = $shell.CreateShortcut($path)
    $link.TargetPath = $env:SLICAP_TARGET
    $link.Arguments = $env:SLICAP_ARGUMENTS
    $link.IconLocation = $env:SLICAP_ICON
    $link.WorkingDirectory = $env:USERPROFILE
    $link.Description = 'SLiCAP'
    $link.Save()
    if ($withId) {
        try { [SLiCAPShortcut.Link]::SetAppId($path, $env:SLICAP_APPID) }
        catch { Write-Output ('NOID ' + $_.Exception.Message) }
    }
    Write-Output $path
}
"""
# In the C#: GPS_READWRITE = 2; PKEY_AppUserModel_ID = the format id
# 9F4C2855-... with property id 5; VT_LPWSTR = 31.


def _conda_cwp() -> "Path | None":
    """cwp.py ("call with prefix") of the conda base installation, or None
    outside conda. The base is this prefix itself, the installation that
    CONDA_EXE points to, or the folder that holds envs/<name>."""
    prefix = Path(sys.prefix)
    candidates = [prefix / "cwp.py"]
    conda_exe = os.environ.get("CONDA_EXE")
    if conda_exe:
        candidates.append(Path(conda_exe).parent.parent / "cwp.py")
    if prefix.parent.name.lower() == "envs":
        candidates.append(prefix.parent.parent / "cwp.py")
    for cwp in candidates:
        if cwp.is_file():
            return cwp
    return None


def _windowed(python: Path) -> Path:
    """pythonw.exe next to *python*, which starts without a console window,
    or *python* itself when there is none."""
    pythonw = python.with_name("pythonw.exe")
    return pythonw if pythonw.is_file() else python


def windows_command() -> tuple:
    """(target, arguments) of the Windows shortcut. Without conda the
    target is the pythonw.exe of this environment. With conda it is the
    pythonw.exe of the base, which runs cwp.py with this prefix and this
    environment's pythonw.exe."""
    target = _windowed(Path(sys.executable))
    cwp = _conda_cwp()
    if cwp is None:
        return str(target), "-m %s" % MODULE
    base = _windowed(cwp.with_name("python.exe"))
    return str(base), '"%s" "%s" "%s" -m %s' % (cwp, sys.prefix, target, MODULE)


def _windows() -> Created:
    target, arguments = windows_command()
    env = dict(os.environ, SLICAP_TARGET=target, SLICAP_ARGUMENTS=arguments,
               SLICAP_ICON="%s,0" % (icons_dir() / "slicap.ico"),
               SLICAP_APPID=APP_ID)
    encoded = base64.b64encode(_POWERSHELL.encode("utf-16-le")).decode("ascii")
    try:
        done = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded],
            env=env, capture_output=True, text=True,
            creationflags=NO_WINDOW)
    except OSError as exc:
        raise ShortcutError("PowerShell could not be started: %s" % exc) from exc
    if done.returncode != 0:
        raise ShortcutError(done.stderr.strip() or "PowerShell could not write the shortcut.")
    paths, warnings = [], []
    for line in (l.strip() for l in done.stdout.splitlines()):
        if line.startswith("NOID "):
            warnings.append("Windows may show SLiCAP twice in the taskbar: the "
                            "application id could not be written into the "
                            "shortcut (%s)." % line[5:])
        elif line:
            paths.append(Path(line))
    return Created(paths, warnings)


# ── Linux ─────────────────────────────────────────────────────────────────

_RESERVED = set(' \t\n"\'\\><~|&;$*?#()`')


def _exec_argument(arg: str) -> str:
    """One argument of the Exec key of a desktop entry. An argument with a
    reserved character is quoted. Inside the quotes " ` $ and \\ get a
    backslash, and the string rule of the format doubles every backslash.
    A % is written as %%."""
    arg = arg.replace("%", "%%")
    if not any(c in _RESERVED for c in arg):
        return arg
    quoted = "".join("\\" + c if c in '"`$\\' else c for c in arg)
    return '"%s"' % quoted.replace("\\", "\\\\")


def desktop_entry() -> str:
    """The text of slicap.desktop."""
    exec_line = " ".join(_exec_argument(a) for a in (sys.executable, "-m", MODULE))
    return "\n".join([
        "[Desktop Entry]",
        "Type=Application",
        "Name=SLiCAP",
        "GenericName=Electronic design environment",
        "Comment=Schematics, symbolic analysis with SLiCAP, simulation with NGspice",
        "Exec=" + exec_line,
        "Icon=" + str(icons_dir() / "slicap_256.png"),
        "Terminal=false",
        "Categories=Science;Engineering;Electronics;",
        "StartupNotify=true",
        "StartupWMClass=" + WM_CLASS,
        "",
    ])


def _linux() -> Path:
    data = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    folder = Path(data) / "applications"
    path = folder / (DESKTOP_ID + ".desktop")
    try:
        folder.mkdir(parents=True, exist_ok=True)
        path.write_text(desktop_entry(), encoding="utf-8")
    except OSError as exc:
        raise ShortcutError("The shortcut could not be written: %s" % exc) from exc
    return path
