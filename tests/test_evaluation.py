"""Auswertung (`dje_evaluation`): 90-%-Wert, Statistik je Stufe, Zählungen über die Messreihen, Live-Vergleich. Handwerte als Rechnung."""

import dje_algorithm as A
import dje_evaluation as ev
from dje_scenario import make_jobshop


def _reihe(knoten_je_instanz, abbruch=(), opt=(10, 20, 30, 40, 50)):
    """Mini-Messreihe: knoten_je_instanz[s] ist die Liste der Knotenzahlen der Stufe s."""
    stufen = list(range(len(knoten_je_instanz)))
    n = len(knoten_je_instanz[0])
    inst = []
    for i in range(n):
        eintrag = {"seed": i, "optimum_cpsat": opt[i % len(opt)], "stufen": {}}
        for s in stufen:
            eintrag["stufen"][str(s)] = {"knoten": knoten_je_instanz[s][i], "bewiesen": (s, i) not in abbruch, "optimum": opt[i % len(opt)], "fehlschlaege": knoten_je_instanz[s][i] // 2,
                                         "fehl_vorrang": knoten_je_instanz[s][i] // 2, "fehl_paar": 0, "fehl_edge": 0, "fehl_wurzel": 0, "kanten_paar": 1, "ef_verengungen": 2, "runden": 3}
        inst.append(eintrag)
    return {"stufen": stufen, "instanzen": inst}


def test_p90_ist_der_wert_an_stelle_ceil_0_9_n():
    """n = 10: ceil(9) = 9, der neunte der aufsteigend sortierten Werte; n = 20: der 18.; n = 1: der einzige Wert."""
    assert ev.p90(list(range(10, 0, -1))) == 9
    assert ev.p90(list(range(1, 21))) == 18
    assert ev.p90([7]) == 7
    assert ev.p90([1, 1, 1, 100]) == 100        # n = 4: ceil(3,6) = 4


def test_statistik_median_p90_max_abbrueche():
    r = _reihe([[4, 2, 10, 6], [1, 1, 1, 1]], abbruch={(0, 2)})
    s0, s1 = ev.statistik(r)
    assert (s0["median"], s0["p90"], s0["max"], s0["abbrueche"], s0["n"], s0["summe"]) == (5.0, 10, 10, 1, 4, 22)    # Median (4 + 6) / 2
    assert (s1["median"], s1["max"], s1["abbrueche"]) == (1, 1, 0)


def test_gleiche_knoten_und_optima():
    r = _reihe([[1, 2, 3], [1, 5, 3]])
    assert ev.gleiche_knoten(r, 0, 1) == (2, 3)
    assert ev.optima_stimmen(r) == (6, 6)
    r["instanzen"][0]["stufen"]["1"]["optimum"] = 99
    assert ev.optima_stimmen(r) == (5, 6)
    r["instanzen"][0]["stufen"]["1"]["bewiesen"] = False       # nicht bewiesene Optima zählen nicht
    assert ev.optima_stimmen(r) == (5, 5)


def test_ursachen_summiert_ueber_instanzen():
    u = ev.ursachen(_reihe([[2, 4], [6, 8]]), stufen=(0, 1))
    assert u[0]["knoten"] == 6 and u[0]["fehlschlaege"] == 3 and u[1]["knoten"] == 14 and u[1]["fehlschlaege"] == 7
    assert u[1]["kanten_paar"] == 2 and u[1]["ef_verengungen"] == 4 and u[1]["runden"] == 6


def test_horizont_statistik():
    h = {"5x5": {"instanzen": [
        {"beweis": {"0": {"knoten": 10, "abgebrochen": False}, "1": {"knoten": 4, "abgebrochen": False}}, "loesung": {"0": {"knoten": 6, "abgebrochen": False}, "1": {"knoten": 2, "abgebrochen": True}}},
        {"beweis": {"0": {"knoten": 20, "abgebrochen": False}, "1": {"knoten": 8, "abgebrochen": False}}, "loesung": {"0": {"knoten": 8, "abgebrochen": False}, "1": {"knoten": 4, "abgebrochen": False}}}]}}
    b = ev.horizont_statistik(h, "5x5", "beweis", stufen=(0, 1))
    assert (b[0]["median"], b[0]["summe"], b[1]["summe"]) == (15, 30, 12)
    l = ev.horizont_statistik(h, "5x5", "loesung", stufen=(0, 1))
    assert l[1]["abbrueche"] == 1 and l[0]["max"] == 8


def test_zahlenformat_deutsch():
    assert ev._zahl(1234567) == "1.234.567" and ev._zahl(52.5) == "52,5" and ev._zahl(4.0) == "4" and ev._zahl(1500.5) == "1.500,5"


def test_live_vergleich_ist_dieselbe_suche_und_ohne_widerspruch():
    s = ev.Settings(jobs=3, machines=3, dmax=4, seed=5, budget=5000)
    erg = ev.live_vergleich(s)
    inst = make_jobshop(3, 3, 5, 4)
    assert erg[2].z.knoten == A.loese(inst, 2, budget=5000).z.knoten
    assert not ev.widerspruch_im_optimum(erg)
    erg[1] = A.Ergebnis(erg[1].optimum + 1, True, erg[1].plan, erg[1].start_schranke, erg[1].z)
    assert ev.widerspruch_im_optimum(erg)
    erg[1] = A.Ergebnis(erg[1].optimum + 1, False, erg[1].plan, erg[1].start_schranke, erg[1].z)    # ein nicht bewiesener Wert ist kein Widerspruch
    assert not ev.widerspruch_im_optimum(erg)


def test_tail_abbrueche_zaehlt_die_scan_zeilen():
    sw = {"scan": [{"abbruch1": True}, {"abbruch1": False}, {"abbruch1": False}]}
    assert ev.tail_abbrueche(sw) == (1, 3)
