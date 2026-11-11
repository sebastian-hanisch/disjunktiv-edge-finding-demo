"""Disjunktiv und Edge-Finding – Schlüsse über Maschinen - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Ein Job Shop als Suchproblem: „höchstens eine Operation je Maschine“ heißt „a vor b oder b vor a“, also Verzweigen. Das Mini-CP dieser Demo zählt Suchknoten bei drei (vier) Stufen
der Propagation: nur Vorrang, + Paar-Test, + Edge-Finding (Intervallfassung), + Θ-Λ-Baum (Erweiterung).

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import dje_algorithm as A
import dje_aufzaehlung as Z
import dje_constants as C
import dje_evaluation as ev
import dje_live as L
from dje_layout import dunkles_design, kopf_css
from dje_presets import (
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
    SETTING_SPECS,
)
from dje_scenario import HANDBEISPIEL
from dje_visualization import build_fenster, build_gantt, build_ursachen, build_verteilung

st.set_page_config(page_title="Disjunktiv und Edge-Finding – Sebastian Hanisch", layout="wide")


def _zahl(x) -> str:
    return ev._zahl(x)


def _md_table(headers, rows) -> str:
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    for r in rows:
        out.append("| " + " | ".join(str(c) for c in r) + " |")
    return "\n".join(out)


@st.cache_data(show_spinner=False)
def _handbeispiel(H, stufe):
    return A.entscheide(HANDBEISPIEL, H, stufe, protokoll=True)


@st.cache_data(show_spinner=False)
def _handbeispiel_knoten(H):
    return {s: (lambda e: (e.z.knoten, e.z.fehlschlaege, e.gefunden))(A.entscheide(HANDBEISPIEL, H, s)) for s in C.STAGES}


@st.cache_data(show_spinner=False)
def _aufzaehlung():
    return Z.aufzaehlen(HANDBEISPIEL)


DATA = ev.lade_sweeps()
REIHEN = DATA["reihen"]

# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in dje_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🧩 Disjunktiv und Edge-Finding – Schlüsse über Maschinen")
st.markdown(
    """
In einem **Job Shop** bearbeitet jede Maschine höchstens eine Operation zugleich. Das ist eine **Disjunktion**: Für zwei Operationen auf derselben Maschine gilt „a vor b **oder** b vor a“, und aus der Bedingung wird **Suche**.
Das **Constraint Programming** (CP) hält die Suche klein, indem es nach jeder Entscheidung die **Zeitfenster** der Operationen eingrenzt (Propagation). Diese Demo zählt **Suchknoten** bis zum bewiesenen Optimum bei vier Stufen:
nur **Vorrang**, dazu der **Paar-Test**, dazu **Edge-Finding** (Schlüsse über ganze Mengen von Operationen) und, als Erweiterung, derselbe Schluss mit einem **Θ-Λ-Baum**.

Unten: die Experimente (**🔬 Handbeispiel**, **Stufen im Vergleich**, **Tail**, **Woher die Ersparnis kommt**, **Gleicher Schluss, gleiche Knoten**), der Abschnitt **🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**.
"""
)

with st.expander("So funktioniert die Propagation am Job Shop", expanded=True):
    st.markdown(
        """
Jede Operation hat ein **Fenster**: frühester Start `est`, spätester Start `lst` (aus dem Horizont H: Makespan höchstens H) und spätestes Ende `lct = lst + Dauer`. Die Suche verzweigt auf der Reihenfolge je Paar von Operationen auf einer Maschine; nach jeder Entscheidung schieben die Stufen die Fenster, bis sich nichts mehr ändert (Fixpunkt), oder melden einen **Fehlschlag**.

