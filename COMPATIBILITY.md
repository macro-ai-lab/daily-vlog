# 스킬 실행 환경별 호환성 점검

점검일: 2026-10-22. 대상은 공개 daily-vlog v014와 naver-blog-draft v0.1.3 설치 ZIP입니다. 현재 자동 설치는 Codex용입니다. 스킬 표준 형식의 호환성과 각 앱에서 실제로 실행되는지는 구분합니다.

| 환경 | 확인한 결과 | 현재 판정 |
| --- | --- | --- |
| Codex와 macOS Apple Silicon | 공개 ZIP을 빈 프로젝트·빈 도구 캐시에 설치하고 테스트 영상 읽기와 10초 MP4 렌더 성공 | 로컬 실행 검증 통과. 새 OS·초보 사용자 시험은 별도 |
| Codex와 Windows x64 | PowerShell 파서 및 설치 계정·소유자·경로 가드 28개 항목을 macOS에서 실행해 통과 | Windows 실기 미검증. 기존 `.agents` 보호 권한 실패는 해결 확인 전 |
| Claude Code | `.claude/skills/daily-vlog` 구조에 놓고 런타임 경로를 명시했을 때 doctor·영상 생성·디코드·프레임 추출 성공 | 편집 코드 재사용 경로만 검증. 자동 설치·스킬 탐색·Claude의 실제 호출은 미지원 또는 미검증 |
| 일반 Claude 채팅 | 배포 ZIP의 루트에 설치기·README 등이 있고 현재 런처는 macOS/Windows x64용 | 현재 ZIP 그대로의 업로드·편집 지원으로 안내하지 않음 |
| Claude Cowork | 로컬 사용자 스킬 경로와 계정에 활성화한 스킬의 로딩 방식이 다름 | 계정 스킬 포장·실행 환경·파일 및 이미지 도구 검증 필요. 실기 미검증 |
| 네이버 블로그 기능 | 프로젝트·사용자 범위 파일 설치, 동일 재실행, 개인 지침 보존 성공 | 실제 브라우저 작성·파일 첨부·임시저장·재열람은 미검증 |

## 직접 실행한 검사

기존 Python·uv·Homebrew를 PATH에 노출하지 않고 공개 설치 ZIP에서 시작했습니다. 새 프로젝트의 빈 `.daily-vlog-runtime/v1`에 uv와 전용 Python·Pillow·PyAV·FFmpeg를 내려받았습니다. 설치에는 약 30초가 걸렸지만 다른 컴퓨터에서의 소요 시간을 보장하는 수치는 아닙니다.

프로젝트 설치, 별도 실행에서 오프라인 doctor, 동일 설치 재실행, 격리 사용자 범위 설치, 블로그의 프로젝트·사용자 설치와 재실행, Claude Code 폴더 구조의 편집 엔진 실행, 입력 검사, 전체 렌더, 미지원 Linux 분기까지 12개 단계가 예상 결과를 반환했습니다. 사용자 범위 설치와 Claude Code 폴더 검사에서는 앞서 준비한 격리 런타임을 명시적으로 재사용했습니다. Claude Code 경로 검사는 Claude를 실행한 것이 아니라 같은 코드가 해당 폴더에서도 작동하는지 확인한 것입니다.

최종 MP4는 무음 H.264, 1080×1920, 24fps, 10초·240프레임으로 전체 디코드를 확인했습니다. Noto Sans KR의 한글 자막과 시간 표시를 포스터로 직접 열람했습니다. 테스트에는 생성한 단색 영상만 사용했으며 사용자 원본·개인 프로필·네이버 계정은 사용하지 않았습니다. 원본 해시와 공용 렌더 잠금 파일 내용도 유지됐습니다.

Windows 검사는 실제 설치 스크립트의 가드를 PowerShell 7.6.7에서 실행한 것입니다. 샌드박스 계정 설치 거부, 해당 계정 소유 폴더 거부, 일반 계정 대조군, 공백·한글 경로, 파일/링크 경로 거부와 실행기 도움말을 확인했습니다. 실제 Windows ACL 변경 권한, 보호 권한 갱신 또는 Windows PowerShell 5.1의 동작을 증명하는 시험은 아닙니다.

## 남은 호환성 조건

Claude Code의 표준 경로는 `.claude/skills`입니다. 현재 설치기는 Codex 경로를 사용하고 개인 지침도 기본적으로 CODEX_HOME 아래를 읽습니다. 클라이언트별 설치·설정 경로 분기 없이 Claude 자동 설치를 지원한다고 안내하면 안 됩니다. 이 점검에서 실행 가능한 Claude 앱·CLI를 찾지 못했으므로 Claude의 스킬 선택과 실제 도구 호출은 확인하지 않았습니다.

일반 Claude의 업로드용 스킬은 공식 문서의 스킬 폴더 중심 ZIP으로 따로 포장해야 합니다. 현재 두 ZIP은 Codex 설치기 포함 배포물이며 업로드 전용 포장이 아닙니다. 실행 환경이 Linux인 경우 현재 런처는 지원하지 않는다고 중단합니다. Linux 분기를 테스트한 것은 해당 OS를 실제로 구동한 시험이 아니라, 런처의 거부 동작을 모의한 검사입니다. Cowork나 일반 Claude의 실제 환경을 확인하기 전에 동일 동작을 보장하지 않습니다.

Windows에서 `.agents` 보호 권한을 설정하다 거부된 기존 문제는 설치 재실행만으로 복구하지 않습니다. 설치기의 계정·소유자 점검은 예방 로직이며 실제 권한 갱신 성공과 다릅니다. 문제 폴더의 소유자·ACL·해당 시점 로그를 확인해야 하며 기존 ACL, 보안 정책과 프로젝트 전체 권한은 자동 변경하지 않습니다.

## 공식 근거

- [Codex의 로컬 스킬 검색 위치](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills)
- [Codex의 Windows 샌드박스와 권한 문제 해결](https://learn.chatgpt.com/docs/windows/windows-sandbox#troubleshooting-and-faq)
- [Claude Code의 스킬 설치 위치와 Cowork 로딩 차이](https://code.claude.com/docs/en/skills)
- [Claude 업로드용 스킬 포장](https://support.claude.com/en/articles/12512198-how-to-create-custom-skills)
- [Claude 제품별 실행 환경과 의존성 차이](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
