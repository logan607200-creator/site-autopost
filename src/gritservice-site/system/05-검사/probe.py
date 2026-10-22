"""사이트 접속 확인. 결과를 02-실측/probe.csv 에 남긴다. 못 하면 ERROR 로 남긴다(통과로 치지 않는다)."""
import csv
import datetime
import urllib.request
from common import SYS, brand

url = brand()["대표주소"]
now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
try:
    with urllib.request.urlopen(url, timeout=10) as r:
        body = r.read(200000).decode("utf-8", "replace")
        code = r.status
        has_naver = "naver-site-verification" in body
        result, detail = "OK", f"status={code} naver-meta={'있음' if has_naver else '없음'}"
except Exception as e:  # 접속 못 함, 프록시 차단, 인증서 오류 등
    result, detail = "ERROR", f"{type(e).__name__}: {e}"[:200]
with open(SYS / "02-실측" / "probe.csv", "a", newline="", encoding="utf-8") as f:
    csv.writer(f).writerow([now, url, result, detail])
print(result, url, detail)
