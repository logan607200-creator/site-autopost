#!/usr/bin/env python3
"""수리사례(/cases/) 정적 생성기 — 그릿서비스·로건서비스 공통. 약속은 ../SPEC.md.

사용:
  python3 make_cases.py ../grit  ../build/grit-preview --preview --copy-assets   # draft 포함, noindex
  python3 make_cases.py ../grit  ../build/grit-upload                           # draft 제외 (서버용)
  옵션: --assets <dir>  사진 크기를 읽을 로컬 사이트 루트(src 가 assets/... 이므로 그 상위 폴더)
        --copy-assets   쓰인 사진을 out_dir 에 복사(미리보기용)
출력: out_dir/cases/ 아래 index.html, {카테고리}/index.html, {slug}/index.html, case.css,
      home-section.html, sitemap-cases.xml, llms-cases.txt, feed.xml
      case.css 는 모든 페이지 <style> 에 인라인으로 넣는다(첫 표시 속도). 파일도 그대로 출력(다른 곳에서 쓸 수 있게).
      카드용 썸네일: 사진 옆 thumbs/ 폴더에 폭 THUMB_W webp 를 만든다(없거나 원본보다 오래됐을 때만).
검증 실패 시 종료 코드 1. 경고(seo_title 70자 초과 등)는 출력만 한다.
"""
import argparse, datetime as dt, json, posixpath, re, shutil, sys
from email.utils import format_datetime
from pathlib import Path
from xml.sax.saxutils import escape as xesc

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup, escape

KNOWN_ORG_IDS = {"grit": "#grit-service", "logan": "#logan-service"}  # 홈 JSON-LD 와 같은 @id
KNOWN_LABELS = {"grit": "수리사례", "logan": "정비사례"}                  # site.yaml cases_label 이 없을 때
SLUG_RE = re.compile(r"^\d{6}-[a-z0-9]+(?:-[a-z0-9]+){2,}$")
REQUIRED = ["slug", "date", "category", "title", "seo_title", "description", "summary", "car", "sections"]  # cover 는 선택(없으면 site.default_image 를 og 이미지로)
DEFAULT_WH = (1200, 800)
THUMB_W = 420                     # 목록·홈 카드용 썸네일 폭(원본은 글 본문용으로 그대로)
errors, warnings = [], []


def err(msg): errors.append(msg)
def warn(msg): warnings.append(msg)


# ---------- 필터 ----------
LINK_RE = re.compile(r"(https?://[^\s<>()\"]+[^\s<>()\".,]|(?<![\w/.])(?:www\.)?(?:loganservice|gritservice)\.co\.kr(?:/[^\s<>()\"]*[^\s<>()\".,])?)")


def _links(h):
    """이스케이프된 글 안의 주소(https://…, loganservice.co.kr 등)를 <a> 로. 다른 사이트는 새 창."""
    def a(m):
        u = m.group(1)
        href = u if u.startswith("http") else "https://" + u
        return f'<a href="{href}" target="_blank" rel="noopener">{u}</a>'
    return LINK_RE.sub(a, h)


def autolink(text):
    return Markup(_links(str(escape(str(text or "")))))


def para(text):
    """빈 줄 = 문단, **굵게** → <strong>, 줄바꿈 → <br>, 주소 → 링크. 나머지는 모두 이스케이프."""
    if not text:
        return Markup("")
    out = []
    for block in re.split(r"\n\s*\n", str(text).strip()):
        h = _links(str(escape(block.strip())))
        h = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", h)
        out.append("<p>" + h.replace("\n", "<br>\n") + "</p>")
    return Markup("\n".join(out))


def to_date(v):
    if isinstance(v, dt.datetime):
        return v.date()
    if isinstance(v, dt.date):
        return v
    return dt.date.fromisoformat(str(v).strip())


