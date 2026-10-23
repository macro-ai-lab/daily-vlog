# daily-vlog 실행 환경과 설치 검증

점검일: 2026-10-23. 대상: daily-vlog v017. 같은 공통 설치 정책을 naver-blog-draft v0.1.5에도 적용했습니다. 자동 설치 클라이언트는 Codex와 로컬 Claude Code입니다.

| 환경 | 확인한 근거와 결과 | 남은 검증 |
| --- | --- | --- |
| macOS Apple Silicon | 관리 세션에서 최종 ZIP을 새 폴더에 풀고 빈 런타임 도구 준비·doctor·smoke·이미지 열람·후속 명령 확인 | 새 물리 컴퓨터·다른 OS 정책 |
| Windows x64 · Codex | 사용자 전달 실기 보고: CodexSandboxOffline의 기존 캐시 설치, CodexSandboxOnline의 빈 캐시 도구 준비·doctor·smoke·PNG 열람·후속 명령 성공. 기존 Python 대체 다운로드 사용 | 최종 v016 ZIP의 Windows 재시험·새 채팅의 스킬 발견·다른 계정 접근·전체 브이로그 렌더 |
| Windows x64 · Claude Code | 공통 설치·런타임 코드 경로 제공 | 실제 클라이언트의 설치·스킬 호출·영상 처리 |
| Intel Mac | 코드 경로 제공 | 실제 장치 |
| 일반 Claude 채팅·Cowork | 자동 설치 대상 밖 | 지원한다고 안내하지 않음 |

런타임은 macOS 14 이상과 네이티브 Windows 10/11 x64용입니다. Windows ARM/32비트, Linux/WSL, 모바일·태블릿 단독 편집은 현재 지원하지 않습니다. 같은 컴퓨터의 새 폴더 시험은 새 OS나 다른 사용자 계정의 시험과 다릅니다.

## Windows 실기 결과의 의미

사용자가 전달한 인수인계와 붙여넣은 패치에 따르면 공개 v015는 실제 쓰기를 시도하기 전에 계정 이름이 `CodexSandbox`로 시작한다는 이유로 설치를 거부했습니다. 별도로 폴더 소유자 이름도 선제 거부했습니다. 이는 실제 쓰기 권한 부족을 입증한 결과가 아닙니다. v016은 두 검사를 제거하고 실제 디렉터리 생성·파일 쓰기·잠금 결과로 판단합니다. 기존 ACL·소유권·보안 정책은 변경하지 않습니다. Codex 자체에서 명령 실행 전 발생하는 `setup refresh` 오류와도 구분합니다.

차단을 제거한 빈 캐시 시험에서는 Windows HTTPS가 `SEC_E_NO_CREDENTIALS`로 실패했습니다. 기존 Python의 인증서 검증 HTTPS를 사용하는 대체 경로를 추가한 뒤 uv 0.13.1, 전용 Python 3.12.15, Pillow 13.0.0, PyAV 19.0.1, imageio-ffmpeg 0.6.0 준비와 테스트 영상 읽기가 성공했다고 전달받았습니다. 사용자 CMD 수동 실행 없이 에이전트 명령으로 완료한 결과입니다. 도구 캐시나 실제 개인 지침은 배포하지 않습니다.

실기 보고의 수정본·개인 지침 보존, 같은 버전 재실행, 설치 기록 충돌, 잠금, 변조 다운로드 거부 검사 결과는 전달 자료에 근거합니다. 원본 검증 JSON·전체 소스 ZIP은 이 관리 세션에 첨부되지 않았고, 붙여넣은 diff의 서식 일부가 손상되어 변경 의도를 정상 소스에 재적용했습니다. 따라서 이 보고를 최종 v016 ZIP의 Windows 시험으로 표시하지 않습니다.

## 관리 세션에서 다시 실행한 검사

- 기존 Python 회귀 검사 48개와 HTTPS 코드 검사 3개 통과. 후자는 인증서·호스트명 검증 유지, 최종 HTTP 리디렉션 거부, 인증서 실패 전파를 확인합니다.
- PowerShell 7.6.7을 macOS에서 실행해 설치·재실행·수정본/개인 지침·설치 기록·잠금 보호와 다운로드 분기 22개를 검사했습니다. 이 파일 작업 시험은 임시 fixture에서 플랫폼 검사만 생략하고 doctor/smoke는 대체했으므로 Windows ACL이나 영상 처리 시험이 아닙니다.
- 동일한 제품 다운로드 함수를 사용해 실제 기존 Python의 HTTPS로 공식 Windows uv ZIP을 받고 고정 SHA256 검증까지 통과했습니다. 기본 Windows HTTPS 실패는 제어된 오류로 대체했습니다. macOS에서 실행한 다운로드 시험이며 Windows Schannel 시험과 다릅니다.
- 최종 ZIP의 macOS 빈 캐시 설치·실제 doctor/smoke·이미지 열람은 별도로 확인했습니다. 사용자 원본과 실제 개인 프로필은 사용하지 않았습니다. 제작 SKILL.md·UI 기본 프롬프트·렌더러·기본 스타일은 변경하지 않았습니다.

## Python 사전 설치 안내의 범위

일반 설치 경로는 기존 Python이 필요 없습니다. Windows 기본 HTTPS가 실패한 경우 대체 다운로드는 이미 있는 실제 Python을 사용합니다. **기본 HTTPS도 실패하고 Python도 없는 PC는 현재 해결되지 않았습니다.** 인증서 검증을 끄거나 Python 스토어 바로가기를 실행하지 않습니다. Python 없는 Windows와 정상 Windows HTTPS 경로의 실제 장치 검증, 다른 계정·새 채팅 접근 검증이 남아 있습니다.

공식 문서: [Codex 로컬 스킬](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills), [Codex Windows 샌드박스 진단](https://learn.chatgpt.com/docs/windows/windows-sandbox#troubleshooting-and-faq), [Claude Code 스킬](https://code.claude.com/docs/en/skills).

## 공통 설치 정책 2026-10-23.1

2026-10-23 사용자가 v016 재시험에서 한 번에 설치된 것으로 추가 보고했습니다. 세부 검사 로그까지 새로 전달된 것은 아니므로 현재 세션의 모든 단계·새 채팅·다른 계정의 성공을 의미하지 않습니다. v017은 제품 제작 로직을 바꾸지 않고 공통 생성기·등록 프로젝트 검사·네 경우 GitHub OS 검사를 추가합니다. Windows 실제 에이전트 세션 보고와 CI의 실제 OS 설치·런타임 검사는 구분합니다.

CI는 Python이 있는 검사 프로세스에서 시작하지만 제품 설치 자식 프로세스의 PATH에서 별도 Python·Git을 제외하고 빈 프로젝트 캐시를 사용합니다. Windows 기본 HTTPS가 정상인 Python 없는 설치 경로를 검사할 수 있습니다. 제한된 계정의 기본 HTTPS까지 실패하는 경우 기존 Python 대체 경로에 대한 알려진 한계는 유지합니다. macOS의 시스템 기본 도구는 제거하지 않습니다. 실제 결과는 해당 커밋의 GitHub Installation matrix와 아티팩트에서 확인합니다.
