"""로건서비스 index.php(올려주신 원본)를 그릿서비스용으로 변환: 같은 레이아웃·CSS, 내용·색상·사진만 교체."""
import pathlib, re, sys, json

HERE = pathlib.Path(__file__).parent
OUT = pathlib.Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)

# ---------- 그릿서비스 정보 ([대괄호] = 아직 모름) ----------
SITE = "https://gritservice.co.kr/"
PHONE = "1577-0412"; TEL = "15770412"
ADDR = "경기도 파주시 교하로 1312-53"
MAP = "https://map.naver.com/p/search/%EA%B2%BD%EA%B8%B0%EB%8F%84%20%ED%8C%8C%EC%A3%BC%EC%8B%9C%20%EA%B5%90%ED%95%98%EB%A1%9C%201312-53"
BLOG = "https://blog.naver.com/grit_service"
INSTA_ID = "grit_service"; INSTA = "https://www.instagram.com/grit_service/"
KAKAO = "https://pf.kakao.com/_UExgxaX"
COMPANY = "(주)그릿서비스"
CEO = "지철구"; BIZNO = "513-86-04243"; ADDR_FULL = "경기도 파주시 교하로 1312-53, 1동 1층"
LOGAN = "https://loganservice.co.kr/"
GA4 = "G-J953M2539G"  # 구글 애널리틱스 측정 ID (2026-10-20)
TODAY = "2026-10-22"
TITLE = "파주 사고수리·판금도색 공업사 그릿서비스 | 자동차정비·외형관리·중고차 성능보증수리"
DESC = "파주 교하 자동차 공업사 그릿서비스. 국산차·수입차 사고수리, 판금·도색, 보험수리, 중고차 성능보증수리, 자동차정비, 광택·PPF 외형관리, 탁송까지. 전화 상담 24시간 1577-0412(작업 평일 09~18시)."

# ---------- CSS: 로건 원본 그대로, 색만 와인 → 그릿 블루 / 따뜻한 회색 → 차가운 회색 ----------
css = (HERE / "grit2-style.css").read_text()
swaps = [
    ("--wine2", "--brand2"), ("--wine", "--brand"),
    ("--brand:#c42739;", "--brand:#004a9f;"), ("--brand2:#c42739;", "--brand2:#004a9f;"),
    ("--ivory:#f6f2ec;", "--ivory:#eef2f8;"), ("--paper:#fcfbf8;", "--paper:#fbfcfe;"), ("--muted:#8b877f;", "--muted:#7f8794;"),
    ("rgba(255,252,248,", "rgba(251,252,254,"), ("rgba(252,251,248,", "rgba(251,252,254,"),
    ("rgba(122,26,40,.10)", "rgba(0,74,159,.10)"), ("rgba(91,17,26,.045)", "rgba(20,50,140,.05)"),
    ('content:"LOGAN"', 'content:"GRIT"'), ("rgba(75,44,40,.10)", "rgba(30,45,80,.10)"),
    ("assets/hero-main.webp", "assets/grit-hero-main.webp"),
    # 속도: 모바일 히어로는 828px 작은 사진
    ('url("assets/grit-hero-main.webp") center 66px', 'url("assets/grit-hero-main-828.webp") center 66px'),
    ('.focus.mas{', '.focus.rep{'), ('.focus.fer{', '.focus.care{'), ('.focus.fer{background-position', '.focus.care{background-position'),
    ("assets/maserati-service-02.webp", "assets/grit-repair.webp"), ("assets/logan-workshop-01.webp", "assets/grit-care.webp"),
    ("#f7f4ef", "#f4f6fa"), ("#efeae3", "#eaeff6"), ("#f2ece8", "#edf1f7"), ("#f3f1ed", "#f2f4f8"), ("#f6f2ec", "#eef2f8"),
    ("#e1ddd6", "#dde2ea"), ("#ddd7cf", "#d9dfe8"), ("#cfc9c1", "#c9d0db"), ("#cfcac1", "#c9d0db"), ("#d8d0c9", "#d2d9e3"), ("#eee8e1", "#e6eaf0"),
    ("#fff7f7", "#f3f6ff"), ("#eadedf", "#dfe5f3"), ("#6c5c5f", "#5a6274"), ("#bcaeb0", "#aab4c8"),
    ("#a7a19a", "#9aa2ae"), ("#847d76", "#7b8390"), ("#7c746d", "#737b88"), ("#7a746d", "#727a87"), ("#8d877f", "#858d99"),
    ("#6f6a64", "#666d78"), ("#615d57", "#5b616b"), ("#67615b", "#5f6670"), ("#928c85", "#89919c"), ("#6d665f", "#646b76"),
    ("#625d57", "#5c626c"), ("#6b645e", "#646a74"), ("#8d8279", "#858c97"), ("#4f4a45", "#4a4f57"), ("#3b3935", "#383b40"),
    ("#c8c2bc", "#c3c8d0"), ("#b7ada4", "#a9b1bd"), ("#bdb7b1", "#b8bec7"), ("#c9c4bd", "#c4c9d1"),
]
for a, b in swaps:
    css = css.replace(a, b)