# ---------- 이미지 ----------
class Images:
    def __init__(self, site_dir, assets_dir):
        self.roots = [p for p in [assets_dir, site_dir.parent, site_dir] if p]
        self.used, self.cache = {}, {}

    def find(self, src):
        rel = src.lstrip("/")
        for r in self.roots:
            for cand in (r / rel, r / rel.split("assets/", 1)[-1]):
                if cand.is_file():
                    return cand
        return None

    def size(self, src):
        if src not in self.cache:
            f, wh = self.find(src), DEFAULT_WH
            if f:
                try:
                    from PIL import Image
                    with Image.open(f) as im:
                        wh = im.size
                except Exception as e:
                    warn(f"사진 크기 읽기 실패 {src}: {e}")
            self.cache[src] = (f, wh)
        f, wh = self.cache[src]
        self.used[src] = f
        return wh

    def fill(self, photo):
        if isinstance(photo, dict) and photo.get("src"):
            photo.setdefault("w", self.size(photo["src"])[0])
            photo.setdefault("h", self.size(photo["src"])[1])

    def thumb(self, photo):
        """카드용 썸네일(폭 THUMB_W)을 사진 옆 thumbs/ 에 만들고 photo['thumb'] 등에 넣는다. 원본이 작거나 없으면 안 만든다."""
        if not (isinstance(photo, dict) and photo.get("src")) or "thumb" in photo:
            return
        self.size(photo["src"])
        f, (w, h) = self.cache[photo["src"]]
        if not f or w <= THUMB_W:
            return
        src = photo["src"]
        tsrc = posixpath.join(posixpath.dirname(src), "thumbs", posixpath.basename(src).rsplit(".", 1)[0] + ".webp")
        dst = f.parent / "thumbs" / (f.stem + ".webp")
        th = round(h * THUMB_W / w)
        if not dst.is_file() or dst.stat().st_mtime < f.stat().st_mtime:
            try:
                from PIL import Image
                dst.parent.mkdir(parents=True, exist_ok=True)
                with Image.open(f) as im:
                    im.convert("RGB").resize((THUMB_W, th), Image.LANCZOS).save(dst, "WEBP", quality=78, method=6)
            except Exception as e:
                warn(f"썸네일 만들기 실패 {src}: {e}")
                return
        self.used[tsrc] = dst
        photo.update(thumb=tsrc, thumb_w=THUMB_W, thumb_h=th)


# ---------- 읽기·검증 ----------
def load_site(site_dir):
    site = yaml.safe_load((site_dir / "site.yaml").read_text(encoding="utf-8")) or {}
    for k in ("key", "name", "site", "categories"):
        if not site.get(k):
            err(f"site.yaml: '{k}' 없음")
    site["site"] = str(site.get("site", "")).rstrip("/") + "/"
    site.setdefault("org_id", site["site"] + KNOWN_ORG_IDS.get(site.get("key"), "#org").lstrip("/"))
    if site["org_id"].startswith("#"):
        site["org_id"] = site["site"] + site["org_id"]
    lab = site.setdefault("cases_label", KNOWN_LABELS.get(site.get("key"), "수리사례"))
    if not site.get("cases_intro"):
        regs = "·".join((site.get("regions") or [])[:4])
        site["cases_intro"] = (f"{site.get('name', '')} {lab}. {regs + '에서' if regs else '고객님이'} 맡겨 주신 차량의 "
                               "실제 기록입니다. 어떤 증상으로 들어왔고 무엇을 확인해 어떻게 고쳤는지 한 건씩 정리했습니다.")
    return site


TITLE_MAX, DESC_MAX = 40, 80


def fit_title(t, title, name):
    """제목이 40자를 넘으면 '본제목 | 사이트이름' → 'title | 사이트이름' → 본제목 → title 순으로 맞는 것을 쓴다."""
    t = str(t).strip()
    if len(t) <= TITLE_MAX:
        return t
    base = re.sub(r"\s*\|\s*[^|]*$", "", t).strip()
    for c in (f"{base} | {name}", f"{title} | {name}", base, str(title)):
        if len(c) <= TITLE_MAX:
            return c
    return str(title)[:TITLE_MAX - 1].rstrip() + "…"


def fit_desc(d):
    """설명이 80자를 넘으면 앞 문장부터 80자 안에 들어가는 만큼만 쓰고, 그래도 길면 단어 단위로 자른다."""
    d = " ".join(str(d).split())
    if len(d) <= DESC_MAX:
        return d
    out = ""
    for sent in re.split(r"(?<=[.])\s+", d):
        if len((out + " " + sent).strip()) > DESC_MAX:
            break
        out = (out + " " + sent).strip()
    if len(out) >= 40:
        return out
    cut = d[:DESC_MAX - 1]
    return (cut[:cut.rfind(" ")] if " " in cut else cut).rstrip(" ,·") + "…"


