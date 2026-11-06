# .ai 의 그룹·패스에 이름을 붙이고 층 이름을 정해 같은 자리에 저장 — 내가 연 문서만 닫는다
import sys, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import win32com.client as w32
app = w32.GetActiveObject('Illustrator.Application')
p = os.path.abspath(sys.argv[1]).replace(chr(92), '/')
js = r'''
var d = app.open(new File("%s"));
try {
  d.layers[0].name = "고객B_한지반전";
  var L = d.layers[0];
  function g(n) { for (var i = 0; i < L.groupItems.length; i++) if (L.groupItems[i].name == n) return L.groupItems[i]; return null; }
  var h = g("hanji"); h.name = "한지(크림)"; h.pathItems[0].name = "한지 바탕";
  var f = g("frame"); f.name = "틀"; f.pathItems[0].name = "위 틀"; f.pathItems[1].name = "아래 틀";
  var r = g("roof"); r.name = "지붕";
  var t = r.groupItems[0]; t.name = "기와 9장";
  for (var i = 0; i < t.pathItems.length; i++) t.pathItems[i].name = "기와 " + (t.pathItems.length - i);
  r.pathItems[0].name = "처마+서까래";
  var c = g("cauldron"); c.name = "가마솥"; c.pathItems[0].name = "가마솥";
  var l = g("letters"); l.name = "글자 고객B"; l.compoundPathItems[0].name = "고객B";
  d.save();
  "ok";
} finally { d.close(SaveOptions.DONOTSAVECHANGES); }
''' % p
print(app.DoJavaScript(js))
