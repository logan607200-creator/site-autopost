"""로건 홈에 정비사례(/cases/) 연결: 메뉴 CASES, 홈 "최근 정비사례" 섹션, llms.txt 사례 목록, robots 사이트맵.
사용: python3 add_cases.py <사이트폴더>   (사이트폴더 = index.php 가 있는 곳, cases/ 가 이미 들어 있어야 함)
여러 번 돌려도 한 번만 들어간다(표식 <!-- cases-home --> 로 교체).
"""
import re, sys
from pathlib import Path

root = Path(sys.argv[1])
idx = root / "index.php"
s = idx.read_text()
sec = (root / "cases" / "home-section.html").read_text().strip()

# 메뉴(PC·모바일)마다 SERVICE 다음 줄에 CASES 를 한 번만 넣는다. 줄 맨 앞부터 맞춰서 들여쓰기가 다른 메뉴끼리 섞이지 않게 함
s = re.sub(r'(?m)^( *)<a href="cases/">CASES</a>\n', "", s)
s = re.sub(r'(?m)^( *)(<a href="#service">SERVICE</a>\n)', r'\1\2\1<a href="cases/">CASES</a>\n', s)
s = re.sub(r"\n?<!-- cases-home -->.*?<!-- /cases-home -->\n?", "\n", s, flags=re.S)
anchor = '  <section class="instagram" id="instagram">'
assert s.count(anchor) == 1, "instagram 섹션 위치를 못 찾음"
s = s.replace(anchor, f"<!-- cases-home -->\n{sec}\n<!-- /cases-home -->\n{anchor}")
idx.write_text(s)

llms = root / "llms.txt"
t = re.sub(r"\n## 로건서비스 정비사례.*", "", llms.read_text(), flags=re.S).rstrip() + "\n\n"
llms.write_text(t + (root / "cases" / "llms-cases.txt").read_text())

rb = root / "robots.txt"
r = rb.read_text()
if "sitemap-cases.xml" not in r:
    rb.write_text(r.rstrip() + "\nSitemap: https://loganservice.co.kr/cases/sitemap-cases.xml\n")
print("ok", s.count('href="cases/'), "links")
