#!/bin/bash
# The agent selects the scope after checking the host and its allowed write roots.
set -euo pipefail
BUNDLE="$(cd "$(dirname "$0")" && pwd -P)"
NAME="daily-vlog"
SOURCE="$BUNDLE/$NAME"
PROJECT=""
case "${1:-}" in
  --project)
    [[ $# == 2 && -d "$2" ]] || { echo '기존 작업 폴더를 --project 뒤에 지정하세요.' >&2; exit 2; }
    PROJECT="$(cd "$2" && pwd -P)"
    SKILLS="$PROJECT/.agents/skills"
    ;;
  --user|'')
    [[ $# -le 1 ]] || exit 2
    SKILLS="${CODEX_HOME:-$HOME/.codex}/skills"
    ;;
  *) echo '설치 인수: --project 작업폴더 또는 --user. Codex가 환경과 권한을 확인해 선택합니다.' >&2; exit 2 ;;
esac
[[ "$(uname -s)" == Darwin ]] || { echo 'README의 환경 분기를 따라 이 환경에 맞는 설치기를 사용하세요.' >&2; exit 2; }
[[ -f "$SOURCE/SKILL.md" ]] || { echo '스킬 파일이 없습니다. 압축을 완전히 해제하세요.' >&2; exit 2; }
# Reject links before creating anything beneath the installation root.
for CHECK_PATH in "${PROJECT:+$PROJECT/.agents}" "$SKILLS"; do
  [[ -z "$CHECK_PATH" || ! -L "$CHECK_PATH" ]] || { echo '설치 상위 경로가 링크입니다. 원래 위치를 확인하세요.' >&2; exit 2; }
done
if ! mkdir -p "$SKILLS"; then
  echo '[INSTALL_PATH_DENIED] 설치 위치에 쓸 수 없습니다. README의 권한 진단을 따르세요.' >&2; exit 2
fi
TARGET="$SKILLS/$NAME"
STAGE=""
LOCK=""
cleanup() {
  [[ -z "$STAGE" || ! -d "$STAGE" ]] || rm -rf "$STAGE"
  [[ -z "$LOCK" ]] || rmdir "$LOCK" 2>/dev/null || true
}
trap cleanup EXIT
if ! mkdir "$SKILLS/.$NAME-install.lock" 2>/dev/null; then
  echo '[INSTALL_LOCK_OR_PERMISSION] 다른 설치 또는 쓰기 권한을 확인하세요. 기존 잠금은 삭제하지 않았습니다.' >&2; exit 2
fi
LOCK="$SKILLS/.$NAME-install.lock"
if [[ -e "$TARGET" || -L "$TARGET" ]]; then
  if [[ -L "$TARGET" || ! -d "$TARGET" ]] || ! diff -qr "$SOURCE" "$TARGET" >/dev/null; then
    echo '[EXISTING_SKILL_DIFFERS] 다른 버전 또는 수정본이 있습니다. 기존 파일은 보존했습니다.' >&2; exit 2
  fi
  echo '같은 스킬이 있습니다. 남은 점검을 이어갑니다.'
else
  STAGE="$(mktemp -d "$SKILLS/.$NAME-install.XXXXXX")"
  cp -R "$SOURCE/." "$STAGE/"
  mv "$STAGE" "$TARGET"
  STAGE=""
fi
echo "스킬 파일 확인 완료: $TARGET"
if [[ "$NAME" == daily-vlog ]]; then
  if [[ -n "$PROJECT" ]]; then
    export DAILY_VLOG_RUNTIME="${DAILY_VLOG_RUNTIME:-$PROJECT/.daily-vlog-runtime/v1}"
  fi
  if ! bash "$TARGET/scripts/run.sh" doctor; then
    echo '[RUNTIME_CHECK_FAILED] 스킬 파일은 복사됐지만 편집 도구 준비·점검이 실패했습니다. 위 오류를 확인하세요.' >&2; exit 1
  fi
  CHECK_ROOT="${DAILY_VLOG_RUNTIME:-$HOME/Library/Caches/daily-vlog/v1}/checks"
  if ! bash "$TARGET/scripts/run.sh" smoke --output-dir "$CHECK_ROOT/check-$(/usr/bin/uuidgen)"; then
    echo '[VIDEO_CHECK_FAILED] 테스트 영상 생성·읽기 점검이 실패했습니다. 오류 보고를 확인하세요.' >&2; exit 1
  fi
  echo '편집 도구와 테스트 영상 읽기 점검 완료. 에이전트의 이미지 열람 가능 여부는 별도로 확인하세요.'
else
  echo '스킬 파일 설치 완료. 컴퓨터 유즈·파일 첨부·로그인은 현재 채팅에서 별도로 확인하세요.'
fi
[[ -z "$PROJECT" ]] || echo "사용 범위: 이 프로젝트($PROJECT). 런타임과 개인 자료는 Git에 올리지 마세요."
echo '현재 채팅에서 스킬 인식을 먼저 확인하세요. 목록에 없을 때만 같은 프로젝트의 새 채팅을 여세요.'
