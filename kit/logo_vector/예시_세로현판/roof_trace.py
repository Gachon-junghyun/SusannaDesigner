import numpy as np, cv2, json
from scipy import ndimage as ndi
from tl import trace
G=np.load("roof_G.npy"); Gb=np.load("roof_Gb.npy")
r=json.load(open("roof_reg.json")); s,tx,ty=r["s"],r["tx"],r["ty"]
k=1; BL=0.8
# 검정 몸통(연속값, 가장 큰 덩이만)
lbm=ndi.binary_dilation(Gb,iterations=3)
A=G*lbm
f=cv2.GaussianBlur(cv2.resize(A,None,fx=k,fy=k,interpolation=cv2.INTER_CUBIC),(0,0),BL*k)
black=f>0.5
sil=ndi.binary_fill_holes(black)
holes=sil&~black
# 기와 틈: 작은 구멍 티끌은 버리고, 검정 밑으로 1.5px(원본) 깔리게 키운다
lab,n=ndi.label(holes); sizes=ndi.sum(holes,lab,range(1,n+1))
tiles=np.isin(lab,1+np.where(sizes>400*k*k)[0])
print("tiles",int((sizes>400*k*k).sum()),"dropped holes",int((sizes<=400*k*k).sum()))
tiles_g=tiles
# 검정에서 작은 구멍은 메운다
black2=sil   # 지붕 검정 = 구멍 없는 실루엣, 기와 크림은 그 위에 얹는다
mp=lambda x,y:(x/k*s+tx, y/k*s+ty)
db,nb,cb=trace(black2,mp,optol=0.4,alphamax=1.0,turd=int(80*k*k))
dt,nt,ct=trace(tiles_g,mp,optol=0.4,alphamax=1.0,turd=int(80*k*k))
print("black",nb,cb,"tiles",nt,ct)
json.dump(dict(black=db,tiles=dt),open("roof_path.json","w"))
