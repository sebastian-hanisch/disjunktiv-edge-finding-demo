"""Gemeinsame Fixtures: die Mini-Instanzen, an denen jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dje_scenario import HANDBEISPIEL, Instance, as_instance  # noqa: E402


@pytest.fixture
def hb():
    """Das Handbeispiel (README und App): 3 Aufträge, 3 Maschinen, Optimum 8, bei Horizont 7 Beweis ohne Plan.

    Operation (j, k) = Nummer 3 j + k:  (0,0) M2 d2 | (0,1) M0 d2 | (0,2) M1 d1 | (1,0) M0 d2 | (1,1) M2 d1 | (1,2) M1 d2 | (2,0) M2 d2 | (2,1) M0 d1 | (2,2) M1 d2."""
    return HANDBEISPIEL


@pytest.fixture
def zwei_auftraege():
    """Kleinste Instanz mit Wartezeit: zwei Aufträge auf zwei Maschinen, Dauern 2 und 3 (Optimum 5, von Hand: beide Reihenfolgen auf M1 sind zulässig)."""
    return as_instance([[(0, 2), (1, 3)], [(1, 2), (0, 3)]])


def einzelmaschine(dauern):
    """Eine Maschine mit lauter Ein-Operations-Aufträgen: der Schauplatz für Edge-Finding auf einer Ressource."""
    return Instance(tuple(((0, d),) for d in dauern))
