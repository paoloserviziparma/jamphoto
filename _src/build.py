"""Genera le pagine HTML statiche del sito in public/.

Uso:  python3 -I _src/build.py
Il sito pubblicato è solo HTML/CSS/JS statico: questo script serve a non
ripetere a mano intestazione, piè di pagina e dati strutturati in ogni pagina.
"""
import hashlib, html, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUB = os.path.join(ROOT, 'public')
SRC = os.path.join(ROOT, '_src')
SITE = 'https://www.jamphoto.it'
TODAY = '2026-10-29'
IMG = json.load(open(os.path.join(SRC, 'images.json')))
LOGO_SVG = open(os.path.join(SRC, 'logo.svg')).read().replace(
    '<svg ', '<svg aria-hidden="true" focusable="false" ', 1).replace(' role="img" aria-label="JAM Photo"', '')

def vhash(p):
    return hashlib.md5(open(os.path.join(PUB, p), 'rb').read()).hexdigest()[:8]
CSS_V = vhash('assets/css/site.css')
JS_V = vhash('assets/js/site.js')

e = lambda s: html.escape(s, quote=True)

PHONE_DISPLAY = '0521 252824'
PHONE_TEL = '+390521252824'
EMAIL = 'paolo@jamphoto.it'
ADDRESS = 'Strada Martinella 76/1, 43124 Parma'
MAPS = 'https://www.google.com/maps/search/?api=1&query=Strada+Martinella+76%2F1%2C+43124+Parma'
INSTAGRAM = 'https://instagram.com/jamphotoglam'
FACEBOOK = 'https://www.facebook.com/jamphoto.it/'

# ------------------------------------------------------------------ percorsi
ROUTES = {
    'home':      {'it': '/', 'en': '/en/'},
    'headshot':  {'it': '/headshot/', 'en': '/en/headshot/'},
    'ritratto':  {'it': '/ritratto/', 'en': '/en/portrait/'},
    'team':      {'it': '/team-aziendali/', 'en': '/en/corporate-headshots/'},
    'studio':    {'it': '/studio/', 'en': '/en/studio-rental/'},
    'portfolio': {'it': '/portfolio/', 'en': '/en/portfolio/'},
    'lizard':    {'it': '/lizard/', 'en': '/en/lizard/'},
    'privacy':   {'it': '/privacy/', 'en': '/en/privacy/'},
    'cookie':    {'it': '/cookie/', 'en': '/en/cookies/'},
    'grazie':    {'it': '/grazie/', 'en': '/en/thank-you/'},
}
R = lambda page, L: ROUTES[page][L]

# ------------------------------------------------------------------ immagini
def img(key, alt, sizes='100vw', cls='', eager=False, sub=None):
    m = IMG[key] if sub is None else sub
    folder = '/assets/img/' + ('lizard/' if key.startswith('lizard-') else '')
    ws = m['sizes']
    biggest = ws[-1]
    h = round(m['h'] * biggest / m['w'])
    srcset = ', '.join(f'{folder}{key}-{w}.webp {w}w' for w in ws)
    small = ws[0]
    attrs = [f'src="{folder}{key}-{small if len(ws) > 1 else biggest}.webp"', f'srcset="{srcset}"', f'sizes="{sizes}"',
             f'width="{biggest}"', f'height="{h}"', f'alt="{e(alt)}"', 'decoding="async"']
    attrs.append('fetchpriority="high"' if eager else 'loading="lazy"')
    if cls:
        attrs.append(f'class="{cls}"')
    return '<img ' + ' '.join(attrs) + '>'

def full(key):
    m = IMG[key]
    return f'/assets/img/{key}-{m["sizes"][-1]}.webp'

def gallery(name, items, L, cls='gallery'):
    out = [f'<div class="{cls}" data-gallery="{name}">']
    for key, alt in items:
        out.append(f'<a href="{full(key)}" data-full="{full(key)}">{img(key, alt, "(max-width: 700px) 100vw, (max-width: 1100px) 50vw, 33vw")}</a>')
    out.append('</div>')
    return ''.join(out)

LIGHTBOX = {
    'it': ('Galleria a schermo pieno', 'Chiudi', 'Foto precedente', 'Foto successiva'),
    'en': ('Full-screen gallery', 'Close', 'Previous photo', 'Next photo'),
}
def lightbox(L):
    t = LIGHTBOX[L]
    return (f'<dialog class="lightbox" id="lightbox" aria-label="{t[0]}"><figure><img alt=""><figcaption></figcaption></figure>'
            f'<button type="button" class="lb-btn lb-close" aria-label="{t[1]}">&times;</button>'
            f'<button type="button" class="lb-btn lb-prev" aria-label="{t[2]}">&larr;</button>'
            f'<button type="button" class="lb-btn lb-next" aria-label="{t[3]}">&rarr;</button></dialog>')

# ------------------------------------------------------------------ testi comuni
UI = {
    'it': {
        'skip': 'Vai al contenuto', 'menu': 'Menu', 'nav_label': 'Menu principale', 'home_label': 'JAM Photo, pagina iniziale',
        'nav': [('headshot', 'Headshot'), ('ritratto', 'Ritratti'), ('team', 'Team aziendali'), ('portfolio', 'Portfolio'),
                ('lizard', 'Lizard'), ('studio', 'Studio'), ('#chi-sono', 'Chi sono')],
        'book': 'Prenota', 'lang_label': 'Lingua',
        'footer_nav': 'Link utili', 'privacy': 'Privacy', 'cookie': 'Cookie',
        'company': '© JAM Photo · Servizi Informatici S.r.l. · P. IVA 01721620340',
        'crumb_home': 'Home',
    },
    'en': {
        'skip': 'Skip to content', 'menu': 'Menu', 'nav_label': 'Main menu', 'home_label': 'JAM Photo, home page',
        'nav': [('headshot', 'Headshots'), ('ritratto', 'Portraits'), ('team', 'Corporate'), ('portfolio', 'Portfolio'),
                ('lizard', 'Lizard'), ('studio', 'Studio'), ('#chi-sono', 'About')],
        'book': 'Book', 'lang_label': 'Language',
        'footer_nav': 'Useful links', 'privacy': 'Privacy', 'cookie': 'Cookies',
        'company': '© JAM Photo · Servizi Informatici S.r.l. · VAT IT01721620340',
        'crumb_home': 'Home',
    },
}

def header(L, page):
    u = UI[L]
    links = []
    for key, label in u['nav']:
        if key.startswith('#'):
            href = R('home', L) + key
            cur = ''
        else:
            href = R(key, L)
            cur = ' aria-current="page"' if key == page else ''
        links.append(f'<a href="{href}"{cur}>{label}</a>')
    links.append(f'<a class="nav-cta" href="{R("home", L)}#contatti">{u["book"]}</a>')
    other = 'en' if L == 'it' else 'it'
    it_href = R(page, 'it') if page in ROUTES else '/'
    en_href = R(page, 'en') if page in ROUTES else '/en/'
    return f'''<a class="skip" href="#main">{u["skip"]}</a>
<header class="site-header">
<div class="wrap">
<a class="brand" href="{R("home", L)}" aria-label="{u["home_label"]}">{LOGO_SVG}</a>
<nav class="nav" id="nav" aria-label="{u["nav_label"]}">{"".join(links)}</nav>
<div class="header-tools">
<div class="lang" role="group" aria-label="{u["lang_label"]}"><a href="{it_href}" hreflang="it" lang="it"{' aria-current="true"' if L == 'it' else ''}>IT</a><span aria-hidden="true">/</span><a href="{en_href}" hreflang="en" lang="en"{' aria-current="true"' if L == 'en' else ''}>EN</a></div>
<a class="btn header-cta" href="{R("home", L)}#contatti">{u["book"].upper()}</a>
<button type="button" class="menu-toggle" aria-expanded="false" aria-controls="nav"><span class="bars" aria-hidden="true"></span>{u["menu"]}</button>
</div>
</div>
</header>'''

def footer(L):
    u = UI[L]
    return f'''<footer class="site-footer on-dark">
<div class="wrap">
<a class="brand" href="{R("home", L)}" aria-label="{u["home_label"]}">{LOGO_SVG}</a>
<p>{u["company"]}<br>{ADDRESS}</p>
<nav aria-label="{u["footer_nav"]}"><a href="{INSTAGRAM}" rel="noopener">Instagram</a><a href="{FACEBOOK}" rel="noopener">Facebook</a><a href="{R("privacy", L)}">{u["privacy"]}</a><a href="{R("cookie", L)}">{u["cookie"]}</a></nav>
</div>
</footer>'''

# ------------------------------------------------------------------ dati strutturati
def business(L):
    desc = {
        'it': 'Fotografo ritrattista a Parma: headshot per LinkedIn, ritratti personali, foto per team aziendali e noleggio di uno studio fotografico di 130 m² con limbo bianco.',
        'en': 'Portrait photographer in Parma, Italy: LinkedIn headshots, personal portraits, corporate team headshots and rental of a 130 m² photo studio with a white cyclorama.',
    }[L]
    return {
        '@type': ['LocalBusiness', 'ProfessionalService'],
        '@id': SITE + '/#business',
        'name': 'JAM Photo',
        'alternateName': 'Jamphoto',
        'legalName': 'Servizi Informatici S.r.l.',
        'vatID': 'IT01721620340',
        'description': desc,
        'url': SITE + R('home', L),
        'logo': SITE + '/assets/img/logo.svg',
        'image': SITE + '/assets/img/og.jpg',
        'telephone': '+39 0521 252824',
        'email': EMAIL,
        'priceRange': '€€',
        'address': {'@type': 'PostalAddress', 'streetAddress': 'Strada Martinella 76/1', 'postalCode': '43124',
                    'addressLocality': 'Parma', 'addressRegion': 'PR', 'addressCountry': 'IT'},
        'hasMap': MAPS,
        'areaServed': {'@type': 'City', 'name': 'Parma'},
        'founder': {'@type': 'Person', 'name': 'Paolo', 'jobTitle': 'Fotografo ritrattista' if L == 'it' else 'Portrait photographer'},
        'sameAs': [INSTAGRAM, FACEBOOK],
    }

def service_ld(name, desc, L, page, price=None, vat_included=True, unit=None):
    d = {'@type': 'Service', 'name': name, 'description': desc, 'serviceType': name,
         'provider': {'@id': SITE + '/#business'}, 'areaServed': {'@type': 'City', 'name': 'Parma'},
         'url': SITE + R(page, L)}
    if price is not None:
        offer = {'@type': 'Offer', 'price': str(price), 'priceCurrency': 'EUR', 'url': SITE + R(page, L),
                 'availability': 'https://schema.org/InStock'}
        spec = {'@type': 'UnitPriceSpecification', 'price': str(price), 'priceCurrency': 'EUR', 'valueAddedTaxIncluded': vat_included}
        if unit:
            spec['unitText'] = unit
        offer['priceSpecification'] = spec
        d['offers'] = offer
    return d

def faq_ld(items):
    return {'@type': 'FAQPage', 'mainEntity': [
        {'@type': 'Question', 'name': re.sub('<[^>]+>', '', q),
         'acceptedAnswer': {'@type': 'Answer', 'text': ' '.join(re.sub('<[^>]+>', '', p) for p in a)}} for q, a in items]}

def crumbs_ld(L, trail):
    items = [{'@type': 'ListItem', 'position': 1, 'name': UI[L]['crumb_home'], 'item': SITE + R('home', L)}]
    for i, (name, page) in enumerate(trail, 2):
        items.append({'@type': 'ListItem', 'position': i, 'name': name, 'item': SITE + R(page, L)})
    return {'@type': 'BreadcrumbList', 'itemListElement': items}