def check_post(p, fname, cats):
    where = f"posts/{fname}"
    for k in REQUIRED:
        if p.get(k) in (None, "", [], {}):
            err(f"{where}: 필수 필드 '{k}' 없음")
    slug = str(p.get("slug", ""))
    if slug and not SLUG_RE.match(slug):
        err(f"{where}: slug 형식 틀림 '{slug}' (예: 261022-kia-k5-rear-bumper, 소문자·숫자·하이픈)")
    if slug and Path(fname).stem != slug:
        warn(f"{where}: 파일 이름과 slug 가 다름 ({slug})")
    try:
        d = to_date(p.get("date"))
        p["date"] = d
        if slug[:6].isdigit() and slug[:6] != d.strftime("%y%m%d"):
            warn(f"{where}: slug 날짜 {slug[:6]} ≠ date {d}")
    except Exception:
        err(f"{where}: date 형식 틀림 '{p.get('date')}' (YYYY-MM-DD)")
        p["date"] = dt.date.min
    if p.get("category") and p["category"] not in cats:
        err(f"{where}: category '{p['category']}' 가 site.yaml 에 없음 (가능: {', '.join(cats)})")
    # 네이버 서치어드바이저 기준: 제목 40자, 설명 80자 이내. 넘으면 경고만 하고 fit_* 로 줄여 쓴다.
    if len(str(p.get("seo_title", ""))) > TITLE_MAX:
        warn(f"{where}: seo_title {len(p['seo_title'])}자 ({TITLE_MAX}자 초과 → 자동으로 줄임)")
    dl = len(str(p.get("description", "")))
    if p.get("description") and dl < 50:
        err(f"{where}: description {dl}자 (50~{DESC_MAX}자여야 함)")
    elif dl > DESC_MAX:
        warn(f"{where}: description {dl}자 ({DESC_MAX}자 초과 → 자동으로 줄임)")
    car = p.get("car") or {}
    if not isinstance(car, dict) or not car.get("brand") or not car.get("model"):
        err(f"{where}: car.brand, car.model 필요")
    secs = p.get("sections") or []
    if len(secs) < 2:
        err(f"{where}: sections 가 {len(secs)}개 (2개 이상)")
    photos = [p["cover"]] if p.get("cover") else []
    for i, s in enumerate(secs, 1):
        if not s.get("h2"):
            err(f"{where}: sections[{i}] h2 없음")
        photos += s.get("photos") or []
    for ph in photos:
        if not isinstance(ph, dict) or not ph.get("src"):
            err(f"{where}: 사진 src 없음 {ph}")
        elif not str(ph.get("alt", "")).strip():
            err(f"{where}: 사진 alt 없음 ({ph['src']})")
    for i, f in enumerate(p.get("faq") or [], 1):
        if not (isinstance(f, dict) and f.get("q") and f.get("a")):
            err(f"{where}: faq[{i}] q/a 필요")
    if len(p.get("faq") or []) > 3:
        warn(f"{where}: faq {len(p['faq'])}개 (약속은 0~3개)")


def load_posts(site_dir, cats):
    posts, seen = [], {}
    for f in sorted((site_dir / "posts").glob("*.yaml")):
        try:
            p = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as e:
            err(f"posts/{f.name}: YAML 오류 {e}")
            continue
        check_post(p, f.name, cats)
        s = p.get("slug")
        if s in seen:
            err(f"posts/{f.name}: slug 중복 '{s}' ({seen[s]})")
        seen[s] = f.name
        posts.append(p)
    for p in posts:
        for r in p.get("related") or []:
            if r not in seen:
                err(f"posts/{seen.get(p.get('slug'), '?')}: related '{r}' 인 글이 없음")
    return posts


