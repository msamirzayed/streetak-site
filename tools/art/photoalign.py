import cv2, numpy as np, json
from bdalign import bg_mask
P='/home/claude/grip/photos/'
def fit(court):
    F=cv2.imread(f'/home/claude/orig/load_{court}.jpg').astype(np.float32)/255
    m,ao=bg_mask(court)
    q=0.25; sm=lambda im: cv2.resize(im,None,fx=q,fy=q,interpolation=cv2.INTER_AREA)
    T=sm(cv2.cvtColor(F,cv2.COLOR_BGR2GRAY)); M=sm(m.astype(np.float32))
    B=cv2.imread(P+court+'.jpg').astype(np.float32)/255
    best=None
    s0=max(1080/B.shape[0],1920/B.shape[1])
    for flip in (False,True):
        Bf=B[:, ::-1] if flip else B
        Bg=cv2.cvtColor(Bf,cv2.COLOR_BGR2GRAY)
        for s in np.arange(s0, s0*2.6, 0.03*s0):
            Bs=cv2.resize(Bg,None,fx=s*q,fy=s*q,interpolation=cv2.INTER_AREA)
            if Bs.shape[0]<T.shape[0] or Bs.shape[1]<T.shape[1]: continue
            for sig in (0,1,2):
                Bb=cv2.GaussianBlur(Bs,(0,0),sig) if sig else Bs
                r=cv2.matchTemplate(Bb,T,cv2.TM_CCOEFF_NORMED,mask=M)
                r=np.nan_to_num(r,nan=-1,posinf=-1,neginf=-1); _,mv,_,ml=cv2.minMaxLoc(r)
                if best is None or mv>best[0]: best=(float(mv),flip,float(s),sig/q,ml[0]/q,ml[1]/q)
    return best
if __name__=='__main__':
    out={}
    for c in ['sayeda','space','riyadh','dubai','turf']:
        b=fit(c); out[c]=b; print(c,[round(x,3) if isinstance(x,float) else x for x in b],flush=True)
    json.dump(out,open('photoalign.json','w'))
