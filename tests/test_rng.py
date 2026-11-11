"""SplitMix64: Regressionstest auf feste Werte (Vigna-Konvention). Der Generator ist ein wörtlicher Auszug aus reduktionskette-demo/red_scenario.py."""

from pathlib import Path

import pytest

from dje_rng import SplitMix64

ROOT = Path(__file__).resolve().parent.parent


def test_seed_0_gives_the_published_stream():
    """Erste drei Ausgaben von SplitMix64 mit Seed 0 (Referenzwerte aus der Konvention von Vigna)."""
    r = SplitMix64(0)
    assert [r.next() for _ in range(3)] == [16294208416658607535, 7960286522194355700, 487617019471545679]


def test_same_seed_same_stream_different_seed_different_stream():
    a, b, c = SplitMix64(42), SplitMix64(42), SplitMix64(43)
    xs, ys, zs = [a.next() for _ in range(5)], [b.next() for _ in range(5)], [c.next() for _ in range(5)]
    assert xs == ys and xs != zs


def test_below_is_in_range_and_covers_it():
    r = SplitMix64(7)
    werte = [r.below(6) for _ in range(600)]
    assert min(werte) == 0 and max(werte) == 5 and set(werte) == set(range(6))


def test_extract_is_verbatim_from_the_original():
    """Die Klasse und `MASK` stehen wörtlich im Original, solange es im Portfolio-Ordner liegt."""
    quelle = ROOT.parent / "reduktionskette-demo" / "red_scenario.py"
    if not quelle.exists():
        pytest.skip("Original liegt nicht im Portfolio-Ordner")
    original = quelle.read_text(encoding="utf-8").splitlines()
    mine = (ROOT / "dje_rng.py").read_text(encoding="utf-8").splitlines()
    assert mine[0].startswith("# Auszug aus reduktionskette-demo/red_scenario.py")
    kopie = mine[mine.index("MASK = (1 << 64) - 1"):]
    start = original.index("MASK = (1 << 64) - 1")
    assert original[start:start + len(kopie)] == kopie, "der Auszug weicht vom Original ab: Änderungen gehören ins Original, danach neu kopieren"
