#!/bin/bash
# 사례 글(src/cases-system/*/posts)로 두 사이트를 다시 만들어 deploy/ 에 넣는다.
# 검사(noindex·금지어·링크·구조화 데이터) 하나라도 실패하면 deploy/ 를 건드리지 않고 멈춘다.
# 사용: bash build.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
SRC="$ROOT/src"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# 1) 그릿: make_grit.py 가 사이트 전체(사례 포함)를 upload/ 에 만든다
cd "$SRC/gritservice-site"
python3 make_grit.py upload > "$TMP/grit.log"
cp -r upload "$TMP/grit"

# 2) 로건: 사례만 만들고 홈(index.php)·llms·robots 에 연결
cd "$SRC/cases-system/engine"
python3 make_cases.py ../logan "$TMP/logan-cases" > "$TMP/logan.log"
mkdir -p "$TMP/logan"
cp "$SRC/loganservice-site/upload/index.php" "$SRC/loganservice-site/upload/llms.txt" "$SRC/loganservice-site/upload/robots.txt" "$TMP/logan/"
cp -r "$TMP/logan-cases/cases" "$TMP/logan/cases"
cp -r "$SRC/loganservice-site/upload/privacy" "$TMP/logan/privacy"
mkdir -p "$TMP/logan/assets"
cp "$SRC/gritservice-site/upload/assets/logan-logo-240.webp" "$TMP/logan/assets/"
cp "$SRC/loganservice-site/upload/assets/favicon.png" "$SRC/loganservice-site/upload/assets/favicon-64.png" "$TMP/logan/assets/"
[ -d "$SRC/cases-system/logan/assets/cases" ] && cp -r "$SRC/cases-system/logan/assets/cases" "$TMP/logan/assets/cases" || true
python3 "$SRC/loganservice-site/add_cases.py" "$TMP/logan" > /dev/null
cp "$TMP/logan/index.php" "$TMP/logan/llms.txt" "$TMP/logan/robots.txt" "$SRC/loganservice-site/upload/"

# 3) 검사
python3 check_cases.py "$TMP/grit" ../grit/site.yaml --mode upload --no-browser > "$TMP/chk-grit.txt" || { cat "$TMP/chk-grit.txt"; echo "그릿 검사 실패"; exit 1; }
python3 check_cases.py "$TMP/logan" ../logan/site.yaml --mode upload --no-browser > "$TMP/chk-logan.txt" || { cat "$TMP/chk-logan.txt"; echo "로건 검사 실패"; exit 1; }
grep -q "'FAIL'" "$TMP/chk-grit.txt" "$TMP/chk-logan.txt" && { echo "검사 FAIL 있음"; exit 1; }
# 절대 규칙: 올라가는 파일에 noindex 금지
if grep -rli noindex "$TMP/grit" "$TMP/logan"; then echo "noindex 발견 → 중단"; exit 1; fi

# 4) 통과하면 deploy/ 교체
rm -rf "$ROOT/deploy/grit" "$ROOT/deploy/logan"
mkdir -p "$ROOT/deploy"
cp -r "$TMP/grit" "$ROOT/deploy/grit"
cp -r "$TMP/logan" "$ROOT/deploy/logan"
echo "빌드·검사 통과: deploy/grit → /public_html/gritservice, deploy/logan → /public_html"
