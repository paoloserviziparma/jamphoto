/* JAM Photo — comportamento del sito (nessun cookie, nessun tracciamento) */
(function () {
  'use strict';
  var doc = document.documentElement;
  doc.classList.add('js');
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------- Intestazione che sparisce scorrendo in giù ---------- */
  var header = document.querySelector('.site-header');
  var nav = document.getElementById('nav');
  var toggle = document.querySelector('.menu-toggle');
  var lastY = window.scrollY;
  var ticking = false;
  function menuOpen() { return toggle && toggle.getAttribute('aria-expanded') === 'true'; }
  function onScrollHeader() {
    var y = window.scrollY;
    if (!header) return;
    if (y < 80 || menuOpen() || header.querySelector(':focus-visible')) {
      header.classList.remove('is-hidden');
    } else if (y > lastY + 4) {
      header.classList.add('is-hidden');
    } else if (y < lastY - 4) {
      header.classList.remove('is-hidden');
    }
    lastY = y;
  }

  /* ---------- Menu a tendina su telefono ---------- */
  if (toggle && nav) {
    toggle.addEventListener('click', function () {
      var open = !menuOpen();
      toggle.setAttribute('aria-expanded', String(open));
      nav.classList.toggle('is-open', open);
      if (open) header.classList.remove('is-hidden');
    });
    nav.addEventListener('click', function (e) {
      if (e.target.closest('a')) {
        toggle.setAttribute('aria-expanded', 'false');
        nav.classList.remove('is-open');
      }
    });
    nav.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && menuOpen()) {
        toggle.setAttribute('aria-expanded', 'false');
        nav.classList.remove('is-open');
        toggle.focus();
      }
    });
  }

  /* ---------- Parallax leggero (dimezzato su telefono) ---------- */
  var plx = reduce ? [] : Array.prototype.slice.call(document.querySelectorAll('.parallax'));
  function onScrollParallax() {
    var vh = window.innerHeight;
    var k = window.innerWidth < 768 ? 0.05 : 0.1;
    for (var i = 0; i < plx.length; i++) {
      var box = plx[i];
      var r = box.getBoundingClientRect();
      if (r.bottom < -100 || r.top > vh + 100) continue;
      var center = r.top + r.height / 2 - vh / 2;
      var half = r.height * 0.06; /* l'immagine è alta il 112%: si sposta tra -12% e 0 */
      var off = Math.max(-half, Math.min(half, -center * k)) - half;
      box.style.setProperty('--py', off.toFixed(1) + 'px');
    }
  }

  window.addEventListener('scroll', function () {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(function () {
      onScrollHeader();
      if (plx.length) onScrollParallax();
      ticking = false;
    });
  }, { passive: true });
  window.addEventListener('resize', function () { if (plx.length) onScrollParallax(); }, { passive: true });
  if (plx.length) onScrollParallax();

  /* ---------- Titoli parola per parola ---------- */
  function splitWords(el) {
    var i = 0;
    var walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT, null);
    var nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach(function (node) {
      var parts = node.nodeValue.split(/(\s+)/);
      var frag = document.createDocumentFragment();
      parts.forEach(function (p) {
        if (!p) return;
        if (/^\s+$/.test(p)) { frag.appendChild(document.createTextNode(' ')); return; }
        var w = document.createElement('span');
        w.className = 'w';
        var inner = document.createElement('span');
        inner.textContent = p;
        inner.style.setProperty('--i', i++);
        w.appendChild(inner);
        frag.appendChild(w);
      });
      node.parentNode.replaceChild(frag, node);
    });
    el.setAttribute('aria-label', el.textContent.replace(/\s+/g, ' ').trim());
  }

  /* ---------- Comparsa allo scorrimento (IntersectionObserver) ---------- */
  var reveal = Array.prototype.slice.call(document.querySelectorAll('[data-reveal], .split-title'));
  if (!reduce) {
    document.querySelectorAll('.split-title').forEach(splitWords);
  }
  if (!reduce && 'IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add('is-in'); io.unobserve(en.target); }
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.12 });
    reveal.forEach(function (el) { io.observe(el); });
  } else {
    reveal.forEach(function (el) { el.classList.add('is-in'); });
  }

  /* ---------- Hero: testi in sequenza al caricamento ---------- */
  var hero = document.querySelector('.hero');
  if (hero) {
    hero.querySelectorAll('[data-seq]').forEach(function (el, i) { el.style.setProperty('--s', i); });
    requestAnimationFrame(function () { hero.classList.add('is-loaded'); });
  }

  /* ---------- Galleria a schermo pieno ---------- */
  var lb = document.getElementById('lightbox');
  var groups = {};
  document.querySelectorAll('[data-gallery] a[data-full]').forEach(function (a) {
    var g = a.closest('[data-gallery]').getAttribute('data-gallery');
    (groups[g] = groups[g] || []).push(a);
  });
  if (lb && typeof lb.showModal === 'function') {
    var lbImg = lb.querySelector('img');
    var lbCap = lb.querySelector('figcaption');
    var cur = null, idx = 0, opener = null;
    function show(i) {
      var list = groups[cur];
      idx = (i + list.length) % list.length;
      var a = list[idx];
      var img = a.querySelector('img');
      lbImg.src = a.getAttribute('data-full');
      lbImg.alt = img ? img.alt : '';
      lbCap.textContent = (idx + 1) + ' / ' + list.length;
      var nx = list[(idx + 1) % list.length];
      if (nx) { var pre = new Image(); pre.src = nx.getAttribute('data-full'); }
    }
    Object.keys(groups).forEach(function (g) {
      groups[g].forEach(function (a, i) {
        a.addEventListener('click', function (e) {
          if (e.metaKey || e.ctrlKey || e.shiftKey) return;
          e.preventDefault();
          cur = g; opener = a; show(i);
          lb.showModal();
        });
      });
    });
    lb.querySelector('.lb-prev').addEventListener('click', function () { show(idx - 1); });
    lb.querySelector('.lb-next').addEventListener('click', function () { show(idx + 1); });
    lb.querySelector('.lb-close').addEventListener('click', function () { lb.close(); });
    lb.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowRight') show(idx + 1);
      if (e.key === 'ArrowLeft') show(idx - 1);
    });
    lb.addEventListener('click', function (e) { if (e.target === lb) lb.close(); });
    lb.addEventListener('close', function () { lbImg.removeAttribute('src'); if (opener) opener.focus(); });
    var sx = null;
    lb.addEventListener('touchstart', function (e) { sx = e.touches[0].clientX; }, { passive: true });
    lb.addEventListener('touchend', function (e) {
      if (sx === null) return;
      var dx = e.changedTouches[0].clientX - sx;
      if (Math.abs(dx) > 50) show(idx + (dx < 0 ? 1 : -1));
      sx = null;
    });
  }

  /* ---------- Selettore "quale sessione fa per te" ---------- */
  var quiz = document.getElementById('quiz');
  if (quiz) {
    var data = JSON.parse(quiz.getAttribute('data-results'));
    var out = document.getElementById('quiz-result');
    function pick() {
      var get = function (n) { var c = quiz.querySelector('input[name="' + n + '"]:checked'); return c ? c.value : null; };
      var scopo = get('q-scopo'), persone = get('q-persone'), tempo = get('q-tempo');
      var key;
      if (persone === 'team') key = 'team';
      else if (scopo === 'lavoro' && tempo !== 'comodo') key = 'headshot';
      else key = 'ritratto';
      var r = data[key];
      out.querySelector('[data-r="title"]').textContent = r.title;
      out.querySelector('[data-r="text"]').textContent = r.text;
      var btn = out.querySelector('[data-r="cta"]');
      btn.setAttribute('data-session', key);
      btn.setAttribute('href', r.href);
      return key;
    }
    quiz.addEventListener('change', pick);
    pick();
    out.querySelector('[data-r="cta"]').addEventListener('click', function (e) {
      var form = document.querySelector('form[name="contatti"]');
      if (!form) return;
      e.preventDefault();
      var key = this.getAttribute('data-session');
      var sel = form.querySelector('select[name="sessione"]');
      if (sel) sel.value = key;
      var n = quiz.querySelector('input[name="q-n"]');
      var pers = form.querySelector('input[name="persone"]');
      if (n && n.value && pers) pers.value = n.value;
      var msg = form.querySelector('textarea[name="messaggio"]');
      if (msg && !msg.value) msg.value = data._prefill.replace('{s}', data[key].title);
      form.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block: 'start' });
      setTimeout(function () { var f = form.querySelector('input[name="nome"]'); if (f) f.focus({ preventScroll: true }); }, reduce ? 0 : 600);
    });
  }

  /* ---------- Modulo: sessione preselezionata da ?sessione= ---------- */
  var params = new URLSearchParams(window.location.search);
  var pre = params.get('sessione');
  if (pre) {
    var s = document.querySelector('form[name="contatti"] select[name="sessione"]');
    if (s && s.querySelector('option[value="' + pre + '"]')) s.value = pre;
  }
})();
