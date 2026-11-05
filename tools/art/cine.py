"""Cinematic loops of the court key art for streetak.com: a 2.5D camera move.

Layers: the court (the player painted out), the player (rembg cut-out), dust in depth, a floodlight
sweep, bloom, grade, vignette and grain. The camera eases out and back (1 - cos), and the dust and
light are periodic, so every clip loops without a seam.

usage: python3 cine.py IMG_DIR OUT_DIR [court ...]
"""
import math
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image
from rembg import new_session, remove

src, out = sys.argv[1], sys.argv[2]
courts = sys.argv[3:] or ['sayeda', 'riyadh', 'dubai', 'sand', 'roof', 'street', 'neon', 'space', 'turf']
W, H, FPS, SECS = 1280, 720, 30, 7
N = FPS * SECS
sess = new_session('isnet-general-use')
# where the camera drifts (+1: towards the right of the frame) and the light colour, per court
LOOK = {
    'sayeda': (-1, (255, 214, 160)), 'riyadh': (1, (255, 190, 130)), 'dubai': (-1, (170, 200, 255)),
    'sand': (-1, (255, 210, 150)), 'roof': (-1, (255, 225, 190)), 'street': (-1, (255, 200, 140)),
    'neon': (-1, (255, 140, 220)), 'space': (-1, (190, 170, 255)), 'turf': (-1, (200, 225, 255)),
}


def layers(k):
    pil = Image.open(f'{src}/load_{k}.jpg').convert('RGB')
    img = np.array(pil)[..., ::-1].copy()
    m = np.array(remove(pil, session=sess, only_mask=True))
    m = cv2.GaussianBlur(m, (0, 0), 1.2).astype(np.float32) / 255
    # the court without the player: paint the hole at half size (the backgrounds are soft anyway)
    hole = (cv2.dilate((m > 0.2).astype(np.uint8), np.ones((25, 25), np.uint8)) * 255)
    small = cv2.resize(img, (960, 540), interpolation=cv2.INTER_AREA)
    hs = cv2.resize(hole, (960, 540), interpolation=cv2.INTER_NEAREST)
    bg = cv2.inpaint(small, hs, 15, cv2.INPAINT_TELEA)
    bg = cv2.GaussianBlur(bg, (0, 0), 2.0)
    bg = cv2.resize(bg, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_CUBIC)
    # keep the real pixels where the player wasn't
    keep = cv2.GaussianBlur(1 - hole.astype(np.float32) / 255, (0, 0), 6)[..., None]
    bg = (img * keep + bg * (1 - keep)).astype(np.uint8)
    return img, bg, m


def affine(scale, tx, ty, cx, cy):
    # scale about (cx, cy) of the 1920x1080 source, then fit into W x H
    f = W / 1920
    return np.float32([[scale * f, 0, (cx - scale * cx + tx) * f], [0, scale * f, (cy - scale * cy + ty) * f]])


def dust(seed, n=90):
    r = np.random.default_rng(seed)
    return dict(x=r.uniform(0, W, n), y0=r.uniform(0, H, n), z=r.uniform(0.15, 1.0, n),
                ph=r.uniform(0, 2 * np.pi, n), loops=r.integers(1, 3, n))


def render(k):
    side, light = LOOK[k]
    img, bg, m = layers(k)
    ys, xs = np.nonzero(m > 0.5)
    cx, cy = float(xs.mean()), float(ys.min() + (ys.max() - ys.min()) * 0.35)  # around the player's chest
    D = dust(hash(k) % 1000)
    lc = np.array(light[::-1], np.float32) / 255
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    vig = 1 - 0.55 * (((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H / 2) / (H * 0.75)) ** 2)
    vig = np.clip(vig, 0.35, 1)[..., None]
    grain_rng = np.random.default_rng(7)
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}',
                           '-r', str(FPS), '-i', '-', '-an', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '25',
                           '-pix_fmt', 'yuv420p', '-movflags', '+faststart', f'{out}/{k}.mp4'], stdin=subprocess.PIPE)
    for i in range(N):
        t = i / N
        p = (1 - math.cos(2 * math.pi * t)) / 2           # 0 → 1 → 0
        q = math.sin(2 * math.pi * t)                     # the drift sideways
        A = affine(1.06 + 0.035 * p, side * 18 * q, -6 * p, cx, cy)
        B = affine(1.03 + 0.085 * p, side * 46 * q, -10 * p, cx, cy)
        b = cv2.warpAffine(bg, A, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT).astype(np.float32) / 255
        f = cv2.warpAffine(img, B, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT).astype(np.float32) / 255
        a = cv2.warpAffine(m, B, (W, H), flags=cv2.INTER_LINEAR)[..., None]
        # a little depth: the court a touch softer and darker behind the player
        b = cv2.GaussianBlur(b, (0, 0), 1.2 + 0.8 * p) * 0.9
        fr = b * (1 - a) + f * a
        # floodlight sweep: a soft diagonal band crossing the frame once a loop
        u = (xx * 0.8 + yy * 0.6) / (W * 0.8 + H * 0.6)
        c = (t * 1.6 - 0.3) % 1.6 - 0.3
        band = np.exp(-((u - c) / 0.09) ** 2)[..., None] * 0.16
        fr = 1 - (1 - fr) * (1 - band * lc)
        # dust in depth: near motes big and soft, far ones small; they rise and wrap once or twice a loop
        dl = np.zeros((H, W), np.float32)
        y = (D['y0'] - t * H * D['loops'] * 1.0) % H
        x = D['x'] + 14 * np.sin(2 * np.pi * t * D['loops'] + D['ph']) - side * 40 * q * D['z']
        for xi, yi, zi in zip(x, y, D['z']):
            cv2.circle(dl, (int(xi), int(yi)), max(1, int(zi * 3.2)), float(0.25 + 0.75 * zi), -1, cv2.LINE_AA)
        dl = cv2.GaussianBlur(dl, (0, 0), 1.6)
        fr = fr + dl[..., None] * lc * 0.35
        # bloom on the highlights
        hi = np.clip(fr - 0.8, 0, 1)
        fr = fr + cv2.GaussianBlur(hi, (0, 0), 18) * 0.55
        # grade: lifted blacks into teal, warm highlights, contrast, vignette, grain
        lum = fr.mean(axis=2, keepdims=True)
        fr = fr + (1 - lum) * np.float32([0.035, 0.02, -0.01]) * 0.6 + lum * np.float32([-0.02, 0.0, 0.03]) * 0.5
        fr = np.clip(fr, 0, 1)
        fr = fr * fr * (3 - 2 * fr) * 0.35 + fr * 0.65
        fr = fr * vig
        fr = fr + grain_rng.normal(0, 0.012, (H, W, 1)).astype(np.float32)
        frame = np.clip(fr * 255, 0, 255).astype(np.uint8)
        if i == 0:
            cv2.imwrite(f'{out}/{k}.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 82])
        ff.stdin.write(frame.tobytes())
    ff.stdin.close()
    ff.wait()
    print('clip', k, flush=True)


for k in courts:
    render(k)
