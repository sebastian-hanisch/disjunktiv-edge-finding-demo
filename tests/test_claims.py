"""Jede Zahl der README in einem Test (DEMO-PLAYBOOK §4 und §11a): über dieselben Auswertungsfunktionen wie in der App, auf den festen Instanzen der Messreihen (`dje_sweeps.json`).

Die JSON-Datei selbst ist in `tests/test_sweeps.py` gegen eine Neuberechnung geprüft (5 × 5 und 6 × 6 alle Stufen, 8 × 8 Stufe 1 und 2); hier stehen die Zählungen, die der Text nennt.
Nicht im Test, sondern Messung der README: der große Lauf im Scratch-Ordner (siehe README, Abschnitt Verifikation) und die Zahlen der früheren Messung im Abschnitt „Korrekturen“."""

import dje_algorithm as A
import dje_aufzaehlung as Z
import dje_constants as C
import dje_evaluation as ev
from dje_rng import SplitMix64
from dje_scenario import HANDBEISPIEL

DATA = ev.lade_sweeps()
R = DATA["reihen"]


def _stat(key, stufen=(0, 1, 2)):
    return {r["stufe"]: r for r in ev.statistik(R[key], stufen)}


def test_claim_handbeispiel():
    az = Z.aufzaehlen(HANDBEISPIEL)
    assert (az.kombinationen, az.zulaessig, az.optimum, az.am_optimum) == (216, 132, 8, 4) and 6 ** 3 == 216
    h7 = {s: A.entscheide(HANDBEISPIEL, 7, s) for s in (0, 1, 2, 3)}
    assert [h7[s].z.knoten for s in (0, 1, 2, 3)] == [17, 3, 1, 1] and [h7[s].z.fehlschlaege for s in (0, 1, 2, 3)] == [9, 2, 1, 1]
    h8 = {s: A.entscheide(HANDBEISPIEL, 8, s) for s in (0, 1, 2, 3)}
    assert [h8[s].z.knoten for s in (0, 1, 2, 3)] == [10, 2, 2, 2] and all(h8[s].z.fehlschlaege == 0 and h8[s].gefunden for s in h8)


def test_claim_paar_test_median():
    s5, s6 = _stat("5x5"), _stat("6x6")
    assert (s5[0]["median"], s5[1]["median"]) == (198, 35) and (s6[0]["median"], s6[1]["median"]) == (1864, 151)
    assert round(s5[0]["median"] / s5[1]["median"], 1) == 5.7 and round(s6[0]["median"] / s6[1]["median"], 1) == 12.3
    assert (s5[0]["summe"], s5[1]["summe"], s6[0]["summe"], s6[1]["summe"]) == (3004, 404, 106886, 3340)
    assert (len(R["5x5"]["instanzen"]), len(R["6x6"]["instanzen"])) == (10, 20)


def test_claim_edge_finding_im_median():
    s5, s6, s8 = _stat("5x5"), _stat("6x6"), _stat("8x8", (1, 2))
    assert (s5[1]["median"], s5[2]["median"]) == (35, 35) and (s6[1]["median"], s6[2]["median"]) == (151, 138) and (s8[1]["median"], s8[2]["median"]) == (891, 599)
    assert round(100 * (151 - 138) / 151) == 9 and round(100 * (891 - 599) / 891) == 33
    assert [ev.gleiche_knoten(R[k], 1, 2) for k in ("5x5", "6x6", "8x8")] == [(4, 10), (5, 20), (0, 10)]
    weniger = [sum(1 for a, b in zip(ev.knoten(R[k], 1), ev.knoten(R[k], 2)) if b < a) for k in ("5x5", "6x6", "8x8")]
    mehr = [[(z["seed"], z["stufen"]["1"]["knoten"], z["stufen"]["2"]["knoten"]) for z in R[k]["instanzen"] if z["stufen"]["2"]["knoten"] > z["stufen"]["1"]["knoten"]] for k in ("5x5", "6x6", "8x8")]
    assert weniger == [6, 14, 10] and mehr == [[], [(9, 247, 251)], []]
    assert len(R["8x8"]["instanzen"]) == 10


def test_claim_tail():
    s5, s6, s8 = _stat("5x5"), _stat("6x6"), _stat("8x8", (1, 2))
    assert [(s5[s]["p90"], s5[s]["max"]) for s in (0, 1, 2)] == [(401, 1231), (97, 97), (79, 95)]
    assert [(s6[s]["p90"], s6[s]["max"]) for s in (0, 1, 2)] == [(12935, 43007), (259, 603), (249, 269)]
    assert [(s8[s]["p90"], s8[s]["max"]) for s in (1, 2)] == [(10753, 15615), (1107, 5521)]
    assert all(r["abbrueche"] == 0 for k in ("5x5", "6x6", "8x8") for r in ev.statistik(R[k]))      # keine Abbrüche in den Messreihen


