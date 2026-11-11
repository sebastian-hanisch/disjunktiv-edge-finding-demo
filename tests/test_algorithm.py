"""Das Mini-CP gegen Handrechnung am Handbeispiel (jede Einheit einzeln, DEMO-PLAYBOOK §1b) und gegen die Regeln der Stufen.

Operation (j, k) hat die Nummer 3 j + k (siehe `tests/conftest.py`). Die Erwartungswerte stehen als Rechnung da, nicht als abgeschriebenes Ergebnis."""

import pytest

import dje_algorithm as A
from dje_scenario import as_instance, make_jobshop, spt_plan

# Nummern der Operationen
O00, O01, O02, O10, O11, O12, O20, O21, O22 = range(9)


def _fenster(hb, H, stufe=0):
    M = A.Modell(hb)
    est, lst, kanten = A.anfangsfenster(M, H)
    z = A.Zaehler()
    ursache = A.propagiere(M, est, lst, kanten, H, stufe, z)
    return M, est, lst, kanten, z, ursache


# -------------------------------------------------------------------------------------------------------------------------------- Modell, Fenster
def test_vorlauf_und_rest_des_handbeispiels(hb):
    """Vorlauf = Summe der Dauern davor, Rest = Summe der Dauern ab der Operation (einschließlich): Auftrag 0 hat Dauern 2, 2, 1."""
    M = A.Modell(hb)
    assert M.vorlauf[:3] == [0, 2, 4] and M.rest[:3] == [5, 3, 1]
    assert M.vorlauf[3:6] == [0, 2, 3] and M.rest[3:6] == [5, 3, 2]     # Dauern 2, 1, 2
    assert M.vorlauf[6:] == [0, 2, 3] and M.rest[6:] == [5, 3, 2]       # Dauern 2, 1, 2


def test_fenster_bei_horizont_7_nach_reinem_vorrang(hb):
    """Von Hand: est = Vorlauf, lst = 7 - Rest. Tabelle der Operationen (0,0) ... (2,2)."""
    _, est, lst, _, _, ursache = _fenster(hb, 7, stufe=0)
    assert ursache is None
    assert est == [0, 2, 4, 0, 2, 3, 0, 2, 3]
    assert lst == [2, 4, 6, 2, 4, 5, 2, 4, 5]


def test_fenster_bei_horizont_8_sind_um_eins_weiter(hb):
    _, est, lst, _, _, _ = _fenster(hb, 8, stufe=0)
    assert est == [0, 2, 4, 0, 2, 3, 0, 2, 3] and lst == [3, 5, 7, 3, 5, 6, 3, 5, 6]


def test_horizont_kleiner_als_die_laengste_kette_scheitert_an_der_wurzel(hb):
    """Kette von Auftrag 0 hat Länge 2 + 2 + 1 = 5, die von Auftrag 1 und 2 je 5: Horizont 4 ist zu eng (est > lst)."""
    _, _, _, _, z, ursache = _fenster(hb, 4, stufe=0)
    assert ursache == "vorrang"
    assert A.entscheide(hb, 4, 0).z.knoten == 1


# ------------------------------------------------------------------------------------------------------------------------------------ Paar-Test
def test_paartest_setzt_die_vier_kanten_des_handbeispiels(hb):
    """Von Hand: 'a vor b' passt genau dann, wenn est_a + d_a <= lst_b. Bei H = 7 auf M0: (1,0) [0,2] d2 und (0,1) [2,4] d2: (0,1) vor (1,0) braucht 2 + 2 = 4 <= 2 (nein),
    (1,0) vor (0,1) braucht 0 + 2 = 2 <= 4 (ja) => Kante (1,0)->(0,1). Ebenso (1,0)->(2,1), (0,0)->(1,1), (2,0)->(1,1)."""
    M, est, lst, kanten, z, ursache = _fenster(hb, 7, stufe=1)
    assert ursache is None
    paarkanten = [k for k in kanten if k not in set(M.ketten)]
    assert set(paarkanten) == {(O10, O01), (O10, O21), (O00, O11), (O20, O11)}
    assert z.kanten_paar == 4
    assert est == [0, 2, 4, 0, 2, 3, 0, 2, 3] and lst == [2, 4, 6, 2, 4, 5, 2, 4, 5]     # nach den Kanten ändert sich kein Fenster


