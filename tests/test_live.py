"""Live-Knöpfe: Zwischenspeicher und Fortschrittsanzeige (dje_live.py). Der Zwischenspeicher ändert keine Zahl: gespeichert gleich ungespeichert (bitgleich),
ein anderer Parameter kommt nie aus dem Speicher, ein zweiter Aufruf mit denselben Parametern rechnet nicht noch einmal."""

import dje_algorithm as A
import dje_constants as C
import dje_evaluation as ev
import dje_live as L
from dje_scenario import make_jobshop
from streamlit.testing.v1 import AppTest

KEY = (4, 4, 9, 7, 3000)      # Aufträge, Maschinen, größte Dauer, Zufalls-Seed, Knotenbudget


def _zaehler(monkeypatch):
    aufrufe = []
    echt = A.loese

    def zaehlend(inst, stufe, *args, **kwargs):
        aufrufe.append(stufe)
        return echt(inst, stufe, *args, **kwargs)

    monkeypatch.setattr(A, "loese", zaehlend)
    return aufrufe


def _gleich(a, b):
    return (a.optimum, a.bewiesen, a.z, a.plan) == (b.optimum, b.bewiesen, b.z, b.plan)


def test_stufe_gespeichert_gleich_ungespeichert_und_gleich_live_vergleich():
    L.stufe_lauf.clear()
    ref = ev.live_vergleich(ev.Settings(*KEY))
    # unabhängige Abschrift der früheren Fassung: eine Instanz, alle Stufen nacheinander
    inst = make_jobshop(KEY[0], KEY[1], KEY[3], KEY[2])
    alt = {s: A.loese(inst, s, budget=KEY[4]) for s in (0, 1, 2)}
    for s in (0, 1, 2):
        assert _gleich(ref[s], alt[s])
        assert _gleich(L.stufe_lauf(*KEY, s), alt[s]) and _gleich(L.stufe_lauf(*KEY, s), alt[s])
    assert all(_gleich(a, b) for a, b in zip(L.einzel_aus_speicher(KEY).values(), alt.values()))


def test_zweiter_aufruf_rechnet_nicht_anderer_parameter_schon(monkeypatch):
    L.stufe_lauf.clear()
    aufrufe = _zaehler(monkeypatch)
    L.stufe_lauf(*KEY, 1)
    L.stufe_lauf(*KEY, 1)
    assert aufrufe == [1]
    jobs, machines, dmax, seed, budget = KEY
    a = L.stufe_lauf(jobs, machines, dmax, seed + 1, budget, 1)          # anderer Zufalls-Seed
    b = L.stufe_lauf(jobs, machines, dmax, seed, budget, 2)              # andere Stufe
    c = L.stufe_lauf(jobs, machines, dmax, seed, budget // 2, 1)         # anderes Budget
    d = L.stufe_lauf(jobs, machines + 1, dmax, seed, budget, 1)          # andere Maschinenzahl
    assert len(aufrufe) == 5
    assert _gleich(a, ev.live_stufe(ev.Settings(jobs, machines, dmax, seed + 1, budget), 1)) and _gleich(b, ev.live_stufe(ev.Settings(*KEY), 2))
    assert _gleich(c, ev.live_stufe(ev.Settings(jobs, machines, dmax, seed, budget // 2), 1))
    assert _gleich(d, ev.live_stufe(ev.Settings(jobs, machines + 1, dmax, seed, budget), 1))


def test_tail_gespeichert_gleich_ungespeichert_und_anderes_budget_nicht_aus_dem_speicher(monkeypatch):
    L.tail_stufe.clear()
    sw = ev.lade_sweeps()["tail"]
    inst = ev.tail_instanz(sw)
    for s in L.TAIL_STUFEN:
        roh = A.loese(inst, s, budget=300)
        assert _gleich(L.tail_stufe(300, s), roh) and _gleich(L.tail_stufe(300, s), roh)
    aufrufe = _zaehler(monkeypatch)
    L.tail_stufe(300, 1)
    assert aufrufe == []                                                  # steht schon im Speicher
    anders = L.tail_stufe(301, 1)
    assert aufrufe == [1]                                                 # anderes Budget: neu gerechnet
    assert _gleich(anders, A.loese(inst, 1, budget=301))


def test_fortschrittsanzeige_liefert_ergebnisse_in_reihenfolge_und_ohne_fehler():
    def skript():
        import streamlit as st
        import dje_live as L

        erg = L.mit_fortschritt("Probe", [("eins", (1,)), ("zwei", (2,)), ("drei", (3,))], lambda x: x * 10)
        st.write(f"ergebnis {erg}")

    at = AppTest.from_function(skript)
    at.run(timeout=60)
    assert not at.exception, [str(e) for e in at.exception]
    assert any("ergebnis [10, 20, 30]" in m.value for m in at.markdown)