def crumbs_html(L, trail):
    lab = 'Percorso' if L == 'it' else 'Breadcrumb'
    li = [f'<li><a href="{R("home", L)}">{UI[L]["crumb_home"]}</a></li>']
    for name, page in trail[:-1]:
        li.append(f'<li><a href="{R(page, L)}">{name}</a></li>')
    li.append(f'<li aria-current="page">{trail[-1][0]}</li>')
    return f'<nav class="breadcrumb" aria-label="{lab}"><ol>{"".join(li)}</ol></nav>'

# ------------------------------------------------------------------ FAQ
FAQ = {
 'it': {
  'brutto': ('"Ma io non vengo bene in foto"', ['Pensa alla foto del passaporto: possiamo solo migliorare. È il nostro lavoro: sappiamo come farti muovere e dove mettere la luce.', 'Prima di scattare facciamo sempre un briefing per capire cosa vuoi ottenere, guardare qualche esempio e spiegarti come funziona. Lo scopo è farti sembrare naturale, in uno dei tuoi giorni migliori.']),
  'eta': ('Non ho più vent\'anni: ha senso un ritratto?', ['Sì, e spesso è proprio il momento giusto. Un ritratto non serve a sembrare più giovani, ma a sembrare te: lavoriamo con luce, posa ed espressione, non con ritocchi che cambiano i lineamenti.']),
  'dove': ('Meglio in studio o da me?', ['Consigliamo lo studio, in Strada Martinella 76/1 a Parma: lì abbiamo il controllo completo di luce e sfondo, e molta luce naturale che a volte usiamo per effetti particolari. Scattiamo collegati al computer, così vedi subito il risultato. E c\'è sempre un caffè, o un bicchiere di vino se i nervi lo chiedono.', 'Se preferisci, veniamo nella tua sede con tutta l\'attrezzatura: basta una stanza con almeno 4 × 4 m liberi. In questo caso si aggiungono il tempo in più e la trasferta.']),
  'vestiti': ('Come mi devo vestire?', ['Prima regola: sentiti a tuo agio in quello che indossi. Abiti nuovi o mai indossati ti irrigidiscono, e abiti troppo impegnativi distolgono l\'attenzione dal viso.', 'Per una foto profilo professionale l\'inquadratura arriva alle spalle: pantaloni e scarpe non si vedono. Porta un paio di outfit, così proviamo abbinamenti diversi.']),
  'trucco': ('Trucco e capelli?', ['Donne: consigliamo un trucco coprente ma naturale, e una piega non guasta. Su richiesta possiamo fornirti una truccatrice professionista che si occupa di te per tutta la sessione. Vogliamo evitare il fotoritocco e non farti sembrare chi non sei, quindi non esagerare.', 'Uomini: capelli in ordine; per la barba, pensa a come stai meglio, con o senza.']),
  'consegna': ('Come ricevo le foto?', ['Normalmente scattiamo 50–100 foto per ogni look. Ne selezioniamo 10–20, che entro 24 ore trovi in una cartella web protetta da password: puoi condividerla con chi vuoi farti aiutare a scegliere, e resta disponibile finché ti serve. Se necessario facciamo qualche piccolo ritocco di postproduzione.']),
  'consegna_prezzo': ('Come ricevo le foto?', ['Normalmente scattiamo 50–100 foto per ogni look. Ne selezioniamo 10–20, che entro 24 ore trovi in una cartella web protetta da password: puoi condividerla con chi vuoi farti aiutare a scegliere, e resta disponibile finché ti serve. Se necessario facciamo qualche piccolo ritocco di postproduzione.', 'È disponibile anche un ritocco professionale, a € 80 per foto.']),
  'pagamento': ('Come posso pagare? E se devo disdire?', ['Accettiamo contanti, ma preferiamo bonifico o PayPal: 50% alla prenotazione e il resto alla fine degli scatti.', 'Se ci avvisi almeno 48 ore prima, fissiamo un nuovo appuntamento senza costi. Se non vuoi riprogrammare, o ci avvisi con meno di 48 ore di anticipo, tratteniamo l\'anticipo a titolo di risarcimento.']),
  'ritorno': ('E se torno per altri scatti?', ['Se sei soddisfatta o soddisfatto e torni più avanti per altri scatti, hai uno sconto del 50%.']),
  'gruppi': ('Fate sconti per gruppi o aziende?', [f'Certo. Il costo varia in base al numero di persone e alla location; per i gruppi aziendali applichiamo tariffe dedicate. Scrivici a <a href="mailto:{EMAIL}">{EMAIL}</a> o usa il modulo qui sotto.']),
  'stampa': ('Fate anche la stampa delle foto?', ['Non direttamente: la stampa non è compresa nel pacchetto, ma possiamo ordinarla per te presso i nostri fornitori.']),
  'studio_incluso': ('Cosa è incluso nel noleggio dello studio?', ['Fondali da 3 m di larghezza in vari colori, sgabelli e scatole in legno, flash con trigger, diffusori e ombrelli, proiettore, impianto stereo, consumo elettrico (4,5 kW disponibili), camerino e bagno con doccia, accesso alla zona caffè.']),
  'studio_accesso': ('Come si arriva allo studio?', ['L\'ingresso è diretto da Strada Martinella 76/1, 43124 Parma; lo studio si raggiunge tramite scale. Il parcheggio è libero.']),
  'studio_extra': ('Potete fornire trucco, parrucchiere o catering?', ['Sì, su richiesta: truccatrice, parrucchiere e catering, anche per la colazione. Indicalo nella richiesta così organizziamo tutto per tempo.']),
 },
 'en': {
  'brutto': ('"But I never look good in photos"', ['Think of your passport photo: we can only do better. It\'s our job to know how to make you move and where to put the light.', 'Before shooting we always have a short briefing to understand what you want, look at a few examples and explain how it works. The goal is for you to look natural, on one of your best days.']),
  'eta': ('I\'m not twenty any more: is a portrait worth it?', ['Yes, and it\'s often exactly the right moment. A portrait isn\'t about looking younger, it\'s about looking like you: we work with light, posing and expression, not with retouching that changes your features.']),
  'dove': ('In the studio or at my place?', ['We recommend the studio at Strada Martinella 76/1 in Parma, where we fully control light and background, and have plenty of natural light we sometimes use for special effects. We shoot tethered to a computer so you see the result immediately. And there\'s always a coffee, or a glass of wine if your nerves need it.', 'If you prefer, we come to your premises with all the equipment: all we need is a room with at least 4 × 4 m of free space. In that case extra time and travel are added.']),
  'vestiti': ('What should I wear?', ['Rule number one: feel comfortable in what you wear. Brand-new or never-worn clothes make you stiff, and very busy outfits draw attention away from your face.', 'For a professional profile photo the frame stops at the shoulders, so trousers and shoes won\'t show. Bring a couple of outfits so we can try different looks.']),
  'trucco': ('Make-up and hair?', ['Women: we recommend natural make-up with good coverage, and a blow-dry never hurts. On request we can provide a professional make-up artist for the whole session. We want to avoid heavy retouching and never make you look like someone else, so don\'t overdo it.', 'Men: tidy hair; as for the beard, go with how you look best, with or without.']),
  'consegna': ('How do I receive my photos?', ['We usually shoot 50–100 photos per look. We select 10–20, which you\'ll find within 24 hours in a password-protected web folder: share it with anyone you want help choosing from, and it stays online as long as you need. Where needed we do some light post-production.']),
  'consegna_prezzo': ('How do I receive my photos?', ['We usually shoot 50–100 photos per look. We select 10–20, which you\'ll find within 24 hours in a password-protected web folder: share it with anyone you want help choosing from, and it stays online as long as you need. Where needed we do some light post-production.', 'Professional retouching is also available at € 80 per photo.']),
  'pagamento': ('How can I pay? And what if I need to cancel?', ['We accept cash, but prefer bank transfer or PayPal: 50% when booking and the balance at the end of the shoot.', 'If you let us know at least 48 hours in advance, we set a new date at no cost. If you don\'t want to reschedule, or tell us less than 48 hours before, the deposit is kept as compensation.']),
  'ritorno': ('What if I come back for more photos?', ['If you\'re happy and come back later for another shoot, you get a 50% discount.']),
  'gruppi': ('Do you offer discounts for groups or companies?', [f'Of course. The price depends on the number of people and the location; corporate groups get dedicated rates. Write to <a href="mailto:{EMAIL}">{EMAIL}</a> or use the form below.']),
  'stampa': ('Do you also print the photos?', ['Not directly: printing isn\'t included in the package, but we\'re happy to order prints for you from our suppliers.']),
  'studio_incluso': ('What\'s included in the studio rental?', ['3 m wide backdrops in several colours, stools and wooden boxes, flash units with trigger, diffusers and umbrellas, projector, sound system, electricity (4.5 kW available), dressing room and bathroom with shower, access to the coffee area.']),
  'studio_accesso': ('How do I get to the studio?', ['Direct entrance from Strada Martinella 76/1, 43124 Parma; the studio is reached by stairs. Parking is free.']),
  'studio_extra': ('Can you provide make-up, hair or catering?', ['Yes, on request: make-up artist, hairdresser and catering, including breakfast. Mention it in your request so we can organise everything in time.']),
 },
}

def faq_block(L, keys, title=None, white=False):
    items = [FAQ[L][k] for k in keys]
    t = title or ('Domande frequenti' if L == 'it' else 'Frequently asked questions')
    dets = ''.join(f'<details><summary>{q}</summary>{"".join(f"<p>{p}</p>" for p in a)}</details>' for q, a in items)
    cls = 'section section--white' if white else 'section'
    return f'''<section class="{cls}" aria-labelledby="faq-t"><div class="wrap split split--top">
<h2 id="faq-t" class="h-md split-title">{t}</h2>
<div class="faq">{dets}</div>
</div></section>''', items

# ------------------------------------------------------------------ modulo contatti
FORM = {
 'it': {'title': 'Prenota la tua sessione', 'lead': 'Scrivici cosa ti serve: ti rispondiamo con le date disponibili.',
        'name': 'Nome e cognome', 'email': 'Email', 'phone': 'Telefono (facoltativo)', 'session': 'Cosa ti interessa',
        'people': 'Numero di persone (per i team)', 'msg': 'Messaggio',
        'opts': [('headshot', 'Headshot LinkedIn'), ('ritratto', 'Ritratto personale'), ('team', 'Headshot per team aziendali'), ('studio', 'Noleggio studio'), ('altro', 'Altro')],
        'privacy': 'Ho letto l\'<a href="/privacy/">informativa privacy</a> e acconsento al trattamento dei miei dati per ricevere una risposta.',
        'send': 'Invia la richiesta', 'hp': 'Non compilare questo campo', 'phone_l': 'Telefono', 'mail_l': 'Email', 'addr_l': 'Indirizzo'},
 'en': {'title': 'Book your session', 'lead': 'Tell us what you need and we\'ll reply with available dates.',
        'name': 'Full name', 'email': 'Email', 'phone': 'Phone (optional)', 'session': 'I\'m interested in',
        'people': 'Number of people (for teams)', 'msg': 'Message',
        'opts': [('headshot', 'LinkedIn headshot'), ('ritratto', 'Personal portrait'), ('team', 'Corporate team headshots'), ('studio', 'Studio rental'), ('altro', 'Something else')],
        'privacy': 'I have read the <a href="/en/privacy/">privacy notice</a> and agree to my data being processed in order to receive a reply.',
        'send': 'Send request', 'hp': 'Leave this field empty', 'phone_l': 'Phone', 'mail_l': 'Email', 'addr_l': 'Address'},
}

