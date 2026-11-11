"""Erweiterung 11b: Edge-Finding und Überlastprüfung mit dem Θ-Λ-Baum (O(n log n) je Durchlauf statt Teilmengen oder Intervallpaaren).

Eigene Nachbildung des in der Literatur beschriebenen Verfahrens, aus dem Gedächtnis geschrieben, **Quelle nicht gelesen** (nur Suchtreffer zu Wallace, Vilím, Barták, Čepek 2004 und
Vilím, Barták, Čepek 2005). Die Korrektheit stützt sich deshalb nicht auf die Quelle, sondern auf Tests gegen die Aufzählung aller Mengen Ω (tests/test_oracle_baum.py).

Idee. Die Aktivitäten einer Maschine stehen als Blätter eines Baums, sortiert nach frühestem Start est. Jede Aktivität ist „Θ“ (zählt), „grau“ (Λ: zählt höchstens eine von ihnen, die
beste) oder „aus“. Jeder Knoten hält vier Zahlen und kennt, welches graue Blatt dafür verantwortlich ist:
  sumP    Summe der Dauern der Θ-Blätter darunter
  ect     früheste Fertigstellung der Θ-Blätter darunter: max(ect(rechts), ect(links) + sumP(rechts))
  sumPb   wie sumP, aber mit dem einen grauen Blatt, das die Summe am meisten erhöht
  ectb    wie ect, mit dem einen grauen Blatt, das die Fertigstellung am meisten erhöht
Edge-Finding auf est: alle Aktivitäten Θ; in der Reihenfolge fallender spätester Fertigstellung lct wandert die Aktivität j mit dem größten lct nach Λ. Ist ect(Θ) größer als der lct der
nächsten, Überlast (Fehlschlag). Solange ectb(Θ, Λ) den lct der nächsten übersteigt, muss die verantwortliche graue Aktivität i nach allen Θ-Aktivitäten laufen: est_i wird mindestens ect(Θ);
danach scheidet i aus Λ aus. Die Spiegelung (Zeit umkehren) liefert dasselbe für lct."""

NEG = -(10 ** 9)


class ThetaLambdaBaum:
    def __init__(self, est: list[int], dauer: list[int]):
        n = len(est)
        self.est, self.p = est, dauer
        reihenfolge = sorted(range(n), key=lambda i: (est[i], i))
        self.pos = {i: k for k, i in enumerate(reihenfolge)}
        groesse = 1
        while groesse < max(n, 1):
            groesse *= 2
        self.groesse = groesse
        m = 2 * groesse
        self.sum_p = [0] * m
        self.ect = [NEG] * m
        self.sum_pb = [0] * m
        self.ectb = [NEG] * m
        self.verantw_sum = [-1] * m     # graues Blatt, das sum_pb erreicht
        self.verantw_ect = [-1] * m     # graues Blatt, das ectb erreicht

    def setze(self, i: int, art: str):
        """Blatt i auf „theta“, „grau“ oder „aus“ setzen und die Knoten bis zur Wurzel neu berechnen."""
        k = self.groesse + self.pos[i]
        p, e = self.p[i], self.est[i]
        if art == "theta":
            self.sum_p[k], self.ect[k], self.sum_pb[k], self.ectb[k] = p, e + p, p, e + p
            self.verantw_sum[k] = self.verantw_ect[k] = -1
        elif art == "grau":
            self.sum_p[k], self.ect[k], self.sum_pb[k], self.ectb[k] = 0, NEG, p, e + p
            self.verantw_sum[k] = self.verantw_ect[k] = i
        else:
            self.sum_p[k], self.ect[k], self.sum_pb[k], self.ectb[k] = 0, NEG, 0, NEG
            self.verantw_sum[k] = self.verantw_ect[k] = -1
        k //= 2
        while k >= 1:
            self._neu(k)
            k //= 2

    def _neu(self, k: int):
        links, rechts = 2 * k, 2 * k + 1
        self.sum_p[k] = self.sum_p[links] + self.sum_p[rechts]
        self.ect[k] = max(self.ect[rechts], self.ect[links] + self.sum_p[rechts])
        a = self.sum_pb[links] + self.sum_p[rechts]
        b = self.sum_p[links] + self.sum_pb[rechts]
        if a >= b:
            self.sum_pb[k], self.verantw_sum[k] = a, self.verantw_sum[links]
        else:
            self.sum_pb[k], self.verantw_sum[k] = b, self.verantw_sum[rechts]
        o1 = self.ectb[rechts]
        o2 = self.ect[links] + self.sum_pb[rechts]
        o3 = self.ectb[links] + self.sum_p[rechts]
        beste = max(o1, o2, o3)
        self.ectb[k] = beste
        if beste == o1:
            self.verantw_ect[k] = self.verantw_ect[rechts]
        elif beste == o2:
            self.verantw_ect[k] = self.verantw_sum[rechts]
        else:
            self.verantw_ect[k] = self.verantw_ect[links]

    def wurzel_ect(self) -> int:
        return self.ect[1]

    def wurzel_ectb(self) -> int:
        return self.ectb[1]

    def wurzel_verantwortlich(self) -> int:
        return self.verantw_ect[1]