# ---------- 가공 ----------
def enrich(p, site, cats, imgs):
    cat = cats.get(p["category"], {})
    p["url"] = f"cases/{p['slug']}/"                 # 사이트 루트 기준. 템플릿에서 {{ root }}{{ p.url }}
    p["abs_url"] = site["site"] + p["url"]
    d = p["date"]
    p["date_iso"] = d.isoformat()
    p["date_kr"] = f"{d.year}년 {d.month}월 {d.day}일"
    p["category_name"] = cat.get("name", p["category"])
    p["category_slug"] = cat.get("slug", p["category"])
    p["category_url"] = f"cases/{p['category_slug']}/"
    p.setdefault("faq", []); p.setdefault("tags", []); p.setdefault("symptoms", []); p.setdefault("work", [])
    p["draft"] = bool(p.get("draft"))
    if p.get("cover"):
        imgs.fill(p["cover"])
    else:
        p["cover"] = None
    p["photos_all"] = [p["cover"]] if p["cover"] else []
    for s in p["sections"]:
        s.setdefault("text", ""); s.setdefault("photos", [])
        for ph in s["photos"]:
            imgs.fill(ph)
            p["photos_all"].append(ph)
    p["card_img"] = p["photos_all"][0] if p["photos_all"] else None   # 카드 사진 = 첫 사진(썸네일 포함)
    if p["card_img"]:
        imgs.thumb(p["card_img"])


def og_image(site, p):
    """글: 첫 사진. 사진 없는 글(photos_pending)은 공통 대표 사진이 아니라 사이트 로고(그 글 사진인 척하지 않게).
    목록: 첫 글 사진, 없으면 site.default_image."""
    if p and p.get("photos_all"):
        return absu(site, p["photos_all"][0]["src"])
    if p is not None:
        return absu(site, site.get("logo") or site.get("default_image") or "")
    return absu(site, site.get("default_image") or site.get("logo") or "")


# ---------- 관련 사례 ----------
REL_N = 3
_STOP = {"교환", "교체", "수리", "점검", "작업", "정비", "입고", "출고", "사례", "확인", "원인", "순서", "함께", "그리고",
         "앞", "뒤", "전", "후", "중", "및", "—", "-", "·"}


def _model(p):
    m = str((p.get("car") or {}).get("model", "")).strip()
    return m.split(" ")[0].lower() if m else ""


def _words(p):
    """증상·부위 비교용 낱말: 제목·증상·작업·태그에서 차종 이름과 흔한 낱말을 뺀 것."""
    car = " ".join(str(v) for v in (p.get("car") or {}).values()).lower()
    raw = " ".join([str(p.get("title", ""))] + [str(x) for x in (p.get("symptoms") or []) + (p.get("work") or []) + (p.get("tags") or [])])
    out = set()
    for w in re.split(r"[\s,·/()\[\]—\-]+", raw.lower()):
        w = re.sub(r"(을|를|이|가|은|는|의|과|와|로|으로)$", "", w)
        if len(w) >= 2 and w not in _STOP and w not in car and not w.isdigit():
            out.add(w)
    return out


def _rank(p, posts):
    """p 와 가까운 순: 같은 모델 → 증상·부위 낱말 겹침 → 같은 분류 → 날짜 가까운 글."""
    pw, pm = _words(p), _model(p)
    def key(q):
        return (-(pm != "" and _model(q) == pm), -len(pw & _words(q)), -(q["category"] == p["category"]),
                abs((q["date"] - p["date"]).days), q["slug"])
    return sorted((q for q in posts if q is not p), key=key)


def assign_related(posts):
    """글마다 관련 사례 REL_N 개. yaml related 를 먼저 쓰고 _rank 순으로 채운 뒤,
    다른 글에서 들어오는 링크가 0개인 글이 없도록 바꿔 넣는다(들어오는 링크가 2개 이상인 자리만 내준다)."""
    by = {q["slug"]: q for q in posts}
    rank = {q["slug"]: _rank(q, posts) for q in posts}
    rel = {}
    for p in posts:
        fixed = [by[s] for s in (p.get("related") or []) if s in by and by[s] is not p][:REL_N]
        p["_fixed"] = {q["slug"] for q in fixed}
        r = list(fixed)
        for q in rank[p["slug"]]:
            if len(r) >= REL_N:
                break
            if q not in r:
                r.append(q)
        rel[p["slug"]] = r
    if len(posts) > REL_N:
        for _ in range(len(posts) * 2):
            inc = {q["slug"]: 0 for q in posts}
            for r in rel.values():
                for q in r:
                    inc[q["slug"]] += 1
            orphans = [s for s, n in inc.items() if n == 0]
            if not orphans:
                break
            o = by[orphans[0]]
            done = False
            for p in rank[o["slug"]]:        # o 와 가장 가까운 글부터: 그 글의 관련 사례 중 자리 하나를 o 에게
                r = rel[p["slug"]]
                for i in range(len(r) - 1, -1, -1):
                    q = r[i]
                    if q["slug"] not in p["_fixed"] and inc[q["slug"]] >= 2:
                        r[i] = o
                        done = True
                        break
                if done:
                    break
            if not done:
                warn(f"관련 사례: {o['slug']} 로 들어오는 링크를 만들 자리가 없음")
                break
    for p in posts:
        p["related_posts"] = rel[p["slug"]]
    return rel


