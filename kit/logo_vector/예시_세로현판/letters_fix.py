# 제미나이 글자 → (음절별) 작업 해상도 이진 마스크 → 손질(가는 끝 자르고 둥글게 · ㅇ 속공간 꼭지 둥글게) → potrace
import numpy as np, cv2, json, sys
from PIL import Image
from scipy import ndimage as ndi
from skimage.morphology import skeletonize
from tl import trace
from tips import walk
g=np.array(Image.open('rd_letters/gemini/letters.png').convert('L')).astype(np.float32)
A=np.clip((200-g)/150,0,1)
reg=json.load(open("reg.json")); k=3; BL=2.5
RATIO=0.27
OPT=float(sys.argv[1]) if len(sys.argv)>1 else 1.0   # 끝 굵기 하한 = 주획의 27%
log=[]; out={}
BRIDGE={'근':[(930,1004,1200,1265)]}
def disk(r): return cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(2*r+1,2*r+1))
for nm,r in reg.items():
    g0,g1=r["g"]; sub=np.zeros_like(A); sub[g0:g1]=A[g0:g1]
    f=cv2.GaussianBlur(cv2.resize(sub,None,fx=k,fy=k,interpolation=cv2.INTER_CUBIC),(0,0),BL*k)
    M=(f>0.5)
    ppo=k/r["s"]   # 작업 px / 원본 px
    m8=M.astype(np.uint8); dt=cv2.distanceTransform(m8,cv2.DIST_L2,5)
    sk=skeletonize(M); main=np.median(dt[sk])*2; T=main*RATIO
    kk=cv2.filter2D(sk.astype(np.uint8),-1,np.ones((3,3),np.uint8))
    ends=np.argwhere(sk&(kk==2))
    for y,x in ends:
        p=walk(sk,y,x,int(main*3))
        w=np.array([dt[q]*2 for q in p])
        d8=int(round(8*ppo))
        if len(w)<=d8 or w[min(d8,len(w)-1)]>=T: continue      # 둥근 끝이면 둔다
        idx=np.where(w>=T)[0]
        if not len(idx): continue
        i=idx[0]; py,px=p[i]
        # 가는 끝 구역(창)만 지름 T 원으로 «열기» — T 보다 가는 꼬리는 사라지고 끝은 반지름 T/2 로 둥글어진다
        W=np.zeros_like(m8)
        for q in p[:i+int(T)]: cv2.circle(W,(int(q[1]),int(q[0])),int(main*0.8),1,-1)
        W=W.astype(bool)
        Op=cv2.morphologyEx(M.astype(np.uint8),cv2.MORPH_OPEN,disk(int(T/2)))
        # 꼬리 빠진 자리의 오목한 홈을 메운다 — 획 방향으로 긴 타원으로 닫아서 옆 획과는 안 붙게
        j=min(i+int(T),len(p)-1); vy,vx=np.array(p[j],float)-np.array(p[0],float); ang=np.degrees(np.arctan2(vy,vx))
        a_=int(main*0.9); b_=max(2,int(main*0.18)); ker=np.zeros((2*a_+1,2*a_+1),np.uint8)
        cv2.ellipse(ker,(a_,a_),(a_,b_),ang,0,360,1,-1)
        Op=cv2.morphologyEx(Op,cv2.MORPH_CLOSE,ker).astype(bool)
        M=(M&~W)|(Op&W)
        lab,n=ndi.label(M)
        if n>1:
            sizes=ndi.sum(M,lab,range(1,n+1)); M=np.isin(lab,1+np.where(sizes>0.002*M.size)[0])
        oy,ox=p[0][0]/k*r["s"]+r["ty"],p[0][1]/k*r["s"]+r["tx"]
        log.append(dict(syl=nm,at=[round(ox),round(oy)],tip_w8=round(float(w[min(d8,len(w)-1)])/ppo,1),cut_len=round(i/ppo,1),cap=round(T/ppo,1),main=round(main/ppo,1)))
    # 손으로 짚은 자리: 근 ㅡ 아랫면 «계단»(꼬리를 빼낸 자리, 원본 x 964~996 에서 6px 뚝 떨어짐).
    #  왼쪽 선(x930)과 오른쪽 끝 덩이(x1004)를 기울기까지 맞춘 3차 에르미트 곡선으로 잇고, 그 위까지 메운다(더하기만).
    for (x0_,x1_,ylo,yhi) in BRIDGE.get(nm,[]):
        def bottom(xo):
            xw=int(round((xo-r["tx"])/r["s"]*k)); y0w=int((ylo-r["ty"])/r["s"]*k); y1w=int((yhi-r["ty"])/r["s"]*k)
            col=np.where(M[y0w:y1w,xw])[0]; return (col.max()+y0w)/k*r["s"]+r["ty"]
        ya,yb=bottom(x0_),bottom(x1_); ma=(bottom(x0_)-bottom(x0_-12))/12; mb=(bottom(x1_+12)-bottom(x1_))/12
        h=x1_-x0_; added=0
        for xw in range(int((x0_-r["tx"])/r["s"]*k),int((x1_-r["tx"])/r["s"]*k)+1):
            xo=xw/k*r["s"]+r["tx"]; t=(xo-x0_)/h
            yt=(2*t**3-3*t**2+1)*ya+(t**3-2*t**2+t)*h*ma+(-2*t**3+3*t**2)*yb+(t**3-t**2)*h*mb
            ytw=int(round((yt-r["ty"])/r["s"]*k)); y0w=int((ylo-r["ty"])/r["s"]*k)
            col=np.where(M[y0w:ytw+1,xw])[0]
            if len(col):
                top=col.min()+y0w; added+=int((~M[top:ytw+1,xw]).sum()); M[top:ytw+1,xw]=True
        log.append(dict(syl=nm,bridge=[x0_,x1_],ends=[round(ya,1),round(yb,1)],px_orig=round(added/ppo/ppo,1)))
    # ㅇ 속공간: 꼭지 둥글게(구멍을 반지름 3px 로 열기)
    sil=ndi.binary_fill_holes(M); holes=sil&~M
    if holes.any():
        rr=int(round(6*ppo)); h2=cv2.morphologyEx(holes.astype(np.uint8),cv2.MORPH_OPEN,disk(rr)).astype(bool)
        M=M|(holes&~h2); log.append(dict(syl=nm,counter_px_filled=int((holes&~h2).sum()/ppo/ppo)))
    # 🔴 작업 해상도(k=3)에서 바로 따면 거의 곧은 테두리의 픽셀 계단이 «잔물결»로 남는다(이 ㅣ 오른쪽, 실측).
    #    원 해상도로 내려 potrace 자신의 계단 처리에 맡기고, 허용치를 원 픽셀 단위로 준다.
    TK=float(sys.argv[2]) if len(sys.argv)>2 else 1.0
    Mf=cv2.resize(M.astype(np.float32),None,fx=TK/k,fy=TK/k,interpolation=cv2.INTER_AREA)
    M2=cv2.GaussianBlur(Mf,(0,0),0.7)>0.5
    s,tx,ty=r["s"],r["tx"],r["ty"]
    d,nseg,nc=trace(M2, lambda x,y:(x/TK*s+tx, y/TK*s+ty), optol=OPT, alphamax=1.0, turd=int(60*TK*TK))
    out[nm]=d; log.append(dict(syl=nm,segments=nseg,contours=nc))
    np.save("Mfix_%d.npy"%list(reg).index(nm),M)
json.dump(out,open("letters_fix_path.json","w"),ensure_ascii=False)
for l in log: print(l)
json.dump(log,open("letters_fix_log.json","w"),ensure_ascii=False,indent=1,default=float)
