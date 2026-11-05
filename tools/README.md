# streetak.com: how the pages are made

English is the default at `/` (and `x-default`). Each other language has its own page and address: Arabic `/ar/`,
Portuguese (Brazil) `/pt-br/`, French `/fr/`. Every page is static HTML that crawlers read as it is, with its own
title, description, canonical, hreflang for every language, Open Graph image and JSON-LD.

| File | What |
|---|---|
| `tools/site/page.html` | the page's source, in English. Text with `data-t="key"`, `alt` with `data-ta`, `aria-label` with `data-tl`, `title` with `data-tt` |
| `tools/i18n/<code>.json` | one language: `_meta` (address, direction, hreflang, og:locale, its name in the menu, its share image, its credits page), `_seo` (the head and JSON-LD words), `_rt` (the script's words: WhatsApp message, the ticker, labels), `t` (every key of the page) |
| `tools/build.js` | writes `index.html`, `<path>/index.html` for each language, `sitemap.xml` and the old `/en/` redirects. `LANGS` sets the languages and the menu's order (the first is `/`). `V` is the version on the art and clips' URLs: bump it when they change, or browsers keep the old ones |
| `assets/img/og*.jpg` | the share image per language (1200×630) |

## Add a country / language
1. `cp tools/i18n/en.json tools/i18n/<code>.json` (e.g. `es`, `de`, `tr`, `id`), translate `t`, `_seo` and `_rt`, set
   `_meta`: `code`, `path` (`/es/`), `dir`, `hreflang`, `locale` (`es_ES`), `name` (in its own language), `short`,
   `og` (its share image), `credits` (`credits.html` unless it has its own).
2. Add the code to `LANGS` in `tools/build.js`, run `node tools/build.js`.
3. Its share image: `og-<code>.jpg`, 1200×630 (the English one with the words translated).
4. Check: `python3 tools/check_site.py` (every language at 1440 and 390: no overflow, no errors), then push to `main`
   (GitHub Pages deploys it).

Say only what the game has: the game itself speaks English and Arabic for now, so the FAQ «which languages» answers so.
When the game gets the language, change `x4a` in that language's file.

## The language rules (the script in the page)
- The menu (`.langs`) links to each page and remembers the pick (`localStorage.stk_lang`).
- Only `/` redirects: to a remembered pick, a `?lang=<code>`, or, on a first visit, the browser's own language when
  there is a page for it. No other page redirects, so a shared link always opens in its language.
