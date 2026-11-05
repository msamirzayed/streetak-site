import cv2, numpy as np
from align import load, matte
def gm(im):
    g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY); gx = cv2.Sobel(g, cv2.CV_32F, 1, 0); gy = cv2.Sobel(g, cv2.CV_32F, 0, 1)
    m = np.sqrt(gx*gx+gy*gy); return cv2.GaussianBlur(m/(m.max()+1e-6), (0,0), 1.5)
def find(court, tag, s=0.68):
    K = load(f'{tag}_{court}_k.png'); W = load(f'{tag}_{court}_w.png'); a = matte(K, W)
    F = cv2.imread(f'/home/claude/orig/load_{court}.jpg').astype(np.float32)/255
    ys, xs = np.nonzero(a > .5); x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    Ks = cv2.resize(K, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
    yb = int(min(y1*s, y0*s + 700))
    T = Ks[int(y0*s):yb, int(x0*s):int(x1*s)]
    r = cv2.matchTemplate(gm(F), gm(T), cv2.TM_CCOEFF_NORMED); _, mv, _, ml = cv2.minMaxLoc(r)
    return mv, ml[0]-x0*s, ml[1]-y0*s
for c,t in [('sayeda','p5'),('space','p5'),('riyadh','p9'),('dubai','p5'),('turf','p9')]:
    print(c, [round(float(v),2) for v in find(c,t)])