def contact_section(L, preselect=None, anchor='contatti'):
    f = FORM[L]
    opts = ''.join(f'<option value="{v}"{" selected" if v == preselect else ""}>{lab}</option>' for v, lab in f['opts'])
    return f'''<section id="{anchor}" class="section section--dark on-dark" aria-labelledby="contact-t"><div class="wrap split split--top">
<div class="stack">
<h2 id="contact-t" class="h-lg split-title">{f["title"]}</h2>
<p class="lead muted">{f["lead"]}</p>
<address class="contact-lines">
<a href="tel:{PHONE_TEL}"><span class="visually-hidden">{f["phone_l"]}: </span>{PHONE_DISPLAY}</a>
<a href="mailto:{EMAIL}"><span class="visually-hidden">{f["mail_l"]}: </span>{EMAIL}</a>
<a href="{MAPS}" rel="noopener"><span class="visually-hidden">{f["addr_l"]}: </span>{ADDRESS}</a>
</address>
</div>
<form class="form" name="contatti" method="POST" action="{R("grazie", L)}" data-netlify="true" netlify-honeypot="bot-field">
<input type="hidden" name="form-name" value="contatti">
<input type="hidden" name="lingua" value="{L}">
<p class="hp"><label>{f["hp"]}<input name="bot-field" tabindex="-1" autocomplete="off"></label></p>
<label class="f">{f["name"]}<input type="text" name="nome" autocomplete="name" required></label>
<label class="f">{f["email"]}<input type="email" name="email" autocomplete="email" required></label>
<label class="f">{f["phone"]}<input type="tel" name="telefono" autocomplete="tel"></label>
<label class="f">{f["session"]}<select name="sessione">{opts}</select></label>
<label class="f">{f["people"]}<input type="number" name="persone" min="1" inputmode="numeric"></label>
<label class="f full">{f["msg"]}<textarea name="messaggio" rows="5"></textarea></label>
<label class="check full"><input type="checkbox" name="privacy" value="accettata" required><span>{f["privacy"]}</span></label>
<button type="submit" class="btn btn--light">{f["send"]}</button>
</form>
</div></section>'''

# ------------------------------------------------------------------ pagina completa
def page(L, key, title, desc, body, ld=None, noindex=False, og_img='/assets/img/og.jpg', has_lightbox=False):
    alt_it = SITE + R(key, 'it') if key in ROUTES else None
    alt_en = SITE + R(key, 'en') if key in ROUTES else None
    canonical = SITE + R(key, L) if key in ROUTES else SITE + '/404.html'
    graph = [business(L)] + (ld or [])
    ldjson = json.dumps({'@context': 'https://schema.org', '@graph': graph}, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    alts = ''
    if alt_it and not noindex:
        alts = (f'<link rel="alternate" hreflang="it" href="{alt_it}">\n<link rel="alternate" hreflang="en" href="{alt_en}">\n'
                f'<link rel="alternate" hreflang="x-default" href="{alt_it}">\n')
    robots = '<meta name="robots" content="noindex, follow">\n' if noindex else ''
    locale = 'it_IT' if L == 'it' else 'en_GB'
    alt_locale = 'en_GB' if L == 'it' else 'it_IT'
    return f'''<!doctype html>
<html lang="{L}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
{robots}<link rel="canonical" href="{canonical}">
{alts}<meta property="og:type" content="website">
<meta property="og:site_name" content="JAM Photo">
<meta property="og:locale" content="{locale}">
<meta property="og:locale:alternate" content="{alt_locale}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{SITE}{og_img}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#0E0E0E">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="icon" href="/favicon-32.png" sizes="32x32" type="image/png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="preload" href="/assets/fonts/bebas-neue-latin-400-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/fonts/manrope-latin-400-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/css/site.css?v={CSS_V}">
<script src="/assets/js/site.js?v={JS_V}" defer></script>
<script type="application/ld+json">{ldjson}</script>
</head>
<body>
{header(L, key)}
<main id="main">
{body}
</main>
{footer(L)}
{lightbox(L) if has_lightbox else ''}
</body>
</html>
'''

def write(path, content):
    out = os.path.join(PUB, path.lstrip('/'))
    if out.endswith('/'):
        out += 'index.html'
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, 'w') as fh:
        fh.write(content)

