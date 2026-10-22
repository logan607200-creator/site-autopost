#!/bin/bash
# 새 컨테이너에서 정본 쓰기 차단 훅을 다시 설치한다. 실행: bash install_guard.sh
G="$(cd "$(dirname "$0")" && pwd)/guard_canon.py"
S="$HOME/.claude/settings.json"; mkdir -p "$HOME/.claude"
[ -f "$S" ] || echo '{}' > "$S"
jq --arg c "python3 $G" '.hooks.PreToolUse = ((.hooks.PreToolUse // []) | map(select(.hooks[0].command != $c))) + [{"matcher":"Edit|Write|NotebookEdit|MultiEdit|Bash","hooks":[{"type":"command","command":$c,"timeout":10}]}]' "$S" > "$S.tmp" && mv "$S.tmp" "$S" && echo "훅 설치됨: $S"