# 그룹 카드: 그릿 카드가 강조(파란 테두리)인 건 원본과 같고, 로건 카드는 로건 와인색으로 살짝 강조
css = css.replace("</style>", "    .group-card.logan{border-color:rgba(196,39,57,.20)}\n    /* 상단 메뉴: 검정 바탕 + 흰 글씨 */\n    header{background:rgba(0,0,0,.94);border-bottom-color:rgba(255,255,255,.10)}\n    .nav,.brand,.menu-btn{color:#fff}\n    .brand small{color:#a3abb8}\n    .navlinks{color:#fff}\n    .navlinks a:hover{color:#7fa6e6}\n    .mobile{background:#000;border-top-color:rgba(255,255,255,.10)}\n    .mobile a{color:#fff;border-bottom-color:rgba(255,255,255,.08)}\n    .mobile a:active{background:#1a1a1a}\n    .work-m{color:#fff;border-color:rgba(255,255,255,.35)}\n    .brand-copy{white-space:nowrap}\n    @media(max-width:430px){.work-m{font-size:11px;padding:5px 8px;margin-right:8px}.brand small{display:none}}\n    h1,h2,h3,.display,.lead{word-break:keep-all}\n    .callbar{display:none}\n    @media(max-width:760px){.callbar{display:grid;grid-template-columns:1fr 1fr;position:fixed;left:0;right:0;bottom:0;z-index:60;box-shadow:0 -4px 16px rgba(0,0,0,.15)}.callbar a{display:flex;align-items:center;justify-content:center;min-height:54px;font-weight:700;font-size:15px;color:#fff;background:#004a9f}.callbar a+a{background:#fee500;color:#191919}body{padding-bottom:54px}}\n    .contact-brand{display:flex;align-items:center;gap:16px;margin-bottom:6px}\n    .contact-brand-copy{display:grid;font-size:12px;letter-spacing:.1em;color:#646a74}\n    .service-links{margin-top:28px;font-size:15px;color:#c9d0db;word-break:keep-all}.service-links a{color:#fff;text-decoration:underline;text-underline-offset:3px}\n    .footer-links a{text-decoration:underline;text-underline-offset:3px}\n    /* 속도: 모바일은 750px 사진 */\n    @media(max-width:620px){.focus.rep{background:linear-gradient(180deg,rgba(0,0,0,.08),rgba(0,0,0,.86)),url(\"assets/grit-repair-750.webp\") center/cover no-repeat}.focus.care{background:linear-gradient(180deg,rgba(0,0,0,.10),rgba(0,0,0,.88)),url(\"assets/grit-care-750.webp\") center 35%/cover no-repeat}}\n  </style>")
leftover = re.findall(r"#c42739|LOGAN|maserati|logan-workshop|#f7f4ef", css)
assert not leftover, leftover

SERVICES = [
    ("01 / ACCIDENT REPAIR", "사고수리", "접촉사고부터 대형 사고까지 파손 진단, 부품 교환, 판금·도색, 출고 점검을 한 공업사에서 진행합니다."),
    ("02 / BODY &amp; PAINT", "판금·도색", "찌그러짐·긁힘 판금 복원과 부분·전체 도색, 원래 색에 맞춘 조색까지 진행합니다."),
    ("03 / INSURANCE REPAIR", "보험수리", "자차·대물 보험 사고 접수 후 보험사 협의, 수리, 출고까지 필요한 과정을 연결합니다."),
    ("04 / USED CAR WARRANTY", "중고차 성능보증수리", "중고차 성능·상태점검 책임보험(성능보증보험) 수리를 진단, 보험 접수, 수리까지 처리합니다."),
    ("05 / MAINTENANCE", "자동차정비", "엔진오일, 브레이크, 배터리, 타이어, 경고등 점검 등 국산차·수입차 전 차종 정비."),
    ("06 / EXTERIOR CARE", "자동차 외형관리", "광택, 코팅 등 차량 외관을 새 차에 가깝게 관리합니다."),
    ("07 / PPF &amp; WASH", "PPF·프리미엄 세차", "PPF 보호필름 시공과 도장면 손상을 줄이는 프리미엄 세차로 차량을 보호합니다."),
    ("08 / DELIVERY", "탁송", "입고와 출고가 어려운 고객을 위해 차량 탁송을 지원합니다."),
]
FAQ = [
    ("파주에서 사고수리 잘하는 공업사를 찾고 있어요.", f"그릿서비스는 파주 교하에 있는 자동차 공업사로, 사고수리와 판금·도색, 보험수리를 직접 진행합니다. 파손 부위 사진을 보내주시면 수리 범위와 예상 비용을 먼저 안내합니다."),
    ("어떤 차량을 수리하나요?", "국산차와 수입차 등 전 차종의 사고수리, 판금·도색, 자동차정비를 진행합니다."),
    ("판금 도색 비용은 어떻게 정해지나요?", "파손 범위, 패널 수, 도색 범위(부분·전체)에 따라 달라집니다. 차량을 확인한 뒤 항목별 견적을 먼저 드리고 동의하신 작업만 진행합니다."),
    ("보험수리도 가능한가요?", "가능합니다. 자차·대물 보험 모두 처리하며, 보험사 사고 접수번호를 알려주시면 보험사와 수리 범위를 협의하고 수리를 진행합니다."),
    ("중고차 성능보증수리도 하나요?", "네. 중고차 구입 후 성능·상태점검 기록부와 다른 고장이 발견되면 성능·상태점검 책임보험(성능보증보험)으로 수리받을 수 있습니다. 그릿서비스에서 진단, 보험 접수, 수리까지 진행합니다. 보증 적용 여부는 차량과 점검 기록에 따라 확인이 필요합니다."),
    ("자동차 외형관리는 어떤 것을 하나요?", "광택, 코팅, PPF 보호필름, 프리미엄 세차 등 차량 외관 관리를 진행합니다."),
    ("사고가 났을 때 바로 연락해도 되나요?", f"네. 대표번호 {PHONE}로 24시간 전화 상담할 수 있습니다. 입고·작업은 평일 오전 9시~오후 6시이며, 차를 맡기기 어려우면 탁송도 이용할 수 있습니다."),
    ("로건서비스와는 어떤 관계인가요?", "로건서비스와 그릿서비스는 같은 그룹의 자동차 서비스 브랜드입니다. 로건서비스는 마세라티·페라리 전문, 그릿서비스는 전 차종 사고수리·정비·외형관리를 담당합니다."),
    ("그릿서비스 위치와 대표번호는 어떻게 되나요?", f"{ADDR_FULL}(교하동)에 위치하고 있으며 대표번호는 {PHONE}입니다. 운정, 일산, 김포에서도 가깝습니다."),
    ("그릿서비스 영업시간은 어떻게 되나요?", f"입고·작업은 평일 오전 9시부터 오후 6시까지입니다. 전화 상담은 대표번호 {PHONE}로 24시간 가능합니다."),
    ("상담은 어떤 방법으로 할 수 있나요?", f"대표전화 {PHONE}, 카카오 채널, 인스타그램, 네이버 블로그를 통해 상담할 수 있습니다."),
]

