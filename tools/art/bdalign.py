import cv2, numpy as np
from regrip import load, to_final, JOBS, matte
KA='/mnt/user-data/uploads/zkick/unreal/ka/'
CANDS={'sayeda':['bd4_sayeda'],'space':['bd4_space'],'riyadh':['bd5_riyadh','bd4_riyadh'],'dubai':['bd5_dubai','bd4_dubai'],'turf':['bd4_turf']}
def bg_mask(court):
    old,new,tx,ty=JOBS[court]
    Ko,Wo=load(f'{old}_{court}_k.png'),load(f'{old}_{court}_w.png')
    ao=to_final(matte(Ko,Wo),tx,ty)
    return cv2.erode(((ao<0.01)).astype(np.uint8),np.ones((25,25),np.uint8)), ao
def fit(court):
    F=cv2.imread(f'/home/claude/orig/load_{court}.jpg').astype(np.float32)/255
    m,ao=bg_mask(court)
    Fg=cv2.cvtColor(F,cv2.COLOR_BGR2GRAY)
    small=lambda im,f=0.25: cv2.resize(im,None,fx=f,fy=f,interpolation=cv2.INTER_AREA)
    T=small(Fg); M=small(m.astype(np.float32))
    best=None
    for name in CANDS[court]:
        B=cv2.imread(KA+name+'.jpg').astype(np.float32)/255; Bg=cv2.cvtColor(B,cv2.COLOR_BGR2GRAY)
        for s in np.arange(1920/B.shape[1]*0.95, 1920/B.shape[1]*1.9, 0.02):
            Bs=small(cv2.resize(Bg,None,fx=s,fy=s,interpolation=cv2.INTER_AREA))
            if Bs.shape[0]<T.shape[0] or Bs.shape[1]<T.shape[1]: continue
            for sig in (0,2,4):
                Bb=cv2.GaussianBlur(Bs,(0,0),sig) if sig else Bs
                r=cv2.matchTemplate(Bb,T,cv2.TM_CCOEFF_NORMED,mask=M)
                r=np.nan_to_num(r,nan=-1,posinf=-1,neginf=-1); _,mv,_,ml=cv2.minMaxLoc(r)
                if best is None or mv>best[0]: best=(mv,name,s,sig*4,ml[0]*4,ml[1]*4)
    return best
if __name__=='__main__':
    for c in CANDS: print(c,fit(c),flush=True)
