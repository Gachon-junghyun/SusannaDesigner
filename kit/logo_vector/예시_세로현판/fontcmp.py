import io,sys
from PIL import Image, ImageDraw, ImageFont
src=Image.open(r"../../../mark/sil/S3_세로현판.png").convert("RGB")
crop=src.crop((600,520,1210,2050)).resize((300,750))
fonts=["NanumBrushScript-Regular.ttf","EastSeaDokdo-Regular.ttf","Dokdo-Regular.ttf","KirangHaerang-Regular.ttf","YeonSung-Regular.ttf"]
W=300*(len(fonts)+1); out=Image.new("RGB",(W,800),"white")
out.paste(crop,(0,0))
for i,f in enumerate(fonts):
    x0=300*(i+1); d=ImageDraw.Draw(out)
    d.rectangle((x0+20,0,x0+280,750),fill=(168,35,42))
    ft=ImageFont.truetype("fonts/"+f,230)
    for j,ch in enumerate("고객B"):
        d.text((x0+150,130+j*240),ch,font=ft,fill=(243,233,210),anchor="mm")
    d.text((x0+10,760),f.split("-")[0],fill="black")
out.save("font_compare.png")
