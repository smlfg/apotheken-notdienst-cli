# Pflicht-QA: notdienst

- **Datum:** 11.11.2026
- **Version/Commit:** `notdienst 0.1.0`, Repo-HEAD `ed7a415` (docs(ux): UX-Gate-Bericht)
- **Installation:** `pipx install git+https://github.com/smlfg/apotheken-notdienst-cli`
  (frisch durch den Orchestrator, Protokoll `scratch/qa/pipx-install.log`;
  installiert mit Python 3.14.7). Die installierte Quelle ist identisch mit dem
  Repo-HEAD (`diff -r` ohne Unterschied).
- **Aufruf:** ausschließlich über `PATH=$PWD/scratch/pipx/bin:$PATH`, nicht aus
  `scratch/venv`.
- **Test-HOME:** alle Config-/Cache-Pfade unter `scratch/qa/…`; Live-Sitzungen
  mit `NOTDIENST_HEUTE=2026-11-11` für reproduzierbare Datumsbezüge.
- **Live:** nur lesende GETs gegen `https://www.aponet.de`; keine Logins, keine
  schreibenden Web-Aktionen. Fake-Läufe nutzen `tests/harness/fake_server.py`
  unverändert.
- **Auftrag:** reine Prüfung (find → file), keine Codeänderungen.
- **Nachprüfung S6:** Fixes `3b5301a`, `49e4a8b`, `fda0250`, `ca0f32d`;
  betroffene Zeilen erneut ausgeführt, pytest 73 passed, UX-Gate und
  UX-Session je Exit 0.

Hinweis: Die Live-Quelle lieferte am Prüftag 7 Treffer für `jetzt heilbronn`
und 5 für `datum samstag 74072`; die UX-Fixtures kürzen bewusst auf 3. Das ist
kein Fehler. Der Server meldet im Kopf „25 km“ und liefert teils Treffer über
25 km; das Werkzeug gibt die gelieferten Werte weiter, `--max-km` filtert lokal.

## Prüfungen

