"""Portable .npz serialization of a Recording — the cross-platform bridge.

A `.adicht` file can only be read where the ADInstruments DLL runs (Windows,
e.g. a UTM VM). `to_npz` writes the read Recording to a plain NumPy archive that
any platform reads back with `from_npz` — no ADInstruments dependency. This is
how the proprietary-read step (Windows) is decoupled from analysis (macOS/Linux).

Layout: a single .npz holding flat arrays + a JSON sidecar string for structure.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from .model import Channel, Comment, Record, Recording

FORMAT_VERSION = 1


def to_npz(rec: Recording, path: str | Path) -> Path:
    """Serialize a Recording to a portable .npz archive."""
    path = Path(path)
    arrays: dict[str, np.ndarray] = {}
    structure = {
        "format_version": FORMAT_VERSION,
        "source_path": rec.source_path,
        "backend": rec.backend,
        "meta": rec.meta,
        "records": [],
    }
    for ri, record in enumerate(rec.records):
        chans = []
        for ci, ch in enumerate(record.channels):
            key = f"r{ri}_c{ci}"
            arrays[key] = np.asarray(ch.data, dtype=np.float64)
            chans.append({"name": ch.name, "units": ch.units,
                          "fs_hz": ch.fs_hz, "array": key})
        comments = [{"text": cm.text, "channel": cm.channel, "record": cm.record,
                     "tick_pos": cm.tick_pos, "time_s": cm.time_s}
                    for cm in record.comments]
        structure["records"].append({"channels": chans, "comments": comments})
    arrays["__structure__"] = np.frombuffer(
        json.dumps(structure).encode("utf-8"), dtype=np.uint8)
    np.savez_compressed(path, **arrays)
    return path if path.suffix == ".npz" else path.with_suffix(".npz")


def from_npz(path: str | Path) -> Recording:
    """Load a Recording from a portable .npz archive (any platform)."""
    path = Path(path)
    with np.load(path, allow_pickle=False) as npz:
        structure = json.loads(bytes(npz["__structure__"]).decode("utf-8"))
        records = []
        for rs in structure["records"]:
            channels = [Channel(name=c["name"], units=c["units"],
                                fs_hz=c["fs_hz"], data=npz[c["array"]])
                        for c in rs["channels"]]
            comments = [Comment(**cm) for cm in rs["comments"]]
            records.append(Record(channels=channels, comments=comments))
    return Recording(records=records, source_path=structure["source_path"],
                     backend=structure["backend"], meta=structure["meta"])
