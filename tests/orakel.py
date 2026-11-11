"""Unabhängige Referenzen für die Orakel-Tests (kein Code aus dem Mini-CP, kein Import aus dje_algorithm).

- `semiaktive_plaene`: alle semiaktiven Pläne durch Aufzählung der Einplanungsreihenfolgen (jede Operation so früh wie möglich); das Optimum aller Pläne liegt darunter.
- `cpsat_optimum`: OR-Tools CP-SAT mit NoOverlap (nur im Test-venv).
- `alle_loesungen_einzelmaschine`: alle ganzzahligen Startzeiten ohne Überlappung innerhalb vorgegebener Fenster.
- `ect`, `edge_finding_mengen`: Edge-Finding und Überlast in der Mengenform durch Aufzählung aller Teilmengen Ω (Regel: ECT(Ω ∪ {i}) > lct(Ω) ⇒ est_i ≥ ECT(Ω))."""

import itertools

import pytest


def semiaktive_plaene(jobs):
    """Alle semiaktiven Pläne als Menge von Startzeit-Tupeln (in der Reihenfolge Auftrag 0 Operation 0, Auftrag 0 Operation 1, ...)."""
    n_jobs = len(jobs)
    offsets, t = [], 0
    for job in jobs:
        offsets.append(t)
        t += len(job)
    n_ops = t
    plaene = set()
    nxt = [0] * n_jobs
    job_ready = [0] * n_jobs
    mach_ready: dict[int, int] = {}
    starts = [0] * n_ops

    def rec(placed):
        if placed == n_ops:
            plaene.add(tuple(starts))
            return
        for j in range(n_jobs):
            k = nxt[j]
            if k < len(jobs[j]):
                m, d = jobs[j][k]
                alt_m, alt_j = mach_ready.get(m, 0), job_ready[j]
                st = max(alt_j, alt_m)
                starts[offsets[j] + k] = st
                nxt[j] += 1
                job_ready[j] = mach_ready[m] = st + d
                rec(placed + 1)
                nxt[j] -= 1
                job_ready[j], mach_ready[m] = alt_j, alt_m

    rec(0)
    return plaene


def makespan(jobs, starts):
    out, i = 0, 0
    for job in jobs:
        for _, d in job:
            out = max(out, starts[i] + d)
            i += 1
    return out


def optimum_aufzaehlung(jobs):
    return min(makespan(jobs, p) for p in semiaktive_plaene(jobs))


def cpsat_optimum(jobs):
    cp_model = pytest.importorskip("ortools.sat.python.cp_model")
    horizon = sum(d for job in jobs for _, d in job)
    m = cp_model.CpModel()
    starts, per_machine = {}, {}
    for j, job in enumerate(jobs):
        for k, (mach, d) in enumerate(job):
            s = m.NewIntVar(0, horizon, f"s{j}_{k}")
            starts[j, k] = s
            per_machine.setdefault(mach, []).append(m.NewIntervalVar(s, d, s + d, f"i{j}_{k}"))
            if k:
                m.Add(s >= starts[j, k - 1] + job[k - 1][1])
    for ivs in per_machine.values():
        m.AddNoOverlap(ivs)
    cmax = m.NewIntVar(0, horizon, "cmax")
    for j, job in enumerate(jobs):
        m.Add(cmax >= starts[j, len(job) - 1] + job[-1][1])
    m.Minimize(cmax)
    solver = cp_model.CpSolver()
    solver.parameters.num_workers = 1
    solver.parameters.max_time_in_seconds = 60
    status = solver.Solve(m)
    assert status == cp_model.OPTIMAL
    return int(round(solver.ObjectiveValue()))


def alle_loesungen_einzelmaschine(est, lst, dauer):
    """Alle ganzzahligen Startzeiten s_i in [est_i, lst_i] ohne Überlappung (eine Maschine)."""
    loesungen = []
    for s in itertools.product(*[range(e, l + 1) for e, l in zip(est, lst)]):
        if all(s[a] + dauer[a] <= s[b] or s[b] + dauer[b] <= s[a] for a in range(len(s)) for b in range(a + 1, len(s))):
            loesungen.append(s)
    return loesungen


def ect(menge, est, dauer):
    """Früheste Fertigstellung einer Menge: max über Teilmengen S von (min est in S + Summe der Dauern in S), hier über alle nichtleeren Teilmengen aufgezählt."""
    best = None
    for r in range(1, len(menge) + 1):
        for s in itertools.combinations(menge, r):
            w = min(est[i] for i in s) + sum(dauer[i] for i in s)
            best = w if best is None else max(best, w)
    return best


def edge_finding_mengen(est, lct, dauer):
    """Ein Durchlauf der Mengenform auf est (Fenster fest, wie die Regel sie beschreibt): Überlast für jede Menge Ω; für i ∉ Ω mit ECT(Ω ∪ {i}) > lct(Ω) folgt est_i >= ECT(Ω).
    Rückgabe die neue est-Liste oder None bei Überlast."""
    n = len(est)
    neu = list(est)
    for r in range(1, n + 1):
        for omega in itertools.combinations(range(n), r):
            if ect(omega, est, dauer) > max(lct[i] for i in omega):
                return None
    for r in range(1, n):
        for omega in itertools.combinations(range(n), r):
            lct_omega = max(lct[i] for i in omega)
            e = ect(omega, est, dauer)
            for i in range(n):
                if i in omega:
                    continue
                if ect(omega + (i,), est, dauer) > lct_omega and e > neu[i]:
                    neu[i] = e
    return neu
