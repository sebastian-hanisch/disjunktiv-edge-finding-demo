"""Konstanten: Regler-Grenzen, feste Annahmen, Farben und Presets."""

JOBS_MIN, JOBS_MAX, DEFAULT_JOBS = 3, 6, 4
MACHINES_MIN, MACHINES_MAX, DEFAULT_MACHINES = 3, 6, 4
DMAX_MIN, DMAX_MAX, DMAX_DEFAULT = 3, 9, 9
SEED_MAX, DEFAULT_SEED = 999999, 7
BUDGET_MIN, BUDGET_MAX, DEFAULT_BUDGET = 1000, 50000, 20000   # Knotenbudget der Live-Läufe (Experiment 2)
TAIL_BUDGET = 20000                                          # Knotenbudget des Live-Nachrechnens im Tail-Experiment

HB_HORIZONTS = (7, 8)                                        # Handbeispiel: „Makespan <= 7“ (Beweis) und „<= 8“ (erste Lösung)
DEFAULT_HB_H = 7
STAGES = (0, 1, 2)                                           # Gerüst: Stufe 0 Vorrang, 1 + Paar-Test, 2 + Edge-Finding (Intervallfassung)
DEFAULT_HB_STAGE = 2

STAGE_NAMES = {
    0: "Stufe 0: nur Vorrang",
    1: "Stufe 1: + Paar-Test",
    2: "Stufe 2: + Edge-Finding",
    3: "Stufe 3: + Θ-Λ-Baum",
}
STAGE_SHORT = {0: "Vorrang", 1: "+ Paar-Test", 2: "+ Edge-Finding", 3: "+ Θ-Λ-Baum"}

# Messreihen (vorgerechnet in dje_sweeps.json, Messskript tools/messung_sweeps.py): feste Seeds, nie ein einzelner Seed als Befund
SWEEP_5X5_SEEDS = tuple(range(1, 11))
SWEEP_6X6_SEEDS = tuple(range(1, 21))
SWEEP_8X8_SEEDS = tuple(range(1, 11))
SWEEP_BUDGET_SMALL = 50000    # 5 x 5 und 6 x 6
SWEEP_BUDGET_8X8 = 100000
SWEEPS_FILE = "dje_sweeps.json"
MEASURE_SCRIPT = "tools/messung_sweeps.py"

COLOR_WINDOW = "rgba(76,120,168,0.28)"
COLOR_WINDOW_LINE = "#4c78a8"
COLOR_MANDATORY = "#2F6B65"
COLOR_HORIZON = "#c0392b"
COLOR_STAGE = {0: "#9a9a9a", 1: "#4c78a8", 2: "#2F6B65", 3: "#b07aa1"}

PRESETS = {
    "Handbeispiel: Makespan ≤ 7 (Beweis)": {"jobs": DEFAULT_JOBS, "machines": DEFAULT_MACHINES, "dmax": DMAX_DEFAULT, "seed": DEFAULT_SEED,
                                           "budget": DEFAULT_BUDGET, "hb_h": 7, "hb_stage": 2},
    "Handbeispiel: Makespan ≤ 8 (erste Lösung)": {"jobs": DEFAULT_JOBS, "machines": DEFAULT_MACHINES, "dmax": DMAX_DEFAULT, "seed": DEFAULT_SEED,
                                                 "budget": DEFAULT_BUDGET, "hb_h": 8, "hb_stage": 2},
    "Zufall 5 × 5": {"jobs": 5, "machines": 5, "dmax": DMAX_DEFAULT, "seed": 3, "budget": DEFAULT_BUDGET, "hb_h": 7, "hb_stage": 2},
    "Zufall 6 × 6": {"jobs": 6, "machines": 6, "dmax": DMAX_DEFAULT, "seed": 3, "budget": DEFAULT_BUDGET, "hb_h": 7, "hb_stage": 2},
}
PRESET_HELP = {
    "Handbeispiel: Makespan ≤ 7 (Beweis)": "Das 3 × 3-Handbeispiel mit Horizont 7: Es gibt keinen Plan mit Makespan 7 oder weniger. Stufe 2 beweist das an der Wurzel (1 Knoten), Stufe 0 braucht 17.",
    "Handbeispiel: Makespan ≤ 8 (erste Lösung)": "Dasselbe Handbeispiel mit Horizont 8 (dem Optimum): Die Suche findet einen Plan, Stufe 0 nach 10 Knoten, Stufe 1 und 2 nach 2.",
    "Zufall 5 × 5": "Zufalls-Job-Shop mit 5 Aufträgen und 5 Maschinen (Dauern 1 bis 9, Zufalls-Seed 3) für die Stufen im Vergleich.",
    "Zufall 6 × 6": "Zufalls-Job-Shop mit 6 Aufträgen und 6 Maschinen (Dauern 1 bis 9, Zufalls-Seed 3): die Stufen im Vergleich; Stufe 0 braucht hier oft tausend Knoten und mehr.",
}
