// Verifica del sito in un browser headless.
// Uso: node _src/check.js [porta]   (con un server statico già avviato su public/)
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const PORT = process.argv[2] || 8123;
const BASE = `http://127.0.0.1:${PORT}`;
const OUT = process.env.SHOTS || '/tmp/shots';
fs.mkdirSync(OUT, { recursive: true });

const PAGES = ['/', '/headshot/', '/ritratto/', '/team-aziendali/', '/studio/', '/portfolio/', '/lizard/', '/privacy/', '/cookie/', '/grazie/', '/404.html',
  '/en/', '/en/headshot/', '/en/portrait/', '/en/corporate-headshots/', '/en/studio-rental/', '/en/portfolio/', '/en/lizard/', '/en/privacy/', '/en/cookies/', '/en/thank-you/'];
const SIZES = [[1440, 900], [1366, 768], [1280, 720], [1024, 768], [768, 1024], [390, 844]];

(async () => {
  const browser = await chromium.launch();
  const problems = [];
  const seenLinks = new Set();
  for (const [w, h] of SIZES) {
    const ctx = await browser.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: 1 });
    for (const p of PAGES) {
      const page = await ctx.newPage();
      const errs = [];
      page.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
      page.on('pageerror', e => errs.push('JS: ' + e.message));
      page.on('response', r => { if (r.status() >= 400 && !r.url().endsWith('/404.html')) errs.push(`${r.status()} ${r.url()}`); });
      await page.goto(BASE + p, { waitUntil: 'networkidle' });
      // scorre la pagina per attivare lazy-load e animazioni
      await page.evaluate(async () => {
        for (let y = 0; y < document.body.scrollHeight; y += 500) { window.scrollTo(0, y); await new Promise(r => setTimeout(r, 30)); }
        window.scrollTo(0, 0);
      });
      await page.waitForTimeout(400);
      const r = await page.evaluate(() => {
        const out = { hscroll: document.documentElement.scrollWidth > window.innerWidth + 1, overflow: [], ld: [], anchors: [], links: [], imgsNoAlt: 0 };
        document.querySelectorAll('h1, h2, .h-xl, .h-lg, .h-md').forEach(el => {
          const parent = el.parentElement.getBoundingClientRect();
          const b = el.getBoundingClientRect();
          if (el.scrollWidth > el.clientWidth + 2 || b.right > parent.right + 2 || b.right > window.innerWidth) out.overflow.push(el.textContent.trim().slice(0, 40));
        });
        document.querySelectorAll('script[type="application/ld+json"]').forEach(s => { try { JSON.parse(s.textContent); } catch (e) { out.ld.push(e.message); } });
        document.querySelectorAll('a[href^="#"]').forEach(a => { const id = a.getAttribute('href').slice(1); if (id && !document.getElementById(id)) out.anchors.push(id); });
        document.querySelectorAll('a[href]').forEach(a => out.links.push(a.getAttribute('href')));
        document.querySelectorAll('img').forEach(i => { if (!i.hasAttribute('alt')) out.imgsNoAlt++; });
        return out;
      });
      if (errs.length) problems.push(`[${w}] ${p} errori: ${[...new Set(errs)].join(' | ')}`);
      if (r.hscroll) problems.push(`[${w}] ${p} scroll orizzontale`);
      if (r.overflow.length) problems.push(`[${w}] ${p} titoli fuori colonna: ${r.overflow.join(' / ')}`);
      if (r.ld.length) problems.push(`[${w}] ${p} JSON-LD non valido: ${r.ld.join(' | ')}`);
      if (r.anchors.length) problems.push(`[${w}] ${p} ancore mancanti: ${r.anchors.join(', ')}`);
      if (r.imgsNoAlt) problems.push(`[${w}] ${p} immagini senza alt: ${r.imgsNoAlt}`);
      r.links.forEach(l => seenLinks.add(JSON.stringify([p, l])));
      if (['/', '/en/', '/studio/', '/ritratto/', '/lizard/'].includes(p)) {
        await page.screenshot({ path: path.join(OUT, `${p.replace(/\//g, '_') || 'home'}-${w}.png`), fullPage: w <= 390 || w === 1440 });
      }
      await page.close();
    }
    await ctx.close();
  }
  // link interni: verifica che le pagine e le ancore esistano
  const ctx = await browser.newContext();
  const pg = await ctx.newPage();
  const checked = new Map();
  for (const s of seenLinks) {
    const [from, href] = JSON.parse(s);
    if (/^(https?:|mailto:|tel:)/.test(href) || href.startsWith('#')) continue;
    const url = new URL(href, BASE + from);
    const key = url.pathname;
    if (!checked.has(key)) {
      const resp = await pg.request.get(BASE + key);
      checked.set(key, resp.status());
    }
    if (checked.get(key) >= 400) problems.push(`link rotto da ${from}: ${href} (${checked.get(key)})`);
    if (url.hash && checked.get(key) < 400) {
      await pg.goto(BASE + key);
      const ok = await pg.evaluate(id => !!document.getElementById(id), url.hash.slice(1));
      if (!ok) problems.push(`ancora mancante da ${from}: ${href}`);
    }
  }
  // selettore: cambia risposte e controlla consiglio + precompilazione
  await pg.setViewportSize({ width: 1280, height: 800 });
  await pg.goto(BASE + '/');
  await pg.click('text=Un team');
  const t1 = await pg.textContent('[data-r="title"]');
  await pg.click('text=Solo io');
  await pg.click('text=Per me, o un regalo');
  const t2 = await pg.textContent('[data-r="title"]');
  await pg.click('[data-r="cta"]');
  await pg.waitForTimeout(900);
  const sel = await pg.$eval('form[name="contatti"] select[name="sessione"]', s => s.value);
  const msg = await pg.$eval('form[name="contatti"] textarea[name="messaggio"]', t => t.value);
  if (!/team/i.test(t1) || !/Ritratto/.test(t2) || sel !== 'ritratto' || !msg) problems.push(`selettore: "${t1}" / "${t2}" / ${sel} / ${msg}`);
  // finestra galleria
  await pg.goto(BASE + '/ritratto/');
  await pg.click('[data-gallery="ritratti"] a >> nth=1');
  await pg.waitForTimeout(400);
  const open = await pg.$eval('#lightbox', d => d.open && !!d.querySelector('img').getAttribute('src'));
  await pg.keyboard.press('ArrowRight');
  const cap = await pg.textContent('#lightbox figcaption');
  await pg.keyboard.press('Escape');
  const closed = await pg.$eval('#lightbox', d => !d.open);
  if (!open || cap !== '3 / 8' || !closed) problems.push(`lightbox: open=${open} cap=${cap} closed=${closed}`);
  // menu mobile e intestazione
  await pg.setViewportSize({ width: 390, height: 844 });
  await pg.goto(BASE + '/');
  await pg.click('.menu-toggle');
  const navVisible = await pg.isVisible('#nav a >> nth=0');
  await pg.click('.menu-toggle');
  await pg.mouse.wheel(0, 1500); await pg.waitForTimeout(500);
  await pg.mouse.wheel(0, 600); await pg.waitForTimeout(500);
  const hidden = await pg.$eval('.site-header', h => h.classList.contains('is-hidden'));
  await pg.mouse.wheel(0, -300); await pg.waitForTimeout(500);
  const shown = await pg.$eval('.site-header', h => !h.classList.contains('is-hidden'));
  if (!navVisible || !hidden || !shown) problems.push(`menu/header: nav=${navVisible} hidden=${hidden} shown=${shown}`);
  // riduzione movimento: niente elementi invisibili
  const rctx = await browser.newContext({ reducedMotion: 'reduce' });
  const rp = await rctx.newPage();
  await rp.goto(BASE + '/');
  const invisible = await rp.evaluate(() => [...document.querySelectorAll('[data-reveal],[data-seq]')].filter(e => getComputedStyle(e).opacity === '0').length);
  if (invisible) problems.push(`reduced-motion: ${invisible} elementi invisibili`);
  await browser.close();
  console.log(problems.length ? problems.join('\n') : 'NESSUN PROBLEMA');
})();
