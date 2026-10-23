"""로건서비스 차종별·증상별 안내 페이지와 탁송 안내 페이지를 만든다(내용은 실제 정비사례와 FAQ 답변에서만 가져옴).
사용: python3 make_hubs.py <사이트폴더>   (build.sh 가 add_cases.py 다음에 부름. cases/ 와 faq/ 가 이미 있어야 함)
만드는 것: maserati/(모델 목록) maserati/{ghibli,levante,quattroporte,granturismo}/, symptoms/{...}/, delivery/
그리고 홈에 링크 한 블록, sitemap.xml·llms.txt 에 주소를 넣는다. 여러 번 돌려도 한 번만 들어간다."""
import html as H
import json, re, sys
from pathlib import Path
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lastmod import lastmod

root = Path(sys.argv[1])
HERE = Path(__file__).resolve().parent
POSTS = HERE.parent / "cases-system" / "logan" / "posts"
SITE = "https://loganservice.co.kr/"
PHONE, TEL = "1544-6072", "15446072"
KAKAO = "https://pf.kakao.com/_PKYxdG"
MAP = "https://map.naver.com/p/entry/place/20277854"
ADDR = "경기도 파주시 아침노을길 55"
GA4 = "G-9TNRSR44QK"
TODAY = lastmod(HERE / "make_hubs.py", POSTS, HERE / "upload" / "faq")

MODELS = [("ghibli", "기블리", "마세라티 기블리"), ("levante", "르반떼", "마세라티 르반떼"),
          ("quattroporte", "콰트로포르테", "마세라티 콰트로포르테"), ("granturismo", "그란투리스모", "마세라티 그란투리스모")]
SYMPTOMS = [("warning-light", "엔진경고등·고장코드", r"경고등|고장코드|실화|출력 저하", "경고등이 켜지거나 고장코드가 뜬 마세라티를 진단·수리한 기록입니다."),
            ("oil-leak", "엔진오일·미션 누유", r"누유|오일씰|가스켓|리테이너", "엔진·미션에서 오일이 새 입고된 마세라티의 누유 위치 확인과 수리 기록입니다."),
            ("suspension-noise", "하체 소음·충격", r"하체|소음|쇼크|부싱|마운트|로우암", "주행 중 하체 소음이나 충격으로 입고된 마세라티의 점검·부품 교환 기록입니다."),
            ("cooling", "냉각·서모스탯", r"서모스탯|냉각", "냉각수 순환 불량, 서모스탯 고장코드로 입고된 마세라티 수리 기록입니다.")]

posts = []
for f in sorted(POSTS.glob("*.yaml")):
    p = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
    if not p.get("draft"):
        posts.append(p)
posts.sort(key=lambda p: str(p.get("date")), reverse=True)

# FAQ 답변(화면용 HTML 그대로)
faq_html = (root / "faq" / "index.php").read_text(encoding="utf-8")
FAQS = [(re.sub(r"<[^>]+>", "", q).strip(), a.strip()) for q, a in re.findall(r"<details[^>]*><summary>(.*?)</summary><p>(.*?)</p>", faq_html, re.S)]


def faqs_for(pattern, limit=6, exclude=None):
    out, seen = [], set()
    for q, a in FAQS:
        if re.search(pattern, q) and not (exclude and re.search(exclude, q)) and q not in seen:
            seen.add(q)
            out.append((q, a))
    return out[:limit]


