"""Fehlerklassen mit Exit-Code und nächstem Schritt."""

from __future__ import annotations


class NotdienstError(Exception):
    exit_code = 1

    def __init__(
        self,
        meldung: str,
        naechster_schritt: str,
        *,
        vorschlaege: list[str] | None = None,
    ) -> None:
        super().__init__(meldung)
        self.meldung = meldung
        self.naechster_schritt = naechster_schritt
        self.vorschlaege = vorschlaege or []


class LocalError(NotdienstError):
    exit_code = 1


class InputError(NotdienstError):
    exit_code = 2


class AmbiguousError(InputError):
    pass


class SourceError(NotdienstError):
    exit_code = 3


class ParseError(SourceError):
    pass
