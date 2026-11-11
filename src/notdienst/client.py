"""HTTP-Client für die aponet-Notdienstsuche (nur lesende GETs)."""

from __future__ import annotations

import os
from urllib.parse import urlsplit

import httpx

from . import cache
from .errors import InputError, SourceError
from .models import Suchergebnis
from .parser import Suchformular, parse_ergebnis, parse_formular

STANDARD_BASE_URL = "https://www.aponet.de"
USER_AGENT = (
    "apotheken-notdienst-cli "
    "(+https://github.com/smlfg/apotheken-notdienst-cli)"
)

_FELD = "tx_aponetpharmacy_search[search]"


def _base_url(wert: str | None) -> str:
    roh = (wert if wert is not None else os.environ.get("NOTDIENST_BASE_URL", ""))
    roh = roh.strip() or STANDARD_BASE_URL
    fehler = InputError(
        f"Ungültige Basis-URL: {roh!r}.",
        "NOTDIENST_BASE_URL als http(s)://host[:port] setzen oder entfernen.",
    )
    try:
        teile = urlsplit(roh)
        _ = teile.port
    except ValueError:
        raise fehler from None
    if (
        teile.scheme not in {"http", "https"}
        or not teile.netloc
        or teile.hostname is None
    ):
        raise fehler
    return roh.rstrip("/")


class Client:
    def __init__(
        self,
        base_url: str | None = None,
        *,
        timeout: float = 15.0,
        transport: httpx.BaseTransport | None = None,
        use_cache: bool = True,
    ) -> None:
        self.base_url = _base_url(base_url)
        self.use_cache = use_cache
        self._formular: Suchformular | None = None
        self._client = httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": USER_AGENT},
            transport=transport,
        )

    def __enter__(self) -> "Client":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def close(self) -> None:
        self._client.close()

    def _get(self, url: str, params: list[tuple[str, str]] | None = None) -> str:
        try:
            antwort = self._client.get(url, params=params)
        except httpx.TimeoutException:
            raise SourceError(
                "Die Abfrage bei aponet.de hat zu lange gedauert.",
                "Später erneut versuchen oder die Netzverbindung prüfen.",
            ) from None
        except httpx.RequestError:
            raise SourceError(
                "aponet.de ist nicht erreichbar.",
                "Netzverbindung prüfen und später erneut versuchen.",
            ) from None
        if antwort.status_code != 200:
            raise SourceError(
                f"aponet.de antwortet mit HTTP {antwort.status_code}.",
                "Später erneut versuchen; hilft das nicht, die Quelle prüfen.",
            )
        return antwort.text

    def _hole_formular(self) -> Suchformular:
        if self._formular is None:
            self._formular = parse_formular(
                self._get(f"{self.base_url}/notdienstsuche")
            )
        return self._formular

    def suche(
        self,
        ort: str,
        *,
        datum: str | None = None,
        strasse: str | None = None,
        radius: int = 5,
    ) -> Suchergebnis:
        if self.use_cache:
            zwischengespeichert = cache.lade(
                self.base_url, ort, datum, strasse, radius
            )
            if zwischengespeichert is not None:
                return zwischengespeichert

        formular = self._hole_formular()
        params = list(formular.params)
        params.extend(
            [
                (f"{_FELD}[plzort]", ort.lower()),
                (f"{_FELD}[date]", datum or ""),
                (f"{_FELD}[street]", strasse or ""),
                (f"{_FELD}[radius]", str(radius)),
            ]
        )
        ergebnis = parse_ergebnis(
            self._get(f"{self.base_url}{formular.path}", params),
            angefragter_radius=radius,
        )
        if self.use_cache and ergebnis.trefferblock:
            cache.speichere(
                self.base_url, ort, datum, strasse, radius, ergebnis
            )
        return ergebnis
