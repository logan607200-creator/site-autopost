"""그릿서비스 하위 페이지: 서비스 상세 7개, 오시는 길·서비스 지역, 개인정보처리방침, 공통 머리글·바닥글.
make_grit.py 가 부른다. 질문·답변은 geo/geo_qa.py, 사례는 ../cases-system/grit/posts 에서 가져온다(새로 지어내지 않음).
서비스 상세는 index.html 로 만든다(서버에 원래 있던 index.html 을 덮어써서 canonical 이 /xxx/ 로 정리되게)."""
import html as H
import json, re
import yaml

C = {}  # make_grit.py 가 init() 으로 채우는 업체 정보


def init(**kw):
    C.update(kw)


# ---------- 공통 ----------
URL_RE = re.compile(r"(https?://[^\s()<>,]+[^\s()<>,.])|(?<![/\w.])(loganservice\.co\.kr)(?![\w/])")


def linkify(text):
    """글자(이미 escape 된 HTML)의 주소를 링크로. 카톡·블로그·상대 사이트 주소를 눌러 바로 갈 수 있게."""
    def rep(m):
        u = m.group(1) or ("https://" + m.group(2) + "/")
        shown = m.group(0)
        ext = not u.startswith(C["SITE"])
        return f'<a href="{u}"' + (' target="_blank" rel="noopener"' if ext else "") + f">{shown}</a>"
    return URL_RE.sub(rep, text)


NAV = [("", "홈"), ("#service", "서비스"), ("cases/", "수리사례"), ("faq/", "자주 묻는 질문"), ("area/", "오시는 길")]

CSS = """
    :root{color-scheme:only light}
    *{box-sizing:border-box}body{margin:0;font-family:"Pretendard","Apple SD Gothic Neo","Malgun Gothic","Noto Sans KR",sans-serif;color:#1c1f24;background:#fbfcfe;line-height:1.7;word-break:keep-all}
    a{color:#004a9f}
    .skip{position:absolute;left:-999px;top:0;background:#fff;padding:8px 12px;z-index:99}.skip:focus{left:8px}
    .w{max-width:900px;margin:0 auto;padding:0 16px}
    header.top{background:#000;color:#fff}
    header.top .w{display:flex;align-items:center;gap:8px 18px;flex-wrap:wrap;min-height:64px;padding-top:6px;padding-bottom:6px}
    header.top .brand{display:flex;align-items:center;gap:10px;color:#fff;text-decoration:none;font-weight:800;letter-spacing:.06em;min-height:44px}
    header.top .brand img{width:40px;height:40px}
    header.top nav{display:flex;flex-wrap:wrap;gap:2px 4px;margin-left:auto}
    header.top nav a{color:#fff;text-decoration:none;font-size:15px;padding:10px 8px;min-height:44px;display:inline-flex;align-items:center}
    header.top nav a.tel{background:#004a9f;border-radius:6px;padding:10px 14px;font-weight:700}
    .crumb{font-size:14px;color:#4a4f57;margin:18px 0 0}.crumb a{display:inline-block;padding:10px 2px}
    h1{font-size:clamp(26px,5vw,38px);line-height:1.3;margin:12px 0 12px}
    h2{font-size:22px;margin:44px 0 12px;padding-top:12px;border-top:2px solid #004a9f;color:#003a7d}
    h3{font-size:18px;margin:22px 0 6px}
    .lead{font-size:17px;color:#383b40}
    .card-list{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,260px),1fr));gap:12px;padding:0;list-style:none}
    .card-list li{background:#fff;border:1px solid #dde2ea;border-radius:10px;padding:14px 16px}
    .card-list a{font-weight:700;text-decoration:none}.card-list p{margin:6px 0 0;font-size:15px;color:#4a4f57}
    ol.steps{padding-left:22px}ol.steps li{margin:6px 0}
    details{border-bottom:1px solid #e1e5ec;padding:12px 0}summary{cursor:pointer;font-weight:700;min-height:28px}details p{margin:8px 0 0;color:#383b40;overflow-wrap:anywhere}
    .similar{font-size:14px;color:#5b616b}
    .more{margin:14px 0 0;font-size:15px}.more a{display:inline-block;padding:8px 0;font-weight:700}
    .cta{display:flex;flex-wrap:wrap;gap:10px;margin:36px 0}.cta a{flex:1 1 220px;text-align:center;padding:15px;border-radius:8px;font-weight:700;text-decoration:none;background:#004a9f;color:#fff}.cta a+a{background:#fee500;color:#191919}
    .info{background:#fff;border:1px solid #dde2ea;border-radius:10px;padding:6px 18px}.info dt{font-weight:700;margin-top:12px}.info dd{margin:2px 0 12px}
    table{border-collapse:collapse;width:100%;font-size:15px;margin:10px 0}th,td{border:1px solid #d9dfe8;padding:8px;text-align:left;vertical-align:top}th{background:#eef2f8}
    footer.bot{background:#eef2f8;color:#383b40;font-size:14px;padding:26px 0;margin-top:48px}
    footer.bot a{display:inline-block;padding:6px 0}
    .callbar{display:none}
    @media(max-width:760px){.callbar{display:grid;grid-template-columns:1fr 1fr;position:fixed;left:0;right:0;bottom:0;z-index:60;box-shadow:0 -4px 16px rgba(0,0,0,.15)}.callbar a{display:flex;align-items:center;justify-content:center;min-height:54px;font-weight:700;font-size:15px;color:#fff;background:#004a9f;text-decoration:none}.callbar a+a{background:#fee500;color:#191919}body{padding-bottom:54px}header.top nav a.tel{display:none}}
"""