CSS = """:root{color-scheme:only light}*{box-sizing:border-box}body{margin:0;font-family:"Pretendard","Apple SD Gothic Neo","Malgun Gothic","Noto Sans KR",sans-serif;color:#171717;background:#fcfbf8;line-height:1.7;word-break:keep-all}
a{color:#a11f30}.skip{position:absolute;left:-999px;top:0;background:#fff;padding:8px 12px;z-index:99}.skip:focus{left:8px}
.w{max-width:900px;margin:0 auto;padding:0 16px}
header.top{background:#171717;color:#fff}header.top .w{display:flex;align-items:center;gap:8px 18px;flex-wrap:wrap;min-height:64px;padding-top:6px;padding-bottom:6px}
header.top .brand{display:flex;align-items:center;color:#fff;text-decoration:none;min-height:44px}header.top .brand img{height:30px;width:auto}
header.top nav{display:flex;flex-wrap:wrap;gap:2px 4px;margin-left:auto}header.top nav a{color:#fff;text-decoration:none;font-size:15px;padding:10px 8px;min-height:44px;display:inline-flex;align-items:center}
header.top nav a.tel{background:#c42739;border-radius:6px;padding:10px 14px;font-weight:700}
.crumb{font-size:14px;color:#4f4a45;margin:18px 0 0}.crumb a{display:inline-block;padding:10px 2px}
h1{font-size:clamp(26px,5vw,38px);line-height:1.3;margin:12px 0}h2{font-size:22px;margin:44px 0 12px;padding-top:12px;border-top:2px solid #c42739;color:#8e1b2a}
.lead{font-size:17px;color:#3b3935}
.card-list{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,260px),1fr));gap:12px;padding:0;list-style:none}
.card-list li{background:#fff;border:1px solid #ddd7cf;border-radius:10px;padding:14px 16px}.card-list a{font-weight:700;text-decoration:none}.card-list p{margin:6px 0 0;font-size:15px;color:#4f4a45}
details{border-bottom:1px solid #ddd7cf;padding:12px 0}summary{cursor:pointer;font-weight:700}details p{margin:8px 0 0;color:#3b3935;overflow-wrap:anywhere}
ol li{margin:6px 0}.more a{display:inline-block;padding:8px 0;font-weight:700}
.cta{display:flex;flex-wrap:wrap;gap:10px;margin:36px 0}.cta a{flex:1 1 220px;text-align:center;padding:15px;border-radius:8px;font-weight:700;text-decoration:none;background:#c42739;color:#fff}.cta a+a{background:#fee500;color:#191919}
footer.bot{background:#f6f2ec;color:#3b3935;font-size:14px;padding:26px 0;margin-top:48px}footer.bot a{display:inline-block;padding:6px 0}
.callbar{display:none}@media(max-width:760px){.callbar{display:grid;grid-template-columns:1fr 1fr;position:fixed;left:0;right:0;bottom:0;z-index:60}.callbar a{display:flex;align-items:center;justify-content:center;min-height:54px;font-weight:700;color:#fff;background:#c42739;text-decoration:none}.callbar a+a{background:#fee500;color:#191919}body{padding-bottom:54px}header.top nav a.tel{display:none}}"""
TRACK = """<script>
document.addEventListener('click',function(e){var a=e.target.closest('a[href^="tel:"],a[href*="pf.kakao.com"]');if(!a)return;var t=a.href.indexOf('tel:')===0?'call':'kakao';
var s=a.closest('.callbar,header,footer,section,.cta,nav');var p=s?(s.id||(s.className&&String(s.className).split(' ')[0])||s.tagName.toLowerCase()):'page';
if(window.gtag)gtag('event','contact_'+t,{method:t,position:p});});
</script>"""