# ================================================================== HOME
def home(L):
    it = L == 'it'
    T = {
     'title': 'Fotografo ritrattista a Parma – headshot e ritratti | JAM Photo' if it else 'Portrait photographer in Parma, Italy – headshots | JAM Photo',
     'desc': 'Ritratti professionali, headshot per LinkedIn e foto per team aziendali a Parma. Studio di 130 m² con limbo bianco, disponibile anche a noleggio.' if it else
             'Professional portraits, LinkedIn headshots and corporate team photos in Parma, Italy. 130 m² photo studio with white cyclorama, also available for rent.',
    }
    hero_kicker = 'Fotografo ritrattista a Parma · Strada Martinella 76/1' if it else 'Portrait photographer in Parma, Italy · Strada Martinella 76/1'
    hero_lead = ('Ritratti che ti somigliano, in uno dei tuoi giorni migliori. Headshot per LinkedIn, foto coerenti per i team aziendali e ritratti personali per chi ha una storia da raccontare, a qualsiasi età.' if it else
                 'Portraits that look like you, on one of your best days. LinkedIn headshots, consistent photos for corporate teams and personal portraits for anyone with a story to tell, at any age.')
    hero_alt = ('Ritratto in bianco e nero di una donna con lunghi capelli mossi e abito di pizzo nero, una mano tra i capelli e lo sguardo abbassato' if it else
                'Black and white portrait of a woman with long wavy hair in a black lace dress, one hand in her hair, looking down')
    q = lambda a, b: a if it else b

    cards = f'''<div class="cards">
<article class="card" data-reveal><h3 class="h-sm">{q("Headshot LinkedIn", "LinkedIn headshot")}</h3>
<ul><li>{q("60 minuti in studio", "60 minutes in the studio")}</li><li>{q("2 foto postprodotte incluse", "2 retouched photos included")}</li><li>{q("Per LinkedIn, CV, sito e WhatsApp", "For LinkedIn, CV, website and WhatsApp")}</li><li>{q("Gallery riservata per scegliere", "Private gallery to choose from")}</li></ul>
<a class="link-arrow" href="{R("headshot", L)}">{q("Scopri l'headshot", "Discover the headshot")} →</a></article>
<article class="card card--dark" data-reveal="2"><p class="badge note">{q("Il più amato dalle donne", "Women's favourite")}</p><h3 class="h-sm">{q("Ritratto personale", "Personal portrait")}</h3>
<ul><li>{q("120 minuti in studio", "120 minutes in the studio")}</li><li>{q("2 foto postprodotte incluse", "2 retouched photos included")}</li><li>{q("Outfit a scelta", "Outfits of your choice")}</li><li>{q("Per personal brand, book o per te", "For personal branding, a book or just for you")}</li></ul>
<a class="link-arrow" href="{R("ritratto", L)}">{q("Scopri il ritratto", "Discover the portrait")} →</a></article>
<article class="card" data-reveal="3"><h3 class="h-sm">{q("Team aziendali", "Corporate teams")}</h3>
<ul><li>{q("Stessa luce e stesso sfondo per tutti", "Same light and background for everyone")}</li><li>{q("In studio o nella vostra sede", "In the studio or at your offices")}</li><li>{q("Tariffe in base al numero di persone", "Rates based on the number of people")}</li><li>{q("Per sito, LinkedIn e materiali", "For website, LinkedIn and materials")}</li></ul>
<a class="link-arrow" href="{R("team", L)}">{q("Chiedi un preventivo", "Ask for a quote")} →</a></article>
<article class="card" data-reveal="3"><h3 class="h-sm">{q("Noleggio studio", "Studio rental")}</h3>
<ul><li>{q("Giornata intera o mezza giornata", "Full day or half day")}</li><li>{q("130 m², altezza 5,25 m", "130 m², 5.25 m ceiling")}</li><li>{q("Limbo bianco 3,5 × 3,5 m", "3.5 × 3.5 m white cyclorama")}</li><li>{q("Flash, fondali e camerino inclusi", "Flash, backdrops and dressing room included")}</li></ul>
<a class="link-arrow" href="{R("studio", L)}">{q("Vedi lo studio", "See the studio")} →</a></article>
</div>'''

    guide_rows = [
        (q('Headshot LinkedIn', 'LinkedIn headshot'), q('LinkedIn, CV, sito aziendale, WhatsApp', 'LinkedIn, CV, company website, WhatsApp'), q('60 minuti', '60 minutes'), q('2 foto postprodotte e gallery riservata', '2 retouched photos and private gallery'), 'headshot'),
        (q('Ritratto personale', 'Personal portrait'), q('Personal brand, book, un regalo per te', 'Personal branding, a book, a gift to yourself'), q('120 minuti, outfit a scelta', '120 minutes, outfits of your choice'), q('2 foto postprodotte e gallery riservata', '2 retouched photos and private gallery'), 'ritratto'),
        (q('Team aziendali', 'Corporate teams'), q('Tutto il team, sito e materiali aziendali', 'The whole team, website and company materials'), q('In studio o nella vostra sede', 'In the studio or at your offices'), q('Foto coerenti per tutte le persone', 'Consistent photos for everyone'), 'team'),
        (q('Noleggio studio', 'Studio rental'), q('Fotografi, videomaker, produzioni', 'Photographers, videomakers, productions'), q('4 oppure 8 ore', '4 or 8 hours'), q('Sala di 130 m² attrezzata', 'Fully equipped 130 m² studio'), 'studio'),
    ]
    gh = [q('Sessione', 'Session'), q('Ideale per', 'Ideal for'), q('Tempo', 'Time'), q('Cosa ricevi', 'What you get')]
    guide_body = ''.join(
        f'<tr><th scope="row"><a href="{R(p, L)}">{a}</a></th><td data-label="{gh[1]}">{b}</td><td data-label="{gh[2]}">{c}</td><td data-label="{gh[3]}">{d}</td></tr>'
        for a, b, c, d, p in guide_rows)

    vs_cols = [q('Selfie', 'Selfie'), q('Foto di un amico', 'Photo by a friend'), q('Ritratto in studio JAM', 'JAM studio portrait')]
    vs_rows = [
        (q('Luce', 'Light'), q('Quella che c\'è', 'Whatever is there'), q('Casuale', 'Random'), q('Flash e riflettori controllati', 'Controlled flash and reflectors')),
        (q('Sfondo', 'Background'), q('La stanza dietro di te', 'The room behind you'), q('Quello che capita', 'Whatever happens to be there'), q('Fondo pulito, scelto con te', 'Clean backdrop, chosen with you')),
        (q('Posa ed espressione', 'Pose and expression'), q('Braccio teso, angolo dal basso', 'Arm\'s length, low angle'), q('Dipende dall\'amico', 'Depends on the friend'), q('Ti guidiamo scatto dopo scatto', 'We guide you shot by shot')),
        (q('Coerenza nel team', 'Team consistency'), q('Impossibile', 'Impossible'), q('Difficile', 'Hard'), q('Stessa luce per tutti', 'Same light for everyone')),
        (q('Scelta delle foto', 'Choosing photos'), q('Tra pochi tentativi', 'From a few attempts'), q('Tra pochi scatti', 'From a few shots'), q('10–20 foto selezionate in gallery', '10–20 selected photos in a gallery')),
    ]
    vs_body = ''.join(f'<tr><th scope="row">{r[0]}</th><td data-label="{vs_cols[0]}">{r[1]}</td><td data-label="{vs_cols[1]}">{r[2]}</td><td class="hl" data-label="{vs_cols[2]}">{r[3]}</td></tr>' for r in vs_rows)

    quiz_data = {
        'headshot': {'title': q('Headshot LinkedIn', 'LinkedIn headshot'), 'text': q('60 minuti in studio, 2 foto postprodotte incluse e una gallery riservata per scegliere con calma.', '60 minutes in the studio, 2 retouched photos included and a private gallery to choose from at your own pace.'), 'href': R('headshot', L)},
        'ritratto': {'title': q('Ritratto personale', 'Personal portrait'), 'text': q('Due ore tutte per te, outfit a scelta e 2 foto postprodotte incluse.', 'Two hours just for you, outfits of your choice and 2 retouched photos included.'), 'href': R('ritratto', L)},
        'team': {'title': q('Headshot per il team', 'Team headshots'), 'text': q('Stessa luce e stesso sfondo per tutte le persone, in studio o nella vostra sede. Ti prepariamo un preventivo.', 'Same light and background for everyone, in the studio or at your offices. We\'ll prepare a quote.'), 'href': R('team', L)},
        '_prefill': q('Ciao Paolo, il selettore mi consiglia: {s}. Vorrei sapere le prossime date disponibili.', 'Hi Paolo, the selector suggests: {s}. I\'d like to know your next available dates.'),
    }
    def choice(name, opts):
        return '<div class="choices">' + ''.join(
            f'<label><input type="radio" name="{name}" value="{v}"{" checked" if i == 0 else ""}><span>{lab}</span></label>' for i, (v, lab) in enumerate(opts)) + '</div>'
    quiz = f'''<section class="section section--white" aria-labelledby="quiz-t"><div class="wrap split split--top">
<div class="stack">
<h2 id="quiz-t" class="h-md split-title">{q("Quale sessione fa per te?", "Which session is right for you?")}</h2>
<p class="muted">{q("Tre domande, dieci secondi. Ti consigliamo la sessione giusta e ti prepariamo già la richiesta.", "Three questions, ten seconds. We suggest the right session and prepare your request for you.")}</p>
<form id="quiz" class="quiz" data-results="{e(json.dumps(quiz_data, ensure_ascii=False))}" onsubmit="return false">
<fieldset><legend>1. {q("A cosa ti servono le foto?", "What do you need the photos for?")}</legend>{choice("q-scopo", [("lavoro", q("Lavoro e LinkedIn", "Work and LinkedIn")), ("personale", q("Per me, o un regalo", "For me, or a gift")), ("book", q("Book o personal brand", "Book or personal brand"))])}</fieldset>
<fieldset><legend>2. {q("Quante persone?", "How many people?")}</legend>{choice("q-persone", [("solo", q("Solo io", "Just me")), ("team", q("Un team", "A team"))])}</fieldset>
<fieldset><legend>3. {q("Quanto tempo vuoi dedicarci?", "How much time do you want to spend?")}</legend>{choice("q-tempo", [("breve", q("Un'ora basta", "An hour is enough")), ("comodo", q("Me la prendo comoda", "I'll take my time"))])}</fieldset>
<div class="quiz-optional"><label>{q("Quante persone? (facoltativo)", "How many people? (optional)")}<input type="number" name="q-n" min="1" inputmode="numeric"></label></div>
</form>
</div>
<div class="frame" data-reveal>
<div class="result" id="quiz-result" aria-live="polite">
<p class="eyebrow">{q("Il nostro consiglio", "Our suggestion")}</p>
<p class="h-md" data-r="title">{quiz_data["headshot"]["title"]}</p>
<p data-r="text">{quiz_data["headshot"]["text"]}</p>
<a class="btn" data-r="cta" data-session="headshot" href="{R("headshot", L)}">{q("Richiedi questa sessione", "Request this session")}</a>
</div>
</div>
</div></section>'''

    faq_html, faq_items = faq_block(L, ['brutto', 'eta', 'vestiti', 'dove', 'consegna', 'pagamento', 'ritorno'])

    body = f'''<section class="hero"><div class="wrap split">
<div class="stack-lg">
<h1><span class="kicker" data-seq>{hero_kicker}</span><span class="claim h-xl" data-seq>Beautiful<br>people.</span></h1>
<p class="lead" data-seq>{hero_lead}</p>
<div class="btn-row" data-seq><a class="btn" href="#contatti">{q("Prenota una sessione", "Book a session")}</a><a class="btn btn--ghost" href="{R("portfolio", L)}">{q("Guarda i ritratti", "See the portraits")}</a></div>
<p class="small muted" data-seq>{q("Formazione con Joel Grimes, Peter Hurley e Peter Coulson · Studio di 130 m² a Parma", "Trained with Joel Grimes, Peter Hurley and Peter Coulson · 130 m² studio in Parma")}</p>
</div>
<div class="frame"><div class="hero-photo parallax">{img("hero", hero_alt, "(max-width: 900px) 100vw, 46vw", eager=True)}</div></div>
</div></section>

<section class="section section--white" aria-labelledby="servizi-t" id="servizi"><div class="wrap stack-lg">
<div class="head-row"><h2 id="servizi-t" class="h-md split-title">{q("Scegli la tua sessione", "Choose your session")}</h2>
<p class="muted">{q("Ogni sessione inizia con un briefing. Tutti gli scatti arrivano in una gallery riservata, così scegli con calma.", "Every session starts with a briefing. All shots go into a private gallery, so you can choose at your own pace.")}</p></div>
{cards}
</div></section>

<section class="section section--dark on-dark" aria-labelledby="ritratti-t" id="ritratti"><div class="wrap split">
<div class="stack">
<p class="eyebrow">{q("Ritratto personale", "Personal portrait")}</p>
<h2 id="ritratti-t" class="h-lg split-title">{q("Il tuo ritratto.<br>Finalmente.", "Your portrait.<br>At last.")}</h2>
<p class="lead">{q("Non serve sentirsi modelle. Hai un viso che ha vissuto, uno stile tutto tuo e qualcosa da raccontare: il nostro lavoro è trovare la luce giusta e metterti a tuo agio.", "You don't need to feel like a model. You have a face that has lived, a style of your own and something to say: our job is to find the right light and put you at ease.")}</p>
<p class="muted">{q("Due ore tutte per te, gli outfit che ami, un trucco naturale (anche con una truccatrice professionista, se vuoi) e un caffè, o un bicchiere di vino se i nervi lo chiedono. Niente ritocchi che ti trasformano in un'altra persona: solo tu, al tuo meglio.", "Two hours just for you, the outfits you love, natural make-up (with a professional make-up artist if you like) and a coffee, or a glass of wine if your nerves need it. No retouching that turns you into someone else: just you, at your best.")}</p>
<div class="btn-row"><a class="btn btn--light" href="{R("ritratto", L)}">{q("Regalati un ritratto", "Treat yourself to a portrait")}</a></div>
</div>
<div class="duo">
<div class="ph r-23 parallax" data-reveal>{img("chignon-v", q("Ritratto in bianco e nero di una donna con chignon e cardigan nero, una mano alla tempia, su fondo chiaro", "Black and white portrait of a woman with a bun and black cardigan, hand at her temple, on a light background"), "(max-width: 900px) 50vw, 25vw")}</div>
<div class="ph r-23 offset parallax" data-reveal="2">{img("primo-piano", q("Primo piano in bianco e nero di una donna con capelli voluminosi e orecchini chiari, sguardo intenso", "Black and white close-up of a woman with voluminous hair and pale earrings, intense gaze"), "(max-width: 900px) 50vw, 25vw")}</div>
<div class="ph r-32 wide parallax" data-reveal>{img("abito-nero", q("Ritratto in bianco e nero di una donna in abito nero, una mano tra i capelli, davanti a una parete a pannelli bianchi", "Black and white portrait of a woman in a black dress, hand in her hair, in front of a white panelled wall"), "(max-width: 900px) 100vw, 50vw")}</div>
</div>
</div></section>

<section class="section" aria-labelledby="team-t" id="team"><div class="wrap stack-lg">
<div class="split split--top">
<div class="stack"><p class="eyebrow">{q("Headshot aziendali", "Corporate headshots")}</p>
<h2 id="team-t" class="h-lg split-title">{q("Tutto il team,<br>una sola immagine.", "The whole team,<br>one single look.")}</h2></div>
<div class="stack">
<p class="lead">{q("Foto coerenti per tutte le persone dell'azienda: stessa luce, stesso sfondo, stessa qualità, pronte per il sito, LinkedIn e le presentazioni.", "Consistent photos for everyone in the company: same light, same background, same quality, ready for your website, LinkedIn and presentations.")}</p>
<p class="muted">{q("Scattiamo in studio a Parma o veniamo da voi con tutta l'attrezzatura: basta una stanza con almeno 4 × 4 m liberi. Il prezzo dipende dal numero di persone e dalla location.", "We shoot in our Parma studio or come to you with all the equipment: all we need is a room with at least 4 × 4 m of free space. The price depends on the number of people and the location.")}</p>
<div class="btn-row"><a class="btn" href="{R("team", L)}">{q("Chiedi un preventivo per il team", "Get a quote for your team")}</a></div>
</div></div>
<div class="grid-4">
<div class="ph r-45" data-reveal>{img("hs-camicia-nera", q("Headshot a colori di una donna sorridente con camicia nera e braccia incrociate su fondo scuro", "Colour headshot of a smiling woman in a black shirt with folded arms on a dark background"), "(max-width: 700px) 100vw, 25vw", cls="")}</div>
<div class="ph r-45" data-reveal="2">{img("hs-occhiali", q("Headshot a colori di un uomo con occhiali, giacca blu e camicia a righe su fondo grigio", "Colour headshot of a man with glasses, blue jacket and striped shirt on a grey background"), "(max-width: 700px) 100vw, 25vw")}</div>
<div class="ph r-45" data-reveal="3">{img("hs-verde", q("Headshot a colori di una donna bionda con blusa verde petrolio su fondo scuro", "Colour headshot of a blonde woman in a teal blouse on a dark background"), "(max-width: 700px) 100vw, 25vw")}</div>
<div class="ph r-45" data-reveal="3">{img("hs-camicia-blu", q("Headshot a colori di un giovane uomo sorridente con camicia blu su fondo grigio", "Colour headshot of a smiling young man in a blue shirt on a grey background"), "(max-width: 700px) 100vw, 25vw")}</div>
</div>
</div></section>

{quiz}

<section class="section" aria-labelledby="guida-t"><div class="wrap stack-lg">
<div class="head-row"><h2 id="guida-t" class="h-md split-title">{q("Quale sessione scegliere", "Which session to choose")}</h2>
<p class="muted">{q("Un colpo d'occhio sulle differenze. I dettagli sono nelle pagine di ogni servizio.", "The differences at a glance. Full details are on each service page.")}</p></div>
<div class="table-wrap" data-reveal><table class="compare"><caption class="visually-hidden">{q("Confronto tra le sessioni fotografiche", "Comparison of photo sessions")}</caption>
<thead><tr>{''.join(f'<th scope="col">{h}</th>' for h in gh)}</tr></thead><tbody>{guide_body}</tbody></table></div>
</div></section>

<section class="section section--white" aria-labelledby="vs-t"><div class="wrap stack-lg">
<div class="head-row"><h2 id="vs-t" class="h-md split-title">{q("Selfie, amico o studio?", "Selfie, friend or studio?")}</h2>
<p class="muted">{q("Tre modi di avere una foto profilo, messi a confronto.", "Three ways to get a profile photo, compared.")}</p></div>
<div class="table-wrap" data-reveal><table class="compare"><caption class="visually-hidden">{q("Confronto tra selfie, foto di un amico e ritratto in studio", "Comparison between selfie, photo by a friend and studio portrait")}</caption>
<thead><tr><th scope="col"><span class="visually-hidden">{q("Aspetto", "Aspect")}</span></th>{''.join(f'<th scope="col"{" class=\"hl\"" if i == 2 else ""}>{c}</th>' for i, c in enumerate(vs_cols))}</tr></thead><tbody>{vs_body}</tbody></table></div>
</div></section>

<section class="section section--dark on-dark" aria-labelledby="come-t"><div class="wrap stack-lg">
<h2 id="come-t" class="h-md split-title">{q("Come funziona", "How it works")}</h2>
<ol class="steps">
<li data-reveal><span class="n">01</span><strong>Briefing</strong><span>{q("Prima di scattare parliamo di cosa vuoi ottenere, guardiamo insieme qualche esempio e ti spieghiamo come funziona.", "Before shooting we talk about what you want, look at a few examples together and explain how it works.")}</span></li>
<li data-reveal="2"><span class="n">02</span><strong>{q("Lo scatto", "The shoot")}</strong><span>{q("Flash e riflettori per il controllo totale della luce. Scattiamo collegati al computer: vedi subito il risultato.", "Flash and reflectors for full control of the light. We shoot tethered to a computer, so you see the result straight away.")}</span></li>
<li data-reveal="3"><span class="n">03</span><strong>{q("La gallery", "The gallery")}</strong><span>{q("50–100 scatti per ogni look; entro 24 ore trovi 10–20 foto selezionate in una cartella web protetta da password.", "50–100 shots per look; within 24 hours you'll find 10–20 selected photos in a password-protected web folder.")}</span></li>
<li data-reveal="3"><span class="n">04</span><strong>{q("Le tue foto", "Your photos")}</strong><span>{q("Scegli con calma, anche insieme a chi vuoi. Poi ricevi le foto postprodotte.", "Choose at your own pace, with whoever you like. Then you receive your retouched photos.")}</span></li>
</ol>
</div></section>

<section class="section" aria-labelledby="portfolio-t"><div class="wrap stack-lg">
<div class="head-row"><h2 id="portfolio-t" class="h-md split-title">Portfolio</h2><p class="muted">I like white spaces. I like black spaces.</p></div>
<div class="tiles">
<a class="tile" href="{R("portfolio", L)}#ritratti" data-reveal>{img("sorriso-abito", q("Ritratto in bianco e nero di una ragazza sorridente con orecchini importanti; sullo sfondo una figura di spalle in controluce", "Black and white portrait of a smiling young woman with statement earrings; in the background a backlit figure seen from behind"), "(max-width: 700px) 100vw, 25vw")}<span>{q("Ritratti", "Portraits")}</span></a>
<a class="tile" href="{R("portfolio", L)}#fashion" data-reveal="2">{img("armatura", q("Foto fashion in bianco e nero di una modella con abito-armatura traforato e mani sui fianchi", "Black and white fashion photo of a model in a cut-out armour dress with hands on hips"), "(max-width: 700px) 100vw, 25vw")}<span>Fashion</span></a>
<a class="tile" href="{R("portfolio", L)}#headshot" data-reveal="3">{img("hs-ramata", q("Headshot a colori di una ragazza con lunghi capelli ramati e lentiggini su fondo grigio", "Colour headshot of a young woman with long auburn hair and freckles on a grey background"), "(max-width: 700px) 100vw, 25vw")}<span>Headshot</span></a>
<a class="tile" href="{R("lizard", L)}" data-reveal="3">{img("lizard-002", q("Ritratto Lizard: volto di donna in bianco e nero ad alto contrasto su fondo nero", "Lizard portrait: high-contrast black and white face of a woman on a black background"), "(max-width: 700px) 100vw, 25vw", sub=next(x for x in IMG["_lizard"] if x["key"] == "lizard-002"))}<span>Lizard</span></a>
</div>
</div></section>

<section class="section section--white" aria-labelledby="studio-t" id="studio"><div class="wrap split">
<div class="stack">
<p class="eyebrow">{q("JAM Studio · noleggio sala di posa a Parma", "JAM Studio · photo studio rental in Parma")}</p>
<h2 id="studio-t" class="h-lg split-title">{q("130 m² di luce.", "130 m² of light.")}</h2>
<p class="lead">{q("Open space con 5,25 m di altezza sottotrave e un limbo bianco lucido di 3,5 × 3,5 m. Ingresso diretto da Strada Martinella 76/1, parcheggio libero.", "Open space with a 5.25 m ceiling and a 3.5 × 3.5 m glossy white cyclorama. Direct entrance from Strada Martinella 76/1, free parking.")}</p>
<p class="muted">{q("Flash, fondali, camerino con doccia e zona caffè inclusi. Su richiesta: catering, truccatrice, parrucchiere.", "Flash units, backdrops, dressing room with shower and coffee area included. On request: catering, make-up artist, hairdresser.")}</p>
<div class="btn-row"><a class="btn btn--ghost" href="{R("studio", L)}">{q("Scopri lo studio", "Discover the studio")}</a></div>
</div>
<div class="ph r-43 parallax" data-reveal>{img("studio-sala", q("Lo studio JAM: sala bianca a doppia altezza con grandi finestre, limbo bianco, ombrello da studio e scala verso il soppalco", "The JAM studio: double-height white room with large windows, white cyclorama, studio umbrella and stairs to the mezzanine"), "(max-width: 900px) 100vw, 50vw")}</div>
</div></section>

<section class="section" aria-labelledby="paolo-t" id="chi-sono"><div class="wrap split">
<div class="ph r-32 parallax" data-reveal>{img("paolo", q("Paolo, fotografo di JAM Photo, ritratto a colori con camicia blu scuro su fondo grigio", "Paolo, JAM Photo's photographer, colour portrait in a dark blue shirt on a grey background"), "(max-width: 900px) 100vw, 50vw")}</div>
<div class="stack">
<p class="eyebrow">{q("Chi sono", "About me")}</p>
<h2 id="paolo-t" class="h-lg split-title">Paolo.<br>It's never too late.</h2>
<p class="lead">{q("Fotografo ritrattista a Parma. I like white spaces, I like black spaces. Il mio lavoro è farti sembrare naturale in uno dei tuoi giorni migliori: so come farti muovere e dove mettere la luce, tu devi solo esserci.", "Portrait photographer in Parma. I like white spaces, I like black spaces. My job is to make you look natural on one of your best days: I know how to make you move and where to put the light, you just need to show up.")}</p>
<ul class="timeline">
<li><strong>2017</strong> · Joel Grimes Workshop, {q("Milano", "Milan")}</li>
<li><strong>2018</strong> · Peter Hurley Workshop, {q("Londra", "London")}</li>
<li><strong>2019</strong> · Peter Coulson Workshop, {q("Londra", "London")}</li>
<li><strong>2020</strong> · Marianna Santoni, {q("sviluppo RAW, Milano", "RAW development, Milan")}</li>
<li><strong>{q("Premi", "Awards")}</strong> · {q("quasi tutti dicono che sono un bravo fotografo", "almost everyone says I'm a good photographer")}</li>
</ul>
</div>
</div></section>

{faq_html}

{contact_section(L)}'''
    ld = [faq_ld(faq_items),
          service_ld(q('Ritratto fotografico personale', 'Personal portrait session'), q('Sessione di 120 minuti in studio a Parma con outfit a scelta e 2 foto postprodotte incluse.', '120-minute studio session in Parma with outfits of your choice and 2 retouched photos included.'), L, 'ritratto')]
    write(R('home', L), page(L, 'home', T['title'], T['desc'], body, ld))

