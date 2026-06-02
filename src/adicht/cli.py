"""adicht CLI.

  adicht export <in.adicht> --to <out.npz>   # run inside Windows/UTM (DLL backend)
  adicht export-dir <dir> --to <outdir>       # batch every .adicht in a folder
  adicht info <file.adicht|file.npz>          # summarize a recording (any platform)
"""

from __future__ import annotations

import argparse
from pathlib import Path

from . import read, to_npz


def _info(rec) -> str:
    lines = [f"source: {rec.source_path}", f"backend: {rec.backend}",
             f"records: {rec.n_records}", f"channels: {rec.channel_names()}"]
    for ri, r in enumerate(rec.records):
        for ch in r.channels:
            lines.append(f"  rec{ri} '{ch.name}' [{ch.units}] "
                         f"fs={ch.fs_hz:g}Hz n={ch.n_samples} dur={ch.duration_s:.1f}s")
        if r.comments:
            lines.append(f"  rec{ri} comments: {len(r.comments)}")
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="adicht", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def _read_opts(p):
        p.add_argument("--channels", default=None,
                       help="1-based channel indices to keep, comma-sep (e.g. 2)")
        p.add_argument("--records", default=None,
                       help="1-based record indices to keep, comma-sep (e.g. 1)")
        p.add_argument("--window-min", type=float, default=None,
                       help="keep only the first N minutes of each channel")

    pe = sub.add_parser("export", help="read one .adicht (DLL backend) → .npz")
    pe.add_argument("input")
    pe.add_argument("--to", required=True)
    pe.add_argument("--backend", default=None)
    _read_opts(pe)

    pd = sub.add_parser("export-dir", help="batch-export every .adicht in a folder")
    pd.add_argument("indir")
    pd.add_argument("--to", required=True)
    _read_opts(pd)

    pi = sub.add_parser("info", help="summarize a recording (.adicht or .npz)")
    pi.add_argument("input")
    pi.add_argument("--backend", default=None)

    args = ap.parse_args(argv)

    def _read_kwargs(a):
        kw = {}
        if getattr(a, "channels", None):
            kw["channels"] = [int(x) for x in a.channels.split(",")]
        if getattr(a, "records", None):
            kw["records"] = [int(x) for x in a.records.split(",")]
        if getattr(a, "window_min", None) is not None:
            kw["window_s"] = a.window_min * 60.0
        return kw

    if args.cmd == "export":
        rec = read(args.input, backend=args.backend, **_read_kwargs(args))
        out = to_npz(rec, args.to)
        print(f"wrote {out}"); return 0
    if args.cmd == "export-dir":
        outdir = Path(args.to); outdir.mkdir(parents=True, exist_ok=True)
        files = sorted(Path(args.indir).glob("*.adicht"))
        if not files:
            print(f"no .adicht files in {args.indir}"); return 1
        kw = _read_kwargs(args)
        for f in files:
            rec = read(f, backend="dll", **kw)
            out = to_npz(rec, outdir / (f.stem + ".npz"))
            print(f"{f.name} → {out}")
        return 0
    if args.cmd == "info":
        print(_info(read(args.input, backend=args.backend))); return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
