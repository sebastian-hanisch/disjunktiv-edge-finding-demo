"""Kennzahlen, Verdikt-Logik und Auswertung der vorgerechneten Messreihen (`dje_sweeps.json`, Messskript tools/messung_sweeps.py).

Alle Verdikte sind reine Funktionen `verdict_*(...) -> (Art, Text)`: die App ruft `getattr(st, Art)(Text)`, `tests/test_verdicts.py` prüft jede Zahl im Text an handgesetzten Werten.
Gezählt wird in Suchknoten, nie in Sekunden."""

import json
import math
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from statistics import median

import dje_algorithm as A
import dje_constants as C
from dje_scenario import Instance, make_jobshop

SWEEPS_PATH = Path(__file__).resolve().parent / C.SWEEPS_FILE


@dataclass(frozen=True)
class Settings:
    jobs: int = C.DEFAULT_JOBS
    machines: int = C.DEFAULT_MACHINES
    dmax: int = C.DMAX_DEFAULT
    seed: int = C.DEFAULT_SEED
    budget: int = C.DEFAULT_BUDGET
    hb_h: int = C.DEFAULT_HB_H
    hb_stage: int = C.DEFAULT_HB_STAGE


def instanz(s: Settings) -> Instance:
    return make_jobshop(s.jobs, s.machines, s.seed, s.dmax)


# ------------------------------------------------------------------------------------------------------------------------- Messreihen (JSON)
@lru_cache(maxsize=1)
def lade_sweeps() -> dict:
    return json.loads(SWEEPS_PATH.read_text(encoding="utf-8"))


def p90(werte) -> int:
    """90-%-Wert nach dem Nächste-Rang-Verfahren: der Wert an Stelle ceil(0,9 n) der aufsteigend sortierten Liste."""
    w = sorted(werte)
    return w[math.ceil(0.9 * len(w)) - 1]


def knoten(reihe: dict, stufe: int) -> list[int]:
    return [z["stufen"][str(stufe)]["knoten"] for z in reihe["instanzen"]]


def abbrueche(reihe: dict, stufe: int) -> int:
    return sum(1 for z in reihe["instanzen"] if not z["stufen"][str(stufe)]["bewiesen"])


def statistik(reihe: dict, stufen=None) -> list[dict]:
    """Je Stufe Median, P90, Maximum, Abbrüche am Budget und Zahl der Instanzen (Knoten bis zum Beweis des Optimums; bei Abbruch ist der Wert das Budget, also eine untere Schranke)."""
    stufen = reihe["stufen"] if stufen is None else stufen
    rows = []
    for s in stufen:
        w = knoten(reihe, s)
        rows.append({"stufe": s, "n": len(w), "median": median(w), "p90": p90(w), "max": max(w), "abbrueche": abbrueche(reihe, s), "summe": sum(w)})
    return rows


def gleiche_knoten(reihe: dict, stufe_a: int, stufe_b: int) -> tuple[int, int]:
    """(Zahl der Instanzen mit gleicher Knotenzahl in beiden Stufen, Zahl der Instanzen)."""
    a, b = knoten(reihe, stufe_a), knoten(reihe, stufe_b)
    return sum(1 for x, y in zip(a, b) if x == y), len(a)


def optima_stimmen(reihe: dict) -> tuple[int, int]:
    """(Zahl der bewiesenen Optima aller Stufen, die dem CP-SAT-Wert gleichen, Zahl der bewiesenen Optima)."""
    ok = tot = 0
    for z in reihe["instanzen"]:
        for st in z["stufen"].values():
            if st["bewiesen"]:
                tot += 1
                ok += st["optimum"] == z["optimum_cpsat"]
    return ok, tot


