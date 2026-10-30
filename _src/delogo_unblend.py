"""Per i loghi a riquadro semitrasparente su tessuti fantasia: toglie il velo
(stimandone trasparenza e colore dal bordo del riquadro) e ricostruisce con LaMa
solo le lettere. Uso: python3 -I _src/delogo_unblend.py 095 [altre...]"""
import json, os, sys, glob
import cv2, numpy as np, torch
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import delogo

def text_mask(box_w, box_h):
    t = cv2.imread(delogo.files()[3])  # foto 4: riquadro chiaro di riferimento
    h, w = t.shape[:2]; s = int(min(h, w) * 0.25)
    crop = t[h - s + 42:h - s + 231, w - s + 44:w - s + 235]
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    m = ((gray < 95) | (hsv[..., 1] > 60)).astype(np.uint8) * 255
    m[:, :6] = 0; m[:, -6:] = 0; m[:6, :] = 0; m[-6:, :] = 0
    m = cv2.resize(m, (box_w, box_h), interpolation=cv2.INTER_NEAREST)
    return cv2.dilate(m, np.ones((7, 7), np.uint8), iterations=2)

def unblend(img, box):
    x0, y0, x1, y1 = box
    f = img.astype(np.float32)
    k = max(3, (x1 - x0) // 40)
    ins, outs = [], []
    for (ys, xs, yo, xo) in (
        (slice(y0 + 2, y0 + 2 + k), slice(x0 + 10, x1 - 10), slice(y0 - 2 - k, y0 - 2), slice(x0 + 10, x1 - 10)),
        (slice(y1 - 2 - k, y1 - 2), slice(x0 + 10, x1 - 10), slice(y1 + 2, y1 + 2 + k), slice(x0 + 10, x1 - 10)),
        (slice(y0 + 10, y1 - 10), slice(x0 + 2, x0 + 2 + k), slice(y0 + 10, y1 - 10), slice(x0 - 2 - k, x0 - 2)),
        (slice(y0 + 10, y1 - 10), slice(x1 - 2 - k, x1 - 2), slice(y0 + 10, y1 - 10), slice(x1 + 2, x1 + 2 + k))):
        a = f[ys, xs].reshape(-1, 3); b = f[yo, xo].reshape(-1, 3)
        n = min(len(a), len(b)); ins.append(a[:n]); outs.append(b[:n])
    I = np.concatenate(ins).mean(1); O = np.concatenate(outs).mean(1)
    # I = alpha*W + (1-alpha)*O  -> retta I = (1-alpha)*O + alpha*W
    slope, icpt = np.polyfit(O, I, 1)
    alpha = float(np.clip(1 - slope, 0.05, 0.9)); W = float(icpt / alpha)
    region = f[y0:y1, x0:x1]
    rec = np.clip((region - alpha * W) / (1 - alpha), 0, 255)
    out = img.copy(); out[y0:y1, x0:x1] = rec.astype(np.uint8)
    return out, alpha, W

def run(key):
    d = json.load(open(delogo.JSON))[key]
    box = d['box']
    img = cv2.imread(delogo.files()[int(key) - 1])
    out, alpha, W = unblend(img, box)
    x0, y0, x1, y1 = box
    H, Wd = img.shape[:2]
    mask = np.zeros((H, Wd), np.uint8)
    tm = text_mask(x1 - x0, y1 - y0)
    hsv = cv2.cvtColor(img[y0:y1, x0:x1], cv2.COLOR_BGR2HSV)
    sat = (hsv[..., 1] > 30).astype(np.uint8) * 255
    tm = cv2.dilate(cv2.bitwise_or(tm, sat), np.ones((5, 5), np.uint8), iterations=3)
    mask[y0:y1, x0:x1] = tm
    # bordo del riquadro: sottile cornice da ricucire
    e = 4
    border = np.zeros_like(mask); border[y0 - e:y1 + e, x0 - e:x1 + e] = 255; border[y0 + e:y1 - e, x0 + e:x1 - e] = 0
    mask = cv2.bitwise_or(mask, border)
    model = torch.jit.load('/home/claude/lama/big-lama.pt', map_location='cpu').eval()
    res = delogo.lama_inpaint(model, out, mask, box)
    # foto in bianco e nero: niente residui di colore del logo
    g = cv2.cvtColor(res, cv2.COLOR_BGR2GRAY)
    res = cv2.cvtColor(g, cv2.COLOR_GRAY2BGR)
    cv2.imwrite(os.path.join(delogo.OUT, f'lizard-{key}.png'), res)
    print(key, 'alpha', round(alpha, 2), 'W', round(W))

if __name__ == '__main__':
    for k in sys.argv[1:]:
        run(k)
