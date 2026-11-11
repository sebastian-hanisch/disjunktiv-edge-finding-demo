"""Orakel-Tests des Mini-CP (DEMO-PLAYBOOK §12, ORACLE-PLAYBOOK §5): ein anderer Rechenweg als die Suche der Demo.

Orakel 1: Aufzählung. Alle semiaktiven Pläne (Einplanungsreihenfolgen) und alle Maschinenreihenfolgen (`dje_aufzaehlung`, getestet gegen die Handzahlen 216 / 132 / 8 / 4) liefern das Optimum.
Orakel 2: OR-Tools CP-SAT (NoOverlap), nur im Test-venv (`pytest.importorskip`), 20 Zufalls-Seeds je Größe.
Orakel 3: Solidität gegen die Aufzählung aller Pläne: jeder Plan mit Makespan höchstens H liegt nach jeder Stufe in den Fenstern; Eigenschaften (idempotent, monoton, Umnummerierung, Skalierung).
Im Repo laufen kleine Fassungen; die großen Läufe (Scratch, nicht im Repo) stehen in der README."""

import pytest

import dje_algorithm as A
import dje_aufzaehlung as Z
from dje_rng import SplitMix64
from dje_scenario import HANDBEISPIEL, as_instance, make_jobshop
from orakel import cpsat_optimum, makespan, optimum_aufzaehlung, semiaktive_plaene


def _jobs(inst):
    return [list(job) for job in inst.jobs]


def test_orakel_am_handbeispiel_von_hand():
    """Das Orakel zuerst am Handbeispiel: Optimum 8 (Aufzählung der Einplanungsreihenfolgen), und die Aufzählung der Maschinenreihenfolgen liefert 216 / 132 / 8 / 4."""
    assert optimum_aufzaehlung(_jobs(HANDBEISPIEL)) == 8
    az = Z.aufzaehlen(HANDBEISPIEL)
    assert (az.kombinationen, az.zulaessig, az.optimum, az.am_optimum) == (216, 132, 8, 4)
    assert cpsat_optimum(_jobs(HANDBEISPIEL)) == 8


@pytest.mark.parametrize("n_jobs, n_machines", [(3, 3), (2, 4), (4, 2), (3, 2)])
def test_loese_stimmt_mit_der_aufzaehlung_ueberein(n_jobs, n_machines):
    """40 feste Zufalls-Job-Shops je Form: bewiesenes Optimum aller Stufen = Optimum der Aufzählung aller semiaktiven Pläne = Optimum der Maschinenreihenfolgen."""
    for seed in range(40):
        inst = make_jobshop(n_jobs, n_machines, 500 + seed, 5)
        erwartet = optimum_aufzaehlung(_jobs(inst))
        for stufe in (0, 1, 2, 3):
            r = A.loese(inst, stufe)
            assert r.bewiesen and r.optimum == erwartet, (n_jobs, n_machines, seed, stufe)
            ok, grund = A.pruefe_plan(inst, r.plan)
            assert ok and A.makespan(inst, r.plan) == r.optimum, (seed, stufe, grund)
        if n_jobs * n_machines <= 8:
            assert Z.aufzaehlen(inst).optimum == erwartet, (n_jobs, n_machines, seed)


def test_aufzaehlung_der_maschinenreihenfolgen_stimmt_mit_der_einplanung_bei_4_x_3_ueberein():
    """4 Aufträge auf 3 Maschinen: 24^3 = 13.824 Kombinationen; Optimum gegen die zweite Aufzählung (semiaktive Pläne wären 369.600 Folgen, daher hier gegen CP-SAT)."""
    for seed in range(3):
        inst = make_jobshop(4, 3, 900 + seed, 4)
        az = Z.aufzaehlen(inst)
        assert az.kombinationen == 24 ** 3
        assert az.optimum == cpsat_optimum(_jobs(inst)), seed


@pytest.mark.parametrize("n, stufen", [(4, (0, 1, 2, 3)), (5, (1, 2, 3))])
def test_optimum_stimmt_mit_cpsat_ueberein(n, stufen):
    """CP-SAT (NoOverlap) auf 4 × 4 und 5 × 5, 20 Zufalls-Seeds; Stufe 0 auf 5 × 5 läuft im großen Scratch-Lauf mit."""
    for seed in range(20):
        inst = make_jobshop(n, n, 7000 + seed)
        ref = cpsat_optimum(_jobs(inst))
        for stufe in stufen:
            r = A.loese(inst, stufe)
            assert r.bewiesen and r.optimum == ref, (n, seed, stufe)


