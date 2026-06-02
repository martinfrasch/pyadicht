"""DLL backend — reads .adicht via adi-reader (ADInstruments Windows SDK).

Works ONLY where the ADInstruments DLL loads — i.e. Windows (a UTM VM is fine).
On macOS/Linux the `import adi` will fail with a clear message pointing to the
portable workflow. This is the single point in the package that touches the
proprietary binary; everything downstream uses the neutral Recording model.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from ..model import Channel, Comment, Record, Recording


class DllBackend:
    name = "dll"

    def _require_adi(self):
        try:
            import adi  # adi-reader; bundles the ADInstruments Windows DLL
        except Exception as exc:  # ImportError or DLL-load failure off-Windows
            raise RuntimeError(
                "The DLL backend needs `adi-reader`, which only runs on Windows "
                "(it wraps the ADInstruments DLL). Run it inside a Windows VM "
                "(e.g. UTM), export with `adicht export ... --to file.npz`, then "
                "read the .npz on macOS/Linux with the 'portable' backend. "
                f"(import error: {exc})"
            ) from exc
        return adi

    def read(self, path: str | Path) -> Recording:
        adi = self._require_adi()
        path = Path(path)
        f = adi.read_file(str(path))
        records: list[Record] = []
        # adi-reader exposes 1-based channels; n_records per file; per-record
        # sampling and data. We normalize into the neutral model.
        n_records = f.n_records
        for r in range(1, n_records + 1):
            channels: list[Channel] = []
            for ch in f.channels:
                # ch.fs is a per-record list (samples/s); data is 1-based by record
                try:
                    fs = float(ch.fs[r - 1])
                    data = np.asarray(ch.get_data(r), dtype=np.float64)
                except Exception:
                    # channel not present in this record
                    continue
                channels.append(Channel(name=str(ch.name), units=str(ch.units[r - 1])
                                        if hasattr(ch, "units") else "",
                                        fs_hz=fs, data=data))
            comments: list[Comment] = []
            for rec_obj in (f.records[r - 1],) if hasattr(f, "records") else ():
                for cm in getattr(rec_obj, "comments", []) or []:
                    comments.append(Comment(
                        text=str(getattr(cm, "text", "")),
                        channel=int(getattr(cm, "channel_", -1)),
                        record=r,
                        tick_pos=int(getattr(cm, "tick_position", 0)),
                        time_s=float(getattr(cm, "time", 0.0)),
                    ))
            records.append(Record(channels=channels, comments=comments))
        return Recording(records=records, source_path=str(path), backend=self.name,
                         meta={"n_records": n_records})
