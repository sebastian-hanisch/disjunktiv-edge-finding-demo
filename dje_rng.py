# Auszug aus reduktionskette-demo/red_scenario.py (letzter Commit der Datei: ba24648): `MASK` und die Klasse `SplitMix64`, Zeilen 5 bis 26, wörtlich und unverändert. Änderungen gehören ins Original, nicht hierher.
"""Zufallsgenerator SplitMix64 (ganzzahlig, auf jeder Plattform und in jeder Python-Version derselbe Strom). Nie Python-`random` oder `hash()` verwenden."""

MASK = (1 << 64) - 1


class SplitMix64:
    """Zufallsgenerator nach der SplitMix64-Konvention (Vigna); gleicher Seed, gleicher Strom."""

    def __init__(self, seed: int):
        self.state = seed & MASK

    def next(self) -> int:
        self.state = (self.state + 0x9E3779B97F4A7C15) & MASK
        z = self.state
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & MASK
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & MASK
        return z ^ (z >> 31)

    def below(self, k: int) -> int:
        """Gleichverteilte ganze Zahl in [0, k) (bis auf den vernachlässigbaren Rest der Modulo-Bildung)."""
        return self.next() % k

    def coin(self) -> bool:
        return bool(self.next() >> 63)
