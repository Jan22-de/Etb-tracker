"""Erzeugt die Bildschirmfotos für die Anleitung aus der aktuellen index.html (Handy-Ansicht)."""
import asyncio
from playwright.async_api import async_playwright
import os, pathlib
HERE = pathlib.Path(__file__).resolve().parent
APP = (HERE.parent.parent / 'index.html').as_uri()
CHROME = os.environ.get('CHROME', '/usr/bin/google-chrome')
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path=CHROME if os.path.exists(CHROME) else None,args=['--no-sandbox'])
    ctx=await b.new_context(viewport={'width':390,'height':780},device_scale_factor=2,is_mobile=True,has_touch=True,locale='de-DE')
    pg=await ctx.new_page(); errs=[]; pg.on('pageerror',lambda e: errs.append(str(e)))
    async def shot(n): await pg.wait_for_timeout(250); await pg.evaluate("document.getElementById('toast').classList.add('hidden')"); await pg.screenshot(path=str(HERE / 'img' / f'{n}.png'))
    showshare="document.querySelectorAll('.share-only').forEach(b=>b.classList.remove('hidden'))"
    await pg.goto(APP); await pg.wait_for_timeout(300); await pg.evaluate(showshare)
    await shot('00_home_leer')
    await pg.click('[data-click=openConfig]'); await shot('01_ereignisse'); await pg.click('#configModal [data-click=closeConfig] >> nth=-1')
    await pg.click('[data-click=openTeam]')
    names={'5':'Max','6':'Lena','7':'Tom','9':'Mia','10':'Ben','12':'Paul','13':'Emma','16':'Noah'}
    for k,v in names.items(): await pg.fill(f'#nameList input[data-p="{k}"]',v)
    await pg.evaluate("document.activeElement.blur()"); await pg.wait_for_timeout(300); await pg.evaluate("document.querySelector('#setupModal .dbody').scrollTop=0; document.getElementById('nameList').scrollTop=0"); await shot('02a_mannschaft')
    await pg.fill('#rosterTplName','U12'); await pg.evaluate("document.activeElement.blur(); const d=document.querySelector('#setupModal .dbody'); d.scrollTop=d.scrollHeight"); await shot('02_vorlage')
    await pg.click('[data-click=saveRosterTpl]'); await pg.click('#setupSaveBtn')
    await pg.click('[data-click=newGameFlow]'); await pg.fill('#setupOpponent','TV Musterstadt'); await pg.evaluate("document.activeElement.blur()"); await pg.wait_for_timeout(300); await pg.evaluate("document.querySelector('#setupModal .dbody').scrollTop=0; document.getElementById('nameList').scrollTop=0"); await shot('03_neues_spiel')
    await pg.click('#setupSaveBtn')
    for pl,cat in [('5','Steal'),('7','Block'),('10','Assist'),('5','Rebound'),('12','Pass abgefangen'),('16','Freiem Ball nachgehen')]:
      await pg.click(f'.tile[data-p="{pl}"]'); await pg.click(f'.act:text-is("{cat}")')
    await pg.evaluate("hideBanner()"); await shot('03_haupt')
    await pg.click('.tile[data-p="9"]'); await shot('04_menue')
    await pg.click('.act:text-is("Steal + Score")'); await pg.wait_for_timeout(1200); await shot('05_banner')
    await pg.evaluate("hideBanner()")
    await pg.click('#undoBtn'); await shot('06_undo'); await pg.click('#askCancel')
    await pg.click('#bottomNav [data-click=goHome]'); await shot('10_home_laeuft')
    await pg.click('[data-click=continueGame]')
    await pg.evaluate(showshare); await pg.click('#bottomNav [data-click=openExportCurrent]'); await shot('07_export')
    await pg.click('#exportModal [data-click=closeExport] >> nth=0')
    await pg.click('#bottomNav [data-click=finishGame]'); await shot('08_spielende'); await pg.click('#askOk'); await pg.wait_for_timeout(300)
    await shot('11_home_nach')
    await pg.click('.sq[data-click=openArchive]'); await shot('09_archiv'); await pg.click('#archiveModal [data-click=closeArchive] >> nth=0')
    await pg.evaluate(showshare); await pg.click('.sq[data-click=openBackup]'); await shot('12_sicherung')
    print(errs); await b.close()
asyncio.run(main())
