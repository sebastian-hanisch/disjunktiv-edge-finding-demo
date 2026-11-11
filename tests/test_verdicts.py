"""Verdikte an von Hand gesetzten Werten (DEMO-PLAYBOOK §12): jede Zahl im Text und jede Schwelle der Art steht hier.

Ein Verdikt ist eine reine Funktion (Art, Text) und bekommt Zeilen, nicht Seeds."""

import dje_algorithm as A
import dje_evaluation as ev


def _row(stufe, median, p90, maximum, abbrueche=0, n=10):
    return {"stufe": stufe, "n": n, "median": median, "p90": p90, "max": maximum, "abbrueche": abbrueche, "summe": 0}


def test_verdict_handbeispiel_beweis_und_loesung():
    kind, text = ev.verdict_handbeispiel(7, 2, {0: (17, 9, False), 1: (3, 2, False), 2: (1, 1, False)})
    assert kind == "success"
    assert "Es gibt keinen Plan mit Makespan höchstens 7" in text and "in 1 Knoten (Fehlschläge: 1)" in text and "Stufe 0: 17, Stufe 1: 3, Stufe 2: 1" in text
    kind, text = ev.verdict_handbeispiel(8, 1, {0: (10, 0, True), 1: (2, 0, True), 2: (2, 0, True)})
    assert kind == "info" and "findet einen Plan mit Makespan höchstens 8" in text and "auf Stufe 1 braucht sie dafür 2 Knoten (Fehlschläge: 0)" in text


def test_verdict_stufen_nennt_median_und_tail_getrennt():
    rows = [_row(0, 200, 400, 1200), _row(1, 40, 90, 100), _row(2, 30, 60, 95)]
    kind, text = ev.verdict_stufen(rows, "5x5")
    assert kind == "success"
    assert "5x5 (10 feste Instanzen)" in text and "im Median 200 Knoten" in text and "mit Paar-Test 40 (5,0-fach weniger)" in text and "mit Edge-Finding 30" in text
    assert "spart im Median 25 % der Knoten des Paar-Tests (Bezug: Stufe 1)" in text                      # (40 - 30) / 40
    assert "Maximum 1.200 / 100 / 95 Knoten, 90-%-Wert 400 / 90 / 60" in text
    assert "brachen" not in text


def test_verdict_stufen_schwelle_faktor_2_ist_inklusive():
    assert ev.verdict_stufen([_row(0, 80, 1, 1), _row(1, 40, 1, 1), _row(2, 40, 1, 1)], "x")[0] == "success"     # genau Faktor 2
    kind, text = ev.verdict_stufen([_row(0, 79, 1, 1), _row(1, 40, 1, 1), _row(2, 40, 1, 1)], "x")                # Faktor 1,975
    assert kind == "info" and "spart Edge-Finding hier nichts" in text


def test_verdict_stufen_gleicher_median_und_schlechterer_median():
    assert "Im Median spart Edge-Finding hier nichts" in ev.verdict_stufen([_row(0, 100, 1, 1), _row(1, 30, 1, 1), _row(2, 30, 1, 1)], "x")[1]
    assert "braucht Edge-Finding mehr Knoten als der Paar-Test" in ev.verdict_stufen([_row(0, 100, 1, 1), _row(1, 30, 1, 1), _row(2, 31, 1, 1)], "x")[1]


def test_verdict_stufen_nennt_abbrueche_als_untere_schranken():
    rows = [_row(0, 100, 1, 1, abbrueche=2), _row(1, 30, 1, 1, abbrueche=1), _row(2, 30, 1, 1)]
    text = ev.verdict_stufen(rows, "x")[1]
    assert "3 Läufe brachen am Knotenbudget ab; ihre Zahlen sind untere Schranken." in text


def _ergebnis(opt, bewiesen, knoten):
    z = A.Zaehler(knoten=knoten)
    return A.Ergebnis(opt, bewiesen, None, opt, z)