| # | Prüfung | Befehl (gekürzt) | Erwartet | Ergebnis | Beleg (gekürzt) |
|---|---|---|---|---|---|
| 1 | Frische pipx-Installation | `pipx install git+https://github.com/smlfg/apotheken-notdienst-cli` | installiert, Exit 0 | OK | `installed package notdienst 0.1.0, installed using Python 3.14.7` |
| 2 | Befehl über pipx-PATH | `command -v notdienst`, `notdienst --version` | Pfad aus `scratch/pipx/bin`, Exit 0 | OK | `…/scratch/pipx/bin/notdienst`; `notdienst 0.1.0` |
| 3 | Installierte Quelle == Repo | `diff -r src/notdienst scratch/pipx/venvs/notdienst/lib/python3.14/site-packages/notdienst` | keine Unterschiede | OK | leerer diff |
| 4 | Hilfe | `notdienst --help` | Exit 0, verständliche Befehle/Flags | OK | Befehle `jetzt datum suche details standard`, deutsche Hilfetexte |
| 5 | Unterkommando-Hilfen | `notdienst <sub> --help` für alle 5 | je Exit 0 | OK | 5× Exit 0 |
| 6 | README Zeile 1 (PTY) | `script -qec "pipx install …" …` | Exit 0 | OK | `'notdienst' (0.1.0) is already installed` |
| 7 | README `jetzt` (PTY, live) | `script -qec "notdienst jetzt heilbronn" …` | lesbare Treffer, Exit 0 | OK | „Notdienst-Apotheken für heute (11.11.2026) in Heilbronn“, 7 Treffer |
| 8 | README `datum` (PTY, live) | `script -qec "notdienst datum samstag 74072" …` | Samstag, 14.11.2026, Exit 0 | OK | „Samstag, 14.11.2026 … 5 Treffer“, erster Treffer 0.28 km |
| 9 | README `standard` (PTY, live) | `script -qec "notdienst standard heilbronn" …` | speichert 0600 | OK | `Standard-Ort gespeichert: Heilbronn`; Config `600`, Verzeichnis `700` |
| 10 | README `details` (PTY, live) | `script -qec "notdienst details Greif" …` | vollständiger Eintrag, Exit 0 | OK | `Greif-Apotheke (8.01 km)`, Adresse, `Tel: +49 7132 83811` |
| 11 | Schnellstart komplett gegen Fake | alle 5 README-Zeilen, `NOTDIENST_BASE_URL=<fake>/docs/UX.md` | Ausgaben wie UX-Spec | OK | `3 Treffer`, `14.11.2026`, Details Greif; alle Exit 0 |
| 12 | Live `suche` Radius/Straße | `notdienst suche "74072 Heilbronn" --radius 10 --strasse Wollhaus --json` | valide Treffer, Straße übergeben | OK | `"strasse": "Wollhaus"`, `"radius_km": 30` (Server erweitert) |
| 13 | Namens-Tippvariante | `notdienst details greif --json` | genau 1 Treffer | OK | `Greif-Apotheke` |
| 14 | Umlaute im Namen | Fake: `details Müller`, `details MÜLLER`, `details Schloß` | gefunden | OK | je genau 1 Treffer. `Muller`/`schloss` ohne Umlaut finden nicht (Spec verlangt keine Transliteration) |
| 15 | `--limit` | `notdienst jetzt heilbronn --limit 3 --json` | genau 3 Treffer | OK | `anzahl: 3`, 3 Einträge |
| 16 | `--max-km` | `notdienst jetzt heilbronn --max-km 10 --json` | jeder Treffer ≤ 10 km | OK | max. `7.50`; Skript prüft alle Treffer |
| 17 | `--offen-um` mit Treffern | `notdienst jetzt heilbronn --offen-um 09:00 --json` | jeder Dienst deckt 09:00 ab | OK | alle `08:30`–`08:30` Folgetag |
| 18 | `--offen-um` ohne Treffer | `notdienst jetzt heilbronn --offen-um 07:00 --json` | Exit 1, nächster Schritt | OK | `Keine Notdienst-Apotheke gefunden – anderen Ort … versuchen.` |
| 19 | Datum über alle Treffer | `notdienst datum samstag 74072 --json` | jeder Eintrag am 14.11.2026 | OK | alle `notdienst_von <= 14.11. 23:59` und `bis >= 14.11. 00:00` |
| 20 | Datum + `--max-km` | `notdienst datum samstag 74072 --max-km 6 --json` | jeder Treffer ≤ 6 km | OK | max. `5.97` |
| 21 | Datum + `--limit` | `notdienst datum samstag 74072 --limit 2 --json` | genau 2 Treffer | OK | `anzahl: 2`, 2 Einträge |
| 22 | Datum + `--offen-um` leer | `notdienst datum samstag 74072 --offen-um 07:00 --json` | Exit 1 | OK | Fehlerobjekt mit `exit_code: 1` |
| 23 | Mehrdeutiger Ort ohne TTY | Fake: `notdienst jetzt vorschlag --json` | Exit 2 mit Vorschlagsliste | OK | `Ort ist mehrdeutig: 74388 Talheim Rauher Stich; 91555 Feuchtwangen Heilbronn.` |
| 24 | Mehrdeutiger Ort mit `--erster` | Fake: `notdienst jetzt vorschlag --erster --json` | Treffer des gewählten Orts, Ausgabe nennt gewählten Ort | OK (nach Fix fda0250) | `abfrage.ort=74388 Talheim Rauher Stich`, 3 Treffer, Exit 0 (`scratch/qa/s6_ambig.txt`) |
| 25 | TTY-Auswahl / Fehleingabe / EOF | Fake: Auswahl `2`, `99`, Strg+D | 2 → Treffer; 99 → Exit 2; EOF → Exit 130 | OK | `Auswahl [1-2]:`; `Ungültige Auswahl: 99.`; `Eingabe abgebrochen.`, keine Tracebacks |
| 26 | Details-Mehrfachauswahl TTY | Fake: `details Apotheke --ort umlaut`, Auswahl `2` | genau der gewählte Eintrag | OK | `Schloß-Apotheke (2.00 km)`, kein Kopf/keine Nummer |
| 27 | Leere Trefferliste | Fake: `notdienst jetzt ohnetreffer --json` | Exit 1, nächster Schritt | OK | `Keine Notdienst-Apotheke gefunden` |
| 28 | Quellfehler HTTP 500 | Fake: `notdienst jetzt serverfehler --json` | Exit 3, keine Traceback | OK | `aponet.de antwortet mit HTTP 500.` |
| 29 | Netz nicht erreichbar | `NOTDIENST_BASE_URL=http://127.0.0.1:1 notdienst jetzt heilbronn --json` | Exit 3, nächster Schritt | OK | `aponet.de ist nicht erreichbar. – Netzverbindung prüfen …` |
| 30 | Fehlertext im TTY | `script -qec "notdienst …"` mit Netz-/Datumsfehler | Text auf stderr, kein JSON/Traceback | OK | `Ungültiges Datum: 'quatsch'. – Datum als … angeben.`, Exit 2 |
| 31 | JSON-Fehlerobjekt | `--json` bei Netz-, Datums-, Basis-URL-Fehler | genau ein valides JSON-Objekt | OK | `{"fehler": {"exit_code": …, "meldung": …, "naechster_schritt": …}}` |
| 32 | Nur GETs, User-Agent | lokaler Mitschnitt eines normalen Laufs | 2× GET, UA mit Repo-URL | OK | 2 Requests; `apotheken-notdienst-cli (+https://github.com/smlfg/apotheken-notdienst-cli)` |
| 33 | Cache (10 min) | zweimal `notdienst jetzt heilbronn --json` | 2. Lauf ohne neuen Request | OK | Requests nach Lauf 1: 2, nach Lauf 2: 2; stdout identisch |
| 34 | Unlesbarer Cache-Eintrag | Fake-Cache mit `entfernung_km: "x"`, TTY | Eintrag verwerfen/neu holen, kein Traceback | OK (nach Fix 49e4a8b) | Eintrag verworfen, live 7 Treffer, Exit 0, kein Traceback (`scratch/qa/s6_badcache-tty.log`) |
| 35 | Ungültige Basis-URL (Form) | `NOTDIENST_BASE_URL=notaurl`, `=http://` | Exit 2, klare Meldung | OK | `Ungültige Basis-URL: 'notaurl'. – NOTDIENST_BASE_URL als http(s)://…` |
| 36 | Ungültige Basis-URL (Port/IPv6) | `NOTDIENST_BASE_URL='http://host:abc'`, `='http://[::1'` | Exit 2, klare Meldung, kein Traceback | OK (nach Fix 3b5301a) | je Exit 2, JSON-Fehlerobjekt, kein Traceback (`scratch/qa/json/s6_url_*.out`) |
| 37 | Datum ungültig/außerhalb | `datum quatsch`, `datum 2026-12-01` | Exit 2 mit gültigem Bereich | OK | `Datum zwischen 11.11.2026 und 25.11.2026 wählen` |
| 38 | Radius/Limit/Uhrzeit ungültig | `--radius 0`, `--limit 0`, `--offen-um 25:99` | Exit 2, klare Meldung | OK | `--radius muss zwischen 1 und 50 liegen`, `--limit muss mindestens 1 sein`, `--offen-um erwartet HH:MM` |
| 39 | Kein Standard-Ort | `details Greif` / `jetzt` mit leerem HOME | Exit 1, Verweis auf `standard` | OK | `Kein Standard-Ort gespeichert – mit notdienst standard ORT …` |
| 40 | Standard anzeigen | `notdienst standard --json` | gespeicherter Ort + Pfad | OK | `{"standard_ort": "Heilbronn", "config": "…/config.json"}` |
| 41 | Globale Flags nach Unterkommando | `notdienst jetzt heilbronn --version` | Exit 0 | OK | `notdienst 0.1.0` |
| 42 | Strg+C | Request gegen nicht antwortende Adresse, `SIGINT` | Exit 130, kein Traceback | OK | `Abgebrochen.`, Exit 130 |
| 43 | Unbekannter Ort | `notdienst jetzt Xyzzyquatsch --json` | laut `INTERFACE.md`: Exit 1 wie „keine Treffer“ | OK (nach Fix ca0f32d) | Exit 1, `Keine Notdienst-Apotheke gefunden`; `INTERFACE.md`/README an UX und Akzeptanztest angeglichen (`scratch/qa/json/s6_unbekannter_ort.out`) |
| 44 | Request-Anzahl bei Mehrdeutigkeit | Fake: `--erster` vs. ohne | Doku nennt höchstens drei GETs pro Aufruf | OK (nach Fix fda0250, ca0f32d) | ohne `--erster`: 2 Requests, Exit 2; mit `--erster`: 3 Requests (Formular einmal, zwei Suchen) (`scratch/qa/s6_ambig.txt`) |

