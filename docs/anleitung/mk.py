"""Rendert anleitung.html zu ETB_DPC_Anleitung.pdf (A4, mit Seitenzahlen)."""
import asyncio, os, pathlib
HERE = pathlib.Path(__file__).resolve().parent
CHROME = os.environ.get('CHROME', '/usr/bin/google-chrome')
from playwright.async_api import async_playwright
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path=CHROME if os.path.exists(CHROME) else None,args=['--no-sandbox'])
    pg=await b.new_page(); await pg.goto((HERE / 'anleitung.html').as_uri()); await pg.wait_for_timeout(500)
    await pg.pdf(path=str(HERE / 'ETB_DPC_Anleitung.pdf'), format='A4', print_background=True, prefer_css_page_size=True,
      display_header_footer=True, header_template='<span></span>',
      footer_template='<div style="font-size:8px;width:100%;text-align:center;color:#94a3b8;font-family:Arial">Seite <span class="pageNumber"></span> von <span class="totalPages"></span></div>')
    await b.close()
asyncio.run(main())