# ================================================================== pagine servizio
def service_hero(L, trail, eyebrow, title, lead, image_key, alt, extra='', wide=False):
    return f'''<section class="hero"><div class="wrap split">
<div class="stack-lg">
{crumbs_html(L, trail)}
<h1><span class="kicker" data-seq>{eyebrow}</span><span class="claim h-xl" data-seq>{title}</span></h1>
<p class="lead" data-seq>{lead}</p>
{extra}
</div>
<div class="frame"><div class="hero-photo parallax{" hero-photo--wide" if wide else ""}">{img(image_key, alt, "(max-width: 900px) 100vw, 46vw", eager=True)}</div></div>
</div></section>'''

def headshot_page(L):
    it = L == 'it'
    q = lambda a, b: a if it else b
    name = q('Headshot LinkedIn', 'LinkedIn headshot')
    trail = [(name, 'headshot')]
    body = service_hero(L, trail,
        q('Foto profilo LinkedIn a Parma', 'LinkedIn profile photos in Parma, Italy'),
        q('Rock your<br>profile.', 'Rock your<br>profile.'),
        q('Un headshot professionale per LinkedIn, CV, sito aziendale e WhatsApp: un\'immagine riconoscibile ti rende diverso e credibile.', 'A professional headshot for LinkedIn, your CV, company website and WhatsApp: a recognisable image makes you stand out and look credible.'),
        'hs-camicia-nera', q('Headshot a colori di una donna sorridente con camicia nera e braccia incrociate su fondo scuro', 'Colour headshot of a smiling woman in a black shirt with folded arms on a dark background'),
        f'<div class="btn-row" data-seq><a class="btn" href="#prenota">{q("Prenota l\'headshot", "Book your headshot")}</a></div>')
    body += f'''<section class="section section--white" aria-labelledby="pk-t"><div class="wrap split split--top">
<div class="stack"><h2 id="pk-t" class="h-md split-title">{q("LinkedIn headshot session", "LinkedIn headshot session")}</h2>
<p class="lead">{q("La scelta ideale per aggiornare la tua foto profilo sui social.", "The ideal choice to update your social profile photo.")}</p>
<p class="muted">{q("Personal branding: un\'immagine riconoscibile ti rende unico, differente e credibile. Lavoriamo su luce ed espressione, non su filtri.", "Personal branding: a recognisable image makes you unique, different and credible. We work on light and expression, not filters.")}</p></div>
<div class="card" data-reveal><p class="price">€ 199 <small>{q("IVA inclusa", "VAT included")}</small></p>
<ul><li>{q("60 minuti in studio", "60 minutes in the studio")}</li><li>{q("2 foto postprodotte incluse", "2 retouched photos included")}</li><li>{q("Ritratto professionale per uso business", "Professional portrait for business use")}</li><li>{q("Tutti gli scatti in una gallery riservata, per scegliere con calma", "All shots in a private gallery, to choose at your own pace")}</li></ul>
<a class="btn" href="#prenota">{q("Prenota l\'headshot", "Book your headshot")}</a></div>
</div></section>
<section class="section" aria-labelledby="g-t"><div class="wrap stack-lg">
<h2 id="g-t" class="h-md split-title">{q("Alcuni headshot", "Some headshots")}</h2>
{gallery("headshot", [
  ("hs-occhiali", q("Headshot a colori di un uomo con occhiali, giacca blu e camicia a righe su fondo grigio", "Colour headshot of a man with glasses, blue jacket and striped shirt on a grey background")),
  ("hs-verde", q("Headshot a colori di una donna bionda con blusa verde petrolio su fondo scuro", "Colour headshot of a blonde woman in a teal blouse on a dark background")),
  ("hs-blazer", q("Headshot a colori di una donna sorridente con blazer nero e foulard a righe", "Colour headshot of a smiling woman in a black blazer and striped scarf")),
  ("hs-camicia-blu", q("Headshot a colori di un giovane uomo sorridente con camicia blu", "Colour headshot of a smiling young man in a blue shirt")),
  ("hs-ramata", q("Headshot a colori di una ragazza con lunghi capelli ramati e lentiggini", "Colour headshot of a young woman with long auburn hair and freckles")),
  ("hs-tshirt", q("Headshot a colori di un ragazzo con t-shirt nera su fondo grigio scuro", "Colour headshot of a young man in a black t-shirt on a dark grey background")),
  ("hs-coda", q("Headshot a colori di una ragazza sorridente con coda di cavallo e blusa bianca traforata", "Colour headshot of a smiling young woman with a ponytail and white eyelet blouse")),
  ("hs-camicia-nera", q("Headshot a colori di una donna sorridente con camicia nera", "Colour headshot of a smiling woman in a black shirt")),
], L)}
</div></section>'''
    faq_html, items = faq_block(L, ['brutto', 'vestiti', 'trucco', 'dove', 'consegna_prezzo', 'pagamento', 'ritorno', 'stampa'], white=True)
    body += faq_html + contact_section(L, 'headshot', 'prenota')
    desc = q('Headshot professionale per LinkedIn, CV e sito aziendale: 60 minuti in studio a Parma, 2 foto postprodotte, gallery riservata. € 199 IVA inclusa.',
             'Professional headshot for LinkedIn, CV and company website: 60 minutes in our Parma studio, 2 retouched photos, private gallery. € 199 VAT included.')
    ld = [crumbs_ld(L, trail), faq_ld(items), service_ld(name, desc, L, 'headshot', 199, True)]
    write(R('headshot', L), page(L, 'headshot', q('Foto profilo LinkedIn a Parma – headshot | JAM Photo', 'LinkedIn headshot photographer in Parma | JAM Photo'), desc, body, ld, has_lightbox=True))

