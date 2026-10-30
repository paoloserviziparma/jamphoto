"""Trova e rimuove il logo "jam photo" dalle foto Lizard.

Uso:
  python3 -I _src/delogo.py detect   -> scrive _src/logos.json con la posizione del logo in ogni foto
  python3 -I _src/delogo.py clean    -> crea le versioni senza logo in _work/lizard-clean/ (con LaMa se disponibile)
Le foto originali non vengono mai modificate.
"""
import glob, json, os, sys
import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIZARD_DIR = '/home/claude/jamphoto/_in/zip'
OUT = '/home/claude/jamphoto/_work/lizard-clean'
JSON = os.path.join(ROOT, '_src', 'logos.json')

def files():
    return sorted(glob.glob(os.path.join(LIZARD_DIR, '*.jpg')))

def edges(gray):
    g = cv2.GaussianBlur(gray, (3, 3), 0)
    e = cv2.Canny(g, 30, 90)
    return cv2.dilate(e, np.ones((3, 3), np.uint8))

def template_from(n, corner, rel):
    """rel = riquadro (x0,y0,x1,y1) dentro il ritaglio d'angolo di lato 25% del lato corto"""
    im = cv2.imread(files()[n - 1], cv2.IMREAD_GRAYSCALE)
    h, w = im.shape
    s = int(min(h, w) * 0.25)
    ox, oy = (w - s, h - s) if corner == 'br' else (0, 0)
    x0, y0, x1, y1 = rel
    return im[oy + y0:oy + y1, ox + x0:ox + x1]

TEMPLATES = None

def templates():
    global TEMPLATES
    if TEMPLATES is None:
        TEMPLATES = [
            ('chiaro', template_from(4, 'br', (44, 42, 235, 231))),
            ('scuro', template_from(99, 'tl', (88, 90, 263, 265))),
        ]
    return TEMPLATES

def detect_one(path):
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    h, w = img.shape
    short = min(h, w)
    s = int(short * 0.36)
    best = None
    for corner, (ox, oy) in (('br', (w - s, h - s)), ('tl', (0, 0))):
        roi = img[oy:oy + s, ox:ox + s]
        eroi = edges(roi).astype(np.float32)
        for name, t in templates():
            for frac in np.arange(0.07, 0.19, 0.005):
                size = int(short * frac)
                if size >= s - 2:
                    continue
                tt = cv2.resize(t, (size, size), interpolation=cv2.INTER_AREA)
                et = edges(tt).astype(np.float32)
                res = cv2.matchTemplate(eroi, et, cv2.TM_CCOEFF_NORMED)
                _, mx, _, loc = cv2.minMaxLoc(res)
                if best is None or mx > best['score']:
                    best = {'score': float(mx), 'corner': corner, 'tpl': name,
                            'box': [int(ox + loc[0]), int(oy + loc[1]), int(ox + loc[0] + size), int(oy + loc[1] + size)]}
    return best

def detect():
    res = {}
    for i, f in enumerate(files(), 1):
        b = detect_one(f)
        res[f'{i:03d}'] = b
        print(i, round(b['score'], 3), b['corner'], b['tpl'], b['box'])
    json.dump(res, open(JSON, 'w'), indent=1)

def clean():
    data = json.load(open(JSON))
    os.makedirs(OUT, exist_ok=True)
    lama = None
    try:
        import torch
        lama = torch.jit.load('/home/claude/lama/big-lama.pt', map_location='cpu').eval()
        torch.set_num_threads(os.cpu_count() or 4)
    except Exception as ex:
        print('LaMa non disponibile, uso OpenCV:', ex)
    for i, f in enumerate(files(), 1):
        key = f'{i:03d}'
        d = data[key]
        img = cv2.imread(f, cv2.IMREAD_COLOR)
        if not d.get('logo'):
            cv2.imwrite(os.path.join(OUT, f'lizard-{key}.png'), img)
            continue
        x0, y0, x1, y1 = d['box']
        m = int((x1 - x0) * 0.06) + 2
        H, W = img.shape[:2]
        mask = np.zeros((H, W), np.uint8)
        mask[max(0, y0 - m):min(H, y1 + m), max(0, x0 - m):min(W, x1 + m)] = 255
        if lama is not None:
            out = lama_inpaint(lama, img, mask, (x0, y0, x1, y1))
        else:
            out = cv2.inpaint(img, mask, 9, cv2.INPAINT_TELEA)
        cv2.imwrite(os.path.join(OUT, f'lizard-{key}.png'), out)
        print('pulita', key)

def lama_inpaint(model, img, mask, box):
    """LaMa su un ritaglio attorno al logo (più veloce e più fedele), poi incolla."""
    import torch
    H, W = img.shape[:2]
    x0, y0, x1, y1 = box
    side = int(max(x1 - x0, y1 - y0) * 3.2)
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    X0 = max(0, min(W - side, cx - side // 2)); Y0 = max(0, min(H - side, cy - side // 2))
    X1 = min(W, X0 + side); Y1 = min(H, Y0 + side)
    crop = img[Y0:Y1, X0:X1]
    mcrop = mask[Y0:Y1, X0:X1]
    ch, cw = crop.shape[:2]
    # risoluzione nativa fino a 1024 px (multiplo di 8), così la zona ricostruita resta nitida
    S = min(1024, max(256, (max(ch, cw) // 8) * 8))
    ci = cv2.resize(crop, (S, S), interpolation=cv2.INTER_AREA if max(ch, cw) > S else cv2.INTER_CUBIC)
    mi = cv2.resize(mcrop, (S, S), interpolation=cv2.INTER_NEAREST)
    t_img = torch.from_numpy(cv2.cvtColor(ci, cv2.COLOR_BGR2RGB)).permute(2, 0, 1).float().unsqueeze(0) / 255.0
    t_mask = torch.from_numpy((mi > 127).astype(np.float32)).unsqueeze(0).unsqueeze(0)
    with torch.no_grad():
        r = model(t_img, t_mask)[0].permute(1, 2, 0).clamp(0, 1).numpy()
    r = cv2.cvtColor((r * 255).astype(np.uint8), cv2.COLOR_RGB2BGR)
    r = cv2.resize(r, (cw, ch), interpolation=cv2.INTER_CUBIC)
    # incolla solo dentro la maschera, con bordo sfumato
    soft = cv2.GaussianBlur(mcrop.astype(np.float32) / 255.0, (0, 0), 3)[..., None]
    soft = np.clip(soft * 1.6, 0, 1)
    merged = (r.astype(np.float32) * soft + crop.astype(np.float32) * (1 - soft)).astype(np.uint8)
    out = img.copy()
    out[Y0:Y1, X0:X1] = merged
    return out

if __name__ == '__main__':
    {'detect': detect, 'clean': clean}[sys.argv[1]]()