def test_paartest_meldet_fehlschlag_wenn_beide_richtungen_unmoeglich_sind():
    """Zwei Operationen der Dauer 3 auf einer Maschine, beide im Fenster [0, 1] (spätestes Ende 4): jede Richtung braucht 0 + 3 <= 1 (nein)."""
    inst = as_instance([[(0, 3)], [(0, 3)]])
    M = A.Modell(inst)
    est, lst = [0, 0], [1, 1]
    assert A._paartest(M, est, lst, {}, A.Zaehler(), None) is None


# ---------------------------------------------------------------------------------------------------------------------------------- Edge-Finding
def test_edge_finding_schluss_1_maschine_0(hb):
    """Von Hand (Plan, Maschine 0, H = 7): Ω = {(0,1) [2,4] d2, (2,1) [2,4] d1}: est_Ω = 2, lct_Ω = max(6, 5) = 6, d_Ω = 3.
    Für i = (1,0) [0,2] d2: est_Ω + d_Ω + d_i = 2 + 3 + 2 = 7 > max(6, lct_i = 4) = 6, also muss (1,0) vor beiden laufen: lst_i <= 6 - 3 - 2 = 1 (vorher 2)."""
    M, est, lst, kanten, _, _ = _fenster(hb, 7, stufe=1)
    z = A.Zaehler()
    prot = A.Protokoll()
    r = A._edge_finding(M, est, lst, z, prot)
    assert r is None                                                      # danach scheitert der Lauf an der Überlast auf Maschine 1
    assert lst[O10] == 1
    assert any("(1,0) vor allen aus {(0,1), (2,1)}: lst 2 → 1" in e.text for e in prot.ereignisse)


def test_ueberlast_auf_maschine_1_ist_der_beweis(hb):
    """Von Hand: (0,2) [4,6] d1, (1,2) [3,5] d2, (2,2) [3,5] d2: est der Menge 3, lct der Menge max(7, 7, 7) = 7, Summe der Dauern 5, und 3 + 5 = 8 > 7: Fehlschlag.
    Jedes Paar passt (z. B. (1,2) von 3 bis 5 und (2,2) von 5 bis 7), darum sieht der Paar-Test nichts."""
    M, est, lst, _, _, ursache = _fenster(hb, 7, stufe=1)
    assert ursache is None                                                # Stufe 1 hält den Wurzelzustand für zulässig
    prot = A.Protokoll()
    z = A.Zaehler()
    est2, lst2 = list(est), list(lst)
    assert A._edge_finding(M, est2, lst2, z, prot) is None
    assert any("Summe der Dauern 5 passt nicht in [3, 7] (Länge 4)" in e.text for e in prot.ereignisse)
    _, _, _, _, _, ursache2 = _fenster(hb, 7, stufe=2)
    assert ursache2 == "edge"


def test_jedes_paar_der_maschine_1_passt_aber_alle_drei_nicht(hb):
    """Die Rechnung hinter dem Beweis: Paare (est_a + d_a <= lst_b) passen alle, die Summe 5 > Länge 4 des Fensters [3, 7] nicht."""
    M, est, lst, _, _, _ = _fenster(hb, 7, stufe=0)
    ops = [O02, O12, O22]
    for a in ops:
        for b in ops:
            if a != b:
                assert est[a] + M.d[a] <= lst[b] or est[b] + M.d[b] <= lst[a]
    assert sum(M.d[o] for o in ops) == 5 and max(lst[o] + M.d[o] for o in ops) - min(est[o] for o in ops) == 4


