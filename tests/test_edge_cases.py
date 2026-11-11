"""Randfälle, an denen Kernroutinen erfahrungsgemäß brechen (DEMO-PLAYBOOK §12): n = 1, n = 2, Gleichstände, inklusive Grenzen, Budget auf der Grenze."""

import pytest

import dje_algorithm as A
from dje_scenario import as_instance, make_jobshop


def test_exactly_two_operations_on_one_machine():
    """Zwei Ein-Operations-Aufträge auf einer Maschine (Dauern 2 und 3): Optimum 5 in jeder Stufe, genau ein Paar, beide Reihenfolgen gleich gut."""
    inst = as_instance([[(0, 2)], [(0, 3)]])
    for stufe in (0, 1, 2, 3):
        r = A.loese(inst, stufe)
        assert r.optimum == 5 and r.bewiesen
    assert len(A.Modell(inst).paare) == 1


def test_single_operation_and_single_job():
    """n = 1: eine Operation, kein Paar, kein Edge-Finding-Aufruf (Maschinen mit weniger als zwei Operationen werden übersprungen); Optimum = Dauer."""
    inst = as_instance([[(0, 4)]])
    for stufe in (0, 1, 2, 3):
        r = A.loese(inst, stufe)
        assert (r.optimum, r.bewiesen, r.z.ef_aufrufe) == (4, True, 0)
    assert A.entscheide(inst, 4, 2).gefunden and not A.entscheide(inst, 3, 2).gefunden


def test_horizon_bounds_are_inclusive():
    """Horizont gleich der Kettenlänge ist zulässig (Fenster der Länge null), eins weniger nicht."""
    inst = as_instance([[(0, 2), (1, 3), (2, 1)]])
    for stufe in (0, 1, 2, 3):
        assert A.entscheide(inst, 6, stufe).gefunden
        assert not A.entscheide(inst, 5, stufe).gefunden


def test_budget_exactly_at_the_needed_node_count(hb):
    """Stufe 0 braucht für den Beweis 17 Knoten: mit Budget 17 ist er bewiesen, mit Budget 16 abgebrochen (Budget zählt Knoten, nicht „mehr als“)."""
    assert A.loese(hb, 0, budget=17).bewiesen
    r = A.loese(hb, 0, budget=16)
    assert not r.bewiesen and r.z.knoten == 16


def test_ties_in_the_branching_follow_the_documented_rule():
    """Zwei identische Aufträge auf einer Maschine: gleiche Spielraumsumme, gleiche est. Die Regel: Paar (0,0)-(1,0) (kleinstes Paar), das Paar mit früherem est zuerst, bei Gleichstand das Paar in der Reihenfolge (a, b)."""
    inst = as_instance([[(0, 2)], [(0, 2)]])
    e = A.entscheide(inst, 4, 0, protokoll=True)
    verzweigungen = [x.text for x in e.protokoll.ereignisse if x.art == "verzweigung"]
    assert e.gefunden and verzweigungen[0].startswith("Verzweigung auf das Paar (0,0),(1,0)")
    assert verzweigungen[0].endswith("zuerst (0,0) vor (1,0)")


def test_identical_operations_on_two_machines_are_symmetric():
    gleiche = as_instance([[(0, 2), (1, 2)], [(0, 2), (1, 2)]])
    spiegel = as_instance([[(1, 2), (0, 2)], [(1, 2), (0, 2)]])
    assert A.loese(gleiche, 2).optimum == A.loese(spiegel, 2).optimum == 6


def test_budget_zero_visits_no_node():
    """Budget 0: kein Knoten wird besucht, nichts ist bewiesen."""
    inst = make_jobshop(3, 3, 1, 4)
    r = A.loese(inst, 2, budget=0)
    assert not r.bewiesen and r.z.knoten == 0


def test_invalid_duration_is_rejected():
    with pytest.raises(ValueError):
        as_instance([[(0, 0)]])


def test_protocol_is_cut_at_the_limit():
    p = A.Protokoll(limit=3)
    for i in range(5):
        p.add("knoten", str(i), [0], [1])
    assert len(p.ereignisse) == 3 and p.abgeschnitten