def page(path, title, desc, h1, lead, crumbs, body, about=None):
    depth = path.count("/")
    up = "../" * depth
    url = SITE + path
    el = [{"@type": "ListItem", "position": 1, "name": "로건서비스", "item": SITE}] + \
         [{"@type": "ListItem", "position": i + 2, "name": t, "item": SITE + u} for i, (t, u) in enumerate(crumbs)]
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "WebPage", "@id": url, "url": url, "name": title, "description": desc, "inLanguage": "ko-KR", "dateModified": TODAY,
         "isPartOf": {"@id": SITE + "#website"}, "about": about or {"@id": SITE + "#logan-service"}},
        {"@type": "BreadcrumbList", "itemListElement": el}]}
    cr = " › ".join([f'<a href="{up}">홈</a>'] + [f'<a href="{up}{u}">{H.escape(t)}</a>' for t, u in crumbs[:-1]] + [H.escape(crumbs[-1][0])])
    html = f'''<!doctype html>
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
  <meta property="og:site_name" content="로건서비스" />
  <meta property="og:locale" content="ko_KR" />
  <meta property="og:image" content="{SITE}assets/og-image.jpg" />
  <meta name="theme-color" content="#171717" />
  <script async src="https://www.googletagmanager.com/gtag/js?id={GA4}"></script>
  <script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag('js',new Date());gtag('config','{GA4}');</script>
  <script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
  <style>{CSS}</style>
</head>
<body>
<a class="skip" href="#main">본문 바로가기</a>
<header class="top"><div class="w">
  <a class="brand" href="{up}"><img src="{up}assets/logan-logo-240.webp" alt="로건서비스" width="240" height="86"></a>
  <nav aria-label="주요 메뉴"><a href="{up}">홈</a><a href="{up}maserati/">모델별</a><a href="{up}symptoms/">증상별</a><a href="{up}cases/">정비사례</a><a href="{up}faq/">자주 묻는 질문</a><a href="{up}delivery/">탁송</a><a class="tel" href="tel:{TEL}">{PHONE}</a></nav>
</div></header>
<main id="main" class="w">
  <p class="crumb">{cr}</p>
  <h1>{H.escape(h1)}</h1>
  <p class="lead">{lead}</p>
{body}
  <div class="cta" id="cta"><a href="tel:{TEL}">전화 상담 {PHONE}</a><a href="{KAKAO}" target="_blank" rel="noopener">증상 사진 보내기(카톡)</a></div>
</main>
<footer class="bot"><div class="w">
  <p><strong>로건서비스</strong> · 주식회사 로건 · 대표 류완희 · 사업자등록번호 406-81-05779<br>{ADDR} · 평일 09:00~18:00(점심 12:30~13:30, 토·일 휴무) · {PHONE}</p>
  <p><a href="{up}">홈</a> · <a href="{up}cases/">정비사례</a> · <a href="{up}faq/">자주 묻는 질문</a> · <a href="{MAP}" target="_blank" rel="noopener">네이버 지도</a> · <a href="{up}privacy/">개인정보처리방침</a> · <a href="https://gritservice.co.kr/" target="_blank" rel="noopener">그릿서비스</a></p>
</div></footer>
<nav class="callbar" aria-label="빠른 상담"><a href="tel:{TEL}">전화 상담 {PHONE}</a><a href="{KAKAO}" target="_blank" rel="noopener">증상 사진 보내기</a></nav>
{TRACK}
</body>
</html>
'''
    d = root / path
    d.mkdir(parents=True, exist_ok=True)
    (d / "index.html").write_text(html)
    return url


def cards(ps, up):
    return '  <ul class="card-list">\n' + "\n".join(
        f'    <li><a href="{up}cases/{p["slug"]}/">{H.escape(p["title"])}</a><p>{H.escape(p.get("description") or "")}</p></li>' for p in ps) + "\n  </ul>\n"


def faq_sec(items, title):
    if not items:
        return ""
    return f'  <section id="faq">\n  <h2>{H.escape(title)}</h2>\n' + "\n".join(f"  <details><summary>{H.escape(q)}</summary><p>{a}</p></details>" for q, a in items) + '\n  <p class="more"><a href="../../faq/">자주 묻는 질문 전체 →</a></p>\n  </section>\n'


made = []
# 모델별
model_rows = []
for slug, ko, full in MODELS:
    ps = [p for p in posts if ko in str((p.get("car") or {}).get("model", ""))]
    if not ps:
        continue
    model_rows.append((slug, ko, full, len(ps)))
    body = f'  <section id="cases">\n  <h2>{ko} 정비사례 {len(ps)}건</h2>\n' + cards(ps, "../../") + "  </section>\n"
    body += faq_sec(faqs_for(ko, exclude="페라리"), f"{ko} 자주 묻는 질문").replace("../../faq/", "../../faq/")
    made.append(page(f"maserati/{slug}/", f"파주 {full} 정비 | 로건서비스", f"파주 로건서비스의 {full} 실제 정비사례 {len(ps)}건과 자주 묻는 질문. 상담 {PHONE}.",
                     f"{full} 정비", f"로건서비스는 경기도 파주의 마세라티 전문 정비소입니다. {ko}로 입고된 실제 정비 기록과 자주 묻는 질문을 모았습니다. 직접 오기 어려우면 탁송으로 입고할 수 있습니다.",
                     [("모델별", "maserati/"), (full, f"maserati/{slug}/")], body))