## Zählung

- **OK:** 44 (davon 5 nach Fix nachgeprüft)
- **FAIL:** 0
- **Gesamt:** 44

## Behobene FAILs (Nachprüfung)

1. **Basis-URL-Validierung (Port/IPv6):** `http://host:abc` und `http://[::1`
   liefern jetzt Exit 2 mit JSON-Fehlerobjekt und nächstem Schritt, ohne
   Traceback. Fix `3b5301a`; Belege `scratch/qa/json/s6_url_*.out`.
2. **Cache-Schema:** Falsch typisierte Einträge (`entfernung_km` als String)
   werden verworfen und neu geholt. Fix `49e4a8b`; Beleg
   `scratch/qa/s6_badcache-tty.log`.
3. **Ortsname nach Vorschlagsauswahl:** `--erster` und die TTY-Auswahl nennen
   in Kopfzeile und JSON den tatsächlich gewählten Vorschlag. Fix `fda0250`;
   Beleg `scratch/qa/s6_ambig.txt`.
4. **Unbekannter Ort:** Umsetzung bleibt Exit 1 wie „keine Treffer“ (UX-Spec
   und Akzeptanztest); `INTERFACE.md` und README wurden entsprechend
   präzisiert. Fix `ca0f32d`; Beleg
   `scratch/qa/json/s6_unbekannter_ort.out`.
5. **Request-Anzahl:** Ein normaler Lauf bleibt bei zwei GETs; bei
   Mehrdeutigkeit kommt ein dritter Such-GET hinzu, weil die Formularseite
   wiederverwendet wird. README/Interface/Anforderungen nennen jetzt höchstens
   drei GETs. Fix `fda0250`, `ca0f32d`; Beleg `scratch/qa/s6_ambig.txt`.

## Reproduzierbarkeit

- pytest: `scratch/venv/bin/pytest -q` → **63 passed** (0 failed).
- UX-Gate aus S4 bleibt grün (Bericht `docs/UX-GATE.md`); in dieser QA nicht
  verändert.
- Prüfskripte und Rohlogs liegen unter `scratch/qa/` (nicht committet).
