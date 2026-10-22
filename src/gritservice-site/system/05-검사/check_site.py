"""사이트 검사 C1~C8. 결과는 PASS / FAIL / ERROR / PENDING. 미검사는 통과가 아니다.
사용: check_site.py [--dir 사이트폴더] [--only C1,C2] [--zip zip경로]
종료코드: FAIL 또는 ERROR 가 하나라도 있으면 1."""
import argparse
import hashlib
import html as htmllib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from xml.dom import minidom

from common import CANON, SITE_ROOT, banned_words, brand, kv, services

TEXT_FILES = ["index.php", "llms.txt", "robots.txt", "sitemap.xml"]
# GEO 질문 200개(2026-10-19 추가). 있으면 C1·C3·C4·C6·C7 이 함께 본다. upload 에서는 C6 재빌드 비교로 빠짐이 잡힌다.
EXTRA_FILES = ["faq/index.php", "llms-full.txt"]


class Ctx:
    def __init__(self, d, zip_path):
        self.dir = Path(d)
        self.zip = Path(zip_path)
        self.t = {}
        for n in TEXT_FILES + EXTRA_FILES:
            p = self.dir / n
            self.t[n] = p.read_text(encoding="utf-8") if p.exists() else None
        self.b = brand()

    def need(self, *names):
        miss = [n for n in names if self.t.get(n) is None]
        if miss:
            raise FileNotFoundError(f"{self.dir} 에 {', '.join(miss)} 없음")
        return [self.t[n] for n in names]


def extras(c):
    return tuple((n, c.t[n]) for n in EXTRA_FILES if c.t.get(n) is not None)


def strip_comments(s):
    return re.sub(r"<!--.*?-->", "", s, flags=re.S)


# ---------- C1 이름·주소·전화·사업자번호 일치
def c1(c):
    idx, llms = c.need("index.php", "llms.txt")
    b = c.b
    bad = []
    base, detail = b["주소기본"], b["주소상세"]
    for name, s in (("index.php", idx), ("llms.txt", llms)) + extras(c):
        hits = [m.end() for m in re.finditer(re.escape(base), s)]
        if not hits:
            bad.append(f"{name}: 주소 '{base}' 없음")
        for e in hits:
            if not s[e:].startswith(", " + detail):
                bad.append(f"{name}: '{base}' 뒤에 ', {detail}' 없음 -> ...{s[max(0,e-12):e+14]!r}")
        for m in re.finditer(r"1577-?\d{4}", s):
            if m.group(0) not in (b["전화"], b["전화"].replace("-", "")):
                bad.append(f"{name}: 다른 전화번호 {m.group(0)}")
        for m in re.finditer(r"(?<!\d)1[0-9]{3}-\d{4}(?!\d)", s):
            if m.group(0) != b["전화"]:
                bad.append(f"{name}: 정본에 없는 대표번호 형식 {m.group(0)}")
        for m in re.finditer(r"(?<!\d)\d{3}-\d{2}-\d{5}(?!\d)", s):
            if m.group(0) != b["사업자번호"]:
                bad.append(f"{name}: 다른 사업자번호 {m.group(0)}")
        if re.search(r"http://gritservice", s):
            bad.append(f"{name}: http:// 로 시작하는 대표주소")
    foot = ["(주)그릿서비스", "대표 " + b["대표"], b["사업자번호"], b["전화"]]
    for f in foot:
        if f not in idx:
            bad.append(f"index.php 에 '{f}' 없음")
    return ("FAIL", "; ".join(bad)) if bad else ("PASS", "주소(1동 1층)·전화·사업자번호·법인·대표가 정본과 같음")


