"""Unit-Tests für den HTML-Parser gegen die UX-Fixtures."""

from __future__ import annotations

from pathlib import Path

from notdienst.parser import parse_ergebnis, parse_formular

REPO = Path(__file__).resolve().parents[2]
FIXTURES = REPO / "tests" / "fixtures" / "ux"


def _lies(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_formular_liefert_c_hash_und_versteckte_felder():
    formular = parse_formular(_lies("notdienstsuche_form.html"))

    assert formular.path == "/notdienstsuche"
    assert formular.c_hash == "d60644fbe4920abed16b25ce29f3b7c8"
    namen = {name for name, _ in formular.params}
    assert "tx_aponetpharmacy_search[__trustedProperties]" in namen
    assert "tx_aponetpharmacy_search[__referrer][@request]" in namen


def test_jetzt_parst_drei_treffer_und_radius():
    ergebnis = parse_ergebnis(
        _lies("suche_heilbronn_jetzt.html"), angefragter_radius=5
    )

    assert ergebnis.trefferblock is True
    assert ergebnis.radius_km == 25
    assert len(ergebnis.treffer) == 3

    erster = ergebnis.treffer[0]
    assert erster.id == "1273042"
    assert erster.name == "Apotheke im Staufenberg-Zentrum"
    assert erster.entfernung_km == 3.22
    assert erster.notdienst_von == "2026-11-11T08:30"
    assert erster.notdienst_bis == "2026-11-12T08:30"
    assert (
        erster.dienstzeit
        == "Notdienst 11.11.2026 08:30 bis 12.11.2026 08:30"
    )
    assert erster.strasse == "Staufenbergstr. 31"
    assert erster.plz == "74081"
    assert erster.ort == "Heilbronn"
    assert erster.telefon == "+49 7131 899055"
    assert erster.fax == "+49 7131 899056"
    assert erster.breite == 49.1186511
    assert erster.laenge == 9.1932944


def test_samstag_parst_datum_und_entfernung():
    ergebnis = parse_ergebnis(_lies("suche_heilbronn_samstag.html"))

    assert len(ergebnis.treffer) == 3
    erster = ergebnis.treffer[0]
    assert erster.name == "Harfensteller Apotheke Wollhaus"
    assert erster.entfernung_km == 0.28
    assert erster.notdienst_von == "2026-11-14T08:30"
    assert erster.notdienst_bis == "2026-11-15T08:30"


def test_formularseite_ohne_treffer_ist_kein_quellfehler():
    ergebnis = parse_ergebnis(_lies("suche_ohne_treffer.html"))

    assert ergebnis.treffer == []
    assert ergebnis.trefferblock is False
    assert ergebnis.vorschlaege == []
