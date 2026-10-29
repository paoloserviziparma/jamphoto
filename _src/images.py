"""Prepara le immagini del sito in public/assets/img.

Uso:  python3 -I _src/images.py
Legge gli originali (allegati e zip Lizard) e scrive WebP in più larghezze,
con un duotono leggero (30%) sui toni del sito: nero caldo #141210 -> carta #F3F0EB.
"""
import glob, json, os, sys
from PIL import Image, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'public', 'assets', 'img')
A = '/mnt/user-data/attachments/15d784a8-d061-5c35-bf31-d89465830a1c'
U = '/mnt/user-data/uploads'
LIZARD_DIR = '/home/claude/jamphoto/_in/zip'   # zip "album-47138875-downloads.zip" estratto

SHADOW = (0x14, 0x12, 0x10)
LIGHT = (0xF3, 0xF0, 0xEB)
MIX = 0.30

# chiave: (file sorgente, ritaglio (x0,y0,x1,y1) o None, larghezze)
CATALOG = {
    'hero':        (f'{A}/0e4f8b25-image.jpg', (760, 0, 1784, 1280), (640, 1024)),
    'og':          (f'{A}/0e4f8b25-image.jpg', (0, 136, 1920, 1144), (1200,)),
    'pizzo':       (f'{A}/0e4f8b25-image.jpg', None, (640, 1280, 1920)),
    'chignon':     (f'{A}/a7922033-image.jpg', None, (640, 1280, 1920)),
    'chignon-v':   (f'{A}/a7922033-image.jpg', (820, 0, 1673, 1280), (640, 853)),
    'primo-piano': (f'{A}/fdc9644f-image.jpg', None, (640, 1280, 2000)),
    'abito-nero':  (f'{A}/01fdc354-image.jpg', None, (640, 1280, 1920)),
    'porta-legno': (f'{A}/aa926630-image.jpg', None, (640, 1280, 1920)),
    'armatura':    (f'{A}/774ce574-image.jpg', (0, 0, 1640, 1280), (640, 1280, 1640)),
    'occhiali-prova': (f'{A}/32521910-image.jpg', None, (640, 1280, 1920)),
    'sorriso-abito':  (f'{A}/800c62b0-image.jpg', None, (640, 1280, 1920)),
    'silhouette-doppia': (f'{A}/7a81b4a7-image.jpg', None, (640, 1280, 2000)),
    'silhouette-scritta': (f'{A}/a0746905-image.jpg', None, (640, 1340)),
    'silhouette-beer': (f'{U}/_AOL3600-Modifica.tif', None, (640, 1280, 2000)),
    'carrello': (f'{A}/134d1ced-image.jpg', (0, 0, 1070, 1280), (640, 1070)),
    'danza': (f'{A}/81602fab-image.jpg', None, (640, 1280)),
    'calcio': (f'{A}/838d842c-image.jpg', (0, 0, 853, 1110), (640, 853)),
    'uomo-bn':     (f'{A}/fdb4800b-image.jpg', (0, 0, 1650, 1280), (640, 1280, 1650)),
    'hs-camicia-nera': (f'{A}/c5adec64-image.jpg', None, (640, 1024)),
    'hs-ramata':   (f'{A}/b8aa9404-image.jpg', None, (640, 1280, 1920)),
    'hs-coda':     (f'{A}/088855a4-image.jpg', None, (640, 1280, 1920)),
    'hs-camicia-blu': (f'{A}/cb3d7872-image.jpg', None, (640, 1280, 1920)),
    'hs-verde':    (f'{A}/170e8d6d-image.jpg', None, (640, 1280, 1920)),
    'hs-occhiali': (f'{A}/37a114eb-image.jpg', None, (640, 1280, 1920)),
    'hs-tshirt':   (f'{A}/817b0d47-image.jpg', None, (640, 1280, 1920)),
    'hs-blazer':   (f'{A}/f9e3ad52-image.jpg', (0, 0, 2200, 1717), (640, 1280, 2200)),
    'studio-sala':     (f'{A}/ad14ad06-image.jpg', None, (640, 1280, 2000)),
    'studio-limbo':    (f'{A}/6bbd2620-image.jpg', None, (640, 1280, 2000)),
    'studio-limbo-2':  (f'{A}/6aad107b-image.jpg', None, (640, 1280, 2000)),
    'studio-scala':    (f'{A}/ed60974f-image.jpg', None, (640, 1280, 2000)),
    'studio-open':     (f'{A}/7faa55bb-image.jpg', None, (640, 1280, 2000)),
    'studio-pallet':   (f'{A}/7422219f-image.jpg', None, (640, 1280, 2000)),
    'studio-stender':  (f'{A}/a8917e6f-image.jpg', None, (640, 1280, 2000)),
    'paolo':       (f'{U}/_80A0044-2.jpg', (700, 0, 4148, 2765), (640, 1280, 1920)),
    'paolo-bn':    (f'{U}/Jamphoto-640.jpg', (0, 0, 853, 1100), (640, 853)),
}


def duotone(im):
    g = ImageOps.grayscale(im)
    tone = ImageOps.colorize(g, black=SHADOW, white=LIGHT)
    return Image.blend(im.convert('RGB'), tone, MIX)


def export(key, src, box, widths, out_dir=OUT, quality=78):
    im = ImageOps.exif_transpose(Image.open(src)).convert('RGB')
    if box:
        im = im.crop(box)
    im = duotone(im)
    meta = {'w': im.width, 'h': im.height, 'sizes': []}
    for w in widths:
        w = min(w, im.width)
        c = im if w == im.width else im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
        name = f'{key}-{w}.webp'
        c.save(os.path.join(out_dir, name), 'WEBP', quality=quality, method=6)
        meta['sizes'].append(w)
    return meta


def main():
    os.makedirs(OUT, exist_ok=True)
    only = sys.argv[1:]
    mpath = os.path.join(ROOT, '_src', 'images.json')
    if only:
        manifest = json.load(open(mpath))
        for key in only:
            src, box, widths = CATALOG[key]
            manifest[key] = export(key, src, box, widths); print(key, manifest[key])
        json.dump(manifest, open(mpath, 'w'), indent=1)
        return
    manifest = {}
    for key, (src, box, widths) in CATALOG.items():
        manifest[key] = export(key, src, box, widths)
        print(key, manifest[key])
    # Lizard: tutte le foto dello zip, nomi neutri, miniatura + grande
    ldir = os.path.join(OUT, 'lizard')
    os.makedirs(ldir, exist_ok=True)
    files = sorted(glob.glob(os.path.join(LIZARD_DIR, '*.jpg')) + glob.glob(os.path.join(LIZARD_DIR, '*.JPG')))
    lz = []
    for n, f in enumerate(files, 1):
        key = f'lizard-{n:03d}'
        m = export(key, f, None, (600, 1600), out_dir=ldir, quality=76)
        lz.append({'key': key, **m})
    manifest['_lizard'] = lz
    print('lizard', len(lz))
    with open(os.path.join(ROOT, '_src', 'images.json'), 'w') as fh:
        json.dump(manifest, fh, indent=1)


if __name__ == '__main__':
    main()
