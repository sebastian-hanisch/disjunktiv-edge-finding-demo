"""Die vorgerechneten Messreihen (`dje_sweeps.json`, Messskript tools/messung_sweeps.py) gegen eine Neuberechnung: dieselben Knotenzahlen, dasselbe Optimum wie CP-SAT.

Im Repo wird der kleinere Teil nachgerechnet (5 × 5 und 6 × 6 alle Stufen, 8 × 8 die Instanzen mit höchstens 800 Knoten, der eingefrorene Tail mit Stufe 2); der Seed-Scan,
die größeren 8 × 8-Läufe und Stufe 1 des eingefrorenen Falls (100.000 Knoten) laufen nur im Messskript."""

import dje_algorithm as A
import dje_constants as C
import dje_evaluation as ev
from dje_scenario import make_jobshop

DATA = ev.lade_sweeps()


def test_meta_nennt_skript_und_versionen():
    meta = DATA["meta"]
    assert meta["skript"] == C.MEASURE_SCRIPT and meta["ortools"] and meta["python"]


def test_die_seeds_und_budgets_der_reihen_sind_die_der_konstanten():
    r = DATA["reihen"]
    assert r["5x5"]["seeds"] == list(C.SWEEP_5X5_SEEDS) and r["6x6"]["seeds"] == list(C.SWEEP_6X6_SEEDS) and r["8x8"]["seeds"] == list(C.SWEEP_8X8_SEEDS)
    assert (r["5x5"]["budget"], r["6x6"]["budget"], r["8x8"]["budget"]) == (C.SWEEP_BUDGET_SMALL, C.SWEEP_BUDGET_SMALL, C.SWEEP_BUDGET_8X8)
    assert r["5x5"]["stufen"] == [0, 1, 2, 3] and r["8x8"]["stufen"] == [1, 2, 3]


def test_5x5_knoten_stimmen_mit_der_neuberechnung_ueberein():
    reihe = DATA["reihen"]["5x5"]
    for z in reihe["instanzen"]:
        inst = make_jobshop(5, 5, z["seed"])
        for s in (0, 1, 2, 3):
            r = A.loese(inst, s, budget=reihe["budget"])
            e = z["stufen"][str(s)]
            assert (r.z.knoten, r.z.fehlschlaege, r.optimum, r.bewiesen) == (e["knoten"], e["fehlschlaege"], e["optimum"], e["bewiesen"]), (z["seed"], s)


def test_6x6_knoten_aller_stufen_stimmen_mit_der_neuberechnung_ueberein():
    reihe = DATA["reihen"]["6x6"]
    for z in reihe["instanzen"]:
        inst = make_jobshop(6, 6, z["seed"])
        for s in (0, 1, 2, 3):
            r = A.loese(inst, s, budget=reihe["budget"])
            e = z["stufen"][str(s)]
            assert (r.z.knoten, r.z.ef_verengungen, r.z.kanten_paar) == (e["knoten"], e["ef_verengungen"], e["kanten_paar"]), (z["seed"], s)


def test_8x8_instanzen_bis_800_knoten_stimmen_mit_der_neuberechnung_ueberein():
    """Je Stufe die Instanzen mit höchstens 800 Knoten (die größeren laufen nur im Messskript: 8 × 8 kostet rund 3 Millisekunden je Knoten)."""
    reihe = DATA["reihen"]["8x8"]
    pruefte = {1: 0, 2: 0}
    for z in reihe["instanzen"]:
        inst = make_jobshop(8, 8, z["seed"])
        for s in (1, 2):
            if z["stufen"][str(s)]["knoten"] <= 800:
                assert A.loese(inst, s, budget=reihe["budget"]).z.knoten == z["stufen"][str(s)]["knoten"], (z["seed"], s)
                pruefte[s] += 1
    assert pruefte == {1: 5, 2: 7}


def test_alle_bewiesenen_optima_stimmen_mit_cpsat_ueberein():
    for key, reihe in DATA["reihen"].items():
        ok, gesamt = ev.optima_stimmen(reihe)
        assert ok == gesamt > 0, key


def test_der_eingefrorene_tail_stufe_2_stimmt_mit_der_neuberechnung_ueberein():
    sw = DATA["tail"]
    inst = ev.tail_instanz(sw)
    assert inst == make_jobshop(8, 8, sw["gewaehlt"])
    r = A.loese(inst, 2, budget=sw["budget"])
    assert (r.z.knoten, r.optimum, r.bewiesen) == (sw["stufen"]["2"]["knoten"], sw["stufen"]["2"]["optimum"], True)
    assert r.optimum == sw["optimum_cpsat"]
    assert not sw["stufen"]["1"]["bewiesen"] and sw["stufen"]["1"]["knoten"] == sw["budget"]          # Stufe 1 bricht am Budget ab
    assert sw["gewaehlt"] in sw["scan_seeds"] and len(sw["scan"]) == len(sw["scan_seeds"])


def test_horizont_beweis_und_loesung_haengen_am_optimum_und_stimmen_stichprobenweise():
    for key, n in (("5x5", 5), ("6x6", 6)):
        for eintrag in DATA["horizont"][key]["instanzen"][:3]:
            inst = make_jobshop(n, n, eintrag["seed"])
            for s in (1, 2):
                b = A.entscheide(inst, eintrag["optimum"] - 1, s)
                l = A.entscheide(inst, eintrag["optimum"], s)
                assert not b.gefunden and l.gefunden
                assert (b.z.knoten, l.z.knoten) == (eintrag["beweis"][str(s)]["knoten"], eintrag["loesung"][str(s)]["knoten"])


def test_der_baum_filter_lauf_hat_die_dokumentierten_zaehlungen():
    b = DATA["baum_filter"]
    assert b["faelle"] == 4000 and b["gleich"] == b["faelle"]
    assert b["fehlschlag_faelle"] + b["fenster_faelle"] == b["faelle"]
    assert b["fehlschlag_gleich"] == b["fehlschlag_faelle"] and b["fenster_gleich"] == b["fenster_faelle"]
