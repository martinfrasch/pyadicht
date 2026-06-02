# pyadicht

Cross-platform reader for **ADInstruments LabChart `.adicht`** files.

The `.adicht` binary can only be read where the proprietary ADInstruments DLL
runs (**Windows**; a UTM VM on a Mac is fine). `adi-reader`, the only working
Python reader, is Windows-only for that reason. **pyadicht** isolates that one
step behind a backend and exports to a portable **`.npz`** that macOS/Linux read
back with no ADInstruments dependency — so all analysis runs natively on your Mac
and Linux workstation.

```
.adicht ──(Windows / UTM, DLL backend)──▶ .npz ──(macOS / Linux, portable backend)──▶ analysis
```

## Install

```bash
pip install pyadicht                 # macOS / Linux — portable backend + analysis
pip install "pyadicht[dll]"          # Windows / UTM — adds the adi-reader DLL backend
```

(From source: `pip install -e ".[dev]"`, or `".[dll,dev]"` on Windows.)

## Workflow on a no-Windows host

**1 — inside a Windows VM (UTM) where the `.adicht` files are reachable** (with
`pip install "pyadicht[dll]"`):

```bash
adicht export-dir "HRV Data" --to exported_npz      # batch every .adicht → .npz
# or one file:  adicht export H1.adicht --to H1.npz
```

**2 — copy the small `.npz` files out of the VM, then on macOS / Linux:**

```python
import adicht
rec = adicht.read("H1.npz")                         # auto → portable backend
ch  = rec.records[0].channel_by_name("Pressure")
print(ch.fs_hz, ch.n_samples, ch.duration_s)
import numpy as np;  signal, t = ch.data, ch.time()
```

`adicht info H1.npz` (or `H1.adicht` on Windows) prints a one-screen summary.

## Data model

`read()` returns a `Recording` → `records[]` → each `Record` has `channels[]`
(`name, units, fs_hz, data, time()`) and `comments[]` (LabChart event markers).
This model is identical on every platform and carries no proprietary dependency.

## Backends

| backend | reads | platform |
|---|---|---|
| `dll` | `.adicht` via `adi-reader` (ADInstruments DLL) | Windows / UTM only |
| `portable` | `.npz` written by a `dll` run | any |

`adicht.read(path, backend=...)` forces one; otherwise it's chosen by extension
(`.npz` → portable, else → dll). A future native binary parser would slot in as a
third backend with no change to callers.

## Status

v0.1.0. Portable round-trip + model + graceful-failure are tested on macOS/Linux
(`pytest`). The DLL backend's `.adicht` parsing is exercised on Windows/UTM (it
needs the ADInstruments runtime). If your VM's `adi-reader` exposes channel/
comment attributes differently, `src/adicht/backends/dll.py` is the only file to
adjust — the neutral model and the portable bridge stay fixed.

## License

MIT — see [LICENSE](LICENSE).
