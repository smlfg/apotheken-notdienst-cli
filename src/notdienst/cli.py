"""Kommandozeile für notdienst."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, time

from . import __version__, config, dates
from .client import Client
from .errors import (
    AmbiguousError,
    InputError,
    LocalError,
    NotdienstError,
)
from .models import Suchergebnis, Treffer

class RaisingArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:  # noqa: D401 - argparse-Vertrag
        raise InputError(
            f"Ungültiger Aufruf: {message}.",
            "notdienst --help zeigt alle Befehle und Optionen.",
        )


def _limit(wert: str) -> int:
    try:
        zahl = int(wert)
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"--limit erwartet eine ganze Zahl, erhalten: {wert!r}"
        ) from None
    if zahl < 1:
        raise argparse.ArgumentTypeError("--limit muss mindestens 1 sein")
    return zahl


def _max_km(wert: str) -> float:
    try:
        zahl = float(wert.replace(",", "."))
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"--max-km erwartet eine Zahl, erhalten: {wert!r}"
        ) from None
    if zahl < 0 or zahl != zahl or zahl in (float("inf"), float("-inf")):
        raise argparse.ArgumentTypeError("--max-km muss eine Zahl ab 0 sein")
    return zahl


def _radius(wert: str) -> int:
    try:
        zahl = int(wert)
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"--radius erwartet eine ganze Zahl, erhalten: {wert!r}"
        ) from None
    if not 1 <= zahl <= 50:
        raise argparse.ArgumentTypeError("--radius muss zwischen 1 und 50 liegen")
    return zahl


def _uhrzeit(wert: str) -> time:
    if not re.fullmatch(r"\d{1,2}:\d{2}", wert):
        raise argparse.ArgumentTypeError(
            f"--offen-um erwartet HH:MM, erhalten: {wert!r}"
        )
    try:
        return time.fromisoformat(wert)
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"--offen-um erwartet HH:MM, erhalten: {wert!r}"
        ) from None


def _globale_flags(parser: argparse.ArgumentParser, *, suppress: bool) -> None:
    def basis(wert):
        return argparse.SUPPRESS if suppress else wert

    parser.add_argument(
        "--json",
        action="store_true",
        default=basis(False),
        help="Ausgabe als genau ein JSON-Objekt",
    )
    parser.add_argument(
        "--limit",
        type=_limit,
        default=basis(10),
        metavar="N",
        help="höchstens N Treffer (Standard 10)",
    )
    parser.add_argument(
        "--max-km",
        type=_max_km,
        default=basis(None),
        metavar="KM",
        help="nur Treffer bis KM Entfernung",
    )
    parser.add_argument(
        "--offen-um",
        type=_uhrzeit,
        default=basis(None),
        metavar="HH:MM",
        help="nur Treffer, deren Dienstzeit den Zeitpunkt abdeckt",
    )
    parser.add_argument(
        "--erster",
        action="store_true",
        default=basis(False),
        help="bei Mehrdeutigkeit den ersten Treffer nehmen",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"notdienst {__version__}",
        help="Version ausgeben",
    )


def _such_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--radius",
        type=_radius,
        default=5,
        metavar="KM",
        help="Umkreis in Kilometern (1-50, Standard 5)",
    )
    parser.add_argument(
        "--strasse",
        default=None,
        metavar="STR",
        help="Straße und Hausnummer als Suchfilter",
    )


def baue_parser() -> argparse.ArgumentParser:
    global_parser = argparse.ArgumentParser(add_help=False)
    _globale_flags(global_parser, suppress=False)
    sub_global = argparse.ArgumentParser(add_help=False)
    _globale_flags(sub_global, suppress=True)

    parser = RaisingArgumentParser(
        prog="notdienst",
        description=(
            "Notdienst-Apotheken in Deutschland über die aponet.de-Suche finden."
        ),
        parents=[global_parser],
    )
    unter = parser.add_subparsers(dest="befehl", metavar="UNTERKOMMANDO")

    jetzt = unter.add_parser(
        "jetzt",
        parents=[sub_global],
        help="Notdienst heute zeigen",
        description="Notdienst-Apotheken für heute; ohne Ort gilt der Standard-Ort.",
    )
    jetzt.add_argument("ort", nargs="?", help="Ort, PLZ oder \"PLZ Ort\"")
    _such_flags(jetzt)

    datum = unter.add_parser(
        "datum",
        parents=[sub_global],
        help="Notdienst an einem Datum zeigen",
        description="Notdienst an einem Tag; heute bis heute + 14 Tage.",
    )
    datum.add_argument(
        "datum",
        help="heute, morgen, Wochentag oder JJJJ-MM-TT",
    )
    datum.add_argument("ort", nargs="?", help="Ort, PLZ oder \"PLZ Ort\"")
    _such_flags(datum)

    suche = unter.add_parser(
        "suche",
        parents=[sub_global],
        help="Notdienstsuche mit Umkreis und Straße",
        description="Notdienst-Apotheken für heute suchen.",
    )
    suche.add_argument("ort", help="Ort, PLZ oder \"PLZ Ort\"")
    _such_flags(suche)

    details = unter.add_parser(
        "details",
        parents=[sub_global],
        help="Eintrag per Namens-Teilstring zeigen",
        description="Vollständigen Eintrag im Standard-Ort oder mit --ort zeigen.",
    )
    details.add_argument("name", help="Namens-Teilstring der Apotheke")
    details.add_argument(
        "--ort", default=None, metavar="ORT", help="Ort statt Standard-Ort"
    )

    standard = unter.add_parser(
        "standard",
        parents=[sub_global],
        help="Standard-Ort speichern oder anzeigen",
        description="Ohne Argument wird der gespeicherte Standard-Ort angezeigt.",
    )
    standard.add_argument("ort", nargs="?", help="Ort, PLZ oder \"PLZ Ort\"")

    return parser


def _will_json(argv: list[str]) -> bool:
    return "--json" in argv or not sys.stdout.isatty()


def _anzeige_ort(wert: str) -> str:
    text = wert.strip()
    if not text:
        raise InputError(
            "Der Ort darf nicht leer sein.",
            "Ort als Name, PLZ oder \"PLZ Ort\" angeben.",
        )
    if re.fullmatch(r"\d{4,5}", text):
        return text
    teile = []
    for teil in text.split():
        teile.append(teil[:1].upper() + teil[1:] if teil.islower() else teil)
    return " ".join(teile)


def _ort_aufloesen(ort_argument: str | None) -> str:
    if ort_argument is not None:
        return _anzeige_ort(ort_argument)
    gespeichert = config.standard_ort()
    if not gespeichert:
        raise LocalError(
            "Kein Standard-Ort gespeichert",
            "mit notdienst standard ORT einen Ort speichern.",
        )
    return gespeichert


def _interaktiv() -> bool:
    return sys.stdin.isatty() and sys.stdout.isatty()


def _ort_auswaehlen(vorschlaege: list[str]) -> str:
    print("Mehrdeutige Orte:", file=sys.stderr)
    for nummer, vorschlag in enumerate(vorschlaege, start=1):
        print(f"{nummer}) {vorschlag}", file=sys.stderr)
    antwort = input(f"Auswahl [1-{len(vorschlaege)}]: ").strip()
    if not antwort:
        raise InputError(
            "Keine Auswahl getroffen.",
            "Auswahl als Nummer eingeben oder Ort präziser angeben.",
        )
    try:
        nummer = int(antwort)
    except ValueError:
        raise InputError(
            f"Ungültige Auswahl: {antwort!r}.",
            "Auswahl als Nummer eingeben oder Ort präziser angeben.",
        ) from None
    if not 1 <= nummer <= len(vorschlaege):
        raise InputError(
            f"Ungültige Auswahl: {nummer}.",
            f"Eine Zahl zwischen 1 und {len(vorschlaege)} eingeben.",
        )
    return vorschlaege[nummer - 1].strip()


def _suche(
    client: Client,
    ort: str,
    *,
    datum: str | None,
    strasse: str | None,
    radius: int,
    erster: bool,
) -> Suchergebnis:
    ergebnis = client.suche(
        ort, datum=datum, strasse=strasse, radius=radius
    )
    if ergebnis.treffer or not ergebnis.vorschlaege:
        return ergebnis

    if erster:
        return client.suche(
            ergebnis.vorschlaege[0],
            datum=datum,
            strasse=strasse,
            radius=radius,
        )
    if _interaktiv():
        gewaehlt = _ort_auswaehlen(ergebnis.vorschlaege)
        return client.suche(
            gewaehlt, datum=datum, strasse=strasse, radius=radius
        )
    liste = "; ".join(ergebnis.vorschlaege)
    raise AmbiguousError(
        f"Ort ist mehrdeutig: {liste}.",
        "Ort präzisieren (z. B. \"PLZ Ort\") oder --erster verwenden.",
    )


def _offen(treffer: Treffer, zeitpunkt: str) -> bool:
    if not treffer.notdienst_von or not treffer.notdienst_bis:
        return False
    return treffer.notdienst_von <= zeitpunkt <= treffer.notdienst_bis


def _adresse(treffer: Treffer) -> str:
    teile = []
    if treffer.strasse:
        teile.append(treffer.strasse)
    if treffer.plz and treffer.ort:
        teile.append(f"{treffer.plz} {treffer.ort}")
    elif treffer.ort:
        teile.append(treffer.ort)
    elif treffer.plz:
        teile.append(treffer.plz)
    return ", ".join(teile) if teile else "Adresse unbekannt"


def _eintrag(treffer: Treffer, nummer: int | None = None) -> list[str]:
    entfernung = (
        f"{treffer.entfernung_km:.2f}"
        if treffer.entfernung_km is not None
        else "-"
    )
    prefix = f"{nummer}) " if nummer is not None else ""
    einzug = "   " if nummer is not None else ""
    return [
        f"{prefix}{treffer.name} ({entfernung} km)",
        f"{einzug}{treffer.dienstzeit or 'Notdienstzeit unbekannt'}",
        f"{einzug}{_adresse(treffer)}",
        f"{einzug}Tel: {treffer.telefon}" if treffer.telefon else f"{einzug}Tel: -",
    ]


def _fehler_ausgeben(fehler: NotdienstError, json_modus: bool) -> int:
    if json_modus:
        objekt = {
            "fehler": {
                "exit_code": fehler.exit_code,
                "meldung": fehler.meldung,
                "naechster_schritt": fehler.naechster_schritt,
            }
        }
        print(json.dumps(objekt, ensure_ascii=False))
    else:
        print(
            f"{fehler.meldung} – {fehler.naechster_schritt}",
            file=sys.stderr,
        )
    return fehler.exit_code


def _suche_ausfuehren(args: argparse.Namespace, json_modus: bool) -> int:
    heute_datum = dates.heute()
    befehl = args.befehl

    if befehl == "datum":
        ziel = dates.parse_datum(args.datum, heute_datum)
        server_datum = ziel.isoformat()
    else:
        ziel = heute_datum
        server_datum = None

    if befehl == "details":
        ort = _ort_aufloesen(args.ort)
    else:
        ort = _ort_aufloesen(args.ort)

    strasse = getattr(args, "strasse", None)
    radius = getattr(args, "radius", 5)

    with Client() as client:
        ergebnis = _suche(
            client,
            ort,
            datum=server_datum,
            strasse=strasse,
            radius=radius,
            erster=args.erster,
        )

    treffer = list(ergebnis.treffer)
    if args.max_km is not None:
        treffer = [
            eintrag
            for eintrag in treffer
            if eintrag.entfernung_km is not None
            and eintrag.entfernung_km <= args.max_km
        ]
    if args.offen_um is not None:
        zeitpunkt = datetime.combine(ziel, args.offen_um).isoformat(
            timespec="minutes"
        )
        treffer = [
            eintrag for eintrag in treffer if _offen(eintrag, zeitpunkt)
        ]

    if befehl == "details":
        nadel = args.name.strip().lower()
        treffer = [
            eintrag for eintrag in treffer if nadel in eintrag.name.lower()
        ]
        if args.limit is not None:
            treffer = treffer[: args.limit]
        if not treffer:
            raise LocalError(
                f"Keine Notdienst-Apotheke mit Namen {args.name!r} gefunden",
                "anderen Namen mit notdienst details NAME versuchen.",
            )
        if len(treffer) > 1:
            if args.erster:
                treffer = treffer[:1]
            elif _interaktiv():
                print("Mehrere Apotheken passen:", file=sys.stderr)
                for nummer, eintrag in enumerate(treffer, start=1):
                    print(
                        f"{nummer}) {eintrag.name} – {_adresse(eintrag)}",
                        file=sys.stderr,
                    )
                antwort = input(
                    f"Auswahl [1-{len(treffer)}]: "
                ).strip()
                try:
                    nummer = int(antwort)
                except ValueError:
                    nummer = 0
                if not 1 <= nummer <= len(treffer):
                    raise InputError(
                        f"Ungültige Auswahl: {antwort!r}.",
                        "Auswahl als Nummer eingeben oder Namen genauer angeben.",
                    )
                treffer = [treffer[nummer - 1]]
            else:
                namen = "; ".join(eintrag.name for eintrag in treffer)
                raise AmbiguousError(
                    f"Mehrere Apotheken passen zu {args.name!r}: {namen}.",
                    "Namen genauer angeben oder --erster verwenden.",
                )
        ausgewaehlt = treffer[0]
        if json_modus:
            _json_ausgeben(
                befehl,
                ort,
                ziel,
                heute_datum,
                strasse,
                ergebnis.radius_km,
                [ausgewaehlt],
            )
        else:
            for zeile in _eintrag(ausgewaehlt):
                print(zeile)
        return 0

    if args.limit is not None:
        treffer = treffer[: args.limit]
    if not treffer:
        raise LocalError(
            "Keine Notdienst-Apotheke gefunden",
            "anderen Ort mit notdienst jetzt ORT versuchen.",
        )

    if json_modus:
        _json_ausgeben(
            befehl,
            ort,
            ziel,
            heute_datum,
            strasse,
            ergebnis.radius_km,
            treffer,
        )
        return 0

    anzeige = dates.datum_anzeige(ziel, heute_datum)
    print(f"Notdienst-Apotheken für {anzeige} in {ort}")
    print(f"{len(treffer)} Treffer")
    for nummer, eintrag in enumerate(treffer, start=1):
        for zeile in _eintrag(eintrag, nummer):
            print(zeile)
    return 0


def _json_ausgeben(
    befehl: str,
    ort: str,
    ziel,
    heute_datum,
    strasse: str | None,
    radius_km: int | None,
    treffer: list[Treffer],
) -> None:
    objekt = {
        "abfrage": {
            "befehl": befehl,
            "ort": ort,
            "datum": ziel.isoformat(),
            "datum_anzeige": dates.datum_anzeige(ziel, heute_datum),
            "radius_km": radius_km,
            "strasse": strasse,
            "anzahl": len(treffer),
        },
        "treffer": [eintrag.to_dict() for eintrag in treffer],
    }
    print(json.dumps(objekt, ensure_ascii=False))


def _standard_ausfuehren(args: argparse.Namespace, json_modus: bool) -> int:
    if args.ort is not None:
        ort = _anzeige_ort(args.ort)
        pfad = config.speichere_standard_ort(ort)
        if json_modus:
            print(
                json.dumps(
                    {"standard_ort": ort, "config": str(pfad)},
                    ensure_ascii=False,
                )
            )
        else:
            print(f"Standard-Ort gespeichert: {ort}")
        return 0

    gespeichert = config.standard_ort()
    if not gespeichert:
        raise LocalError(
            "Kein Standard-Ort gespeichert",
            "mit notdienst standard ORT einen Ort speichern.",
        )
    if json_modus:
        print(
            json.dumps(
                {
                    "standard_ort": gespeichert,
                    "config": str(config.config_pfad()),
                },
                ensure_ascii=False,
            )
        )
    else:
        print(f"Standard-Ort: {gespeichert}")
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    json_modus = _will_json(argv)
    parser = baue_parser()

    try:
        args = parser.parse_args(argv)
        if not getattr(args, "befehl", None):
            parser.print_help()
            return 0
        if args.befehl == "standard":
            return _standard_ausfuehren(args, json_modus)
        return _suche_ausfuehren(args, json_modus)
    except NotdienstError as fehler:
        return _fehler_ausgeben(fehler, json_modus)
    except KeyboardInterrupt:
        print("\nAbgebrochen.", file=sys.stderr)
        return 130
    except EOFError:
        print("\nEingabe abgebrochen.", file=sys.stderr)
        return 130
    except BrokenPipeError:
        return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