def ursachen(reihe: dict, stufen=(0, 1, 2)) -> list[dict]:
    """Summen über die Instanzen: Fehlschläge nach Ursache, Kanten des Paar-Tests, Verengungen durch Edge-Finding, Fehlschläge an der Wurzel."""
    rows = []
    for s in stufen:
        zs = [z["stufen"][str(s)] for z in reihe["instanzen"]]
        rows.append({"stufe": s, "knoten": sum(z["knoten"] for z in zs), "fehlschlaege": sum(z["fehlschlaege"] for z in zs), "vorrang": sum(z["fehl_vorrang"] for z in zs),
                     "paar": sum(z["fehl_paar"] for z in zs), "edge": sum(z["fehl_edge"] for z in zs), "wurzel": sum(z["fehl_wurzel"] for z in zs),
                     "kanten_paar": sum(z["kanten_paar"] for z in zs), "ef_verengungen": sum(z["ef_verengungen"] for z in zs), "runden": sum(z["runden"] for z in zs)})
    return rows


def horizont_statistik(h: dict, groesse: str, art: str, stufen=(0, 1, 2)) -> list[dict]:
    """Median und Summe der Knoten je Stufe für `art` = „beweis“ (H = Optimum - 1) oder „loesung“ (H = Optimum, erste Lösung)."""
    rows = []
    for s in stufen:
        eintraege = [z[art][str(s)] for z in h[groesse]["instanzen"]]
        w = [e["knoten"] for e in eintraege]
        rows.append({"stufe": s, "n": len(w), "median": median(w), "summe": sum(w), "max": max(w), "abbrueche": sum(1 for e in eintraege if e["abgebrochen"])})
    return rows


def tail_instanz(sw: dict) -> Instance:
    return Instance(tuple(tuple((int(m), int(d)) for m, d in job) for job in sw["jobs"]))


def tail_abbrueche(sw: dict) -> tuple[int, int]:
    """(Zahl der Seeds im Scan, bei denen Stufe 1 das Scan-Budget erreichte, Zahl der Seeds im Scan)."""
    return sum(1 for z in sw["scan"] if z["abbruch1"]), len(sw["scan"])


# ------------------------------------------------------------------------------------------------------------------------------ Live-Läufe
def live_vergleich(s: Settings, stufen=(0, 1, 2)) -> dict:
    """Die Einzelinstanz mit allen Stufen bis zum bewiesenen Optimum (oder bis zum Knotenbudget)."""
    inst = instanz(s)
    return {st: A.loese(inst, st, budget=s.budget) for st in stufen}


def widerspruch_im_optimum(erg: dict) -> bool:
    """Wahr, wenn zwei Stufen, die ihr Optimum bewiesen haben, verschiedene Werte nennen (darf nie vorkommen)."""
    werte = {e.optimum for e in erg.values() if e.bewiesen}
    return len(werte) > 1


# --------------------------------------------------------------------------------------------------------------------------------- Verdikte
def _zahl(x) -> str:
    """Ganze Zahl mit Tausenderpunkt, Halbe mit Komma (Mediane über eine gerade Zahl von Instanzen können ,5 sein)."""
    if isinstance(x, float) and not x.is_integer():
        return f"{x:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{int(x):,}".replace(",", ".")


def _faktor(a, b) -> str:
    return f"{a / b:.1f}".replace(".", ",")


def verdict_handbeispiel(H: int, stufe: int, entscheidungen: dict) -> tuple[str, str]:
    """Handbeispiel (Experiment 1). `entscheidungen`: Stufe → (Knoten, Fehlschläge, gefunden)."""
    kn, fe, gef = entscheidungen[stufe]
    nachbarn = ", ".join(f"Stufe {s}: {entscheidungen[s][0]}" for s in sorted(entscheidungen))
    if gef:
        text = (f"Horizont {H}: Die Suche findet einen Plan mit Makespan höchstens {H}; auf Stufe {stufe} braucht sie dafür {kn} Knoten (Fehlschläge: {fe}). "
                f"Knoten je Stufe: {nachbarn}.")
        return "info", text
    text = (f"Horizont {H}: Es gibt keinen Plan mit Makespan höchstens {H}. Auf Stufe {stufe} beweist die Suche das in {kn} Knoten (Fehlschläge: {fe}). "
            f"Knoten je Stufe: {nachbarn}.")
    return "success", text


