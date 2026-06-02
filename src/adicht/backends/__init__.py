"""Pluggable .adicht read backends.

Each backend turns a source into a platform-neutral `Recording` (model.py):

  * dll      — wraps adi-reader (ADInstruments Windows DLL). Reads .adicht ONLY
               where the DLL runs (Windows, e.g. a UTM VM). The only backend that
               touches the proprietary binary.
  * portable — reads the .npz archive a dll-backend run wrote (any platform).

The intended workflow on a no-Windows host: read .adicht with `dll` inside a UTM
Windows VM → `to_npz` → carry the .npz to macOS/Linux → `portable` → analyze.
"""

from __future__ import annotations


def get_backend(name: str):
    if name == "dll":
        from .dll import DllBackend
        return DllBackend()
    if name == "portable":
        from .portable_backend import PortableBackend
        return PortableBackend()
    raise ValueError(f"unknown backend {name!r} (choices: dll, portable)")