# ------------------------------------------------------------------------------------------------------------------------------------- Suche
@pytest.mark.parametrize("stufe, knoten, fehlschlaege", [(0, 17, 9), (1, 3, 2), (2, 1, 1), (3, 1, 1)])
def test_suchknoten_bei_horizont_7_von_hand(hb, stufe, knoten, fehlschlaege):
    """Beweis: kein Plan mit Makespan <= 7. Knoten (Zustand nach Propagation, Wurzel eingeschlossen) und Fehlschläge je Stufe (Handbeispiel)."""
    e = A.entscheide(hb, 7, stufe)
    assert not e.gefunden and not e.abgebrochen and e.plan is None
    assert (e.z.knoten, e.z.fehlschlaege) == (knoten, fehlschlaege)


@pytest.mark.parametrize("stufe, knoten", [(0, 10), (1, 2), (2, 2), (3, 2)])
def test_suchknoten_bei_horizont_8_von_hand(hb, stufe, knoten):
    """Erste Lösung mit Makespan <= 8: keine Fehlschläge, ein gültiger Plan."""
    e = A.entscheide(hb, 8, stufe)
    assert e.gefunden and e.z.knoten == knoten and e.z.fehlschlaege == 0
    ok, grund = A.pruefe_plan(hb, e.plan)
    assert ok, grund
    assert A.makespan(hb, e.plan) <= 8


def test_stufen_weichen_voneinander_ab(hb):
    """Zweig-Test: Stufe 0, 1 und 2 haben auf dem Handbeispiel (H = 7) verschiedene Knotenzahlen 17, 3, 1; die Spalte ist nicht konstant."""
    zahlen = [A.entscheide(hb, 7, s).z.knoten for s in (0, 1, 2)]
    assert len(set(zahlen)) == 3 and zahlen == sorted(zahlen, reverse=True)


def test_fehlschlaege_werden_der_ursache_zugeordnet(hb):
    """Stufe 2 beweist H = 7 an der Wurzel durch Edge-Finding; Stufe 1 durch Paar-Test und Vorrang; Summe der Ursachen = Fehlschläge."""
    z2 = A.entscheide(hb, 7, 2).z
    assert (z2.fehl_edge, z2.fehl_paar, z2.fehl_vorrang, z2.fehl_wurzel) == (1, 0, 0, 1)
    z1 = A.entscheide(hb, 7, 1).z
    assert z1.fehl_vorrang + z1.fehl_paar + z1.fehl_edge == z1.fehlschlaege == 2
    for s in (0, 1, 2, 3):
        z = A.entscheide(hb, 7, s).z
        assert z.fehl_vorrang + z.fehl_paar + z.fehl_edge == z.fehlschlaege


def test_optimum_des_handbeispiels_ist_8_in_jeder_stufe(hb):
    """Startschranke 8 (Dispatching-Plan), also ein Beweis „nichts unter 8“; bewiesen von jeder Stufe, Plan ist die Startlösung."""
    for s in (0, 1, 2, 3):
        r = A.loese(hb, s)
        assert (r.optimum, r.bewiesen, r.start_schranke) == (8, True, 8)
        assert r.z.knoten == (17, 3, 1, 1)[s]


def test_wandernde_schranke_nach_jedem_plan(zwei_auftraege):
    """Mit der Startschranke 100 findet die Suche zuerst irgendeinen Plan und senkt H danach auf Makespan - 1, bis 5 bewiesen ist."""
    r = A.loese(zwei_auftraege, 2, start_schranke=100)
    assert r.optimum == 5 and r.bewiesen and r.z.blaetter >= 1
    ok, _ = A.pruefe_plan(zwei_auftraege, r.plan)
    assert ok and A.makespan(zwei_auftraege, r.plan) == 5


def test_budget_bricht_ab_und_meldet_untere_schranke(hb):
    r = A.loese(hb, 0, budget=5)
    assert not r.bewiesen and r.z.knoten == 5
    e = A.entscheide(hb, 7, 0, budget=5)
    assert e.abgebrochen and not e.gefunden and e.z.knoten == 5