def verdict_stufen(rows: list[dict], titel: str) -> tuple[str, str]:
    """Stufenvergleich über eine Messreihe (Experiment 2). `rows`: Statistik je Stufe 0, 1, 2 mit Median, P90, Maximum und Abbrüchen.

    Nennt Median und Tail getrennt; bei Abbrüchen sind die Zahlen untere Schranken."""
    by = {r["stufe"]: r for r in rows}
    r0, r1, r2 = by[0], by[1], by[2]
    n = r0["n"]
    satz1 = f"{titel} ({n} feste Instanzen): reine Vorrangpropagation braucht im Median {_zahl(r0['median'])} Knoten, mit Paar-Test {_zahl(r1['median'])}"
    if r1["median"] > 0 and r0["median"] > r1["median"]:
        satz1 += f" ({_faktor(r0['median'], r1['median'])}-fach weniger)"
    satz1 += f", mit Edge-Finding {_zahl(r2['median'])}."
    if r2["median"] == r1["median"]:
        satz2 = " Im Median spart Edge-Finding hier nichts gegenüber dem Paar-Test."
    elif r2["median"] < r1["median"]:
        prozent = round(100 * (r1["median"] - r2["median"]) / r1["median"])
        satz2 = f" Edge-Finding spart im Median {prozent} % der Knoten des Paar-Tests (Bezug: Stufe 1)."
    else:
        satz2 = " Im Median braucht Edge-Finding mehr Knoten als der Paar-Test."
    satz3 = (f" Im Tail (Stufe 0 / 1 / 2): Maximum {_zahl(r0['max'])} / {_zahl(r1['max'])} / {_zahl(r2['max'])} Knoten, 90-%-Wert {_zahl(r0['p90'])} / {_zahl(r1['p90'])} / {_zahl(r2['p90'])}.")
    ab = r0["abbrueche"] + r1["abbrueche"] + r2["abbrueche"]
    satz4 = f" {ab} Läufe brachen am Knotenbudget ab; ihre Zahlen sind untere Schranken." if ab else ""
    art = "success" if (r1["median"] > 0 and r0["median"] >= 2 * r1["median"]) else "info"
    return art, satz1 + satz2 + satz3 + satz4


def verdict_einzel(erg: dict, budget: int) -> tuple[str, str]:
    """Verdikt für die Einzelinstanz (Live-Lauf): Knoten je Stufe, Optimum, Abbrüche. `erg`: Stufe → `Ergebnis`."""
    if widerspruch_im_optimum(erg):
        return "error", "Widerspruch: zwei Stufen nennen verschiedene bewiesene Optima. Das darf nicht vorkommen."
    teile = []
    for s in sorted(erg):
        e = erg[s]
        teile.append(f"Stufe {s}: {_zahl(e.z.knoten)} Knoten" + ("" if e.bewiesen else " (Abbruch am Budget, untere Schranke)"))
    bewiesen = [e for e in erg.values() if e.bewiesen]
    if bewiesen:
        satz = f"Optimaler Makespan {bewiesen[0].optimum}, bewiesen von {len(bewiesen)} der {len(erg)} Stufen. "
    else:
        satz = f"Keine Stufe beweist das Optimum innerhalb von {_zahl(budget)} Knoten; der beste gefundene Makespan ist {min(e.optimum for e in erg.values())}. "
    text = satz + "; ".join(teile) + ". Einzelinstanz, kein Median."
    if 0 in erg and 1 in erg and erg[0].bewiesen and erg[1].bewiesen and erg[1].z.knoten > 0 and erg[0].z.knoten > erg[1].z.knoten:
        text += f" Stufe 0 braucht hier {_faktor(erg[0].z.knoten, erg[1].z.knoten)}-mal so viele Knoten wie Stufe 1."
    if 1 in erg and 2 in erg and erg[1].bewiesen and erg[2].bewiesen and erg[1].z.knoten == erg[2].z.knoten:
        text += " Edge-Finding spart auf dieser Instanz nichts."
    return "info", text


