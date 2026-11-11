# Interface: notdienst

Vertrag für das CLI `notdienst`. Die Umsetzung muss dieses Dokument wörtlich
einhalten; Erweiterungen sind nur abwärtskompatibel erlaubt.

## Aufruf

```text
notdienst [GLOBALE FLAGS] UNTERKOMMANDO [ARGUMENTE] [FLAGS]
```

Der Befehl heißt im PATH `notdienst`. Paketname ist `notdienst`; die Tests
starten das Werkzeug als `python -m notdienst`. Das Console-Script ist
`notdienst = "notdienst.cli:main"`.

### Globale Flags

| Flag | Wirkung |
|---|---|
| `--json` | Ausgabe als genau ein JSON-Objekt auf stdout |
| `--limit N` | Höchstens N Treffer nach allen Filtern (Standard 10, N ≥ 1) |
| `--max-km KM` | Nur Treffer mit Entfernung ≤ KM (lokaler Filter, KM ≥ 0) |
| `--offen-um HH:MM` | Nur Treffer, deren Dienstzeit den Zeitpunkt am Zieldatum abdeckt |
| `--erster` | Bei mehrdeutigem Ort oder mehreren Details-Treffern den ersten nehmen |
| `--version` | Version ausgeben, Exit 0 |
| `--help` | Hilfe ausgeben, Exit 0 |

Globale Flags dürfen vor oder nach dem Unterkommando stehen. Ohne TTY und ohne
`--json` wird JSON ausgegeben; im Terminal (TTY) ist die lesbare Textform
Standard. `--json` hat immer Vorrang.

## Unterkommandos

| Befehl | Argumente | Flags | Zweck |
|---|---|---|---|
| `notdienst jetzt [ORT\|PLZ]` | optionaler Ort; ohne Argument gilt der Standard-Ort | `--radius KM`, `--strasse STR` | Notdienst heute |
| `notdienst datum DATUM [ORT\|PLZ]` | `DATUM` pflicht, Ort optional (sonst Standard-Ort) | `--radius KM`, `--strasse STR` | Notdienst an einem Tag |
| `notdienst suche ORT\|PLZ` | Ort pflicht | `--radius KM`, `--strasse STR` | Suche ohne Datumsbezug (heute) |
| `notdienst details NAME` | Namens-Teilstring pflicht | `--ort ORT\|PLZ` | Vollständigen Eintrag im Standard-Ort (oder `--ort`) zeigen |
| `notdienst standard [ORT\|PLZ]` | Ort optional | – | Ort speichern; ohne Argument den gespeicherten Ort anzeigen |

`ORT` ist ein Ortsname, eine PLZ oder `"PLZ Ort"`, z. B. `heilbronn`,
`74072` oder `"74072 Heilbronn"`. Groß-/Kleinschreibung ist egal.

`DATUM` ist `heute`, `morgen`, ein Wochentag (`montag`, `dienstag`, …,
`sonntag`) oder ein ISO-Datum `JJJJ-MM-TT`. Ein Wochentag meint das nächste
Vorkommen ab heute (heute zählt mit). Erlaubt ist heute bis heute + 14 Tage;
das entspricht dem Fenster des aponet-Formulars.

`--radius KM` wird an den Server übergeben (1–50, Standard 5). Der Server darf
den Radius selbst erweitern; angezeigt wird der gelieferte Radius.
`--strasse STR` wird als Straßenfilter an den Server übergeben.
`--max-km`, `--offen-um` und `--limit` filtern immer lokal nach dem Parsen –
auch dann, wenn der Server mehr Treffer liefert als angefragt.

## Ausgabe: Text (TTY)

Kopfzeile, Anzahl und je Treffer vier Zeilen:

```text
Notdienst-Apotheken für heute (11.11.2026) in Heilbronn
3 Treffer
1) Apotheke im Staufenberg-Zentrum (3.22 km)
   Notdienst 11.11.2026 08:30 bis 12.11.2026 08:30
   Staufenbergstr. 31, 74081 Heilbronn
   Tel: +49 7131 899055
```

- Bei einem Datum außer heute: `Notdienst-Apotheken für Samstag, 14.11.2026 in 74072`.
- Singular: `1 Treffer`.
- Entfernung immer mit zwei Nachkommastellen und Punkt.
- Fehlt das Telefon, steht `Tel: -`; fehlt die Straße, wird die Adresszeile
  aus den vorhandenen Teilen gebildet.
- `details` gibt keinen Kopf und keine Nummer aus, sondern nur den Eintrag
  (Name mit Entfernung, Dienstzeit, Adresse, Telefon).
- `standard ORT` gibt `Standard-Ort gespeichert: Heilbronn` aus.
- `standard` ohne Argument gibt `Standard-Ort: Heilbronn` aus.

Fehler gehen im Textmodus nach stderr und nennen den nächsten Schritt:

```text
Keine Notdienst-Apotheke gefunden – anderen Ort mit notdienst jetzt ORT versuchen.
```

## Ausgabe: JSON

Mit `--json` (oder wenn stdout kein TTY ist) steht auf stdout genau ein
JSON-Objekt, ohne weitere Ausgaben. Bei Erfolg:

