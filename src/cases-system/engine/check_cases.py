"""수리사례(/cases/) 생성 결과 검사 K1~K8. 결과는 PASS / WARN / FAIL / SKIP / ERROR. 미검사(SKIP)는 통과가 아니다.
사용: python3 check_cases.py <out_dir> <site_yaml> [--mode auto|upload|preview] [--assets 사진폴더]
                            [--site-dir 사이트본체폴더] [--no-browser] [--only K1,K2] [--all] [--strict-links]
  out_dir   make_cases.py 출력 폴더(그 안에 cases/ 가 있음). 예: build/grit-upload/
  site_yaml grit/site.yaml 또는 logan/site.yaml. 같은 폴더의 posts/*.yaml 로 draft 여부도 맞춰 본다.
  --mode    auto 면 out_dir 이름에 'upload' 가 있으면 업로드 모드(K7 엄격), 아니면 미리보기 모드.
  --assets  assets/ 경로를 찾을 폴더(사이트의 assets/ 폴더). out_dir/assets 도 함께 본다.
  --site-dir /cases/ 밖 링크(홈, 서비스 페이지)를 확인할 사이트 본체 폴더. 없으면 그런 링크는 WARN.
  --all     항목마다 문제를 전부 출력(기본은 항목당 12줄).
  --strict-links  K3(내부 링크)의 WARN 을 FAIL 로: 확인 못 한 /cases/ 밖 링크, 없는 사진, 다른 글에서
            들어오는 링크가 0개인 글. 빌드에서 링크 경고가 묻히지 않게 할 때 쓴다.
종료코드: FAIL 또는 ERROR 가 하나라도 있으면 1."""
import argparse
import html as htmllib
import json
import posixpath
import re
import shutil
import subprocess
import sys
import tempfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
from xml.dom import minidom

import yaml

ARTICLE_RE = re.compile(r"^\d{6}-")  # 글 slug 는 YYMMDD- 로 시작
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
CLAIMS = [  # 확인 안 된 주장 -> WARN
    (r"\d[\d,.]*\s*(?:만|천|백)?\s*원(?![가-힣])", "가격(원)"),
    (r"만\s?원", "만원"),
    (r"\d+(?:\.\d+)?\s*%\s*할인", "% 할인"),
    (r"최저가", "최저가"),
    (r"(?<!\d)1\s?위", "1위"),
    (r"24\s?시간", "24시간"),
    (r"당일\s?출고", "당일 출고"),
    (r"무료\s?대차", "무료 대차"),
    (r"공식\s?(?:서비스)?\s?센터", "공식 서비스센터"),
]
PHONE_RE = re.compile(r"(?<![\d-])(?:0\d{1,2}-\d{3,4}-\d{4}|1[5-9]\d{2}-\d{4})(?![\d-])")


# ---------------------------------------------------------------- HTML 읽기
class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []  # (tag, is_faq_root)
        self.h1 = 0
        self.title = None
        self._in_title = False
        self.metas = []  # attrs dict
        self.links = []  # (tag, attr, value)
        self.imgs = []  # attrs dict
        self.ld = []
        self._script = None  # 'ld' | 'other'
        self._buf = []
        self.text = []
        self.faq_roots = 0
        self.faq_depth = 0
        self.faq_counts = {"summary": 0, "dt": 0, "h3": 0}

    def handle_starttag(self, tag, attrs):
        a = {k: (v or "") for k, v in attrs}
        if tag == "h1":
            self.h1 += 1
        elif tag == "title":
            self._in_title, self.title = True, ""
        elif tag == "meta":
            self.metas.append(a)
        elif tag == "img":
            self.imgs.append(a)
        elif tag == "script":
            self._script = "ld" if a.get("type", "").lower() == "application/ld+json" else "other"
            self._buf = []
        elif tag == "style":
            self._script = "other"
        for k in ("href", "src"):
            if a.get(k):
                self.links.append((tag, k, a[k]))
        for k in ("srcset",):
            for part in a.get(k, "").split(","):
                u = part.strip().split(" ")[0]
                if u:
                    self.links.append((tag, k, u))
        if self.faq_depth and tag in self.faq_counts:
            self.faq_counts[tag] += 1
        if tag in VOID:
            return
        cls = (a.get("class", "") + " " + a.get("id", "")).lower()
        is_root = not self.faq_depth and "faq" in cls
        if is_root:
            self.faq_roots += 1
            self.faq_depth = 1
        elif self.faq_depth:
            self.faq_depth += 1
        self.stack.append((tag, is_root))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        if tag in ("script", "style"):
            if self._script == "ld":
                self.ld.append("".join(self._buf))
            self._script = None
        if not any(t == tag for t, _ in self.stack):
            return
        while self.stack:
            t, root = self.stack.pop()
            if self.faq_depth:
                self.faq_depth -= 1
            if t == tag:
                break

    def handle_data(self, d):
        if self._script:
            self._buf.append(d)
            return
        if self._in_title:
            self.title += d
        self.text.append(d)

    def meta(self, key):
        for m in self.metas:
            if m.get("name", "").lower() == key or m.get("property", "").lower() == key:
                return m.get("content")
        return None