# ------------------------------------------------------------------------------------------------------------------------------------ Solidität
def _kleine_instanzen():
    return [make_jobshop(3, 3, 300 + s, 4) for s in range(12)] + [make_jobshop(2, 4, 400 + s, 5) for s in range(6)] + [HANDBEISPIEL]


def test_jeder_plan_liegt_nach_jeder_stufe_in_den_fenstern():
    """Solidität: Für H = Optimum, Optimum + 1, Optimum + 2 liegt jeder semiaktive Plan mit Makespan <= H nach der Propagation an der Wurzel in [est, lst];
    jede vom Paar-Test gesetzte Kante gilt in jedem dieser Pläne."""
    for inst in _kleine_instanzen():
        plaene = semiaktive_plaene(_jobs(inst))
        opt = min(makespan(_jobs(inst), p) for p in plaene)
        M = A.Modell(inst)
        for H in (opt, opt + 1, opt + 2):
            gueltig = [p for p in plaene if makespan(_jobs(inst), p) <= H]
            assert gueltig
            for stufe in (0, 1, 2, 3):
                r = A.fenster_nach_wurzel(inst, H, stufe)
                assert r is not None, (H, stufe)
                est, lst, kanten = r
                for p in gueltig:
                    assert all(est[o] <= p[o] <= lst[o] for o in range(M.n)), (H, stufe)
                    assert all(p[a] + M.d[a] <= p[b] for a, b in kanten), (H, stufe)


def test_horizont_optimum_minus_1_wird_von_jeder_stufe_bewiesen_und_optimum_nie_verworfen():
    for inst in _kleine_instanzen():
        opt = optimum_aufzaehlung(_jobs(inst))
        for stufe in (0, 1, 2, 3):
            kein = A.entscheide(inst, opt - 1, stufe)
            assert not kein.gefunden and not kein.abgebrochen
            gibt = A.entscheide(inst, opt, stufe)
            assert gibt.gefunden and A.pruefe_plan(inst, gibt.plan)[0]
            assert A.makespan(inst, gibt.plan) <= opt


