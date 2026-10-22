#!/bin/bash
# Private runtime; no Homebrew, sudo, shell profile or system Python changes.
set -euo pipefail
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd -P)"
if [[ "${1:-}" == "--help" || $# == 0 ]]; then
  echo '일상 브이로그: setup | doctor | context | smoke --output-dir DIR | inspect FOLDER | inspect --files FILE... | frames FILE --output-dir DIR | survey FILE --output-dir DIR [--start SEC --end SEC --interval SEC --max-frames N] | overrides show/propose/save | customize PLAN --root DIR --patch PATCH --output NEW_PLAN | font --name NAME --output-dir DIR | render PLAN --root DIR --output FILE --poster FILE [--shared-lock FILE]'
  exit 0
fi
if [[ "$(uname -s)" != Darwin ]]; then
  echo '이 실행기는 맥용입니다. Windows x64는 scripts/run.cmd를 사용하세요. Linux는 지원하지 않습니다.' >&2
  exit 2
fi
MAC_MAJOR="$(/usr/bin/sw_vers -productVersion | /usr/bin/cut -d. -f1)"
if (( MAC_MAJOR < 14 )); then
  echo '이 버전은 macOS 14 이상이 필요합니다. 시스템 업데이트는 자동으로 진행하지 않습니다.' >&2
  exit 2
fi
# Installation context persists outside the skill files, without client settings changes.
SKILLS_DIR="$(dirname "$SKILL_DIR")"
CONTAINER_DIR="$(dirname "$SKILLS_DIR")"
INSTALL_MARKER="$SKILLS_DIR/.daily-vlog-install"
INSTALL_SCOPE="source"
INSTALL_CLIENT="${AI_SKILL_CLIENT:-codex}"
if [[ -L "$INSTALL_MARKER" ]]; then
  echo '설치 기록이 링크입니다. 설치 위치를 확인하세요.' >&2; exit 2
elif [[ -e "$INSTALL_MARKER" ]]; then
  INSTALL_DATA=()
  while IFS= read -r INSTALL_LINE || [[ -n "$INSTALL_LINE" ]]; do INSTALL_DATA+=("$INSTALL_LINE"); done < "$INSTALL_MARKER"
  if [[ ${#INSTALL_DATA[@]} != 3 || "${INSTALL_DATA[0]}" != skill-install-v1 ]]; then
    echo '설치 기록 형식이 다릅니다. 설치 위치를 확인하세요.' >&2; exit 2
  fi
  INSTALL_CLIENT="${INSTALL_DATA[1]}"; INSTALL_SCOPE="${INSTALL_DATA[2]}"
  [[ "$INSTALL_SCOPE" == project || "$INSTALL_SCOPE" == user ]] || { echo '설치 범위 기록이 다릅니다.' >&2; exit 2; }
elif [[ "$(basename "$CONTAINER_DIR")" == .claude ]]; then
  INSTALL_CLIENT='claude-code'
elif [[ "$(basename "$CONTAINER_DIR")" == .agents || "$(basename "$CONTAINER_DIR")" == .codex ]]; then
  INSTALL_CLIENT='codex'
fi
case "$INSTALL_CLIENT" in
  claude-code) CONFIG_BASE="${CLAUDE_CONFIG_DIR:-$HOME/.claude}" ;;
  codex) CONFIG_BASE="${CODEX_HOME:-$HOME/.codex}" ;;
  *) echo '설치 클라이언트를 확인할 수 없습니다.' >&2; exit 2 ;;
esac
if [[ ! -e "$INSTALL_MARKER" && "$(basename "$SKILLS_DIR")" == skills ]]; then
  if [[ "$CONTAINER_DIR" == "$CONFIG_BASE" ]]; then INSTALL_SCOPE='user'
  elif [[ "$(basename "$CONTAINER_DIR")" == .agents || "$(basename "$CONTAINER_DIR")" == .claude ]]; then INSTALL_SCOPE='project'
  fi
fi
if [[ "$INSTALL_SCOPE" == user ]]; then CONFIG_BASE="$CONTAINER_DIR"; fi
[[ "$CONFIG_BASE" == /* ]] || { echo '클라이언트 설정 경로는 절대경로여야 합니다.' >&2; exit 2; }
export AI_SKILL_CLIENT="$INSTALL_CLIENT"
export DAILY_VLOG_PROFILE="${DAILY_VLOG_PROFILE:-$CONFIG_BASE/daily-vlog/user-overrides.json}"
if [[ "$INSTALL_SCOPE" == project ]]; then
  PROJECT_ROOT="$(dirname "$CONTAINER_DIR")"
  TASK_RUNTIME="${DAILY_VLOG_RUNTIME:-$PROJECT_ROOT/.daily-vlog-runtime/v1}"
else
  TASK_RUNTIME="${DAILY_VLOG_RUNTIME:-${HOME}/Library/Caches/daily-vlog/v1}"
fi
export UV_CACHE_DIR="$TASK_RUNTIME/uv-cache"
export UV_PYTHON_INSTALL_DIR="$TASK_RUNTIME/python"
export UV_PROJECT_ENVIRONMENT="$TASK_RUNTIME/venv"
export UV_NO_PROGRESS=1
export UV_NO_CONFIG=1
export UV_PYTHON_DOWNLOADS=automatic
export UV_DEFAULT_INDEX=https://pypi.org/simple
export DAILY_VLOG_RUNTIME="$TASK_RUNTIME"
export PYTHONDONTWRITEBYTECODE=1
UV_EXE="$TASK_RUNTIME/bin/uv"
RUNTIME_FINGERPRINT="$(/bin/cat "$SKILL_DIR/runtime/pyproject.toml" "$SKILL_DIR/runtime/uv.lock" | /usr/bin/shasum -a 256 | /usr/bin/cut -d' ' -f1)"
if [[ "$1" != setup && -x "$TASK_RUNTIME/venv/bin/python" && -f "$TASK_RUNTIME/ready.sha256" ]]; then
  if [[ "$(/bin/cat "$TASK_RUNTIME/ready.sha256")" == "$RUNTIME_FINGERPRINT" ]]; then
    exec "$TASK_RUNTIME/venv/bin/python" "$SKILL_DIR/scripts/vlog.py" "$@"
  fi
fi
if ! mkdir -p "$TASK_RUNTIME"; then
  echo '전용 도구 폴더에 쓸 수 없습니다. 에이전트에게 이 폴더의 설치 권한 확인을 요청하세요.' >&2; exit 2
fi
if ! mkdir "$TASK_RUNTIME/setup.lock" 2>/dev/null; then
  if [[ -d "$TASK_RUNTIME/setup.lock" ]]; then
    echo '다른 설치가 진행 중입니다. 완료 후 다시 요청하세요. 중단된 설치라면 실행 중인 설치가 없는지 먼저 확인해야 합니다.' >&2; exit 3
  fi
  echo '설치 폴더에 쓸 권한이 없습니다. 에이전트에게 전용 도구 설치 권한을 확인해 달라고 하세요.' >&2; exit 2
fi
trap 'rmdir "$TASK_RUNTIME/setup.lock" 2>/dev/null || true' EXIT
if [[ ! -x "$UV_EXE" ]]; then
  case "$(uname -m)" in
    arm64) UV_ARCH=aarch64; UV_SHA=cfe454573412ff7380d15fc7dae5997ab53ffce72fce0a78e91ddbc84001acd2 ;;
    x86_64) UV_ARCH=x86_64; UV_SHA=bb7b805bdcf3d0bc8c74ceb94569e6b3e8aa35bd492acdbb9d46bf46d9d4ff6b ;;
    *) echo '지원하지 않는 맥 CPU입니다.' >&2; exit 2 ;;
  esac
  UV_TARGET="uv-${UV_ARCH}-apple-darwin"
  DOWNLOAD_DIR="$(mktemp -d "$TASK_RUNTIME/download.XXXXXX")"
  trap 'rm -rf "$DOWNLOAD_DIR"; rmdir "$TASK_RUNTIME/setup.lock" 2>/dev/null || true' EXIT
  echo '1/3 편집 도구 관리자를 준비합니다. 첫 실행에는 인터넷이 필요합니다.' >&2
  /usr/bin/curl --fail --location --silent --show-error --proto '=https' --tlsv1.2 --connect-timeout 20 --max-time 180 \
    "https://github.com/astral-sh/uv/releases/download/0.13.1/${UV_TARGET}.tar.gz" -o "$DOWNLOAD_DIR/uv.tar.gz"
  printf '%s  %s\n' "$UV_SHA" "$DOWNLOAD_DIR/uv.tar.gz" | /usr/bin/shasum -a 256 -c - >&2
  /usr/bin/tar -xzf "$DOWNLOAD_DIR/uv.tar.gz" -C "$DOWNLOAD_DIR" "$UV_TARGET/uv"
  mkdir -p "$TASK_RUNTIME/bin"
  mv "$DOWNLOAD_DIR/$UV_TARGET/uv" "$UV_EXE"
  rm -rf "$DOWNLOAD_DIR"
  trap 'rmdir "$TASK_RUNTIME/setup.lock" 2>/dev/null || true' EXIT
fi
if [[ "$("$UV_EXE" --version)" != 'uv 0.13.1'* ]]; then
  echo '전용 uv 버전이 예상과 다릅니다. 에이전트에게 환경 확인을 요청하세요.' >&2; exit 2
fi
echo '2/3 전용 Python과 영상 모듈을 확인합니다. 빠진 항목만 준비합니다.' >&2
"$UV_EXE" sync --project "$SKILL_DIR/runtime" --locked --no-dev --no-editable --python 3.12 --managed-python --no-build
"$TASK_RUNTIME/venv/bin/python" "$SKILL_DIR/scripts/vlog.py" doctor >/dev/null
if [[ ! -e "$TASK_RUNTIME/render.lock" ]]; then
  touch "$TASK_RUNTIME/render.lock"
fi
printf '%s\n' "$RUNTIME_FINGERPRINT" > "$TASK_RUNTIME/ready.sha256"
rmdir "$TASK_RUNTIME/setup.lock"
trap - EXIT
if [[ "$1" == setup ]]; then
  shift
  echo '3/3 설치 결과를 확인합니다.' >&2
  exec "$TASK_RUNTIME/venv/bin/python" "$SKILL_DIR/scripts/vlog.py" doctor "$@"
fi
exec "$TASK_RUNTIME/venv/bin/python" "$SKILL_DIR/scripts/vlog.py" "$@"