def parse(path):
    raw = path.read_text(encoding="utf-8")
    p = Page()
    p.feed(raw)
    p.close()
    p.raw = raw
    p.canonicals = re.findall(r"<link\b[^>]*\brel=[\"']canonical[\"'][^>]*>", raw, re.I)
    p.canonical = [htmllib.unescape(m) for c in p.canonicals for m in re.findall(r"\bhref=[\"']([^\"']*)[\"']", c)]
    p.visible = re.sub(r"\s+", " ", " ".join(p.text))
    return p


def ld_types(objs):
    out = {}
    def walk(o):
        if isinstance(o, list):
            for x in o:
                walk(x)
        elif isinstance(o, dict):
            t = o.get("@type")
            for x in (t if isinstance(t, list) else [t]):
                if x:
                    out.setdefault(x, []).append(o)
            for k in ("@graph",):
                if k in o:
                    walk(o[k])
    walk(objs)
    return out


# ---------------------------------------------------------------- 컨텍스트
class Ctx:
    def __init__(self, a):
        self.out = Path(a.out_dir)
        self.cases = self.out / "cases"
        if not self.cases.is_dir():
            raise SystemExit(f"{self.cases} 폴더가 없음")
        self.site_yaml = Path(a.site_yaml)
        self.cfg = yaml.safe_load(self.site_yaml.read_text(encoding="utf-8"))
        self.site = self.cfg["site"].rstrip("/") + "/"
        self.phone_digits = {re.sub(r"\D", "", str(self.cfg.get(k, ""))) for k in ("phone", "tel")} - {""}
        self.key = self.cfg.get("key", "")
        mode = a.mode
        if mode == "auto":
            mode = "upload" if "upload" in self.out.resolve().name.lower() else "preview"
        self.mode = mode
        self.assets_dirs = [d for d in [self.out / "assets", Path(a.assets) if a.assets else None] if d and d.is_dir()]
        self.site_dir = Path(a.site_dir) if a.site_dir else None
        self.no_browser = a.no_browser
        self.strict_links = getattr(a, "strict_links", False)
        self.pages = {}  # rel path -> Page
        self.kind = {}  # rel path -> article | list | snippet
        for f in sorted(self.cases.rglob("*.html")):
            rel = f.relative_to(self.out).as_posix()
            self.pages[rel] = parse(f)
            parts = f.relative_to(self.cases).parts
            if f.name == "home-section.html":
                self.kind[rel] = "snippet"
            elif len(parts) == 2 and f.name == "index.html" and ARTICLE_RE.match(parts[0]):
                self.kind[rel] = "article"
            else:
                self.kind[rel] = "list"
        self.posts = {}
        pdir = self.site_yaml.parent / "posts"
        if pdir.is_dir():
            for f in sorted(pdir.glob("*.yaml")):
                try:
                    d = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
                    self.posts[str(d.get("slug") or f.stem)] = d
                except Exception as e:
                    self.posts[f.stem] = {"_error": str(e)}

    def full(self):  # 문서 페이지(조각 제외)
        return [(r, p) for r, p in self.pages.items() if self.kind[r] != "snippet"]

    def url_of(self, rel):
        d = posixpath.dirname(rel)
        return self.site + (d + "/" if d else "")

    def noindex(self, p):
        r = (p.meta("robots") or "").lower()
        return "noindex" in r


