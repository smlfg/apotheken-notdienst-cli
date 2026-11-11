"""Unit-Tests für Datumsauflösung und Anzeige."""

from __future__ import annotations

from datetime import date

import pytest

from notdienst import dates
from notdienst.errors import InputError

HEUTE = date(2026, 11, 11)


@pytest.mark.parametrize(
    ("wert", "erwartet"),
    [
        ("heute", date(2026, 11, 11)),
        ("HEUTE", date(2026, 11, 11)),
        ("morgen", date(2026, 11, 12)),
        ("samstag", date(2026, 11, 14)),
        ("mittwoch", date(2026, 11, 11)),
        ("montag", date(2026, 11, 16)),
        ("2026-11-14", date(2026, 11, 14)),
    ],
)
def test_parse_datum(wert, erwartet):
    assert dates.parse_datum(wert, HEUTE) == erwartet


@pytest.mark.parametrize(
    "wert", ["gestern", "2026-11-10", "2026-11-26", "2026-13-01", ""]
)
def test_parse_datum_lehnt_ungueltiges_ab(wert):
    with pytest.raises(InputError) as fehler:
        dates.parse_datum(wert, HEUTE)
    assert fehler.value.exit_code == 2
    assert fehler.value.naechster_schritt


def test_anzeige_heute_und_wochentag():
    assert dates.datum_anzeige(HEUTE, HEUTE) == "heute (11.11.2026)"
    assert (
        dates.datum_anzeige(date(2026, 11, 14), HEUTE)
        == "Samstag, 14.11.2026"
    )


def test_heute_aus_env(monkeypatch):
    monkeypatch.setenv("NOTDIENST_HEUTE", "2026-11-11")
    assert dates.heute() == date(2026, 11, 11)


def test_heute_lehnt_kaputte_env_ab(monkeypatch):
    monkeypatch.setenv("NOTDIENST_HEUTE", "11.11.2026")
    with pytest.raises(InputError):
        dates.heute()
