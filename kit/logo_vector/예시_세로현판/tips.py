# 끝점별 굵기 단면 — 원본 px 단위로 보고
import numpy as np, cv2, json
from PIL import Image
from skimage.morphology import skeletonize
def walk(sk, y, x, n):
    path=[(y,x)]; prev=None; cur=(y,x)
    for _ in range(n):
        cy,cx=cur; nb=[(cy+dy,cx+dx) for dy in (-1,0,1) for dx in (-1,0,1) if (dy or dx) and 0<=cy+dy<sk.shape[0] and 0<=cx+dx<sk.shape[1] and sk[cy+dy,cx+dx] and (cy+dy,cx+dx) not in path[-3:]]
        if len(nb)!=1 and _>0: 
            if not nb: break
            if len(nb)>1: break
        if not nb: break
        cur=nb[0]; path.append(cur)
    return path
def analyze(mask, px_per_orig):
    m=(mask>0).astype(np.uint8)
    dt=cv2.distanceTransform(m,cv2.DIST_L2,5)
    sk=skeletonize(m>0)
    main=np.median(dt[sk])*2
    k=cv2.filter2D(sk.astype(np.uint8),-1,np.ones((3,3),np.uint8))
    ends=np.argwhere(sk&(k==2))
    out=[]
    for y,x in ends:
        p=walk(sk,y,x,int(main*2))
        w=[dt[q]*2 for q in p]
        out.append(dict(y=int(y),x=int(x),len=len(p),w=[round(float(v)/px_per_orig,1) for v in w[::max(1,int(px_per_orig*4))]][:12]))
    return main/px_per_orig, out
if __name__=="__main__":
    g=np.array(Image.open('rd_letters/gemini/letters.png').convert('L')).astype(np.float32)
    A=(g<128)
    reg=json.load(open("reg.json"))
    for nm,r in reg.items():
        g0,g1=r["g"]; sub=np.zeros_like(A); sub[g0:g1]=A[g0:g1]
        ppo=1/r["s"]
        main,ends=analyze(sub,ppo)
        print(nm,"main width (orig px)",round(main,1),"1/4 =",round(main/4,1))
        for e in ends: print("  end at orig (%.0f,%.0f)"%(e['x']*r['s']+r['tx'],e['y']*r['s']+r['ty']),"walk",e['len'],"w every 4px:",e['w'])