TRACK = """<script>
// 전화·카카오 상담 클릭 기록(어느 자리에서 눌렀는지 position 으로 구분)
document.addEventListener('click',function(e){var a=e.target.closest('a[href^="tel:"],a[href*="pf.kakao.com"]');if(!a)return;var t=a.href.indexOf('tel:')===0?'call':'kakao';
var s=a.closest('.callbar,header,footer,section,.cta,nav');var p=s?(s.id||(s.className&&String(s.className).split(' ')[0])||s.tagName.toLowerCase()):'page';
if(window.gtag)gtag('event','contact_'+t,{method:t,position:p});});
</script>"""


def head(title, desc, url, depth, ld=None, extra=""):
    up = "../" * depth
    s = C["SITE"]
    return f'''<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta name="color-scheme" content="only light" />
  <title>{H.escape(title)}</title>
  <meta name="description" content="{H.escape(desc)}" />
  <meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1" />
  <link rel="canonical" href="{url}" />
  <link rel="icon" type="image/png" sizes="64x64" href="{up}assets/favicon-64.png" />
  <meta property="og:title" content="{H.escape(title)}" />
  <meta property="og:description" content="{H.escape(desc)}" />
  <meta property="og:url" content="{url}" />
  <meta property="og:type" content="website" />
  <meta property="og:site_name" content="그릿서비스" />
  <meta property="og:locale" content="ko_KR" />
  <meta property="og:image" content="{s}assets/og-image.jpg" />
  <meta name="theme-color" content="#004a9f" />
  <script async src="https://www.googletagmanager.com/gtag/js?id={C["GA4"]}"></script>
  <script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag('js',new Date());gtag('config','{C["GA4"]}');</script>
{('  <script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False) + '</script>') if ld else ''}
  <style>{CSS}{extra}</style>
</head>
<body>
<a class="skip" href="#main">본문 바로가기</a>
<header class="top"><div class="w">
  <a class="brand" href="{up}"><img src="{up}assets/grit-logo-192.webp" alt="" width="40" height="40">GRIT SERVICE</a>
  <nav aria-label="주요 메뉴">{"".join(f'<a href="{up}{h}">{t}</a>' for h, t in NAV)}<a class="tel" href="tel:{C["TEL"]}">{C["PHONE"]}</a></nav>
</div></header>
<main id="main" class="w">
'''