def verdict_tail(sw: dict, reihe_8x8: dict) -> tuple[str, str]:
    """Verdikt des Tail-Experiments aus den eingefrorenen Daten (`tail`) und der 8x8-Reihe."""
    st1, st2 = sw["stufen"]["1"], sw["stufen"]["2"]
    k_ab, k_n = tail_abbrueche(sw)
    med = {r["stufe"]: r["median"] for r in statistik(reihe_8x8, (1, 2))}
    if st1["bewiesen"]:
        satz = (f"Eingefrorener Fall (8 × 8, Zufalls-Seed {sw['gewaehlt']}, größter Abstand unter {k_n} Seeds): Stufe 1 beweist das Optimum {st1['optimum']} in {_zahl(st1['knoten'])} Knoten, "
                f"Stufe 2 in {_zahl(st2['knoten'])}.")
    else:
        satz = (f"Eingefrorener Fall (8 × 8, Zufalls-Seed {sw['gewaehlt']}, größter Abstand unter {k_n} Seeds): Stufe 1 bricht am Budget von {_zahl(sw['budget'])} Knoten ab (untere Schranke), "
                f"Stufe 2 beweist das Optimum {st2['optimum']} in {_zahl(st2['knoten'])} Knoten.")
    satz += f" Im Median der {len(reihe_8x8['instanzen'])} Seeds der 8 × 8-Messreihe sind es {_zahl(med[1])} gegen {_zahl(med[2])} Knoten."
    satz += f" Im Seed-Scan erreichte Stufe 1 das Budget von {_zahl(sw['scan_budget_stufe1'])} Knoten in {k_ab} von {k_n} Seeds."
    return "info", satz


def verdict_horizont(hz: dict, groesse: str) -> tuple[str, str]:
    """Hypothese „der Mengenschluss wirkt vor allem bei engem Horizont“: Knoten von Stufe 2 gegen Stufe 1 beim Beweis (H = Optimum - 1) und bei der Lösung (H = Optimum)."""
    b = {r["stufe"]: r for r in horizont_statistik(hz, groesse, "beweis")}
    l = {r["stufe"]: r for r in horizont_statistik(hz, groesse, "loesung")}
    n = b[1]["n"]

    def anteil(r):
        return round(100 * (r[1]["summe"] - r[2]["summe"]) / r[1]["summe"]) if r[1]["summe"] else 0

    ab, al = anteil(b), anteil(l)
    satz = (f"{groesse.replace('x', ' × ')}, {n} feste Instanzen, Summe der Knoten Stufe 1 gegen Stufe 2: Beweis bei Horizont = Optimum − 1: {_zahl(b[1]['summe'])} gegen {_zahl(b[2]['summe'])} "
            f"({ab} % weniger mit Edge-Finding); erste Lösung bei Horizont = Optimum: {_zahl(l[1]['summe'])} gegen {_zahl(l[2]['summe'])} ({al} % weniger).")
    if ab > al:
        satz += " Der Gewinn durch Edge-Finding liegt hier beim Beweis höher als bei der Lösung."
    elif ab < al:
        satz += " Der Gewinn durch Edge-Finding liegt hier bei der Lösung höher als beim Beweis."
    else:
        satz += " Der Gewinn ist in beiden Fassungen gleich."
    return "info", satz


def verdict_baum(reihen: dict, baum: dict) -> tuple[str, str]:
    """Erweiterung 11b: Stufe 3 (Θ-Λ-Baum) gegen Stufe 2 (Intervall): gleiche Knotenzahl in k von n Instanzen, gleicher Fixpunkt auf Einzelmaschinen in k von n Fällen."""
    gleich = sum(gleiche_knoten(r, 2, 3)[0] for r in reihen.values())
    gesamt = sum(gleiche_knoten(r, 2, 3)[1] for r in reihen.values())
    text = (f"Der Θ-Λ-Baum hat in {gleich} von {gesamt} Instanzen (5 × 5, 6 × 6, 8 × 8) dieselbe Knotenzahl wie die Intervallfassung. Auf {_zahl(baum['faelle'])} zufälligen Einzelmaschinen-Fenstern "
            f"(3 bis 6 Operationen) liefern beide denselben Fixpunkt oder denselben Fehlschlag in {_zahl(baum['gleich'])} Fällen. Der Baum bringt also keine Suchersparnis; "
            f"ob er je Durchlauf schneller ist, misst diese Demo nicht (asymptotisch O(n log n) gegen kubisch in der Zahl der Operationen je Maschine bei der Intervallfassung dieser Demo).")
    return ("success" if gleich == gesamt and baum["gleich"] == baum["faelle"] else "info"), text
