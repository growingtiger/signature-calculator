#!/usr/bin/env python3
"""PWA 아이콘 생성기.

앱의 액센트색(딥 페트롤 틸)에 발자국 마크를 얹은 아이콘을 만든다.
아이콘 모양이나 색을 바꾸려면 아래 상수만 수정하고 다시 실행:

    python3 make-icons.py

4배 크기로 그린 뒤 축소해 가장자리를 부드럽게 처리한다.
"""

import pathlib

from PIL import Image, ImageDraw

TEAL = (12, 107, 102)      # --accent (라이트 테마)
MINT = (99, 211, 198)      # 펄스 라인
WHITE = (255, 255, 255)
SS = 4                     # 슈퍼샘플링 배율


def paw(draw, size, cx, cy, scale, fill):
    """(cx, cy)를 중심으로 발바닥 하나를 그린다. scale은 size 대비 비율."""
    w = size * scale

    # 발바닥 패드
    pw, ph = w * 0.44, w * 0.36
    draw.ellipse([cx - pw / 2, cy + w * 0.06 - ph / 2,
                  cx + pw / 2, cy + w * 0.06 + ph / 2], fill=fill)

    # 발가락 4개 — 바깥쪽 두 개는 살짝 기울인다
    toes = [(-0.275, -0.24, -24), (-0.095, -0.35, -8), (0.095, -0.35, 8), (0.275, -0.24, 24)]
    tw, th = w * 0.17, w * 0.225
    for dx, dy, ang in toes:
        pad = int(max(tw, th) * 1.6)
        layer = Image.new("RGBA", (pad, pad), (0, 0, 0, 0))
        d2 = ImageDraw.Draw(layer)
        d2.ellipse([(pad - tw) / 2, (pad - th) / 2, (pad + tw) / 2, (pad + th) / 2], fill=fill)
        layer = layer.rotate(ang, resample=Image.BICUBIC)
        draw._image.alpha_composite(
            layer, (int(cx + w * dx - pad / 2), int(cy + w * dy - pad / 2)))


def pulse(draw, size, cx, cy, w, color, weight):
    """발자국 아래를 가로지르는 심전도 파형."""
    h = w * 0.16
    pts = [(cx - w / 2, cy), (cx - w * 0.20, cy), (cx - w * 0.10, cy - h),
           (cx, cy + h * 0.9), (cx + w * 0.09, cy - h * 0.5),
           (cx + w * 0.18, cy), (cx + w / 2, cy)]
    draw.line(pts, fill=color, width=int(weight), joint="curve")


LOGO = pathlib.Path(__file__).with_name("logo.png")


def place_logo(img, s, safe):
    """logo.png를 정사각 캔버스 가운데에 비율을 유지해 얹는다.
    safe는 로고가 차지할 최대 폭·높이 비율(마스커블은 잘림을 고려해 작게)."""
    logo = Image.open(LOGO).convert("RGBA")
    box = s * safe
    ratio = min(box / logo.width, box / logo.height)
    logo = logo.resize((max(1, int(logo.width * ratio)),
                        max(1, int(logo.height * ratio))), Image.LANCZOS)
    img.alpha_composite(logo, (int((s - logo.width) / 2), int((s - logo.height) / 2)))


def build(px, maskable=False, simple=False, bg=TEAL, mark=WHITE):
    """simple=True면 파형을 빼고 발자국만 크게 — 32px 이하에서 뭉개지지 않는다.
    폴더에 logo.png가 있으면 발자국 대신 그 로고를 사용한다."""
    s = px * SS
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d._image = img

    if maskable:
        # 마스커블은 어떤 모양으로 잘려도 되도록 배경을 꽉 채우고 마크를 안쪽에 둔다
        d.rectangle([0, 0, s, s], fill=bg)
        mark_scale, mark_cy, safe = 0.44, 0.44, 0.56
    else:
        d.rounded_rectangle([0, 0, s, s], radius=s * 0.22, fill=bg)
        mark_scale, mark_cy, safe = 0.56, 0.43, 0.70

    if LOGO.exists():
        place_logo(img, s, safe)
    elif simple:
        paw(d, s, s / 2, s * 0.52, 0.74, mark)
    else:
        paw(d, s, s / 2, s * mark_cy, mark_scale, mark)
        pulse(d, s, s / 2, s * (mark_cy + mark_scale * 0.46), s * mark_scale * 0.92,
              MINT, s * 0.032)

    return img.resize((px, px), Image.LANCZOS)


def main():
    outputs = [
        ("icon-192.png", build(192)),
        ("icon-512.png", build(512)),
        ("icon-maskable-512.png", build(512, maskable=True)),
        # iOS는 자체적으로 모서리를 깎으므로 투명 영역 없이 꽉 채운다
        ("apple-touch-icon.png", build(180, maskable=True)),
        ("favicon-32.png", build(32, simple=True)),
        ("favicon-16.png", build(16, simple=True)),
    ]
    print("로고 소스:", "logo.png" if LOGO.exists() else "없음 — 기본 발자국 마크 사용")
    for name, im in outputs:
        im.convert("RGB").save(name) if name == "apple-touch-icon.png" else im.save(name)
        print("생성:", name, im.size)


if __name__ == "__main__":
    main()
