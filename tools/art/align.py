import cv2, numpy as np, sys
S='/mnt/user-data/uploads/zkick/unreal/shots/'
def load(f): return cv2.imread(S+f, cv2.IMREAD_UNCHANGED)[..., :3].astype(np.float32)/255
def matte(k, w): return np.clip(1 - (w - k).mean(2), 0, 1)
def find(court, tag):
    K = load(f'{tag}_{court}_k.png'); W = load(f'{tag}_{court}_w.png'); a = matte(K, W)
    F = cv2.imread(f'/home/claude/orig/load_{court}.jpg').astype(np.float32)/255
    g = lambda im: cv2.Canny((cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)*255).astype(np.uint8), 40, 110).astype(np.float32)
    ys, xs = np.nonzero(a > .5); x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    best = None
    Fg = cv2.GaussianBlur(g(F), (0, 0), 2)
    for s in np.arange(0.40, 1.01, 0.02):
        Ks = cv2.resize(K, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
        T = Ks[int(y0*s):int(min(y1, y0+(y1-y0)*0.7)*s), int(x0*s):int(x1*s)]   # the upper body (feet may be cut)
        if T.shape[0] >= F.shape[0] or T.shape[1] >= F.shape[1]: continue
        Tg = cv2.GaussianBlur(g(T), (0, 0), 2)
        r = cv2.matchTemplate(Fg, Tg, cv2.TM_CCORR_NORMED); _, mv, _, ml = cv2.minMaxLoc(r)
        if best is None or mv > best[0]: best = (mv, s, ml[0] - x0*s, ml[1] - y0*s)
    return best
if __name__ == '__main__':
    for c, t in [('sayeda','p5'),('dubai','p5'),('space','p5'),('riyadh','p9'),('turf','p9')]:
        print(c, [round(float(v),3) for v in find(c, t)], flush=True)