def foot(depth):
    up = "../" * depth
    return f'''  <div class="cta" id="cta"><a href="tel:{C["TEL"]}">전화 상담 {C["PHONE"]}</a><a href="{C["KAKAO"]}" target="_blank" rel="noopener">카톡으로 사진 보내 상담</a></div>
</main>
<footer class="bot"><div class="w">
  <p><strong>그릿서비스</strong> · {C["COMPANY"]} · 대표 {C["CEO"]} · 사업자등록번호 {C["BIZNO"]}<br>{C["ADDR_FULL"]} · 작업 평일 09:00~18:00 · 전화 상담 24시간 {C["PHONE"]}</p>
  <p><a href="{up}">홈</a> · <a href="{up}cases/">수리사례</a> · <a href="{up}faq/">자주 묻는 질문</a> · <a href="{up}area/">오시는 길</a> · <a href="{up}privacy/">개인정보처리방침</a> · <a href="{C["LOGAN"]}" target="_blank" rel="noopener">로건서비스</a></p>
</div></footer>
<nav class="callbar" aria-label="빠른 상담"><a href="tel:{C["TEL"]}">전화 상담 {C["PHONE"]}</a><a href="{C["KAKAO"]}" target="_blank" rel="noopener">카톡 사진 상담</a></nav>
{TRACK}
</body>
</html>
'''


def crumb(items, depth):
    up = "../" * depth
    parts = [f'<a href="{up}">홈</a>'] + [f'<a href="{up}{u}">{H.escape(t)}</a>' if u is not None else H.escape(t) for t, u in items]
    return '  <p class="crumb">' + " › ".join(parts) + "</p>\n"


def crumb_ld(items):
    s = C["SITE"]
    el = [{"@type": "ListItem", "position": 1, "name": "그릿서비스", "item": s}]
    el += [{"@type": "ListItem", "position": i + 2, "name": t, "item": s + u} for i, (t, u) in enumerate(items)]
    return {"@type": "BreadcrumbList", "itemListElement": el}


# ---------- 사례 ----------
DOMESTIC = {"현대", "기아", "제네시스", "르노", "르노코리아", "쌍용", "KG모빌리티", "쉐보레", "한국GM"}


def load_cases(posts_dir):
    out = []
    for f in sorted(posts_dir.glob("*.yaml")):
        p = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        if p.get("draft"):
            continue
        out.append(p)
    return sorted(out, key=lambda p: str(p.get("date")), reverse=True)


def case_cards(cases, depth, limit=6):
    up = "../" * depth
    rows = []
    for p in cases[:limit]:
        summ = p.get("description") or p.get("summary") or ""
        rows.append(f'    <li><a href="{up}cases/{p["slug"]}/">{H.escape(p["title"])}</a><p>{H.escape(summ)}</p></li>')
    return '  <ul class="card-list">\n' + "\n".join(rows) + "\n  </ul>\n"


# ---------- 질문 ----------
NATURAL = re.compile(r"(\?|요|까|줘|해|돼|야|어|지|나|니|가|래|죠|는데|할까|될까|다)$")


def is_natural(q):
    return bool(NATURAL.search(q.strip()))


def faq_block(pairs, depth):
    rows = []
    for q, a in pairs:
        rows.append(f'  <details><summary>{H.escape(q)}</summary><p>{linkify(H.escape(a))}</p></details>')
    return "\n".join(rows) + "\n"


