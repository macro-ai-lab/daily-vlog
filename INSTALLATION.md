# 설치를 진행하는 에이전트에게

사용자에게 운영체제별 명령이나 설치 범위를 고르게 하지 않는다. README의 같은 요청 문장에서 시작해 현재 호스트와 실제 허용된 경로에 따라 아래 절차를 적용한다. 이 문서는 스킬 설치가 실패해도 읽을 수 있도록 스킬 폴더 밖에 둔다.

## 0. 사용 중인 에이전트 확인

자동 설치 대상은 **Codex와 로컬 Claude Code**다. 현재 대화의 에이전트가 자기 클라이언트를 확인해 Codex는 `codex`, Claude Code는 `claude-code`를 설치기에 명시한다. 실행 파일이 설치되어 있다는 이유로 현재 클라이언트를 추측하지 않는다. 사용자에게 클라이언트나 OS를 고르게 하지 않는다. 현재 에이전트를 확인할 수 없으면 파일을 쓰기 전에 상황을 설명한다. 일반 Claude 채팅·Cowork는 이번 대상이 아니다.

설치기는 명시한 `--client` / `-Client`를 우선하고, `auto`일 때만 `AI_SKILL_CLIENT`를 읽는다. 둘 다 없거나 지원하지 않는 값이면 `CLIENT_REQUIRED`로 파일 생성 전에 중단한다. 이 환경변수를 전역으로 설정하지 않는다. [점검 범위](https://github.com/macro-ai-lab/reels-maker/blob/main/COMPATIBILITY.md)를 확인한다.

## 1. 실행 환경 확인

파일을 쓰기 전에 현재 작업 폴더, OS/CPU, 명령 실행 도구와 로컬 파일 접근 가능 여부를 확인한다. 읽기 전용의 짧은 명령을 한 번 실행한다. 영상 편집 런타임은 macOS 14 이상 또는 Windows x64를 대상으로 한다. Linux·Windows ARM/32비트·휴대폰/태블릿 단독 편집은 지원한다고 안내하지 않는다. 블로그 스킬은 별도 Python이 필요 없지만 실제 UI와 파일 첨부 도구가 필요하다. 사용자의 실제 앱·도구로 지원 여부를 판단한다.

명령 자체가 `setup refresh had errors`, `Failed to create unified exec process` 등으로 시작되지 않으면 **호스트 실행 환경 실패**다. Python이나 영상 파일 오류로 바꾸어 설명하지 않는다. 복사·재설치·새 채팅을 반복하지 말고 현재 실패와 미완료 단계를 보고한다. 읽을 수 있으면 `$CODEX_HOME/.sandbox/setup_error.json`과 해당 시점의 `sandbox*.log`에서 실패 경로·OS 오류만 확인한다. `.sandbox-secrets`, 인증 파일, 전체 개인 로그는 수집하거나 배포물에 넣지 않는다.

## 2. 설치 범위와 권한 선택

기존 프로젝트·사용자 범위의 같은 스킬을 먼저 찾아 중복 설치와 수정본 덮어쓰기를 피한다. 사용자가 지정한 범위가 있으면 따른다. 지정이 없다면 현재 프로젝트가 있고 허용된 쓰기 범위라면 프로젝트 범위를 우선한다. 프로젝트가 없거나 모든 프로젝트에 쓰는 설치가 허용돼 있으면 사용자 범위를 선택한다. 프로젝트를 소스 압축 해제 폴더나 Downloads로 임의 지정하지 않는다. 작업 폴더가 정해져 있지 않고 사용자 범위도 허용되지 않았을 때만 사용할 폴더를 확인한다.

| 범위 | Codex | Claude Code |
| --- | --- | --- |
| 프로젝트 | `<PROJECT>/.agents/skills/<SKILL_NAME>` | `<PROJECT>/.claude/skills/<SKILL_NAME>` |
| 사용자 | `${CODEX_HOME:-~/.codex}/skills/<SKILL_NAME>` | `${CLAUDE_CONFIG_DIR:-~/.claude}/skills/<SKILL_NAME>` |

사용자 설정 폴더를 지정했다면 절대경로여야 한다. 기존 다른 위치에 같은 스킬이 있으면 임의 이중 설치하지 않는다. Windows의 홈은 사용자 프로필 기준이다. 프로젝트 설치 후에는 같은 프로젝트에서 사용한다.

설치기는 스킬의 형제 파일 `skills/.<SKILL_NAME>-install`에 `skill-install-v1`, 클라이언트, 범위를 세 줄로 기록한다. 다음 세션에서 환경변수를 넘기지 않아도 같은 설치 범위를 찾는다. 사용자 범위의 사용자 지정 설정 폴더는 실제 설치 컨테이너 경로를 유지한다. 기록이 다른 클라이언트·범위와 충돌하거나 링크면 덮어쓰지 않는다. 스킬 밖 개인 지침은 각 클라이언트 설정 폴더의 `daily-vlog/user-overrides.json` 또는 `naver-blog-draft/preferences.md`다. 클라이언트 사이의 지침 복사는 별도 사용자 요청으로 처리한다.

- 편집 런타임: 프로젝트 설치 시 `<PROJECT>/.daily-vlog-runtime/v1`; 사용자 설치 시 OS별 사용자 캐시. 명시한 `DAILY_VLOG_RUNTIME`이 있으면 우선한다. 스킬 경로와 런타임 경로를 모두 실제 허용 범위에 맞춘다. 사용자 캐시가 불허일 때는 승인된 작업 폴더의 별도 캐시를 명시하며, 매 실행 같은 위치를 사용한다. 전역 PATH·시스템 Python은 바꾸지 않는다.

Windows에서는 실행 계정이나 폴더 소유자 이름이 `CodexSandbox`로 시작한다는 이유만으로 설치를 중단하지 않는다. 허용된 작업 폴더에서 설치기를 실행하고 실제 디렉터리 생성·잠금·파일 쓰기 결과로 설치 가능 여부를 판단한다. 기존 파일·개인 지침·링크 거부·설치 기록 충돌 검사와 다운로드 인증서·해시 검증을 유지한다. 실제 권한 오류가 발생하면 해당 단계와 경로를 보고하며, 앱이 제공하는 승인된 실행 경로가 있을 때만 사용한다. 그런 경로가 없으면 미완료로 보고한다. 사용자 CMD 수동 실행을 에이전트 자동 설치 성공으로 기록하지 않는다. 기존 ACL·소유권·시스템 정책은 변경하지 않는다.

사용자 폴더 권한 때문에 실패했고 프로젝트 범위 설치가 허용돼 있다면 해당 위치에 설치할 수 있다. 이미 남은 파일은 보존하고 어느 범위에 무엇이 설치됐는지 보고한다. **프로젝트 범위로 바꾼다고 Codex 자체의 setup refresh 문제가 해결된다고 가정하지 않는다.**

## 3. 환경에 맞는 설치기 실행

사용자가 준 GitHub 주소에서 이 README와 manifest의 현재 버전을 확인하고, **에이전트가** 일치하는 공개 소스 아카이브를 작업 폴더에 내려받아 압축을 완전히 푼다. 사용자에게 ZIP 다운로드·압축 해제나 OS별 설치 파일 선택을 요구하지 않는다. 릴스 메이커 v020.1의 고정 소스는 `https://github.com/macro-ai-lab/reels-maker/archive/refs/tags/v020.1.zip`이다. 릴리스의 배포 ZIP은 검증·복구용으로 유지하며 필요하면 같은 버전인 것을 확인한 에이전트가 직접 사용할 수 있다. Git·GitHub 로그인은 필요 없다. 각 인수에는 환경의 실제 절대경로를 따옴표로 전달한다.

에이전트가 현재 클라이언트를 나타내는 `CLIENT`를 `codex` 또는 `claude-code`의 실제 값으로 치환하고, 범위도 선택해 실행한다. 아래 표는 에이전트용이며 사용자에게 명령을 선택시키지 않는다.

| 감지한 호스트 | 프로젝트 범위 | 사용자 범위 |
| --- | --- | --- |
| macOS | `bash /BUNDLE/install.command --client CLIENT --project /PROJECT` | `bash /BUNDLE/install.command --client CLIENT --user` |
| Windows | `powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File C:\BUNDLE\install-windows.ps1 -Client CLIENT -ProjectPath C:\PROJECT` | 같은 설치기에 `-Client CLIENT -UserScope` 전달 |

PowerShell의 실행 정책 허용은 해당 프로세스에만 한정한다. 조직 정책이 막으면 우회하지 않는다. 설치기는 동일 파일이면 남은 점검을 재개하고, 수정본·다른 버전·링크 대상은 거부한다. 승인 없이 기존 스킬이나 개인 지침을 삭제하지 않는다. 네트워크/다운로드 실패도 원문과 실패 단계를 남기며 해시 검증을 끄지 않는다.

## 다운로드와 Python 사전 설치 범위

기본 경로는 별도 Python·Git 설치 없이 전용 편집 도구를 준비한다. Windows의 uv 다운로드는 먼저 `Invoke-WebRequest`를 사용한다. 실패하면 PATH에서 WindowsApps 스토어 바로가기를 제외한 실제 `python.exe`를 찾아 `-I` 격리 모드와 `ssl.create_default_context()`의 인증서 검증 HTTPS로 재시도한다. 최종 응답 주소도 HTTPS여야 하고, 받은 파일은 기존 고정 SHA256과 일치해야 실행한다. 이 기존 Python은 uv 다운로드용이며 uv가 새로 준비하는 편집용 Python과 구분한다.

Windows HTTPS도 실패하고 기존 Python도 없으면 이 대체 경로는 작동하지 않는다. Python 없는 환경까지 해결됐다고 안내하지 않는다. 대체 경로도 실패하면 원래 오류와 실패 단계를 보고하고 인증서·해시 검증을 끄거나 시스템 설정을 바꾸지 않는다. Python 설치를 사용자 수동 절차로 넘긴 뒤 자동 설치 성공이라고 표시하지 않는다.

## 4. 완료 판정

파일 복사와 실제 사용 가능 여부를 나눠 확인한다. 현재 채팅의 스킬 목록 또는 도구로 인식을 확인하고, 목록이 갱신되지 않을 때만 같은 프로젝트의 새 채팅을 안내한다. 새 채팅 자체가 필요하지 않은 환경에 재시작을 강요하지 않는다.

### reels-maker

설치기는 `doctor` 후 `smoke --output-dir NEW_DIR`를 실행한다. smoke는 사용자 원본 대신 1초짜리 무음 테스트 영상을 생성하고 **실제 인코딩 → 디코딩 → CLI 프레임 3장 추출 → 이미지 읽기·한글 폰트**를 점검한다. 프로젝트 설치 후 새 세션에서도 런처가 같은 프로젝트 캐시와 해당 클라이언트 개인 지침을 선택한다. `context` 또는 `doctor`의 `installation`으로 경로를 확인한다. Codex는 `$reels-maker`, Claude Code는 `/reels-maker` 또는 자연어로 호출한다. 성공 결과의 `preview`를 이미지 열람 도구로 실제로 열고, 동일 채팅에서 간단한 명령이 계속 실행되는지도 확인한다. 도구가 없거나 실패하면 그 단계를 미확인으로 보고한다. 자동 점검의 `agent_image_view: not_checked`는 원본 그대로 두고, 실제 열람 결과와 열람 후 후속 명령 성공은 별도 작업 기록에 남긴다. 현재 세션의 명령 성공, 새 채팅의 스킬 발견·실행, 다른 계정의 파일 접근은 각각 구분한다. 설치만으로 다른 계정의 접근 권한까지 보장하지 않는다.

보고: 설치 버전·범위·스킬 경로·런타임 경로, 파일 설치/도구 점검/테스트 영상 읽기/에이전트 이미지 열람 각각의 성공·실패·미확인. 어느 단계든 실패하면 전체 준비 완료라고 하지 않는다. 사용자의 실제 영상을 편집하려면 별도로 파일 접근·장면 확인 및 기존 콘티/스타일 확인 절차를 따른다.

### naver-blog-draft

설치기는 스킬 파일과 설치 기록만 배치하고 개인 지침 경로를 출력한다. Codex는 `$naver-blog-draft`, Claude Code는 `/naver-blog-draft` 또는 자연어로 호출한다. 현재 채팅에서 컴퓨터 유즈와 로컬 파일 첨부 도구를 사용할 수 있는지 확인한다. 이 점검만을 위해 네이버에 로그인하거나 사진을 업로드하지 않는다. 파일 설치 성공, UI/첨부 도구 가용성, 실계정 작성·저장 미검증을 구분해 보고한다.

## 오류를 구분하는 기준

| 관찰한 오류 | 확인할 지점 |
| --- | --- |
| `setup refresh had errors` | Codex의 샌드박스 준비 로그. `.agents` 소유권/보호 ACL 실패와 런타임 파일 잠금은 별개 후보이며 문구 하나로 원인을 확정하지 않는다. |
| `CLIENT_REQUIRED` / `INSTALL_CONTEXT_CONFLICT` | 현재 에이전트의 클라이언트 인수와 기존 설치 기록을 확인한다. 다른 클라이언트로 덮어쓰지 않는다. |
| `INSTALL_PATH_DENIED` / `INSTALL_LOCK_OR_PERMISSION` | 실제 실패한 경로와 생성·쓰기·잠금 오류, 허용 범위를 확인한다. 기존 ACL을 보존한다. 이전 v015의 `HOST_INSTALL_REQUIRED` / `PROJECT_OWNER_MISMATCH`는 계정 이름에 따른 선제 차단으로, 공통 템플릿은 사용하지 않는다. |
| `RUNTIME_DOWNLOAD_FAILED` / `SEC_E_NO_CREDENTIALS` | 기본 Windows HTTPS와 선택적 기존 Python 대체 경로의 결과를 확인한다. Python이 없으면 대체 경로를 사용할 수 없다. 인증서 검증은 유지한다. |
| `ARCHIVE_HASH_MISMATCH` | 고정 해시와 다운로드 파일이 달라 실행 전에 중단한다. 해시를 임의로 바꾸지 않는다. |
| `RUNTIME_CHECK_FAILED` | 실제 Python/모듈/폰트/FFmpeg 오류. 파일 복사 성공과 분리한다. |
| `VIDEO_CHECK_FAILED` | 해당 출력 폴더의 `installation-check.json`: 처음 실패한 stage, 종료 코드와 stderr. 원본 영상 오류로 단정하지 않는다. |
| 테스트 영상은 성공, 사용자 영상은 실패 | 실제 파일 경로·읽기 권한·파일 존재/크기·디코드 오류를 확인한다. 원음을 삭제하거나 변환하기 전 기존 승인 절차를 따른다. |
| 프레임 추출 성공, 이미지 열람 실패 | 에이전트의 이미지 도구/파일 경로 접근 문제. 영상 내용을 지어내지 않는다. |

설치기의 파일 작업 실패와 Codex 자체의 샌드박스 준비 오류를 구분한다. 사용자 전달 Windows 실기 결과는 해당 PC의 수정 소스 시험이며 최종 배포 ZIP, 새 채팅·다른 계정·Python 없는 환경까지 검증한 결과로 확대하지 않는다.

근거: [Claude Code 스킬](https://code.claude.com/docs/en/skills), [Claude Code 설정 폴더](https://code.claude.com/docs/en/claude-directory), [로컬 스킬 검색 범위](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills), [Windows 샌드박스 문제 해결](https://learn.chatgpt.com/docs/windows/windows-sandbox#troubleshooting-and-faq).

## 유지보수 계약

설치기는 distribution.json과 `_maintenance/skill-distribution`의 공통 템플릿에서 생성합니다. 정책 변경 시 등록된 모든 프로젝트를 동기화하고 누락을 검사합니다. 일반 사용자의 설치는 이 문서를 따르며 관리용 스킬 설치가 선행 조건이 아닙니다. 설치 계정 이름으로 선제 거부하지 않습니다.

## 이전 이름과 설정 보존

제품 이름은 reels-maker로 바뀌었지만 개인 지침 `daily-vlog/user-overrides.json`과 도구 캐시는 호환성을 위해 유지합니다. 기존 daily-vlog 설치·수정본은 별도 요청 없이 삭제·덮어쓰지 않습니다. 전환 요청 시 기존 설치를 확인하고 [호환 안내](reels-maker/references/renaming.md)를 따릅니다.
