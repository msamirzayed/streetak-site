#!/usr/bin/env node
// streetak.com: writes the SEO head (title, description, canonical, hreflang, Open Graph, Twitter, JSON-LD) into
// index.html, and generates en/index.html from index.html + the T.en dictionary in its script, so the English page's
// raw HTML (what crawlers read first) is English. Usage: node tools/build.js   (no dependencies)
// Edit the Arabic in index.html (data-t = text, data-ta = alt), its English in T.en, the head words in SEO below.
'use strict';
const fs = require('fs'), path = require('path'), vm = require('vm');
const ROOT = path.join(__dirname, '..');
const SITE = 'https://streetak.com';
const PLAY = 'https://play.google.com/store/apps/details?id=com.streetak.football';
const APPSTORE = 'https://apps.apple.com/app/id6826257319';
const WEB_GAME = 'https://play.streetak.com/';
const OG = SITE + '/assets/img/og.jpg';

const SEO = {
  ar: {
    url: SITE + '/', locale: 'ar_EG', localeAlt: 'en_US',
    title: 'ستريتك: كورة الشارع | لعبة كورة أونلاين ببلاش مع صحابك',
    desc: 'ستريتك لعبة كورة شارع أونلاين ببلاش: 3 ضد 3 و5 ضد 5 مع صحابك في أوضة بكود. كوبري وطاقية ولفّة، ملاعب فوق السطوح وفي الحارة وعند الهرم، وتعليق مصري. أندرويد وآيفون والمتصفح.',
    ogTitle: 'ستريتك: كورة الشارع | الكورة رجعت الشارع',
    ogDesc: 'لعبة كورة شارع أونلاين ببلاش مع صحابك: 3 ضد 3 و5 ضد 5، مهارات الشارع وتعليق مصري. على أندرويد وآيفون والمتصفح.',
    imgAlt: 'ستريتك: كورة الشارع، لعبة كورة أونلاين مع صحابك',
    game: 'ستريتك: كورة الشارع',
    gameDesc: 'لعبة كورة شارع أونلاين ببلاش، 3 ضد 3 و5 ضد 5: لاعيب واحد لكل واحد والكورة حرة، مهارات الشارع (كوبري، طاقية، لفّة، فينتة، تمويه، زحلقة)، ملاعب فوق السطوح وفي الحارة وعند الهرم والقاهرة نيون والفضاء، أوض مع صحابك بكود، نوادي ودورات منها دورة رمضان، وتعليق مصري. مفيش حاجة بتتشترى بتقوّي حد على حد.',
    genre: ['رياضة', 'كرة قدم', 'كورة شارع', 'أونلاين'],
  },
  en: {
    url: SITE + '/en/', locale: 'en_US', localeAlt: 'ar_EG',
    title: 'Streetak: Street Football | Free Online 3v3 Soccer Game',
    desc: 'Free online street football (soccer) game: 3v3 and 5v5 with friends by room code, street skills, Cairo courts and Egyptian commentary. On Android, iPhone and the web.',
    ogTitle: 'Streetak: Street Football | Football is back on the street',
    ogDesc: 'A free online street football game with your friends: 3v3 and 5v5, street skills and Egyptian commentary. On Android, iPhone and the web.',
    imgAlt: 'Streetak: Street Football, an online football game with friends',
    game: 'Streetak: Street Football',
    gameDesc: 'A free online street football (soccer) game, 3v3 and 5v5: one player each and a free ball, street skills (nutmeg, rainbow, roulette, step-over, fake shot, slide tackle), courts on a Cairo rooftop, in an alley, by the pyramids, Neon Cairo and space, rooms with friends by code, clubs and cups including a Ramadan cup, and Egyptian commentary. Nothing you can buy makes anyone stronger.',
    genre: ['Sports', 'Football', 'Street football', 'Online multiplayer'],
  },
};

