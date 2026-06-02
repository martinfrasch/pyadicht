"""Platform-neutral data model for a read LabChart (.adicht) recording.

Every backend (the Windows DLL reader, the portable .npz reader, a future native
parser) produces this same `Recording`, so downstream analysis is identical on
any platform. The recording is the data *after* the proprietary binary has been
read — it carries no ADInstruments dependency.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class Comment:
    """A LabChart comment (event marker)."""

    text: str
    channel: int        # -1 = all-channels comment
    record: int         # which record/block
    tick_pos: int       # sample index within the record
    time_s: float       # seconds from record start


@dataclass
class Channel:
    """One channel of one record: a uniformly-sampled signal."""

    name: str
    units: str
    fs_hz: float                 # samples per second
    data: np.ndarray             # 1-D float array

    @property
    def n_samples(self) -> int:
        return int(self.data.size)

    @property
    def duration_s(self) -> float:
        return self.n_samples / self.fs_hz if self.fs_hz else 0.0

    def time(self) -> np.ndarray:
        return np.arange(self.n_samples) / self.fs_hz


@dataclass
class Record:
    """A LabChart record (contiguous acquisition block); channels share a clock
    start but may differ in sampling rate."""

    channels: list[Channel] = field(default_factory=list)
    comments: list[Comment] = field(default_factory=list)

    def channel_by_name(self, name: str) -> Channel | None:
        for c in self.channels:
            if c.name == name:
                return c
        return None


@dataclass
class Recording:
    """A full .adicht file: one or more records, plus provenance metadata."""

    records: list[Record] = field(default_factory=list)
    source_path: str = ""
    backend: str = ""            # which backend produced this
    meta: dict = field(default_factory=dict)

    @property
    def n_records(self) -> int:
        return len(self.records)

    def channel_names(self) -> list[str]:
        names: list[str] = []
        for rec in self.records:
            for c in rec.channels:
                if c.name not in names:
                    names.append(c.name)
        return names