def res(items, ok):
    """items: [(level, msg)] -> (status, lines)"""
    lv = {l for l, _ in items}
    st = "FAIL" if "FAIL" in lv else "WARN" if "WARN" in lv else "PASS"
    return st, ([f"[{l}] {m}" for l, m in items] if items else [ok])


# ---------------------------------------------------------------- K1 메타
def k1(c):
    out = []
    for rel, p in c.full():
        if p.h1 != 1:
            out.append(("FAIL", f"{rel}: h1 {p.h1}개 (1개여야 함)"))
        t = (p.title or "").strip()
        if not t:
            out.append(("FAIL", f"{rel}: <title> 없음"))
        elif len(t) > 70:
            out.append(("FAIL", f"{rel}: title {len(t)}자 (70자 이하): {t}"))
        d = (p.meta("description") or "").strip()
        if not d:
            out.append(("FAIL", f"{rel}: meta description 없음"))
        elif not 50 <= len(d) <= 160:
            out.append(("FAIL", f"{rel}: description {len(d)}자 (50~160자)"))
        if len(p.canonical) != 1:
            out.append(("FAIL", f"{rel}: canonical {len(p.canonical)}개"))
        else:
            cu = p.canonical[0]
            if not (cu.startswith(c.site) and cu.endswith("/")):
                out.append(("FAIL", f"{rel}: canonical '{cu}' 가 {c.site} 로 시작하고 / 로 끝나야 함"))
            elif cu != c.url_of(rel):
                out.append(("FAIL", f"{rel}: canonical '{cu}' 가 파일 위치 주소 {c.url_of(rel)} 와 다름"))
        og = p.meta("og:image")
        if not og:
            out.append(("FAIL", f"{rel}: og:image 없음"))
        elif not re.match(r"^https?://[^/]+/", og):
            out.append(("FAIL", f"{rel}: og:image 절대 URL 아님: {og}"))
        for k in ("og:title", "og:description", "og:url", "og:type"):
            if not p.meta(k):
                out.append(("WARN", f"{rel}: {k} 없음"))
        ou = p.meta("og:url")
        if ou and p.canonical and ou != p.canonical[0]:
            out.append(("WARN", f"{rel}: og:url '{ou}' 와 canonical 다름"))
    n = len(c.full())
    return res(out, f"{n}페이지 h1 1개·title≤70·description 50~160·canonical·og:image 정상")


# ---------------------------------------------------------------- K2 JSON-LD
def k2(c):
    out = []
    for rel, p in c.full():
        objs = []
        for i, s in enumerate(p.ld):
            try:
                objs.append(json.loads(s))
            except Exception as e:
                out.append(("FAIL", f"{rel}: JSON-LD {i+1}번째 파싱 실패: {e}"))
        if not p.ld:
            out.append(("FAIL", f"{rel}: JSON-LD 없음"))
            continue
        types = ld_types(objs)
        kind = c.kind[rel]
        if kind == "article":
            for need in ("BlogPosting", "BreadcrumbList"):
                if need not in types:
                    out.append(("FAIL", f"{rel}: {need} 없음"))
            for bp in types.get("BlogPosting", []):
                for f in ("headline", "datePublished", "image"):
                    if not bp.get(f):
                        out.append(("WARN", f"{rel}: BlogPosting.{f} 없음"))
        else:
            for need in ("CollectionPage", "ItemList"):
                if need not in types:
                    out.append(("WARN", f"{rel}: 목록에 {need} 없음"))
        for bl in types.get("BreadcrumbList", []):
            for it in bl.get("itemListElement", []):
                u = it.get("item")
                u = u.get("@id") if isinstance(u, dict) else u
                if u and not str(u).startswith(c.site):
                    out.append(("FAIL", f"{rel}: BreadcrumbList 주소가 {c.site} 밖: {u}"))
        # FAQ: 화면 vs JSON-LD
        qs = [q for fp in types.get("FAQPage", []) for q in (fp.get("mainEntity") or [])]
        qs = qs if isinstance(qs, list) else [qs]
        fc = p.faq_counts
        nvis = fc["summary"] or fc["dt"] or fc["h3"]
        if p.faq_roots and nvis:
            if "FAQPage" not in types:
                out.append(("FAIL", f"{rel}: 화면에 FAQ {nvis}개 있는데 FAQPage 없음"))
            elif len(qs) != nvis:
                out.append(("FAIL", f"{rel}: FAQ 질문 수 화면 {nvis}개 / FAQPage {len(qs)}개"))
        elif "FAQPage" in types and kind == "article":
            out.append(("FAIL", f"{rel}: FAQPage 가 있는데 화면에 FAQ 블록(class/id 'faq') 없음"))
        vis = re.sub(r"\s+", "", p.visible)
        for q in qs:
            name = re.sub(r"\s+", "", htmllib.unescape(str(q.get("name", ""))))
            if name and name not in vis:
                out.append(("FAIL", f"{rel}: FAQPage 질문이 화면에 없음: {q.get('name')}"))
    return res(out, "JSON-LD 모두 파싱, 글 BlogPosting+BreadcrumbList, FAQ 화면·구조화 일치, 목록 CollectionPage/ItemList")