# ---------- 서비스 상세 ----------
SERVICE_DEFS = [
    # slug, 이름, H1, title(40자 이내), 설명(80자 이내), 질문 분류, 사례 고르는 방법, 작업 범위, 진행 순서
    ("accident-repair/", "사고수리", "파주 교하 자동차 사고수리", "파주 사고수리 공업사 | 그릿서비스",
     "파주 교하 그릿서비스 사고수리: 파손 진단, 부품 교환, 판금·도색, 출고 점검. 국산차·수입차. 상담 1577-0412.",
     "사고수리", lambda p: p.get("category") == "accident",
     ["파손 진단: 부딪힌 부위와 그 주변까지 손상 범위를 확인합니다.", "부품 교환: 복원이 어려운 부품은 교환합니다.",
      "판금·도색: 찌그러진 면을 판금으로 펴고 원래 색에 맞춰 조색·도색합니다.", "출고 점검: 단차, 색 경계, 작동 상태를 확인한 뒤 출고합니다."]),
    ("painting/", "판금·도색", "파주 판금·도색", "파주 판금도색 공업사 | 그릿서비스",
     "찌그러짐·긁힘·문콕 판금 복원과 부분·전체 도색, 원래 색에 맞춘 조색. 파주 교하 그릿서비스.",
     "판금·도색", lambda p: p.get("category") == "painting" or "도색" in p.get("title", ""),
     ["판금 복원: 찌그러진 면과 라인을 판금으로 다시 잡습니다.", "하지작업: 연마·퍼티·프라이머로 도장 바탕을 만듭니다.",
      "조색: 차량 원래 색에 맞춰 색을 만듭니다.", "부분·전체 도색: 손상 범위에 맞춰 도색 범위를 정합니다."]),
    ("insurance-repair/", "보험수리", "파주 자동차 보험수리", "파주 보험수리 공업사 | 그릿서비스",
     "자차·대물 보험 사고 접수부터 보험사 협의, 수리, 출고까지. 파주 교하 공업사 그릿서비스.",
     "보험수리", lambda p: p.get("category") in ("accident", "painting"),
     ["보험사 사고 접수: 고객이 보험사에 사고를 접수하고 접수번호를 받습니다.", "입고·진단: 차량을 확인하고 손상 범위를 정리합니다.",
      "보험사 협의: 수리 범위를 보험사와 협의합니다.", "수리·출고: 협의된 범위로 수리하고 점검 후 출고합니다."]),
    ("certified-repair/", "중고차 성능보증수리", "파주 중고차 성능보증수리", "파주 중고차 성능보증수리 | 그릿서비스",
     "중고차 성능·상태점검 책임보험(성능보증보험) 수리: 진단, 보험 접수, 수리까지. 파주 그릿서비스.",
     "중고차 성능보증수리", lambda p: p.get("category") == "warranty",
     ["진단: 성능·상태점검기록부와 다른 고장인지 확인합니다.", "보험 접수: 성능·상태점검 책임보험 접수를 돕습니다.",
      "수리: 보험 처리 범위가 확인된 작업을 진행합니다.", "출고: 수리 내용을 설명하고 출고합니다."]),
    ("imported-cars/", "수입차 수리", "파주 수입차 사고수리·정비", "파주 수입차 수리·정비 | 그릿서비스",
     "벤츠·BMW·아우디·테슬라 등 수입차 사고수리, 판금·도색, 정비. 파주 교하 그릿서비스 실제 사례.",
     "차종·수입차", lambda p: (p.get("car") or {}).get("brand") not in DOMESTIC,
     ["사고수리·판금·도색: 수입차도 같은 순서로 진단, 복원, 도색, 점검합니다.", "정비: 엔진오일, 브레이크, 냉각·누유 점검 등.",
      "마세라티·페라리: 그룹사 로건서비스(loganservice.co.kr)가 전문으로 정비합니다."]),
    ("maintenance/", "자동차정비", "파주 자동차정비·카센터", "파주 자동차정비·카센터 | 그릿서비스",
     "엔진오일, 브레이크, 배터리, 타이어, 경고등 점검 등 국산차·수입차 정비. 파주 교하 그릿서비스.",
     "자동차정비", lambda p: p.get("category") == "maintenance",
     ["소모품 정비: 엔진오일, 브레이크 패드·디스크, 배터리, 타이어.", "점검: 경고등, 누유, 냉각수, 하체 소음.",
      "수리: 점검 결과를 설명하고 동의하신 작업만 진행합니다."]),
    ("exterior-care/", "외형관리·PPF", "파주 자동차 외형관리·PPF", "파주 광택·코팅·PPF 외형관리 | 그릿서비스",
     "광택, 코팅, PPF 보호필름, 프리미엄 세차. 파주 교하 그릿서비스 자동차 외형관리 상담 1577-0412.",
     "외형관리·PPF·세차", lambda p: p.get("category") == "exterior",
     ["광택: 도장면의 잔 스크래치와 얼룩을 연마해 윤기를 살립니다.", "코팅: 광택 뒤 도장 위에 보호층을 입힙니다.",
      "PPF: 투명 보호필름으로 돌튐·잔흠집을 막습니다. 부분 시공도 상담합니다.", "프리미엄 세차: 도장면 손상을 줄이는 방식으로 세차합니다."]),
]
SERVICE_PAGES = [(s[0], s[1]) for s in SERVICE_DEFS]
LEADS = {
    "accident-repair/": "국산차·수입차 사고 차량을 파손 진단, 부품 교환, 판금·도색, 출고 점검 순서로 한 공업사에서 수리합니다.",
    "painting/": "찌그러짐·긁힘·문콕을 판금으로 복원하고, 원래 색에 맞춰 조색한 뒤 부분 또는 전체 도색합니다.",
    "insurance-repair/": "자차·대물 보험 사고를 접수번호로 연결해 보험사와 수리 범위를 협의하고 수리·출고까지 진행합니다.",
    "certified-repair/": "중고차를 산 뒤 성능·상태점검기록부와 다른 고장이 나오면 성능·상태점검 책임보험으로 진단·접수·수리를 진행합니다.",
    "imported-cars/": "벤츠·BMW·아우디·테슬라 등 수입차의 사고수리, 판금·도색, 정비를 합니다.",
    "maintenance/": "엔진오일, 브레이크, 배터리, 타이어, 경고등 점검 등 국산차·수입차 정비를 하는 카센터 역할도 합니다.",
    "exterior-care/": "광택, 코팅, PPF 보호필름, 프리미엄 세차로 도장면을 보호하고 외관을 관리합니다.",
}


