"""End-to-end Smoke-Test via Streamlits offiziellem AppTest-Framework: laedt app.py mit den
Standardeinstellungen, klickt jeden Preset-Button und faehrt jeden Slider an seine Grenzen und prueft, dass
kein Python-Fehler auftritt - insbesondere `streamlit.errors.StreamlitDuplicateElementId` (mehrere
st.plotly_chart-Aufrufe ohne eindeutiges key= koennen zufaellig identischen Inhalt rendern und kollidieren)
und `StreamlitAPIException` bei Slidern mit berechneten Grenzen (min == max)."""

import os

from streamlit.testing.v1 import AppTest

APP_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))  # unter Last (parallele Läufe) reichen 180 s nicht immer; Umgebungsvariable zum Anpassen
AUTOPLAY_MARKER = "\u25b6"  # Auto-Play-Buttons (Animation mit sleep) im Smoke-Test auslassen


def _fresh_app() -> AppTest:
    at = AppTest.from_file(APP_PATH)
    at.run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    return at


def test_app_loads_without_exception():
    _fresh_app()


def test_every_button_click_does_not_raise():
    labels = [b.label for b in _fresh_app().button]
    assert labels, "keine Buttons gefunden"
    for index, label in enumerate(labels):
        if AUTOPLAY_MARKER in label:
            continue
        at = _fresh_app()
        at.button[index].click().run(timeout=TIMEOUT)
        assert not at.exception, (label, [str(e) for e in at.exception])


def test_every_slider_at_its_min_and_max_does_not_raise():
    labels = [s.label for s in _fresh_app().slider]
    assert labels, "keine Slider gefunden"
    for index, label in enumerate(labels):
        for edge in ("min", "max"):
            at = _fresh_app()
            slider = at.slider[index]
            value = slider.min if edge == "min" else slider.max
            if isinstance(slider.value, int):
                value = int(value)
            slider.set_value(value).run(timeout=TIMEOUT)
            assert not at.exception, (label, edge, [str(e) for e in at.exception])


def test_handbook_horizon_and_stage_combinations_do_not_raise():
    """Alle sechs Kombinationen aus Horizont (7, 8) und Stufe (0, 1, 2), jeweils bis zum letzten Schritt und zurück."""
    for h in (7, 8):
        for stufe in (0, 1, 2):
            at = _fresh_app()
            at.radio(key="hb_h_radio").set_value(h).run(timeout=TIMEOUT)
            at.radio(key="hb_stage_radio").set_value(stufe).run(timeout=TIMEOUT)
            assert not at.exception, (h, stufe, [str(e) for e in at.exception])
            at.button(key="hb_ende").click().run(timeout=TIMEOUT)
            assert not at.exception, (h, stufe)
            letzter = at.session_state["hb_schritt"]
            assert letzter >= 2
            at.button(key="hb_zurueck").click().run(timeout=TIMEOUT)
            assert at.session_state["hb_schritt"] == letzter - 1
            at.button(key="hb_weiter").click().run(timeout=TIMEOUT)
            assert at.session_state["hb_schritt"] == letzter and not at.exception


def test_changing_horizon_or_stage_restarts_the_step_view():
    at = _fresh_app()
    at.button(key="hb_ende").click().run(timeout=TIMEOUT)
    assert at.session_state["hb_schritt"] > 1
    at.radio(key="hb_stage_radio").set_value(0).run(timeout=TIMEOUT)
    assert at.session_state["hb_schritt"] == 1


def test_the_handbook_verdict_names_the_known_node_counts():
    """Horizont 7 (Standard): Beweis in 1 Knoten auf Stufe 2; Knoten je Stufe 17, 3, 1."""
    at = _fresh_app()
    texte = [s.value for s in at.success]
    assert any("keinen Plan mit Makespan höchstens 7" in t and "Stufe 0: 17, Stufe 1: 3, Stufe 2: 1" in t for t in texte)


def test_live_run_shows_a_checked_plan_for_the_default_instance():
    at = _fresh_app()
    at.button(key="live_knopf").click().run(timeout=TIMEOUT)
    assert not at.exception
    assert any("als zulässig bestätigt" in c.value for c in at.caption)
    assert any("Einzelinstanz, kein Median" in i.value for i in at.info)


def test_tail_live_run_does_not_raise():
    at = _fresh_app()
    at.button(key="tail_knopf").click().run(timeout=TIMEOUT)
    assert not at.exception
    assert any("nein (Abbruch)" in m.value for m in at.markdown)
