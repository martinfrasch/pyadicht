"""pyadicht — cross-platform reader for ADInstruments LabChart (.adicht) files.

The proprietary `.adicht` binary can only be read where the ADInstruments DLL
runs (Windows; a UTM VM works). pyadicht isolates that to one backend and exports
to a portable `.npz` that macOS/Linux read with no ADInstruments dependency.

Quick start
-----------
On a host that can read .adicht (Windows / UTM):
    import adicht
    rec = adicht.read("H1.adicht")            # auto-selects the DLL backend
    adicht.to_npz(rec, "H1.npz")

Anywhere (macOS/Linux):
    rec = adicht.read("H1.npz")               # auto-selects the portable backend
    ch = rec.records[0].channel_by_name("Pressure")

Or force a backend:  adicht.read(path, backend="portable")
"""

from __future__ import annotations

from pathlib import Path

from .model import Channel, Comment, Record, Recording
from .portable import from_npz, to_npz
from .backends import get_backend

__version__ = "0.1.0"
__all__ = ["read", "to_npz", "from_npz", "Recording", "Record", "Channel", "Comment"]


def read(path: str | Path, backend: str | None = None) -> Recording:
    """Read a recording. Backend auto-selected by extension unless given:
    .npz → portable; otherwise → dll (the ADInstruments reader)."""
    if backend is None:
        backend = "portable" if str(path).lower().endswith(".npz") else "dll"
    return get_backend(backend).read(path)