```json
{
  "abfrage": {
    "befehl": "jetzt",
    "ort": "Heilbronn",
    "datum": "2026-11-11",
    "datum_anzeige": "heute (11.11.2026)",
    "radius_km": 25,
    "strasse": null,
    "anzahl": 3
  },
  "treffer": [
    {
      "id": "1273042",
      "name": "Apotheke im Staufenberg-Zentrum",
      "entfernung_km": 3.22,
      "notdienst_von": "2026-11-11T08:30",
      "notdienst_bis": "2026-11-12T08:30",
      "dienstzeit": "Notdienst 11.11.2026 08:30 bis 12.11.2026 08:30",
      "strasse": "Staufenbergstr. 31",
      "plz": "74081",
      "ort": "Heilbronn",
      "telefon": "+49 7131 899055",
      "fax": "+49 7131 899056",
      "breite": 49.1186511,
      "laenge": 9.1932944
    }
  ]
}
```

- `treffer` ist immer eine Liste, auch bei `details` und bei einem Treffer.
- Unbekannte Felder dürfen `null` sein; die Schlüssel bleiben vorhanden.
- `standard ORT` liefert `{"standard_ort": "Heilbronn", "config": "/…/config.json"}`,
  `standard` ohne Argument dasselbe ohne Schreibvorgang.
- Fehler liefern genau ein Objekt:
  `{"fehler": {"exit_code": 2, "meldung": "…", "naechster_schritt": "…"}}`.
- Usage-Fehler des Parsers werden zentral abgefangen und liefern ebenfalls
  dieses Fehlerobjekt, wenn `--json` gesetzt ist oder stdout kein TTY ist.

## Exit-Codes

| Code | Bedeutung |
|---|---|
| 0 | Erfolg: Treffer gefunden, Standard-Ort gespeichert/angezeigt, Details gefunden |
| 1 | Keine Treffer, unbekannter Ort oder lokaler Fehler (z. B. kein Standard-Ort gespeichert, Config unlesbar) |
| 2 | Aufruf-/Eingabefehler: unbekanntes Unterkommando, ungültiges Datum/Radius/Limit, mehrdeutiger Ort ohne `--erster` |
| 3 | Netz-/Quellfehler: DNS, Timeout, HTTP ≠ 200, fehlende `cHash`, unerwartetes HTML |
| 4 | Login nötig (reserviert; dieses Werkzeug braucht nie einen Login) |
| 130 | Abbruch durch Strg+C/EOF, ohne Traceback |

Ein leerer Trefferfall ist kein Usage-Fehler. Meldet der Server keine Treffer
oder kennt er den Ort nicht, endet der Befehl mit Exit 1 und nennt den nächsten
Schritt; die Quelle unterscheidet beides nicht. Liefert der Server eine
Vorschlagsliste für einen mehrdeutigen Ort, ist das Exit 2.

## Umgebungsvariablen

| Variable | Wirkung |
|---|---|
| `NOTDIENST_BASE_URL` | Basis-URL überschreiben, Standard `https://www.aponet.de` (für Fake-Server und Tests) |
| `NOTDIENST_HEUTE` | Nur für Tests: heutiges Datum als `JJJJ-MM-TT`, damit `heute`, `morgen` und Wochentage reproduzierbar sind |
| `XDG_CONFIG_HOME` | Basis für die Config, Standard `~/.config` |
| `XDG_CACHE_HOME` | Basis für den Cache, Standard `~/.cache` |
| `HOME` | Fallback für Config und Cache |

Ungültige Werte (kein Datum, keine URL, kein positiver Radius) führen zu einer
klaren Meldung mit nächstem Schritt und Exit 2, nie zu einem Traceback.

## Config und Cache

- Config: `~/.config/apotheken-notdienst-cli/config.json`, Verzeichnis `0700`,
  Datei `0600`. Inhalt: `{"standard_ort": "Heilbronn"}`.
- Cache: `~/.cache/apotheken-notdienst-cli/`, ein JSON-Eintrag je Suchanfrage
  (Schlüssel: Basis-URL, Ort, Datum, Straße, Radius), TTL 600 Sekunden.
  Abgelaufene oder unlesbare Einträge werden verworfen und neu geholt.
- `notdienst standard` schreibt nur lokal und sendet keinen Request.

## Netzverhalten

- Pro Suchlauf höchstens zwei lesende GETs: zuerst die Formularseite für die
  aktuelle `cHash` und `__trustedProperties`, danach die Extbase-Suche mit den
  Suchfeldern als Query-Parameter.
- Nur bei einem mehrdeutigen Ort kommt ein weiterer Such-GET für den gewählten
  Vorschlag hinzu; die Formularseite wird dabei wiederverwendet. Pro Aufruf
  sind es damit höchstens drei GETs (ein Formular-GET, zwei Such-GETs).
- `cHash` und versteckte Felder werden nie hart codiert.
- User-Agent:
  `apotheken-notdienst-cli (+https://github.com/smlfg/apotheken-notdienst-cli)`.
- Keine POST-, PUT-, PATCH- oder DELETE-Requests an die echte Quelle. Keine
  Cookies, keine Zugangsdaten, keine schreibenden Aktionen.
