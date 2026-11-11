"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen, jedes Preset verspricht, was es hält."""

import dje_algorithm as A
import dje_constants as C
import dje_evaluation as ev
import dje_presets as P
from dje_scenario import HANDBEISPIEL


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_slider_bounds():
    for name, preset in C.PRESETS.items():
        for key, state_key in P.PRESET_KEYS.items():
            spec = P.SETTING_SPECS[state_key]
            assert spec.lo <= preset[key] <= spec.hi, (name, key)
        assert preset["hb_h"] in C.HB_HORIZONTS and preset["hb_stage"] in C.STAGES


def test_default_preset_equals_the_default_settings():
    assert ev.Settings(**C.PRESETS["Handbeispiel: Makespan ≤ 7 (Beweis)"]) == ev.Settings()


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)


def test_presets_are_pairwise_different():
    """Sonst könnte das aktive Preset nicht eindeutig hervorgehoben werden."""
    werte = [tuple(sorted(p.items())) for p in C.PRESETS.values()]
    assert len(set(werte)) == len(werte)


def test_the_two_handbook_presets_keep_what_their_help_says():
    """Hilfetext: Horizont 7 = Beweis (Stufe 2: 1 Knoten, Stufe 0: 17), Horizont 8 = erste Lösung (Stufe 0: 10 Knoten, Stufe 1 und 2: 2)."""
    p7, p8 = C.PRESETS["Handbeispiel: Makespan ≤ 7 (Beweis)"], C.PRESETS["Handbeispiel: Makespan ≤ 8 (erste Lösung)"]
    assert (p7["hb_h"], p8["hb_h"]) == (7, 8)
    e7 = {s: A.entscheide(HANDBEISPIEL, 7, s) for s in (0, 1, 2)}
    assert not e7[2].gefunden and (e7[2].z.knoten, e7[0].z.knoten) == (1, 17)
    e8 = {s: A.entscheide(HANDBEISPIEL, 8, s) for s in (0, 1, 2)}
    assert all(e.gefunden for e in e8.values()) and (e8[0].z.knoten, e8[1].z.knoten, e8[2].z.knoten) == (10, 2, 2)
    h7, h8 = C.PRESET_HELP["Handbeispiel: Makespan ≤ 7 (Beweis)"], C.PRESET_HELP["Handbeispiel: Makespan ≤ 8 (erste Lösung)"]
    assert "(1 Knoten)" in h7 and "17" in h7 and "nach 10 Knoten" in h8 and "nach 2" in h8


def test_the_random_presets_name_their_size():
    for name, (jobs, machines) in (("Zufall 5 × 5", (5, 5)), ("Zufall 6 × 6", (6, 6))):
        assert (C.PRESETS[name]["jobs"], C.PRESETS[name]["machines"]) == (jobs, machines)
        assert f"{jobs} Aufträgen und {machines} Maschinen" in C.PRESET_HELP[name]


def test_the_sweep_seeds_are_the_documented_counts():
    assert (len(C.SWEEP_5X5_SEEDS), len(C.SWEEP_6X6_SEEDS), len(C.SWEEP_8X8_SEEDS)) == (10, 20, 10)
