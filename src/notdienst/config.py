"""Config-Datei mit dem gespeicherten Standard-Ort."""

from __future__ import annotations

import json
import os
from pathlib import Path

from .errors import LocalError

_NAME = "apotheken-notdienst-cli"


def config_dir() -> Path:
    basis = os.environ.get("XDG_CONFIG_HOME")
    if basis:
        return Path(basis) / _NAME
    return Path.home() / ".config" / _NAME


def config_pfad() -> Path:
    return config_dir() / "config.json"


def standard_ort() -> str | None:
    pfad = config_pfad()
    try:
        inhalt = pfad.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    except OSError:
        raise LocalError(
            f"Config-Datei ist nicht lesbar: {pfad}.",
            "Dateirechte prüfen oder notdienst standard ORT neu setzen.",
        ) from None
    try:
        daten = json.loads(inhalt)
    except (ValueError, TypeError):
        raise LocalError(
            f"Config-Datei ist unlesbar: {pfad}.",
            "notdienst standard ORT neu setzen.",
        ) from None
    ort = daten.get("standard_ort") if isinstance(daten, dict) else None
    if ort is None:
        return None
    if not isinstance(ort, str) or not ort.strip():
        raise LocalError(
            f"Config-Datei enthält keinen gültigen Standard-Ort: {pfad}.",
            "notdienst standard ORT neu setzen.",
        )
    return ort.strip()


def speichere_standard_ort(ort: str) -> Path:
    verzeichnis = config_dir()
    verzeichnis.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(verzeichnis, 0o700)
    except OSError:
        pass

    pfad = config_pfad()
    daten = json.dumps({"standard_ort": ort}, ensure_ascii=False) + "\n"
    beschreibung = os.open(pfad, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        with os.fdopen(beschreibung, "w", encoding="utf-8") as datei:
            datei.write(daten)
    finally:
        try:
            os.chmod(pfad, 0o600)
        except OSError:
            pass
    return pfad