ld = {
    "@context": "https://schema.org",
    "@graph": [
        {
            "@type": ["AutoRepair", "AutoBodyShop"], "@id": SITE + "#grit-service", "url": SITE,
            "logo": {"@type": "ImageObject", "@id": SITE + "#logo", "url": SITE + "assets/grit-service-logo.png", "width": 387, "height": 384, "caption": "그릿서비스 로고"},
            "image": [SITE + "assets/grit-hero-main.webp", SITE + "assets/grit-repair.webp", SITE + "assets/grit-care.webp", SITE + "assets/grit-shop-night.webp"],
            "name": "그릿서비스", "alternateName": "GRIT SERVICE", "telephone": PHONE,
            "description": "그릿서비스는 파주 교하의 자동차 공업사로 전 차종 사고수리, 판금·도색, 보험수리, 중고차 성능보증수리, 자동차정비, 자동차 외형관리(광택·코팅·PPF·세차), 탁송을 제공합니다.",
            "address": {"@type": "PostalAddress", "streetAddress": "교하로 1312-53, 1동 1층", "addressLocality": "파주시", "addressRegion": "경기도", "addressCountry": "KR"},
            "areaServed": ["파주", "교하", "운정", "일산", "고양", "김포", "양주", "은평"],
            "knowsAbout": ["사고수리", "판금", "도색", "도장", "보험수리", "중고차 성능보증수리", "성능·상태점검 책임보험", "자동차정비", "자동차 외형관리", "광택", "코팅", "PPF", "세차", "탁송"],
            "hasOfferCatalog": {"@type": "OfferCatalog", "name": "그릿서비스 주요 서비스", "itemListElement": [
                {"@type": "Offer", "itemOffered": {"@type": "Service", "name": s[1].replace("&amp;", "&"), "serviceType": s[1].replace("&amp;", "&"), "description": s[2], "areaServed": "경기도 파주시", "provider": {"@id": SITE + "#grit-service"}}} for s in SERVICES]},
            "sameAs": [BLOG, INSTA, KAKAO],
            "legalName": COMPANY, "taxID": BIZNO, "foundingDate": "2026-09-01", "slogan": "기본이 가장 중요합니다.", "hasMap": MAP,
            "contactPoint": [{"@type": "ContactPoint", "telephone": "+82-1577-0412", "contactType": "customer service", "areaServed": "KR", "availableLanguage": ["Korean"], "description": "전화 상담 24시간 (입고·작업은 평일 09:00~18:00)", "hoursAvailable": {"@type": "OpeningHoursSpecification", "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"], "opens": "00:00", "closes": "23:59"}}],
            "founder": {"@type": "Person", "name": CEO}, "knowsLanguage": "ko", "mainEntityOfPage": {"@id": SITE + "#webpage"},
        },
        {"@type": "WebSite", "@id": SITE + "#website", "url": SITE, "name": "그릿서비스", "alternateName": "GRIT SERVICE", "inLanguage": "ko-KR", "publisher": {"@id": SITE + "#grit-service"}},
        {"@type": "WebPage", "@id": SITE + "#webpage", "url": SITE, "name": TITLE,
         "description": DESC,
         "inLanguage": "ko-KR", "isPartOf": {"@id": SITE + "#website"}, "about": {"@id": SITE + "#grit-service"}, "dateModified": TODAY,
         "primaryImageOfPage": {"@type": "ImageObject", "url": SITE + "assets/grit-hero-main.webp"},
         "speakable": {"@type": "SpeakableSpecification", "cssSelector": ["h1", ".hero .lead", ".intro p"]},
         "mainEntity": {"@id": SITE + "#grit-service"}, "mentions": [{"@id": SITE + "#logan-service"}], "breadcrumb": {"@id": SITE + "#breadcrumb"}},
        {"@type": "AutoRepair", "@id": SITE + "#logan-service", "name": "로건서비스", "alternateName": "LOGAN SERVICE", "url": LOGAN,
         "logo": LOGAN + "assets/logan-service-logo.png", "description": "2016년부터 마세라티와 페라리에 집중한 전문 자동차 서비스. 진단·정비·사고수리·보험수리·성능보증수리."},
        {"@type": "BreadcrumbList", "@id": SITE + "#breadcrumb", "itemListElement": [{"@type": "ListItem", "position": 1, "name": "그릿서비스", "item": SITE}]},
        {"@type": "FAQPage", "@id": SITE + "#faq", "url": SITE + "#faq", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ]},
    ],
}

# 사장님이 확인해 주신 값만 채운다. 비어 있으면 JSON-LD 에 넣지 않는다(지어내지 않음).
# HOURS 예: [{"days": ["Monday", "Tuesday"], "opens": "09:00", "closes": "18:00"}]  (쉬는 날은 넣지 않음)
_ALL = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
# (2026-10-21 "24시간 운영" → 2026-10-22 사장님 정정: 입고·작업 평일 09~18시, 전화 상담만 24시간)
HOURS = [{"days": _ALL[:5], "opens": "09:00", "closes": "18:00"}]  # 2026-10-22 사장님: 작업 평일 9~18시, 전화 상담만 24시간
GEO = (37.748557, 126.739341)            # 예: (37.7xxxxx, 126.7xxxxx)  구글 지도에서 가게 위치를 우클릭해 복사한 값
EXTRA_SAME_AS = ["https://map.naver.com/p/entry/place/2053438921",
                  "https://www.google.com/maps/place/%EA%B7%B8%EB%A6%BF%EC%84%9C%EB%B9%84%EC%8A%A4/data=!4m2!3m1!1s0x0:0x88345fd7d053df58"]    # 네이버 플레이스 공유 주소, 구글 지도/비즈니스 프로필 주소
_n = ld["@graph"][0]
if HOURS:
    _n["openingHoursSpecification"] = [{"@type": "OpeningHoursSpecification", "dayOfWeek": h["days"], "opens": h["opens"], "closes": h["closes"]} for h in HOURS]
if GEO:
    _n["geo"] = {"@type": "GeoCoordinates", "latitude": GEO[0], "longitude": GEO[1]}
if EXTRA_SAME_AS:
    _n["sameAs"] = _n["sameAs"] + [u for u in EXTRA_SAME_AS if u not in _n["sameAs"]]