def ritratto_page(L):
    it = L == 'it'
    q = lambda a, b: a if it else b
    name = q('Ritratto personale', 'Personal portrait')
    trail = [(name, 'ritratto')]
    body = service_hero(L, trail,
        q('Ritratto fotografico a Parma', 'Portrait photography in Parma, Italy'),
        q('Il tuo ritratto.<br>Finalmente.', 'Your portrait.<br>At last.'),
        q('Al tuo meglio, per immagini che non passano mai. Un ritratto pensato per te: per il tuo personal brand, per un book, o semplicemente perché te lo meriti.', 'At your best, for images that never go out of date. A portrait made for you: for your personal brand, for a book, or simply because you deserve it.'),
        'chignon-v', q('Ritratto in bianco e nero di una donna con chignon e cardigan nero, una mano alla tempia', 'Black and white portrait of a woman with a bun and black cardigan, hand at her temple'),
        f'<div class="btn-row" data-seq><a class="btn" href="#prenota">{q("Prenota il tuo ritratto", "Book your portrait")}</a></div>')
    body += f'''<section class="section section--dark on-dark" aria-labelledby="pk-t"><div class="wrap split split--top">
<div class="stack"><h2 id="pk-t" class="h-lg split-title">{q("Non serve sentirsi modelle.", "No need to feel like a model.")}</h2>
<p class="lead">{q("Hai un viso che ha vissuto, uno stile tutto tuo e qualcosa da raccontare. Il nostro lavoro è trovare la luce giusta e metterti a tuo agio: ti guidiamo nella posa, scatto dopo scatto, e vedi subito il risultato sullo schermo.", "You have a face that has lived, a style of your own and something to say. Our job is to find the right light and put you at ease: we guide your pose shot by shot, and you see the result on screen right away.")}</p>
<p class="muted">{q("Niente ritocchi che ti trasformano in un\'altra persona. Vogliamo che tu ti riconosca, in uno dei tuoi giorni migliori.", "No retouching that turns you into someone else. We want you to recognise yourself, on one of your best days.")}</p></div>
<div class="card card--dark card--outline" data-reveal><p class="price">€ 350 <small>{q("IVA inclusa", "VAT included")}</small></p>
<ul><li>{q("120 minuti in studio", "120 minutes in the studio")}</li><li>{q("2 foto postprodotte incluse", "2 retouched photos included")}</li><li>{q("Outfit a scelta", "Outfits of your choice")}</li><li>{q("Ritratto professionale per personal brand o book", "Professional portrait for personal branding or a book")}</li><li>{q("Tutti gli scatti in una gallery riservata, per scegliere con calma", "All shots in a private gallery, to choose at your own pace")}</li><li>{q("Truccatrice professionista su richiesta", "Professional make-up artist on request")}</li></ul>
<a class="btn btn--light" href="#prenota">{q("Prenota il tuo ritratto", "Book your portrait")}</a></div>
</div></section>
<section class="section" aria-labelledby="g-t"><div class="wrap stack-lg">
<h2 id="g-t" class="h-md split-title">{q("Ritratti", "Portraits")}</h2>
{gallery("ritratti", [
  ("pizzo", q("Donna con lunghi capelli mossi e abito di pizzo nero, mano tra i capelli, in bianco e nero", "Woman with long wavy hair in a black lace dress, hand in her hair, black and white")),
  ("primo-piano", q("Primo piano in bianco e nero di una donna con orecchini chiari e sguardo intenso", "Black and white close-up of a woman with pale earrings and an intense gaze")),
  ("chignon", q("Donna con chignon e cardigan nero, mano alla tempia, su fondo chiaro", "Woman with a bun and black cardigan, hand at her temple, on a light background")),
  ("abito-nero", q("Donna in abito nero, mano tra i capelli, davanti a una parete a pannelli bianchi", "Woman in a black dress, hand in her hair, in front of a white panelled wall")),
  ("porta-legno", q("Donna con capelli lunghi e maglia a costine davanti a una vecchia porta di legno", "Woman with long hair and a ribbed top in front of an old wooden door")),
  ("sorriso-abito", q("Ragazza sorridente con orecchini importanti; sullo sfondo una figura di spalle in controluce", "Smiling young woman with statement earrings; a backlit figure seen from behind in the background")),
  ("uomo-bn", q("Uomo calvo con giacca, occhi chiusi e due dita sulla fronte, in bianco e nero", "Bald man in a jacket, eyes closed and two fingers on his forehead, black and white")),
  ("occhiali-prova", q("Ragazzo con berretto che guarda attraverso gli occhiali di prova dell\'ottico", "Young man in a beanie looking through an optician\'s trial frame")),
], L)}
</div></section>'''
    faq_html, items = faq_block(L, ['eta', 'brutto', 'trucco', 'vestiti', 'dove', 'consegna_prezzo', 'pagamento', 'ritorno', 'stampa'], white=True)
    body += faq_html + contact_section(L, 'ritratto', 'prenota')
    desc = q('Un ritratto che ti somiglia: 2 ore in studio a Parma, outfit a scelta, truccatrice su richiesta, 2 foto postprodotte. € 350 IVA inclusa.',
             'A portrait that looks like you: 2 hours in our Parma studio, outfits of your choice, make-up artist on request, 2 retouched photos. € 350 VAT included.')
    ld = [crumbs_ld(L, trail), faq_ld(items), service_ld(name, desc, L, 'ritratto', 350, True)]
    write(R('ritratto', L), page(L, 'ritratto', q('Ritratto fotografico personale a Parma | JAM Photo', 'Personal portrait photographer in Parma | JAM Photo'), desc, body, ld, has_lightbox=True))

def team_page(L):
    it = L == 'it'
    q = lambda a, b: a if it else b
    name = q('Headshot aziendali', 'Corporate headshots')
    trail = [(name, 'team')]
    body = service_hero(L, trail,
        q('Headshot aziendali a Parma', 'Corporate headshots in Parma, Italy'),
        q('Tutto il team,<br>una sola immagine.', 'The whole team,<br>one single look.'),
        q('Foto coerenti per tutte le persone dell\'azienda: stessa luce, stesso sfondo, stessa qualità. Pronte per il sito, LinkedIn, le presentazioni e i materiali stampati.', 'Consistent photos for everyone in the company: same light, same background, same quality. Ready for your website, LinkedIn, presentations and printed materials.'),
        'hs-occhiali', q('Headshot a colori di un uomo con occhiali, giacca blu e camicia a righe su fondo grigio', 'Colour headshot of a man with glasses, blue jacket and striped shirt on a grey background'),
        f'<div class="btn-row" data-seq><a class="btn" href="#prenota">{q("Chiedi un preventivo", "Get a quote")}</a></div>')
    body += f'''<section class="section section--white" aria-labelledby="how-t"><div class="wrap split split--top">
<div class="stack"><h2 id="how-t" class="h-md split-title">{q("In studio o da voi", "In our studio or at yours")}</h2>
<p class="lead">{q("Potete venire nel nostro studio a Parma, oppure veniamo noi nella vostra sede con tutta l\'attrezzatura: luci, fondale e computer per vedere subito gli scatti.", "You can come to our studio in Parma, or we come to your offices with all the equipment: lights, backdrop and a computer to review shots on the spot.")}</p>
<p class="muted">{q("In sede ci basta una stanza dedicata con almeno 4 × 4 m liberi. Il costo varia in base al numero di persone e alla location; per i gruppi aziendali applichiamo tariffe dedicate.", "On site all we need is a dedicated room with at least 4 × 4 m of free space. The price depends on the number of people and the location; corporate groups get dedicated rates.")}</p></div>
<ul class="ticks" data-reveal>
<li>{q("Stessa luce e stesso sfondo per tutte le persone, anche in giorni diversi", "Same light and background for everyone, even on different days")}</li>
<li>{q("Briefing iniziale per scegliere lo stile più adatto all\'azienda", "Initial briefing to choose the style that suits your company")}</li>
<li>{q("Ogni persona viene guidata nella posa: niente foto rigide", "Everyone is guided through the pose: no stiff photos")}</li>
<li>{q("Scatti visibili subito sul computer", "Shots visible immediately on the computer")}</li>
<li>{q("Gallery riservata per scegliere con calma", "Private gallery to choose at your own pace")}</li>
</ul>
</div></section>
<section class="section" aria-labelledby="g-t"><div class="wrap stack-lg">
<h2 id="g-t" class="h-md split-title">{q("Headshot professionali", "Professional headshots")}</h2>
{gallery("team", [
  ("hs-occhiali", q("Uomo con occhiali, giacca blu e camicia a righe su fondo grigio", "Man with glasses, blue jacket and striped shirt on a grey background")),
  ("hs-blazer", q("Donna sorridente con blazer nero e foulard a righe", "Smiling woman in a black blazer and striped scarf")),
  ("hs-camicia-nera", q("Donna sorridente con camicia nera e braccia incrociate", "Smiling woman in a black shirt with folded arms")),
  ("hs-camicia-blu", q("Giovane uomo sorridente con camicia blu", "Smiling young man in a blue shirt")),
  ("hs-verde", q("Donna bionda con blusa verde petrolio", "Blonde woman in a teal blouse")),
  ("hs-tshirt", q("Ragazzo con t-shirt nera su fondo grigio scuro", "Young man in a black t-shirt on a dark grey background")),
], L)}
</div></section>'''
    faq_html, items = faq_block(L, ['gruppi', 'dove', 'vestiti', 'trucco', 'consegna'], white=True)
    body += faq_html + contact_section(L, 'team', 'prenota')
    desc = q('Foto coerenti per tutto il team: stessa luce e stesso sfondo, in studio a Parma o nella vostra sede. Preventivo in base al numero di persone.',
             'Consistent photos for the whole team: same light and background, in our Parma studio or at your offices. Quote based on the number of people.')
    ld = [crumbs_ld(L, trail), faq_ld(items), service_ld(name, desc, L, 'team')]
    write(R('team', L), page(L, 'team', q('Headshot aziendali per team a Parma | JAM Photo', 'Corporate team headshots in Parma, Italy | JAM Photo'), desc, body, ld, has_lightbox=True))

