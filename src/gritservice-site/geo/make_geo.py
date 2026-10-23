"""GEO 질문·답변 200개로 faq/index.php(사람용 페이지 + FAQPage JSON-LD)와 llms-full.txt(AI용)를 만든다.
make_grit.py 끝에서 build() 를 부른다. 질문·답변 내용은 geo_qa.py 에서만 고친다."""
import html as H
import json
from geo_qa import qa, TOP, TOP_CAT

FAQ_PATH = "faq/"


def build(OUT, SITE, PHONE, TEL, ADDR_FULL, KAKAO, BLOG, INSTA, COMPANY, CEO, BIZNO, TODAY):
    items = qa(PHONE, ADDR_FULL, KAKAO, BLOG, INSTA)
    url = SITE + FAQ_PATH
    cats = list(dict.fromkeys(c for c, _, _, _ in items))
    title = "파주 자동차 공업사 질문 200 | 사고수리·판금도색·보험수리·성능보증수리 - 그릿서비스"
    desc = f"파주 교하 자동차 공업사 그릿서비스가 사고수리, 판금·도색, 보험수리, 중고차 성능보증수리, 정비, 외형관리, 탁송에 대해 자주 받는 질문 200개에 답합니다. 상담 {PHONE}."

    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "FAQPage", "@id": url + "#faq", "url": url, "name": title, "inLanguage": "ko-KR", "dateModified": TODAY,
         "about": {"@id": SITE + "#grit-service"}, "isPartOf": {"@id": SITE + "#website"},
         "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in TOP + [(q, a) for _, _, q, a in items]]},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "그릿서비스", "item": SITE},
            {"@type": "ListItem", "position": 2, "name": "자주 묻는 질문 200", "item": url}]},
    ]}
    toc = f'      <a href="#cq">{H.escape(TOP_CAT)}</a>\n' + "\n".join(f'      <a href="#c{i}">{H.escape(c)}</a>' for i, c in enumerate(cats))
    top_rows = "\n".join(f'      <details><summary>{H.escape(q)}</summary><p>{H.escape(a)}</p></details>' for q, a in TOP)
    secs = [f'    <section id="cq">\n      <h2>{H.escape(TOP_CAT)}</h2>\n{top_rows}\n    </section>']
    for i, c in enumerate(cats):
        rows = "\n".join(f'      <details><summary>{H.escape(q)}</summary><p>{H.escape(a)}</p></details>'
                         for cc, _, q, a in items if cc == c)
        secs.append(f'    <section id="c{i}">\n      <h2>{H.escape(c)}</h2>\n{rows}\n    </section>')
    page = f'''<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title}</title>
  <meta name="description" content="{desc}" />
  <meta name="robots" content="index,follow,max-snippet:-1" />
  <link rel="canonical" href="{url}" />
  <link rel="icon" href="{SITE}assets/favicon.png" />
  <link rel="alternate" type="text/markdown" title="그릿서비스 AI용 전체 질문·답변 (llms-full.txt)" href="{SITE}llms-full.txt" />
  <meta property="og:title" content="{title}" />
  <meta property="og:description" content="{desc}" />
  <meta property="og:url" content="{url}" />
  <meta property="og:type" content="website" />
  <meta property="og:image" content="{SITE}assets/og-image.jpg" />
  <script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
  <style>
    *{{box-sizing:border-box}}body{{margin:0;font-family:"Pretendard","Apple SD Gothic Neo","Noto Sans KR",sans-serif;color:#1c1f24;background:#fff;line-height:1.65;word-break:keep-all}}
    header{{background:#000;color:#fff}}header .w{{display:flex;justify-content:space-between;align-items:center;min-height:60px}}header a{{color:#fff;text-decoration:none;font-weight:700}}
    .w{{max-width:900px;margin:0 auto;padding:0 16px}}h1{{font-size:clamp(24px,5vw,36px);line-height:1.3;margin:36px 0 10px;word-break:keep-all}}
    .lead{{color:#5c626c}}nav.toc{{display:flex;flex-wrap:wrap;gap:8px;margin:20px 0 8px}}nav.toc a{{font-size:14px;padding:6px 12px;border:1px solid #d5dae2;border-radius:999px;color:#004a9f;text-decoration:none}}
    h2{{font-size:22px;margin:40px 0 10px;padding-top:10px;border-top:2px solid #004a9f;color:#004a9f}}
    details{{border-bottom:1px solid #e6e9ee;padding:12px 0}}summary{{cursor:pointer;font-weight:700}}details p{{margin:8px 0 0;color:#3d434c;overflow-wrap:anywhere}}
    .cta{{display:flex;flex-wrap:wrap;gap:10px;margin:36px 0}}.cta a{{flex:1 1 200px;text-align:center;padding:14px;border-radius:8px;font-weight:700;text-decoration:none;background:#004a9f;color:#fff}}.cta a+a{{background:#fee500;color:#191919}}
    footer{{background:#f3f5f8;color:#646a74;font-size:13px;padding:24px 0;margin-top:40px}}
  </style>
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-J953M2539G"></script>
  <script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag('js',new Date());gtag('config','G-J953M2539G');</script>
</head>
<body>
<header><div class="w"><a href="{SITE}">GRIT SERVICE 그릿서비스</a><a href="tel:{TEL}">{PHONE}</a></div></header>
<main class="w">
  <h1>파주 자동차 공업사 그릿서비스<br>자주 묻는 질문 200</h1>
  <p class="lead">사고수리, 판금·도색, 보험수리, 중고차 성능보증수리, 자동차정비, 외형관리, 탁송에 대해 자주 받는 질문을 정리했습니다. 비용과 일정은 차량을 확인한 뒤 안내합니다.</p>
  <nav class="toc">
{toc}
  </nav>
{chr(10).join(secs)}
  <div class="cta"><a href="tel:{TEL}">전화 상담 {PHONE}</a><a href="{KAKAO}" target="_blank" rel="noopener">카카오톡 상담</a></div>
  <p><a href="{SITE}">그릿서비스 홈으로</a></p>
</main>
<footer><div class="w">{COMPANY} · 대표 {CEO} · 사업자등록번호 {BIZNO} · {ADDR_FULL} · {PHONE}</div></footer>
<script>
// 전화·카카오 상담 클릭을 광고 전환으로 기록
document.addEventListener('click',function(e){{var a=e.target.closest('a[href^="tel:"],a[href*="pf.kakao.com"]');if(!a)return;var t=a.href.indexOf('tel:')===0?'call':'kakao';if(window.gtag)gtag('event','contact_'+t,{{method:t}});}});
</script>
</body>
</html>
'''
    (OUT / "faq").mkdir(exist_ok=True)
    (OUT / "faq" / "index.php").write_text(page)

    md = [f"# 그릿서비스 (GRIT SERVICE) 자주 묻는 질문 200\n",
          f"> 경기도 파주시 교하의 자동차 공업사 그릿서비스가 고객과 AI 검색이 자주 묻는 질문에 답합니다. 주소 {ADDR_FULL}, 대표번호 {PHONE}(24시간 상담). 요약은 {SITE}llms.txt, 사람이 보는 페이지는 {url} 입니다.\n"]
    md.append(f"\n## 자주 찾는 질문: {TOP_CAT}\n")
    md += [f"\n### {q}\n{a}\n" for q, a in TOP]
    for c in cats:
        md.append(f"\n## {c}\n")
        md += [f"\n### {q}\n{a}\n" for cc, _, q, a in items if cc == c]
    (OUT / "llms-full.txt").write_text("".join(md))
    return url


