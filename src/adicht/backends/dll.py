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

    def read(self, path: str | Path, channels: list[int] | None = None,
             records: list[int] | None = None, window_s: float | None = None,
             retries: int = 5) -> Recording:
        """Read a .adicht into the neutral model.

        channels : 1-based channel indices to keep (None = all). Selecting just
                   the channel you need keeps the export small and bounds VM RAM
                   (full multi-channel reads of long files are GB-scale).
        records  : 1-based record indices to keep (None = all).
        window_s : keep only the first `window_s` seconds of each channel
                   (None = full). Use to export just the basal window.
        retries  : the SDK throws transient open errors on a network share;
                   retry with backoff.
        """
        import time
        adi = self._require_adi()
        path = Path(path)
        last = None
        for i in range(max(1, retries)):
            try:
                f = adi.read_file(str(path))
                break
            except Exception as e:               # transient share/open error
                last = e; time.sleep(2)
        else:
            raise RuntimeError(f"could not open {path} after {retries} tries: {last}")
        out_records: list[Record] = []
        n_records = f.n_records
        rec_idx = records or list(range(1, n_records + 1))
        for r in rec_idx:
            chans: list[Channel] = []
            for ci, ch in enumerate(f.channels, start=1):
                if channels and ci not in channels:
                    continue
                try:
                    fs = float(ch.fs[r - 1])
                    if window_s is not None:
                        stop = max(1, int(window_s * fs))
                        data = np.asarray(ch.get_data(r, start_sample=1,
                                                      stop_sample=stop), dtype=np.float64)
                    else:
                        data = np.asarray(ch.get_data(r), dtype=np.float64)
                except Exception:
                    continue                     # channel absent in this record
                chans.append(Channel(name=str(ch.name), units=str(ch.units[r - 1])
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
            out_records.append(Record(channels=chans, comments=comments))
        return Recording(records=out_records, source_path=str(path),
                         backend=self.name,
                         meta={"n_records": n_records,
                               "selected_channels": channels,
                               "selected_records": records,
                               "window_s": window_s})
