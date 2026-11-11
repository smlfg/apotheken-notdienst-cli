"""Parser für die aponet-Notdienstsuche."""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import parse_qsl, urlsplit

from bs4 import BeautifulSoup, Tag

from .errors import ParseError
from .models import Suchergebnis, Treffer

_DIENST_RE = re.compile(
    r"Notdienst vom (\d{2}\.\d{2}\.\d{4}) um (\d{2}:\d{2}) Uhr"
    r" bis (\d{2}\.\d{2}\.\d{4}) um (\d{2}:\d{2}) Uhr"
)
_KOPF_RE = re.compile(
    r"(\d+)\s+Apotheken?\s+im Umkreis von\s+(\d+)\s+Kilometern"
)
_KM_RE = re.compile(r"([0-9]+(?:[.,][0-9]+)?)\s*km")


@dataclass
class Suchformular:
    path: str
    params: list[tuple[str, str]]
    c_hash: str


def _text(tag: Tag | None) -> str | None:
    if tag is None:
        return None
    value = tag.get_text(" ", strip=True)
    return value or None


def _float(attr: str | None) -> float | None:
    if attr is None:
        return None
    try:
        return float(attr.replace(",", "."))
    except ValueError:
        return None


def _iso_datum(datum: str, zeit: str) -> str:
    tag, monat, jahr = datum.split(".")
    return f"{jahr}-{monat}-{tag}T{zeit}"


def _dienstzeit(card: Tag) -> tuple[str | None, str | None, str | None]:
    match = _DIENST_RE.search(card.get_text(" ", strip=True))
    if not match:
        return None, None, None
    von = _iso_datum(match.group(1), match.group(2))
    bis = _iso_datum(match.group(3), match.group(4))
    anzeige = (
        f"Notdienst {match.group(1)} {match.group(2)}"
        f" bis {match.group(3)} {match.group(4)}"
    )
    return von, bis, anzeige


def _fax(card: Tag) -> str | None:
    for span in card.find_all("span"):
        if not span.get_text(strip=True).startswith("Fax:"):
            continue
        sibling = span.next_sibling
        if sibling is not None:
            value = str(sibling).strip()
            if value:
                return value
    match = re.search(
        r"Fax:\s*(\+?[0-9][0-9 ()/-]*)", card.get_text(" ", strip=True)
    )
    if match:
        return match.group(1).strip() or None
    return None


def _telefon(card: Tag) -> str | None:
    link = card.select_one("a[href^='tel:']")
    if link is not None:
        value = link.get_text(strip=True)
        if value:
            return value
        href = link.get("href") or ""
        value = href[4:].strip()
        if value:
            return value
    match = re.search(
        r"Tel:\s*(\+?[0-9][0-9 ()/-]*)", card.get_text(" ", strip=True)
    )
    if match:
        return match.group(1).strip() or None
    return None


def parse_formular(html: str) -> Suchformular:
    soup = BeautifulSoup(html, "html.parser")
    form = soup.find("form", id="pharmacy-searchform")
    if form is None:
        form = soup.find("form", attrs={"name": "search"})
    if form is None:
        raise ParseError(
            "Die Notdienstsuche hat kein erkennbares Suchformular geliefert.",
            "Später erneut versuchen; hilft das nicht, notdienst --version prüfen.",
        )

    action = form.get("action") or ""
    parts = urlsplit(action)
    params = [
        (str(key), str(value))
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
    ]
    for feld in form.find_all("input"):
        name = feld.get("name")
        if not name or feld.get("type") != "hidden":
            continue
        params.append((str(name), str(feld.get("value") or "")))

    c_hash = next((value for key, value in params if key == "cHash"), "")
    if not c_hash:
        raise ParseError(
            "Der Suchseite fehlt die aktuelle cHash.",
            "Später erneut versuchen; die Quelle hat sich möglicherweise geändert.",
        )

    return Suchformular(
        path=parts.path or "/notdienstsuche",
        params=params,
        c_hash=c_hash,
    )


def parse_ergebnis(html: str, angefragter_radius: int | None = None) -> Suchergebnis:
    soup = BeautifulSoup(html, "html.parser")
    container = soup.find(id="pharmacy-search-result")
    vorschlaege = _vorschlaege(soup)

    if container is None:
        if vorschlaege:
            return Suchergebnis(vorschlaege=vorschlaege)
        if soup.find("form", id="pharmacy-searchform") is not None:
            return Suchergebnis()
        raise ParseError(
            "Die Antwort der Notdienstsuche ist nicht lesbar.",
            "Später erneut versuchen; die Quelle hat sich möglicherweise geändert.",
        )

    radius = angefragter_radius
    kopf = _KOPF_RE.search(container.get_text(" ", strip=True))
    if kopf:
        radius = int(kopf.group(2))

    cards = container.select("li.list-group-item")
    treffer = [_karte(card) for card in cards]
    return Suchergebnis(treffer=treffer, radius_km=radius, trefferblock=True)


def _vorschlaege(soup: BeautifulSoup) -> list[str]:
    bereich = soup.find(id="alternatives")
    if bereich is None:
        return []
    werte: list[str] = []
    for option in bereich.find_all("option"):
        value = str(option.get("value") or "").strip()
        if value and not option.has_attr("disabled"):
            werte.append(value)
    return werte


def _karte(card: Tag) -> Treffer:
    name = _text(card.select_one("h2.name"))
    if not name:
        raise ParseError(
            "Eine Trefferkarte enthält keinen Apothekennamen.",
            "Später erneut versuchen; die Quelle hat sich möglicherweise geändert.",
        )

    distanz = _text(card.select_one(".distanz"))
    entfernung = None
    if distanz:
        match = _KM_RE.search(distanz)
        if match:
            entfernung = _float(match.group(1))

    von, bis, dienstzeit = _dienstzeit(card)
    return Treffer(
        id=(card.get("data-id") or None),
        name=name,
        entfernung_km=entfernung,
        notdienst_von=von,
        notdienst_bis=bis,
        dienstzeit=dienstzeit,
        strasse=_text(card.select_one("span.strasse")),
        plz=_text(card.select_one("span.plz")),
        ort=_text(card.select_one("span.ort")),
        telefon=_telefon(card),
        fax=_fax(card),
        breite=_float(card.get("data-latitude")),
        laenge=_float(card.get("data-longitude")),
    )
