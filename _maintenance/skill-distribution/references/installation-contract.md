# 네 경우의 설치 계약

| 호스트 | 현재 세션 | 프로젝트 설치 | 실행기 |
| --- | --- | --- | --- |
| macOS | Codex | PROJECT/.agents/skills/NAME | bash install.command --client codex --project PROJECT |
| macOS | Claude Code | PROJECT/.claude/skills/NAME | bash install.command --client claude-code --project PROJECT |
| Windows x64 네이티브 | Codex | PROJECT\.agents\skills\NAME | powershell.exe -NoProfile -ExecutionPolicy Bypass -File install-windows.ps1 -Client codex -ProjectPath PROJECT |
| Windows x64 네이티브 | Claude Code | PROJECT\.claude\skills\NAME | 같은 실행기에 -Client claude-code |

사용자는 하나의 주소와 같은 자연어 요청을 사용한다. 에이전트가 위 인수를 선택한다. 현재 클라이언트를 설치된 바이너리나 추측한 환경변수로 알아내지 않는다. 명시적 client 인수가 우선하고 `AI_SKILL_CLIENT`는 명시적으로 제공된 경우에만 보조한다. 모호하면 쓰기 전에 중단한다.

사용자 범위는 기존 배포 호환을 위해 Codex CODEX_HOME/skills(기본 ~/.codex/skills), Claude Code CLAUDE_CONFIG_DIR/skills(기본 ~/.claude/skills)를 쓴다. 최신 Codex 문서의 ~/.agents/skills와 기존 배포 경로는 구분한다. 기존 인식 경로를 확인해 중복 설치하지 않으며 새 프로젝트의 기본 시험은 프로젝트 범위로 한다. 스킬 인식을 실제 세션에서 별도 확인한다.

설정 폴더는 절대경로다. 프로젝트/사용자, 두 클라이언트의 개인 지침은 스킬 밖에 둔다. 설치 형제 기록 `.<NAME>-install`은 버전·클라이언트·범위 세 줄이며 비밀번호·토큰·절대 개인 경로를 넣지 않는다. 사용자 지정 설정 폴더에 사용자 범위로 설치했으면 다음 세션에도 실제 컨테이너를 유지한다. 다른 클라이언트의 개인 지침을 자동 복사하지 않는다.

설치기는 임시 복사 → 대상 이동을 사용한다. 동일 내용은 점검을 재개하고, 다른 버전/수정본/추가 파일·충돌 기록은 보존해 보고한다. 중복 잠금, 링크·정션·파일 경로를 거부한다. 원래 설치나 다른 렌더 락을 삭제하지 않는다. 실제 폴더 권한으로 판단하고 계정·소유자 이름으로 선제 거부하지 않는다. 승인 실행 경로가 있을 때만 실제 권한 실패 후 요청하고 ACL·소유권·전역 PATH·시스템 정책은 바꾸지 않는다.

manifest의 runtime이 null이면 파일 배치만 하며 Python을 요구하지 않는다. runtime 객체가 있으면 env, project_cache, user_cache, macos_launcher, windows_launcher를 지정한다. 런처는 doctor와 smoke --output-dir NEW_DIR를 제공하며 프로젝트 캐시 자동 선택과 사용자 범위 캐시를 지원한다. 새 프로젝트의 특별한 도구는 별도로 구현·검증하고 이 기본 계약만으로 자동 설치됐다고 표시하지 않는다.

README, INSTALLATION, 시작 안내, 오류 문서와 ZIP에 같은 버전·지원 범위를 사용한다. SDK·런처의 플랫폼 제약을 클라이언트 지원과 혼동하지 않는다. Git·패키지 관리자·GitHub 로그인 없이 공개 소스 ZIP을 에이전트가 받을 수 있어야 한다. 다운로드보안 경계와 첫 설치 네트워크 필요 여부는 설명한다.

공식 근거: [Codex 로컬 스킬](https://learn.chatgpt.com/docs/build-skills), [Claude Code 스킬](https://code.claude.com/docs/en/skills), [CLAUDE_CONFIG_DIR](https://code.claude.com/docs/en/claude-directory). 확인일 2026-10-23. 실제 클라이언트 인식은 별도 시험한다.
