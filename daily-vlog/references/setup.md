# 환경 준비와 지원 범위

macOS 14 이상 및 Windows 10/11 x64용 시험판. 실제 Windows 장치에서 첫 설치·렌더는 아직 검증하지 않았다. Windows ARM/32비트와 Linux는 미지원이다. 사용자에게 터미널 명령을 직접 입력시키지 않고 에이전트가 Mac에서는 `scripts/run.sh`, Windows에서는 `scripts\run.cmd`를 실행한다. 기본 런타임 위치는 macOS `~/Library/Caches/daily-vlog/v1`, Windows `%LOCALAPPDATA%\daily-vlog\v1`이다. `DAILY_VLOG_RUNTIME`으로 쓰기 가능한 전용 위치를 지정할 수 있다. 자료/스킬과 런타임은 별개이므로 스킬 ZIP에 캐시를 담지 않는다.

## 자동 설치

1. OS/CPU를 확인한다. uv 0.13.1 공식 GitHub 배포를 다운로드하고 고정된 공개 SHA256과 비교한다. Windows는 x64만 받는다.
2. uv가 전용 CPython 3.12를 다운로드하고 독립 가상환경을 만든다. 기존 시스템 Python은 사용하지 않는다.
3. uv.lock의 PyPI wheel 해시·버전으로 Pillow/PyAV/imageio-ffmpeg를 설치한다. 소스 빌드는 막는다. FFmpeg 실행 파일은 imageio-ffmpeg wheel에서, 미디어 정보는 PyAV의 포함 FFmpeg 라이브러리에서 얻는다. 별도 ffprobe 설치가 필요 없다.
4. 한글 폰트(macOS Apple SD Gothic Neo, Windows 맑은 고딕)와 H.264/AAC 인코더를 점검한다. 설치 성공 후 의존성 구성 지문을 저장한다. 같은 구성의 재사용에서는 설치/동기화/쓰기 잠금 없이 바로 실행하고, `setup`을 명시하거나 구성 지문이 달라질 때만 다시 준비한다.

`doctor`는 준비 상태, `inspect`는 폴더의 입력 지원 여부를 JSON으로 출력한다. 새 환경 시험은 같은 Mac의 빈 캐시에서 시스템 Python/Homebrew 없이 진행하는 시험이며 새 기기/OS 설치 검증과 같다고 표현하지 않는다.

## 실패 처리

- 네트워크 실패: 설치가 완료됐다고 하지 않는다. 연결/승인 상태를 알려주고 재실행한다. TLS 검증을 끄지 않는다.
- 다운로드 해시 불일치: 즉시 중단한다. 예상 해시를 임의로 바꾸지 않는다.
- 설치 잠금: 동시에 실행하지 않는다. 중단된 이전 설치 프로세스가 정말 없는지 확인한 뒤 해당 전용 캐시의 비어 있는 setup.lock 디렉터리만 정리할 수 있다. 다른 렌더 락은 건드리지 않는다.
- 지원하지 않는 파일: 원음·HDR/HEVC 등을 조용히 제거/변환하지 않는다. 실제 사용한 파일만 성공으로 보고한다.
- OS 권한·다운로드 보안 경고: 앱/OS가 요구하는 승인 경계를 설명한다. Gatekeeper를 끄거나 quarantine을 일괄 삭제하지 않는다.

## 비용과 데이터

도구 의존성 설치에 별도 유료 API 키는 필요 없다. 에이전트 앱/계정과 서비스 이용 요금은 별개다. 패키지 다운로드는 인터넷 연결이 필요하며 렌더는 로컬에서 수행한다. 에이전트의 프레임 분석까지 완전 오프라인이라고 주장하지 않는다. 원본/스톡/음원과 시스템 폰트는 번들에 재배포하지 않는다. 타임로그용 Pretendard SemiBold는 SIL OFL 1.1 라이선스·저작권 고지와 함께 번들에 포함한다. 이 폰트는 시스템에 설치하지 않고 파일 경로로 사용한다.

## 근거

- uv 설치/관리 Python: https://docs.astral.sh/uv/getting-started/installation/ 및 https://docs.astral.sh/uv/guides/install-python/
- uv 고정 해시: https://github.com/astral-sh/uv/releases/tag/0.13.1
- FFmpeg 포함 wheel: https://github.com/imageio/imageio-ffmpeg
- PyAV wheel: https://pyav.org/docs/stable/overview/installation.html
- 스킬 형식: https://developers.openai.com/codex/skills/

## Windows 설치와 재시도

ZIP을 완전히 푼 뒤 `install-windows.cmd`를 실행하거나 Codex에게 설치를 요청한다. 스킬은 `%USERPROFILE%\.codex\skills\daily-vlog`에 추가한다(CODEX_HOME 설정 시 그 경로 기준). Python은 사전 설치할 필요가 없다. PowerShell 5.1 이상·인터넷·사용자 폴더 쓰기 권한과 설치된 맑은 고딕이 필요하다. 관리자·Homebrew·Visual Studio 빌드 도구를 설치하지 않으며 소스 빌드는 막는다.

`.cmd`는 이 프로세스에서만 PowerShell 스크립트 실행을 허용한다. 전역 Set-ExecutionPolicy나 Defender/SmartScreen/조직 정책 변경은 하지 않는다. 차단되면 자동 우회하지 말고 사용자에게 알린다.

중간에 도구 다운로드가 실패하면 같은 `install-windows.cmd`를 다시 실행할 수 있다. 복사된 스킬이 배포본과 정확히 같은 경우만 준비를 재개하고, 수정본/다른 버전은 덮어쓰지 않는다. 설치 잠금은 프로세스가 끝나면 OS가 해제하며 파일 내용/다른 작업을 건드리지 않는다. 준비 완료 시 이후 doctor/inspect/render는 설치 쓰기 없이 기존 환경을 재사용한다.

Windows 렌더 잠금은 LockFileEx로 기존 파일을 rb로 열어 즉시 독점 획득한다. 맥은 기존 flock 방식을 유지한다. 같은 Windows 컴퓨터에서 돌아가는 다른 렌더러도 같은 파일과 잠금 방식을 사용해야 한다. Mac의 로컬 잠금 파일을 별도 Windows PC와 공유한다고 가정하지 않는다.

Windows 폰트는 단일 TTF이므로 예제의 macOS TTC font_index=4를 0으로 정규화한다. 맑은 고딕 파일이 없으면 자동 폰트 다운로드 대신 필요한 파일 위치를 알려 달라고 한다. 시스템 폰트는 재배포하지 않는다.

API 근거: https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-lockfileex