def test_fenster_werden_mit_jeder_stufe_enger():
    """Fenster nach Stufe 2 ⊆ nach Stufe 1 ⊆ nach Stufe 0 (und Stufe 3 gleich Stufe 2), an der Wurzel bei H = Optimum + 1 auf 60 Instanzen."""
    for seed in range(60):
        inst = make_jobshop(3 + seed % 2, 3 + (seed // 2) % 2, 1100 + seed, 6)
        opt = A.loese(inst, 2).optimum
        fenster = [A.fenster_nach_wurzel(inst, opt + 1, s) for s in (0, 1, 2, 3)]
        assert all(f is not None for f in fenster)
        for weit, eng in ((0, 1), (1, 2)):
            assert all(fenster[eng][0][o] >= fenster[weit][0][o] and fenster[eng][1][o] <= fenster[weit][1][o] for o in range(len(fenster[0][0])))
        assert fenster[2][:2] == fenster[3][:2], seed


def test_propagation_ist_idempotent_und_monoton_im_horizont():
    for seed in range(30):
        inst = make_jobshop(4, 3, 1300 + seed, 6)
        M = A.Modell(inst)
        opt = A.loese(inst, 2).optimum
        for stufe in (0, 1, 2, 3):
            H = opt + 1
            est, lst, kanten = A.anfangsfenster(M, H)
            assert A.propagiere(M, est, lst, kanten, H, stufe, A.Zaehler()) is None
            e2, l2, k2 = list(est), list(lst), dict(kanten)
            assert A.propagiere(M, e2, l2, k2, H, stufe, A.Zaehler()) is None
            assert (e2, l2, set(k2)) == (est, lst, set(kanten))                       # idempotent
            est3, lst3, kanten3 = A.anfangsfenster(M, H + 3)
            assert A.propagiere(M, est3, lst3, kanten3, H + 3, stufe, A.Zaehler()) is None
            assert all(lst3[o] >= lst[o] and est3[o] <= est[o] for o in range(M.n))   # größerer Horizont: weitere Fenster


def test_umnummerierung_der_maschinen_aendert_das_optimum_nie():
    rng = SplitMix64(123)
    for seed in range(25):
        inst = make_jobshop(4, 4, 1500 + seed, 6)
        perm = list(range(4))
        for i in range(3, 0, -1):
            j = rng.below(i + 1)
            perm[i], perm[j] = perm[j], perm[i]
        umbenannt = as_instance([[(perm[m], d) for m, d in job] for job in inst.jobs])
        assert A.loese(inst, 2).optimum == A.loese(umbenannt, 2).optimum, seed


def test_skalieren_aller_dauern_skaliert_den_makespan():
    for seed in range(15):
        inst = make_jobshop(3, 3, 1700 + seed, 5)
        for c in (2, 3):
            skaliert = as_instance([[(m, c * d) for m, d in job] for job in inst.jobs])
            assert A.loese(skaliert, 2).optimum == c * A.loese(inst, 2).optimum, (seed, c)


def test_pflichtteil_ueberlappung_macht_den_paartest_unmoeglich():
    """Auf 10.000 Zufallsfenstern: überlappen die Pflichtteile zweier Operationen, ist weder „a vor b“ noch „b vor a“ möglich (der Paar-Test scheitert). Die Umkehrung gilt nicht."""
    rng = SplitMix64(2026)
    ueberlappung = ohne_ueberlappung_aber_unmoeglich = 0
    for _ in range(10000):
        da, db = 1 + rng.below(6), 1 + rng.below(6)
        ea, eb = rng.below(8), rng.below(8)
        la, lb = ea + rng.below(8), eb + rng.below(8)
        pa = (la, ea + da) if la < ea + da else None
        pb = (lb, eb + db) if lb < eb + db else None
        ab = ea + da <= lb
        ba = eb + db <= la
        if pa and pb and max(pa[0], pb[0]) < min(pa[1], pb[1]):
            ueberlappung += 1
            assert not ab and not ba, (ea, la, da, eb, lb, db)
        elif not ab and not ba:
            ohne_ueberlappung_aber_unmoeglich += 1
    assert ueberlappung > 100 and ohne_ueberlappung_aber_unmoeglich > 100       # beide Fälle kommen vor: die Umkehrung ist falsch


def test_randfaelle():
    """Ein Auftrag, eine Maschine, Dauer 1 überall, Horizont gleich der Summe aller Dauern, zwei Maschinen mit identischen Operationen."""
    ein_auftrag = as_instance([[(0, 2), (1, 3), (2, 1)]])
    assert [A.loese(ein_auftrag, s).optimum for s in (0, 1, 2, 3)] == [6] * 4
    eine_maschine = as_instance([[(0, 2)], [(0, 3)], [(0, 1)]])
    assert [A.loese(eine_maschine, s).optimum for s in (0, 1, 2, 3)] == [6] * 4
    einsen = as_instance([[(0, 1), (1, 1)], [(1, 1), (0, 1)], [(0, 1), (1, 1)]])
    assert optimum_aufzaehlung(_jobs(einsen)) == 3
    assert [A.loese(einsen, s).optimum for s in (0, 1, 2, 3)] == [3] * 4
    gleiche = as_instance([[(0, 2), (1, 2)], [(0, 2), (1, 2)]])                           # zwei Aufträge mit identischen Operationen
    assert optimum_aufzaehlung(_jobs(gleiche)) == 6 == A.loese(gleiche, 2).optimum
    summe = HANDBEISPIEL.total_duration                                                    # Horizont = Summe aller Dauern: immer lösbar
    assert A.entscheide(HANDBEISPIEL, summe, 0).gefunden
    for stufe in (0, 1, 2, 3):
        assert not A.entscheide(HANDBEISPIEL, 4, stufe).gefunden                           # Horizont kleiner als die längste Kette
        assert A.entscheide(HANDBEISPIEL, 4, stufe).z.knoten == 1


def test_aufzaehlung_wehrt_zu_grosse_instanzen_ab():
    assert Z.aufzaehlen(make_jobshop(6, 6, 1, 9)) is None
    assert Z.anzahl_kombinationen(make_jobshop(3, 3, 1, 9)) == 216


def test_orakel_vergleicht_wirklich_verschiedene_wege():
    """Das Orakel zählt andere Dinge als die Suche: für das Handbeispiel gibt es mehr semiaktive Pläne als eine Handvoll, und nicht alle sind optimal."""
    plaene = semiaktive_plaene(_jobs(HANDBEISPIEL))
    werte = sorted(makespan(_jobs(HANDBEISPIEL), p) for p in plaene)
    assert len(plaene) > 10 and werte[0] == 8 and werte[-1] > 8
