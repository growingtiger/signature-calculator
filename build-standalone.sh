#!/bin/sh
# vet-calculator.html은 Artifact 게시용 조각(fragment)이라 doctype/head/body 태그가 없다.
# 이 스크립트가 하는 일:
#   1. 조각을 완전한 HTML 문서 index.html로 감싼다
#   2. PWA 메타 태그와 서비스 워커 등록 코드를 넣는다 (설치형 앱 + 오프라인 사용)
#   3. index.html 해시로 sw.js를 생성해 배포할 때마다 캐시가 자동 갱신되게 한다
#
# 계산기를 수정한 뒤 다시 실행:  sh build-standalone.sh
# 아이콘을 바꾸려면:              python3 make-icons.py

set -e
cd "$(dirname "$0")"

python3 - <<'PY'
import base64
import hashlib
import mimetypes
import pathlib
import re

src = pathlib.Path('vet-calculator.html').read_text(encoding='utf-8')

# logo.png(또는 logo.svg)가 있으면 헤더의 기본 마크를 실제 로고로 교체한다.
# 외부 파일 참조 없이 data URI로 심어 단일 파일로도 동작하게 한다.
logo = next((p for p in (pathlib.Path('logo.svg'), pathlib.Path('logo.png'))
             if p.exists()), None)
if logo:
    mime = mimetypes.guess_type(logo.name)[0] or 'image/png'
    b64 = base64.b64encode(logo.read_bytes()).decode('ascii')
    img = ('<img src="data:%s;base64,%s" alt="시그니처 동물의료센터 로고">' % (mime, b64))
    new_src, n = re.subn(
        r'(<span class="brand-mark"[^>]*>).*?(</span>)',
        lambda m: m.group(1) + img + m.group(2),
        src, count=1, flags=re.S)
    if n:
        src = new_src
        print('로고 삽입: %s (%.1f KB)' % (logo.name, len(b64) * 3 / 4 / 1024))
    else:
        print('경고: brand-mark 자리를 찾지 못해 로고를 넣지 못했습니다')
else:
    print('로고 없음 — 기본 마크 사용 (logo.png를 이 폴더에 두면 자동 반영)')

head, body = src.split('</style>', 1)

DESC = ('시그니처 동물의료센터 수의사를 위한 임상 계산기. 수액·응급, 전해질, 약물 용량, '
        '영양, 신장·투석 등을 종과 체중 한 번 입력으로 계산합니다.')

PWA_HEAD = '''<meta name="description" content="{d}">
<meta name="color-scheme" content="light dark">
<meta name="theme-color" content="#2B3A5E" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#0E121B" media="(prefers-color-scheme: dark)">
<meta property="og:type" content="website">
<meta property="og:title" content="시그니처 동물의료센터 · 수의 임상 계산기">
<meta property="og:description" content="{d}">
<meta property="og:image" content="icon-512.png">
<meta name="twitter:card" content="summary">
<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" href="favicon-32.png" sizes="32x32" type="image/png">
<link rel="icon" href="favicon-16.png" sizes="16x16" type="image/png">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="수의 계산기">
'''.format(d=DESC)

# file://에서는 서비스 워커를 등록할 수 없으므로 프로토콜을 확인하고 조용히 넘어간다
SW_REG = '''
<script>
(function () {
  if (!("serviceWorker" in navigator)) return;
  var okHost = location.protocol === "https:" || location.hostname === "localhost"
            || location.hostname === "127.0.0.1";
  if (!okHost) return;
  window.addEventListener("load", function () {
    navigator.serviceWorker.register("sw.js").catch(function () {});
  });
})();
</script>
'''

doc = ('<!doctype html>\n<html lang="ko">\n<head>\n'
       '<meta charset="utf-8">\n'
       '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
       + PWA_HEAD + head + '</style>\n</head>\n<body>'
       + body + SW_REG + '</body>\n</html>\n')

pathlib.Path('index.html').write_text(doc, encoding='utf-8')

# 문서 내용이 바뀌면 캐시 이름이 바뀌도록 해시를 심는다
version = hashlib.sha256(doc.encode('utf-8')).hexdigest()[:12]
sw = pathlib.Path('sw.template.js').read_text(encoding='utf-8').replace('__VERSION__', version)
pathlib.Path('sw.js').write_text(sw, encoding='utf-8')

print('index.html 생성 (%d bytes)' % len(doc.encode('utf-8')))
print('sw.js 생성   (캐시 버전 %s)' % version)
PY
