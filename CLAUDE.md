# ETB Defensive Point Club – Projektbeschreibung

Offlinefähige Web-App zur Erfassung einer **Defensiv-Punktestatistik** im Jugendbasketball (ETB).
Ein Helfer tippt während des Spiels am Handy Spieler + Aktion an; die App vergibt Punkte, zeigt eine
Live-Statistik und exportiert PDF/Excel/CSV für den Coach.

- **Live:** https://jan22-de.github.io/Etb-tracker/ (GitHub Pages, Branch `main`, Ordner `/`)
- **Sprache der App und der Doku:** Deutsch, Ansprache mit „du“.

## Wichtig vor jeder Änderung

1. **Jeder Push auf `main` ist sofort live** für alle Nutzer. Größere Änderungen auf einem eigenen
   Branch machen und vom Eigentümer prüfen lassen.
2. **Bei jeder Änderung `CACHE` in `sw.js` hochzählen** (`etb-dpc-vN`), sonst bekommen installierte
   Apps das Update nicht. Updates erscheinen beim Nutzer meist beim *zweiten* Öffnen mit Internet.
3. **Vor dem Push testen** (siehe „Testen“). Nie ungetestet hochladen.
4. **Gespeicherte Daten nie brechen:** Nutzer haben echte Spiele im `localStorage`. Formatänderungen
   immer mit Migration (siehe `migrateCategories`, `game.active`-Migration in `init`).

## Dateien

| Datei | Zweck |
|---|---|
| `index.html` | Die gesamte App (HTML, CSS, JS in einer Datei, keine externen Abhängigkeiten) |
| `sw.js` | Service Worker: Offline-Cache, liefert aus dem Cache und aktualisiert im Hintergrund |
| `manifest.webmanifest`, `icon-*.png` | Installierbarkeit („Zum Startbildschirm“) |
| `.nojekyll` | GitHub Pages ohne Jekyll ausliefern |
| `tests/e2e_test.py` | Automatischer Ablauftest (Playwright + Chrome, Handy-Ansicht) |
| `docs/anleitung/` | Bedienungsanleitung: HTML-Quelle, Bildschirmfotos, Skripte, fertiges PDF |

## Bewusste Entscheidungen (vom Eigentümer so gewollt)

- **Keine externen Bibliotheken/CDNs** – alles inline, damit die App in der Halle ohne Netz läuft.
  Symbole sind eigene SVG-`<symbol>`s am Ende von `index.html`.
- **Daten nur auf dem Gerät** (`localStorage`), kein Server, keine Anmeldung, keine Synchronisation.
  Sicherung nur per Datei (Backup speichern/teilen/laden). Das Repo ist öffentlich – **niemals
  Nutzerdaten oder Backups ins Repo**.
- **Excel (.xlsx) und PDF werden in der App selbst erzeugt** (eigener ZIP-/XLSX-Writer und eigener
  PDF-Generator mit Helvetica-Metriken, A4 quer). Grund: Der Druckdialog der Handy-Browser lieferte
  falsche Formate (A5, abgeschnitten). „Über den Browser drucken“ bleibt nur als Ausweichweg.
- **Empfohlener Browser: Chrome (Android) / Safari (iPhone).** Firefox Android öffnet bei
  Blob-Downloads nur `about:blank` (bekannter Mozilla-Fehler) und kann keine Dateien teilen.
- **Start immer im Hauptmenü** (`#home`), nicht direkt im Spiel. Laufendes Spiel = `game.active`.
- **Erfassungsmenü:** öffnet als Leiste von unten, nach **Gruppen** (farbige Überschriften),
  **ohne Punktwerte und ohne Zähler** auf den Knöpfen (Eigentümer: „macht es nur voller“),
  kein „Abbrechen“-Knopf (X oder Tipp daneben). Ereignisnamen in der Einzahl.
- **Standard-Gruppen:** Ball erobert · Korb verteidigt · Einsatz · Mitspieler bedient · Ballverlust.
  Gruppe ist pro Ereignis frei editierbar.
