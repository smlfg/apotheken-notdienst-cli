# UX-Spec: notdienst

Diese Datei beschreibt die drei wichtigsten Aufgaben für Menschen, die den
Notdienst in ihrer Nähe suchen. Alle Befehle sind so abtippbar, wie sie im
Terminal eingegeben werden. Die Beispieldaten stammen aus echten, gekürzten
Antworten der aponet.de-Notdienstsuche vom 11.11.2026.

Das Werkzeug ist rein lesend: Es sucht Notdienst-Apotheken und zeigt Name,
Entfernung, Dienstzeit, Adresse und Telefon. Es gibt keine Buchung, keinen
Login und damit keine schreibende Web-Aktion.

## Meta

Der Befehl heißt `notdienst`. Die Basis-URL lässt sich für den Fake-Server über
`NOTDIENST_BASE_URL` überschreiben. `NOTDIENST_HEUTE` setzt in Tests das
heutige Datum (JJJJ-MM-TT), damit „heute“, „morgen“ und Wochentage
reproduzierbar sind. Im Alltag wird die Variable nicht gesetzt.

```ux-meta
{"tool": "notdienst",
 "install": "pipx install git+https://github.com/smlfg/apotheken-notdienst-cli",
 "base_url_env": "NOTDIENST_BASE_URL",
 "env": {"NOTDIENST_HEUTE": "2026-11-11"}}
```

## Sitzungen

`$` ist ein Befehl, `>` eine Eingabe, `<` eine erwartete Ausgabe und `!` der
erwartete Exit-Code. Die Installation wird von der Harness durch eine lokale
Installation in ein frisches venv ersetzt.

### Installation und Notdienst jetzt

Nach der Installation fragt der Mensch mit einem positional Ort oder einer
Postleitzahl nach dem aktuellen Notdienst. Ohne Argument gilt der gespeicherte
Standard-Ort. Die Ausgabe zeigt pro Treffer Name, Entfernung, Dienstzeit,
Adresse und Telefon.

```ux-session
$ pipx install git+https://github.com/smlfg/apotheken-notdienst-cli
$ notdienst jetzt heilbronn
< Notdienst-Apotheken für heute (11.11.2026) in Heilbronn
< 3 Treffer
< 1) Apotheke im Staufenberg-Zentrum (3.22 km)
<    Notdienst 11.11.2026 08:30 bis 12.11.2026 08:30
<    Staufenbergstr. 31, 74081 Heilbronn
<    Tel: +49 7131 899055
< 2) Heuchelberg-Apotheke (7.50 km)
<    Notdienst 11.11.2026 08:30 bis 12.11.2026 08:30
<    Hauptstr. 46, 74226 Nordheim
<    Tel: +49 7133 17013
< 3) Greif-Apotheke (8.01 km)
<    Notdienst 11.11.2026 08:30 bis 12.11.2026 08:30
<    Frankenweg 5, 74172 Neckarsulm
<    Tel: +49 7132 83811
! exit 0
```

### Notdienst an einem Tag

Für einen anderen Tag stehen `heute`, `morgen`, `samstag`, `sonntag` oder ein
Datum als `JJJJ-MM-TT` bereit. Der Ort bleibt positional und kann auch eine
Postleitzahl sein.

```ux-session
$ notdienst datum samstag 74072
< Notdienst-Apotheken für Samstag, 14.11.2026 in 74072
< 3 Treffer
< 1) Harfensteller Apotheke Wollhaus (0.28 km)
<    Notdienst 14.11.2026 08:30 bis 15.11.2026 08:30
<    Am Wollhaus 4, 74072 Heilbronn
<    Tel: +49 7131 991990
< 2) Engel Apotheke (5.97 km)
<    Notdienst 14.11.2026 08:30 bis 15.11.2026 08:30
<    Marktstr. 37, 74172 Neckarsulm
<    Tel: +49 7132 6182
< 3) apotheke actuell (9.01 km)
<    Notdienst 14.11.2026 08:30 bis 15.11.2026 08:30
<    Schillerstr. 18, 74348 Lauffen am Neckar
<    Tel: +49 7133 17909
! exit 0
```

### Standard-Ort speichern und Details nachlesen

`notdienst standard ORT` merkt sich den Ort in
`~/.config/apotheken-notdienst-cli/config.json` (Rechte 0600). Danach genügt
`notdienst jetzt`. `notdienst details NAME` sucht den Namen als Teilstring im
Notdienst des Standard-Orts und zeigt den vollständigen Eintrag.

```ux-session
$ notdienst standard heilbronn
< Standard-Ort gespeichert: Heilbronn
$ notdienst details Greif
< Greif-Apotheke (8.01 km)
< Notdienst 11.11.2026 08:30 bis 12.11.2026 08:30
< Frankenweg 5, 74172 Neckarsulm
< Tel: +49 7132 83811
! exit 0
```

Gibt es keinen Treffer, endet der Befehl mit Exit 1 und nennt den nächsten
Schritt, zum Beispiel
`Keine Notdienst-Apotheke gefunden – anderen Ort mit notdienst jetzt ORT versuchen.`
Mehrdeutige Orte zeigt das Werkzeug im Terminal als nummerierte Auswahl; ohne
TTY nennt es die Vorschläge und endet mit Exit 2. `--erster` wählt den ersten
Vorschlag. Ein unbekannter Ort führt zu derselben klaren Meldung, nie zu einem
Traceback.

## Lesende Routen

Alle Sitzungen fragen zuerst die Formularseite ab, um die aktuelle `cHash` und
`__trustedProperties` zu bekommen, und rufen danach die Extbase-Suche per GET
auf. Die Suchparameter stehen als Query-Parameter in der URL; es wird nichts
geschrieben. Die konkreten Such-Routen stehen vor der allgemeinen
Formular-Route, weil `path` allein sonst nicht unterscheidbar wäre.

```ux-routes
[{"method":"GET","path":"/notdienstsuche","query_contains":"2026-11-14","response":"tests/fixtures/ux/suche_heilbronn_samstag.html","status":200,"content_type":"text/html; charset=utf-8"},
 {"method":"GET","path":"/notdienstsuche","query_contains":"heilbronn","response":"tests/fixtures/ux/suche_heilbronn_jetzt.html","status":200,"content_type":"text/html; charset=utf-8"},
 {"method":"GET","path":"/notdienstsuche","response":"tests/fixtures/ux/notdienstsuche_form.html","status":200,"content_type":"text/html; charset=utf-8"}]
```

Die Antworten sind gekürzte echte Trefferlisten (drei statt sieben Treffer,
Werbung und Skripte entfernt). Die Formularseite enthält das echte
Formulargerüst mit `cHash` und versteckten Feldern, aber ohne Werbung.

## Keine schreibenden Formularschritte

Die Notdienstsuche ist rein lesend. Deshalb gibt es keinen `ux-formsteps`-Block,
keine `credential_env` und keinen Bestätigungsschritt. UX07, UX08 und UX09
entfallen beziehungsweise werden als SKIP beziehungsweise PASS ohne Aktion
gemeldet. Spätere Befehle wie `notdienst standard` speichern nur lokal und
senden keinen Request.
