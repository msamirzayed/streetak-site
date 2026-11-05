"""Fix the held ball in the loading key art (fingers sank into the ball in the Unreal renders).

For each court: take the scene's light off the old ball (its white panels, spots filled in, blurred),
paint the Blender ball's panels (ALBEDO renders) under that light, a little higher and bigger so the
ball sits under the hand, then put the hand back on top (the player mask from rembg, above the ball only).
Neon and the pyramids balance the ball on the thigh: same ball swap, no hand.

usage: python3 fix_balls.py SRC_DIR OUT_DIR ALBEDO_DIR
"""
import sys

import cv2
import numpy as np
from rembg import new_session, remove
from PIL import Image

src, out, alb = sys.argv[1:4]
# x, y, r of the old ball (Hough, checked by eye); hand = held from above
B = {
    'dubai': (1222, 738, 85, True), 'riyadh': (395, 708, 86, True), 'sayeda': (1600, 760, 89, True),
    'space': (1585, 705, 85, True), 'turf': (1559, 760, 89, True),
    'neon': (1223, 545, 111, False), 'sand': (1501, 629, 111, False),
}
sess = new_session('isnet-general-use')

for i, (k, (x, y, r, hand)) in enumerate(B.items()):
    im = cv2.imread(f'{src}/load_{k}.jpg').astype(np.float32) / 255
    H, W = im.shape[:2]
    fg = np.array(remove(Image.open(f'{src}/load_{k}.jpg'), session=sess, only_mask=True)).astype(np.float32) / 255

    # 1. the scene's light on the old ball: white panels kept, dark spots filled, smoothed
    pad = int(r * 1.6)
    x0, y0 = x - pad, y - pad
    crop = (im[y0:y0 + 2 * pad, x0:x0 + 2 * pad] * 255).astype(np.uint8)
    yy, xx = np.mgrid[0:2 * pad, 0:2 * pad]
    inside = (xx - pad) ** 2 + (yy - pad) ** 2 <= (r - 2) ** 2
    lum = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY).astype(np.float32)
    thr = np.percentile(lum[inside], 55)
    dark = (inside & (lum < thr * 0.82)).astype(np.uint8) * 255
    dark = cv2.dilate(dark, np.ones((5, 5), np.uint8))
    outside = (~inside).astype(np.uint8) * 255
    light = cv2.inpaint(crop, cv2.bitwise_or(dark, outside), 9, cv2.INPAINT_TELEA).astype(np.float32) / 255
    light = cv2.GaussianBlur(light, (0, 0), r * 0.06)

    # 2. the new ball: a bit higher and bigger when held, so the fingers rest on it
    d = int(round(r * 0.17)) if hand else 0
    R = r + d
    nx, ny = x, y - d
    a = Image.open(f'{alb}/alb_{i % 7}.png').convert('RGBA')
    a = a.crop(a.getbbox()).resize((2 * R, 2 * R), Image.LANCZOS)
    a = np.array(a).astype(np.float32) / 255
    alb_rgb, alb_a = a[..., 2::-1], a[..., 3:4]
    # the light map, mapped from the old circle onto the new one
    lmap = cv2.resize(light[pad - r:pad + r, pad - r:pad + r], (2 * R, 2 * R), interpolation=cv2.INTER_CUBIC)
    white = np.percentile(cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)[inside], 92) / 255
    ball = np.clip(alb_rgb / max(alb_rgb.max(), 1e-3) * lmap / max(white, 0.2) * 0.98, 0, 1)
    # a soft rim so its edge sits in the frame like the rest (renders are a little soft)
    alb_a = cv2.GaussianBlur(alb_a[..., 0], (0, 0), 0.8)[..., None]

    res = im.copy()
    # the old ball out first (painted over by the bigger new one; this only matters at the seam)
    old = np.zeros((H, W), np.uint8)
    cv2.circle(old, (x, y), r + 8, 255, -1)
    res = cv2.inpaint((res * 255).astype(np.uint8), old, 7, cv2.INPAINT_TELEA).astype(np.float32) / 255
    ys, xs = ny - R, nx - R
    reg = res[ys:ys + 2 * R, xs:xs + 2 * R]
    res[ys:ys + 2 * R, xs:xs + 2 * R] = reg * (1 - alb_a) + ball * alb_a

    if hand:
        # 3. the hand back on top: the player's pixels outside the old ball, in the ball's upper cap
        cap = np.zeros((H, W), np.float32)
        cv2.circle(cap, (nx, ny), R + 2, 1.0, -1)
        cv2.circle(cap, (x, y), r + 5, 0.0, -1)
        cap[int(y - 0.25 * r):, :] = 0
        cap[:, :int(x - 0.8 * r)] = 0
        cap[:, int(x + 0.8 * r):] = 0
        m = np.clip(fg * cap, 0, 1)
        m = (m > 0.5).astype(np.float32)
        m = cv2.GaussianBlur(m, (0, 0), 0.9)[..., None]
        res = res * (1 - m) + im * m
        # contact shadow under the fingertips, on the ball only
        sh = np.zeros((H, W), np.float32)
        tips = (fg > 0.5).astype(np.uint8)
        ring = np.zeros((H, W), np.uint8)
        cv2.circle(ring, (x, y), r + 7, 1, 5)
        sh = cv2.GaussianBlur((tips & ring).astype(np.float32), (0, 0), r * 0.08)
        ballm = np.zeros((H, W), np.float32)
        ballm[ys:ys + 2 * R, xs:xs + 2 * R] = alb_a[..., 0]
        sh = np.clip(sh * 2.2, 0, 0.55) * ballm * (1 - m[..., 0])
        res = res * (1 - sh[..., None])

    cv2.imwrite(f'{out}/load_{k}.jpg', np.clip(res * 255, 0, 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 95])
    print('fixed', k, flush=True)
