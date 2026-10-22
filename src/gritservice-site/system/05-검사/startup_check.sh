#!/bin/bash
# 시작 점검. FAIL/ERROR 가 하나라도 있으면 새 작업을 시작하지 말고 사례로 기록한다.
cd "$(dirname "$0")" || exit 2
rc=0
echo "== 1. 규칙·사례 위생"; python3 check_rules.py || rc=1
echo; echo "== 2. 사이트 검사 C1~C8 (C8=정본 해시)"; python3 check_site.py || rc=1
echo; echo "== 3. 본보기 회귀"; python3 regress.py || rc=1
echo; [ $rc -eq 0 ] && echo "시작 점검: 막힘 없음 (PENDING 은 위에서 확인)" || echo "시작 점검: 막힘 있음"
exit $rc
