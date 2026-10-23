"""블로그 사진을 사례 글에 넣는다.
사용: python3 add_photos.py <사진폴더 incoming/blog-photos> [--max 8]   |   python3 add_photos.py --fix-alt
- 사진폴더/{grit|logan}/{slug}/01.jpg ... (노트북에서 블로그 원본을 받아 둔 것)
- 400px 미만(아이콘·스티커)은 뺀다. 글마다 최대 --max 장, 처음·끝을 포함해 고르게 고른다.
- webp(q80, 긴 변 1200 이하)로 바꿔 저장: 그릿 → src/gritservice-site/upload/assets/cases/, 로건 → src/cases-system/logan/assets/cases/
- 첫 장은 cover, 나머지는 본문 섹션에 순서대로 나눠 넣는다. photos_pending: true → false
- 이미 cover 가 있는 글은 건너뛴다(사장님이 직접 고른 사진 보호).
- alt 는 '차종 + 작업(제목의 작업 부분) + 섹션' (photo_alt). 예전 '섹션 사진 N' alt 는
  python3 add_photos.py --fix-alt 로 이미 들어간 글까지 고친다(여러 번 돌려도 같은 결과).
번호판은 블로그 원본에서 사장님이 이미 가린 사진을 쓴다. 새 사진은 올리기 전에 번호판을 확인할 것.
"""
import re, sys, argparse
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
CS = HERE.parent
DEST = {"grit": CS.parent / "gritservice-site" / "upload" / "assets" / "cases",
        "logan": CS / "logan" / "assets" / "cases"}


def pick(files, n):
    if len(files) <= n:
        return files
    idx = sorted({round(i * (len(files) - 1) / (n - 1)) for i in range(n)})
    return [files[i] for i in idx]


def q(s):
    return '"' + s.replace('"', "'") + '"'


def _clean(s):
    return re.sub(r"\s+", " ", str(s or "")).strip()


def car_name(car):
    if not isinstance(car, dict):
        return ""
    return _clean(f"{car.get('brand', '')} {car.get('model', '')}")


def work_of(title, car, short=False):
    """글 제목에서 차종 단어(브랜드·모델·섀시코드·'중고')를 앞에서 뺀 나머지.
    short=True 이고 제목이 'A — B' 꼴이면 A(부품·원인 부분)만 쓴다(본문 사진 alt 가 너무 길어지지 않게)."""
    t = _clean(title)
    if short and " — " in t:
        t = t.split(" — ", 1)[0]
    cn = car_name(car).lower()
    words = t.split(" ")
    while len(words) > 1:
        w = re.sub(r"\(.*?\)$", "", words[0]).lower()  # '르반떼(M161)' → '르반떼'
        if w and (w in cn or w == "중고"):
            words.pop(0)
        else:
            break
    return " ".join(words)


def photo_alt(car, title, h2=None, n=1):
    """cover: '차종 작업', 본문: '차종 작업 — 섹션' (같은 섹션 2장째부터 '(2)'). 차종 중복 단어·앞뒤 공백 제거."""
    if not h2:
        return _clean(f"{car_name(car)} {work_of(title, car)}")
    base = _clean(f"{car_name(car)} {work_of(title, car, short=True)}")
    sec = _clean(h2).replace(" — ", ": ")
    return f"{base} — {sec}" + (f" ({n})" if n > 1 else "")


OLD_ALT = re.compile(r"(사진 \d+|^\s.*)$")


