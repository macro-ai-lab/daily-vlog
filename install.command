#!/bin/bash
set -euo pipefail
BUNDLE="$(cd "$(dirname "$0")" && pwd)"
SOURCE="$BUNDLE/daily-vlog"
TARGET_BASE="${CODEX_HOME:-$HOME/.codex}/skills"
TARGET="$TARGET_BASE/daily-vlog"
if [[ ! -f "$SOURCE/SKILL.md" ]]; then
  echo '스킬 파일이 없습니다. ZIP을 완전히 압축 해제한 뒤 다시 실행하세요.' >&2; exit 1
fi
mkdir -p "$TARGET_BASE"
if ! mkdir "$TARGET" 2>/dev/null; then
  echo '일상 브이로그 스킬이 이미 있거나 설치 위치에 쓸 수 없습니다. 기존 파일은 바꾸지 않았습니다. 에이전트에게 확인을 요청하세요.' >&2; exit 1
fi
/usr/bin/ditto "$SOURCE" "$TARGET"
echo '스킬을 추가했습니다. 영상 편집 도구를 준비합니다.'
bash "$TARGET/scripts/run.sh" setup
echo '준비가 끝났습니다. Codex에서 새 채팅을 열고 영상 폴더를 지정한 뒤 브이로그를 만들어 달라고 하세요.'
