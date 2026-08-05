#!/bin/sh
# vet-calculator.html은 Artifact 게시용 조각(fragment)이라 doctype/html/head/body 태그가 없습니다.
# 이 스크립트는 브라우저에서 직접 열 수 있는 완전한 문서 index.html을 생성합니다.
# 계산기를 수정한 뒤 다시 실행하면 index.html이 갱신됩니다.
#
# 사용법: sh build-standalone.sh

set -e
cd "$(dirname "$0")"

python3 - <<'PY'
import pathlib

src = pathlib.Path('vet-calculator.html').read_text(encoding='utf-8')
head, body = src.split('</style>', 1)

DESC = ('시그니처 동물의료센터 수의사를 위한 임상 계산기. 수액·응급, 전해질, 약물 용량, '
        '영양, 신장·투석 등 29종을 종과 체중 한 번 입력으로 계산합니다.')

doc = (
    '<!doctype html>\n'
    '<html lang="ko">\n'
    '<head>\n'
    '<meta charset="utf-8">\n'
    '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
    '<meta name="description" content="' + DESC + '">\n'
    '<meta name="color-scheme" content="light dark">\n'
    '<meta property="og:type" content="website">\n'
    '<meta property="og:title" content="시그니처 동물의료센터 · 수의 임상 계산기">\n'
    '<meta property="og:description" content="' + DESC + '">\n'
    '<meta name="twitter:card" content="summary">\n'
    + head + '</style>\n'
    '</head>\n'
    '<body>' + body + '</body>\n'
    '</html>\n'
)

pathlib.Path('index.html').write_text(doc, encoding='utf-8')
print('index.html 생성 완료 (%d bytes)' % len(doc.encode('utf-8')))
PY