body = '  <section id="models">\n  <h2>모델 선택</h2>\n  <ul class="card-list">\n' + "\n".join(
    f'    <li><a href="{s}/">{H.escape(full)}</a><p>정비사례 {n}건</p></li>' for s, ko, full, n in model_rows) + "\n  </ul>\n  </section>\n"
made.append(page("maserati/", "파주 마세라티 모델별 정비 | 로건서비스", f"기블리·르반떼·콰트로포르테·그란투리스모 모델별 실제 정비사례. 파주 로건서비스 {PHONE}.",
                 "마세라티 모델별 정비", "모델을 고르면 그 모델의 실제 정비사례와 자주 묻는 질문을 볼 수 있습니다.", [("모델별", "maserati/")], body))
# 증상별
sym_rows = []
for slug, name, pat, lead in SYMPTOMS:
    ps = [p for p in posts if re.search(pat, p.get("title", ""))]
    if not ps:
        continue
    sym_rows.append((slug, name, len(ps)))
    body = f'  <section id="cases">\n  <h2>{H.escape(name)} 정비사례 {len(ps)}건</h2>\n' + cards(ps, "../../") + "  </section>\n"
    body += faq_sec(faqs_for(pat, exclude="페라리"), f"{name} 자주 묻는 질문")
    made.append(page(f"symptoms/{slug}/", f"마세라티 {name} 수리 | 로건서비스", f"마세라티 {name} 실제 진단·수리 사례 {len(ps)}건. 파주 로건서비스 상담 {PHONE}.",
                     f"마세라티 {name}", lead + " 같은 증상이면 사진이나 계기판 화면을 카톡으로 보내 주세요.", [("증상별", "symptoms/"), (name, f"symptoms/{slug}/")], body))
body = '  <section id="symptoms">\n  <h2>증상 선택</h2>\n  <ul class="card-list">\n' + "\n".join(
    f'    <li><a href="{s}/">{H.escape(n)}</a><p>정비사례 {c}건</p></li>' for s, n, c in sym_rows) + "\n  </ul>\n  </section>\n"
made.append(page("symptoms/", "마세라티 증상별 정비 안내 | 로건서비스", f"경고등, 누유, 하체 소음, 냉각 등 증상별 마세라티 실제 정비사례. 파주 로건서비스 {PHONE}.",
                 "마세라티 증상별 정비 안내", "증상을 고르면 같은 증상으로 입고된 실제 정비사례와 자주 묻는 질문을 볼 수 있습니다.", [("증상별", "symptoms/")], body))
# 탁송
dq = faqs_for(r"탁송|지방|부산|대전|대구|광주|서울|인천|수원|제주", 12)
body = f'''  <section id="steps">
  <h2>탁송 입고 순서</h2>
  <ol>
    <li>전화({PHONE})나 카카오톡으로 차량 위치, 모델, 증상을 알려 주세요.</li>
    <li>일정과 탁송 비용을 안내받습니다.</li>
    <li>탁송 기사가 차량을 받아 파주 로건서비스로 입고합니다.</li>
    <li>진단 결과와 견적을 안내받고, 동의하신 작업만 진행합니다.</li>
    <li>작업이 끝나면 탁송으로 차량을 돌려드립니다.</li>
  </ol>
  </section>
''' + faq_sec(dq, "탁송 자주 묻는 질문").replace("../../faq/", "../faq/")
made.append(page("delivery/", "마세라티 전국 탁송 정비 | 로건서비스", f"파주 로건서비스 마세라티·페라리 전국 탁송 입고 순서와 지역별 탁송 안내. 상담 {PHONE}.",
                 "마세라티 전국 탁송 정비", f"로건서비스는 경기도 파주({ADDR})에 있는 마세라티·페라리 전문 정비소입니다. 직접 오기 어려우면 탁송으로 입고·출고할 수 있습니다.",
                 [("탁송", "delivery/")], body))

