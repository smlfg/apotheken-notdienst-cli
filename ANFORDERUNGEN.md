# Anforderungen: apotheken-notdienst-cli

## Zweck

`notdienst` beantwortet die Frage „Welche Apotheke hat jetzt oder an einem
bestimmten Tag Notdienst in meiner Nähe?“ live über die
[Notdienstsuche von aponet.de](https://www.aponet.de/notdienstsuche), dem
Angebot der ABDA und der Landesapothekerkammern. Zu jedem Treffer zeigt das
Werkzeug Name, Entfernung, Dienstzeit, Adresse und Telefon.

Das Werkzeug ist rein lesend. Es gibt keinen Login, keine Buchung und keine
schreibende Web-Aktion.

## Nutzer-Aufgaben

1. **Aktueller Notdienst.** `notdienst jetzt heilbronn` oder
   `notdienst jetzt 74072` zeigt die Apotheken, die heute Notdienst haben –
   auch ohne Argument, wenn ein Standard-Ort gespeichert ist.
2. **Notdienst an einem Tag.** `notdienst datum samstag 74072` oder
   `notdienst datum 2026-11-14 heilbronn` zeigt die Dienstapotheken für einen
   Wochentag oder ein konkretes Datum.
3. **Standard-Ort und Details.** `notdienst standard heilbronn` merkt sich den
   Ort lokal; `notdienst details Greif` zeigt danach den vollständigen Eintrag
   der Apotheke mit diesem Namens-Teilstring.
4. **Eingrenzen.** Suchbefehle akzeptieren `--radius KM`, `--strasse STR`,
   `--max-km KM`, `--offen-um HH:MM` und `--limit N`. `--json` liefert
   maschinenlesbare Ausgabe.

Die genauen Befehle, Flags, Exit-Codes und Ausgabeformate stehen in
[`INTERFACE.md`](INTERFACE.md). Die drei wichtigsten Sitzungen mit erwarteter
Terminal-Ausgabe stehen in [`docs/UX.md`](docs/UX.md).

## Nachfrage

- **Quelle und Datum:** `NEXT20.md` der täglichen CLI-Routine, Platz 10
  (`apotheken-notdienst-cli (aponet)`), Stand 30.10.2026.
- **Bedingung:** „Suche-Endpunkt noch nicht verifiziert“. Die Bedingung ist am
  11.11.2026 erfüllt: Der Orchestrator hat den Suche-Endpunkt live getestet
  (HTTP 200, Treffer-Karten mit Entfernung, Dienstzeit, Adresse und Telefon).
- **Wettbewerb:** nur ein MagicMirror-Modul (★6); kein CLI und kein MCP-Server
  mit vergleichbarer Abdeckung gefunden.
- **Ergebnis:** GO für ein CLI, Typ `cli`, kein Login.

## Datenquelle

- Formularseite: `GET https://www.aponet.de/notdienstsuche` (TYPO3/Extbase,
  `id="pharmacy-searchform"`). Die Seite liefert die aktuelle `cHash` und die
  versteckten Felder; beides wird bei jedem Lauf frisch gelesen und nie hart
  codiert.
- Suche: `GET /notdienstsuche` mit den Query-Parametern
  `tx_aponetpharmacy_search[search][plzort]`,
  `tx_aponetpharmacy_search[search][date]` (leer = jetzt),
  `tx_aponetpharmacy_search[search][street]` und
  `tx_aponetpharmacy_search[search][radius]`.
- Trefferliste: Karten mit `h2.name`, Entfernung, „Notdienst vom … bis …“,
  `span.strasse`, `span.plz`, `span.ort`, Telefonnummmer sowie
  `data-latitude`/`data-longitude`. Kopfzeile:
  „N Apotheken im Umkreis von R Kilometern gefunden.“
- Der Server kann den angefragten Radius selbst erweitern. Angezeigt wird der
  tatsächlich gelieferte Radius; `--max-km` filtert lokal nach der Entfernung.
- Live wurde ausschließlich lesend gearbeitet. Die im Tool-Brief ursprünglich
  vermutete POST-Suche erwies sich als nicht nötig: Dieselbe Extbase-Action
  antwortet auch auf GET, mit und ohne `cHash`.

## Grenzen

- **Inoffiziell.** aponet.de ist keine dokumentierte API. Ändert sich das
  HTML, bricht das Parsen; das Werkzeug meldet dann einen Quell-/Netzfehler
  (Exit 3) statt eines Tracebacks.
- **Nur Deutschland.** Die Suche erwartet PLZ, Ort oder „PLZ Ort“; eine
  Adress-Geocodierung über die Straße hinaus gibt es nicht.
- **Datumsfenster.** Das Formular erlaubt heute bis heute + 14 Tage. Ältere oder
  weiter entfernte Daten werden mit einem Hinweis auf den gültigen Bereich
  abgelehnt.
- **Nur öffentlich veröffentlichte Notdienste.** Keine Buchung, keine
  Reservierung, kein Login. `notdienst standard` schreibt ausschließlich lokal.
- **Keine Personendaten.** Apothekennamen, Adressen und Telefonnummern sind
  öffentliche Geschäftsdaten. Das Repo enthält keine echten Personendaten,
  keine Secrets und keine Zugangsdaten.
- **Höflichkeit.** Pro normalem Suchlauf höchstens zwei lesende GETs (Formular
  und Suche); nur bei einem mehrdeutigen Ort kommt ein weiterer Such-GET hinzu
  (höchstens drei pro Aufruf). Dazu ein Such-Cache von 10 Minuten und ein
  User-Agent mit Repo-URL.
