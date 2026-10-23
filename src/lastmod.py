"""페이지 '최종 수정일'을 실제로 바뀐 날로 계산한다(날짜를 손으로 적지 않게).
원본 파일이 커밋 안 된 채 바뀌어 있으면 오늘(한국 시간), 아니면 그 파일들의 마지막 커밋 날짜."""
import datetime, subprocess, pathlib


def today():
    return (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=9)).date().isoformat()


def lastmod(*paths):
    paths = [str(p) for p in paths]
    root = pathlib.Path(__file__).resolve().parent.parent
    try:
        dirty = subprocess.run(["git", "status", "--porcelain", "--", *paths], cwd=root, capture_output=True, text=True, check=True).stdout.strip()
        if dirty:
            return today()
        d = subprocess.run(["git", "log", "-1", "--format=%cs", "--", *paths], cwd=root, capture_output=True, text=True, check=True).stdout.strip()
        return min(d, today()) if d else today()
    except Exception:
        return today()
