# -*- coding: utf-8 -*-
"""폰으로 보낼 PDF: 벡터 도면은 그대로 두고 넣은 그림만 JPEG 로 다시 압축한다.
제안서 원본 PDF(12~37MB)는 텔레그램 전송이 시간 초과났다(10-21) → 원본은 드라이브, 폰에는 이것(2MB 안팎).
"""
import io
import os


def phone_pdf(src, dst=None, max_px=1600, quality=82):
    import fitz
    from PIL import Image
    dst = dst or src[:-4] + '_폰용.pdf'
    d = fitz.open(src); done = set()
    for p in d:
        for im in p.get_images(full=True):
            x = im[0]
            if x in done:
                continue
            done.add(x)
            pix = fitz.Pixmap(d, x)
            if pix.alpha:
                pix = fitz.Pixmap(pix, 0)
            if pix.n > 3:
                pix = fitz.Pixmap(fitz.csRGB, pix)
            pi = Image.frombytes('RGB', (pix.width, pix.height), pix.samples)
            pi.thumbnail((max_px, max_px)); b = io.BytesIO(); pi.save(b, 'JPEG', quality=quality)
            p.replace_image(x, stream=b.getvalue())
    d.save(dst, garbage=4, deflate=True)
    return dict(dst=dst, src_mb=round(os.path.getsize(src) / 1e6, 1), dst_mb=round(os.path.getsize(dst) / 1e6, 1), pages=len(d))
