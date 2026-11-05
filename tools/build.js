#!/usr/bin/env node
// streetak.com: one page per language, each with its own SEO head, from one English template.
//   source: tools/site/page.html (English; data-t = text, data-ta = alt, data-tl = aria-label, data-tt = title)
//   words:  tools/i18n/<code>.json  { _meta: where it lives, _seo: the head, _rt: the script's strings, t: the keys }
//   writes: index.html (English, the default, x-default), ar/, pt-br/, fr/ … , sitemap.xml, and en/ redirects to /
// Add a language: copy tools/i18n/en.json to tools/i18n/<code>.json, translate it, add the code to LANGS, run this.
// Usage: node tools/build.js   (no dependencies)
'use strict';
const fs = require('fs'), path = require('path');
const ROOT = path.join(__dirname, '..');
const SITE = 'https://streetak.com';
const PLAY = 'https://play.google.com/store/apps/details?id=com.streetak.football';
const APPSTORE = 'https://apps.apple.com/app/id6826257319';
const WEB_GAME = 'https://play.streetak.com/';
const V = 'v=20261105b';                       // bump when the art or the clips change (browsers keep the old ones)
const COURTS = ['sayeda', 'riyadh', 'dubai', 'sand', 'roof', 'street', 'neon', 'space', 'turf'];
const REEL_DURATION = 'PT18S';
const LANGS = ['en', 'ar', 'pt-BR', 'fr'];     // the order of the language menu; the first is the default at /
const TODAY = new Date().toISOString().slice(0, 10);

const L = LANGS.map(c => JSON.parse(fs.readFileSync(path.join(ROOT, 'tools', 'i18n', c + '.json'), 'utf8')));
const TPL = fs.readFileSync(path.join(ROOT, 'tools', 'site', 'page.html'), 'utf8');
const esc = s => String(s).replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;');
const text = html => html.replace(/<[^>]+>/g, '').replace(/&nbsp;/g, ' ').replace(/&amp;/g, '&').replace(/\s+/g, ' ').trim();
const url = m => SITE + m.path;

function faqOf(html) {
  const out = [];
  for (let i = 1; ; i++) {
    const q = html.match(new RegExp(`data-t="x${i}q"[^>]*>([\\s\\S]*?)</summary>`));
    const a = html.match(new RegExp(`data-t="x${i}a"[^>]*>([\\s\\S]*?)</p>`));
    if (!q || !a) break;
    out.push({ q: text(q[1]), a: text(a[1]) });
  }
  if (!out.length) throw new Error('no FAQ (data-t="x1q") found');
  return out;
}