# ---------------------------------------------------------------- K3 내부 링크
def resolve(c, rel, url):
    """-> (kind, target_path_from_out_root) 또는 None(검사 안 함)"""
    if url.startswith(("#", "mailto:", "tel:", "sms:", "javascript:", "data:")):
        return None
    if c.kind.get(rel) == "snippet":
        base = ""  # 홈에 붙는 조각: root = ""
    else:
        base = posixpath.dirname(rel)
    sp = urlsplit(url)
    if sp.scheme in ("http", "https") or url.startswith("//"):
        full = url if sp.scheme else "https:" + url
        if not full.startswith(c.site):
            return None  # 외부 링크
        path = urlsplit(full).path.lstrip("/")
    elif sp.scheme:
        return None
    elif url.startswith("/"):
        path = sp.path.lstrip("/")
    else:
        path = posixpath.normpath(posixpath.join(base, sp.path)) if sp.path else rel
        if sp.path.endswith("/") and path not in (".", ""):
            path += "/"
        if path.startswith(".."):
            return ("outside", path)
    path = unquote(path)
    if path in (".", ""):
        path = ""
    return ("ok", path)


def exists_under(root, path):
    p = root / path
    if path == "" or path.endswith("/") or p.is_dir():
        return (p / "index.html").is_file() or (p / "index.php").is_file()
    return p.is_file()


def k3(c):
    out, n = [], 0
    for rel, p in c.pages.items():
        for tag, attr, url in p.links:
            r = resolve(c, rel, url)
            if not r:
                continue
            n += 1
            kind, path = r
            if kind == "outside":
                out.append(("FAIL", f"{rel}: {url} 가 사이트 루트 밖으로 나감"))
                continue
            if path.startswith("cases/") or path == "cases":
                if not exists_under(c.out, path):
                    out.append(("FAIL", f"{rel}: 깨진 링크 {url} -> {path}"))
            elif path.startswith("assets/"):
                if not any(exists_under(d, path[len("assets/"):]) for d in c.assets_dirs):
                    out.append(("WARN", f"{rel}: 사진/파일 없음 {path} (out_dir/assets, --assets 에서 못 찾음)"))
            else:
                if exists_under(c.out, path) or (c.site_dir and exists_under(c.site_dir, path)):
                    continue
                out.append(("WARN", f"{rel}: /cases/ 밖 링크 {url} -> /{path} 확인 못 함(--site-dir 로 사이트 본체 지정)"))
    # 고아 글: 다른 글(관련 사례)·목록에서 들어오는 링크 수. 다른 '글'에서 0개면 WARN
    arts = {posixpath.dirname(r) + "/": r for r, k in c.kind.items() if k == "article"}
    inbound = {d: 0 for d in arts}
    for rel, p in c.pages.items():
        if c.kind.get(rel) != "article":
            continue
        seen = set()
        for tag, attr, url in p.links:
            if tag != "a":
                continue
            r = resolve(c, rel, url)
            if r and r[0] == "ok" and r[1] in inbound and r[1] != posixpath.dirname(rel) + "/" and r[1] not in seen:
                seen.add(r[1])
                inbound[r[1]] += 1
    orphans = sorted(d for d, k in inbound.items() if k == 0)
    for d in orphans:
        out.append(("WARN", f"{d}: 다른 글에서 들어오는 링크 0개(관련 사례에 안 걸림)"))
    if c.strict_links:
        out = [("FAIL" if l == "WARN" else l, m + (" [--strict-links]" if l == "WARN" else "")) for l, m in out]
    lo = min(inbound.values()) if inbound else 0
    return res(out, f"내부 링크 {n}개 모두 존재, 글 {len(inbound)}편 모두 다른 글에서 링크 {lo}개 이상")


