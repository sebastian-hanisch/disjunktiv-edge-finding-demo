"""Orakel-Tests für Edge-Finding in den drei Fassungen (Intervall, Θ-Λ-Baum, Mengenform per Teilmengen-Aufzählung); Erweiterung 11b.

T1  Ein Durchlauf des Θ-Λ-Baums gegen die Aufzählung aller Mengen Ω (Regel ECT(Ω ∪ {i}) > lct(Ω) ⇒ est_i ≥ ECT(Ω), Überlast für jede Menge).
T2  Solidität: die Filter schneiden nie eine Lösung ab (alle ganzzahligen Startzeiten ohne Überlappung in den Fenstern aufgezählt) und scheitern nur ohne Lösung.
T4  Intervallfassung gegen Θ-Λ-Baum gegen Mengenform: gleicher Fixpunkt oder gleicher Fehlschlag.
Die Quelle des Verfahrens ist nicht gelesen; diese Tests sind die Absicherung (siehe README). Im Repo kleine Fassungen, der große Lauf steht in `dje_sweeps.json` (4.000 Fälle)."""

import pytest

import dje_algorithm as A
import dje_baum as B
from conftest import einzelmaschine
from dje_rng import SplitMix64
from orakel import alle_loesungen_einzelmaschine, edge_finding_mengen


def _fall(rng, n_min=3, n_max=6, d_max=4, est_max=7, spiel_max=6):
    n = n_min + rng.below(n_max - n_min + 1)
    dauer = [1 + rng.below(d_max) for _ in range(n)]
    est = [rng.below(est_max) for _ in range(n)]
    lst = [e + rng.below(spiel_max) for e in est]
    return est, lst, dauer


def _fixpunkt(filter_fn, est, lst, dauer):
    """Wiederholt den Filter (auf est und lst) bis nichts mehr ändert; None bei Fehlschlag."""
    M = A.Modell(einzelmaschine(dauer))
    e, l = list(est), list(lst)
    if any(e[o] > l[o] for o in range(M.n)):
        return None
    z = A.Zaehler()
    while True:
        r = filter_fn(M, e, l, z, None)
        if r is None:
            return None
        if not r:
            return tuple(e), tuple(l)


def _mengen_fixpunkt(est, lst, dauer):
    """Fixpunkt der Mengenform (Aufzählung aller Teilmengen) auf est und, an der Zeit gespiegelt, auf lct."""
    n = len(est)
    e = list(est)
    lct = [lst[i] + dauer[i] for i in range(n)]
    if any(e[i] + dauer[i] > lct[i] for i in range(n)):
        return None
    while True:
        r = edge_finding_mengen(e, lct, dauer)
        if r is None:
            return None
        spiegel = edge_finding_mengen([-x for x in lct], [-x for x in r], dauer)
        if spiegel is None:
            return None
        neu_lct = [-x for x in spiegel]
        if any(r[i] + dauer[i] > neu_lct[i] for i in range(n)):
            return None
        if r == e and neu_lct == lct:
            return tuple(e), tuple(lct[i] - dauer[i] for i in range(n))
        e, lct = r, neu_lct


def test_t1_theta_lambda_baum_gegen_aufzaehlung_aller_mengen():
    """Ein Durchlauf des Baums auf est: dieselbe neue est-Liste wie die Aufzählung aller Mengen, dieselbe Überlast."""
    rng = SplitMix64(11)
    fehl = 0
    for _ in range(400):
        est, lst, dauer = _fall(rng)
        lct = [lst[i] + dauer[i] for i in range(len(est))]
        erwartet = edge_finding_mengen(est, lct, dauer)
        r = B.durchlauf_est(est, lct, dauer)
        if erwartet is None:
            assert r is None, (est, lst, dauer)
            fehl += 1
        else:
            assert r is not None and r[0] == erwartet, (est, lst, dauer, erwartet, r)
    assert 30 < fehl < 370                                                                 # beide Ausgänge kommen vor