def index_more(SITE, PHONE, ADDR_FULL, KAKAO, BLOG, INSTA):
    """홈 FAQ 아래 '더보기'. <details> 라 JS 없이 펼쳐지고, 접혀 있어도 HTML 안에 있어 검색·AI가 읽는다."""
    items = qa(PHONE, ADDR_FULL, KAKAO, BLOG, INSTA)
    cats = list(dict.fromkeys(c for c, _, _, _ in items))
    body = []
    for c in cats:
        body.append(f'          <h3 class="faq-cat">{H.escape(c)}</h3>')
        body += [f'          <details class="faq-item"><summary>{H.escape(q)}</summary><p>{H.escape(a)}</p></details>'
                 for cc, _, q, a in items if cc == c]
    top = "".join(f'        <details class="faq-item"><summary>{H.escape(q)}</summary><p>{H.escape(a)}</p></details>\n' for q, a in TOP)
    return top + (f'''        <details class="faq-more" id="faq-more">
          <summary><span class="more-open">더보기 · 자주 묻는 질문 {len(items)}개</span><span class="more-close">접기</span></summary>
{chr(10).join(body)}
          <p class="faq-more-link"><a href="{SITE}faq/">질문 {len(items)}개 한 페이지로 보기 →</a></p>
        </details>
        <style>
          .faq-more>summary{{list-style:none;cursor:pointer;margin-top:22px;padding:15px;text-align:center;border:1px solid #004a9f;border-radius:8px;color:#004a9f;font-weight:700}}
          .faq-more>summary::-webkit-details-marker{{display:none}}
          .faq-more .more-close,.faq-more[open] .more-open{{display:none}}.faq-more[open] .more-close{{display:inline}}
          .faq-cat{{margin:34px 0 4px;font-size:15px;letter-spacing:.04em;color:#004a9f}}
          .faq-more-link a{{color:#004a9f;font-weight:700}}
        </style>''')