def build_services(OUT, items, cases):
    s = C["SITE"]
    for slug, name, h1, title, desc, cat, pick, scope, *_ in SERVICE_DEFS:
        url = s + slug
        qs = [(q, a) for c, _, q, a in items if c == cat and is_natural(q)][:6]
        if len(qs) < 3:
            qs = [(q, a) for c, _, q, a in items if c == cat][:6]
        mine = [p for p in cases if pick(p)]
        ld = {"@context": "https://schema.org", "@graph": [
            {"@type": "Service", "@id": url + "#service", "name": name, "serviceType": name, "url": url, "description": desc,
             "provider": {"@id": s + "#grit-service"}, "areaServed": ["파주", "교하", "운정", "일산", "고양", "김포"]},
            {"@type": "WebPage", "@id": url, "url": url, "name": title, "description": desc, "inLanguage": "ko-KR",
             "isPartOf": {"@id": s + "#website"}, "about": {"@id": url + "#service"}, "dateModified": C["TODAY"]},
            crumb_ld([(name, slug)])]}
        others = " · ".join(f'<a href="../{u}">{t}</a>' for u, t in SERVICE_PAGES if u != slug)
        body = crumb([(name, None)], 1)
        body += f"  <h1>{H.escape(h1)}</h1>\n"
        body += f'  <p class="lead">그릿서비스는 경기도 파주시 교하에 있는 자동차 공업사입니다. {H.escape(LEADS[slug])} 파손이나 증상 사진을 카카오톡으로 보내 주시면 필요한 작업과 범위를 먼저 안내합니다.</p>\n'
        body += '  <section id="scope">\n  <h2>작업 범위</h2>\n  <ul>\n' + "".join(f"    <li>{linkify(H.escape(x))}</li>\n" for x in scope) + "  </ul>\n  </section>\n"
        body += f'''  <section id="steps">
  <h2>진행 순서</h2>
  <ol class="steps">
    <li><strong>사진 상담</strong>: 카카오톡이나 전화({C["PHONE"]}, 24시간)로 차량 상태를 알려 주세요.</li>
    <li><strong>입고·진단</strong>: 평일 09:00~18:00 입고. 직접 오기 어려우면 탁송으로 입고할 수 있습니다.</li>
    <li><strong>견적 안내</strong>: 항목별 견적을 먼저 드리고, 동의하신 작업만 진행합니다.</li>
    <li><strong>작업·출고</strong>: 작업 후 점검하고 출고합니다.</li>
  </ol>
  </section>
'''
        if mine:
            body += f'  <section id="cases">\n  <h2>{H.escape(name)} 실제 사례</h2>\n  <p>그릿서비스에 입고된 차량의 실제 작업 기록입니다.</p>\n' + case_cards(mine, 1) + '  <p class="more"><a href="../cases/">수리사례 전체 보기 →</a></p>\n  </section>\n'
        elif slug == "exterior-care/":
            body += f'  <section id="cases">\n  <h2>작업 사진</h2>\n  <p>외형관리 작업 사진은 <a href="{C["INSTA"]}" target="_blank" rel="noopener">인스타그램 @grit_service</a>와 <a href="{C["BLOG"]}" target="_blank" rel="noopener">네이버 블로그</a>에서 볼 수 있습니다.</p>\n  </section>\n'
        body += f'  <section id="faq">\n  <h2>{H.escape(name)} 자주 묻는 질문</h2>\n' + faq_block(qs, 1) + '  <p class="more"><a href="../faq/">자주 묻는 질문 전체 보기 →</a></p>\n  </section>\n'
        body += f'  <section id="others">\n  <h2>다른 서비스</h2>\n  <p>{others}</p>\n  </section>\n'
        d = OUT / slug
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(head(title, desc, url, 1, ld) + body + foot(1))