def absu(site, src):
    return src if src.startswith("http") else site["site"] + src.lstrip("/")


def org(site):
    o = {"@type": "Organization", "@id": site["org_id"], "name": site["name"], "url": site["site"]}
    if site.get("logo"):
        o["logo"] = {"@type": "ImageObject", "url": absu(site, site["logo"])}
    return o


def crumbs(site, items):
    return {"@type": "BreadcrumbList", "@id": items[-1][1] + "#breadcrumb", "itemListElement": [
        {"@type": "ListItem", "position": i, "name": n, "item": u} for i, (n, u) in enumerate(items, 1)]}


def ld_dump(graph):
    s = json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, indent=1)
    return Markup(s.replace("</", "<\\/"))


def post_jsonld(p, site):
    if not p["photos_all"]:
        warn(f"posts/{p['slug']}.yaml: 사진 없음(photos_pending) → 대표 이미지는 사이트 로고로 대신함. 블로그 사진을 넣어 주세요.")
    image = [absu(site, ph["src"]) for ph in p["photos_all"]] or \
        {"@type": "ImageObject", "url": absu(site, site.get("logo") or site.get("default_image") or "")}
    u, car = p["abs_url"], p["car"]
    carnode = {"@type": "Car", "brand": {"@type": "Brand", "name": str(car["brand"])}, "model": str(car["model"])}
    if car.get("year"):
        carnode["vehicleModelDate"] = str(car["year"])
    if car.get("km"):
        carnode["mileageFromOdometer"] = {"@type": "QuantitativeValue", "value": car["km"], "unitCode": "KMT"}
    art = {"@type": "BlogPosting", "@id": u + "#article", "headline": p["title"], "name": p["seo_title"],
           "description": p["description"], "abstract": p["summary"], "datePublished": p["date_iso"],
           "dateModified": str(p.get("updated") or p["date_iso"]), "inLanguage": "ko-KR",
           "image": image, "author": {"@id": site["org_id"]},
           "publisher": {"@id": site["org_id"]}, "mainEntityOfPage": {"@type": "WebPage", "@id": u},
           "isPartOf": {"@id": site["site"] + "#website"}, "about": carnode,
           "articleSection": p["category_name"], "keywords": ", ".join(p["tags"])}
    if p.get("source"):  # 블로그 원문(네이버) — 사이트 글은 새로 쓴 것
        art["isBasedOn"] = str(p["source"])
    if p.get("mentions"):  # 글에서 소개하는 다른 업체: 그 업체 홈의 @id 로만 참조
        art["mentions"] = [{"@id": str(m)} for m in p["mentions"]]
    cat_u = site["site"] + p["category_url"]
    g = [art, crumbs(site, [("홈", site["site"]), (site["cases_label"], site["site"] + "cases/"),
                            (p["category_name"], cat_u), (p["title"], u)])]
    if p["faq"]:
        g.append({"@type": "FAQPage", "@id": u + "#faq", "mainEntity": [
            {"@type": "Question", "name": f["q"], "acceptedAnswer": {"@type": "Answer", "text": f["a"]}}
            for f in p["faq"]]})
    return ld_dump(g)


def list_jsonld(site, posts, url, name, desc, cat=None):
    items = [("홈", site["site"]), (site["cases_label"], site["site"] + "cases/")] + ([(cat["name"], url)] if cat else [])
    return ld_dump([
        {"@type": "CollectionPage", "@id": url, "url": url, "name": name, "description": desc,
         "inLanguage": "ko-KR", "isPartOf": {"@id": site["site"] + "#website"}, "about": {"@id": site["org_id"]},
         "mainEntity": {"@id": url + "#list"}, "breadcrumb": {"@id": url + "#breadcrumb"}},
        {"@type": "ItemList", "@id": url + "#list", "numberOfItems": len(posts), "itemListElement": [
            {"@type": "ListItem", "position": i, "url": p["abs_url"], "name": p["title"]}
            for i, p in enumerate(posts, 1)]},
        crumbs(site, items)])


