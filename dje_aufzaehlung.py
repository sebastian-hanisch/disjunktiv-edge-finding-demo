"""Aufzählung aller Maschinenreihenfolgen: der exakte, einfache Gegenentwurf zur Suche (nur für sehr kleine Instanzen).

Je Maschine wird jede Reihenfolge der Operationen betrachtet (Permutation); eine Kombination ist zulässig, wenn die Kanten (Auftragsketten plus Maschinenreihenfolgen)
keinen Kreis bilden, und ihr Makespan ist der längste Weg. Das ist die Zählung des Handbeispiels (216 Kombinationen, 132 zulässig, Optimum 8, 4 Kombinationen am Optimum)."""

import itertools
import math
from dataclasses import dataclass

from dje_scenario import Instance

MAX_KOMBINATIONEN = 300000


@dataclass(frozen=True)
class Aufzaehlung:
    kombinationen: int
    zulaessig: int
    optimum: int | None
    am_optimum: int
    beste_starts: tuple | None


def anzahl_kombinationen(inst: Instance) -> int:
    zaehler: dict[int, int] = {}
    for job in inst.jobs:
        for m, _ in job:
            zaehler[m] = zaehler.get(m, 0) + 1
    return math.prod(math.factorial(c) for c in zaehler.values())


def aufzaehlen(inst: Instance) -> Aufzaehlung | None:
    """Alle Kombinationen durchgehen; None, wenn es mehr als MAX_KOMBINATIONEN wären."""
    if anzahl_kombinationen(inst) > MAX_KOMBINATIONEN:
        return None
    ops = [(j, k) for j, job in enumerate(inst.jobs) for k in range(len(job))]
    d = {(j, k): inst.jobs[j][k][1] for j, k in ops}
    je_maschine: dict[int, list] = {}
    for j, k in ops:
        je_maschine.setdefault(inst.jobs[j][k][0], []).append((j, k))
    ketten = [((j, k), (j, k + 1)) for j, job in enumerate(inst.jobs) for k in range(len(job) - 1)]
    zulaessig = 0
    optimum, am_optimum, beste = None, 0, None
    for wahl in itertools.product(*[itertools.permutations(v) for v in je_maschine.values()]):
        kanten = list(ketten)
        for reihenfolge in wahl:
            kanten.extend(zip(reihenfolge, reihenfolge[1:]))
        nachf = {o: [] for o in ops}
        grad = {o: 0 for o in ops}
        for a, b in kanten:
            nachf[a].append(b)
            grad[b] += 1
        start = {o: 0 for o in ops}
        bereit = [o for o in ops if grad[o] == 0]
        gesehen = 0
        while bereit:
            u = bereit.pop()
            gesehen += 1
            for w in nachf[u]:
                start[w] = max(start[w], start[u] + d[u])
                grad[w] -= 1
                if grad[w] == 0:
                    bereit.append(w)
        if gesehen < len(ops):
            continue
        zulaessig += 1
        cmax = max(start[o] + d[o] for o in ops)
        if optimum is None or cmax < optimum:
            optimum, am_optimum, beste = cmax, 1, tuple(start[o] for o in ops)
        elif cmax == optimum:
            am_optimum += 1
    return Aufzaehlung(anzahl_kombinationen(inst), zulaessig, optimum, am_optimum, beste)
