"""규칙·사례 위생 검사. 규칙 머리의 근거/충돌검토 누락, 유효기한 만료, 같은 항목 중복, 사례 형식, 승격 대기(같은 패턴 2회)를 본다.
결과는 PASS / FAIL / PENDING. FAIL 이 있으면 종료코드 1."""
import datetime
import re
import sys
from collections import Counter
from common import SYS


def head(path):
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^(근거|충돌검토|유효기한|항목|상태|패턴|날짜):\s*(.*)$", line)
        if m and m.group(1) not in out:
            out[m.group(1)] = m.group(2).strip()
    return out


def main():
    bad, pend = [], []
    rules = sorted((SYS / "04-규칙").glob("R-*.md"))
    topics = {}
    today = datetime.date.today()
    for p in rules:
        h = head(p)
        active = h.get("상태", "유효") != "폐기"
        if not h.get("근거"):
            bad.append(f"{p.name}: 근거 없음")
        if not h.get("충돌검토"):
            bad.append(f"{p.name}: 충돌검토 없음 (부딪히는 규칙이 없으면 '없음'이라고 적는다)")
        ex = h.get("유효기한", "없음")
        if active and ex != "없음":
            try:
                if datetime.date.fromisoformat(ex) < today:
                    bad.append(f"{p.name}: 유효기한 {ex} 지남")
            except ValueError:
                bad.append(f"{p.name}: 유효기한 형식 오류 {ex}")
        m = re.match(r"사례\s*(03-사례/\S+)", h.get("근거", ""))
        if m and not (SYS / m.group(1)).exists():
            bad.append(f"{p.name}: 근거 사례 파일이 없음 {m.group(1)}")
        if active:
            topics.setdefault(h.get("항목", p.stem), []).append(p.name)
    for t, names in topics.items():
        if len(names) > 1:
            bad.append(f"같은 항목 '{t}' 을 여러 규칙이 말함: {names} (진 쪽에 상태: 폐기를 표시할 것)")
    pats = Counter()
    for p in sorted((SYS / "03-사례").glob("C-*.md")):
        text = p.read_text(encoding="utf-8")
        h = head(p)
        for k in ("상황", "판단", "결과", "교훈"):
            if not re.search(rf"^- {k}: \S", text, re.M):
                bad.append(f"{p.name}: '{k}' 칸 없음")
        if not h.get("패턴"):
            bad.append(f"{p.name}: 패턴 이름 없음")
        else:
            pats[h["패턴"]] += 1
    covered = " ".join((SYS / "04-규칙" / n).read_text(encoding="utf-8") for n in [p.name for p in rules])
    for pat, n in pats.items():
        if n >= 2 and pat not in covered:
            pend.append(f"패턴 '{pat}' {n}회 -> 규칙으로 승격할 차례")
    print("규칙", len(rules), "개, 사례", sum(pats.values()), "개, 패턴", dict(pats))
    for b in bad:
        print("FAIL -", b)
    for p in pend:
        print("PENDING -", p)
    st = "FAIL" if bad else ("PENDING" if pend else "PASS")
    print("규칙·사례 위생:", st)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
