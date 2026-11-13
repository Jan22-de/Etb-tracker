"""Ablauftest der ETB-App in Handy-Ansicht.

Aufruf:  python3 tests/e2e_test.py
Chrome:  Standard /usr/bin/google-chrome, sonst Umgebungsvariable CHROME=/pfad/zu/chrome
Ergebnis: Bildschirmfotos und Exportdateien in tests/out/
"""
import asyncio, os, sys, pathlib
from playwright.async_api import async_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / 'tests' / 'out'
APP = (ROOT / 'index.html').as_uri()
CHROME = os.environ.get('CHROME', '/usr/bin/google-chrome')


def check(cond, msg):
    print(('OK   ' if cond else 'FEHL ') + msg)
    if not cond:
        check.failed = True
check.failed = False


async def main():
    OUT.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME if os.path.exists(CHROME) else None, args=['--no-sandbox'])
        ctx = await b.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=2,
                                  is_mobile=True, has_touch=True, accept_downloads=True, locale='de-DE')
        pg = await ctx.new_page()
        errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)

        async def download(selector, name):
            async with pg.expect_download() as d:
                await pg.click(selector)
            dl = await d.value
            await dl.save_as(OUT / name)
            return dl.suggested_filename

        # --- Migration aus Altformat ---
        await pg.goto(APP); await pg.wait_for_timeout(300)
        await pg.evaluate("""localStorage.clear();
          localStorage.setItem('etb_categories_config', JSON.stringify([{id:'assists',name:'Assists',points:2},{id:'steals',name:'Steals',points:2}]));
          localStorage.setItem('etb_game_v2', JSON.stringify({id:'x',opponent:'Alt',date:'2026-11-12',players:['5'],history:[{id:'a',time:'10:00:00',player:'5',cat:'steals'}]}));""")
        await pg.reload(); await pg.wait_for_timeout(300)
        check(await pg.evaluate("game.active === true"), 'Altes Spiel wird als laufend übernommen')
        check(await pg.evaluate("categories[1].name === 'Steal' && categories[1].group === 'Ball erobert'"), 'Alte Ereignisnamen/Gruppen migriert')

        # --- Frischer Start: Hauptmenü ---
        await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(300)
        check(await pg.evaluate("document.body.classList.contains('home')"), 'Start im Hauptmenü')
        await pg.screenshot(path=OUT / '01_home.png')

        # --- Mannschaft mit Namen ---
        await pg.click('[data-click=openTeam]')
        check(await pg.evaluate("document.getElementById('setupGameRow').classList.contains('hidden')"), 'Mannschaft ohne Gegner/Datum')
        await pg.fill('#nameList input[data-p="5"]', 'Max')
        await pg.fill('#nameList input[data-p="7"]', 'Lena-Sophie Müller')
        await pg.click('#setupSaveBtn')

        # --- Neues Spiel ---
        await pg.click('[data-click=newGameFlow]')
        check(await pg.inner_text('#setupSaveBtn') == 'Spiel starten', 'Knopf „Spiel starten“')
        check(await pg.input_value('#nameList input[data-p="5"]') == 'Max', 'Namen vorausgefüllt')
        await pg.fill('#setupOpponent', 'Testgegner Münster')
        await pg.click('#setupSaveBtn')
        check(not await pg.evaluate("document.body.classList.contains('home')"), 'Spielansicht geöffnet')

        # --- Erfassen ---
        for pl, cat in [('5', 'Steal'), ('7', 'Block'), ('10', 'Assist'), ('12', 'Turnover / Offensivfoul')]:
            await pg.click(f'.tile[data-p="{pl}"]')
            await pg.click(f'.act:text-is("{cat}")')
        check(await pg.inner_text('#teamPoints') == '3', 'Teampunkte 2+1+2-2 = 3')
        await pg.click('.tile[data-p="9"]'); await pg.screenshot(path=OUT / '02_aktionsmenue.png')
        await pg.click('.act:text-is("Steal + Score")'); await pg.wait_for_timeout(800)
        bar = await pg.evaluate("document.getElementById('bannerBar').getBoundingClientRect().height")
        check(bar <= 4, f'Fortschrittsbalken dünn ({bar}px)')
        await pg.screenshot(path=OUT / '03_spiel.png')
        await pg.click('#banner .undo')
        check(await pg.evaluate("game.history.length") == 4, 'Rückgängig über grüne Leiste')
        check('Turnover' in await pg.inner_text('#undoLabel'), 'Rückgängig-Knopf zeigt letzte Erfassung')

        # --- Export ---
        await pg.click('#bottomNav [data-click=openExportCurrent]')
        await download('[data-click=exportPdfSave]', 'spiel.pdf')
        await download('[data-click=exportXlsxSave]', 'spiel.xlsx')
        await download('[data-click=exportCsvSave]', 'spiel.csv')
        await pg.click('#exportModal [data-click=closeExport] >> nth=0')
        pdf = (OUT / 'spiel.pdf').read_bytes()
        check(pdf.startswith(b'%PDF') and b'/MediaBox [0 0 842 595]' in pdf, 'PDF ist A4 quer')
        try:
            import openpyxl
            ws = openpyxl.load_workbook(OUT / 'spiel.xlsx')['Statistik']
            rows = list(ws.iter_rows(values_only=True))
            check(rows[4][1] == 'Name' and any(r[0] == '#5' and r[1] == 'Max' for r in rows), 'Excel enthält Namen-Spalte')
        except ImportError:
            print('---- openpyxl fehlt, Excel-Inhalt nicht geprüft')
        csv = (OUT / 'spiel.csv').read_text(encoding='utf-8-sig')
        check('Testgegner Münster' in csv and ';Gesamtpunkte' in csv, 'CSV mit Umlauten und Semikolon')

        # --- Menü / weiter / Spielende ---
        await pg.click('#bottomNav [data-click=goHome]')
        check(await pg.locator('.run').count() == 1, 'Karte „Spiel läuft“ im Hauptmenü')
        await pg.screenshot(path=OUT / '04_home_laeuft.png')
        await pg.click('[data-click=continueGame]')
        await pg.click('#bottomNav [data-click=finishGame]'); await pg.click('#askOk'); await pg.wait_for_timeout(300)
        check(await pg.evaluate("archive.length === 1 && !game.active"), 'Spiel archiviert, kein laufendes Spiel')
        check(await pg.locator('.bkwarn').count() == 1, 'Sicherungs-Erinnerung sichtbar')

        # --- Archiv-Export ---
        await pg.click('.sq[data-click=openArchive]'); await pg.click('[data-click=archiveExport]')
        await download('[data-click=exportPdfSave]', 'archiv.pdf')
        await pg.click('#exportModal [data-click=closeExport] >> nth=0')
        await pg.click('#archiveModal [data-click=closeArchive] >> nth=0')

        # --- Sicherung ---
        await pg.click('.bkwarn .btn')
        await download('[data-click=backupSave]', 'backup.json')
        await pg.click('#backupModal [data-click=closeBackup] >> nth=0')
        check(await pg.locator('.bkwarn').count() == 0, 'Erinnerung nach Sicherung weg')

        # --- Neues Spiel bei laufendem Spiel fragt nach ---
        await pg.click('[data-click=newGameFlow]'); await pg.click('#setupSaveBtn')
        await pg.click('.tile[data-p="5"]'); await pg.click('.act:text-is("Steal")')
        await pg.click('#bottomNav [data-click=goHome]'); await pg.click('[data-click=newGameFlow]')
        check(await pg.is_visible('#askModal'), 'Nachfrage vor neuem Spiel')
        await pg.click('#askOk')
        check(await pg.evaluate("archive.length") == 2, 'Laufendes Spiel archiviert')

        # --- Neu laden: Daten bleiben ---
        await pg.reload(); await pg.wait_for_timeout(300)
        check(await pg.evaluate("archive.length === 2 && archive[0].names['5'] === 'Max'"), 'Daten nach Neuladen erhalten')

        check(not errs, 'Keine JavaScript-Fehler' + (': ' + '; '.join(errs) if errs else ''))
        await b.close()
    print('\nERGEBNIS:', 'FEHLGESCHLAGEN' if check.failed else 'alles bestanden', '· Ausgaben in', OUT)
    sys.exit(1 if check.failed else 0)

asyncio.run(main())
