"""Kurzzeit-Cache für Suchanfragen (10 Minuten)."""

from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path

from .models import Suchergebnis, Treffer

_NAME = "apotheken-notdienst-cli"
_TTL = 600


def cache_dir() -> Path:
    basis = os.environ.get("XDG_CACHE_HOME")
    if basis:
        return Path(basis) / _NAME
    return Path.home() / ".cache" / _NAME


def _schluessel(
    base_url: str,
    ort: str,
    datum: str | None,
    strasse: str | None,
    radius: int,
) -> str:
    roh = "\x1f".join(
        [
            base_url,
            ort.lower(),
            datum or "",
            (strasse or "").lower(),
            str(radius),
        ]
    )
    return hashlib.sha256(roh.encode("utf-8")).hexdigest()


def _datei(
    base_url: str,
    ort: str,
    datum: str | None,
    strasse: str | None,
    radius: int,
) -> Path:
    return cache_dir() / f"{_schluessel(base_url, ort, datum, strasse, radius)}.json"


def lade(
    base_url: str,
    ort: str,
    datum: str | None,
    strasse: str | None,
    radius: int,
) -> Suchergebnis | None:
    pfad = _datei(base_url, ort, datum, strasse, radius)
    try:
        daten = json.loads(pfad.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return None
    if not isinstance(daten, dict):
        return None
    try:
        alter = time.time() - float(daten.get("ts", 0))
    except (TypeError, ValueError):
        return None
    if alter < 0 or alter > _TTL:
        try:
            pfad.unlink()
        except OSError:
            pass
        return None

    roh_treffer = daten.get("treffer")
    if not isinstance(roh_treffer, list):
        return None
    erlaubt = set(Treffer.__dataclass_fields__)
    treffer: list[Treffer] = []
    try:
        for eintrag in roh_treffer:
            if not isinstance(eintrag, dict):
                return None
            treffer.append(Treffer(**{k: v for k, v in eintrag.items() if k in erlaubt}))
        radius_km = daten.get("radius_km")
        radius_km = int(radius_km) if radius_km is not None else None
    except (TypeError, ValueError):
        return None
    return Suchergebnis(
        treffer=treffer, radius_km=radius_km, trefferblock=True
    )


def speichere(
    base_url: str,
    ort: str,
    datum: str | None,
    strasse: str | None,
    radius: int,
    ergebnis: Suchergebnis,
) -> None:
    verzeichnis = cache_dir()
    try:
        verzeichnis.mkdir(parents=True, exist_ok=True)
        os.chmod(verzeichnis, 0o700)
    except OSError:
        return
    pfad = _datei(base_url, ort, datum, strasse, radius)
    daten = {
        "ts": time.time(),
        "radius_km": ergebnis.radius_km,
        "treffer": [treffer.to_dict() for treffer in ergebnis.treffer],
    }
    try:
        pfad.write_text(json.dumps(daten, ensure_ascii=False), encoding="utf-8")
    except OSError:
        return
