"""블로그 사진을 사례 글에 넣는다.
사용: python3 add_photos.py <사진폴더 incoming/blog-photos> [--max 8]
- 사진폴더/{grit|logan}/{slug}/01.jpg ... (노트북에서 블로그 원본을 받아 둔 것)
- 400px 미만(아이콘·스티커)은 뺀다. 글마다 최대 --max 장, 처음·끝을 포함해 고르게 고른다.
- webp(q80, 긴 변 1200 이하)로 바꿔 저장: 그릿 → src/gritservice-site/upload/assets/cases/, 로건 → src/cases-system/logan/assets/cases/
- 첫 장은 cover, 나머지는 본문 섹션에 순서대로 나눠 넣는다. photos_pending: true → false
- 이미 cover 가 있는 글은 건너뛴다(사장님이 직접 고른 사진 보호).
번호판은 블로그 원본에서 사장님이 이미 가린 사진을 쓴다. 새 사진은 올리기 전에 번호판을 확인할 것.
"""
import re, sys, argparse
from pathlib import Path
from PIL import Image, ImageOps

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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("photos")
    ap.add_argument("--max", type=int, default=8)
    a = ap.parse_args()
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
            car = re.search(r"^car: \{brand: ([^,}]+), model: ([^,}]+)", text, re.M)
            carname = f"{car.group(1).strip()} {car.group(2).strip()}" if car else ""
            title = re.search(r'^title: "?(.*?)"?$', text, re.M).group(1)
            cover_alt = title if car and car.group(2).strip() in title else f"{carname} {title}"
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
                        out.append(f"{ind}  - {{src: {s}, alt: {q(f'{carname} {h2s[sec]} 사진 {j}')}}}")
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


main()