def build_area(OUT, items, cases):
    s = C["SITE"]
    url = s + "area/"
    title = "그릿서비스 오시는 길·서비스 지역 | 파주 교하"
    desc = "파주 교하로 1312-53 그릿서비스 위치, 운정·일산·김포·고양에서 오는 방법, 탁송 입고 안내."
    qs = [(q, a) for c, _, q, a in items if c in ("지역 추천", "탁송") and is_natural(q)]
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "WebPage", "@id": url, "url": url, "name": title, "description": desc, "inLanguage": "ko-KR",
         "isPartOf": {"@id": s + "#website"}, "about": {"@id": s + "#grit-service"}, "dateModified": C["TODAY"]},
        crumb_ld([("오시는 길", "area/")])]}
    body = crumb([("오시는 길", None)], 1)
    body += "  <h1>그릿서비스 오시는 길·서비스 지역</h1>\n"
    body += f'  <p class="lead">그릿서비스는 경기도 파주시 교하동에 있는 자동차 공업사입니다. 파주(교하·운정·금촌·문산·탄현)와 가까운 일산·고양·김포에서도 이용할 수 있고, 직접 오기 어려우면 탁송으로 입고할 수 있습니다.</p>\n'
    body += f'''  <section id="where">
  <h2>위치와 운영 시간</h2>
  <dl class="info">
    <dt>주소</dt><dd>{C["ADDR_FULL"]}</dd>
    <dt>지도</dt><dd><a href="{C["MAP"]}" target="_blank" rel="noopener">네이버 지도에서 그릿서비스 보기</a> · <a href="{C["GMAP"]}" target="_blank" rel="noopener">구글 지도</a></dd>
    <dt>입고·작업</dt><dd>평일 09:00~18:00</dd>
    <dt>전화 상담</dt><dd><a href="tel:{C["TEL"]}">{C["PHONE"]}</a> (24시간)</dd>
    <dt>카카오톡</dt><dd><a href="{C["KAKAO"]}" target="_blank" rel="noopener">그릿서비스 채널로 사진 보내기</a></dd>
  </dl>
  </section>
  <section id="areas">
  <h2>지역별 안내</h2>
  <h3>파주 교하·운정·금촌·문산·탄현</h3>
  <p>같은 파주시 안이라 직접 입고하기 편합니다. 네이버 지도에서 '그릿서비스'를 검색해 오시면 됩니다.</p>
  <h3>일산·고양</h3>
  <p>파주 교하와 가까운 지역입니다. 직접 입고하거나 탁송으로 맡길 수 있습니다.</p>
  <h3>김포·양주·서울 은평</h3>
  <p>탁송으로 입고·출고를 상담할 수 있습니다. 차량 위치와 원하는 일정을 알려 주세요.</p>
  <h3>그 밖의 지역</h3>
  <p>탁송은 전국 가능하며, 비용은 차량 상태와 위치를 확인한 뒤 안내합니다.</p>
  </section>
'''
    if cases:
        body += '  <section id="cases">\n  <h2>최근 수리사례</h2>\n' + case_cards(cases, 1, 4) + '  <p class="more"><a href="../cases/">수리사례 전체 보기 →</a></p>\n  </section>\n'
    body += '  <section id="faq">\n  <h2>지역·탁송 자주 묻는 질문</h2>\n' + faq_block(qs[:10], 1) + "  </section>\n"
    d = OUT / "area"
    d.mkdir(parents=True, exist_ok=True)
    (d / "index.php").write_text(head(title, desc, url, 1, ld) + body + foot(1))