WORKTABLE = "https://script.google.com/macros/s/AKfycbxdq7ZpcAp9qPwPiE8C0PRi3lLsgViflIPwh0JKx4BvGUVBkmF1sP4sl65BsvOke-xo/exec"  # 로건서비스 응대 매뉴얼
WT = f'<a href="{WORKTABLE}" target="_blank" rel="noopener nofollow">WORKTABLE</a>'
# ---------- 수리사례 /cases/ (글: ../cases-system/grit/posts/*.yaml, 약속: ../cases-system/SPEC.md) ----------
# 공개 글(draft 아님)이 1개 이상일 때만 메뉴·홈 섹션·sitemap 에 붙인다. GRIT_CASES_PREVIEW=1 이면 예시 글까지(미리보기용).
import os, subprocess
CASES = HERE.parent / "cases-system"
_cp = os.environ.get("GRIT_CASES_PREVIEW") == "1"
subprocess.run([sys.executable, str(CASES / "engine" / "make_cases.py"), str(CASES / "grit"), str(OUT), "--assets", str(HERE / "upload")]
               + (["--preview", "--copy-assets"] if _cp else []), check=True)
_home_cases = (OUT / "cases" / "home-section.html").read_text().strip() + "\n" if (OUT / "cases" / "home-section.html").exists() else ""
HAS_CASES = 'href="cases/' in _home_cases and "cases-card" in _home_cases
if not HAS_CASES:
    _home_cases = ""
    import shutil; shutil.rmtree(OUT / "cases", ignore_errors=True)
NAV = [("#about", "ABOUT"), ("#care", "REPAIR / CARE"), ("#service", "SERVICE")] + ([("cases/", "수리사례")] if HAS_CASES else []) + [("#works", "WORK"), ("#instagram", "INSTAGRAM"), ("#group", "GROUP"), ("#faq", "FAQ"), ("#contact", "CONTACT")]
nav = "\n".join(f'      <a href="{h}">{t}</a>' for h, t in NAV)
mnav = "\n".join(f'    <a href="{h}">{t}</a>' for h, t in NAV)
services = "\n".join(f'        <article class="service"><div class="num">{n}</div><h3>{t}</h3><p>{d}</p></article>' for n, t, d in SERVICES)
# 라이브 서버의 서비스 상세 페이지 5개 (홈·llms.txt 에서 링크)
SERVICE_PAGES = [("accident-repair/", "사고수리"), ("painting/", "판금·도색"), ("insurance-repair/", "보험수리"),
                 ("certified-repair/", "중고차 성능보증수리"), ("imported-cars/", "수입차 수리")]
service_links = " · ".join(f'<a href="{u}">{t}</a>' for u, t in SERVICE_PAGES)
# GEO 질문·답변 200개 (내용은 geo/geo_qa.py): 홈 FAQ 더보기 + faq/ 페이지 + llms-full.txt
sys.path.insert(0, str(HERE / "geo"))
import make_geo
geo_more = make_geo.index_more(SITE, PHONE, ADDR_FULL, KAKAO, BLOG, INSTA)
faq_html = "\n".join(f'        <details class="faq-item"{" open" if i == 0 else ""}><summary>{q}</summary><p>{a}</p></details>' for i, (q, a) in enumerate(FAQ))



