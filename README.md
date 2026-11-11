# apotheken-notdienst-cli

Notdienst-Apotheken in Deutschland live über die
[aponet.de-Notdienstsuche](https://www.aponet.de/notdienstsuche) der
ABDA/Landesapothekerkammern finden: Welche Apotheke hat jetzt oder an einem
Datum Notdienst in meiner Nähe, mit Entfernung, Dienstzeit, Adresse und
Telefon.

## Schnellstart

```bash
pipx install git+https://github.com/smlfg/apotheken-notdienst-cli
notdienst jetzt heilbronn
notdienst datum samstag 74072
notdienst standard heilbronn
notdienst details Greif
```

`notdienst` landet durch `pipx` im PATH. Ohne Argument nutzt `jetzt` und
`datum` den gespeicherten Standard-Ort; `notdienst standard ORT` merkt ihn sich
in `~/.config/apotheken-notdienst-cli/config.json` mit Rechten 0600.

## Befehle

| Befehl | Zweck |
|---|---|
| `notdienst jetzt [ORT\|PLZ]` | Notdienst heute; ohne Ort gilt der Standard-Ort |
| `notdienst datum DATUM [ORT]` | Notdienst an einem Tag (`heute`, `morgen`, `samstag`, `sonntag`, `JJJJ-MM-TT`) |
| `notdienst suche ORT [--radius KM] [--strasse STR]` | Suche mit Umkreis und optionaler Straße |
| `notdienst details NAME` | Treffer per Namens-Teilstring im Standard-Ort |
| `notdienst standard ORT` | Standard-Ort speichern |
| `notdienst standard` | Gespeicherten Standard-Ort anzeigen |

Gemeinsame Filter: `--max-km KM`, `--offen-um HH:MM`, `--limit N`.
`--json` liefert maschinenlesbares JSON; ohne TTY ist JSON der Standard.
Mehrdeutige Orte werden im Terminal nummeriert zur Auswahl gestellt; ohne TTY
nennt das Werkzeug die Vorschläge und endet mit Exit 2. `--erster` nimmt den
ersten Vorschlag.

## Umgebung

| Variable | Wirkung |
|---|---|
| `NOTDIENST_BASE_URL` | Basis-URL überschreiben (z. B. für einen Fake-Server) |
| `NOTDIENST_HEUTE` | Testdatum `JJJJ-MM-TT` für `heute`/`morgen`/Wochentage |

## Exit-Codes

| Code | Bedeutung |
|---|---|
| 0 | Treffer gefunden bzw. Befehl erfolgreich |
| 1 | Keine Treffer oder Netz-/Serverfehler (Meldung nennt den nächsten Schritt) |
| 2 | Aufruf- oder Eingabefehler, z. B. mehrdeutiger oder unbekannter Ort |

Höflich gegenüber dem Dienst: ein Suchlauf mit kurzem Cache (10 Minuten) unter
`~/.cache/apotheken-notdienst-cli`, ein User-Agent mit Repo-URL. Es gibt keine
schreibenden Web-Aktionen und keinen Login.

## Lizenz

MIT, Copyright smlfg.