def fix_alts(path, force=False):
    """이미 들어간 글의 자동 alt(예전 '섹션 사진 N', 앞 공백, 제목 그대로)를 photo_alt 로 바꾼다. 손으로 쓴 alt 는 둔다."""
    text = path.read_text()
    d = yaml.safe_load(text) or {}
    car, title = d.get("car") or {}, d.get("title", "")
    want = {}
    cov = d.get("cover") or {}
    if cov.get("src"):
        old = str(cov.get("alt", ""))
        if force or OLD_ALT.search(old) or " — " in old or _clean(old) in (_clean(title), _clean(f"{car_name(car)} {title}")):
            want[cov["src"]] = photo_alt(car, title)
    for s in d.get("sections") or []:
        for j, ph in enumerate(s.get("photos") or [], 1):
            if isinstance(ph, dict) and ph.get("src") and (force or OLD_ALT.search(str(ph.get("alt", "")))):
                want[ph["src"]] = photo_alt(car, title, s.get("h2"), j)
    out, n = [], 0
    for line in text.split("\n"):
        m = re.search(r"src: ([^,}\s]+), alt: (\"[^\"]*\"|'[^']*'|[^}]*)", line)
        if m and m.group(1) in want:
            new = q(want[m.group(1)])
            if m.group(2) != new:
                line = line[:m.start(2)] + new + line[m.end(2):]
                n += 1
        out.append(line)
    if n:
        path.write_text("\n".join(out))
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("photos", nargs="?")
    ap.add_argument("--fix-alt", action="store_true", help="이미 들어간 글의 자동 alt 만 고친다")
    ap.add_argument("--force", action="store_true", help="--fix-alt 와 함께: 손으로 쓴 alt 까지 모두 다시 만든다(제목을 바꾼 뒤)")
    ap.add_argument("--max", type=int, default=8)
    a = ap.parse_args()
    if not a.photos and not a.fix_alt:
        ap.error("사진폴더 또는 --fix-alt 가 필요합니다")
    if a.fix_alt:
        for site in ("grit", "logan"):
            for post in sorted((CS / site / "posts").glob("*.yaml")):
                n = fix_alts(post, a.force)
                if n:
                    print(site, post.stem, f"alt {n}개 고침")
        return
    from PIL import Image, ImageOps
    for site in ("grit", "logan"):
        DEST[site].mkdir(parents=True, exist_ok=True)
        for post in sorted((CS / site / "posts").glob("*.yaml")):
            slug = post.stem
            src_dir = Path(a.photos) / site / slug
            text = post.read_text()
            if not src_dir.is_dir() or re.search(r"^cover:", text, re.M):
                continue
            files = []
            for f in sorted(src_dir.iterdir()):
                if f.suffix.lower() not in (".jpg", ".jpeg", ".png", ".webp"):
                    continue
                with Image.open(f) as im:
                    if min(im.size) >= 400:
                        files.append(f)
            files = pick(files, a.max)
            if not files:
                continue
            d = yaml.safe_load(text) or {}
            car, title = d.get("car") or {}, d.get("title", "")
            cover_alt = photo_alt(car, title)
            srcs = []
            for i, f in enumerate(files, 1):
                name = f"{slug}-{i:02d}.webp"
                im = ImageOps.exif_transpose(Image.open(f)).convert("RGB")
                im.thumbnail((1200, 1200))
                im.save(DEST[site] / name, "WEBP", quality=80, method=6)
                srcs.append(f"assets/cases/{name}")
            lines = text.split("\n")
            H2 = re.compile(r"^( *)- h2:")
            h2s = [l.split("h2:", 1)[1].strip().strip('"') for l in lines if H2.match(l)]
            ind = " " * (len(H2.match(next(l for l in lines if H2.match(l))).group(1)) + 2) if h2s else "  "
            rest = srcs[1:]
            per = [[] for _ in h2s]
            for k, s in enumerate(rest):
                per[k * len(h2s) // max(len(rest), 1)].append(s)
            out, sec, in_sec = [], -1, False

            def flush():
                if in_sec and sec >= 0 and per[sec]:
                    out.append(ind + "photos:")
                    for j, s in enumerate(per[sec], 1):
                        out.append(f"{ind}  - {{src: {s}, alt: {q(photo_alt(car, title, h2s[sec], j))}}}")
            for l in lines:
                if l.startswith("sections:"):
                    out.append(f"cover: {{src: {srcs[0]}, alt: {q(cover_alt)}}}")
                    out.append(l); in_sec = True; continue
                if in_sec and H2.match(l):
                    while out and out[-1] == "":
                        out.pop()
                    flush(); sec += 1
                elif in_sec and re.match(r"^[A-Za-z_]", l):
                    while out and out[-1] == "":
                        out.pop()
                    flush(); in_sec = False
                out.append(l)
            if in_sec:
                while out and out[-1] == "":
                    out.pop()
                flush(); out.append("")
            new = "\n".join(out).replace("photos_pending: true", "photos_pending: false")
            post.write_text(new)
            print(site, slug, len(srcs))
            fix_alts(post)


if __name__ == "__main__":
    main()