function head(lang, html) {
  const m = lang._meta, S = lang._seo;
  const OG = `${SITE}/assets/img/${m.og}?${V}`;
  const org = SITE + '/#org', site = SITE + '/#website', game = SITE + '/#game';
  const ld = {
    '@context': 'https://schema.org',
    '@graph': [
      { '@type': 'Organization', '@id': org, name: 'Lamma Labs', url: SITE + '/', email: 'support@streetak.com', logo: SITE + '/icon-512.png' },
      { '@type': 'WebSite', '@id': site, url: SITE + '/', name: 'Streetak', alternateName: ['ستريتك', 'Streetak: Street Football', 'ستريتك: كورة الشارع'], inLanguage: LANGS, publisher: { '@id': org } },
      { '@type': 'WebPage', '@id': url(m) + '#webpage', url: url(m), name: S.title, description: S.desc, inLanguage: m.code, isPartOf: { '@id': site }, about: { '@id': game }, primaryImageOfPage: OG },
      {
        '@type': 'VideoGame', '@id': game, name: S.game, alternateName: ['Streetak', 'ستريتك', 'Streetak: Street Football', 'ستريتك: كورة الشارع'],
        url: url(m), description: S.gameDesc, image: OG,
        screenshot: COURTS.map(n => `${SITE}/assets/img/k/${n}-w.webp`),
        trailer: { '@type': 'VideoObject', name: S.video, description: S.videoDesc, thumbnailUrl: `${SITE}/assets/video/reel.jpg`,
          contentUrl: `${SITE}/assets/video/reel.mp4`, uploadDate: '2026-11-05T12:00:00+02:00', duration: REEL_DURATION, inLanguage: m.code },
        genre: S.genre, gamePlatform: ['Android', 'iOS', 'Web browser'], operatingSystem: 'Android, iOS, Web',
        applicationCategory: 'GameApplication', applicationSubCategory: 'Sports', playMode: 'MultiPlayer',
        inLanguage: ['en', 'ar'], isAccessibleForFree: true,
        offers: { '@type': 'Offer', price: '0', priceCurrency: 'USD', availability: 'https://schema.org/InStock', url: WEB_GAME },
        publisher: { '@id': org }, author: { '@id': org }, sameAs: [PLAY, APPSTORE, WEB_GAME],
      },
      { '@type': 'FAQPage', '@id': url(m) + '#faq', inLanguage: m.code, mainEntity: faqOf(html).map(x => ({ '@type': 'Question', name: x.q, acceptedAnswer: { '@type': 'Answer', text: x.a } })) },
    ],
  };
  const json = JSON.stringify(ld, null, 1).replace(/</g, '\\u003c');
  return [
    `<title>${esc(S.title)}</title>`,
    `<meta name="description" content="${esc(S.desc)}">`,
    `<meta name="robots" content="index,follow,max-image-preview:large">`,
    `<link rel="canonical" href="${url(m)}">`,
    ...L.map(o => `<link rel="alternate" hreflang="${o._meta.hreflang}" href="${url(o._meta)}">`),
    `<link rel="alternate" hreflang="x-default" href="${url(L[0]._meta)}">`,
    `<meta property="og:type" content="website">`,
    `<meta property="og:site_name" content="${m.code === 'ar' ? 'ستريتك' : 'Streetak'}">`,
    `<meta property="og:title" content="${esc(S.ogTitle)}">`,
    `<meta property="og:description" content="${esc(S.ogDesc)}">`,
    `<meta property="og:url" content="${url(m)}">`,
    `<meta property="og:image" content="${OG}">`,
    `<meta property="og:image:width" content="1200">`,
    `<meta property="og:image:height" content="630">`,
    `<meta property="og:image:alt" content="${esc(S.imgAlt)}">`,
    `<meta property="og:locale" content="${m.locale}">`,
    ...L.filter(o => o !== lang).map(o => `<meta property="og:locale:alternate" content="${o._meta.locale}">`),
    `<meta name="twitter:card" content="summary_large_image">`,
    `<meta name="twitter:title" content="${esc(S.ogTitle)}">`,
    `<meta name="twitter:description" content="${esc(S.ogDesc)}">`,
    `<meta name="twitter:image" content="${OG}">`,
    `<meta name="twitter:image:alt" content="${esc(S.imgAlt)}">`,
    `<script type="application/ld+json">\n${json}\n</script>`,
  ].join('\n');
}

function menu(lang) {
  const m = lang._meta;
  const items = L.map(o => {
    const om = o._meta, cur = o === lang ? ' aria-current="page"' : '';
    return `<li><a href="${om.path}" hreflang="${om.hreflang}" lang="${om.code}" data-code="${om.code}"${cur}>${om.name}<small>${om.short}</small></a></li>`;
  }).join('');
  return `<details class="langs"><summary aria-label="${esc(lang._rt.langLabel)}"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.6 2.6 3.8 5.6 3.8 9S14.6 18.4 12 21M12 3C9.4 5.6 8.2 8.6 8.2 12S9.4 18.4 12 21"/></svg><span>${m.short}</span><i aria-hidden="true">▾</i></summary><ul>${items}</ul></details>`;
}

