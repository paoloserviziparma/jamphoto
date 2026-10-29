# jamphoto.it

Sito di **JAM Photo**, fotografo ritrattista a Parma. Statico (HTML, CSS, JS), nessun framework, nessuna build su Netlify: si pubblica la cartella `public/`.

## Struttura

```
public/                 ← quello che va online
  index.html            home IT          en/index.html            home EN
  headshot/             Headshot LinkedIn en/headshot/
  ritratto/             Ritratto personale en/portrait/
  team-aziendali/       Headshot per team  en/corporate-headshots/
  studio/               Noleggio studio    en/studio-rental/
  portfolio/            Ritratti, Fashion & creative, Headshot   en/portfolio/
  lizard/               Galleria Lizard (139 foto)               en/lizard/
  privacy/ cookie/      Testi legali        en/privacy/ en/cookies/
  grazie/               Dopo l'invio del modulo (noindex)        en/thank-you/
  404.html
  sitemap.xml robots.txt llms.txt favicon.svg
  assets/css/site.css   stile
  assets/js/site.js     menu, intestazione a scomparsa, parallax, animazioni, galleria, selettore
  assets/fonts/         Bebas Neue e Manrope in locale (licenza OFL)
  assets/img/           immagini WebP in più larghezze; lizard/ per la galleria Lizard
_src/                   ← strumenti, NON vanno online
  build.py              genera tutte le pagine HTML (testi IT/EN qui dentro)
  images.py             prepara le immagini (WebP, duotono leggero, nomi neutri)
  privacy-*.html cookie-*.html   testi legali
  check.js              prova il sito in un browser headless
netlify.toml            redirect dai vecchi indirizzi Wix, sicurezza, cache
```

## Modificare il sito

1. Cambia i testi in `_src/build.py` (o i testi legali in `_src/*.html`).
2. `python3 -I _src/build.py` rigenera le pagine e aggiorna il numero di versione di CSS e JS (`?v=…`).
3. Controllo: `cd public && python3 -m http.server 8123` e in un altro terminale `node _src/check.js 8123`.
4. Commit e push: ogni push pubblica il sito (e consuma crediti Netlify), quindi raggruppa le modifiche.

Nuove foto: aggiungile al `CATALOG` in `_src/images.py` e lancia `python3 -I _src/images.py nome-chiave`.

## Modulo contatti

Netlify Forms, modulo `contatti` (stesso nome e stessi campi in tutte le pagine e lingue):
`nome`, `email`, `telefono`, `sessione` (headshot, ritratto, team, studio, altro), `persone`, `messaggio`, `privacy`, più il campo nascosto `lingua` (it/en). Antispam con campo esca `bot-field`.
Dopo l'invio si va su `/grazie/` o `/en/thank-you/`. Le notifiche email si impostano nel pannello Netlify → Forms → Notifications.

## Statistiche, cookie e privacy

Nessun cookie e nessuno script di tracciamento, quindi nessun banner. Le statistiche si leggono con **Netlify Analytics** (dai registri del server), da attivare nel pannello del sito. I testi di privacy e cookie partono da quelli del sito precedente: vanno fatti verificare da un consulente.

## Video

Il sito precedente non aveva video. Per aggiungerne uno: miniatura locale e caricamento solo al clic (YouTube tramite `youtube-nocookie.com`, Vimeo con `dnt=1`, oppure mp4 in `assets/`).

## Foto

Tutte le foto sono di JAM Photo. I nomi dei file non contengono i nomi delle persone ritratte.
Da tenere presente: alcune foto della galleria Lizard mostrano il logo di un salone (Carlo Mora) e ritraggono minori; la foto "calcio" mostra marchi di terzi (BVB, Puma, Evonik); la foto "danza" ritrae minori. Serve il consenso delle persone ritratte (dei genitori per i minori).
