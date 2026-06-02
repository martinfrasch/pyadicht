"""Cross-platform tests: model + portable .npz round-trip + DLL graceful-fail.

These run on any platform (no .adicht, no DLL). They guard the contract that the
Windows-read → .npz → anywhere-read bridge preserves the data exactly.
"""

from __future__ import annotations

import numpy as np
import pytest

import adicht
from adicht.model import Channel, Comment, Record, Recording
from adicht.backends import get_backend


def _sample_recording():
    rng = np.random.default_rng(0)
    ch1 = Channel("Pressure", "mmHg", 1000.0, rng.standard_normal(5000))
    ch2 = Channel("ECG", "mV", 2000.0, rng.standard_normal(10000))
    cm = Comment("occlusion start", channel=-1, record=0, tick_pos=1234, time_s=1.234)
    rec = Record(channels=[ch1, ch2], comments=[cm])
    return Recording(records=[rec], source_path="H1.adicht", backend="dll",
                     meta={"n_records": 1})


def test_portable_roundtrip_preserves_data(tmp_path):
    rec = _sample_recording()
    p = adicht.to_npz(rec, tmp_path / "H1.npz")
    back = adicht.read(p)                      # auto → portable backend
    assert back.backend == "dll"               # provenance preserved
    assert back.channel_names() == ["Pressure", "ECG"]
    orig, got = rec.records[0], back.records[0]
    for a, b in zip(orig.channels, got.channels):
        assert a.name == b.name and a.units == b.units and a.fs_hz == b.fs_hz
        np.testing.assert_array_equal(a.data, b.data)
    assert got.comments[0].text == "occlusion start"
    assert got.comments[0].tick_pos == 1234


def test_read_auto_selects_portable_for_npz(tmp_path):
    p = adicht.to_npz(_sample_recording(), tmp_path / "x.npz")
    # no exception, and it did NOT try the DLL backend
    assert adicht.read(p).n_records == 1


def test_channel_helpers():
    ch = Channel("p", "mmHg", 500.0, np.zeros(1000))
    assert ch.n_samples == 1000
    assert ch.duration_s == pytest.approx(2.0)
    assert ch.time()[-1] == pytest.approx(999 / 500.0)


def test_dll_backend_fails_gracefully_without_windows():
    """Off-Windows, the DLL backend must raise a CLEAR, actionable error."""
    try:
        import adi  # noqa: F401
        pytest.skip("adi-reader importable here; graceful-fail path not exercised")
    except Exception:
        pass
    with pytest.raises(RuntimeError, match="only runs on Windows"):
        get_backend("dll").read("nonexistent.adicht")


def test_unknown_backend():
    with pytest.raises(ValueError, match="unknown backend"):
        get_backend("bogus")
