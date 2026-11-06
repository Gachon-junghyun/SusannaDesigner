# .ai 를 열어 구조(층·그룹·패스 수·칠 종류·겹친 같은 패스)를 보고 «내가 연 문서만» 닫는다
import sys, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import win32com.client as w32
app = w32.GetActiveObject('Illustrator.Application')
p = os.path.abspath(sys.argv[1]).replace(chr(92), '/')
js = r'''
var d = app.open(new File("%s"));
var out = [];
try {
  out.push("layers=" + d.layers.length + " artboards=" + d.artboards.length + " ab=" + d.artboards[0].artboardRect.join(","));
  out.push("paths=" + d.pathItems.length + " compound=" + d.compoundPathItems.length + " groups=" + d.groupItems.length + " text=" + d.textFrames.length + " raster=" + d.rasterItems.length + " placed=" + d.placedItems.length + " gradients=" + d.gradients.length);
  function walk(c, ind) {
    for (var i = 0; i < c.pageItems.length; i++) {
      var it = c.pageItems[i];
      if (it.parent != c) continue;
      var s = ind + it.typename + " '" + it.name + "'";
      if (it.typename == "GroupItem") { s += " clipped=" + it.clipped; out.push(s); walk(it, ind + "  "); continue; }
      if (it.typename == "PathItem") { s += " pts=" + it.pathPoints.length + " fill=" + (it.filled ? it.fillColor.typename : "none") + " stroke=" + it.stroked + " clip=" + it.clipping; }
      if (it.typename == "CompoundPathItem") { s += " sub=" + it.pathItems.length + " fill=" + it.pathItems[0].fillColor.typename; }
      out.push(s);
    }
  }
  for (var L = 0; L < d.layers.length; L++) { out.push("LAYER " + d.layers[L].name); walk(d.layers[L], "  "); }
  // 칠 색
  var cols = {};
  for (var i = 0; i < d.pathItems.length; i++) { var f = d.pathItems[i].fillColor; if (f.typename == "RGBColor") cols[Math.round(f.red)+","+Math.round(f.green)+","+Math.round(f.blue)] = 1; else cols[f.typename]=1; }
  var k = []; for (var c in cols) k.push(c); out.push("colors: " + k.join(" | "));
} finally { d.close(SaveOptions.DONOTSAVECHANGES); }
out.join("\n");
''' % p
print(app.DoJavaScript(js))
