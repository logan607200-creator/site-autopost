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
cp "$SRC/loganservice-site/upload/index.php" "$SRC/loganservice-site/upload/llms.txt" "$SRC/loganservice-site/upload/robots.txt" "$SRC/loganservice-site/upload/favicon.ico" "$TMP/logan/"
cp -r "$TMP/logan-cases/cases" "$TMP/logan/cases"
cp -r "$SRC/loganservice-site/upload/privacy" "$TMP/logan/privacy"
# 질문 페이지·AI용 전체 문답·사이트맵도 여기서 관리한다(서버에서 손으로 고친 판이 자동 업로드로 덮이지 않게)
cp -r "$SRC/loganservice-site/upload/faq" "$TMP/logan/faq"
cp "$SRC/loganservice-site/upload/llms-full.txt" "$SRC/loganservice-site/upload/sitemap.xml" "$TMP/logan/"
mkdir -p "$TMP/logan/assets"
cp "$SRC/gritservice-site/upload/assets/logan-logo-240.webp" "$TMP/logan/assets/"
cp "$SRC/loganservice-site/upload/assets/favicon.png" "$SRC/loganservice-site/upload/assets/favicon-64.png" "$TMP/logan/assets/"
[ -d "$SRC/cases-system/logan/assets/cases" ] && cp -r "$SRC/cases-system/logan/assets/cases" "$TMP/logan/assets/cases" || true
python3 "$SRC/loganservice-site/add_cases.py" "$TMP/logan" > /dev/null
# 모델별·증상별·탁송 안내 페이지(사례·FAQ 에서 만듦) + 홈 링크·sitemap·llms
python3 "$SRC/loganservice-site/make_hubs.py" "$TMP/logan" > /dev/null
# IndexNow 키 파일(그릿과 같은 키)
cp "$SRC/loganservice-site/upload/0d5b85b24fd3f3b1750da89666d9a379.txt" "$TMP/logan/"
cp "$TMP/logan/index.php" "$TMP/logan/llms.txt" "$TMP/logan/robots.txt" "$SRC/loganservice-site/upload/"

# 3) 검사
python3 check_cases.py "$TMP/grit" ../grit/site.yaml --mode upload --no-browser --strict-links --site-dir "$TMP/grit" > "$TMP/chk-grit.txt" || { cat "$TMP/chk-grit.txt"; echo "그릿 검사 실패"; exit 1; }
python3 check_cases.py "$TMP/logan" ../logan/site.yaml --mode upload --no-browser --strict-links --site-dir "$TMP/logan" > "$TMP/chk-logan.txt" || { cat "$TMP/chk-logan.txt"; echo "로건 검사 실패"; exit 1; }
# 사이트 전체(홈·FAQ·서비스·개인정보·sitemap·robots) 검사: 제목·설명 길이, canonical, 깨진 링크, 미래 lastmod 등
python3 "$SRC/check_site.py" "$TMP/grit" https://gritservice.co.kr/ || { echo "그릿 사이트 검사 실패"; exit 1; }
python3 "$SRC/check_site.py" "$TMP/logan" https://loganservice.co.kr/ || { echo "로건 사이트 검사 실패"; exit 1; }
# 절대 규칙: 올라가는 파일에 noindex 금지
if grep -rli noindex "$TMP/grit" "$TMP/logan"; then echo "noindex 발견 → 중단"; exit 1; fi

# 4) 통과하면 deploy/ 교체
rm -rf "$ROOT/deploy/grit" "$ROOT/deploy/logan"
mkdir -p "$ROOT/deploy"
cp -r "$TMP/grit" "$ROOT/deploy/grit"
cp -r "$TMP/logan" "$ROOT/deploy/logan"
echo "빌드·검사 통과: deploy/grit → /public_html/gritservice, deploy/logan → /public_html"