# ---------- C2 서비스 이름이 정본과 같다
def c2(c):
    idx, llms = c.need("index.php", "llms.txt")
    canon = services()
    cards = [htmllib.unescape(x).strip() for x in re.findall(r'<article class="service">.*?<h3>(.*?)</h3>', idx, re.S)]
    sec = llms.split("## 서비스", 1)[-1].split("\n## ", 1)[0]
    llm = [x.strip() for x in re.findall(r"^- \*\*(.+?)\*\*", sec, re.M)]
    ld = []
    for m in re.findall(r'<script type="application/ld\+json">(.*?)</script>', idx, re.S):
        try:
            j = json.loads(m)
        except Exception:
            continue
        for g in j.get("@graph", [j]):
            for o in g.get("hasOfferCatalog", {}).get("itemListElement", []):
                ld.append(o["itemOffered"]["name"])
    bad = []
    for label, got in (("사이트 서비스 카드", cards), ("llms.txt 서비스", llm), ("JSON-LD 서비스", ld)):
        if sorted(got) != sorted(canon):
            bad.append(f"{label}: 정본에 없는 것 {sorted(set(got)-set(canon))}, 빠진 것 {sorted(set(canon)-set(got))}")
    return ("FAIL", "; ".join(bad)) if bad else ("PASS", f"서비스 {len(canon)}개가 사이트·llms.txt·JSON-LD에서 정본과 같음")


# ---------- C3 금지어
def c3(c):
    idx, llms = c.need("index.php", "llms.txt")
    words = banned_words()
    bad = []
    for name, s in (("index.php", idx), ("llms.txt", llms)) + extras(c):
        for w in words:
            n = s.count(w)
            if n:
                bad.append(f"{name}: '{w}' {n}회")
    return ("FAIL", "; ".join(bad)) if bad else ("PASS", f"금지어 {len(words)}개 없음")


# ---------- C4 구조화 정보·사이트맵·대표주소
def c4(c):
    idx, robots, smap = c.need("index.php", "robots.txt", "sitemap.xml")
    site = c.b["대표주소"]
    bad = []
    lds = re.findall(r'<script type="application/ld\+json">(.*?)</script>', idx, re.S)
    if not lds:
        bad.append("JSON-LD 없음")
    types = set()
    for m in lds:
        try:
            j = json.loads(m)
        except Exception as e:
            bad.append(f"JSON-LD 파싱 실패: {e}")
            continue
        for g in j.get("@graph", [j]):
            t = g.get("@type")
            types.update(t if isinstance(t, list) else [t])
    faq = c.t.get("faq/index.php")
    if faq is not None:
        fl = re.findall(r'<script type="application/ld\+json">(.*?)</script>', faq, re.S)
        try:
            fq = [q for m in fl for g in json.loads(m).get("@graph", []) if g.get("@type") == "FAQPage" for q in g["mainEntity"]]
            nvis = faq.count("<details>")
            if not fq or len(fq) != nvis:
                bad.append(f"faq/index.php: JSON-LD 질문 {len(fq)}개와 화면 질문 {nvis}개가 다름")
        except Exception as e:
            bad.append(f"faq/index.php JSON-LD 파싱 실패: {e}")
        if f'<link rel="canonical" href="{site}faq/"' not in faq:
            bad.append("faq/index.php canonical 이 대표주소/faq/ 가 아님")
        if site + "faq/" not in smap:
            bad.append("sitemap 에 faq/ 주소 없음")
    for need in ("AutoRepair", "FAQPage", "WebSite"):
        if lds and not bad and need not in types:
            bad.append(f"JSON-LD에 {need} 없음")
    try:
        dom = minidom.parseString(smap.encode("utf-8"))
    except Exception as e:
        bad.append(f"sitemap.xml 파싱 실패: {e}")
        dom = None
    nimg = 0
    if dom:
        locs = [n.firstChild.data.strip() for n in dom.getElementsByTagName("loc")]
        if site not in locs:
            bad.append(f"sitemap 에 대표주소 {site} 없음")
        for n in dom.getElementsByTagName("image:loc"):
            u = n.firstChild.data.strip()
            nimg += 1
            if not u.startswith(site + "assets/"):
                bad.append(f"이미지 주소가 대표주소 아래가 아님: {u}")
                continue
            f = c.dir / "assets" / u[len(site + "assets/"):]
            if not f.exists():
                bad.append(f"sitemap 이미지 파일 없음: {f.name}")
    can = re.findall(r'<link rel="canonical" href="([^"]+)"', idx)
    ogu = re.findall(r'<meta property="og:url" content="([^"]+)"', idx)
    if can != [site] or ogu != [site]:
        bad.append(f"canonical {can} / og:url {ogu} 가 대표주소 {site} 와 다름")
    if site + "sitemap.xml" not in robots:
        bad.append("robots.txt 의 Sitemap 줄이 대표주소와 다름")
    for bot in ("Yeti", "Googlebot", "GPTBot", "ClaudeBot"):
        if f"User-agent: {bot}" not in robots:
            bad.append(f"robots.txt 에 {bot} 허용 줄 없음")
    return ("FAIL", "; ".join(bad)) if bad else ("PASS", f"JSON-LD {sorted(types)} 파싱 OK, sitemap 이미지 {nimg}장 존재, canonical·og:url·robots 일치")