html = f'''<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{TITLE}</title>
  <meta name="description" content="{DESC}" />
  <meta name="keywords" content="그릿서비스, 파주 사고수리, 파주 공업사, 파주 판금도색, 파주 판금도장, 파주 자동차정비, 파주 정비소, 파주 카센터, 파주 보험수리, 중고차 성능보증수리, 성능보증보험 수리, 파주 외형관리, 파주 광택, 파주 PPF, 파주 세차, 교하 공업사, 교하 사고수리, 운정 사고수리, 운정 판금도색, 운정 정비소" />
  <meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1" />
  <meta name="googlebot" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1" />
  <meta name="author" content="그릿서비스 GRIT SERVICE" />
  <meta name="application-name" content="그릿서비스" />
  <meta name="geo.region" content="KR-41" />
  <meta name="geo.placename" content="경기도 파주시" />
  <!-- 검색엔진 소유확인 코드: 발급받은 값으로 주석을 풀어 사용하세요 -->
  <!-- <meta name="google-site-verification" content="구글서치콘솔_코드" /> -->
  <meta name="naver-site-verification" content="a8e8cd270aae2495f2acadde3de5b7ce966b4a23" />
  <!-- <meta name="msvalidate.01" content="빙웹마스터도구_코드" /> -->
  <meta property="og:title" content="{TITLE}" />
  <meta property="og:description" content="{DESC}" />
  <meta property="og:type" content="website" />
  <meta property="og:site_name" content="GRIT SERVICE" />
  <link rel="canonical" href="{SITE}" />
  <link rel="alternate" hreflang="ko-KR" href="{SITE}" />
  <link rel="alternate" hreflang="x-default" href="{SITE}" />
  <link rel="alternate" type="text/markdown" title="그릿서비스 AI 요약 (llms.txt)" href="{SITE}llms.txt" />
  <link rel="sitemap" type="application/xml" href="{SITE}sitemap.xml" />
  <meta property="og:url" content="{SITE}" />
  <meta property="og:locale" content="ko_KR" />
  <meta property="og:image" content="{SITE}assets/og-image.jpg" />
  <meta property="og:image:type" content="image/jpeg" />
  <meta property="og:image:width" content="1200" />
  <meta property="og:image:height" content="630" />
  <meta property="og:image:alt" content="파주 교하 그릿서비스 자동차 공업사 외관" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{TITLE}" />
  <meta name="twitter:description" content="{DESC}" />
  <meta name="twitter:image" content="{SITE}assets/og-image.jpg" />
  <meta name="theme-color" content="#004a9f" />
  <link rel="icon" type="image/png" sizes="64x64" href="assets/favicon-64.png" />
  <link rel="apple-touch-icon" href="assets/favicon.png" />
  <link rel="preload" as="image" href="assets/grit-hero-main-828.webp" media="(max-width:620px)" fetchpriority="high" />
  <link rel="preload" as="image" href="assets/grit-hero-main.webp" media="(min-width:621px)" fetchpriority="high" />
  <!-- 방문자·광고 전환 분석: 발급받은 ID로 바꾸고 주석을 풀어 사용하세요 -->
  <!-- 구글 애널리틱스(GA4) / 구글 광고 (2026-10-20 사장님 발급) -->
  <script async src="https://www.googletagmanager.com/gtag/js?id={GA4}"></script>
  <script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag('js',new Date());gtag('config','{GA4}');</script>
  <!-- 네이버 애널리틱스 / 네이버 검색광고 전환추적(공통 스크립트)
  <script src="//wcs.naver.net/wcslog.js"></script>
  <script>if(!wcs_add)var wcs_add={{}};wcs_add["wa"]="네이버_공통키";if(!_nasa)var _nasa={{}};if(window.wcs){{wcs.inflow();wcs_do(_nasa);}}</script>
  -->
{css}
  <script type="application/ld+json">
{json.dumps(ld, ensure_ascii=False, indent=2)}
  </script>
</head>
<body>
<header>
  <div class="wrap nav">
    <a href="#top" class="brand"><img src="assets/grit-logo-192.webp" alt="GRIT SERVICE 로고" width="192" height="191" decoding="async"><span class="brand-copy">GRIT SERVICE<small>PREMIUM AUTOMOTIVE CARE</small></span></a>
    <nav class="navlinks" aria-label="주요 메뉴">
{nav}
    </nav>
    <a class="work-m" href="tel:{TEL}" data-track="call">전화</a>
    <button class="menu-btn" aria-label="메뉴" aria-expanded="false" onclick="var m=document.querySelector('.mobile');var o=m.classList.toggle('open');this.setAttribute('aria-expanded',o);this.textContent=o?'✕':'☰'">☰</button>
  </div>
  <nav class="mobile" aria-label="모바일 메뉴" onclick="if(event.target.tagName==='A'){{this.classList.remove('open');var b=document.querySelector('.menu-btn');b.textContent='☰';b.setAttribute('aria-expanded','false')}}">
{mnav}
  </nav>
</header>

<main id="top">
  <section class="hero">
    <div class="wrap hero-grid">
      <div>
        <div class="eyebrow">파주 교하 · 사고수리 · 판금도색 · 자동차정비</div>
        <h1 class="display">파주 사고수리,<br>기본이 가장 중요합니다.</h1>
        <p class="lead">그릿서비스는 파주 교하의 자동차 공업사입니다. 국산차·수입차 전 차종의 사고수리, 판금·도색, 보험수리, 중고차 성능보증수리, 자동차정비부터 광택·PPF 같은 자동차 외형관리까지 한 곳에서 해결합니다.</p>
        <div class="btns">
          <a class="btn primary" href="tel:{TEL}">{PHONE} 상담</a>
          <a class="btn" href="{KAKAO}" target="_blank" rel="noopener" data-track="kakao">카톡으로 사진 보내 상담</a>
        </div>
      </div>
      <div class="hero-card">
        <div class="eyebrow">Total automotive care</div>
        <div class="big">ALL CARS</div>
        <div class="label">국산차 · 수입차 전 차종</div>
        <div class="stats">
          <div class="stat"><strong>24H</strong><span>Consultation</span></div>
          <div class="stat"><strong>8</strong><span>Services</span></div>
          <div class="stat"><strong>파주</strong><span>Gyoha-ro</span></div>
        </div>
      </div>
    </div>
  </section>

  <section class="intro" id="about">
    <div class="wrap intro-grid">
      <div>
        <div class="eyebrow" style="color:#737b88">About Grit Service</div>
        <div class="quote">어떤 차든,<br>기본부터 제대로.</div>
      </div>
      <p>사고 차량 수리부터 매일 타는 차의 관리까지, 차에 필요한 일은 서로 이어져 있습니다. 파주 교하의 자동차 공업사 그릿서비스는 사고수리, 판금·도색, 보험수리, 중고차 성능보증수리, 자동차정비, 외형관리를 한 곳에서 맡아 입고부터 출고까지 하나의 기준으로 관리합니다. 화려한 말보다 기본에 충실한 작업, 그것이 그릿서비스가 지키는 원칙입니다.</p>
    </div>
  </section>

  <section class="brand-focus" id="care">
    <div class="wrap">
      <div class="eyebrow" style="color:#737b88">Repair &amp; Care</div>
      <h2 class="section-title">사고수리와 외형관리,<br>하나의 기준으로.</h2>
      <div class="focus-grid">
        <article class="focus rep" data-word="R">
          <div class="eyebrow">REPAIR</div>
          <h3>사고 이후까지 책임집니다.</h3>
          <p>사고수리, 판금·도색, 보험수리, 중고차 성능보증수리를 한 흐름으로 진행해 차량을 원래 상태에 가깝게 되돌립니다.</p>
        </article>
        <article class="focus care" data-word="C">
          <div class="eyebrow">CARE</div>
          <h3>매일 타는 차를 새 차처럼.</h3>
          <p>광택, 코팅, PPF, 프리미엄 세차 등 자동차 외형관리로 도장면을 보호하고 차량의 가치를 지킵니다.</p>
        </article>
      </div>
    </div>
  </section>

  <section class="dark" id="service">
    <div class="wrap">
      <div class="eyebrow">Service</div>
      <h2 class="section-title">사고수리부터 외형관리까지,<br>한 공업사에서.</h2>
      <p class="lead">사고수리·판금도색·보험수리·중고차 성능보증수리·자동차정비·외형관리. 차량 입고부터 출고까지 필요한 과정을 하나의 흐름으로 관리합니다.</p>
      <div class="service-grid">
{services}
      </div>
      <p class="service-links">자세히 보기: {service_links}</p>
    </div>
  </section>

{_home_cases}  <section class="works" id="works">
    <div class="wrap">
      <div class="eyebrow" style="color:#737b88">Selected Works</div>
      <h2 class="section-title">작업 사례가 곧 신뢰입니다.</h2>
      <div class="work-grid">
        <article class="work-card"><div class="work-image"><img src="assets/grit-work-01.webp" alt="리프트가 늘어선 파주 그릿서비스 공업사 정비 작업장" loading="lazy" width="900" height="1600" decoding="async"></div><div class="work-copy"><span>Grit / Accident Repair</span><h3>파손 범위부터 정확히 확인합니다.</h3><p>사고수리 입고 차량의 진단부터 출고까지 수리 전후 과정을 기록합니다.</p></div></article>
        <article class="work-card"><div class="work-image"><img src="assets/grit-work-02.webp" alt="범퍼 판금 도색 작업 중인 그릿서비스 도장 부스" loading="lazy" width="900" height="1600" decoding="async"></div><div class="work-copy"><span>Grit / Body &amp; Paint</span><h3>원래 색에 맞춰 도색합니다.</h3><p>판금 복원부터 조색, 도색까지 작업 품질을 보여드립니다.</p></div></article>
        <article class="work-card"><div class="work-image"><img src="assets/grit-work-03.webp" alt="작업 부스에 입고된 흰색 벤츠" loading="lazy" width="900" height="1600" decoding="async"></div><div class="work-copy"><span>Grit / Exterior Care</span><h3>출고 전 외관까지 마무리합니다.</h3><p>광택, PPF, 세차 등 외형관리로 차량을 깨끗한 상태로 돌려드립니다.</p></div></article>
      </div>
      <div class="btns"><a class="btn light" href="{BLOG}" target="_blank" rel="noopener">네이버 블로그 보기</a></div>
    </div>
  </section>


  <section class="instagram" id="instagram">
    <div class="wrap">
      <div class="instagram-head">
        <div><div class="eyebrow" style="color:#737b88">Instagram / @{INSTA_ID}</div><h2 class="section-title">작업 현장을 그대로 보여드립니다.</h2></div>
        <p>그릿서비스의 실제 작업 사진과 수리 전후 사례를 인스타그램에서 확인할 수 있습니다.</p>
      </div>
      <div class="insta-grid">
        <a class="insta-card" href="{INSTA}" target="_blank" rel="noopener" aria-label="그릿서비스 인스타그램 보기">
          <img src="assets/grit-shop-night.webp" alt="불이 켜진 그릿서비스 작업장 외관" loading="lazy" width="1086" height="1448" decoding="async">
          <div class="insta-meta"><span class="eyebrow">INSTAGRAM</span><strong>GRIT WORK SHOP</strong></div>
        </a>
        <a class="insta-card small" href="{INSTA}" target="_blank" rel="noopener" aria-label="그릿서비스 인스타그램 보기">
          <img src="assets/grit-bay.webp" alt="그릿서비스 작업장 안에 입고된 흰색 벤츠" loading="lazy" width="900" height="1600" decoding="async">
          <div class="insta-meta"><span class="eyebrow">WORKSHOP</span><strong>WORK BAY</strong></div>
        </a>
        <a class="insta-card small" href="{INSTA}" target="_blank" rel="noopener" aria-label="그릿서비스 인스타그램 보기">
          <img src="assets/grit-care.webp" alt="그릿서비스 작업장 앞 흰색 제네시스 GV70" loading="lazy" width="1086" height="1448" decoding="async">
          <div class="insta-meta"><span class="eyebrow">GRIT SERVICE</span><strong>PREMIUM CARE</strong></div>
        </a>
      </div>
      <div class="social-row">
        <a class="btn light" href="{INSTA}" target="_blank" rel="noopener">INSTAGRAM @{INSTA_ID}</a>
      </div>
    </div>
  </section>

  <section class="group" id="group">
    <div class="wrap">
      <div class="group-head">
        <div><div class="eyebrow">Our Group</div><h2 class="section-title">하나의 기준,<br>서로 다른 전문성.</h2></div>
        <p>그릿서비스와 로건서비스는 각자의 전문 영역에서 자동차 서비스를 제공합니다. 그릿서비스는 전 차종 토탈 자동차 서비스를 담당하고, 로건서비스는 마세라티·페라리에 집중합니다.</p>
      </div>
      <div class="group-grid">
        <article class="group-card grit">
          <div class="brand-top center"><div class="brand-logo-wrap" style="justify-content:center;width:100%;"><img class="brand-logo-img" src="assets/grit-logo-192.webp" alt="GRIT SERVICE 로고" width="192" height="191" decoding="async"></div><div class="sub">PREMIUM AUTOMOTIVE CARE</div></div>
          <div><h3>Total Automotive Care</h3><p>전 차종을 대상으로 사고수리, 판금·도색, 보험수리, 중고차 성능보증수리, 자동차정비, 외형관리(광택·코팅·PPF·세차), 탁송까지 제공하는 파주 자동차 공업사.</p></div>
          <a href="#top" class="btn" style="align-self:flex-start">GRIT SERVICE</a>
        </article>
        <article class="group-card logan">
          <div class="brand-top center"><div class="brand-logo-wrap" style="justify-content:center;width:100%;"><img class="logan-mark" src="assets/logan-logo-240.webp" alt="Logan Service 로고" width="240" height="86" decoding="async"></div><div class="sub">MASERATI &amp; FERRARI SPECIALIST</div></div>
          <div><h3>Specialized Service</h3><p>2016년부터 마세라티와 페라리의 진단, 정비, 보험수리, 성능보증수리를 전문적으로 제공합니다. 사고수리는 그릿서비스와 연계합니다.</p></div>
          <a href="{LOGAN}" class="btn" style="align-self:flex-start" target="_blank" rel="noopener">LOGAN SERVICE</a>
        </article>
      </div>
    </div>
  </section>

  <section class="journal">
    <div class="wrap journal-grid">
      <div><div class="eyebrow" style="color:#8ea2d6">Journal</div><h2 class="section-title">실제 작업은<br>콘텐츠로 남깁니다.</h2><p>네이버 블로그와 인스타그램에 실제 입고 차량의 수리 과정과 전후 사진을 기록합니다.</p></div>
      <div class="btns"><a class="btn" href="{BLOG}" target="_blank" rel="noopener">NAVER BLOG</a><a class="btn" href="{INSTA}" target="_blank" rel="noopener">INSTAGRAM</a></div>
    </div>
  </section>


  <section class="faq" id="faq">
    <div class="wrap faq-grid">
      <div>
        <div class="eyebrow" style="color:#737b88">FAQ / Grit Service</div>
        <h2 class="section-title">그릿서비스를
          <br>빠르게 이해하는 정보.</h2>
        <p style="color:#5c626c">자주 묻는 질문과 답변으로 그릿서비스의 서비스와 이용 방법을 정리했습니다.</p>
      </div>
      <div class="faq-list">
{faq_html}
{geo_more}
      </div>
    </div>
  </section>

  <section class="contact" id="contact">
    <div class="wrap contact-grid">
      <div><div class="eyebrow">Contact</div><h2 class="section-title">차량의 상태와 상황을<br>먼저 알려주세요.</h2><div class="phone">{PHONE}</div></div>
      <div class="contact-meta">
        <div class="contact-brand">
          <img class="brand-logo-img" src="assets/grit-logo-192.webp" alt="GRIT SERVICE 로고" width="192" height="191" decoding="async" style="max-height:64px;width:auto">
          <div class="contact-brand-copy"><strong>PREMIUM AUTOMOTIVE CARE</strong><span>24H CONSULTATION</span></div>
        </div>
        <div class="contact-list">
          <div class="contact-item"><span>Phone</span><a href="tel:{TEL}" data-track="call">{PHONE}</a></div>
          <div class="contact-item"><span>Hours</span><strong style="font-weight:400;color:#292929">작업 평일 09:00~18:00 · 전화 상담 24시간</strong></div>
          <div class="contact-item"><span>Area</span><strong style="font-weight:400;color:#292929">파주 · 교하 · 운정 · 일산 · 고양 · 김포</strong></div>
          <div class="contact-item"><span>Address</span><a href="{MAP}" target="_blank" rel="noopener">{ADDR_FULL}</a></div>
          <div class="contact-item"><span>Instagram</span><a href="{INSTA}" target="_blank" rel="noopener">@{INSTA_ID}</a></div>
          <div class="contact-item"><span>Kakao Channel</span><a href="{KAKAO}" target="_blank" rel="noopener">그릿서비스 채널 상담</a></div>
          <div class="contact-item"><span>Naver Blog</span><a href="{BLOG}" target="_blank" rel="noopener">blog.naver.com/grit_service</a></div>
        </div>
        <div class="btns"><a class="btn primary" href="tel:{TEL}">전화 상담</a><a class="btn" href="{KAKAO}" target="_blank" rel="noopener">카톡 사진 상담</a><a class="btn" href="{INSTA}" target="_blank" rel="noopener">인스타그램</a></div>
      </div>
    </div>
  </section>
</main>

<footer>
  <div class="wrap footer-row"><span>© 2026 GRIT SERVICE. ALL RIGHTS RESERVED.</span><span>{COMPANY} · 대표 {CEO} · 사업자등록번호 {BIZNO} · {ADDR_FULL} · {PHONE}</span><span class="footer-links">최종 업데이트 {TODAY} · {'<a href="cases/">수리사례</a> · ' if HAS_CASES else ''}<a href="faq/">자주 묻는 질문 200</a> · <a href="privacy/">개인정보처리방침</a> · <a href="{LOGAN}" target="_blank" rel="noopener">로건서비스</a> · <a href="{WORKTABLE}" target="_blank" rel="noopener nofollow">직원용 WORKTABLE</a></span></div>
</footer>
<div class="callbar" aria-label="빠른 상담"><a href="tel:{TEL}" data-track="call">전화 상담 {PHONE}</a><a href="{KAKAO}" target="_blank" rel="noopener" data-track="kakao">카톡 사진 상담</a></div>
<script>
// 전화·카카오 상담 클릭을 광고 전환으로 기록 (분석 코드를 넣었을 때만 동작)
document.addEventListener('click',function(e){{var a=e.target.closest('a[href^="tel:"],a[href*="pf.kakao.com"]');if(!a)return;var t=a.href.indexOf('tel:')===0?'call':'kakao';
if(window.gtag)gtag('event','contact_'+t,{{method:t}});
if(window.wcs){{window._nasa={{}};_nasa["cnv"]=wcs.cnv("4","1");wcs_do(_nasa);}}}});
</script>
</body>
</html>
'''
(OUT / "index.php").write_text(html)