def test_verdict_einzel_alle_zweige():
    erg = {0: _ergebnis(35, True, 37), 1: _ergebnis(35, True, 1), 2: _ergebnis(35, True, 1)}
    kind, text = ev.verdict_einzel(erg, 20000)
    assert kind == "info"
    assert "Optimaler Makespan 35, bewiesen von 3 der 3 Stufen" in text and "Stufe 0: 37 Knoten; Stufe 1: 1 Knoten; Stufe 2: 1 Knoten" in text and "Einzelinstanz, kein Median" in text
    assert "Stufe 0 braucht hier 37,0-mal so viele Knoten wie Stufe 1" in text and "Edge-Finding spart auf dieser Instanz nichts" in text
    erg2 = {0: _ergebnis(40, False, 20000), 1: _ergebnis(38, False, 20000), 2: _ergebnis(37, False, 20000)}
    text2 = ev.verdict_einzel(erg2, 20000)[1]
    assert "Keine Stufe beweist das Optimum innerhalb von 20.000 Knoten; der beste gefundene Makespan ist 37" in text2 and text2.count("Abbruch am Budget, untere Schranke") == 3
    assert "mal so viele" not in text2 and "spart auf dieser Instanz nichts" not in text2
    erg3 = {0: _ergebnis(35, True, 37), 1: _ergebnis(36, True, 1)}
    kind3, text3 = ev.verdict_einzel(erg3, 100)
    assert kind3 == "error" and "Widerspruch" in text3


def _tail(bewiesen1):
    return {"gewaehlt": 12, "budget": 100000, "scan_seeds": list(range(60)), "scan_budget_stufe1": 20000, "scan": [{"abbruch1": i == 0} for i in range(60)],
            "stufen": {"1": {"knoten": 100000 if not bewiesen1 else 3000, "bewiesen": bewiesen1, "optimum": 75}, "2": {"knoten": 285, "bewiesen": True, "optimum": 75}}}


def _reihe8():
    return {"stufen": [1, 2], "instanzen": [{"seed": i, "optimum_cpsat": 5, "stufen": {"1": {"knoten": k1, "bewiesen": True}, "2": {"knoten": k2, "bewiesen": True}}}
                                             for i, (k1, k2) in enumerate([(900, 600), (800, 500), (1000, 700)])]}


def test_verdict_tail_abbruch_und_beweis():
    kind, text = ev.verdict_tail(_tail(False), _reihe8())
    assert kind == "info"
    assert "Zufalls-Seed 12" in text and "größter Abstand unter 60 Seeds" in text and "Stufe 1 bricht am Budget von 100.000 Knoten ab (untere Schranke)" in text
    assert "Stufe 2 beweist das Optimum 75 in 285 Knoten" in text and "Im Median der 3 Seeds der 8 × 8-Messreihe sind es 900 gegen 600 Knoten" in text
    assert "Budget von 20.000 Knoten in 1 von 60 Seeds" in text
    assert "beweist das Optimum 75 in 3.000 Knoten, Stufe 2 in 285" in ev.verdict_tail(_tail(True), _reihe8())[1]


def _horizont(b1, b2, l1, l2):
    def e(k):
        return {"knoten": k, "abgebrochen": False}
    return {"5x5": {"instanzen": [{"beweis": {"0": e(999), "1": e(b1), "2": e(b2)}, "loesung": {"0": e(999), "1": e(l1), "2": e(l2)}}]}}


def test_verdict_horizont_drei_zweige():
    text = ev.verdict_horizont(_horizont(40, 14, 78, 55), "5x5")[1]
    assert "5 × 5, 1 feste Instanzen" in text and "Beweis bei Horizont = Optimum − 1: 40 gegen 14 (65 % weniger mit Edge-Finding)" in text
    assert "erste Lösung bei Horizont = Optimum: 78 gegen 55 (29 % weniger)" in text and "beim Beweis höher als bei der Lösung" in text
    assert "bei der Lösung höher als beim Beweis" in ev.verdict_horizont(_horizont(40, 38, 78, 55), "5x5")[1]
    assert "in beiden Fassungen gleich" in ev.verdict_horizont(_horizont(40, 20, 80, 40), "5x5")[1]               # beide 50 %


def test_verdict_baum_success_und_info():
    reihen = {"a": _reihe_gleich(10, 10), "b": _reihe_gleich(20, 20)}
    baum = {"faelle": 4000, "gleich": 4000}
    kind, text = ev.verdict_baum(reihen, baum)
    assert kind == "success" and "in 30 von 30 Instanzen" in text and "in 4.000 Fällen" in text and "auf 4.000 zufälligen" in text.replace("Auf", "auf")
    assert "ob er je Durchlauf schneller ist, misst diese Demo nicht" in text
    assert ev.verdict_baum({"a": _reihe_gleich(10, 9)}, baum)[0] == "info"
    assert ev.verdict_baum(reihen, {"faelle": 4000, "gleich": 3999})[0] == "info"


def _reihe_gleich(n, gleich):
    inst = []
    for i in range(n):
        k = 5
        inst.append({"seed": i, "stufen": {"2": {"knoten": k, "bewiesen": True}, "3": {"knoten": k if i < gleich else k + 1, "bewiesen": True}}})
    return {"stufen": [2, 3], "instanzen": inst}
