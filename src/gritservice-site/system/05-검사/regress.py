"""본보기 회귀 실행. 좋은 예는 통과, 나쁜 예는 expect.txt 의 검사에서 반드시 FAIL 이어야 한다.
C6·C8·규칙 위생은 임시 복사본을 일부러 망가뜨려 확인한다. 하나라도 기대와 다르면 종료코드 1."""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from common import SITE_ROOT, SYS
import check_site as cs

TEXT = cs.TEXT_FILES
G = SYS / "06-본보기" / "good"
BAD = SYS / "06-본보기" / "bad"
ASSETS = SITE_ROOT / "upload" / "assets"
ZIP = str(SITE_ROOT / "gritservice-upload.zip")
problems = []


def overlay(files):
    tmp = Path(tempfile.mkdtemp())
    for n in TEXT:
        shutil.copy(files.get(n, G / n), tmp / n)
    (tmp / "assets").symlink_to(ASSETS)
    return tmp


def expect(label, ok, detail=""):
    print(("OK   " if ok else "어긋남 "), label, detail)
    if not ok:
        problems.append(label)


# 1) 좋은 예
t = overlay({})
res = cs.run(t, ["C1", "C2", "C3", "C4", "C5", "C7"], ZIP)
shutil.rmtree(t)
expect("좋은 예가 C1~C5,C7을 통과(PENDING 허용, FAIL·ERROR 불가)", all(v[0] in ("PASS", "PENDING") for v in res.values()),
       str({k: v[0] for k, v in res.items()}))

# 2) 나쁜 예
for d in sorted(BAD.iterdir()):
    want = (d / "expect.txt").read_text(encoding="utf-8").strip().split(",")
    files = {p.name: p for p in d.iterdir() if p.name in TEXT}
    t = overlay(files)
    res = cs.run(t, want, ZIP)
    shutil.rmtree(t)
    expect(f"나쁜 예 {d.name} 가 {want} 에서 FAIL", all(res[k][0] == "FAIL" for k in want), str({k: res[k][0] for k in want}))

# 3) C6: 업로드 파일 하나가 zip과 달라지면 FAIL
tmp = Path(tempfile.mkdtemp())
shutil.copytree(SITE_ROOT / "upload", tmp / "u")
(tmp / "u" / "robots.txt").write_text("User-agent: *\nAllow: /\n", encoding="utf-8")
r = cs.run(tmp / "u", ["C6"], ZIP)
shutil.rmtree(tmp)
expect("나쁜 예 stale-zip(upload가 zip과 다름)이 C6에서 FAIL", r["C6"][0] == "FAIL", r["C6"][1][:80])

# 4) C8 / 규칙 위생: 시스템 폴더를 임시로 복사해 망가뜨린다
tmp = Path(tempfile.mkdtemp())
shutil.copytree(SYS, tmp / "system")
(shutil.copy(SITE_ROOT / "make_grit.py", tmp / "make_grit.py"))
canon = tmp / "system" / "01-정본" / "brand.md"
canon.chmod(0o644)
canon.write_text(canon.read_text(encoding="utf-8").replace("1577-0412", "1577-9999"), encoding="utf-8")
r = subprocess.run([sys.executable, str(tmp / "system/05-검사/check_site.py"), "--only", "C8", "--dir", str(SITE_ROOT / "upload")],
                   capture_output=True, text=True)
expect("나쁜 예 정본 변조가 C8에서 FAIL", r.returncode == 1 and "바뀜" in r.stdout, r.stdout.strip()[:90])
shutil.copy(SYS / "01-정본" / "brand.md", canon)

rules = tmp / "system" / "04-규칙"
(rules / "R-901-근거없음.md").write_text("# 근거 없는 규칙\n충돌검토: 없음\n항목: 시험1\n", encoding="utf-8")
(rules / "R-902-만료.md").write_text("# 만료된 규칙\n근거: 지시 2020-01-01\n충돌검토: 없음\n유효기한: 2020-01-01\n항목: 시험2\n", encoding="utf-8")
(rules / "R-903-중복.md").write_text("# 중복\n근거: 지시 2026-10-11\n충돌검토: 없음\n항목: 지시처리\n", encoding="utf-8")
r = subprocess.run([sys.executable, str(tmp / "system/05-검사/check_rules.py")], capture_output=True, text=True)
out = r.stdout
expect("나쁜 규칙 3종(근거 없음·만료·같은 항목 중복)이 모두 걸림",
       r.returncode == 1 and "근거 없음" in out and "지남" in out and "여러 규칙이 말함" in out, out.strip().splitlines()[-1] if out.strip() else "")
for p in ("a", "b"):
    (tmp / "system" / "03-사례" / f"C-9999000{p}-시험.md").write_text(
        "# 시험\n날짜: 2026-10-11\n패턴: test-pattern\n\n- 상황: x\n- 판단: x\n- 결과: x\n- 교훈: x\n", encoding="utf-8")
r = subprocess.run([sys.executable, str(tmp / "system/05-검사/check_rules.py")], capture_output=True, text=True)
expect("같은 패턴 2회가 '승격할 차례'로 보고됨", "'test-pattern' 2회" in r.stdout, "")
shutil.rmtree(tmp)

print("회귀 결과:", "모두 기대대로" if not problems else f"어긋남 {len(problems)}건 {problems}")
sys.exit(1 if problems else 0)
