# .ai 를 열어 구조만 읽고 닫는다(내가 연 문서만)
import sys, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import win32com.client as w32
app = w32.GetActiveObject("Illustrator.Application")
p=os.path.abspath(sys.argv[1]).replace("\\","/")
js=r'''
var d=app.open(new File("%s")); var out=[];
try{
 out.push("mode="+d.documentColorSpace+" ab="+d.artboards.length+" rect="+d.artboards[0].artboardRect.join(","));
 out.push("layers="+d.layers.length+" groups="+d.groupItems.length+" paths="+d.pathItems.length+" compound="+d.compoundPathItems.length+" text="+d.textFrames.length+" raster="+d.rasterItems.length+" placed="+d.placedItems.length+" grad="+d.gradients.length);
 function walk(c,ind){ for(var i=0;i<c.pageItems.length;i++){var it=c.pageItems[i]; if(it.parent!==c) continue;
   var s=ind+it.typename+" '"+it.name+"'";
   if(it.typename=="PathItem"){s+=" pts="+it.pathPoints.length+" fill="+(it.filled?it.fillColor.typename:"none")+" clip="+it.clipping+" stroked="+it.stroked;}
   if(it.typename=="CompoundPathItem"){var n=0; for(var j=0;j<it.pathItems.length;j++) n+=it.pathItems[j].pathPoints.length; var f=it.pathItems[0]; s+=" sub="+it.pathItems.length+" pts="+n+" fill="+(f.filled?f.fillColor.typename:"none")+" stroked="+f.stroked;}
   out.push(s); if(it.typename=="GroupItem") walk(it,ind+"  ");}}
 for(var L=0;L<d.layers.length;L++){out.push("LAYER "+d.layers[L].name); walk(d.layers[L],"  ");}
} finally { d.close(SaveOptions.DONOTSAVECHANGES); }
out.join("\n");
''' % p
print(app.DoJavaScript(js))
