"""Messskript für `dje_sweeps.json`: die vorgerechneten Messreihen der Demo (in der App „vorgerechnet, nicht live“).

Aufruf (aus dem Repo-Ordner, mit dem Test-venv, das OR-Tools für die Gegenprobe enthält):
    python tools/messung_sweeps.py [--nur 5x5,6x6,8x8,horizont,tail,baum]

Gemessen wird in Suchknoten, nie in Sekunden. Jedes Optimum wird mit OR-Tools CP-SAT (NoOverlap, ein Arbeiter) geprüft; OR-Tools gehört nur in `requirements-dev.txt`,
die App liest ausschließlich die JSON-Datei."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import dje_algorithm as A  # noqa: E402
import dje_constants as C  # noqa: E402
from dje_baum import durchlauf_est  # noqa: E402
from dje_rng import SplitMix64  # noqa: E402
from dje_scenario import Instance, make_jobshop, spt_plan  # noqa: E402

OUT = ROOT / C.SWEEPS_FILE
SCAN_SEEDS = tuple(range(1, 61))     # Seed-Scan für den Tail (8 x 8)
SCAN_BUDGET = C.TAIL_BUDGET
BAUM_FAELLE = 4000
BAUM_SEED = 20261110


def cpsat_optimum(inst: Instance) -> int:
    from ortools.sat.python import cp_model

    horizon = inst.total_duration
    m = cp_model.CpModel()
    starts, per_machine = {}, {}
    for j, job in enumerate(inst.jobs):
        for k, (mach, d) in enumerate(job):
            s = m.NewIntVar(0, horizon, f"s{j}_{k}")
            starts[j, k] = s
            per_machine.setdefault(mach, []).append(m.NewIntervalVar(s, d, s + d, f"i{j}_{k}"))
            if k:
                m.Add(s >= starts[j, k - 1] + job[k - 1][1])
    for ivs in per_machine.values():
        m.AddNoOverlap(ivs)
    cmax = m.NewIntVar(0, horizon, "cmax")
    for j, job in enumerate(inst.jobs):
        m.Add(cmax >= starts[j, len(job) - 1] + job[-1][1])
    m.Minimize(cmax)
    solver = cp_model.CpSolver()
    solver.parameters.num_workers = 1
    solver.parameters.max_time_in_seconds = 300
    status = solver.Solve(m)
    if status != cp_model.OPTIMAL:
        raise RuntimeError("CP-SAT hat das Optimum nicht bewiesen")
    return int(round(solver.ObjectiveValue()))


def lauf(inst: Instance, stufe: int, budget: int) -> dict:
    r = A.loese(inst, stufe, budget=budget)
    return {"optimum": r.optimum, "bewiesen": r.bewiesen, **r.z.als_dict()}


def messreihe(jobs: int, machines: int, seeds, stufen, budget: int) -> dict:
    zeilen = []
    for seed in seeds:
        inst = make_jobshop(jobs, machines, seed)
        opt = cpsat_optimum(inst)
        zeile = {"seed": seed, "start_schranke": spt_plan(inst)[0], "optimum_cpsat": opt, "stufen": {}}
        for s in stufen:
            zeile["stufen"][str(s)] = lauf(inst, s, budget)
        zeilen.append(zeile)
        print(f"{jobs}x{machines} Seed {seed}: Optimum {opt}, Knoten", {s: zeile['stufen'][str(s)]['knoten'] for s in stufen}, flush=True)
    return {"jobs": jobs, "machines": machines, "dmax": C.DMAX_DEFAULT, "seeds": list(seeds), "budget": budget, "stufen": list(stufen), "instanzen": zeilen}


def horizont(reihen: dict, stufen=(0, 1, 2)) -> dict:
    """Beweis bei H = Optimum - 1 und erste Lösung bei H = Optimum, je Stufe, auf den Instanzen der 5x5- und 6x6-Reihe."""
    out = {}
    for key in ("5x5", "6x6"):
        reihe = reihen[key]
        zeilen = []
        for z in reihe["instanzen"]:
            inst = make_jobshop(reihe["jobs"], reihe["machines"], z["seed"])
            opt = z["optimum_cpsat"]
            eintrag = {"seed": z["seed"], "optimum": opt, "beweis": {}, "loesung": {}}
            for s in stufen:
                e = A.entscheide(inst, opt - 1, s, budget=C.SWEEP_BUDGET_SMALL)
                f = A.entscheide(inst, opt, s, budget=C.SWEEP_BUDGET_SMALL)
                eintrag["beweis"][str(s)] = {"knoten": e.z.knoten, "fehlschlaege": e.z.fehlschlaege, "abgebrochen": e.abgebrochen, "gefunden": e.gefunden}
                eintrag["loesung"][str(s)] = {"knoten": f.z.knoten, "fehlschlaege": f.z.fehlschlaege, "abgebrochen": f.abgebrochen, "gefunden": f.gefunden}
            zeilen.append(eintrag)
        out[key] = {"stufen": list(stufen), "instanzen": zeilen}
        print("Horizont", key, "fertig", flush=True)
    return out


def tail() -> dict:
    """Seed-Scan 8 x 8: Stufe 1 mit Budget SCAN_BUDGET, Stufe 2 mit dem Budget der Reihe; der Fall mit dem größten Abstand wird eingefroren."""
    scan = []
    for seed in SCAN_SEEDS:
        inst = make_jobshop(8, 8, seed)
        r1 = A.loese(inst, 1, budget=SCAN_BUDGET)
        r2 = A.loese(inst, 2, budget=C.SWEEP_BUDGET_8X8)
        scan.append({"seed": seed, "knoten1": r1.z.knoten, "abbruch1": not r1.bewiesen, "knoten2": r2.z.knoten, "abbruch2": not r2.bewiesen, "optimum2": r2.optimum})
        print(f"Scan 8x8 Seed {seed}: Stufe 1 {r1.z.knoten}{' (Abbruch)' if not r1.bewiesen else ''}, Stufe 2 {r2.z.knoten}", flush=True)
    kandidaten = [z for z in scan if z["abbruch1"] and not z["abbruch2"]]
    wahl = max(kandidaten or scan, key=lambda z: (z["knoten1"] / max(z["knoten2"], 1), -z["seed"]))
    inst = make_jobshop(8, 8, wahl["seed"])
    opt = cpsat_optimum(inst)
    detail = {str(s): lauf(inst, s, C.SWEEP_BUDGET_8X8) for s in (1, 2, 3)}
    return {"scan_seeds": list(SCAN_SEEDS), "scan_budget_stufe1": SCAN_BUDGET, "scan": scan, "gewaehlt": wahl["seed"], "optimum_cpsat": opt, "budget": C.SWEEP_BUDGET_8X8, "stufen": detail,
            "jobs": [[list(op) for op in job] for job in inst.jobs]}


def baum_filter() -> dict:
    """Einzelmaschine: Fixpunkt der Intervallfassung gegen den Fixpunkt des Θ-Λ-Baums auf zufälligen Fenstern (3 bis 6 Operationen)."""
    import dje_baum as B

    rng = SplitMix64(BAUM_SEED)
    gleich, mit_loesung_gleich, fehl_gleich, faelle_loesung, faelle_fehl = 0, 0, 0, 0, 0
    for _ in range(BAUM_FAELLE):
        n = 3 + rng.below(4)
        inst = Instance(tuple(((0, 1 + rng.below(4)),) for _ in range(n)))
        M = A.Modell(inst)
        est0 = [rng.below(7) for _ in range(n)]
        lst0 = [est0[o] + rng.below(6) for o in range(n)]
        a = _fix_intervall(M, est0, lst0)
        b = _fix_baum(M, est0, lst0, B)
        if (a is None) == (b is None) and (a is None or a == b):
            gleich += 1
        if a is None:
            faelle_fehl += 1
            fehl_gleich += b is None
        else:
            faelle_loesung += 1
            mit_loesung_gleich += (b is not None and a == b)
    return {"faelle": BAUM_FAELLE, "seed": BAUM_SEED, "gleich": gleich, "fehlschlag_faelle": faelle_fehl, "fehlschlag_gleich": fehl_gleich,
            "fenster_faelle": faelle_loesung, "fenster_gleich": mit_loesung_gleich}


def _fix_intervall(M, est0, lst0):
    est, lst = list(est0), list(lst0)
    z = A.Zaehler()
    if any(est[o] > lst[o] for o in range(M.n)):
        return None
    while True:
        r = A._edge_finding(M, est, lst, z, None)
        if r is None:
            return None
        if not r:
            return tuple(est), tuple(lst)


def _fix_baum(M, est0, lst0, B):
    est, lst = list(est0), list(lst0)
    z = A.Zaehler()
    if any(est[o] > lst[o] for o in range(M.n)):
        return None
    while True:
        r = B.edge_finding_baum(M, est, lst, z, None)
        if r is None:
            return None
        if not r:
            return tuple(est), tuple(lst)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nur", default="5x5,6x6,8x8,horizont,tail,baum")
    args = ap.parse_args()
    teile = set(args.nur.split(","))
    daten = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    daten.setdefault("meta", {})
    from ortools import __version__ as ort_version

    daten["meta"] = {"skript": C.MEASURE_SCRIPT, "ortools": ort_version, "python": sys.version.split()[0],
                     "hinweis": "Knoten, nie Sekunden; Optima mit OR-Tools CP-SAT (ein Arbeiter) geprüft; vorgerechnet, nicht live"}
    reihen = daten.setdefault("reihen", {})
    def sichern():
        OUT.write_text(json.dumps(daten, ensure_ascii=False, indent=1), encoding="utf-8")

    if "5x5" in teile:
        reihen["5x5"] = messreihe(5, 5, C.SWEEP_5X5_SEEDS, (0, 1, 2, 3), C.SWEEP_BUDGET_SMALL)
        sichern()
    if "6x6" in teile:
        reihen["6x6"] = messreihe(6, 6, C.SWEEP_6X6_SEEDS, (0, 1, 2, 3), C.SWEEP_BUDGET_SMALL)
        sichern()
    if "8x8" in teile:
        reihen["8x8"] = messreihe(8, 8, C.SWEEP_8X8_SEEDS, (1, 2, 3), C.SWEEP_BUDGET_8X8)
        sichern()
    if "horizont" in teile:
        daten["horizont"] = horizont(reihen)
        sichern()
    if "tail" in teile:
        daten["tail"] = tail()
        sichern()
    if "baum" in teile:
        daten["baum_filter"] = baum_filter()
        sichern()
    print("geschrieben:", OUT)


if __name__ == "__main__":
    main()