# ---------------------------------------------------------------- K4 이미지
def k4(c):
    out, n = [], 0
    for rel, p in c.pages.items():
        for im in p.imgs:
            n += 1
            src = im.get("src", "?")
            if "alt" not in im:
                out.append(("FAIL", f"{rel}: alt 없음 {src}"))
            elif not im["alt"].strip():
                out.append(("FAIL", f"{rel}: 빈 alt {src}"))
            for k in ("width", "height"):
                if not im.get(k, "").strip():
                    out.append(("FAIL", f"{rel}: {k} 없음 {src}"))
    return res(out, f"이미지 {n}장 모두 alt·width·height 있음")


# ---------------------------------------------------------------- K5 sitemap
def k5(c):
    out = []
    sm = c.cases / "sitemap-cases.xml"
    if not sm.is_file():
        return "FAIL", ["[FAIL] cases/sitemap-cases.xml 없음"]
    try:
        dom = minidom.parseString(sm.read_bytes())
    except Exception as e:
        return "FAIL", [f"[FAIL] sitemap-cases.xml 파싱 실패: {e}"]
    locs = []
    for u in dom.getElementsByTagName("url"):
        ls = u.getElementsByTagName("loc")
        loc = ls[0].firstChild.data.strip() if ls and ls[0].firstChild else ""
        lm = u.getElementsByTagName("lastmod")
        lmv = lm[0].firstChild.data.strip() if lm and lm[0].firstChild else ""
        locs.append(loc)
        if not lmv:
            out.append(("FAIL", f"lastmod 없음: {loc}"))
        elif not re.match(r"^\d{4}-\d{2}-\d{2}", lmv):
            out.append(("FAIL", f"lastmod 형식 이상 '{lmv}': {loc}"))
    if len(locs) != len(set(locs)):
        out.append(("FAIL", "sitemap 에 중복 주소"))
    want = {c.url_of(r) for r, p in c.full() if not c.noindex(p)}
    arts = {c.url_of(r) for r, p in c.full() if c.kind[r] == "article" and not c.noindex(p)}
    have = set(locs)
    for u in sorted(arts - have):
        out.append(("FAIL", f"글이 sitemap 에 없음: {u}"))
    for u in sorted(want - arts - have):
        out.append(("FAIL", f"목록 페이지가 sitemap 에 없음: {u}"))
    for u in sorted(have - want):
        if not u.startswith(c.site):
            out.append(("FAIL", f"sitemap 주소가 {c.site} 밖: {u}"))
            continue
        path = u[len(c.site):]
        noidx = [r for r, p in c.full() if c.url_of(r) == u and c.noindex(p)]
        if noidx:
            out.append(("FAIL", f"noindex 페이지가 sitemap 에 있음: {u}"))
        elif not exists_under(c.out, path):
            out.append(("FAIL", f"sitemap 주소에 해당하는 파일 없음: {u}"))
    for p in dom.getElementsByTagName("image:loc"):
        u = p.firstChild.data.strip() if p.firstChild else ""
        if not u.startswith(c.site):
            out.append(("WARN", f"sitemap 이미지 주소가 {c.site} 밖: {u}"))
    return res(out, f"sitemap {len(locs)}개 주소 = 실제 페이지 {len(want)}개 (글 {len(arts)}), lastmod 모두 있음")


# ---------------------------------------------------------------- K6 금지어·전화
def text_sources(c):
    for rel, p in c.pages.items():
        metas = " ".join(m.get("content", "") for m in p.metas)
        yield rel, p.visible + " " + metas + " " + (p.title or "") + " " + " ".join(p.ld), p
    for n in ("llms-cases.txt", "feed.xml"):
        f = c.cases / n
        if f.is_file():
            yield "cases/" + n, htmllib.unescape(f.read_text(encoding="utf-8")), None