def head_meta(site, title, desc, url, image, otype, noindex):
    e = lambda s: str(escape(s))
    lines = [f'<meta name="description" content="{e(desc)}">',
             f'<link rel="canonical" href="{e(url)}">',
             f'<meta name="robots" content="{"noindex,nofollow" if noindex else "index,follow"}">',
             f'<meta property="og:type" content="{otype}">', '<meta property="og:locale" content="ko_KR">',
             f'<meta property="og:site_name" content="{e(site["name"])}">',
             f'<meta property="og:title" content="{e(title)}">', f'<meta property="og:description" content="{e(desc)}">',
             f'<meta property="og:url" content="{e(url)}">',
             f'<link rel="alternate" type="application/rss+xml" title="{e(site["name"])} {e(site.get("cases_label", "수리사례"))}" href="{e(site["site"])}cases/feed.xml">']
    if image:
        lines.append(f'<meta property="og:image" content="{e(image)}">')
    return Markup("\n".join(lines))


def finalize(html, title, meta, jsonld):
    """템플릿이 빠뜨린 head 요소를 보충하고 lang="ko" 를 보장한다."""
    head = ""
    if "<title>" not in html:
        head += f"<title>{escape(title)}</title>\n"
    if 'rel="canonical"' not in html:
        head += meta + "\n"
    if "application/ld+json" not in html:
        head += f'<script type="application/ld+json">{jsonld}</script>\n'
    if head:
        html = html.replace("</head>", head + "</head>", 1) if "</head>" in html else head + html
    html = re.sub(r"<html(?![^>]*\blang=)", '<html lang="ko"', html, count=1)
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
        try:
            json.loads(m.group(1))
        except ValueError as e:
            err(f"JSON-LD 파싱 실패: {e}")
    return html


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


# ---------- 목록 제목·브랜드 ----------
def join_brands(bs):
    return "·".join(bs)


def fill_brands(site, cats, posts):
    """site.yaml 문구의 {brands} 를 실제 글이 있는 브랜드로 바꾼다(글 많은 순). 예: 페라리 글이 0편이면 '마세라티'만.
    카테고리 문구의 {brands} 는 그 카테고리 글의 브랜드(없으면 사이트 전체)."""
    def brands(ps):
        cnt = {}
        for p in ps:
            b = str((p.get("car") or {}).get("brand", "")).strip()
            if b:
                cnt[b] = cnt.get(b, 0) + 1
        return [b for b, _ in sorted(cnt.items(), key=lambda x: -x[1])]
    pub = [p for p in posts if not p.get("draft")] or posts
    allb = join_brands(brands(pub)) or site.get("brands_default", "")
    site["brands"] = brands(pub)
    site["brands_text"] = allb
    for k in ("cases_intro", "cases_meta_desc", "cases_title", "cases_h1", "cases_lead"):
        if site.get(k):
            site[k] = str(site[k]).replace("{brands}", allb)
    for c in cats.values():
        cb = join_brands(brands([p for p in pub if p["category"] == c["key"]])) or allb
        for k in ("intro", "meta_desc", "title"):
            if c.get(k):
                c[k] = str(c[k]).replace("{brands}", cb)


def list_title(site, c):
    """목록·카테고리 <title>. site.yaml cases_title / 카테고리 title 이 있으면 그것, 없으면
    '{지역} {카테고리} 사례 | 이름'. '정비 정비사례'처럼 겹치는 말은 한 번만."""
    lab, name = site["cases_label"], site["name"]
    region = (site.get("regions") or [""])[0]
    if c is None:
        t = site.get("cases_title") or f"{region} {lab} | {name}"
    else:
        cn = c["name"]
        t = c.get("title") or f"{region} {cn} 사례 | {name}"
    t = re.sub(r"(정비|수리) \1사례", r"\1사례", t)          # '마세라티 정비 정비사례' → '마세라티 정비사례'
    t = " ".join(t.split())
    if len(t) > TITLE_MAX:
        warn(f"목록 제목 {len(t)}자 ({TITLE_MAX}자 초과): {t}")
    return t


