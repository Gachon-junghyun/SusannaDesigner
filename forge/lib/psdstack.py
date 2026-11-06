"""레이어 PNG 여러 장 → 포토샵 COM 으로 레이어 PSD (+ 미리보기 JPG).

레이어마다 판 크기 그대로의 투명 PNG 를 주면 위치를 포토샵에서 다시 잡을 일이 없다.
포토샵은 먼저 띄워 두고(창 확인), 이 함수는 자기가 만든 문서만 닫는다(일러 교훈과 같음).

    from forge.lib.psdstack import build
    build(w, h, dpi, "이름", [{"file": png, "name": "01 바탕", "opacity": 100, "visible": True, "blend": "normal"}, ...],
          psd="out.psd", jpg="out.jpg")   # 레이어는 아래 → 위 순서
"""
from __future__ import annotations

import json
import os

JSX = r"""
app.displayDialogs = DialogModes.NO;
var P = $.global.__ARGS, out = [];
var pu = app.preferences.rulerUnits; app.preferences.rulerUnits = Units.PIXELS;
var doc = app.documents.add(P.w, P.h, P.dpi, P.docname, NewDocumentMode.RGB, DocumentFill.TRANSPARENT);
try {
    var BM = {normal: BlendMode.NORMAL, screen: BlendMode.SCREEN, multiply: BlendMode.MULTIPLY, overlay: BlendMode.OVERLAY};
    var first = doc.layers[0];
    for (var i = 0; i < P.layers.length; i++) {
        var Q = P.layers[i];
        var d = app.open(new File(Q.file));
        d.activeLayer.duplicate(doc, ElementPlacement.PLACEATBEGINNING);
        d.close(SaveOptions.DONOTSAVECHANGES);
        app.activeDocument = doc;
        var l = doc.layers[0];
        l.name = Q.name; l.blendMode = BM[Q.blend || "normal"]; l.opacity = Q.opacity; l.visible = Q.visible;
    }
    first.remove();
    var so = new PhotoshopSaveOptions(); so.layers = true; so.embedColorProfile = true;
    doc.saveAs(new File(P.psd), so, true, Extension.LOWERCASE);
    if (P.jpg) { var jo = new JPEGSaveOptions(); jo.quality = 10; doc.saveAs(new File(P.jpg), jo, true, Extension.LOWERCASE); }
    out.push("layers=" + doc.layers.length);
} finally {
    doc.close(SaveOptions.DONOTSAVECHANGES);
    app.preferences.rulerUnits = pu;
}
out.join("\n");
"""


def build(w: int, h: int, dpi: int, docname: str, layers: list[dict], psd: str, jpg: str | None = None) -> str:
    import win32com.client
    fwd = lambda p: os.path.abspath(p).replace("\\", "/")
    P = {"w": w, "h": h, "dpi": dpi, "docname": docname, "psd": fwd(psd), "jpg": fwd(jpg) if jpg else None,
         "layers": [{"opacity": 100, "visible": True, "blend": "normal", **L, "file": fwd(L["file"])} for L in layers]}
    app = win32com.client.Dispatch("Photoshop.Application")
    return app.DoJavaScript("$.global.__ARGS = " + json.dumps(P, ensure_ascii=False) + ";\n" + JSX)
