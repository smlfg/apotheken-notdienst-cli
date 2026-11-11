# apotheken-notdienst-cli

Notdienst-Apotheken in Deutschland live über die
[aponet.de-Notdienstsuche](https://www.aponet.de/notdienstsuche) der
ABDA/Landesapothekerkammern finden: Welche Apotheke hat jetzt oder an einem
Datum Notdienst in meiner Nähe, mit Entfernung, Dienstzeit, Adresse und
Telefon? Rein lesend, ohne Login.

## Schnellstart

```bash
pipx install git+https://github.com/smlfg/apotheken-notdienst-cli
notdienst jetzt heilbronn
notdienst datum samstag 74072
notdienst standard heilbronn
notdienst details Greif
```

`notdienst` landet durch `pipx` im PATH. Ohne Ortsargument nutzen `jetzt` und
`datum` den gespeicherten Standard-Ort; `notdienst standard ORT` merkt ihn sich
in `~/.config/apotheken-notdienst-cli/config.json` mit Rechten 0600.

## Befehle

| Befehl | Zweck |
|---|---|
| `notdienst jetzt [ORT\|PLZ]` | Notdienst heute; ohne Ort gilt der Standard-Ort |
| `notdienst datum DATUM [ORT]` | Notdienst an einem Tag (`heute`, `morgen`, `samstag`, `sonntag`, `JJJJ-MM-TT`) |
| `notdienst suche ORT [--radius KM] [--strasse STR]` | Suche mit Umkreis und optionaler Straße |
| `notdienst details NAME [--ort ORT]` | Treffer per Namens-Teilstring im Standard-Ort |
| `notdienst standard ORT` | Standard-Ort speichern |
| `notdienst standard` | Gespeicherten Standard-Ort anzeigen |

Gemeinsame Filter: `--max-km KM`, `--offen-um HH:MM`, `--limit N`.
`--json` liefert maschinenlesbares JSON; ohne TTY ist JSON der Standard.
Mehrdeutige Orte werden im Terminal nummeriert zur Auswahl gestellt; ohne TTY
nennt das Werkzeug die Vorschläge und endet mit Exit 2. `--erster` nimmt den
ersten Vorschlag. `notdienst --help` zeigt alle Optionen, `notdienst --version`
die Version.

### Beispiele

```bash
notdienst jetzt 74072 --limit 3
notdienst jetzt heilbronn --radius 10 --max-km 5
notdienst datum 2026-11-14 74072 --json
notdienst suche "74072 Heilbronn" --strasse Wollhaus
notdienst details Greif --json
```

## Umgebung

| Variable | Wirkung |
|---|---|
| `NOTDIENST_BASE_URL` | Basis-URL überschreiben (z. B. für einen Fake-Server) |
| `NOTDIENST_HEUTE` | Nur für Tests: heutiges Datum `JJJJ-MM-TT` für `heute`/`morgen`/Wochentage |

## Exit-Codes

| Code | Bedeutung |
|---|---|
| 0 | Treffer gefunden bzw. Befehl erfolgreich |
| 1 | Keine Treffer, unbekannter Ort oder lokaler Fehler (z. B. kein Standard-Ort gespeichert) |
| 2 | Aufruf-/Eingabefehler, z. B. ungültiges Datum oder mehrdeutiger Ort ohne `--erster` |
| 3 | Netz-/Quellfehler: nicht erreichbar oder Antwort nicht lesbar |
| 4 | Login nötig (reserviert; dieses Werkzeug braucht keinen Login) |

Jede Fehlermeldung nennt den nächsten Schritt. Es gibt keine Tracebacks, auch
nicht bei Strg+C oder EOF.

## Datenquelle und Verhalten

Die Suche nutzt die Formularseite für die aktuelle `cHash` und fragt danach die
Extbase-Suche per GET ab; beides wird nie hart codiert. Ein normaler Suchlauf
kostet zwei lesende GETs (Formular und Suche); bei einem mehrdeutigen Ort kommt
für den gewählten Vorschlag ein weiterer Such-GET hinzu, die Formularseite wird
wiederverwendet – höchstens drei GETs pro Aufruf. Ergebnisse werden 10 Minuten unter
`~/.cache/apotheken-notdienst-cli` zwischengespeichert. Der User-Agent nennt
die Repo-URL. Es gibt keine schreibenden Web-Aktionen und keinen Login.

**Inoffiziell:** aponet.de ist keine dokumentierte API. Ändert sich die Seite,
meldet das Werkzeug einen Quellfehler (Exit 3), statt mit einem Traceback
abzubrechen. Maßgeblich sind [`ANFORDERUNGEN.md`](ANFORDERUNGEN.md) und
[`INTERFACE.md`](INTERFACE.md); die Nutzer-Sitzungen stehen in
[`docs/UX.md`](docs/UX.md).

## Lizenz

MIT, Copyright smlfg. Siehe [`LICENSE`](LICENSE).