def build_privacy(OUT):
    s = C["SITE"]
    url = s + "privacy/"
    title = "개인정보처리방침 | 그릿서비스"
    desc = "그릿서비스 개인정보처리방침: 처리 항목·목적, 보유기간, 파기, 제3자 제공·위탁, 쿠키·분석도구, 권리 행사 방법."
    co, ceo, ph = C["COMPANY"], C["CEO"], C["PHONE"]
    body = crumb([("개인정보처리방침", None)], 1)
    body += f'''  <h1>개인정보처리방침</h1>
  <p>{co}(이하 "회사")는 「개인정보 보호법」 제30조에 따라 정보주체의 개인정보를 보호하고 관련 고충을 빠르게 처리하기 위해 다음과 같이 개인정보처리방침을 둡니다.</p>
  <h2>1. 처리하는 개인정보 항목과 목적</h2>
  <table><tr><th>구분</th><th>항목</th><th>목적</th></tr>
  <tr><td>전화·카카오톡 상담</td><td>이름, 연락처, 차량번호·차종, 고객이 보낸 차량 사진</td><td>상담 응대, 견적 안내</td></tr>
  <tr><td>차량 입고·수리</td><td>이름, 연락처, 차량번호·차종, 차대번호, 보험 접수번호(보험수리 시)</td><td>수리 진행, 출고 연락, 보험 처리, 대금 정산</td></tr>
  <tr><td>탁송</td><td>이름, 연락처, 차량 위치(출발·도착지)</td><td>차량 탁송</td></tr>
  <tr><td>홈페이지 방문</td><td>쿠키, 접속 기록(방문 페이지, 기기·브라우저 정보)</td><td>방문 통계, 상담 버튼 이용 분석</td></tr>
  </table>
  <h2>2. 보유·이용 기간</h2>
  <p>목적을 이루면 지체 없이 파기합니다. 다만 관계 법령에 따라 보관해야 하는 정보는 그 기간 동안 보관합니다.</p>
  <ul><li>계약 또는 청약철회, 대금 결제 및 재화 등의 공급에 관한 기록: 5년(전자상거래 등에서의 소비자보호에 관한 법률)</li>
  <li>세금계산서 등 거래 증빙: 5년(국세기본법)</li>
  </ul>
  <h2>3. 파기 절차와 방법</h2>
  <p>보유 기간이 지나거나 목적을 이룬 개인정보는 지체 없이 파기합니다. 전자 파일은 복구할 수 없는 방법으로 지우고, 종이 문서는 분쇄하거나 소각합니다.</p>
  <h2>4. 제3자 제공</h2>
  <p>회사는 정보주체가 동의했거나 법령에 근거가 있는 경우에만 개인정보를 제3자에게 제공합니다.</p>
  <table><tr><th>받는 자</th><th>항목</th><th>목적</th><th>보유 기간</th></tr>
  <tr><td>고객이 사고 접수한 보험사</td><td>이름, 연락처, 차량번호, 수리 내역</td><td>보험 처리</td><td>보험사의 보유 기간에 따름</td></tr>
  </table>
  <h2>5. 처리 위탁</h2>
  <p>회사는 서비스 제공을 위해 아래 업무를 위탁할 수 있으며, 위탁받은 자가 개인정보를 안전하게 처리하도록 관리합니다.</p>
  <table><tr><th>수탁자</th><th>위탁 업무</th></tr>
  <tr><td>차량 탁송 업체(이용 시 안내)</td><td>차량 탁송</td></tr>
  <tr><td>Google LLC</td><td>홈페이지 방문 통계(구글 애널리틱스)</td></tr>
  </table>
  <h2>6. 개인정보의 국외 이전</h2>
  <p>홈페이지 방문 통계를 위해 구글 애널리틱스를 씁니다. 방문 시 쿠키와 접속 기록이 Google LLC(미국)의 서버로 전송·저장됩니다. 이전 시기는 홈페이지 방문 시점이며, 보유 기간은 Google의 정책에 따릅니다. 원하지 않으면 아래 7번의 방법으로 거부할 수 있습니다.</p>
  <h2>7. 쿠키 등 자동 수집 장치와 거부 방법</h2>
  <p>홈페이지는 방문 통계와 상담 버튼(전화·카카오톡) 이용을 파악하려고 쿠키를 씁니다. 브라우저 설정에서 쿠키 저장을 거부하거나 지울 수 있고, Google 애널리틱스 차단 부가기능(tools.google.com/dlpage/gaoptout)을 설치해 수집을 거부할 수 있습니다. 쿠키를 거부해도 상담·수리 이용에는 지장이 없습니다.</p>
  <h2>8. 안전성 확보 조치</h2>
  <p>개인정보를 다루는 사람을 최소한으로 정하고, 문서와 전자 파일이 외부에 노출되지 않도록 보관합니다.</p>
  <h2>9. 정보주체의 권리와 행사 방법</h2>
  <p>정보주체는 언제든지 개인정보 열람, 정정·삭제, 처리 정지, 동의 철회를 요청할 수 있습니다. 전화({ph})나 방문으로 요청하시면 지체 없이 처리합니다.</p>
  <h2>10. 개인정보 보호책임자</h2>
  <p>{co} 대표 {ceo} · 전화 {ph} · {C["ADDR_FULL"]}</p>
  <h2>11. 권익침해 구제 방법</h2>
  <p>개인정보 침해에 대한 상담이나 분쟁 해결이 필요하면 아래 기관에 문의할 수 있습니다.</p>
  <ul><li>개인정보분쟁조정위원회: 1833-6972 (www.kopico.go.kr)</li><li>개인정보침해신고센터: 118 (privacy.kisa.or.kr)</li><li>대검찰청: 1301 (www.spo.go.kr)</li><li>경찰청: 182 (ecrm.police.go.kr)</li></ul>
  <h2>12. 시행일과 변경 이력</h2>
  <p>이 방침은 {C["PRIVACY_DATE"]}부터 적용합니다. 이전 방침: 2026-10-22 시행(항목·목적, 보유기간, 제3자 제공, 권리, 책임자).</p>
'''
    d = OUT / "privacy"
    d.mkdir(parents=True, exist_ok=True)
    (d / "index.php").write_text(head(title, desc, url, 1, {"@context": "https://schema.org", "@graph": [crumb_ld([("개인정보처리방침", "privacy/")])]}) + body + foot(1))


