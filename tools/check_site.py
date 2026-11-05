"""streetak.com in Chrome: every language page (desktop and phone): JS errors, failed requests, horizontal overflow,
the hero clip, the court switcher; then the language rules (first visit by browser language, the remembered pick,
the old /en/ address). Full-page screenshots to /tmp/s_<lang>_<width>.png."""
import asyncio
import sys

from playwright.async_api import async_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else 'http://localhost:8811'
PAGES = [('/', 'en'), ('/ar/', 'ar'), ('/pt-br/', 'pt'), ('/fr/', 'fr')]
STATE = ("(()=>{var v=document.getElementById('cv');return [v.currentSrc.split('/').pop().split('?')[0],v.paused,"
         "document.getElementById('sname').textContent,document.getElementById('snew').hidden]})()")


async def run():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome',
                                    args=['--no-sandbox', '--autoplay-policy=no-user-gesture-required'])
        for path, tag in PAGES:
            for w, h in [(1440, 900), (390, 844)]:
                ctx = await b.new_context(viewport={'width': w, 'height': h}, locale='en-US')
                pg = await ctx.new_page()
                errs, bad = [], []
                pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
                pg.on('pageerror', lambda e: errs.append(str(e)))
                pg.on('response', lambda r: bad.append(f'{r.status} {r.url}') if r.status >= 400 else None)
                await pg.goto(BASE + path, wait_until='networkidle')
                await pg.wait_for_timeout(1200)
                ov = await pg.evaluate("document.documentElement.scrollWidth-window.innerWidth")
                where = await pg.evaluate("location.pathname")
                H = await pg.evaluate("document.body.scrollHeight")
                for y in range(0, H, 600):
                    await pg.evaluate(f"scrollTo(0,{y})")
                    await pg.wait_for_timeout(50)
                await pg.evaluate("document.getElementById('courts').scrollIntoView()")
                await pg.wait_for_timeout(700)
                await pg.click('.tab[data-c="riyadh"]')
                await pg.wait_for_timeout(1200)
                st = await pg.evaluate(STATE)
                await pg.evaluate("scrollTo(0,0)")
                await pg.wait_for_timeout(600)
                await pg.screenshot(path=f'/tmp/s_{tag}_{w}.png', full_page=True)
                print(tag, w, 'at', where, 'overflow', ov, 'court', st, 'errors', errs[:4], 'bad', bad[:4], flush=True)
                await ctx.close()
        # the language rules
        async def visit(locale, path, store=None):
            ctx = await b.new_context(locale=locale)
            pg = await ctx.new_page()
            if store:
                await pg.goto(BASE + '/fr/')
                await pg.evaluate(f"localStorage.setItem('stk_lang','{store}')")
            await pg.goto(BASE + path)
            await pg.wait_for_timeout(1500)
            r = await pg.evaluate("location.pathname")
            await ctx.close()
            return r
        print('first visit en-US ->', await visit('en-US', '/'))
        print('first visit pt-BR ->', await visit('pt-BR', '/'))
        print('first visit fr-FR ->', await visit('fr-FR', '/'))
        print('first visit ar-EG ->', await visit('ar-EG', '/'))
        print('ar-EG who picked en ->', await visit('ar-EG', '/', store='en'))
        print('en-US who picked ar ->', await visit('en-US', '/', store='ar'))
        print('old /en/ ->', await visit('en-US', '/en/'))
        print('/ar/ never redirects (en-US, picked fr) ->', await visit('en-US', '/ar/', store='fr'))
        # the menu: open it, pick Português
        ctx = await b.new_context(locale='en-US')
        pg = await ctx.new_page()
        await pg.goto(BASE + '/')
        await pg.click('.langs summary')
        await pg.click('.langs a[data-code="pt-BR"]')
        await pg.wait_for_timeout(1200)
        print('menu -> Português:', await pg.evaluate("location.pathname"), await pg.evaluate("localStorage.getItem('stk_lang')"))
        await ctx.close()
        await b.close()


asyncio.run(run())
