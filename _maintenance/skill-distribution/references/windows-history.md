# Windows에서 발생한 실패와 재발 검사

2026-10-22~23 daily-vlog 배포 중 사용자 Windows Codex 실기에서 확인했다. 이 이력을 모든 PC의 동일 원인으로 단정하지 않는다.

## 1. 설치기 자신의 선제 차단

공개 v015는 실행 계정이 CodexSandboxOnline/Offline이거나 기존 .agents/.claude 소유자가 CodexSandbox로 시작하면 실제 쓰기 전에 HOST_INSTALL_REQUIRED/PROJECT_OWNER_MISMATCH로 거부했다. 사용자가 CMD를 직접 열면 일반 계정이어서 통과했다. 이것은 실제 쓰기 권한 부족을 입증한 시험이 아니었다.

v016은 두 이름 검사를 제거했다. 허용된 폴더의 디렉터리 생성·파일 쓰기·설치 잠금 결과로 판정한다. 사용자가 별도 CMD를 열도록 요구하거나 샌드박스 계정이라는 이유만으로 중단하는 코드를 다시 추가하지 않는다. 기존 .agents를 삭제하거나 ACL·소유권을 바꾸는 방식으로 해결하지 않는다.

이후 사용자 보고에서 v016을 이용한 재시험이 한 번에 설치된 것으로 전달됐다. 이 보고는 해당 Windows Codex 설치 결과이며 다른 클라이언트·다른 계정·새 채팅·전체 영상 편집 성공을 의미하지 않는다.

## 2. 캐시가 숨겼던 HTTPS 실패

계정 차단 제거 후 빈 런타임에서 Windows HTTPS가 SEC_E_NO_CREDENTIALS (0x8009030E)로 실패했다. 기존 도구 캐시만 재사용한 시험에서는 드러나지 않았다. 첫 설치는 반드시 빈 캐시에서 별도로 시험한다.

Windows 런처는 Invoke-WebRequest를 먼저 사용한다. 실패 시 PATH의 실제 기존 python.exe를 선택적으로 쓰며 WindowsApps 스토어 바로가기는 제외한다. `assets/windows-https.ps1`은 기존 Python을 -I로 실행하고 ssl.create_default_context()로 인증서·호스트명을 검증하며 최종 URL이 HTTPS인지 확인하는 검증된 함수다. 받은 파일의 고정 SHA256도 맞아야 실행한다. 다운로드용 기존 Python과 편집용 새 전용 Python을 구분한다.

기본 HTTPS가 정상인 경우 기존 Python이 필요 없다. 기본 HTTPS도 실패하고 기존 Python도 없는 환경은 현재 해결되지 않았다. 인증서 검증 해제·해시 재설정·시스템 정책 변경으로 우회하지 않는다. 이 한계를 README와 시작 안내에서 숨기지 않는다. 함수만 복사했다고 새 런타임의 다운로드·휠·코덱이 지원된다고 주장하지 않는다.

회귀 검사: 정상 기본 HTTPS에서 Python 미탐색, 실패 시 Python 없음, WindowsApps 제외, 실제 Python 대체 다운로드, 인증서 실패·HTTP 리디렉션 거부, 변조 해시 실행 전 거부. 소스와 최종 ZIP을 구분해 시험한다.

## 3. 앱 준비·이미지·세션 문제의 구분

setup refresh had errors 또는 Failed to create unified exec process로 명령 자체가 시작되지 않으면 앱 준비 단계다. 설치기 선제 차단·Python·실제 영상 디코드·에이전트 이미지 열람과 혼동하지 않는다. 문구 하나로 ACL이나 파일 잠금 원인을 확정하지 않는다. 읽기 허용된 setup_error.json과 해당 시점 로그의 실패 경로/OS 오류만 확인하고 인증·전체 개인 로그를 배포하지 않는다.

파일 복사 → doctor → 테스트 영상 인코딩·디코딩·프레임 추출 → 이미지 직접 열람 → 후속 명령을 각각 기록한다. 자동 agent_image_view: not_checked를 덮어쓰지 않는다. 새 채팅의 스킬 인식과 다른 계정의 파일 접근은 별도 검사다. 목록이 갱신되지 않을 때만 새 채팅을 안내하며 무조건 재설치를 반복하지 않는다.

## 4. 검사 프로그램의 Windows 환경변수

첫 네이티브 Windows CI에서 검사 프로그램이 dict(os.environ)의 SystemRoot 키를 찾지 못해 설치기 실행 전에 실패했다. Windows os.environ은 대소문자를 구분하지 않지만 일반 dict는 구분한다. 실제 키를 대소문자 없이 찾아 제한된 PATH를 구성하고 그 함수를 회귀 검사한다. 이 실패를 제품 설치·권한 실패로 보고하지 않는다. Windows/Unix의 경로 정렬 차이도 패키지 지문에 들어가지 않도록 POSIX 문자열 순서로 해시한다. 실패한 CI는 구조화된 오류 아티팩트도 남긴다.
