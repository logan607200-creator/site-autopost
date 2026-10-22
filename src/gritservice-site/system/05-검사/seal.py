"""정본의 해시를 새로 봉인한다. **사람(사장님)이 정본을 고친 뒤에만** 돌린다. AI는 승인 없이 돌리지 않는다.
chmod 444 도 시도하지만 이 저장소에서는 효과가 없다(확인함). 지키는 장치는 해시 검사(C8)뿐이다."""
import hashlib
import os
from common import CANON

files = sorted(p for p in CANON.glob("*.md"))
sums = CANON / "SHA256SUMS"
if sums.exists():
    os.chmod(sums, 0o644)
sums.write_text("".join(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n" for p in files), encoding="utf-8")
for p in files + [sums]:
    os.chmod(p, 0o444)
print("봉인:", [p.name for p in files])
