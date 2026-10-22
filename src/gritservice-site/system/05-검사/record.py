"""실측 기록 스크립트. 02-실측 CSV에 줄을 추가만 한다(고치거나 지우지 않는다). 해석을 쓰지 않는다.

사용:
  record.py exposure 2026-10-12 chatgpt Q01 Y|N|ERROR [인용URL] [기록자]
  record.py calls    2026-10-12 3 [메모] [기록자]
  record.py index    2026-10-12 google 1 [메모] [기록자]
잘못된 값은 거부하고 종료코드 2로 끝난다. 확인하지 못한 것은 ERROR로 적는다(빈칸이나 N으로 적지 않는다).
"""
import csv
import datetime
import sys
from common import SYS, engines, queries

R = SYS / "02-실측"


def fail(msg):
    print("거부:", msg)
    sys.exit(2)


def date(s):
    try:
        datetime.date.fromisoformat(s)
    except ValueError:
        fail(f"날짜 형식 YYYY-MM-DD 가 아님: {s}")
    return s


def add(name, row):
    with open(R / name, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(row)
    print("기록:", name, row)


def main(a):
    if len(a) < 2:
        fail("사용법은 파일 머리말 참고")
    kind, rest = a[0], a[1:]
    who = "사람"
    if kind == "exposure":
        if len(rest) < 4:
            fail("exposure 날짜 엔진 질의ID 노출 [URL] [기록자]")
        d, eng, q, v = rest[:4]
        url = rest[4] if len(rest) > 4 else ""
        who = rest[5] if len(rest) > 5 else who
        if eng not in engines():
            fail(f"엔진은 {engines()} 중 하나")
        if q not in queries():
            fail(f"질의ID는 {sorted(queries())} 중 하나")
        if v not in ("Y", "N", "ERROR"):
            fail("노출은 Y, N, ERROR 중 하나 (못 확인했으면 ERROR)")
        if v == "Y" and not url:
            fail("노출 Y는 인용URL(또는 화면에서 본 출처)을 적어야 한다")
        add("exposure.csv", [date(d), eng, q, v, url, who])
    elif kind == "calls":
        if len(rest) < 2:
            fail("calls 날짜 건수 [메모] [기록자]")
        if not rest[1].isdigit():
            fail("건수는 0 이상의 정수 (못 센 날은 기록하지 않는다. 0건과 못 센 것은 다르다)")
        memo = rest[2] if len(rest) > 2 else ""
        who = rest[3] if len(rest) > 3 else who
        add("calls.csv", [date(rest[0]), int(rest[1]), memo, who])
    elif kind == "index":
        if len(rest) < 3:
            fail("index 날짜 엔진(google|naver) 색인수 [메모] [기록자]")
        if rest[1] not in ("google", "naver"):
            fail("엔진은 google 또는 naver")
        if not rest[2].isdigit():
            fail("색인수는 0 이상의 정수")
        memo = rest[3] if len(rest) > 3 else ""
        who = rest[4] if len(rest) > 4 else who
        add("index_status.csv", [date(rest[0]), rest[1], int(rest[2]), memo, who])
    else:
        fail("종류는 exposure, calls, index")


if __name__ == "__main__":
    main(sys.argv[1:])
