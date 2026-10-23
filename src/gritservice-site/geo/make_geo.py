"""GEO 질문·답변으로 faq/index.php(사람용 페이지 + FAQPage JSON-LD)와 llms-full.txt(AI용)를 만든다.
make_grit.py 끝에서 build() 를 부른다. 질문·답변 내용은 geo_qa.py 에서만 고친다.
- 같은 답을 쓰는 질문은 한 항목으로 묶고 나머지 질문은 '비슷한 질문'으로 보여 준다(같은 글 반복 방지).
- FAQPage 구조화 데이터에는 문장형 질문만 넣는다('교하 공업사' 같은 검색어형은 화면·llms-full 에만).
- 차종 질문에는 그 차종의 실제 수리사례 주소를 붙인다."""
import html as H
import json
from geo_qa import qa, TOP, TOP_CAT
import make_pages as P

FAQ_PATH = "faq/"
# 분류별 관련 페이지(분류 끝에 한 줄)
CAT_LINKS = {
    "지역 추천": [("area/", "오시는 길·서비스 지역")],
    "사고수리": [("accident-repair/", "사고수리 안내"), ("cases/accident-repair/", "사고수리 사례")],
    "판금·도색": [("painting/", "판금·도색 안내"), ("cases/painting/", "판금·도색 사례")],
    "보험수리": [("insurance-repair/", "보험수리 안내")],
    "중고차 성능보증수리": [("certified-repair/", "성능보증수리 안내"), ("cases/certified-repair/", "성능보증수리 사례")],
    "자동차정비": [("maintenance/", "자동차정비 안내"), ("cases/maintenance/", "정비 사례")],
    "외형관리·PPF·세차": [("exterior-care/", "외형관리·PPF 안내")],
    "탁송": [("area/", "오시는 길·탁송 안내")],
    "차종·수입차": [("imported-cars/", "수입차 수리 안내"), ("cases/", "수리사례 전체")],
    "업체 정보·이용": [("area/", "오시는 길"), ("privacy/", "개인정보처리방침")],
}
# 차종 질문 첫 단어 → 사례의 brand/model 에서 찾을 말
CAR_KEYS = {"벤츠": ["벤츠", "메르세데스"], "BMW": ["BMW"], "아우디": ["아우디"], "테슬라": ["테슬라"], "현대차": ["현대"],
            "기아": ["기아"], "제네시스": ["제네시스"], "볼보": ["볼보"], "포르쉐": ["포르쉐"],
            "SUV": ["스포티지", "싼타페", "모델Y", "GV70", "GV80", "쏘렌토", "투싼"], "전기차": ["모델Y", "아이오닉", "EV"]}


def _car_cases(q, cases, SITE):
    keys = CAR_KEYS.get(q.split()[0])
    if not keys:
        return ""
    hit = [p for p in cases if any(k in f'{(p.get("car") or {}).get("brand", "")} {(p.get("car") or {}).get("model", "")}' for k in keys)][:2]
    return " 실제 사례: " + ", ".join(f'{p["title"]}({SITE}cases/{p["slug"]}/)' for p in hit) + "." if hit else ""


def entries(items, cases, SITE):
    """[(분류, 대표 질문, 답, 비슷한 질문들)] — 같은 분류 안에서 답이 같은 질문은 하나로."""
    out, seen = [], {}
    for c, _, q, a in items:
        if c == "차종·수입차":
            a = a + _car_cases(q, cases, SITE)
        k = (c, a)
        if k in seen:
            seen[k][3].append(q)
            continue
        e = [c, q, a, []]
        seen[k] = e
        out.append(e)
    # 대표 질문은 문장형 질문을 우선
    for e in out:
        qs = [e[1]] + e[3]
        nat = [x for x in qs if P.is_natural(x)]
        if nat and not P.is_natural(e[1]):
            e[1] = nat[0]
            e[3] = [x for x in qs if x != nat[0]]
    return out


def _row(q, a, sim):
    s = f'      <details><summary>{H.escape(q)}</summary><p>{P.linkify(H.escape(a))}</p>'
    if sim:
        s += f'<p class="similar">비슷한 질문: {H.escape(" · ".join(sim))}</p>'
    return s + "</details>"