(OUT / "llms.txt").write_text(f"""# 그릿서비스 (GRIT SERVICE)

> 그릿서비스는 경기도 파주시 교하에 있는 자동차 공업사입니다. 국산차·수입차 전 차종의 사고수리, 판금·도색, 보험수리, 중고차 성능보증수리, 자동차정비, 자동차 외형관리(광택·코팅·PPF·세차), 탁송을 한 곳에서 제공합니다. 대표번호 {PHONE}(24시간 상담).

## 기본 정보
- 상호: 그릿서비스 (GRIT SERVICE)
- 업종: 자동차 공업사 (사고수리·판금도색·보험수리·자동차정비·외형관리)
- 주소: {ADDR_FULL} (교하동)
- 대표번호: {PHONE} (전화 상담 24시간, 입고·작업 평일 09~18시)
- 영업시간: 입고·작업 평일 09:00~18:00, 전화 상담 24시간
- 위치 좌표: {GEO[0]}, {GEO[1]}
- 네이버 플레이스: {EXTRA_SAME_AS[0]}
- 구글 지도: {EXTRA_SAME_AS[1]}
- 카카오톡 채널: {KAKAO}
- 운영사: {COMPANY} · 대표 {CEO} · 사업자등록번호 {BIZNO}
- 서비스 지역: 파주, 교하, 운정, 일산, 고양, 김포, 양주, 은평
- 대상 차종: 국산차, 수입차 전 차종
- 슬로건: 기본이 가장 중요합니다.

## 서비스
""" + "".join(f"- **{s[1].replace('&amp;', '&')}**: {s[2]}\n" for s in SERVICES) + "\n## 서비스 상세 페이지\n" + "".join(f"- {t}: {SITE}{u}\n" for u, t in SERVICE_PAGES) + """
## 자주 묻는 질문
""" + "".join(f"### {q}\n{a}\n\n" for q, a in FAQ) + f"""## 더 보기
- 홈페이지: {SITE}
- 자주 묻는 질문 200(페이지): {SITE}faq/
""" + (f"- 수리사례(실제 입고 차량 기록): {SITE}cases/\n" if HAS_CASES else "") + f"""- 전체 질문·답변 200(AI용): {SITE}llms-full.txt
- 네이버 블로그(작업기): {BLOG}
- 인스타그램: {INSTA}
- 그룹사 로건서비스(마세라티·페라리 전문): {LOGAN}

최종 업데이트: {TODAY}
""")