const esc = s => String(s).replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;');
const text = html => html.replace(/<[^>]+>/g, '').replace(/&nbsp;/g, ' ').replace(/&amp;/g, '&').replace(/\s+/g, ' ').trim();

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
  const S = SEO[lang];
  const org = SITE + '/#org', site = SITE + '/#website', game = SITE + '/#game';
  const ld = {
    '@context': 'https://schema.org',
    '@graph': [
      { '@type': 'Organization', '@id': org, name: 'Lamma Labs', url: SITE + '/', email: 'support@streetak.com', logo: SITE + '/icon-512.png' },
      { '@type': 'WebSite', '@id': site, url: SITE + '/', name: 'ستريتك', alternateName: ['Streetak', 'Streetak: Street Football', 'ستريتك: كورة الشارع'], inLanguage: ['ar', 'en'], publisher: { '@id': org } },
      { '@type': 'WebPage', '@id': S.url + '#webpage', url: S.url, name: S.title, description: S.desc, inLanguage: lang, isPartOf: { '@id': site }, about: { '@id': game }, primaryImageOfPage: OG },
      {
        '@type': 'VideoGame', '@id': game, name: S.game, alternateName: lang === 'ar' ? ['ستريتك', 'Streetak', 'Streetak: Street Football'] : ['Streetak', 'ستريتك', 'ستريتك: كورة الشارع'],
        url: S.url, description: S.gameDesc, image: OG,
        screenshot: ['hero', 'neon', 'roof', 'hara', 'sand', 'space'].map(n => `${SITE}/assets/img/${n}.jpg`),
        genre: S.genre, gamePlatform: ['Android', 'iOS', 'Web browser'], operatingSystem: 'Android, iOS, Web',
        applicationCategory: 'GameApplication', applicationSubCategory: 'Sports', playMode: 'MultiPlayer',
        inLanguage: ['ar', 'en'], isAccessibleForFree: true,
        offers: { '@type': 'Offer', price: '0', priceCurrency: 'USD', availability: 'https://schema.org/InStock', url: WEB_GAME },
        publisher: { '@id': org }, author: { '@id': org }, sameAs: [PLAY, APPSTORE, WEB_GAME],
      },
      { '@type': 'FAQPage', '@id': S.url + '#faq', inLanguage: lang, mainEntity: faqOf(html).map(x => ({ '@type': 'Question', name: x.q, acceptedAnswer: { '@type': 'Answer', text: x.a } })) },
    ],
  };
  const json = JSON.stringify(ld, null, 1).replace(/</g, '\\u003c');
  return [
    `<title>${esc(S.title)}</title>`,
    `<meta name="description" content="${esc(S.desc)}">`,
    `<meta name="robots" content="index,follow,max-image-preview:large">`,
    `<link rel="canonical" href="${S.url}">`,
    `<link rel="alternate" hreflang="ar" href="${SITE}/">`,
    `<link rel="alternate" hreflang="en" href="${SITE}/en/">`,
    `<link rel="alternate" hreflang="x-default" href="${SITE}/">`,
    `<meta property="og:type" content="website">`,
    `<meta property="og:site_name" content="${lang === 'ar' ? 'ستريتك' : 'Streetak'}">`,
    `<meta property="og:title" content="${esc(S.ogTitle)}">`,
    `<meta property="og:description" content="${esc(S.ogDesc)}">`,
    `<meta property="og:url" content="${S.url}">`,
    `<meta property="og:image" content="${OG}">`,
    `<meta property="og:image:width" content="1200">`,
    `<meta property="og:image:height" content="630">`,
    `<meta property="og:image:alt" content="${esc(S.imgAlt)}">`,
    `<meta property="og:locale" content="${S.locale}">`,
    `<meta property="og:locale:alternate" content="${S.localeAlt}">`,
    `<meta name="twitter:card" content="summary_large_image">`,
    `<meta name="twitter:title" content="${esc(S.ogTitle)}">`,
    `<meta name="twitter:description" content="${esc(S.ogDesc)}">`,
    `<meta name="twitter:image" content="${OG}">`,
    `<meta name="twitter:image:alt" content="${esc(S.imgAlt)}">`,
    `<script type="application/ld+json">\n${json}\n</script>`,
  ].join('\n');
}

const SEO_RE = /(<!-- seo:start[^>]*-->\n)[\s\S]*?(<!-- seo:end -->)/;
function withHead(html, lang) {
  if (!SEO_RE.test(html)) throw new Error('no <!-- seo:start --> … <!-- seo:end --> block');
  return html.replace(SEO_RE, (_, a, b) => a + head(lang, html) + '\n' + b);
}

function replaceOnce(s, a, b) {
  const n = s.split(a).length - 1;
  if (n !== 1) throw new Error(`expected one ${JSON.stringify(a)}, found ${n}`);
  return s.replace(a, b);
}

// --- Arabic page: only its head is written
const srcPath = path.join(ROOT, 'index.html');
let ar = fs.readFileSync(srcPath, 'utf8');
ar = withHead(ar, 'ar');
fs.writeFileSync(srcPath, ar);

// --- English page, from the Arabic one
const m = ar.match(/var T=(\{ar:\{\},en:\{[\s\S]*?\}\});/);
if (!m) throw new Error('T dictionary not found');
const EN = vm.runInNewContext('(' + m[1] + ')').en;
const missing = new Set();
let en = ar;
en = en.replace(/<([a-z0-9]+)([^>]*?)\sdata-t="([^"]+)"([^>]*)>([\s\S]*?)<\/\1>/g, (all, tag, pre, key, post) => {
  if (EN[key] == null) { missing.add(key); return all; }
  return `<${tag}${pre} data-t="${key}"${post}>${EN[key]}</${tag}>`;
});
en = en.replace(/<img\b[^>]*\sdata-ta="([^"]+)"[^>]*>/g, (tag, key) => {
  if (EN[key] == null) { missing.add(key); return tag; }
  return tag.replace(/\salt="[^"]*"/, ` alt="${esc(EN[key])}"`);
});
if (missing.size) throw new Error('T.en is missing: ' + [...missing].join(', '));
en = replaceOnce(en, '<html lang="ar" dir="rtl">', '<html lang="en" dir="ltr">');
en = replaceOnce(en, '<meta charset="utf-8">', '<meta charset="utf-8">\n<base href="/">');
en = replaceOnce(en, '<a class="lang" id="lang" href="en/" hreflang="en" lang="en">EN</a>', '<a class="lang" id="lang" href="/" hreflang="ar" lang="ar">عربي</a>');
en = en.replace(/href="credits\.html"/g, 'href="en/credits.html"');
en = en.replace(/href="#([a-z][\w-]*)"/g, 'href="en/#$1"'); // with <base href="/">, keep in-page links on /en/
en = en.replace(SEO_RE, (_, a, b) => a + head('en', en) + '\n' + b);
en = en.replace('<!doctype html>', '<!doctype html>\n<!-- GENERATED by tools/build.js from index.html and T.en: do not edit by hand -->');
fs.writeFileSync(path.join(ROOT, 'en', 'index.html'), en);

// Arabic left in the English page's markup (outside scripts): printed for a look
const body = en.replace(/<script[\s\S]*?<\/script>/g, '').replace(/<style[\s\S]*?<\/style>/g, '');
const left = (body.match(/[^<>]*[؀-ۿ][^<>]*/g) || []).map(s => s.trim()).filter(Boolean);
console.log('index.html: head written · en/index.html: generated' + (left.length ? '\nArabic left in en/index.html: ' + left.join(' | ') : ''));
