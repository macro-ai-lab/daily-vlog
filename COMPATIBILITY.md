# 실행 환경과 자동 설치 검증

점검일: 2026-10-22. 대상: daily-vlog v015, naver-blog-draft v0.1.4. 자동 설치 대상은 **Codex와 로컬 Claude Code**입니다. 설치기는 클라이언트·OS·설치 범위를 분기합니다. 실제 클라이언트가 스킬을 인식하고 도구를 호출하는 검증과 설치 코드 검증을 구분합니다.

| 환경 | 직접 확인한 결과 | 남은 검증 |
| --- | --- | --- |
| macOS Apple Silicon · Codex 경로 | 프로젝트·사용자 설치, 동일 재실행, 개인 지침 보존, doctor·영상 인코딩·디코딩·프레임 추출 | 새 물리 컴퓨터·초보 사용자 시험 |
| macOS Apple Silicon · Claude Code 경로 | 빈 프로젝트·빈 캐시에서 자동 도구 설치 성공. 다음 프로세스에서 런타임 지정 없이 재사용. 프로젝트·사용자 설치와 재실행, 클라이언트별 개인 지침 제안·승인·재조회 성공 | 실제 Claude Code의 스킬 탐색·모델 호출·이미지 열람 |
| Intel Mac | 설치·런타임 분기 코드 제공 | 실제 장치 시험 |
| Windows x64 · 두 클라이언트 | 실제 설치기·런처를 PowerShell로 파싱하고 계정·소유자·경로 가드 28개 및 클라이언트별 경로 검사 12개 통과 | 실제 Windows·PowerShell 5.1·보호 ACL 갱신·영상 처리 |
| 네이버 블로그 기능 | 두 클라이언트의 프로젝트·사용자 파일 설치와 재실행, 기존 개인 지침 보존 검사 | 실제 브라우저·파일 첨부·임시저장·재열람 |
| 일반 Claude 채팅·Cowork | 이번 자동 설치 대상 밖 | 지원한다고 안내하지 않음 |

브이로그 런타임은 macOS 14 이상, 네이티브 Windows 10/11 x64를 대상으로 합니다. Windows ARM/32비트, Linux/WSL, 모바일·태블릿 단독 편집은 현재 지원하지 않습니다. Claude Code 자체가 실행 가능하더라도 편집 런타임의 OS 조건을 만족해야 합니다. 블로그 스킬은 Python이 필요 없으며 사용 환경에 실제 UI·파일 첨부 도구가 있어야 합니다.

## 직접 실행한 검사

- Python 회귀 검사 48개 통과. 신규 설치·재설치·수정본 보존·잠금·권한 실패·개인 지침·렌더 설정·미디어 분석을 포함합니다.
- 격리 경로에서 실제 자동 설치와 새 프로세스 실행 26단계 통과. Claude Code 프로젝트의 첫 실행은 Python·uv·Homebrew를 PATH에 노출하지 않고 빈 캐시에서 시작했습니다. 공식 uv, 전용 Python, 고정한 영상 모듈 설치부터 테스트 영상 읽기까지 약 31초였으며 일반적인 소요 시간 보장 수치는 아닙니다.
- 같은 배포본 재실행, Codex·Claude Code의 프로젝트·사용자 설치 및 사용자 지정 설정 폴더를 검사했습니다. 추가 조합의 런타임은 앞서 생성한 격리 캐시를 명시적으로 재사용했습니다. 사용자 범위에서는 설정 폴더 환경변수를 제거한 새 프로세스에서도 설치 기록으로 개인 지침 경로를 유지했습니다.
- 생성한 1초 무음 H.264 영상의 실제 인코딩·디코딩·CLI 프레임 3장 추출, 이미지·한글 폰트를 검사하고 결과 PNG를 에이전트 이미지 도구로 열람했습니다. 사용자 영상·실제 개인 프로필·네이버 계정은 사용하지 않았습니다.
- Windows 관련 검사는 macOS의 PowerShell 7.6.7에서 실제 스크립트의 가드·경로 계산 코드를 실행한 것입니다. 실제 Windows ACL, Windows PowerShell 5.1 또는 Claude Code 세션을 실행한 시험이 아닙니다.

이전 v014에서는 같은 Mac의 공개 ZIP 냉간 설치와 10초·1080×1920·24fps 무음 H.264 렌더를 전체 디코드하고 Noto Sans KR 자막·시간 표시를 열람했습니다. v015는 기존 편집 엔진과 Noto 기본값을 유지하며 설치·개인 지침 경로 분기를 추가합니다.

## 남은 조건

이 환경에 Claude Code 앱·CLI가 없어 실제 Claude 세션은 실행하지 않았습니다. 설치 코드·편집 코드의 동작 확인을 실제 클라이언트의 전체 동작 검증이라고 표시하지 않습니다. 설치한 환경에서 스킬 인식, 명령 실행, 프레임 이미지 열람을 확인해야 합니다. 블로그는 UI와 첨부 도구가 없으면 원고 작성까지만 가능합니다.

Windows에서 보고된 `.agents` 보호 권한 실패는 설치 재실행만으로 복구하지 않습니다. 샌드박스 계정의 설치와 해당 계정 소유 폴더를 거부하는 검사는 예방 로직입니다. 기존 폴더의 소유자·ACL·당시 오류 로그를 실제 환경에서 확인해야 하며 보안 정책·소유권·ACL을 자동 변경하지 않습니다.

## 공식 근거

- [Codex 로컬 스킬](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills)
- [Codex Windows 샌드박스 진단](https://learn.chatgpt.com/docs/windows/windows-sandbox#troubleshooting-and-faq)
- [Claude Code 스킬과 설치 범위](https://code.claude.com/docs/en/skills)
- [Claude Code 설정 폴더와 CLAUDE_CONFIG_DIR](https://code.claude.com/docs/en/claude-directory)