""" + _md_table(
            ["Stufe", "Was sie sieht", "Was sie nicht sieht"],
            [
                ["0 Vorrang", "Auftragsketten und beschlossene Reihenfolgen: Fenster werden längs der Kanten verschoben", "dass zwei Operationen sich auf einer Maschine nicht überlappen dürfen"],
                ["1 Paar-Test", "je Paar: „a vor b“ passt, wenn est_a + Dauer_a ≤ lst_b; passt keine Richtung, Fehlschlag; passt nur eine, kommt die Kante", "Überlast durch drei oder mehr Operationen, wenn jedes Paar für sich passt"],
                ["2 Edge-Finding", "Mengen: passt die Summe der Dauern nicht in ihr Zeitfenster, Fehlschlag; sonst Operationen, die vor oder nach der ganzen Menge laufen müssen", "alle möglichen Mengen: dies ist die einfache Fassung (Intervalle)"],
                ["3 Θ-Λ-Baum", "dasselbe wie Stufe 2, mit einer Baum-Datenstruktur", "nichts zusätzlich: dieselben Schlüsse"],
            ],
        )
        + "\n\nEdge-Finding ist hier eine **eigene Nachbildung** des in der Literatur beschriebenen Verfahrens (Quelle nicht gelesen); die Korrektheit stützt sich auf Tests gegen die Aufzählung aller Mengen."
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Zufalls-Job-Shop (Experiment 2)**")
    jobs = st.slider("Aufträge", *bounds("jobs_slider"), key="jobs_slider", help="Wie viele Aufträge der Zufalls-Job-Shop hat.")
    machines = st.slider("Maschinen", *bounds("machines_slider"), key="machines_slider", help="Wie viele Maschinen; jeder Auftrag besucht jede Maschine genau einmal in zufälliger Reihenfolge.")
    dmax = st.slider("Dauer höchstens", *bounds("dmax_slider"), key="dmax_slider", help="Dauern gleichverteilt ganzzahlig von 1 bis zu diesem Wert.")
    seed = st.number_input("Zufalls-Seed der Instanz", *bounds("seed_input"), key="seed_input", step=1)
    st.button("🎲 Neue Instanz generieren", width="stretch", on_click=randomize_seed)
    st.markdown("**Live-Läufe**")
    budget = st.slider("Knotenbudget", *bounds("budget_slider"), key="budget_slider", step=1000,
                       help="Nach so vielen Suchknoten bricht ein Lauf ab; sein Ergebnis ist dann nur eine Schranke.")

# --- Experiment 1: das Handbeispiel Schritt für Schritt -----------------------------------------------------------------------------------------

st.markdown("## 🎯 Das Handbeispiel von Hand")
st.markdown(
    "Drei Aufträge auf drei Maschinen, Dauern 1 oder 2. Eine Operation steht als **Maschine / Dauer**:\n\n"
    + _md_table(
        ["Auftrag", "1. Operation", "2. Operation", "3. Operation"],
        [[j] + [f"M{m} / {d}" for m, d in job] for j, job in enumerate(HANDBEISPIEL.jobs)],
    )
    + "\n\nOperation (j, k) ist die k-te Operation von Auftrag j. **Frage:** Gibt es einen Plan mit Makespan höchstens H?"
)
az = _aufzaehlung()
a1, a2, a3, a4 = st.columns(4)
a1.metric("Reihenfolgen je Maschine, kombiniert", _zahl(az.kombinationen), delta="3! je Maschine, 3 Maschinen", delta_color="off")
a2.metric("davon zulässig (ohne Kreis)", _zahl(az.zulaessig), delta="Aufzählung aller Kombinationen", delta_color="off")
a3.metric("Optimaler Makespan", _zahl(az.optimum), delta="kein Plan mit Makespan 7 oder weniger", delta_color="off")
a4.metric("Kombinationen am Optimum", _zahl(az.am_optimum), delta_color="off", delta="von allen zulässigen")

st.subheader("🔬 Experiment 1: Schritt für Schritt bis zum Beweis")
st.caption("Die Suche rechnet die Entscheidungsfassung „Makespan höchstens H“. Wählen Sie Horizont und Stufe; der Schieberegler geht durch jeden Schritt der Propagation und der Suche, mit der Begründung.")
c1, c2 = st.columns(2)
hb_h = c1.radio("Horizont H", C.HB_HORIZONTS, key="hb_h_radio", horizontal=True, format_func=lambda h: f"H = {h}")
hb_stage = c2.radio("Stufe", C.STAGES, key="hb_stage_radio", horizontal=True, format_func=lambda s: C.STAGE_NAMES[s])
entscheidung = _handbeispiel(int(hb_h), int(hb_stage))
events = entscheidung.protokoll.ereignisse
if st.session_state.get("hb_sig") != (hb_h, hb_stage):
    st.session_state["hb_sig"] = (hb_h, hb_stage)
    st.session_state["hb_schritt"] = 1
st.session_state["hb_schritt"] = max(1, min(int(st.session_state.get("hb_schritt", 1)), len(events)))


def _schritt(delta):
    st.session_state["hb_schritt"] = max(1, min(len(events), st.session_state["hb_schritt"] + delta))


def _zum_ende():
    st.session_state["hb_schritt"] = len(events)


b1, b2, b3 = st.columns(3)
b1.button("← Zurück", on_click=_schritt, args=(-1,), width="stretch", key="hb_zurueck")
b2.button("Weiter →", on_click=_schritt, args=(1,), width="stretch", key="hb_weiter")
b3.button("Zum Ende", on_click=_zum_ende, width="stretch", key="hb_ende")
schritt = st.slider("Schritt", 1, len(events), key="hb_schritt") if len(events) > 1 else 1
ev_now = events[schritt - 1]
M = A.Modell(HANDBEISPIEL)
st.markdown(f"**Schritt {schritt} von {len(events)}** (Knoten {ev_now.knoten}, Tiefe {ev_now.tiefe}): {ev_now.text}")
st.plotly_chart(build_fenster(M, ev_now.est, ev_now.lst, int(hb_h)), width="stretch", key="hb_chart")
st.caption("Hell: das Fenster einer Operation (frühester Start bis spätestes Ende), dunkel: der **Pflichtteil** (der Zeitraum, in dem sie auf jeden Fall läuft). Rote Linie: Horizont H. "
           "Die Zustände sind die Fenster nach dem jeweiligen Schritt.")
if entscheidung.protokoll.abgeschnitten:
    st.warning(f"Die Spur ist nach {A.MAX_EREIGNISSE} Ereignissen abgeschnitten.")
kind, text = ev.verdict_handbeispiel(int(hb_h), int(hb_stage), _handbeispiel_knoten(int(hb_h)))
getattr(st, kind)(text)
with st.expander("Alle Schritte als Liste"):
    st.markdown(_md_table(["Nr.", "Knoten", "Art", "Begründung"], [[i + 1, e.knoten, e.art, e.text.replace("|", "/")] for i, e in enumerate(events)]))

st.markdown("---")

# --- Experiment 2: Stufen im Vergleich ---------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 2: Die Stufen im Vergleich")
st.caption(
    f"Vorgerechnet, nicht live: Knoten bis zum bewiesenen Optimum auf festen Zufalls-Job-Shops (Dauern 1 bis 9, Messskript `{C.MEASURE_SCRIPT}`, Datei `{C.SWEEPS_FILE}`). "
    "Jedes Optimum ist mit OR-Tools CP-SAT geprüft. Eine Stufe bricht am Knotenbudget ab, wenn sie dort noch nicht fertig ist: Dann ist die Zahl eine untere Schranke."
)
spalten = st.columns(2)
for sp, key in zip(spalten, ("5x5", "6x6")):
    reihe = REIHEN[key]
    rows = ev.statistik(reihe, (0, 1, 2))
    with sp:
        st.markdown(f"**{key.replace('x', ' × ')}: {len(reihe['instanzen'])} Instanzen, Budget {_zahl(reihe['budget'])}**")
        st.plotly_chart(build_verteilung({r["stufe"]: ev.knoten(reihe, r["stufe"]) for r in rows}, {r["stufe"]: r["abbrueche"] for r in rows}, reihe["budget"]), width="stretch", key=f"verteilung_{key}")
        st.markdown(_md_table(["Stufe", "Median", "90-%-Wert", "Maximum", "Abbrüche"], [[C.STAGE_SHORT[r["stufe"]], _zahl(r["median"]), _zahl(r["p90"]), _zahl(r["max"]), r["abbrueche"]] for r in rows]))
        kind, text = ev.verdict_stufen(rows, key.replace("x", " × "))
        getattr(st, kind)(text)

st.markdown("**Eine Einzelinstanz live rechnen** (Aufträge, Maschinen, Dauer und Zufalls-Seed aus der Seitenleiste)")
live_key = (int(jobs), int(machines), int(dmax), int(seed), int(budget))
if st.button(f"Rechnen: {jobs} × {machines}, Zufalls-Seed {seed}, Budget {_zahl(budget)}", key="live_knopf"):
    st.session_state["live_key"] = live_key
    L.stufen_einzel(live_key)
if st.session_state.get("live_key") == live_key:
    erg = L.einzel_aus_speicher(live_key)
    st.markdown(_md_table(["Stufe", "Knoten", "Fehlschläge", "Runden", "Edge-Finding-Aufrufe", "bester Makespan", "bewiesen"],
                          [[C.STAGE_NAMES[s], _zahl(e.z.knoten), _zahl(e.z.fehlschlaege), _zahl(e.z.runden), _zahl(e.z.ef_aufrufe), e.optimum, "ja" if e.bewiesen else "nein (Abbruch)"] for s, e in erg.items()]))
    kind, text = ev.verdict_einzel(erg, int(budget))
    getattr(st, kind)(text)
    beste = min(erg.values(), key=lambda e: (e.optimum, not e.bewiesen))
    inst = ev.instanz(ev.Settings(*live_key))
    ok, grund = A.pruefe_plan(inst, beste.plan)
    st.plotly_chart(build_gantt(A.Modell(inst), beste.plan), width="stretch", key="live_gantt")
    st.caption(f"Der beste gefundene Plan (Makespan {A.makespan(inst, beste.plan)}), vom unabhängigen Prüfer " + ("als zulässig bestätigt." if ok else f"**abgelehnt: {grund}**"))
else:
    st.info("Noch nichts gerechnet für diese Einstellungen: der Knopf startet den Lauf.")

st.markdown("---")

# --- Experiment 3: der Tail -----------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 3: Der Tail")
sw = DATA["tail"]
st.caption(
    f"Eingefroren und vorgerechnet (Messskript, Budget {_zahl(sw['budget'])}): unter {len(sw['scan_seeds'])} Zufalls-Seeds eines 8 × 8-Job-Shops der Fall mit dem größten Abstand zwischen Paar-Test und Edge-Finding, "
    "gewählt im Rückblick. Er ist also **kein typischer Fall**, sondern die Tail-Probe."
)
kind, text = ev.verdict_tail(sw, REIHEN["8x8"])
getattr(st, kind)(text)
if st.button(f"Live nachrechnen (Budget {_zahl(C.TAIL_BUDGET)})", key="tail_knopf"):
    st.session_state["tail_live"] = True
    L.tail(C.TAIL_BUDGET)
if st.session_state.get("tail_live"):
    ergs = L.tail_aus_speicher(C.TAIL_BUDGET)
    st.markdown(_md_table(["Stufe", "Knoten", "bewiesen", "bester Makespan"], [[C.STAGE_NAMES[s], _zahl(e.z.knoten), "ja" if e.bewiesen else "nein (Abbruch)", e.optimum] for s, e in ergs.items()]))

st.markdown("---")

# --- Experiment 4: woher die Ersparnis kommt -----------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 4: Woher die Ersparnis kommt")
st.caption("Zählung im Mini-CP über die festen Instanzen (vorgerechnet): welcher Schluss findet die Fehlschläge, wie viele Kanten setzt der Paar-Test, wie oft verengt Edge-Finding ein Fenster.")
gr = st.radio("Messreihe", ("5x5", "6x6"), horizontal=True, key="ursache_reihe", format_func=lambda k: k.replace("x", " × "))
ur = ev.ursachen(REIHEN[gr])
st.plotly_chart(build_ursachen(ur), width="stretch", key="ursachen_chart")
st.markdown(_md_table(
    ["Stufe", "Knoten", "Fehlschläge", "davon an der Wurzel", "Kanten durch Paar-Test", "Verengungen durch Edge-Finding"],
    [[C.STAGE_SHORT[u["stufe"]], _zahl(u["knoten"]), _zahl(u["fehlschlaege"]), _zahl(u["wurzel"]), _zahl(u["kanten_paar"]), _zahl(u["ef_verengungen"])] for u in ur],
))
st.caption("Summen über die Instanzen der Messreihe. Die Kanten des Paar-Tests zählen auch solche, die schon aus den Auftragsketten folgen.")
st.markdown("**Hypothese: Edge-Finding wirkt vor allem bei engem Horizont.** Beweis der Unerfüllbarkeit (Horizont = Optimum − 1) gegen Suche der ersten Lösung (Horizont = Optimum), Summe der Knoten; beides wechselt zusammen, Horizont und Aufgabenart sind hier nicht zu trennen:")
for key in ("5x5", "6x6"):
    kind, text = ev.verdict_horizont(DATA["horizont"], key)
    getattr(st, kind)(text)
with st.expander("Beweis: Überlappen die Pflichtteile zweier Operationen, scheitert der Paar-Test"):
    st.markdown(
        r"""