def test_offene_paare_nach_der_wurzel_von_hand(hb):
    """Bei H = 8 setzt der Paar-Test nur (1,0)->(0,1) (siehe Handbeispiel); offen bleiben alle anderen Paare derselben Maschine, die keine Kette ordnet.
    Maschine 0: (0,1), (1,0), (2,1): Paare (0,1)-(1,0) [Kante], (0,1)-(2,1), (1,0)-(2,1) offen; Maschine 1: (0,2), (1,2), (2,2): 3 offen; Maschine 2: (0,0), (1,1), (2,0): 3 offen.
    (0,0) vor (0,1) vor ... : Ketten ordnen keine Paare derselben Maschine, weil jeder Auftrag jede Maschine nur einmal besucht."""
    M, est, lst, kanten, _, _ = _fenster(hb, 8, stufe=1)
    offen = A.offene_paare(M, kanten)
    assert len(offen) == 8                                                 # 9 Paare minus die Kante (1,0)->(0,1)
    assert (O01, O10) not in offen and (O10, O01) not in offen


# ------------------------------------------------------------------------------------------------------------------------------ Dispatching, Zufall
def test_dispatching_plan_von_hand(zwei_auftraege):
    """Beide Aufträge starten bei 0 (M0 und M1 frei): (0,0) auf M0 0-2, (1,0) auf M1 0-2; dann (0,1) auf M1 2-5 und (1,1) auf M0 2-5: Makespan 5."""
    cmax, starts = spt_plan(zwei_auftraege)
    assert cmax == 5 and starts == (0, 2, 0, 2)


def test_dispatching_plan_ist_zulaessig_und_obere_schranke():
    for seed in range(1, 31):
        inst = make_jobshop(4, 4, seed)
        cmax, starts = spt_plan(inst)
        ok, grund = A.pruefe_plan(inst, starts)
        assert ok, (seed, grund)
        assert A.makespan(inst, starts) == cmax


def test_zufallsinstanz_besucht_jede_maschine_einmal_und_ist_reproduzierbar():
    a = make_jobshop(5, 4, 11, 9)
    assert a == make_jobshop(5, 4, 11, 9) and a != make_jobshop(5, 4, 12, 9)
    for job in a.jobs:
        assert sorted(m for m, _ in job) == [0, 1, 2, 3]
        assert all(1 <= d <= 9 for _, d in job)
    assert all(1 <= d <= 3 for job in make_jobshop(6, 6, 5, 3).jobs for _, d in job)


# ---------------------------------------------------------------------------------------------------------------------------------------- Prüfer
def test_pruefer_erkennt_ueberlappung_und_kettenverletzung(zwei_auftraege):
    assert A.pruefe_plan(zwei_auftraege, (0, 2, 0, 2))[0]
    ok, grund = A.pruefe_plan(zwei_auftraege, (0, 1, 0, 2))             # (0,1) beginnt bei 1, aber (0,0) endet erst bei 2
    assert not ok and "beginnt vor dem Ende" in grund
    ok, grund = A.pruefe_plan(zwei_auftraege, (0, 3, 1, 3))             # (0,1) und (1,0) auf M1: 3-6 und 1-3 überlappen nicht; (1,1) auf M0 3-6 und (0,0) 0-2 auch nicht
    assert ok
    ok, grund = A.pruefe_plan(zwei_auftraege, (0, 2, 0, 2)[:3])
    assert not ok and grund == "falsche Länge"
    ok, grund = A.pruefe_plan(zwei_auftraege, (0, 2, 1, 3))             # (0,1) auf M1 2-5 und (1,0) auf M1 1-3 überlappen
    assert not ok and "überlappen" in grund


def test_pflichtteil_von_hand(hb):
    """Pflichtteil [lst, est + d): bei H = 8 hat (0,0) [0,3] d2 keinen (lst 3 >= est + d = 2); ein Fenster [0,1] mit d = 2 hat den Pflichtteil [1, 2)."""
    M, est, lst, _, _, _ = _fenster(hb, 8, stufe=0)
    assert A.pflichtteil(M, est, lst, O00) is None
    assert A.pflichtteil(M, [0] * 9, [9] * 3 + [1] + [9] * 5, O10) == (1, 2)