def test_claim_tail_eingefroren():
    sw = DATA["tail"]
    assert sw["gewaehlt"] == 12 and len(sw["scan_seeds"]) == 60 and (sw["scan_seeds"][0], sw["scan_seeds"][-1]) == (1, 60)
    assert not sw["stufen"]["1"]["bewiesen"] and sw["stufen"]["1"]["knoten"] == 100000 == sw["budget"]
    assert (sw["stufen"]["2"]["knoten"], sw["stufen"]["3"]["knoten"], sw["stufen"]["2"]["optimum"]) == (285, 285, 75)
    assert ev.tail_abbrueche(sw) == (1, 60) and sw["scan_budget_stufe1"] == 20000
    assert sw["optimum_cpsat"] == 75
    assert ev.abbrueche(R["8x8"], 1) == 0                                                       # in den 10 Seeds der Reihe 8 x 8 bricht Stufe 1 bei 100.000 nie ab
    # größter Abstand unter den Scan-Seeds: das Verhältnis der Knoten ist beim gewählten Seed am größten
    verhaeltnis = {z["seed"]: z["knoten1"] / z["knoten2"] for z in sw["scan"]}
    assert max(verhaeltnis, key=verhaeltnis.get) == sw["gewaehlt"]


def test_claim_horizont():
    h = DATA["horizont"]
    def summe(key, art, s):
        return {r["stufe"]: r for r in ev.horizont_statistik(h, key, art)}[s]["summe"]
    assert (summe("5x5", "beweis", 1), summe("5x5", "beweis", 2)) == (40, 14) and (summe("6x6", "beweis", 1), summe("6x6", "beweis", 2)) == (710, 216)
    assert (summe("5x5", "loesung", 1), summe("5x5", "loesung", 2)) == (78, 55) and (summe("6x6", "loesung", 1), summe("6x6", "loesung", 2)) == (306, 221)
    assert [round(100 * (a - b) / a) for a, b in ((40, 14), (710, 216), (78, 55), (306, 221))] == [65, 70, 29, 28]
    for key in ("5x5", "6x6"):                                                                   # Beweis: größerer Gewinn als bei der Lösung
        gew_b = 1 - summe(key, "beweis", 2) / summe(key, "beweis", 1)
        gew_l = 1 - summe(key, "loesung", 2) / summe(key, "loesung", 1)
        assert gew_b > gew_l


def test_claim_ursachen():
    u = {r["stufe"]: r for r in ev.ursachen(R["6x6"])}
    assert (u[1]["fehlschlaege"], u[1]["vorrang"], u[1]["paar"], u[1]["edge"]) == (1552, 1286, 266, 0)
    assert (u[2]["fehlschlaege"], u[2]["vorrang"], u[2]["paar"], u[2]["edge"]) == (1265, 1143, 50, 72)
    assert u[1]["kanten_paar"] == 16703 and u[2]["ef_verengungen"] == 3600 and u[1]["ef_verengungen"] == 0
    assert u[2]["paar"] + u[2]["edge"] == 122 and u[1]["paar"] == 266


def test_claim_baum():
    gleich = [ev.gleiche_knoten(R[k], 2, 3) for k in ("5x5", "6x6", "8x8")]
    assert gleich == [(10, 10), (20, 20), (10, 10)] and sum(g for g, _ in gleich) == sum(n for _, n in gleich) == 40
    b = DATA["baum_filter"]
    assert (b["faelle"], b["gleich"], b["fenster_faelle"], b["fehlschlag_faelle"]) == (4000, 4000, 1333, 2667)
    assert sum(ev.optima_stimmen(R[k])[0] for k in R) == sum(ev.optima_stimmen(R[k])[1] for k in R) == 150


def test_claim_pflichtteil():
    rng = SplitMix64(2026)
    ueberlappung = ohne = 0
    for _ in range(10000):
        da, db = 1 + rng.below(6), 1 + rng.below(6)
        ea, eb = rng.below(8), rng.below(8)
        la, lb = ea + rng.below(8), eb + rng.below(8)
        pa = (la, ea + da) if la < ea + da else None
        pb = (lb, eb + db) if lb < eb + db else None
        ab, ba = ea + da <= lb, eb + db <= la
        if pa and pb and max(pa[0], pb[0]) < min(pa[1], pb[1]):
            ueberlappung += 1
            assert not ab and not ba
        elif not ab and not ba:
            ohne += 1
    assert (ueberlappung, ohne) == (805, 358)


def test_claim_presets():
    assert A.entscheide(HANDBEISPIEL, 7, 2).z.knoten == 1 and A.entscheide(HANDBEISPIEL, 7, 0).z.knoten == 17
    assert [A.entscheide(HANDBEISPIEL, 8, s).z.knoten for s in (0, 1, 2)] == [10, 2, 2]
    assert C.SWEEP_BUDGET_SMALL == 50000 and C.SWEEP_BUDGET_8X8 == 100000 and C.TAIL_BUDGET == 20000