def build_404(OUT):
    """없는 주소로 왔을 때 보여 줄 페이지(.htaccess 의 ErrorDocument 404 /404.html). 절대 주소로 링크(어느 폴더에서 열려도 깨지지 않게)."""
    s = C["SITE"]
    html = head("페이지를 찾을 수 없습니다 | 그릿서비스", "주소가 바뀌었거나 없는 페이지입니다. 그릿서비스 홈, 수리사례, 자주 묻는 질문에서 찾아 주세요.", s + "404.html", 0)
    html = html.replace('href="assets/', f'href="{s}assets/').replace('src="assets/', f'src="{s}assets/')
    html = re.sub(r'(<nav aria-label="주요 메뉴">.*?</nav>)', lambda m: re.sub(r'href="(?!tel:|https?:)([^"]*)"', lambda n: f'href="{s}{n.group(1)}"', m.group(1)), html, flags=re.S)
    body = f'''  <h1>페이지를 찾을 수 없습니다</h1>
  <p class="lead">주소가 바뀌었거나 없는 페이지입니다. 아래에서 찾아 주세요.</p>
  <ul class="card-list"><li><a href="{s}">그릿서비스 홈</a></li><li><a href="{s}cases/">수리사례</a></li><li><a href="{s}faq/">자주 묻는 질문</a></li><li><a href="{s}area/">오시는 길</a></li></ul>
'''
    f = foot(0).replace('href="./', f'href="{s}')
    f = re.sub(r'href="(?!tel:|https?:)([^"]*)"', lambda n: f'href="{s}{n.group(1)}"', f)
    (OUT / "404.html").write_text(html + body + f)
