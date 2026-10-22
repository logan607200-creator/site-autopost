"""PreToolUse 훅: AI가 01-정본을 고치려 하면 사람에게 승인을 묻는다.
Edit/Write/NotebookEdit은 경로로, Bash는 명령에 쓰기 신호가 있을 때 막는다.
스크립트가 안에서 몰래 쓰는 경우는 못 잡는다. 그 뒷받침은 check_site.py C8(해시)이다."""
import json, re, sys

CANON = "01-정본"
WRITE_BASH = re.compile(r"(>>?|\btee\b|\bsed\s+-[a-z]*i|\brm\b|\bmv\b|\bcp\b|\bchmod\b|\btruncate\b|\bdd\b|\bperl\s+-[a-z]*i|seal\.py|open\(|write_text|write_bytes)")

def decide(p):
    name = p.get("tool_name", "")
    ti = p.get("tool_input", {}) or {}
    if name in ("Edit", "Write", "NotebookEdit", "MultiEdit"):
        path = ti.get("file_path") or ti.get("notebook_path") or ""
        if CANON in path:
            return f"정본 파일 수정 시도: {path}"
    elif name == "Bash":
        cmd = ti.get("command", "")
        if (CANON in cmd and WRITE_BASH.search(cmd)) or "seal.py" in cmd:
            return "정본을 바꾸거나 봉인(seal.py)할 수 있는 명령"
    return None

try:
    why = decide(json.load(sys.stdin))
except Exception:
    why = None
if why:
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "ask",
        "permissionDecisionReason": "정본은 사람만 고칩니다. " + why + " — 승인하려면 사람이 직접 허용하세요."}}, ensure_ascii=False))
