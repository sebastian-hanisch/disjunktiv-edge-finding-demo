"""Live-Knöpfe: Zwischenspeicher und Fortschrittsanzeige.

Jede Live-Aktion (Einzelinstanz mit drei Stufen, Tail-Fall mit zwei Stufen) besteht aus Einheiten (eine Stufe). Jede Einheit ist eine reine Funktion ihrer Parameter und liegt
einzeln im Zwischenspeicher (`st.cache_data`, kleine `max_entries`); die Anzeige zählt die fertigen Stufen (`mit_fortschritt`). Ein zweiter Klick mit denselben Einstellungen
antwortet aus dem Speicher. Innerhalb einer Stufe gibt es keinen Zwischenstand (ein einzelner Suchlauf). Die Ergebnisse sind bitgleich zu den ungespeicherten Funktionen
(`tests/test_live.py`). Rechnung, Zahlen und Aussagen ändern sich nicht."""

import streamlit as st

import dje_constants as C
import dje_evaluation as ev

TAIL_STUFEN = (1, 2)


@st.cache_data(show_spinner=False, max_entries=24)
def stufe_lauf(jobs, machines, dmax, seed, budget, stufe):
    return ev.live_stufe(ev.Settings(jobs, machines, dmax, seed, budget), stufe)


@st.cache_data(show_spinner=False, max_entries=4)
def tail_stufe(budget, stufe):
    return ev.tail_stufe(budget, stufe)


def mit_fortschritt(titel: str, schritte: list, rechne) -> list:
    """Führt die Schritte nacheinander aus und zeigt, wie viele fertig sind. `schritte`: Liste aus (Beschriftung, Argumente); `rechne(*Argumente)` liefert das Ergebnis
    (aus dem Zwischenspeicher oder frisch gerechnet). Rückgabe: die Ergebnisse in der Reihenfolge der Schritte."""
    n = len(schritte)
    ergebnisse = []
    with st.status(titel, expanded=True) as status:
        balken = st.progress(0.0, text=f"0 von {n} fertig")
        for i, (beschriftung, args) in enumerate(schritte):
            balken.progress(i / n, text=f"{beschriftung} (Schritt {i + 1} von {n})")
            ergebnisse.append(rechne(*args))
        balken.progress(1.0, text=f"{n} von {n} fertig")
        status.update(label=f"{titel}: fertig", state="complete", expanded=False)
    return ergebnisse


def stufen_einzel(live_key: tuple) -> dict:
    """Die Einzelinstanz mit allen Stufen, mit Fortschrittsanzeige. `live_key` = (jobs, machines, dmax, seed, budget)."""
    jobs, machines, dmax, seed, budget = live_key
    schritte = [(C.STAGE_NAMES[s], (jobs, machines, dmax, seed, budget, s)) for s in (0, 1, 2)]
    laeufe = mit_fortschritt("Rechnet die Stufen bis zum Beweis des Optimums oder bis zum Knotenbudget", schritte, stufe_lauf)
    return dict(zip((0, 1, 2), laeufe))


def einzel_aus_speicher(live_key: tuple) -> dict:
    """Wie `stufen_einzel`, ohne Anzeige (aus dem Zwischenspeicher; rechnet nur, was dort fehlt)."""
    jobs, machines, dmax, seed, budget = live_key
    return {s: stufe_lauf(jobs, machines, dmax, seed, budget, s) for s in (0, 1, 2)}


def tail(budget: int) -> dict:
    """Den eingefrorenen Tail-Fall mit Stufe 1 und Stufe 2, mit Fortschrittsanzeige."""
    schritte = [(C.STAGE_NAMES[s], (budget, s)) for s in TAIL_STUFEN]
    return dict(zip(TAIL_STUFEN, mit_fortschritt("Rechnet Stufe 1 und Stufe 2 auf dem eingefrorenen Fall", schritte, tail_stufe)))


def tail_aus_speicher(budget: int) -> dict:
    """Wie `tail`, ohne Anzeige."""
    return {s: tail_stufe(budget, s) for s in TAIL_STUFEN}