robots = f"""# 그릿서비스 robots.txt — 모든 검색엔진·AI 검색 수집 허용
User-agent: *
Allow: /

# 네이버
User-agent: Yeti
Allow: /

# 구글
User-agent: Googlebot
Allow: /
User-agent: Googlebot-Image
Allow: /

# 다음·빙
User-agent: Daum
Allow: /
User-agent: Daumoa
Allow: /
User-agent: Bingbot
Allow: /

# AI 검색(ChatGPT, Gemini, Claude, Perplexity)
User-agent: GPTBot
Allow: /
User-agent: OAI-SearchBot
Allow: /
User-agent: ChatGPT-User
Allow: /
User-agent: Google-Extended
Allow: /
User-agent: ClaudeBot
Allow: /
User-agent: Claude-SearchBot
Allow: /
User-agent: PerplexityBot
Allow: /
User-agent: Perplexity-User
Allow: /
User-agent: Applebot
Allow: /
User-agent: Applebot-Extended
Allow: /

Sitemap: {SITE}sitemap.xml
"""
(OUT / "robots.txt").write_text(robots)
if HAS_CASES:  # llms.txt 끝에 수리사례 목록(제목·주소·요약)
    with open(OUT / "llms.txt", "a") as f:
        f.write("\n" + (OUT / "cases" / "llms-cases.txt").read_text())