def test_t1_von_hand_ein_kleiner_fall():
    """Drei Operationen, alle est 0: A d3 lct 3, B d3 lct 6, C d2 lct 8. Ω = {A}: lct 3, ECT({A, B}) = 6 > 3, also muss B nach A: est_B >= ECT({A}) = 3 (ebenso C: ECT({A, C}) = 5 > 3, est_C >= 3).
    Ω = {A, B}: ECT = 6 <= lct = 6 passt; ECT(Ω ∪ {C}) = 8 > 6, also muss C nach A und B: est_C >= 6. Ergebnis [0, 3, 6]."""
    est, lct, dauer = [0, 0, 0], [3, 6, 8], [3, 3, 2]
    r = B.durchlauf_est(est, lct, dauer)
    assert r is not None and r[0] == [0, 3, 6] and edge_finding_mengen(est, lct, dauer) == [0, 3, 6]
    assert B.durchlauf_est([0, 0], [3, 4], [3, 3]) is None                                  # Überlast: 0 + 6 > 4


def test_t2_solide_gegen_aufzaehlung_aller_loesungen():
    """Für beide Fassungen (Intervall, Baum): keine Lösung geht verloren, ein Fehlschlag bedeutet „keine Lösung“, jede Instanz ohne Lösung wird mit dem Fenster-Fixpunkt oder früher erkannt, wenn der Filter es kann."""
    rng = SplitMix64(22)
    mit_loesung = ohne_loesung = 0
    for _ in range(300):
        est, lst, dauer = _fall(rng, 3, 5, 3, 5, 4)
        loesungen = alle_loesungen_einzelmaschine(est, lst, dauer)
        for filter_fn in (A._edge_finding, B.edge_finding_baum):
            fix = _fixpunkt(filter_fn, est, lst, dauer)
            if loesungen:
                assert fix is not None, ("Lösung vorhanden, Filter scheitert", est, lst, dauer)
                e, l = fix
                for s in loesungen:
                    assert all(e[i] <= s[i] <= l[i] for i in range(len(s))), ("Lösung abgeschnitten", est, lst, dauer, s)
        if loesungen:
            mit_loesung += 1
        else:
            ohne_loesung += 1
    assert mit_loesung > 50 and ohne_loesung > 50


def test_t4_intervall_baum_und_mengenform_haben_denselben_fixpunkt():
    rng = SplitMix64(44)
    gleich_loesung = gleich_fehl = 0
    for _ in range(300):
        est, lst, dauer = _fall(rng, 3, 5)
        a = _fixpunkt(A._edge_finding, est, lst, dauer)
        b = _fixpunkt(B.edge_finding_baum, est, lst, dauer)
        c = _mengen_fixpunkt(est, lst, dauer)
        assert a == b == c, (est, lst, dauer, a, b, c)
        if a is None:
            gleich_fehl += 1
        else:
            gleich_loesung += 1
    assert gleich_loesung > 50 and gleich_fehl > 50


def test_baum_einzelne_einheiten_von_hand():
    """Θ-Λ-Baum: drei Blätter mit est 0, 1, 2 und Dauern 2, 1, 3: alle Θ: ECT = max(2 + 6, 2 + 5, 5 ...) von Hand: nach est sortiert ist die letzte Fertigstellung 0 + 2 + 1 + 3 = 6 (Start bei 0)."""
    baum = B.ThetaLambdaBaum([0, 1, 2], [2, 1, 3])
    for i in range(3):
        baum.setze(i, "theta")
    assert baum.wurzel_ect() == 6                      # max über Suffixe: 0 + 6, 1 + 4, 2 + 3
    baum.setze(1, "aus")
    assert baum.wurzel_ect() == 5                      # Blätter 0 und 2: max(0 + 5, 2 + 3) = 5
    baum.setze(1, "grau")
    assert baum.wurzel_ectb() == 6                     # mit dem grauen Blatt 1 wieder 6
    assert baum.wurzel_verantwortlich() == 1


def test_stufe_3_im_suchbaum_gleich_stufe_2_in_der_fenster_und_knotenzahl():
    """Stufe 3 liefert an der Wurzel dieselben Fenster wie Stufe 2, und in der Suche dieselbe Knotenzahl, auf 20 Instanzen 5 × 5."""
    from dje_scenario import make_jobshop

    for seed in range(1, 21):
        inst = make_jobshop(5, 5, 8000 + seed)
        r2, r3 = A.loese(inst, 2), A.loese(inst, 3)
        assert (r2.optimum, r2.z.knoten, r2.z.fehlschlaege) == (r3.optimum, r3.z.knoten, r3.z.fehlschlaege), seed
