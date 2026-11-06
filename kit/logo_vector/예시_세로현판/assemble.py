import numpy as np, cv2, json, fitz, io, sys
from tl import trace
RED,CREAM,BLACK="#A8232A","#F3E9D2","#000000"
roof=json.load(open("roof_path.json")); L=json.load(open("letters_gem_path.json")); C=json.load(open("caul_path.json"))["d"]
LETTERS=json.load(open(sys.argv[1])) if len(sys.argv)>1 else L
# 1) 지붕 아랫면 → 판 위끝(간격 25px 그대로)
K=4; x0,y0,x1,y1=560,100,1240,700
svg='<svg xmlns="http://www.w3.org/2000/svg" width="1792" height="2400" viewBox="0 0 1792 2400"><path fill="#000" fill-rule="evenodd" d="%s"/></svg>'%roof["black"]
open("_roof_only.svg","w").write(svg)
p=fitz.open("_roof_only.svg")[0]
pix=p.get_pixmap(matrix=fitz.Matrix(K,K),clip=fitz.Rect(x0,y0,x1,y1),alpha=False)
a=np.frombuffer(pix.samples,np.uint8).reshape(pix.height,pix.width,3)[...,0]<128
GAP=25; BL,BR,BB,RC=601,1189,2226,22
Hh=(BB+40-y0)*K; Ww=(x1-x0)*K
mask=np.zeros((Hh,Ww),bool)
for cx in range(int((BL-x0)*K),int((BR-x0)*K)+1):
    col=np.where(a[:,cx])[0]
    top=col.max()/K+y0+GAP
    mask[int(round((top-y0)*K)):int((BB-y0)*K), cx]=True
# 아래 모서리 둥글게
r=RC*K
for (cx,sgn) in [((BL-x0)*K+r,-1),((BR-x0)*K-r,1)]:
    cy=(BB-y0)*K-r
    yy,xx=np.mgrid[int(cy):int((BB-y0)*K)+1, int(cx-r) if sgn<0 else int(cx):int(cx)+1 if sgn<0 else int(cx+r)+1]
    out=((yy-cy)**2+(xx-cx)**2)>r*r
    mask[yy[out],xx[out]]=False
mask=cv2.GaussianBlur(mask.astype(np.float32),(0,0),1.5)>0.5
db,nb,cb=trace(mask,lambda x,y:(x/K+x0,y/K+y0),optol=0.8,alphamax=1.0,turd=100)
print("board",nb,cb)
json.dump(dict(d=db),open("board_clean_path.json","w"))
# 2) 조립
VB=(437,113,919,2153)
P=lambda fill,d,id_: '<path id="%s" fill="%s" fill-rule="evenodd" d="%s"/>'%(id_,fill,d)
body=('<g id="roof">'+P(BLACK,roof["black"],"roof_black")+P(CREAM,roof["tiles"],"roof_tiles")+'</g>'
      '<g id="board">'+P(RED,db,"board_red")+'</g>'
      '<g id="letters">'+''.join(P(CREAM,d,nm_) for nm_,d in zip(["letter_1_sang","letter_2_geun","letter_3_i"],LETTERS.values()))+'</g>'
      '<g id="cauldron">'+P(BLACK,C,"cauldron_black")+'</g>')
s='<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" width="%dpt" height="%dpt" viewBox="%d %d %d %d">%s</svg>'%(VB[2],VB[3],*VB,body)
io.open("assembled.svg","w",encoding="utf-8").write(s)