def k6(c):
    out = []
    for rel, s, p in text_sources(c):
        spans = []
        for pat, label in CLAIMS:
            for m in re.finditer(pat, s):
                if any(a < m.end() and m.start() < b for a, b in spans):
                    continue  # 같은 곳을 다른 규칙이 이미 잡음
                spans.append(m.span())
                ctx = s[max(0, m.start() - 20):m.end() + 12].replace("\n", " ")
                out.append(("WARN", f"{rel}: 확인 안 된 주장 '{label}' … {ctx.strip()}"))
        nums = [m.group(0) for m in PHONE_RE.finditer(s)]
        if p is not None:
            nums += [u[4:] for _, _, u in p.links if u.startswith("tel:")]
        for num in nums:
            d = re.sub(r"\D", "", num)
            if d.startswith("82"):
                d = "0" + d[2:] if not d[2:].startswith("1") else d[2:]
            if d not in c.phone_digits:
                out.append(("FAIL", f"{rel}: site.yaml 과 다른 전화번호 {num} (정본 {c.cfg.get('phone')})"))
    return res(out, f"확인 안 된 주장 없음, 전화번호 모두 {c.cfg.get('phone')}")


# ---------------------------------------------------------------- K7 draft
def k7(c):
    out = []
    noidx = [r for r, p in c.full() if c.noindex(p)]
    built = {Path(r).parts[1] for r in c.pages if c.kind[r] == "article"}
    if c.mode == "upload":
        for r in noidx:
            out.append(("FAIL", f"업로드본에 noindex 페이지(드래프트 섞임): {r}"))
        for slug, d in c.posts.items():
            if d.get("_error"):
                out.append(("WARN", f"posts/{slug}.yaml 읽기 실패: {d['_error']}"))
            elif d.get("draft") and slug in built:
                out.append(("FAIL", f"draft: true 글이 업로드본에 있음: {slug}"))
            elif not d.get("draft") and slug not in built:
                out.append(("WARN", f"공개 글인데 업로드본에 없음: {slug}"))
        ok = f"업로드 모드: noindex 0, draft 글 0 (posts {len(c.posts)}개 대조)"
    else:
        for slug, d in c.posts.items():
            if d.get("draft") and slug in built:
                rel = f"cases/{slug}/index.html"
                if rel in c.pages and not c.noindex(c.pages[rel]):
                    out.append(("WARN", f"미리보기의 draft 글에 noindex 없음: {slug}"))
        ok = f"미리보기 모드: noindex {len(noidx)}페이지(허용), draft 표시 정상"
    return res(out, ok)


# ---------------------------------------------------------------- K8 화면
JS = r"""
const [, , pwPath, list] = process.argv;
const { chromium } = await import(pwPath);
const files = JSON.parse(await (await import('fs')).promises.readFile(list, 'utf8'));
const b = await chromium.launch();
const out = {};
for (const f of files) {
  for (const w of [375, 1280]) {
    const p = await b.newPage({ viewport: { width: w, height: 900 } });
    try {
      await p.goto('file://' + f, { waitUntil: 'load', timeout: 20000 });
      await p.evaluate(async () => {
        document.querySelectorAll('img[loading=lazy]').forEach(i => i.loading = 'eager');
        document.querySelectorAll('details').forEach(d => d.open = true);
        await Promise.all([...document.images].map(i => i.complete ? 0 : new Promise(r => { i.onload = i.onerror = r; setTimeout(r, 4000); })));
      });
      out[f + '@' + w] = await p.evaluate(() => ({
        sw: document.documentElement.scrollWidth, iw: window.innerWidth,
        broken: [...document.images].filter(i => !(i.complete && i.naturalWidth > 0)).map(i => i.getAttribute('src')),
      }));
    } catch (e) { out[f + '@' + w] = { error: String(e) }; }
    await p.close();
  }
}
await b.close();
console.log(JSON.stringify(out));
"""


