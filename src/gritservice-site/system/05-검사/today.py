"""오늘 아침 9시에 기록할 항목을 알려 준다. 월요일은 질의 12개 전체, 그 외는 3개 순환."""
import datetime
import sys
from common import queries, engines

d = datetime.date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else datetime.date.today()
q = queries()
ids = sorted(q)
if d.weekday() == 0:
    today = ids
    kind = "월요일 전체 확인(12개 x 엔진 4개 = 48칸) + 색인 확인"
else:
    n = d.toordinal() * 3
    today = [ids[(n + k) % len(ids)] for k in range(3)]
    kind = "일간 순환 확인(3개 x 엔진 4개 = 12칸)"
print(f"{d} {kind}")
y = d - datetime.timedelta(days=1)
print("1) 어제 문의 전화 수: record.py calls", y, "<건수>")
for i in today:
    print(f"   {i} {q[i]}")
print("2) 위 질의를 엔진", ", ".join(engines()), "에 물어 그릿서비스가 나오는지 기록:")
print("   record.py exposure", d, "<엔진> <질의ID> Y|N|ERROR [인용URL]")
if d.weekday() == 0:
    print("3) 색인 수: record.py index", d, "google|naver <건수>   (site:gritservice.co.kr)")