- **Kein Spruch/Slogan** im Hauptmenü.
- **Rückgängig-Knopf** zeigt die letzte Erfassung („#13 Block“), nicht den Text „Rückgängig“.
  Zusätzlich 7-Sekunden-Leiste unten mit „Rückgängig“ und dünnem Fortschrittsbalken.
- **Untere Leiste im Spiel:** Menü · Kader · Ereignisse · Export · Spielende (Symbole mit Text).
- **Spielernamen** optional, klein unter der Nummer (Kacheln, Tabelle, PDF), in Excel/CSV als eigene
  Spalte. Namen von Kindern → Hinweis auf Datenschutz bei geteilten Sicherungen.
- **Sicherungs-Erinnerung** im Hauptmenü, sobald ein beendetes Spiel jünger ist als die letzte
  komplette Sicherung (`etb_last_backup`).
- **Eigene Vorlagen mit Namen:** Ereignis-Vorlagen (plus feste „ETB-Standard“) und Kader-Vorlagen
  (Nummern + Namen). „Nur Einstellungen sichern“ = Ereignisse, Vorlagen, Namen, ohne Spiele.

## Datenmodell (`localStorage`)

| Schlüssel | Inhalt |
|---|---|
| `etb_categories_config` | Ereignisse `[{id, name, points, group}]` – Reihenfolge = Anzeige |
| `etb_game_v2` | Laufendes Spiel `{id, opponent, date, players[], names{}, history[], active, startedAt}` |
| `etb_archive_v2` | Beendete Spiele (Kopie des Spiels + `categories`-Schnappschuss + `finishedAt`) |
| `etb_last_roster`, `etb_player_names` | Zuletzt genutzter Kader, Namen je Trikotnummer |
| `etb_event_templates`, `etb_roster_templates` | Eigene Vorlagen |
| `etb_last_backup` | Zeitpunkt der letzten kompletten Sicherung |
| `etb_basketball_def_app`, `etb_archived_games` | Altformat der ersten (Google-)Version, wird beim Start migriert |

- `history`-Einträge: `{id, time "HH:MM:SS", player, cat}`. **Alle Zahlen werden aus `history`
  berechnet** (`tally`, `pointsOf`) – nie Zähler separat speichern.
- Punktwerte gelten rückwirkend (aktuelle `categories`); archivierte Spiele nutzen ihren Schnappschuss.
- Backup-Datei: `{app:'etb-dpc', version, categories, lastRoster, eventTemplates, rosterTemplates,
  playerNames, game, archive}`; Einstellungen: `{app:'etb-dpc-settings', …}`.

## Aufbau von `index.html`

- Klick-Handling zentral: Elemente mit `data-click="name"` rufen `actions.name(el)` auf.
- Dialoge: `.modal` + `showM(id)` / `hideM(id)`, Sicherheitsabfragen über `await ask(...)`
  (keine `confirm()`/`alert()`).
- Ansichten: `showHome()` / `showGame()` über die Klasse `home` am `<body>`.
- Wichtige Funktionen: `render`, `renderHome`, `recordAction`, `statRows`, `buildXlsx`, `buildCsv`,
  `buildPdf`, `downloadFile`, `shareFile`, `migrateCategories`, `groupsOf`, `fillSetup` (Modi
  `new` / `edit` / `team`).

### Bekannte Stolperfallen

- **CSS-Klassennamen nicht doppelt vergeben.** Die Karte „Spiel läuft“ hieß `.run` – genauso wie die
  Animationsklasse des Fortschrittsbalkens → der Balken wurde riesig und überdeckte „Rückgängig“.
  Jetzt heißt die Animation `.anim`. Neue Klassen vorher mit `grep` prüfen.
- **Reihenfolge/z-index der Dialoge:** Export muss über dem Archiv liegen (`#exportModal{z-index:60}`),
  Sicherheitsabfrage ganz oben (`.modal.top`).
- **Downloads** als `application/octet-stream` und Objekt-URL erst nach 60 s freigeben – sonst brechen
  Downloads auf manchen Handys ab bzw. der Browser versucht, die Datei anzuzeigen.
- **iOS:** Eingabefelder brauchen `font-size:16px` (sonst Zoom) und dürfen kein `user-select:none` haben.
- Datum immer lokal bilden (`todayISO`), nicht über `toISOString()` (UTC → falscher Tag nach Mitternacht).

## Testen

```bash
pip install playwright openpyxl   # falls nötig; Browser: vorhandenes Chrome verwenden
python3 tests/e2e_test.py         # Pfad zu Chrome ggf. per CHROME=/pfad/zu/chrome setzen
```

Der Test spielt in Handy-Ansicht (390×844) durch: Hauptmenü → Mannschaft mit Namen → Neues Spiel →
Aktionen erfassen → Rückgängig → Export PDF/Excel/CSV (Inhalte geprüft) → zurück ins Menü →
Spielende → Archiv-Export → Sicherungs-Erinnerung → Backup. Er meldet jeden fehlgeschlagenen Schritt und JS-Fehler und endet dann mit Fehlercode 1.
Zusätzlich bei Layout-Änderungen **Bildschirmfotos ansehen** (der Test legt sie in `tests/out/` ab).

## Anleitung aktualisieren

`docs/anleitung/`: `shots.py` erzeugt die Bildschirmfotos aus der aktuellen `index.html`,
`mk.py` rendert `anleitung.html` zu `ETB_DPC_Anleitung.pdf` (A4, klickbarer Link + QR-Code).
Nach Änderungen am Ablauf beides neu laufen lassen und das PDF prüfen.

## Ideen-Speicher (noch nicht umgesetzt, nur nach Rücksprache)

- Saison-Auswertung über alle Archivspiele (Rangliste, Schnitt pro Spiel)
- Viertel (Q1–Q4) je Aktion erfassen
- „Nachtippen“: nach „Steal“ kurz „+ Score“ anbieten statt eigener Knöpfe
- Ereignisse ausblenden statt löschen
- Endstand und Notiz zum Spiel
- Archivierte Spiele wieder öffnen/korrigieren
- Querformat-Ansicht (Kacheln und Ereignisse nebeneinander)
- Nicht geplant: Online-Synchronisation (bräuchte Server/Anmeldung, widerspricht „Daten nur auf dem Gerät“)
