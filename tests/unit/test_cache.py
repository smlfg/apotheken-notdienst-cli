"""Unit-Tests für den Such-Cache: gültige und kaputte Einträge."""

from __future__ import annotations

import json

from notdienst import cache
from notdienst.models import Suchergebnis, Treffer


def _speichere_und_lese(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    ergebnis = Suchergebnis(
        treffer=[
            Treffer(
                name="Test-Apotheke",
                entfernung_km=1.5,
                notdienst_von="2026-11-11T08:30",
                notdienst_bis="2026-11-12T08:30",
                strasse="Testweg 1",
                plz="74072",
                ort="Heilbronn",
            )
        ],
        radius_km=25,
        trefferblock=True,
    )
    cache.speichere(
        "https://aponet.example.invalid", "Heilbronn", None, None, 5, ergebnis
    )
    pfad = cache._datei(
        "https://aponet.example.invalid", "Heilbronn", None, None, 5
    )
    return pfad


def test_gueltiger_eintrag_wird_gelesen(tmp_path, monkeypatch):
    pfad = _speichere_und_lese(tmp_path, monkeypatch)

    ergebnis = cache.lade(
        "https://aponet.example.invalid", "Heilbronn", None, None, 5
    )

    assert pfad.is_file()
    assert ergebnis is not None
    assert ergebnis.radius_km == 25
    assert ergebnis.treffer[0].name == "Test-Apotheke"


def test_falsch_typisierter_treffer_wird_verworfen(tmp_path, monkeypatch):
    pfad = _speichere_und_lese(tmp_path, monkeypatch)
    daten = json.loads(pfad.read_text(encoding="utf-8"))
    daten["treffer"][0]["entfernung_km"] = "x"
    pfad.write_text(json.dumps(daten), encoding="utf-8")

    assert (
        cache.lade(
            "https://aponet.example.invalid", "Heilbronn", None, None, 5
        )
        is None
    )
    assert not pfad.exists()


def test_falsch_typisierter_radius_wird_verworfen(tmp_path, monkeypatch):
    pfad = _speichere_und_lese(tmp_path, monkeypatch)
    daten = json.loads(pfad.read_text(encoding="utf-8"))
    daten["radius_km"] = "25"
    pfad.write_text(json.dumps(daten), encoding="utf-8")

    assert (
        cache.lade(
            "https://aponet.example.invalid", "Heilbronn", None, None, 5
        )
        is None
    )
    assert not pfad.exists()
