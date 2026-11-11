"""Datumsauflösung für heute, morgen, Wochentage und ISO-Daten."""

from __future__ import annotations

import os
import re
from datetime import date, timedelta

from .errors import InputError

_WOCHENTAGE = [
    "Montag",
    "Dienstag",
    "Mittwoch",
    "Donnerstag",
    "Freitag",
    "Samstag",
    "Sonntag",
]
_WOCHENTAG_INDEX = {
    name.lower(): index for index, name in enumerate(_WOCHENTAGE)
}
_ISO_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_FENSTER = 14


def heute() -> date:
    wert = os.environ.get("NOTDIENST_HEUTE", "").strip()
    if not wert:
        return date.today()
    if not _ISO_RE.match(wert):
        raise InputError(
            f"NOTDIENST_HEUTE ist kein gültiges Datum: {wert!r}.",
            "NOTDIENST_HEUTE als JJJJ-MM-TT setzen oder entfernen.",
        )
    try:
        return date.fromisoformat(wert)
    except ValueError:
        raise InputError(
            f"NOTDIENST_HEUTE ist kein gültiges Datum: {wert!r}.",
            "NOTDIENST_HEUTE als JJJJ-MM-TT setzen oder entfernen.",
        ) from None


def de(datum: date) -> str:
    return f"{datum.day:02d}.{datum.month:02d}.{datum.year:04d}"


def wochentag(datum: date) -> str:
    return _WOCHENTAGE[datum.weekday()]


def datum_anzeige(datum: date, heute_datum: date) -> str:
    if datum == heute_datum:
        return f"heute ({de(datum)})"
    return f"{wochentag(datum)}, {de(datum)}"


def parse_datum(wert: str, heute_datum: date) -> date:
    roh = wert.strip()
    klein = roh.lower()

    if klein == "heute":
        ziel = heute_datum
    elif klein == "morgen":
        ziel = heute_datum + timedelta(days=1)
    elif klein in _WOCHENTAG_INDEX:
        differenz = (_WOCHENTAG_INDEX[klein] - heute_datum.weekday()) % 7
        ziel = heute_datum + timedelta(days=differenz)
    elif _ISO_RE.match(roh):
        try:
            ziel = date.fromisoformat(roh)
        except ValueError:
            raise InputError(
                f"Ungültiges Datum: {wert!r}.",
                "Datum als heute, morgen, Wochentag oder JJJJ-MM-TT angeben.",
            ) from None
    else:
        raise InputError(
            f"Ungültiges Datum: {wert!r}.",
            "Datum als heute, morgen, Wochentag oder JJJJ-MM-TT angeben.",
        )

    ende = heute_datum + timedelta(days=_FENSTER)
    if ziel < heute_datum or ziel > ende:
        raise InputError(
            f"Datum außerhalb des gültigen Bereichs: {de(ziel)}.",
            f"Datum zwischen {de(heute_datum)} und {de(ende)} wählen"
            " (notdienst datum JJJJ-MM-TT).",
        )
    return ziel
