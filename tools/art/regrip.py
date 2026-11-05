"""Put the re-rendered grip (Unreal, ballholdG/GM) into the finished loading key art.

The finished picture is the old render (difference matte: a black and a white card) scaled 0.68 onto a photo and
graded. The new render has the same camera, body and light; only the hand and the ball differ. So: find what
changed (alpha and colour), learn the grade from the old render to the finished picture around it, paint the
background where the old ball was, and lay the new hand and ball in.

usage: python3 regrip.py OUT_DIR
"""
import sys

import cv2
import numpy as np

S = '/mnt/user-data/uploads/zkick/unreal/shots/'
ORIG = '/home/claude/orig/'
JOBS = {  # court: (old pass, new pass, tx, ty) at scale 0.68 (align3.py)
    'sayeda': ('p5', 'q3', 51.92, -179.08), 'space': ('p5', 'q3', 52.16, -279.72),
    'riyadh': ('p9', 'q3', -686.16, -279.72), 'dubai': ('p5', 'q3', 159.92, -226.0),
    'turf': ('p9', 'q3', -3.44, -164.8),
}
SC = 0.68
import json
PH = json.load(open('/home/claude/grip/photoalign.json'))


def load(f):
    return cv2.imread(S + f, cv2.IMREAD_UNCHANGED)[..., :3].astype(np.float32) / 255


def matte(K, W):
    raw = 1 - (W - K).mean(2)
    # the white card isn't quite white (its gain): the empty background reads ~0.13; that is alpha 0
    a0 = float(np.median(np.concatenate([raw[:40, :40].ravel(), raw[:40, -40:].ravel(), raw[-40:, :40].ravel(), raw[-40:, -40:].ravel()])))
    return np.clip((raw - a0) / max(1e-3, 1 - a0), 0, 1)


def to_final(img, tx, ty):
    small = cv2.resize(img, None, fx=SC, fy=SC, interpolation=cv2.INTER_AREA)
    M = np.float32([[1, 0, tx], [0, 1, ty]])
    return cv2.warpAffine(small, M, (1920, 1080), flags=cv2.INTER_LINEAR, borderValue=0)


def feats(c):
    r, g, b = c[:, 0], c[:, 1], c[:, 2]
    return np.stack([r, g, b, np.ones_like(r), r * r, g * g, b * b, r * g, r * b, g * b], 1)


def run(court, out):
    old, new, tx, ty = JOBS[court]
    Ko, Wo, Kn, Wn = (load(f'{p}_{court}_{k}.png') for p in (old, new) for k in ('k', 'w'))
    ao, an = matte(Ko, Wo), matte(Kn, Wn)
    Ko, Kn = to_final(Ko, tx, ty), to_final(Kn, tx, ty)
    ao, an = to_final(ao, tx, ty), to_final(an, tx, ty)
    F = cv2.imread(ORIG + f'load_{court}.jpg').astype(np.float32) / 255

    # what changed: the geometry (alpha), and the colour where the ball now passes in front of the body
    da = np.abs(an - ao)
    core = (da > 0.1).astype(np.uint8)
    core = cv2.morphologyEx(core, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    ys, xs = np.nonzero(core)
    x0, x1, y0, y1 = max(0, xs.min() - 30), min(1919, xs.max() + 30), max(0, ys.min() - 30), min(1079, ys.max() + 30)
    box = np.zeros((1080, 1920), np.uint8); box[y0:y1, x0:x1] = 1
    dk = np.abs(Kn - Ko).max(2)
    R = (((dk > 0.05) | (da > 0.02)) & (box > 0)).astype(np.uint8)
    R = cv2.morphologyEx(R, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    R = cv2.dilate(R, np.ones((7, 7), np.uint8))
    Rf = cv2.GaussianBlur(R.astype(np.float32), (0, 0), 2.0)

    # the grade: old render -> finished picture, learned on solid player pixels around the change
    win = np.zeros_like(R); win[max(0, y0 - 160):y1 + 160, max(0, x0 - 160):x1 + 160] = 1
    m = (ao > 0.995) & (win > 0) & (R == 0)
    X, Y = feats(Ko[m]), F[m]
    coef, *_ = np.linalg.lstsq(X, Y, rcond=None)
    err = np.abs(X @ coef - Y).mean()

    # the background where the old hand and ball were: painted from around (the photos behind are soft)
    hole = ((ao > 0.02) & (R > 0)).astype(np.uint8) * 255
    hole = cv2.dilate(hole, np.ones((5, 5), np.uint8))
    # the background where the old hand and ball were: the court's own photo (photoalign.py), aligned and graded
    # everything the old hand and ball covered that the new ones don't, with the old edge's glow
    gone = ((ao > 0.01) & (an < 0.5) & (box > 0)).astype(np.uint8)
    gone = cv2.morphologyEx(gone, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8)) * 255
    hole = cv2.dilate(cv2.bitwise_or(hole, gone), np.ones((15, 15), np.uint8))
    R = np.maximum(R, (hole > 0).astype(np.uint8))
    Rf = cv2.GaussianBlur(R.astype(np.float32), (0, 0), 2.0)
    flip, s, sig, px, py = PH[court][1:]
    B = cv2.imread(f'/home/claude/grip/photos/{court}.jpg').astype(np.float32) / 255
    if flip:
        B = B[:, ::-1].copy()
    B = cv2.resize(B, None, fx=s, fy=s, interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC)
    if sig:
        B = cv2.GaussianBlur(B, (0, 0), sig)
    x, y = int(round(px)), int(round(py))
    Pf = B[y:y + 1080, x:x + 1920]
    Pf = cv2.copyMakeBorder(Pf, 0, 1080 - Pf.shape[0], 0, 1920 - Pf.shape[1], cv2.BORDER_REFLECT)
    near = np.zeros_like(R); near[max(0, y0 - 220):y1 + 220, max(0, x0 - 220):x1 + 220] = 1
    mb = (cv2.erode((ao < 0.01).astype(np.uint8), np.ones((15, 15), np.uint8)) > 0) & (near > 0)
    cb, *_ = np.linalg.lstsq(feats(Pf[mb]), F[mb], rcond=None)
    fill = np.clip((feats(Pf.reshape(-1, 3)) @ cb).reshape(Pf.shape), 0, 1)
    hm = cv2.GaussianBlur(hole.astype(np.float32) / 255, (0, 0), 2.5)[..., None]
    bg = F * (1 - hm) + fill * hm
    print(court, 'photo grade err', round(float(np.abs(fill[mb] - F[mb]).mean()), 4))
    # the new hand and ball, graded, over that background
    a = an[..., None]
    col = Kn / np.maximum(a, 0.05)
    g = np.clip((feats(col.reshape(-1, 3)) @ coef).reshape(col.shape), 0, 1)
    comp = g * a + bg * (1 - a)
    res = F * (1 - Rf[..., None]) + comp * Rf[..., None]
    cv2.imwrite(f'{out}/load_{court}.jpg', np.clip(res * 255, 0, 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 95])
    print(court, 'changed box', (x0, y0, x1, y1), 'grade err', round(float(err), 4), flush=True)
    return (x0, y0, x1, y1)


if __name__ == '__main__':
    out = sys.argv[1]
    for c in JOBS:
        run(c, out)
