"""사이트 전체 검사(홈·FAQ·서비스·사례·개인정보·sitemap·robots). build.sh 가 두 사이트에 돌린다. FAIL 이 하나라도 있으면 종료 코드 1.
사용: python3 check_site.py <사이트폴더> <사이트주소 https://.../>
검사: noindex 금지, title(40자)·설명(80자)·h1 1개, canonical·og:url = 자기 주소, JSON-LD 문법, 내부 링크·이미지 파일 존재,
      sitemap 의 주소가 실제 페이지인지·lastmod 가 미래가 아닌지, robots 의 Sitemap 줄."""
import datetime, json, re, sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse, unquote

root, SITE = Path(sys.argv[1]), sys.argv[2]
HOST = urlparse(SITE).netloc
# 서버에만 있고 저장소에는 없는 파일(지우면 안 됨). 링크가 가리켜도 FAIL 로 보지 않는다.
SERVER_ONLY = re.compile(r"^(assets/(hero-main|maserati-service-0\d|logan-workshop-01)\.webp|assets/og-image\.jpg|assets/(logan|grit)-service-logo\.png|work/.*)$")
TODAY = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=9)).date().isoformat()
fails, warns = [], []


class P(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self.meta, self.h1, self.title, self.ld, self._t, self._ld, self.canon = [], {}, 0, "", [], False, None, None

    def handle_starttag(self, tag, a):
        a = dict(a)
        if tag == "a" and a.get("href"):
            self.links.append(a["href"])
        if tag in ("img", "source") and (a.get("src") or a.get("srcset")):
            for part in (a.get("srcset") or a.get("src")).split(","):
                self.links.append(part.strip().split(" ")[0])
        if tag == "link" and a.get("rel") == "canonical":
            self.canon = a.get("href")
        if tag == "link" and a.get("rel") in ("icon", "stylesheet", "preload", "apple-touch-icon") and a.get("href"):
            self.links.append(a["href"])
        if tag == "meta":
            k = a.get("name") or a.get("property")
            if k:
                self.meta[k] = a.get("content", "")
        if tag == "h1":
            self.h1 += 1
        if tag == "title":
            self._t = True
        if tag == "script" and a.get("type") == "application/ld+json":
            self._ld = ""

    def handle_endtag(self, tag):
        if tag == "title":
            self._t = False
        if tag == "script" and self._ld is not None:
            self.ld.append(self._ld)
            self._ld = None

    def handle_data(self, d):
        if self._t:
            self.title += d
        if self._ld is not None:
            self._ld += d


def page_url(f):
    rel = f.relative_to(root).as_posix()
    rel = re.sub(r"(^|/)index\.(html|php)$", r"\1", rel)
    return SITE + rel


def target_exists(base_dir, href):
    u = urlparse(href)
    if u.scheme in ("mailto", "tel", "javascript", "data") or href.startswith("#"):
        return True, None
    if u.scheme in ("http", "https"):
        if u.netloc != HOST:
            return True, None
        path = u.path.lstrip("/")
    else:
        if not u.path:
            return True, None
        path = (base_dir / unquote(u.path)).resolve().relative_to(root.resolve()).as_posix() if not u.path.startswith("/") else u.path.lstrip("/")
    path = unquote(path)
    if path in ("", ".") or path.endswith("/") or (root / path).is_dir():
        d = root / path
        ok = any((d / n).exists() for n in ("index.html", "index.php"))
    else:
        ok = (root / path).exists()
    return ok or bool(SERVER_ONLY.match(path.rstrip("/") if not path.endswith("/") else path)), path


pages = [f for f in sorted(root.rglob("*")) if f.suffix in (".html", ".php") and f.is_file()]
for f in pages:
    rel = f.relative_to(root).as_posix()
    s = f.read_text(encoding="utf-8", errors="replace")
    if "<html" not in s:
        continue  # 조각(home-section 등)
    if rel.startswith("work/"):
        continue  # 직원용 바로가기(손님용 페이지 아님)
    p = P()
    p.feed(s)
    if re.search(r"noindex", s, re.I):
        fails.append(f"{rel}: noindex 있음(절대 금지)")
    if not p.title.strip():
        fails.append(f"{rel}: title 없음")
    elif len(p.title.strip()) > 40:
        fails.append(f"{rel}: title {len(p.title.strip())}자(40자 이내): {p.title.strip()}")
    d = p.meta.get("description", "")
    if not d:
        fails.append(f"{rel}: 설명(description) 없음")
    elif len(d) > 80:
        fails.append(f"{rel}: 설명 {len(d)}자(80자 이내)")
    if p.h1 != 1:
        fails.append(f"{rel}: h1 {p.h1}개")
    want = page_url(f)
    if p.canon != want:
        fails.append(f"{rel}: canonical {p.canon} ≠ {want}")
    if p.meta.get("og:url") and p.meta["og:url"] != want:
        fails.append(f"{rel}: og:url {p.meta['og:url']} ≠ {want}")
    elif not p.meta.get("og:url"):
        warns.append(f"{rel}: og:url 없음")
    for j in p.ld:
        try:
            json.loads(j)
        except Exception as e:
            fails.append(f"{rel}: JSON-LD 문법 오류 {e}")
    for h in set(p.links):
        ok, path = target_exists(f.parent, h)
        if not ok:
            fails.append(f"{rel}: 깨진 링크 {h}")

# sitemap / robots
for sm in [root / "sitemap.xml"] + sorted((root / "cases").glob("sitemap*.xml")) if (root / "cases").exists() else [root / "sitemap.xml"]:
    if not sm.exists():
        fails.append(f"{sm.relative_to(root)}: 없음")
        continue
    x = sm.read_text(encoding="utf-8")
    for loc in re.findall(r"<loc>(.*?)</loc>", x):
        if loc.startswith(SITE) and "/assets/" not in loc:
            ok, _ = target_exists(root, loc)
            if not ok:
                fails.append(f"{sm.relative_to(root)}: 없는 페이지 {loc}")
    for lm in re.findall(r"<lastmod>(.*?)</lastmod>", x):
        if lm[:10] > TODAY:
            fails.append(f"{sm.relative_to(root)}: lastmod 가 미래 날짜 {lm}")
rb = root / "robots.txt"
if rb.exists():
    for u in re.findall(r"(?im)^sitemap:\s*(\S+)", rb.read_text()):
        if not (root / urlparse(u).path.lstrip("/")).exists():
            fails.append(f"robots.txt: 없는 사이트맵 {u}")

for w in warns:
    print("WARN", w)
for x in fails:
    print("FAIL", x)
print(f"{root.name}: 페이지 {len(pages)}개 · FAIL {len(fails)} · WARN {len(warns)}")
sys.exit(1 if fails else 0)