const SEO_RE = /(<!-- seo:start[^>]*-->\n)[\s\S]*?(<!-- seo:end -->)/;
function page(lang) {
  const m = lang._meta, T = lang.t, missing = new Set();
  let h = TPL.replace('{{lang}}', m.code).replace('{{dir}}', m.dir).replace('{{code}}', m.code);
  h = h.replace(/<([a-z0-9]+)([^>]*?)\sdata-t="([^"]+)"([^>]*)>([\s\S]*?)<\/\1>/g, (all, tag, pre, key, post) => {
    if (T[key] == null) { missing.add(key); return all; }
    return `<${tag}${pre} data-t="${key}"${post}>${T[key]}</${tag}>`;
  });
  h = h.replace(/<img\b[^>]*\sdata-ta="([^"]+)"[^>]*>/g, (tag, key) => {
    if (T[key] == null) { missing.add(key); return tag; }
    return tag.replace(/\salt="[^"]*"/, ` alt="${esc(T[key])}"`);
  });
  for (const [attr, name] of [['data-tl', 'aria-label'], ['data-tt', 'title']]) {
    h = h.replace(new RegExp(`<[a-z][^>]*\\s${attr}="([^"]+)"[^>]*>`, 'g'), (tag, key) => {
      if (T[key] == null) { missing.add(key); return tag; }
      return tag.replace(new RegExp(`\\s${name}="[^"]*"`), ` ${name}="${esc(T[key])}"`);
    });
  }
  if (missing.size) throw new Error(`${m.code}: missing ${[...missing].join(', ')}`);
  h = h.replace('<!-- langs -->', menu(lang));
  h = h.replace('/*rt*/{}/*/rt*/', JSON.stringify(lang._rt).replace(/</g, '\\u003c'));
  h = h.replace('/*pages*/{}/*/pages*/', JSON.stringify(Object.fromEntries(L.map(o => [o._meta.code, o._meta.path]))));
  h = h.replace(/href="credits\.html"/g, `href="${m.credits}"`);
  if (m.path !== '/') {
    const dir = m.path.replace(/^\//, '');
    h = h.replace('<meta charset="utf-8">', '<meta charset="utf-8">\n<base href="/">');
    h = h.replace(/href="#([a-z][\w-]*)"/g, `href="${dir}#$1"`);   // with <base href="/">, keep in-page links on this page
  }
  h = h.replace(SEO_RE, (_, a, b) => a + head(lang, h) + '\n' + b);
  h = h.replace('<!doctype html>', '<!doctype html>\n<!-- GENERATED by tools/build.js from tools/site/page.html and tools/i18n: do not edit by hand -->');
  const out = path.join(ROOT, m.path, 'index.html');
  fs.mkdirSync(path.dirname(out), { recursive: true });
  fs.writeFileSync(out, h);
  return out;
}

const written = L.map(page);

// the old English address: /en/ and /en/credits.html now live at / and /credits.html
const redirect = to => `<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><title>Streetak</title><meta name="robots" content="noindex">` +
  `<link rel="canonical" href="${SITE}${to}"><meta http-equiv="refresh" content="0; url=${to}"><script>location.replace(${JSON.stringify(to)}+location.hash)</script></head>` +
  `<body><a href="${to}">Streetak</a></body></html>\n`;
fs.mkdirSync(path.join(ROOT, 'en'), { recursive: true });
fs.writeFileSync(path.join(ROOT, 'en', 'index.html'), redirect('/'));
fs.writeFileSync(path.join(ROOT, 'en', 'credits.html'), redirect('/credits.html'));

// sitemap: every language page with its alternates and the courts' pictures; the credits in English and Arabic
const alt = list => list.map(([hl, u]) => `<xhtml:link rel="alternate" hreflang="${hl}" href="${u}"/>`).join('\n');
const pages = L.map(o => [o._meta.hreflang, url(o._meta)]).concat([['x-default', url(L[0]._meta)]]);
const imgs = COURTS.map(c => `<image:image><image:loc>${SITE}/assets/img/k/${c}-w.webp</image:loc></image:image>`).join('\n');
const cred = [['en', SITE + '/credits.html'], ['ar', SITE + '/ar/credits.html'], ['x-default', SITE + '/credits.html']];
const sm = ['<?xml version="1.0" encoding="UTF-8"?>',
  '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">',
  ...L.map(o => `<url><loc>${url(o._meta)}</loc><lastmod>${TODAY}</lastmod>\n${alt(pages)}\n${imgs}</url>`),
  ...cred.slice(0, 2).map(([, u]) => `<url><loc>${u}</loc><lastmod>${TODAY}</lastmod>\n${alt(cred)}</url>`),
  '</urlset>', ''].join('\n');
fs.writeFileSync(path.join(ROOT, 'sitemap.xml'), sm);

// a word left in another language's script on a page (outside scripts): printed for a look
for (const f of written) {
  const h = fs.readFileSync(f, 'utf8').replace(/<script[\s\S]*?<\/script>/g, '').replace(/<style[\s\S]*?<\/style>/g, '').replace(/<details class="langs">[\s\S]*?<\/details>/, '');
  const isAr = f.includes(path.sep + 'ar' + path.sep);
  const left = (h.match(isAr ? /[^<>]*\b(the|and|your)\b[^<>]*/g : /[^<>]*[؀-ۿ][^<>]*/g) || []).map(s => s.trim()).filter(Boolean);
  console.log(path.relative(ROOT, f) + (left.length ? '  left: ' + left.slice(0, 5).join(' | ') : ''));
}
console.log('sitemap.xml, en/ redirects');