# ---------- C5 소유확인 코드
def c5(c):
    (idx,) = c.need("index.php")
    live = strip_comments(idx)
    cfg = dict(kv(CANON / "verification.md"))
    bad, pend = [], []
    for eng in ("naver", "google"):
        code = cfg.get(eng, "대기")
        if code == "대기":
            pend.append(eng)
            continue
        if not re.search(rf'<meta name="{eng}-site-verification" content="{re.escape(code)}"', live):
            bad.append(f"{eng} 코드 메타가 주석 밖에 없음")
    if bad:
        return "FAIL", "; ".join(bad)
    if pend:
        return "PENDING", f"{', '.join(pend)} 코드 아직 못 받음(통과 아님). 받으면 verification.md에 채울 것"
    return "PASS", "소유확인 코드가 모두 들어 있음"


# ---------- C6 upload = zip = 재빌드
def sha(b):
    return hashlib.sha256(b).hexdigest()


def c6(c):
    if not c.zip.exists():
        raise FileNotFoundError(f"zip 없음: {c.zip}")
    bad = []
    with zipfile.ZipFile(c.zip) as z:
        names = {n for n in z.namelist() if not n.endswith("/")}
        files = {str(p.relative_to(c.dir)) for p in c.dir.rglob("*") if p.is_file()}
        for n in sorted(names - files):
            bad.append(f"zip에만 있음: {n}")
        for n in sorted(files - names):
            bad.append(f"upload에만 있음(zip에 빠짐): {n}")
        for n in sorted(names & files):
            if sha(z.read(n)) != sha((c.dir / n).read_bytes()):
                bad.append(f"zip과 upload 내용이 다름: {n}")
    mk = SITE_ROOT / "make_grit.py"
    tmp = Path(tempfile.mkdtemp())
    try:
        r = subprocess.run([sys.executable, str(mk), str(tmp)], capture_output=True, text=True, timeout=120)
        if r.returncode != 0:
            raise RuntimeError("make_grit.py 실행 실패: " + r.stderr[-200:])
        for n in TEXT_FILES + [x for x in EXTRA_FILES if (tmp / x).exists()]:
            if not (c.dir / n).exists():
                bad.append(f"make_grit.py 가 만드는 {n} 이 없음")
                continue
            if not (tmp / n).exists() or sha((tmp / n).read_bytes()) != sha((c.dir / n).read_bytes()):
                bad.append(f"make_grit.py 재빌드 결과와 다름: {n}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return ("FAIL", "; ".join(bad)) if bad else ("PASS", f"zip {len(names)}개 파일이 upload와 같고 make_grit.py 재빌드와 텍스트 파일이 같음")


# ---------- C7 가로 스크롤 + 제목 줄바꿈 방지
def c7(c):
    (idx,) = c.need("index.php")
    bad = []
    if not re.search(r"h1[^{}]*\{[^}]*word-break:\s*keep-all", idx):
        bad.append("제목(h1)에 word-break:keep-all CSS 없음")
    pw = subprocess.run(["npm", "root", "-g"], capture_output=True, text=True).stdout.strip() + "/playwright/index.mjs"
    if not Path(pw).exists():
        raise FileNotFoundError("playwright 없음: " + pw)
    pages = [("", idx)] + [("faq-", c.t["faq/index.php"])] * (c.t.get("faq/index.php") is not None)
    m = {}
    for pre, src in pages:
        m.update({pre + k: v for k, v in _layout(c, pw, src).items()})
    for k, v in m.items():
        if v["scrollWidth"] > v["innerWidth"] + 1:
            bad.append(f"{k}: 가로 스크롤 생김 scrollWidth {v['scrollWidth']} > {v['innerWidth']}")
    return ("FAIL", "; ".join(bad)) if bad else ("PASS", f"폭 390·1280 가로 스크롤 없음 {m}, h1 keep-all 있음")


def _layout(c, pw, idx):
    tmp = Path(tempfile.mkdtemp())
    try:
        (tmp / "index.html").write_text(idx, encoding="utf-8")
        if (c.dir / "assets").exists():
            (tmp / "assets").symlink_to((c.dir / "assets").resolve())
        r = subprocess.run(["node", str(Path(__file__).parent / "layout.mjs"), pw, str(tmp / "index.html")],
                           capture_output=True, text=True, timeout=120)
        if r.returncode != 0:
            raise RuntimeError("layout.mjs 실패: " + (r.stderr or r.stdout)[-300:])
        m = json.loads(r.stdout.strip().splitlines()[-1])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return m


# ---------- C8 정본 해시
def c8(c):
    sums = CANON / "SHA256SUMS"
    if not sums.exists():
        raise FileNotFoundError("SHA256SUMS 없음 (seal.py 로 봉인 필요)")
    want = {}
    for line in sums.read_text(encoding="utf-8").splitlines():
        h, n = line.split("  ", 1)
        want[n] = h
    have = {p.name: sha(p.read_bytes()) for p in CANON.glob("*.md")}
    bad = []
    for n in sorted(set(want) | set(have)):
        if n not in have:
            bad.append(f"정본 파일 사라짐: {n}")
        elif n not in want:
            bad.append(f"봉인 안 된 정본 파일: {n}")
        elif have[n] != want[n]:
            bad.append(f"정본이 봉인 뒤에 바뀜: {n}")
    return ("FAIL", "; ".join(bad)) if bad else ("PASS", f"정본 {len(have)}개 해시 일치")


CHECKS = {"C1": c1, "C2": c2, "C3": c3, "C4": c4, "C5": c5, "C6": c6, "C7": c7, "C8": c8}
TITLES = {"C1": "상호·주소·전화 일치", "C2": "서비스 이름=정본", "C3": "금지어", "C4": "구조화·사이트맵·대표주소", "C5": "소유확인 코드",
          "C6": "upload=zip=재빌드", "C7": "레이아웃", "C8": "정본 해시"}


def run(d, only, zip_path):
    ctx = Ctx(d, zip_path)
    res = {}
    for k in only:
        try:
            res[k] = CHECKS[k](ctx)
        except Exception as e:
            res[k] = ("ERROR", f"{type(e).__name__}: {e}")
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=str(SITE_ROOT / "upload"))
    ap.add_argument("--only", default=",".join(CHECKS))
    ap.add_argument("--zip", default=str(SITE_ROOT / "gritservice-upload.zip"))
    a = ap.parse_args()
    res = run(a.dir, a.only.split(","), a.zip)
    for k, (st, msg) in res.items():
        print(f"{k} {TITLES[k]}: {st} - {msg}")
    cnt = {s: sum(1 for v in res.values() if v[0] == s) for s in ("PASS", "FAIL", "ERROR", "PENDING")}
    print("요약:", cnt)
    sys.exit(1 if cnt["FAIL"] or cnt["ERROR"] else 0)


if __name__ == "__main__":
    main()