def durchlauf_est(est: list[int], lct: list[int], dauer: list[int]):
    """Überlastprüfung und Edge-Finding auf est. Rückgabe (neue est-Liste, Liste der Verengungen (i, alt, neu)) oder None bei Überlast."""
    n = len(est)
    neu = list(est)
    verengungen = []
    if n < 2:
        return neu, verengungen
    baum = ThetaLambdaBaum(est, dauer)
    for i in range(n):
        baum.setze(i, "theta")
    nach_lct = sorted(range(n), key=lambda i: (-lct[i], i))
    if baum.wurzel_ect() > lct[nach_lct[0]]:
        return None
    for q in range(n - 1):
        baum.setze(nach_lct[q], "grau")
        naechste = nach_lct[q + 1]
        if baum.wurzel_ect() > lct[naechste]:
            return None
        while baum.wurzel_ectb() > lct[naechste]:
            i = baum.wurzel_verantwortlich()
            if i < 0:
                break
            e = baum.wurzel_ect()
            if e > neu[i]:
                verengungen.append((i, neu[i], e))
                neu[i] = e
            baum.setze(i, "aus")
    return neu, verengungen


def filter_einzelmaschine(est: list[int], lct: list[int], dauer: list[int]):
    """Ein Durchlauf auf est und, an der Zeit gespiegelt, auf lct. Rückgabe (est, lct, Verengungen) oder None bei Fehlschlag.

    Verengungen: Liste (Seite, Index, alt, neu) mit Seite „est“ oder „lct“."""
    r = durchlauf_est(est, lct, dauer)
    if r is None:
        return None
    est1, ver_est = r
    spiegel_est = [-x for x in lct]
    spiegel_lct = [-x for x in est1]
    r = durchlauf_est(spiegel_est, spiegel_lct, dauer)
    if r is None:
        return None
    spiegel_neu, ver_lct = r
    lct1 = [-x for x in spiegel_neu]
    for i in range(len(est1)):
        if est1[i] + dauer[i] > lct1[i]:
            return None
    verengungen = [("est", i, a, b) for i, a, b in ver_est] + [("lct", i, -a, -b) for i, a, b in ver_lct]
    return est1, lct1, verengungen


def edge_finding_baum(M, est, lst, z, prot):
    """Stufe 3 im Mini-CP: Θ-Λ-Baum je Maschine. Verändert est und lst; None bei Fehlschlag, sonst True/False (Fenster verengt?)."""
    verengt = False
    for m, ops in enumerate(M.maschinen_ops):
        if len(ops) < 2:
            continue
        z.ef_aufrufe += 1
        e = [est[o] for o in ops]
        l = [lst[o] + M.d[o] for o in ops]
        p = [M.d[o] for o in ops]
        r = filter_einzelmaschine(e, l, p)
        if r is None:
            if prot is not None:
                prot.add("fehlschlag", f"Maschine {m}: Überlast (Θ-Λ-Baum) → Fehlschlag", est, lst)
            return None
        e2, l2, verengungen = r
        for seite, idx, alt, neu in verengungen:
            o = ops[idx]
            if seite == "est" and neu > est[o]:
                if prot is not None:
                    prot.add("edge", f"Θ-Λ-Baum Maschine {m}: {M.bezeichnung(o)} nach einer Menge von Operationen: est {est[o]} → {neu}", est, lst)
                est[o] = neu
                z.ef_verengungen += 1
                verengt = True
            elif seite == "lct" and neu - M.d[o] < lst[o]:
                if prot is not None:
                    prot.add("edge", f"Θ-Λ-Baum Maschine {m}: {M.bezeichnung(o)} vor einer Menge von Operationen: lst {lst[o]} → {neu - M.d[o]}", est, lst)
                lst[o] = neu - M.d[o]
                z.ef_verengungen += 1
                verengt = True
        for o in ops:
            if est[o] > lst[o]:
                if prot is not None:
                    prot.add("fehlschlag", f"Fenster von {M.bezeichnung(o)} ist leer: est {est[o]} > lst {lst[o]} → Fehlschlag", est, lst)
                return None
    return verengt