IMGS = [("grit-hero-main.webp", "파주 교하 그릿서비스 자동차 공업사 외관"),
        ("grit-repair.webp", "그릿서비스 사고수리·판금도색 작업"),
        ("grit-care.webp", "그릿서비스 작업장 앞 제네시스 GV70 외형관리"),
        ("grit-shop-night.webp", "불이 켜진 그릿서비스 작업장 외관"),
        ("grit-bay.webp", "그릿서비스 작업장 안 입고 차량"),
        ("grit-work-01.webp", "리프트가 늘어선 파주 그릿서비스 정비 작업장"),
        ("grit-work-02.webp", "범퍼 판금 도색 작업 중인 그릿서비스 도장 부스"),
        ("grit-work-03.webp", "작업 부스에 입고된 수입차"),
        ("og-image.jpg", "파주 사고수리·판금도색 공업사 그릿서비스")]
img_xml = "".join(f"""    <image:image>
      <image:loc>{SITE}assets/{f}</image:loc>
      <image:title>{t}</image:title>
    </image:image>
""" for f, t in IMGS)
# 라이브 서버에 따로 올라간 서비스 페이지 5개(2026-10-15 확인). 생성기가 sitemap 에서 지우지 않게 유지한다.
EXTRA_PAGES = [("accident-repair/", "0.9"), ("painting/", "0.8"), ("insurance-repair/", "0.8"),
               ("certified-repair/", "0.8"), ("imported-cars/", "0.8")]
extra_xml = "".join(f"""  <url>
    <loc>{SITE}{u}</loc>
    <lastmod>2026-10-15</lastmod>
    <changefreq>monthly</changefreq>
    <priority>{pr}</priority>
  </url>
""" for u, pr in EXTRA_PAGES)
cases_xml = ""
if HAS_CASES:  # 수리사례 URL 을 대표 sitemap 에 합친다(따로 제출할 필요 없게)
    _sx = (OUT / "cases" / "sitemap-cases.xml").read_text()
    cases_xml = "".join("  " + u.strip() + "\n" for u in re.findall(r"<url>.*?</url>", _sx, re.S))
(OUT / "sitemap.xml").write_text(f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">
  <url>
    <loc>{SITE}</loc>
    <lastmod>{TODAY}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
{img_xml}  </url>
  <url>
    <loc>{SITE}faq/</loc>
    <lastmod>{TODAY}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
{extra_xml}{cases_xml}</urlset>
""")
# 개인정보처리방침 (초안, 사장님 확인 전)
(OUT / "privacy").mkdir(exist_ok=True)
(OUT / "privacy" / "index.php").write_text(f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>개인정보처리방침 | 그릿서비스</title>
  <meta name="description" content="그릿서비스 개인정보처리방침: 상담·수리에 필요한 개인정보의 처리 목적, 보유 기간, 문의처 안내." />
  <link rel="canonical" href="{SITE}privacy/" />
  <style>body{{font-family:-apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo","Malgun Gothic",sans-serif;max-width:760px;margin:0 auto;padding:32px 16px 64px;line-height:1.75;color:#222;word-break:keep-all}}h1{{font-size:26px}}h2{{font-size:18px;margin-top:32px}}a{{color:#004a9f}}</style>
</head>
<body>
<p><a href="../">← 그릿서비스 홈</a></p>
<h1>개인정보처리방침</h1>
<p>{COMPANY}(이하 "회사")는 상담과 차량 수리 서비스 제공에 필요한 최소한의 개인정보만 처리하며, 「개인정보 보호법」을 지킵니다.</p>
<h2>1. 처리하는 개인정보와 목적</h2>
<p>전화·카카오톡 채널 상담과 차량 입고 과정에서 이름, 연락처, 차량번호·차종, 고객이 보내 주신 차량 사진을 받습니다. 이 정보는 상담 응대, 견적 안내, 수리 진행과 출고 연락, 보험 처리 안내에만 씁니다.</p>
<h2>2. 보유 기간</h2>
<p>목적을 이루면 지체 없이 파기합니다. 다만 세금계산서·거래 기록 등 관계 법령이 보관을 정한 정보는 그 기간 동안 보관합니다.</p>
<h2>3. 제3자 제공</h2>
<p>고객이 동의하거나 보험 처리처럼 고객이 요청한 업무에 필요한 경우(예: 보험사), 또는 법령에 근거가 있는 경우에만 제공합니다.</p>
<h2>4. 정보주체의 권리</h2>
<p>언제든지 개인정보 열람, 정정, 삭제, 처리 정지를 요청할 수 있으며, 아래 연락처로 요청하시면 지체 없이 처리합니다.</p>
<h2>5. 개인정보 보호책임자</h2>
<p>{COMPANY} 대표 {CEO} · 전화 {PHONE} · {ADDR_FULL}</p>
<h2>6. 시행일</h2>
<p>이 방침은 {TODAY}부터 적용합니다.</p>
</body>
</html>
""")
make_geo.build(OUT, SITE, PHONE, TEL, ADDR_FULL, KAKAO, BLOG, INSTA, COMPANY, CEO, BIZNO, TODAY)
print("ok")