def studio_page(L):
    it = L == 'it'
    q = lambda a, b: a if it else b
    name = q('Noleggio studio', 'Studio rental')
    trail = [(name, 'studio')]
    body = service_hero(L, trail,
        q('Noleggio studio fotografico a Parma', 'Photo studio rental in Parma, Italy'),
        q('130 m²<br>di luce.', '130 m²<br>of light.'),
        q('JAM Studio: sala di posa open space con 5,25 m di altezza sottotrave e limbo bianco lucido di 3,5 × 3,5 m. Per fotografi, videomaker e produzioni.', 'JAM Studio: open-space shooting room with a 5.25 m ceiling and a 3.5 × 3.5 m glossy white cyclorama. For photographers, videomakers and productions.'),
        'studio-sala', q('Lo studio JAM: sala bianca a doppia altezza con grandi finestre, divano in pelle, limbo bianco, ombrello da studio e scala verso il soppalco', 'The JAM studio: double-height white room with large windows, leather sofa, white cyclorama, studio umbrella and stairs to the mezzanine'),
        f'<div class="btn-row" data-seq><a class="btn" href="#prenota">{q("Verifica la disponibilità", "Check availability")}</a></div>', wide=True)
    specs_h = [q('Caratteristica', 'Feature'), q('Dettaglio', 'Detail')]
    specs = [
        (q('Superficie', 'Floor area'), q('Open space di 130 m²', '130 m² open space')),
        (q('Altezza', 'Ceiling height'), q('5,25 m sottotrave', '5.25 m under the beams')),
        (q('Limbo', 'Cyclorama'), q('Bianco lucido, 3,5 × 3,5 m', 'Glossy white, 3.5 × 3.5 m')),
        (q('Fondali', 'Backdrops'), q('3 m di larghezza, vari colori', '3 m wide, several colours')),
        (q('Luci', 'Lighting'), q('Flash con trigger, diffusori e ombrelli', 'Flash units with trigger, diffusers and umbrellas')),
        (q('Potenza elettrica', 'Electrical power'), q('4,5 kW disponibili, consumo incluso', '4.5 kW available, consumption included')),
        (q('Servizi', 'Facilities'), q('Camerino, bagno con doccia, zona caffè, proiettore, impianto stereo', 'Dressing room, bathroom with shower, coffee area, projector, sound system')),
        (q('Arredi', 'Props'), q('Sgabelli e scatole in legno', 'Stools and wooden boxes')),
        (q('Accesso', 'Access'), q('Ingresso diretto da Strada Martinella 76/1, tramite scale; parcheggio libero', 'Direct entrance from Strada Martinella 76/1, by stairs; free parking')),
        (q('Su richiesta', 'On request'), q('Catering (anche colazione), truccatrice, parrucchiere', 'Catering (including breakfast), make-up artist, hairdresser')),
    ]
    rows = ''.join(f'<tr><th scope="row">{a}</th><td data-label="{specs_h[1]}">{b}</td></tr>' for a, b in specs)
    body += f'''<section class="section section--white" aria-labelledby="pr-t"><div class="wrap split split--top">
<div class="stack"><h2 id="pr-t" class="h-md split-title">{q("Prezzi del noleggio", "Rental prices")}</h2>
<dl class="prices" data-reveal>
<div><dt>{q("Giornata (8 ore)", "Full day (8 hours)")}</dt><dd>€ 350 + {q("IVA", "VAT")}</dd></div>
<div><dt>{q("Mezza giornata (4 ore)", "Half day (4 hours)")}</dt><dd>€ 250 + {q("IVA", "VAT")}</dd></div>
</dl>
<p class="muted">{q("Inclusi nell\'affitto: fondali, flash, diffusori, camerino, consumo elettrico e accesso alla zona caffè.", "Included in the rental: backdrops, flash units, diffusers, dressing room, electricity and access to the coffee area.")}</p>
<div class="btn-row"><a class="btn" href="#prenota">{q("Verifica la disponibilità", "Check availability")}</a></div></div>
<div class="table-wrap" data-reveal><table class="compare"><caption class="visually-hidden">{q("Caratteristiche dello studio", "Studio features")}</caption><thead><tr><th scope="col">{specs_h[0]}</th><th scope="col">{specs_h[1]}</th></tr></thead><tbody>{rows}</tbody></table></div>
</div></section>
<section class="section" aria-labelledby="g-t"><div class="wrap stack-lg">
<h2 id="g-t" class="h-md split-title">{q("Lo studio", "The studio")}</h2>
{gallery("studio", [
  ("studio-sala", q("Sala a doppia altezza con grandi finestre, divano in pelle, limbo bianco e scala verso il soppalco", "Double-height room with large windows, leather sofa, white cyclorama and stairs to the mezzanine")),
  ("studio-scala", q("Limbo bianco visto di lato con la scala a chiocciola e la parete dell\'attrezzatura", "White cyclorama seen from the side with the spiral staircase and the equipment wall")),
  ("studio-open", q("L\'open space con finestre alte, soppalco e ombrelli da studio", "The open space with tall windows, mezzanine and studio umbrellas")),
  ("studio-stender", q("Stender con grucce e cappelli davanti al limbo; sullo sfondo divano e carrello degli accessori", "Clothes rail with hangers and hats in front of the cyclorama; sofa and accessories trolley in the background")),
  ("studio-pallet", q("Pavimento lucido e pallet bianco su ruote in primo piano, ombrello da studio sulla destra", "Glossy floor and white pallet on wheels in the foreground, studio umbrella on the right")),
], L)}
</div></section>'''
    faq_html, items = faq_block(L, ['studio_incluso', 'studio_accesso', 'studio_extra'], white=True)
    body += faq_html + contact_section(L, 'studio', 'prenota')
    desc = q('Sala di posa a Parma: 130 m², altezza 5,25 m, limbo bianco 3,5 × 3,5 m, flash e fondali inclusi. € 350 + IVA al giorno, € 250 + IVA mezza giornata.',
             'Photo studio for rent in Parma, Italy: 130 m², 5.25 m ceiling, 3.5 × 3.5 m white cyclorama, flash and backdrops included. € 350 + VAT per day, € 250 + VAT half day.')
    ld = [crumbs_ld(L, trail), faq_ld(items), service_ld(name, desc, L, 'studio', 350, False, q('giornata di 8 ore', '8-hour day'))]
    write(R('studio', L), page(L, 'studio', q('Noleggio studio fotografico a Parma – 130 m² | JAM Photo', 'Photo studio rental in Parma, Italy – 130 m² | JAM Photo'), desc, body, ld, has_lightbox=True))

def portfolio_page(L):
    it = L == 'it'
    q = lambda a, b: a if it else b
    trail = [('Portfolio', 'portfolio')]
    body = f'''<section class="section"><div class="wrap stack-lg">
{crumbs_html(L, trail)}
<h1 class="page-title"><span class="eyebrow">{q("Fotografo a Parma · ritratti, fashion, headshot", "Photographer in Parma, Italy · portraits, fashion, headshots")}</span><span class="h-xl">Portfolio</span></h1>
<p class="lead">I like white spaces. I like black spaces.</p>
<nav class="btn-row" aria-label="{q("Sezioni del portfolio", "Portfolio sections")}"><a class="btn btn--ghost" href="#ritratti">{q("Ritratti", "Portraits")}</a><a class="btn btn--ghost" href="#fashion">Fashion &amp; creative</a><a class="btn btn--ghost" href="#headshot">Headshot</a><a class="btn btn--ghost" href="{R("lizard", L)}">Lizard</a></nav>
</div></section>
<section class="section section--white" id="ritratti" aria-labelledby="r-t"><div class="wrap stack-lg">
<h2 id="r-t" class="h-md split-title">{q("Ritratti", "Portraits")}</h2>
{gallery("ritratti", [
  ("pizzo", q("Donna con lunghi capelli mossi e abito di pizzo nero, mano tra i capelli", "Woman with long wavy hair in a black lace dress, hand in her hair")),
  ("primo-piano", q("Primo piano di una donna con orecchini chiari e sguardo intenso", "Close-up of a woman with pale earrings and an intense gaze")),
  ("chignon", q("Donna con chignon e cardigan nero, mano alla tempia", "Woman with a bun and black cardigan, hand at her temple")),
  ("abito-nero", q("Donna in abito nero davanti a una parete a pannelli bianchi", "Woman in a black dress in front of a white panelled wall")),
  ("porta-legno", q("Donna con capelli lunghi davanti a una vecchia porta di legno", "Woman with long hair in front of an old wooden door")),
  ("sorriso-abito", q("Ragazza sorridente con orecchini importanti e figura in controluce sullo sfondo", "Smiling young woman with statement earrings and a backlit figure behind")),
  ("uomo-bn", q("Uomo calvo con giacca, occhi chiusi e due dita sulla fronte", "Bald man in a jacket, eyes closed, two fingers on his forehead")),
  ("occhiali-prova", q("Ragazzo con berretto che guarda attraverso gli occhiali di prova dell\'ottico", "Young man in a beanie looking through an optician\'s trial frame")),
], L)}
</div></section>
<section class="section" id="fashion" aria-labelledby="f-t"><div class="wrap stack-lg">
<h2 id="f-t" class="h-md split-title">Fashion &amp; creative</h2>
{gallery("fashion", [
  ("armatura", q("Modella con abito-armatura traforato e mani sui fianchi davanti a una parete scura", "Model in a cut-out armour dress, hands on hips, against a dark wall")),
  ("silhouette-beer", q("Silhouette nera di una donna in affondo con il braccio teso, con la scritta give me a beer", "Black silhouette of a woman lunging with an outstretched arm, with the words give me a beer")),
  ("silhouette-doppia", q("Due silhouette speculari di una donna con le mani alzate che si toccano", "Two mirrored silhouettes of a woman with raised hands touching")),
  ("silhouette-scritta", q("Silhouette nera di una donna in piedi con le mani dietro la testa e una scritta bianca sul corpo", "Black silhouette of a standing woman with hands behind her head and white handwriting on her body")),
  ("carrello", q("Ragazza con occhiali bianchi seduta in un carrello della spesa sotto un ponte, effetto movimento", "Young woman in white sunglasses sitting in a shopping trolley under a bridge, motion effect")),
  ("danza", q("Ballerina in salto a spaccata sopra un gruppo di ballerine sedute sul palco, sotto i riflettori", "Dancer in a split leap above a group of dancers sitting on stage, under the spotlights")),
  ("calcio", q("Ragazzo con maglia da calcio gialla che urla tra gli spruzzi d\'acqua su fondo nero", "Young man in a yellow football shirt shouting amid water splashes on a black background")),
], L)}
</div></section>
<section class="section section--white" id="headshot" aria-labelledby="h-t"><div class="wrap stack-lg">
<h2 id="h-t" class="h-md split-title">Headshot</h2>
{gallery("headshot", [
  ("hs-occhiali", q("Uomo con occhiali, giacca blu e camicia a righe", "Man with glasses, blue jacket and striped shirt")),
  ("hs-verde", q("Donna bionda con blusa verde petrolio", "Blonde woman in a teal blouse")),
  ("hs-blazer", q("Donna sorridente con blazer nero e foulard a righe", "Smiling woman in a black blazer and striped scarf")),
  ("hs-ramata", q("Ragazza con lunghi capelli ramati e lentiggini", "Young woman with long auburn hair and freckles")),
  ("hs-camicia-blu", q("Giovane uomo sorridente con camicia blu", "Smiling young man in a blue shirt")),
  ("hs-coda", q("Ragazza sorridente con coda di cavallo e blusa bianca traforata", "Smiling young woman with a ponytail and white eyelet blouse")),
  ("hs-tshirt", q("Ragazzo con t-shirt nera su fondo grigio scuro", "Young man in a black t-shirt on a dark grey background")),
  ("hs-camicia-nera", q("Donna sorridente con camicia nera e braccia incrociate", "Smiling woman in a black shirt with folded arms")),
], L)}
</div></section>
<section class="section section--dark on-dark"><div class="wrap split">
<div class="stack"><h2 class="h-lg split-title">{q("Vuoi un ritratto così?", "Want a portrait like these?")}</h2>
<div class="btn-row"><a class="btn btn--light" href="{R("home", L)}#contatti">{q("Prenota una sessione", "Book a session")}</a><a class="btn btn--light" href="{R("lizard", L)}">{q("Guarda Lizard", "See Lizard")}</a></div></div>
</div></section>'''
    desc = q('Ritratti, fashion e headshot di JAM Photo, fotografo a Parma: una selezione di lavori in studio e in esterni.',
             'Portraits, fashion and headshots by JAM Photo, photographer in Parma, Italy: a selection of studio and location work.')
    write(R('portfolio', L), page(L, 'portfolio', q('Portfolio – ritratti, fashion e headshot | JAM Photo', 'Portfolio – portraits, fashion, headshots | JAM Photo'), desc, body, [crumbs_ld(L, trail)], has_lightbox=True))