Der **Pflichtteil** einer Operation $a$ ist $[\mathrm{lst}_a,\ \mathrm{est}_a + d_a)$, nicht leer, wenn $\mathrm{lst}_a < \mathrm{est}_a + d_a$. Überlappen die Pflichtteile von $a$ und $b$, gilt (ohne Beschränkung der Allgemeinheit $\mathrm{lst}_a \ge \mathrm{lst}_b$)
$\mathrm{lst}_a < \mathrm{est}_a + d_a$ und $\mathrm{lst}_a < \mathrm{est}_b + d_b$. Dann ist

$$a \text{ vor } b \text{ unmöglich: } \mathrm{est}_a + d_a > \mathrm{lst}_a \ge \mathrm{lst}_b,$$

$$b \text{ vor } a \text{ unmöglich: } \mathrm{est}_b + d_b > \mathrm{lst}_a.$$

Also: **Pflichtteil-Überlappung ⇒ der Paar-Test scheitert.** Das ist das Timetabling bei Kapazität 1 (eine Maschine). Die Umkehrung gilt nicht: Der Paar-Test kann auch ohne überlappende Pflichtteile scheitern (der Test an Zufallsfenstern findet solche Fälle). Timetabling bei Kapazität größer 1 ist ein anderes Thema.
        """
    )

st.markdown("---")

# --- Erweiterung 11b ---------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Erweiterung: Gleicher Schluss, gleiche Knoten")
st.caption("Stufe 3 ersetzt die Intervallfassung des Edge-Findings durch den Θ-Λ-Baum (eigene Nachbildung, Quelle nicht gelesen). Vorgerechnet über dieselben Instanzen wie in Experiment 2; Rechenzeiten sind nicht gemessen.")
kind, text = ev.verdict_baum({k: REIHEN[k] for k in ("5x5", "6x6", "8x8")}, DATA["baum_filter"])
getattr(st, kind)(text)
rows3 = []
for key in ("5x5", "6x6", "8x8"):
    g, n = ev.gleiche_knoten(REIHEN[key], 2, 3)
    st3 = {r["stufe"]: r for r in ev.statistik(REIHEN[key], (2, 3))}
    rows3.append([key.replace("x", " × "), n, _zahl(st3[2]["median"]), _zahl(st3[3]["median"]), f"{g} von {n}"])
st.markdown(_md_table(["Größe", "Instanzen", "Median Stufe 2", "Median Stufe 3", "gleiche Knotenzahl"], rows3))
st.caption("Nicht umgesetzt: Detectable Precedences und Not-first/Not-last (weitere Filter auf einer Maschine); siehe README.")

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Ressource mit Kapazität 1** (eine Operation je Maschine) | Bei Kapazität größer 1 reicht der Paar-Test nicht mehr; dort arbeitet das Timetabling mit dem Profil der Pflichtteile und eine Energie-Überlastprüfung. Hier nicht gebaut. | Kumulative Ressourcen (RCPSP) |
| **Eine Verzweigungsregel, eine Startschranke** | Die Knotenzahlen gelten für diese Regel (kleinste Spielraumsumme, Paar mit früherem est zuerst) und den Dispatching-Plan als Start; andere Regeln verschieben die Zahlen. | – |
| **Kleine Instanzen** (bis 8 × 8, Dauern 1 bis 9, 10 bis 20 Instanzen je Größe) | Die Mediane sagen nichts über Benchmark-Instanzen oder 10 × 10 und mehr; Knoten sind keine Rechenzeit, und die Kosten je Knoten sind nicht gemessen. | Job-Shop-Heuristiken und CP-SAT als Maßstab |
| **Eigene Nachbildung des Edge-Findings** | Die Aussage „Θ-Λ-Baum bringt keine Suchersparnis“ gilt für diese Nachbildung und diese Instanzen, nicht für das Verfahren der Literatur im Allgemeinen. | – |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Lesehilfe.** Gegeben sind Aufträge mit je einer festen Folge von Operationen; jede Operation $o$ hat eine Maschine und eine ganzzahlige Dauer $d_o \ge 1$. Gesucht ist ein Plan (Startzeiten $s_o$) mit kleinstem Makespan, in dem die Operationen eines Auftrags nacheinander laufen und jede Maschine höchstens eine Operation zugleich bearbeitet.

| Symbol | Bedeutung |
|---|---|
| $d_o$ | Dauer der Operation $o$ |
| $\mathrm{est}_o,\ \mathrm{lst}_o$ | frühester und spätester Start (Fenster) |
| $\mathrm{lct}_o$ | spätestes Ende, $\mathrm{lst}_o + d_o$ |
| $H$ | Horizont: Makespan höchstens $H$ |
| $\Omega$ | Menge von Operationen auf einer Maschine |
| $\mathrm{est}_\Omega,\ \mathrm{lct}_\Omega,\ d_\Omega$ | kleinstes est, größtes lct, Summe der Dauern über $\Omega$ |

**Fenster.** Für den Horizont $H$ gilt für jede Operation $o$ eines Auftrags (Vorlauf: Summe der Dauern davor, Rest: Summe der Dauern ab $o$ einschließlich)

$$\mathrm{est}_o = \text{Vorlauf}_o, \qquad \mathrm{lst}_o = H - \text{Rest}_o.$$

**Disjunktion.** Für zwei Operationen $a, b$ auf einer Maschine

$$s_a + d_a \le s_b \quad \text{oder} \quad s_b + d_b \le s_a.$$

**Paar-Test (Stufe 1).** Die Reihenfolge „$a$ vor $b$“ ist noch möglich genau dann, wenn

$$\mathrm{est}_a + d_a \le \mathrm{lst}_b.$$

Ist weder „$a$ vor $b$“ noch „$b$ vor $a$“ möglich, gibt es keinen Plan; ist nur eine möglich, steht die Kante fest.

**Überlast (Stufe 2).** Passt die Summe der Dauern einer Menge nicht in ihr Zeitfenster, gibt es keinen Plan:

$$\mathrm{est}_\Omega + d_\Omega > \mathrm{lct}_\Omega \;\Rightarrow\; \text{Fehlschlag}.$$

**Edge-Finding (Stufe 2, einfache Fassung).** Für $i \notin \Omega$ gilt: Passt $i$ nicht mehr vor oder in die Menge, muss $i$ nach allen Operationen aus $\Omega$ laufen,

$$\min(\mathrm{est}_\Omega,\, \mathrm{est}_i) + d_\Omega + d_i > \mathrm{lct}_\Omega \;\Rightarrow\; \mathrm{est}_i \ge \mathrm{est}_\Omega + d_\Omega,$$

und symmetrisch muss $i$ vor allen Operationen aus $\Omega$ laufen,

$$\mathrm{est}_\Omega + d_\Omega + d_i > \max(\mathrm{lct}_\Omega,\, \mathrm{lct}_i) \;\Rightarrow\; \mathrm{lst}_i \le \mathrm{lct}_\Omega - d_\Omega - d_i.$$

In der Intervallfassung dieser Demo läuft $\Omega$ über alle Operationen einer Maschine, die ganz in ein Zeitfenster $[a, b]$ mit $a = \mathrm{est}_o$, $b = \mathrm{lct}_{o'}$ passen.

**Pflichtteil.** Der Zeitraum, in dem $a$ auf jeden Fall läuft:

$$[\mathrm{lst}_a,\ \mathrm{est}_a + d_a).$$

**Literatur.** Edge-Finding und der Θ-Λ-Baum sind Verfahren der Constraint-Programmierung; die Demo enthält eine eigene Nachbildung aus dem Gedächtnis, **die Quellen (Carlier und Pinson; Vilím und Mitarbeiter) sind nicht gelesen**. Die Korrektheit ist durch Tests gegen die Aufzählung abgesichert, nicht durch die Quelle.
        """
    )

sync_query_params({key: st.session_state[key] for key in SETTING_SPECS if key in st.session_state})

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zur Reihe: [SAT und CP: Konfliktlernen bis Wahl](https://sebastianhanisch.net/konzepte-sat-constraint-programming.html)."
)