# 404 페이지(.htaccess 의 ErrorDocument 404 /404.html). 모든 링크를 절대 주소로
_tmp = page("x404/", "페이지를 찾을 수 없습니다 | 로건서비스", "주소가 바뀌었거나 없는 페이지입니다. 로건서비스 홈과 정비사례에서 찾아 주세요.",
            "페이지를 찾을 수 없습니다", "주소가 바뀌었거나 없는 페이지입니다. 아래에서 찾아 주세요.", [("안내", "x404/")],
            '  <ul class="card-list"><li><a href="../">로건서비스 홈</a></li><li><a href="../cases/">정비사례</a></li><li><a href="../maserati/">모델별 정비</a></li><li><a href="../faq/">자주 묻는 질문</a></li></ul>\n')
_h = (root / "x404" / "index.html").read_text(encoding="utf-8")
_h = re.sub(r'(href|src)="\.\./', lambda m: f'{m.group(1)}="{SITE}', _h).replace(SITE + "x404/", SITE + "404.html")
(root / "404.html").write_text(_h)
import shutil; shutil.rmtree(root / "x404")

# 홈에 링크 블록(표식으로 한 번만)
idx = root / "index.php"
s = idx.read_text(encoding="utf-8")
s = re.sub(r"\n?<!-- hubs-home -->.*?<!-- /hubs-home -->\n?", "\n", s, flags=re.S)
block = f'''<!-- hubs-home -->
  <section class="hubs-home" id="guide" aria-label="모델별·증상별 안내" style="padding:28px 0;background:#fff">
    <div class="wrap"><p style="margin:0;font-size:16px;line-height:2;word-break:keep-all"><strong>모델별 정비</strong>: {" · ".join(f'<a href="maserati/{s_}/">{ko}</a>' for s_, ko, _, _ in model_rows)}
    <br><strong>증상별 안내</strong>: {" · ".join(f'<a href="symptoms/{s_}/">{n}</a>' for s_, n, _ in sym_rows)} · <a href="delivery/">전국 탁송</a></p></div>
  </section>
<!-- /hubs-home -->'''
anchor = "<!-- /cases-home -->"
assert s.count(anchor) == 1, "cases-home 표식을 못 찾음(add_cases.py 먼저)"
s = s.replace(anchor, anchor + "\n" + block)
idx.write_text(s)

# sitemap: 만든 주소 추가 + 홈·faq lastmod 를 실제 수정일로
sm = root / "sitemap.xml"
x = sm.read_text(encoding="utf-8")
x = re.sub(r"\n  <!-- hubs -->.*?<!-- /hubs -->", "", x, flags=re.S)
home_mod = lastmod(HERE / "upload" / "index.php", HERE / "add_cases.py", POSTS)
faq_mod = lastmod(HERE / "upload" / "faq")
x = re.sub(r"(<loc>https://loganservice\.co\.kr/</loc>\s*<lastmod>)[^<]*", r"\g<1>" + home_mod, x)
x = re.sub(r"(<loc>https://loganservice\.co\.kr/faq/</loc>\s*<lastmod>)[^<]*", r"\g<1>" + faq_mod, x)
urls = "".join(f"    <url><loc>{u}</loc><lastmod>{TODAY}</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>\n" for u in made)
x = x.replace("</urlset>", f"  <!-- hubs -->\n{urls}  <!-- /hubs -->\n</urlset>")
sm.write_text(x)

ll = root / "llms.txt"
t = re.sub(r"\n## 모델별·증상별 안내.*?(?=\n## |\Z)", "", ll.read_text(encoding="utf-8"), flags=re.S).rstrip() + "\n"
t += "\n## 모델별·증상별 안내\n" + "".join(f"- {u}\n" for u in made) + "\n"
ll.write_text(t)
print("ok", len(made), "pages")