# ---------- 부가 파일 ----------
def sitemap(site, posts, cat_pages):
    newest = posts[0]["date_iso"] if posts else dt.date.today().isoformat()
    rows = [(site["site"] + "cases/", newest, [])]
    for c, ps in cat_pages:
        pub = [p for p in ps if p in posts]
        if pub:
            rows.append((site["site"] + f"cases/{c['slug']}/", pub[0]["date_iso"], []))
    rows += [(p["abs_url"], str(p.get("updated") or p["date_iso"]), p["photos_all"]) for p in posts]
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
           'xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">']
    for loc, lm, photos in rows:
        out.append(f"  <url><loc>{xesc(loc)}</loc><lastmod>{lm}</lastmod>")
        for ph in photos:
            out.append(f"    <image:image><image:loc>{xesc(absu(site, ph['src']))}</image:loc></image:image>")
        out.append("  </url>")
    return "\n".join(out + ["</urlset>", ""])


def llms(site, posts):
    lab = site["cases_label"]
    out = [f"## {site['name']} {lab}", "", f"- [{lab} 목록]({site['site']}cases/): {' '.join(site['cases_intro'].split())}"]
    out += [f"- [{p['title']}]({p['abs_url']}): {' '.join(str(p['summary']).split())}" for p in posts]
    return "\n".join(out) + "\n"


def feed(site, posts):
    kst = dt.timezone(dt.timedelta(hours=9))
    rfc = lambda d: format_datetime(dt.datetime(d.year, d.month, d.day, 9, 0, tzinfo=kst))
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom"><channel>',
           f"<title>{xesc(site['name'])} {xesc(site['cases_label'])}</title>", f"<link>{site['site']}cases/</link>",
           f"<description>{xesc(site['cases_intro'])}</description>", "<language>ko</language>",
           f'<atom:link href="{site["site"]}cases/feed.xml" rel="self" type="application/rss+xml"/>']
    if posts:
        out.append(f"<lastBuildDate>{rfc(posts[0]['date'])}</lastBuildDate>")
    for p in posts[:20]:
        out.append(f"<item><title>{xesc(p['title'])}</title><link>{p['abs_url']}</link>"
                   f"<guid isPermaLink=\"true\">{p['abs_url']}</guid><pubDate>{rfc(p['date'])}</pubDate>"
                   f"<category>{xesc(p['category_name'])}</category>"
                   f"<description>{xesc(str(p['summary']).strip())}</description></item>")
    return "\n".join(out + ["</channel></rss>", ""])


