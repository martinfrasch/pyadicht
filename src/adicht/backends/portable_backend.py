"""Portable backend — reads the .npz a dll-backend run exported. Any platform."""

from __future__ import annotations

from pathlib import Path

from ..model import Recording
from ..portable import from_npz


class PortableBackend:
    name = "portable"

    def read(self, path: str | Path) -> Recording:
        return from_npz(path)
