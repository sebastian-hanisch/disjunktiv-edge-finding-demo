"""Abbildungen: Aufbau der Figuren an kleinen Eingaben (Zahl der Balken, Pflichtteile, Achsen gesperrt)."""

import dje_algorithm as A
import dje_visualization as V


def _hb_fenster(hb, H=7, stufe=1):
    M = A.Modell(hb)
    est, lst, kanten = A.anfangsfenster(M, H)
    A.propagiere(M, est, lst, kanten, H, stufe, A.Zaehler())
    return M, est, lst


def test_fenster_hat_je_operation_einen_balken_und_nur_echte_pflichtteile(hb):
    M, est, lst = _hb_fenster(hb)
    assert not [o for o in range(9) if lst[o] < est[o] + M.d[o]]            # an der Wurzel des Handbeispiels (H = 7) hat keine Operation einen Pflichtteil
    est, lst = [0] * 9, [1, 9, 9, 9, 1, 9, 9, 9, 2]                           # (0,0) d2 [0,1]: Pflichtteil [1,2); (1,1) d1 [0,1]: keiner (1 >= 1); (2,2) d2 [0,2]: keiner
    fig = V.build_fenster(M, est, lst, 11)
    fenster, pflicht = fig.data
    assert len(fenster.y) == 9
    erwartet = [o for o in V.zeilen_nach_maschine(M) if lst[o] < est[o] + M.d[o]]
    assert erwartet == [0] and len(pflicht.y) == 1
    for base, x, o in zip(pflicht.base, pflicht.x, erwartet):
        assert (base, base + x) == (lst[o], est[o] + M.d[o])
    assert fig.layout.xaxis.fixedrange and fig.layout.yaxis.fixedrange


def test_fenster_balken_reichen_von_est_bis_lct(hb):
    M, est, lst = _hb_fenster(hb, stufe=0)
    fenster = V.build_fenster(M, est, lst, 7).data[0]
    for y, base, x in zip(fenster.y, fenster.base, fenster.x):
        o = next(o for o in range(9) if y.startswith(f"M{M.maschine[o]} · {M.bezeichnung(o)} "))
        assert (base, base + x) == (est[o], lst[o] + M.d[o])


def test_alle_ereignisse_aller_kombinationen_lassen_sich_zeichnen(hb):
    M = A.Modell(hb)
    for H in (7, 8):
        for stufe in (0, 1, 2):
            e = A.entscheide(hb, H, stufe, protokoll=True)
            for ereignis in e.protokoll.ereignisse:
                assert len(V.build_fenster(M, ereignis.est, ereignis.lst, H).data) == 2


def test_gantt_hat_eine_zeile_je_maschine_und_einen_balken_je_operation(hb):
    r = A.loese(hb, 2)
    fig = V.build_gantt(A.Modell(hb), r.plan)
    assert len(fig.data) == 9 and set(fig.layout.yaxis.categoryarray) == {"Maschine 0", "Maschine 1", "Maschine 2"}


def test_verteilung_zeichnet_abbrueche_als_kreuz():
    fig = V.build_verteilung({0: [10, 20, 30], 1: [5, 6, 20000]}, {0: 0, 1: 1}, 20000)
    boxen = [t for t in fig.data if t.type == "box"]
    kreuze = [t for t in fig.data if t.type == "scatter"]
    assert len(boxen) == 2 and len(kreuze) == 1 and list(kreuze[0].y) == [20000] and fig.layout.yaxis.type == "log"


def test_ursachen_stapelt_drei_ursachen():
    fig = V.build_ursachen([{"stufe": 0, "vorrang": 5, "paar": 0, "edge": 0}, {"stufe": 1, "vorrang": 3, "paar": 2, "edge": 0}])
    assert len(fig.data) == 3 and list(fig.data[1].y) == [0, 2]