def build(OUT, SITE, PHONE, TEL, ADDR_FULL, KAKAO, BLOG, INSTA, COMPANY, CEO, BIZNO, TODAY, cases=()):
    items = qa(PHONE, ADDR_FULL, KAKAO, BLOG, INSTA)
    ents = entries(items, cases, SITE)
    n_q = len(TOP) + len(items)
    url = SITE + FAQ_PATH
    cats = list(dict.fromkeys(e[0] for e in ents))
    title = "파주 공업사 자주 묻는 질문 | 그릿서비스"  # 40자 이내
    desc = f"파주 교하 공업사 그릿서비스가 사고수리, 판금도색, 보험수리, 성능보증수리, 정비, 탁송 질문에 답합니다. 상담 {PHONE}."  # 80자 이내
    top_q = {q for q, _ in TOP}
    marked = [(q, a) for q, a in TOP] + [(q, a) for _, q, a, _ in ents if P.is_natural(q) and q not in top_q]
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "FAQPage", "@id": url + "#faq", "url": url, "name": title, "inLanguage": "ko-KR", "dateModified": TODAY,
         "about": {"@id": SITE + "#grit-service"}, "isPartOf": {"@id": SITE + "#website"},
         "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in marked]},
        P.crumb_ld([("자주 묻는 질문", FAQ_PATH)]),
    ]}
    toc = f'      <a href="#cq">{H.escape(TOP_CAT)}</a>\n' + "\n".join(f'      <a href="#c{i}">{H.escape(c)}</a>' for i, c in enumerate(cats))
    secs = [f'  <section id="cq">\n    <h2>{H.escape(TOP_CAT)}</h2>\n' + "\n".join(_row(q, a, []) for q, a in TOP) + "\n  </section>"]
    for i, c in enumerate(cats):
        rows = "\n".join(_row(q, a, sim) for cc, q, a, sim in ents if cc == c)
        links = " · ".join(f'<a href="../{u}">{t} →</a>' for u, t in CAT_LINKS.get(c, []))
        secs.append(f'  <section id="c{i}">\n    <h2>{H.escape(c)}</h2>\n{rows}\n' + (f'    <p class="more">{links}</p>\n' if links else "") + "  </section>")
    extra = "nav.toc{display:flex;flex-wrap:wrap;gap:8px;margin:20px 0 8px}nav.toc a{font-size:15px;padding:9px 14px;min-height:44px;display:inline-flex;align-items:center;border:1px solid #c9d0db;border-radius:999px;text-decoration:none;background:#fff}"
    body = P.crumb([("자주 묻는 질문", None)], 1)
    body += f'''  <h1>파주 자동차 공업사 그릿서비스<br>자주 묻는 질문</h1>
  <p class="lead">사고수리, 판금·도색, 보험수리, 중고차 성능보증수리, 자동차정비, 외형관리, 탁송에 대해 자주 받는 질문 {n_q}개를 정리했습니다. 비용과 일정은 차량을 확인한 뒤 안내합니다. 실제 작업은 <a href="../cases/">수리사례</a>에서 볼 수 있습니다.</p>
  <nav class="toc" aria-label="질문 분류">
{toc}
  </nav>
{chr(10).join(secs)}
'''
    page = P.head(title, desc, url, 1, ld, extra).replace(
        '  <meta property="og:title"', f'  <link rel="alternate" type="text/markdown" title="그릿서비스 AI용 전체 질문·답변 (llms-full.txt)" href="{SITE}llms-full.txt" />\n  <meta property="og:title"', 1) + body + P.foot(1)
    (OUT / "faq").mkdir(exist_ok=True)
    (OUT / "faq" / "index.php").write_text(page)

    md = [f"# 그릿서비스 (GRIT SERVICE) 자주 묻는 질문 {n_q}개\n",
          f"> 경기도 파주시 교하의 자동차 공업사 그릿서비스가 고객과 AI 검색이 자주 묻는 질문에 답합니다. 주소 {ADDR_FULL}, 대표번호 {PHONE}(전화 상담 24시간, 입고·작업 평일 09:00~18:00). 요약은 {SITE}llms.txt, 사람이 보는 페이지는 {url}, 실제 수리 기록은 {SITE}cases/ 입니다.\n",
          f"\n최종 업데이트: {TODAY}\n"]
    md.append(f"\n## 자주 찾는 질문: {TOP_CAT}\n")
    md += [f"\n### {q}\n{a}\n" for q, a in TOP]
    for c in cats:
        md.append(f"\n## {c}\n")
        for cc, q, a, sim in ents:
            if cc == c:
                md.append(f"\n### {q}\n" + (f"(비슷한 질문: {' / '.join(sim)})\n" if sim else "") + f"{a}\n")
    (OUT / "llms-full.txt").write_text("".join(md))
    return url, n_q