def k8(c):
    if c.no_browser:
        return "SKIP", ["--no-browser 로 건너뜀(통과 아님)"]
    pw = None
    try:
        root = subprocess.run(["npm", "root", "-g"], capture_output=True, text=True, timeout=30).stdout.strip()
        cand = Path(root) / "playwright" / "index.mjs"
        pw = cand if cand.exists() else None
    except Exception:
        pass
    if not pw:
        raise FileNotFoundError("node playwright 없음(npm root -g)/playwright/index.mjs")
    tmp = Path(tempfile.mkdtemp())
    try:
        site = tmp / "site"
        site.mkdir()
        (site / "cases").symlink_to(c.cases.resolve())
        if c.assets_dirs:
            (site / "assets").symlink_to(c.assets_dirs[0].resolve())
        files = [str(site / r) for r, _ in c.full()]
        (tmp / "list.json").write_text(json.dumps(files), encoding="utf-8")
        (tmp / "k8.mjs").write_text(JS, encoding="utf-8")
        r = subprocess.run(["node", str(tmp / "k8.mjs"), str(pw), str(tmp / "list.json")],
                           capture_output=True, text=True, timeout=60 + 20 * len(files))
        if r.returncode != 0:
            raise RuntimeError("k8.mjs 실패: " + (r.stderr or r.stdout)[-400:])
        m = json.loads(r.stdout.strip().splitlines()[-1])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    out = []
    for k, v in m.items():
        name = k.replace(str(site) + "/", "")
        if "error" in v:
            out.append(("FAIL", f"{name}: 열기 실패 {v['error'][:150]}"))
            continue
        if v["sw"] > v["iw"]:
            out.append(("FAIL", f"{name}: 가로 스크롤 scrollWidth {v['sw']} > {v['iw']}"))
        for src in v["broken"]:
            rel = name.rsplit("@", 1)[0]
            rr = resolve(c, rel, src or "")
            missing = rr and rr[1].startswith("assets/") and not any(exists_under(d, rr[1][7:]) for d in c.assets_dirs)
            out.append(("WARN" if missing else "FAIL",
                        f"{name}: 깨진 이미지 {src}" + (" (파일 없음, K3 참고)" if missing else "")))
    return res(out, f"{len(m)//2}페이지 × 375·1280: 가로 스크롤·깨진 이미지 없음")


CHECKS = [("K1", "메타(h1·title·설명·canonical·og)", k1), ("K2", "JSON-LD", k2), ("K3", "내부 링크", k3),
          ("K4", "이미지 alt·크기", k4), ("K5", "sitemap-cases.xml", k5), ("K6", "금지어·전화번호", k6),
          ("K7", "draft 섞임", k7), ("K8", "화면 375·1280", k8)]


def main():
    ap = argparse.ArgumentParser(description="수리사례 /cases/ 출력 검사 K1~K8")
    ap.add_argument("out_dir")
    ap.add_argument("site_yaml")
    ap.add_argument("--mode", choices=["auto", "upload", "preview"], default="auto")
    ap.add_argument("--assets")
    ap.add_argument("--site-dir")
    ap.add_argument("--no-browser", action="store_true")
    ap.add_argument("--only", default=",".join(k for k, _, _ in CHECKS))
    ap.add_argument("--all", action="store_true", help="문제를 전부 출력")
    ap.add_argument("--strict-links", action="store_true", help="K3 링크 WARN(확인 못 한 링크·없는 사진·고아 글)을 FAIL 로")
    a = ap.parse_args()
    c = Ctx(a)
    kinds = {k: sum(1 for v in c.kind.values() if v == k) for k in ("article", "list", "snippet")}
    print(f"검사 대상: {c.out}  (모드 {c.mode}, 사이트 {c.site}, 글 {kinds['article']} · 목록 {kinds['list']} · 조각 {kinds['snippet']})")
    only = a.only.split(",")
    rows = []
    for k, title, f in CHECKS:
        if k not in only:
            continue
        try:
            st, lines = f(c)
        except Exception as e:
            st, lines = "ERROR", [f"{type(e).__name__}: {e}"]
        rows.append((k, title, st, len([l for l in lines if l.startswith("[")])))
        print(f"\n{k} {title}: {st}")
        show = lines if a.all else lines[:12]
        for l in show:
            print("   " + l)
        if len(lines) > len(show):
            print(f"   … 외 {len(lines) - len(show)}줄 (--all 로 전부)")
    print("\n| 코드 | 항목 | 결과 | 문제 수 |\n|---|---|---|---|")
    for k, title, st, n in rows:
        print(f"| {k} | {title} | {st} | {n} |")
    cnt = {s: sum(1 for r in rows if r[2] == s) for s in ("PASS", "WARN", "FAIL", "SKIP", "ERROR")}
    print("요약:", {k: v for k, v in cnt.items() if v})
    sys.exit(1 if cnt["FAIL"] or cnt["ERROR"] else 0)


if __name__ == "__main__":
    main()