# ---------- 메인 ----------
def main():
    ap = argparse.ArgumentParser(description="수리사례 정적 생성기")
    ap.add_argument("site_dir"); ap.add_argument("out_dir")
    ap.add_argument("--preview", action="store_true", help="draft 포함, noindex")
    ap.add_argument("--assets", help="사진 크기를 읽을 로컬 사이트 루트")
    ap.add_argument("--copy-assets", action="store_true", help="쓰인 사진을 out_dir 에 복사")
    a = ap.parse_args()
    site_dir, out = Path(a.site_dir).resolve(), Path(a.out_dir).resolve()
    tdir = site_dir / "templates"

    site = load_site(site_dir)
    cats = {c["key"]: c for c in site.get("categories") or []}
    all_posts = load_posts(site_dir, cats)
    if errors:
        return report(1)
    posts = sorted([p for p in all_posts if a.preview or not p.get("draft")],
                   key=lambda p: (p["date"], p["slug"]), reverse=True)
    imgs = Images(site_dir, Path(a.assets).resolve() if a.assets else None)
    for p in posts:
        enrich(p, site, cats, imgs)
    fill_brands(site, cats, posts)
    assign_related(posts)

    env = Environment(loader=FileSystemLoader(str(tdir)), autoescape=select_autoescape(["html", "xml"]),
                      trim_blocks=True, lstrip_blocks=True)
    env.filters["para"] = para
    env.filters["autolink"] = autolink
    for t in ("base.html", "case.html", "list.html", "card.html"):
        if not (tdir / t).is_file():
            err(f"templates/{t} 없음")
    if errors:
        return report(1)
    cases = out / "cases"
    if cases.exists():
        shutil.rmtree(cases)
    used = []  # 칩: 이번 빌드에 글이 있는 카테고리만, count 포함
    for c in cats.values():
        n = sum(p["category"] == c["key"] for p in posts)
        if n:
            used.append(dict(c, count=n))
    css = (tdir / "case.css").read_text(encoding="utf-8") if (tdir / "case.css").is_file() else ""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)                       # 주석 빼고
    css = Markup("\n".join(l.strip() for l in css.splitlines() if l.strip()))  # 페이지마다 <style> 로 인라인
    common = {"site": site, "categories": used, "preview": a.preview, "case_css": css}

    for p in posts:
        p["seo_title"] = fit_title(p["seo_title"], p["title"], site["name"])
        p["description"] = fit_desc(p["description"])
        meta = head_meta(site, p["seo_title"], p["description"], p["abs_url"],
                         og_image(site, p), "article", a.preview and p["draft"])
        ld = post_jsonld(p, site)
        html = env.get_template("case.html").render(**common, post=p, related=p["related_posts"],
                                                    jsonld=ld, meta=meta, root="../../")
        write(cases / p["slug"] / "index.html", finalize(html, p["seo_title"], meta, ld))

    cat_pages = []
    for c in [None] + used:
        ps = [p for p in posts if c is None or p["category"] == c["key"]]
        if c is not None and not ps:
            continue
        url = site["site"] + "cases/" + (f"{c['slug']}/" if c else "")
        title = list_title(site, c)
        desc = fit_desc((c.get("meta_desc") or c.get("intro") if c else None) or site.get("cases_meta_desc") or site["cases_intro"])
        first = next((q for q in ps if q["photos_all"]), None)
        meta = head_meta(site, title, desc, url, og_image(site, first) if first else og_image(site, None), "website",
                         bool(c) and all(p["draft"] for p in ps))  # draft 뿐인 카테고리는 noindex
        ld = list_jsonld(site, ps, url, title, desc, c)
        html = env.get_template("list.html").render(**common, posts=ps, current_category=c, jsonld=ld,
                                                    meta=meta, page_title=title, page_description=desc,
                                                    root="../../" if c else "../")
        write(cases / (f"{c['slug']}/index.html" if c else "index.html"), finalize(html, title, meta, ld))
        if c:
            cat_pages.append((c, ps))

    if (tdir / "case.css").is_file():
        shutil.copy2(tdir / "case.css", cases / "case.css")
    else:
        warn("templates/case.css 없음")
    if (tdir / "home-section.html").is_file():
        write(cases / "home-section.html",
              env.get_template("home-section.html").render(**common, posts=posts[:6], root=""))
    else:
        warn("templates/home-section.html 없음")
    public = [p for p in posts if not p["draft"]]  # 색인용 파일에는 draft 를 절대 넣지 않음
    write(cases / "sitemap-cases.xml", sitemap(site, public, cat_pages))
    write(cases / "llms-cases.txt", llms(site, public))
    write(cases / "feed.xml", feed(site, public))

    missing = [s for s, f in imgs.used.items() if not f]
    if missing:
        warn(f"로컬에 없는 사진 {len(missing)}개 → 크기 {DEFAULT_WH[0]}x{DEFAULT_WH[1]} 기본값 사용 (예: {missing[0]})")
    if a.copy_assets:
        for src, f in imgs.used.items():
            dst = out / src.lstrip("/")
            if f and f.resolve() != dst.resolve():
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, dst)
    # 절대 규칙(2026-10-22 사장님): 올리는 글에 noindex 가 있으면 안 된다. 업로드본에 하나라도 있으면 실패.
    if not a.preview:
        bad = [str(f.relative_to(out)) for f in cases.rglob("*.html") if "noindex" in f.read_text().lower()]
        if bad:
            err("업로드본에 noindex 페이지가 있음(절대 규칙 위반, 고칠 때까지 올리지 말 것): " + ", ".join(bad))
    print(f"[{site.get('key')}] {'미리보기' if a.preview else '업로드'}: 글 {len(posts)}개 "
          f"(draft {sum(p['draft'] for p in posts)}), 카테고리 {len(cat_pages)}개 → {cases}")
    return report(1 if errors else 0)


def report(code):
    for w in warnings:
        print("경고:", w)
    for e in errors:
        print("오류:", e, file=sys.stderr)
    if errors:
        print(f"실패: 오류 {len(errors)}개", file=sys.stderr)
    return code


if __name__ == "__main__":
    sys.exit(main())
