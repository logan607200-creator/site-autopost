"""공통 도구: 정본 읽기. 이 파일은 읽기만 한다(정본을 쓰지 않는다)."""
import re
from pathlib import Path

SYS = Path(__file__).resolve().parent.parent
SITE_ROOT = SYS.parent          # gritservice-site/
CANON = SYS / "01-정본"


def kv(path):
    """`- 키: 값` 줄을 [(키, 값), ...] 로 읽는다."""
    out = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        m = re.match(r"^- ([^:]+): (.+)$", line.strip())
        if m:
            out.append((m.group(1).strip(), m.group(2).strip()))
    return out


def brand():
    return dict(kv(CANON / "brand.md"))


def services():
    return [v for k, v in kv(CANON / "services.md") if k == "서비스"]


def banned_words():
    return [v for k, v in kv(CANON / "금지.md") if k == "금지어"]


def queries():
    out = {}
    for line in (CANON / "질의목록.md").read_text(encoding="utf-8").splitlines():
        m = re.match(r"^- (Q\d\d): (.+)$", line.strip())
        if m:
            out[m.group(1)] = m.group(2).strip()
    return out


def engines():
    return [v for k, v in kv(CANON / "질의목록.md") if k == "엔진"]