def lizard_page(L):
    it = L == 'it'
    q = lambda a, b: a if it else b
    trail = [('Lizard', 'lizard')]
    items = []
    lz = IMG['_lizard']
    for n, m in enumerate(lz, 1):
        k = m['key']
        alt = q(f'Ritratto Lizard n. {n}: primo piano in bianco e nero ad alto contrasto su fondo nero', f'Lizard portrait no. {n}: high-contrast black and white close-up on a black background')
        big = f'/assets/img/lizard/{k}-{m["sizes"][-1]}.webp'
        items.append(f'<a href="{big}" data-full="{big}">{img(k, alt, "(max-width: 700px) 50vw, 25vw", sub=m)}</a>')
    body = f'''<section class="section"><div class="wrap stack-lg">
{crumbs_html(L, trail)}
<h1 class="page-title"><span class="eyebrow">{q("Ritratti in bianco e nero · Parma", "Black and white portraits · Parma, Italy")}</span><span class="h-xl">Lizard</span></h1>
<p class="lead">{q("Volti ravvicinati, bianco e nero ad alto contrasto, fondo nero. Nessun filtro tra te e l\'obiettivo: solo luce, pelle e sguardo.", "Close-up faces, high-contrast black and white, black background. Nothing between you and the lens: just light, skin and gaze.")}</p>
<div class="btn-row"><a class="btn" href="{R("home", L)}#contatti">{q("Voglio un ritratto Lizard", "I want a Lizard portrait")}</a></div>
</div></section>
<section class="section section--dark on-dark" aria-label="{q("Galleria Lizard", "Lizard gallery")}"><div class="wrap">
<div class="gallery gallery--lizard" data-gallery="lizard">{"".join(items)}</div>
</div></section>'''
    desc = q(f'Lizard: {len(lz)} ritratti in bianco e nero ad alto contrasto su fondo nero, scattati da JAM Photo nello studio di Parma.',
             f'Lizard: {len(lz)} high-contrast black and white portraits on a black background, shot by JAM Photo in Parma, Italy.')
    write(R('lizard', L), page(L, 'lizard', q('Lizard – ritratti in bianco e nero | JAM Photo', 'Lizard – black and white portraits | JAM Photo'), desc, body, [crumbs_ld(L, trail)], has_lightbox=True))

# ================================================================== testi legali
def legal(L, key, title, html_body, desc):
    trail = [(title, key)]
    body = f'''<section class="section"><div class="wrap stack-lg">
{crumbs_html(L, trail)}
<h1 class="h-lg">{title}</h1>
<div class="prose">{html_body}</div>
</div></section>'''
    write(R(key, L), page(L, key, f'{title} | JAM Photo', desc, body, [crumbs_ld(L, trail)]))

def legal_pages():
    for L in ('it', 'en'):
        src = open(os.path.join(SRC, f'privacy-{L}.html')).read()
        legal(L, 'privacy', 'Privacy policy' if L == 'it' else 'Privacy policy', src,
              'Informativa sul trattamento dei dati personali del sito jamphoto.it.' if L == 'it' else 'Information on the processing of personal data on jamphoto.it.')
        src = open(os.path.join(SRC, f'cookie-{L}.html')).read()
        legal(L, 'cookie', 'Cookie policy', src,
              'Cookie policy del sito jamphoto.it: il sito non usa cookie né strumenti di tracciamento.' if L == 'it' else 'Cookie policy of jamphoto.it: the site uses no cookies or tracking tools.')

def thanks():
    for L in ('it', 'en'):
        it = L == 'it'
        q = lambda a, b: a if it else b
        body = f'''<section class="section"><div class="wrap split">
<div class="stack-lg">
<h1 class="h-xl">{q("Grazie!", "Thank you!")}</h1>
<p class="lead">{q("Abbiamo ricevuto la tua richiesta. Ti rispondiamo il prima possibile con le date disponibili.", "We've received your request. We'll get back to you as soon as possible with available dates.")}</p>
<p class="muted">{q("Se hai fretta chiamaci al", "In a hurry? Call us on")} <a href="tel:{PHONE_TEL}">{PHONE_DISPLAY}</a>.</p>
<div class="btn-row"><a class="btn" href="{R("home", L)}">{q("Torna alla home", "Back to home")}</a><a class="btn btn--ghost" href="{R("portfolio", L)}">Portfolio</a></div>
</div>
<div class="frame"><div class="ph r-45">{img("sorriso-abito", q("Ragazza sorridente in bianco e nero", "Smiling young woman, black and white"), "(max-width: 900px) 100vw, 46vw", eager=True)}</div></div>
</div></section>'''
        write(R('grazie', L), page(L, 'grazie', q('Richiesta inviata | JAM Photo', 'Request sent | JAM Photo'), q('Grazie per averci scritto.', 'Thanks for getting in touch.'), body, noindex=True))

def not_found():
    body = f'''<section class="section"><div class="wrap split">
<div class="stack-lg">
<h1 class="h-xl">404</h1>
<p class="lead">Questa pagina non esiste, o non esiste più.<br><span lang="en">This page doesn't exist, or no longer does.</span></p>
<div class="btn-row"><a class="btn" href="/">Home</a><a class="btn btn--ghost" href="/en/" lang="en">English</a><a class="btn btn--ghost" href="/portfolio/">Portfolio</a></div>
</div>
<div class="frame"><div class="ph r-45">{img("uomo-bn", "Uomo con gli occhi chiusi e due dita sulla fronte, in bianco e nero", "(max-width: 900px) 100vw, 46vw", eager=True)}</div></div>
</div></section>'''
    html_ = page('it', 'home', 'Pagina non trovata | JAM Photo', 'La pagina richiesta non esiste.', body, noindex=True)
    html_ = html_.replace(f'<link rel="canonical" href="{SITE}/">\n', '')
    with open(os.path.join(PUB, '404.html'), 'w') as fh:
        fh.write(html_)

# ================================================================== sitemap, robots, llms
def sitemap():
    pages = ['home', 'headshot', 'ritratto', 'team', 'studio', 'portfolio', 'lizard', 'privacy', 'cookie']
    prio = {'home': '1.0', 'headshot': '0.9', 'ritratto': '0.9', 'team': '0.8', 'studio': '0.8', 'portfolio': '0.7', 'lizard': '0.6', 'privacy': '0.2', 'cookie': '0.2'}
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for p in pages:
        for L in ('it', 'en'):
            out.append(f'<url><loc>{SITE}{R(p, L)}</loc><lastmod>{TODAY}</lastmod><priority>{prio[p]}</priority>'
                       f'<xhtml:link rel="alternate" hreflang="it" href="{SITE}{R(p, "it")}"/>'
                       f'<xhtml:link rel="alternate" hreflang="en" href="{SITE}{R(p, "en")}"/>'
                       f'<xhtml:link rel="alternate" hreflang="x-default" href="{SITE}{R(p, "it")}"/></url>')
    out.append('</urlset>')
    open(os.path.join(PUB, 'sitemap.xml'), 'w').write('\n'.join(out) + '\n')
    open(os.path.join(PUB, 'robots.txt'), 'w').write(f'User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n')

def llms():
    txt = f'''# JAM Photo

> Fotografo ritrattista a Parma (Italia). Headshot per LinkedIn, ritratti personali, headshot per team aziendali e noleggio di uno studio fotografico di 130 m². Portrait photographer in Parma, Italy.

- Fotografo: Paolo
- Indirizzo dello studio: {ADDRESS} (ingresso diretto, accesso tramite scale, parcheggio libero)
- Telefono: {PHONE_DISPLAY} (+39 0521 252824)
- Email: {EMAIL}
- Ragione sociale: Servizi Informatici S.r.l., P. IVA 01721620340
- Lingue del sito: italiano, inglese
- Prenotazione: modulo sul sito, telefono o email; acconto del 50% alla prenotazione (bonifico, PayPal o contanti)

## Servizi e prezzi

- [Headshot LinkedIn]({SITE}/headshot/): € 199 IVA inclusa. 60 minuti in studio, 2 foto postprodotte, gallery riservata.
- [Ritratto personale]({SITE}/ritratto/): € 350 IVA inclusa. 120 minuti in studio, outfit a scelta, 2 foto postprodotte, truccatrice su richiesta.
- [Headshot aziendali per team]({SITE}/team-aziendali/): su preventivo, in base al numero di persone e alla location. In studio o in sede (serve una stanza con almeno 4 × 4 m liberi).
- [Noleggio studio]({SITE}/studio/): € 350 + IVA giornata (8 ore), € 250 + IVA mezza giornata (4 ore). 130 m², altezza 5,25 m, limbo bianco lucido 3,5 × 3,5 m, fondali 3 m, flash con trigger, camerino e bagno con doccia, 4,5 kW.
- Ritocco professionale extra: € 80 per foto.

## Come funziona una sessione

Briefing iniziale; scatti con flash e riflettori collegati al computer; 50–100 scatti per look; entro 24 ore 10–20 foto selezionate in una cartella web protetta da password. Disdetta gratuita con almeno 48 ore di preavviso. Sconto del 50% per chi torna per altri scatti. Stampa non inclusa (ordinabile tramite fornitori).

## Pagine

- [Home]({SITE}/) · [English]({SITE}/en/)
- [Portfolio]({SITE}/portfolio/)
- [Lizard – ritratti in bianco e nero]({SITE}/lizard/)
- [Privacy]({SITE}/privacy/) · [Cookie]({SITE}/cookie/) (il sito non usa cookie)
'''
    open(os.path.join(PUB, 'llms.txt'), 'w').write(txt)

if __name__ == '__main__':
    for L in ('it', 'en'):
        home(L); headshot_page(L); ritratto_page(L); team_page(L); studio_page(L); portfolio_page(L); lizard_page(L)
    legal_pages(); thanks(); not_found(); sitemap(); llms()
    print('ok', CSS_V, JS_V)
