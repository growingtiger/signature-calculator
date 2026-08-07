#!/usr/bin/env python3
"""PWA 아이콘 생성기.

센터 CI 색(네이비 바탕 + 골드 마크)으로 아이콘을 만든다. 폴더에 logo.png가
있으면 발자국 대신 그 로고를 쓰고 바탕색도 로고 배경에서 읽어온다.
아이콘 모양이나 색을 바꾸려면 아래 상수만 수정하고 다시 실행:

    python3 make-icons.py

4배 크기로 그린 뒤 축소해 가장자리를 부드럽게 처리한다.
"""

import pathlib

from PIL import Image, ImageDraw

NAVY = (33, 46, 81)        # 센터 CI 네이비 #212E51 — 로고에서 추출
GOLD = (175, 148, 118)     # 센터 CI 골드 #AF9476 — 로고에서 추출
MINT = (200, 176, 148)     # 펄스 라인(밝은 골드)
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


def logo_bg(default):
    """로고에 단색 배경이 깔려 있으면 그 색을 아이콘 바탕으로 쓴다.
    네 모서리 색이 모두 같고 불투명할 때만 인정한다(투명 배경 로고는 제외)."""
    if not LOGO.exists():
        return default
    im = Image.open(LOGO).convert("RGBA")
    w, h = im.size
    corners = [im.getpixel(p) for p in ((1, 1), (w - 2, 1), (1, h - 2), (w - 2, h - 2))]
    if all(c[3] == 255 for c in corners) and len({c[:3] for c in corners}) == 1:
        return corners[0][:3]
    return default


MARK = pathlib.Path(__file__).with_name("logo-mark.png")


def extract_symbol():
    """로고에서 심볼(맨 위 도형 블록)만 잘라 logo-mark.png로 저장한다.

    아이콘 크기에서는 'SIGNATURE ANIMAL MEDICAL CENTER' 글자가 읽히지 않고
    심볼만 작아지므로, 글자를 뺀 심볼만 쓰는 것이 맞다. 세로 방향으로 마크
    픽셀이 이어지는 구간(밴드)을 찾아 첫 번째 밴드를 심볼로 본다.
    밴드가 하나뿐이면(=심볼만 있는 로고) 원본을 그대로 쓴다.
    """
    im = Image.open(LOGO).convert("RGBA")
    w, h = im.size
    px = im.load()
    bg = px[1, 1]

    def marked(c):
        return sum(abs(a - b) for a, b in zip(c[:3], bg[:3])) > 60 and c[3] > 40

    bands, start = [], None
    for y in range(h):
        n = sum(1 for x in range(0, w, 3) if marked(px[x, y]))
        if n > 2 and start is None:
            start = y
        elif n <= 2 and start is not None:
            if y - start > h * 0.01:
                bands.append((start, y))
            start = None
    if start is not None:
        bands.append((start, h))

    if len(bands) < 2:
        return LOGO  # 잘라낼 글자가 없다

    top, bot = bands[0]
    xs = [x for x in range(w) for y in range(top, bot, 3) if marked(px[x, y])]
    if not xs:
        return LOGO
    left, right = min(xs), max(xs)

    pad = int(max(bot - top, right - left) * 0.08)
    box = max(bot - top, right - left) + pad * 2
    cx, cy = (left + right) // 2, (top + bot) // 2
    out = Image.new("RGBA", (box, box), bg)
    crop = im.crop((max(0, cx - box // 2), max(0, cy - box // 2),
                    min(w, cx + box // 2), min(h, cy + box // 2)))
    out.paste(crop, ((box - crop.width) // 2, (box - crop.height) // 2))

    # 헤더에 data URI로 심으므로 용량을 줄인다. 사실상 2색 이미지라
    # 512px 팔레트 PNG로도 화질 손실이 없다.
    out = out.convert("RGB").resize((512, 512), Image.LANCZOS)
    out = out.quantize(colors=32, method=Image.MEDIANCUT)
    out.save(MARK, optimize=True)
    return MARK


def place_logo(img, s, safe):
    """로고를 정사각 캔버스 가운데에 비율을 유지해 얹는다.
    safe는 로고가 차지할 최대 폭·높이 비율(마스커블은 잘림을 고려해 작게)."""
    logo = Image.open(MARK if MARK.exists() else LOGO).convert("RGBA")
    box = s * safe
    ratio = min(box / logo.width, box / logo.height)
    logo = logo.resize((max(1, int(logo.width * ratio)),
                        max(1, int(logo.height * ratio))), Image.LANCZOS)
    img.alpha_composite(logo, (int((s - logo.width) / 2), int((s - logo.height) / 2)))


def build(px, maskable=False, simple=False, bg=None, mark=GOLD):
    """simple=True면 파형을 빼고 발자국만 크게 — 32px 이하에서 뭉개지지 않는다.
    폴더에 logo.png가 있으면 발자국 대신 그 로고를 쓰고, 로고 배경색을 바탕으로 삼는다."""
    bg = bg or logo_bg(NAVY)
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
    # 심볼 추출을 아이콘 생성보다 먼저 해야 첫 실행부터 반영된다
    if LOGO.exists():
        src = extract_symbol()
        print("로고 소스: %s%s" % (src.name,
              " (심볼만 자동 추출)" if src == MARK else " (밴드가 하나뿐이라 원본 사용)"))
    else:
        print("로고 소스: 없음 — 기본 발자국 마크 사용")
    bg = logo_bg(NAVY)
    print("아이콘 바탕: #%02X%02X%02X%s" % (bg[0], bg[1], bg[2],
          " (로고 배경에서 추출)" if bg != NAVY else " (CI 네이비)"))

    outputs = [
        ("icon-192.png", build(192)),
        ("icon-512.png", build(512)),
        ("icon-maskable-512.png", build(512, maskable=True)),
        # iOS는 자체적으로 모서리를 깎으므로 투명 영역 없이 꽉 채운다
        ("apple-touch-icon.png", build(180, maskable=True)),
        ("favicon-32.png", build(32, simple=True)),
        ("favicon-16.png", build(16, simple=True)),
    ]
    for name, im in outputs:
        im.convert("RGB").save(name) if name == "apple-touch-icon.png" else im.save(name)
        print("생성:", name, im.size)


if __name__ == "__main__":
    main()
