"""Datenmodelle für Treffer und Suchergebnisse."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class Treffer:
    id: str | None = None
    name: str = ""
    entfernung_km: float | None = None
    notdienst_von: str | None = None
    notdienst_bis: str | None = None
    dienstzeit: str | None = None
    strasse: str | None = None
    plz: str | None = None
    ort: str | None = None
    telefon: str | None = None
    fax: str | None = None
    breite: float | None = None
    laenge: float | None = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Suchergebnis:
    treffer: list[Treffer] = field(default_factory=list)
    radius_km: int | None = None
    vorschlaege: list[str] = field(default_factory=list)
    trefferblock: bool = False
