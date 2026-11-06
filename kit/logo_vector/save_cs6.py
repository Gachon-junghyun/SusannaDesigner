"""일러스트 .ai/.svg 를 열어 «CS6 호환(ILLUSTRATOR16)» .ai 로 저장. 내가 연 문서만 닫는다.
usage: python lock.py illu -- python save_cs6.py <입력.ai|.svg> <출력_CS6.ai>"""
import sys, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import win32com.client as w32
src, dst = map(os.path.abspath, sys.argv[1:3])
try: app = w32.GetActiveObject("Illustrator.Application")
except Exception: raise SystemExit("일러스트가 안 떠 있다 — Start-Process 로 먼저 띄우고 창 제목을 확인해라(COM 이 띄우면 창 없이 멈춘다)")
js = r'''
var d = app.open(new File("%s"));
try {
  // 글자는 전부 윤곽선으로(CS6 에 그 글꼴이 없어도 안 깨지게)
  for (var i = d.textFrames.length - 1; i >= 0; i--) { d.textFrames[i].createOutline(); }
  var o = new IllustratorSaveOptions();
  o.compatibility = Compatibility.%s;   // 16 = CS6 (기본) · 17 = CC (--cc)
  o.pdfCompatible = true; o.embedLinkedFiles = true; o.compressed = true;
  d.saveAs(new File("%s"), o);
  "ok paths=" + d.pathItems.length + " compound=" + d.compoundPathItems.length;
} finally { d.close(SaveOptions.DONOTSAVECHANGES); }
''' % (src.replace("\\", "/"), "ILLUSTRATOR17" if "--cc" in sys.argv else "ILLUSTRATOR16", dst.replace("\\", "/"))
print(app.DoJavaScript(js.replace("app.open", "app.open")))
