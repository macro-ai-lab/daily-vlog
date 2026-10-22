# Windows x64; private runtime only, no administrator or persistent PATH changes.
$ErrorActionPreference = 'Stop'
$VlogArguments = @($args)
if ($VlogArguments.Count -eq 0 -or $VlogArguments[0] -eq '--help') {
    Write-Output 'daily-vlog: setup | doctor | smoke --output-dir DIR | inspect FOLDER | inspect --files FILE... | frames FILE --output-dir DIR | survey FILE --output-dir DIR [--start SEC --end SEC --interval SEC --max-frames N] | overrides show/propose/save | customize PLAN --root DIR --patch PATCH --output NEW_PLAN | font --name NAME --output-dir DIR | render PLAN --root DIR --output FILE --poster FILE'
    return
}
if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) { throw '이 실행기는 Windows용입니다.' }
$NativeArch = $env:PROCESSOR_ARCHITEW6432
if (-not $NativeArch) { $NativeArch = $env:PROCESSOR_ARCHITECTURE }
if ($NativeArch -ne 'AMD64') { throw '현재 Windows x64만 지원합니다. ARM/32비트는 지원하지 않습니다.' }
$SkillDir = Split-Path $PSScriptRoot -Parent
$RuntimeDir = $env:DAILY_VLOG_RUNTIME
if (-not $RuntimeDir) {
    $ProjectRoot = Split-Path (Split-Path (Split-Path $SkillDir -Parent) -Parent) -Parent
    $ProjectSkill = Join-Path $ProjectRoot '.agents\skills\daily-vlog'
    if ([IO.Path]::GetFullPath($SkillDir) -eq [IO.Path]::GetFullPath($ProjectSkill)) {
        $RuntimeDir = Join-Path $ProjectRoot '.daily-vlog-runtime\v1'
    }
    else {
        if (-not $env:LOCALAPPDATA) { throw '사용자 LocalAppData 폴더를 찾지 못했습니다.' }
        $RuntimeDir = Join-Path $env:LOCALAPPDATA 'daily-vlog\v1'
    }
}
$env:DAILY_VLOG_RUNTIME = $RuntimeDir
$env:UV_CACHE_DIR = Join-Path $RuntimeDir 'uv-cache'
$env:UV_PYTHON_INSTALL_DIR = Join-Path $RuntimeDir 'python'
$env:UV_PROJECT_ENVIRONMENT = Join-Path $RuntimeDir 'venv'
$env:UV_NO_PROGRESS = '1'
$env:UV_NO_CONFIG = '1'
$env:UV_PYTHON_DOWNLOADS = 'automatic'
$env:UV_DEFAULT_INDEX = 'https://pypi.org/simple'
$env:UV_PYTHON_INSTALL_BIN = '0'
$env:UV_PYTHON_INSTALL_REGISTRY = '0'
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTHONUTF8 = '1'
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
$PythonExe = Join-Path $RuntimeDir 'venv\Scripts\python.exe'
$UvExe = Join-Path $RuntimeDir 'bin\uv.exe'
$ReadyFile = Join-Path $RuntimeDir 'ready.sha256'
# Hash concatenated bytes, same algorithm as the macOS launcher; no path dependence.
[byte[]]$Bytes = [IO.File]::ReadAllBytes((Join-Path $SkillDir 'runtime\pyproject.toml')) + [IO.File]::ReadAllBytes((Join-Path $SkillDir 'runtime\uv.lock'))
$Hasher = [Security.Cryptography.SHA256]::Create()
try { $Fingerprint = ([BitConverter]::ToString($Hasher.ComputeHash($Bytes))).Replace('-', '').ToLowerInvariant() }
finally { $Hasher.Dispose() }
$Ready = (Test-Path -LiteralPath $PythonExe) -and (Test-Path -LiteralPath $ReadyFile)
if ($Ready) { $Ready = ([IO.File]::ReadAllText($ReadyFile).Trim() -eq $Fingerprint) }
if ($VlogArguments[0] -eq 'setup' -or -not $Ready) {
    [IO.Directory]::CreateDirectory($RuntimeDir) | Out-Null
    $SetupHandle = $null
    $DownloadDir = $null
    try {
        try { $SetupHandle = [IO.File]::Open((Join-Path $RuntimeDir 'setup.lock'), [IO.FileMode]::OpenOrCreate, [IO.FileAccess]::ReadWrite, [IO.FileShare]::None) }
        catch { throw '설치 잠금을 얻지 못했습니다. 다른 설치가 실행 중이거나 폴더 쓰기 권한이 없습니다. 기존 작업을 중단하지 마세요.' }
        if (-not (Test-Path -LiteralPath $UvExe)) {
            Write-Host '1/3 편집 도구 관리자를 준비합니다. 첫 실행에는 인터넷이 필요합니다.'
            $DownloadDir = Join-Path $RuntimeDir ('download-' + [Guid]::NewGuid().ToString('N'))
            [IO.Directory]::CreateDirectory($DownloadDir) | Out-Null
            $Archive = Join-Path $DownloadDir 'uv.zip'
            [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
            Invoke-WebRequest -UseBasicParsing -Uri 'https://github.com/astral-sh/uv/releases/download/0.13.1/uv-x86_64-pc-windows-msvc.zip' -OutFile $Archive -TimeoutSec 180
            $Expected = '3b2661a463a5baea7f5076ea2b25ab71d77f36a6c0d809e5350651792f80a672'
            if ((Get-FileHash -LiteralPath $Archive -Algorithm SHA256).Hash.ToLowerInvariant() -ne $Expected) { throw '설치 파일 해시가 다릅니다. 실행하지 않고 중단합니다.' }
            Expand-Archive -LiteralPath $Archive -DestinationPath (Join-Path $DownloadDir 'expanded')
            $Candidates = @(Get-ChildItem -LiteralPath (Join-Path $DownloadDir 'expanded') -Filter 'uv.exe' -File -Recurse)
            if ($Candidates.Count -ne 1) { throw 'uv 실행 파일을 하나로 확인하지 못했습니다.' }
            [IO.Directory]::CreateDirectory((Join-Path $RuntimeDir 'bin')) | Out-Null
            [IO.File]::Move($Candidates[0].FullName, $UvExe)
        }
        $Version = & $UvExe --version
        if ($LASTEXITCODE -ne 0 -or $Version -notlike 'uv 0.13.1*') { throw '전용 uv 버전이 예상과 다릅니다.' }
        Write-Host '2/3 전용 Python과 편집 모듈을 준비합니다.'
        & $UvExe sync --project (Join-Path $SkillDir 'runtime') --locked --no-dev --no-editable --python 3.12 --managed-python --no-build
        if ($LASTEXITCODE -ne 0) { throw 'Python/모듈 준비가 실패했습니다. 연결과 설치 권한을 확인한 뒤 다시 요청하세요.' }
        & $PythonExe (Join-Path $PSScriptRoot 'vlog.py') doctor | Out-Null
        if ($LASTEXITCODE -ne 0) { throw '편집 도구 점검이 실패했습니다. 에이전트에게 오류를 알려주세요.' }
        $RenderLock = Join-Path $RuntimeDir 'render.lock'
        if (-not (Test-Path -LiteralPath $RenderLock)) { [IO.File]::WriteAllBytes($RenderLock, [byte[]]@()) }
        [IO.File]::WriteAllText($ReadyFile, $Fingerprint, (New-Object System.Text.UTF8Encoding($false)))
    }
    finally {
        if ($SetupHandle) { $SetupHandle.Dispose() }
        if ($DownloadDir -and (Test-Path -LiteralPath $DownloadDir)) { Remove-Item -LiteralPath $DownloadDir -Recurse -Force }
    }
}
if ($VlogArguments[0] -eq 'setup') { $VlogArguments = @('doctor') }
& $PythonExe (Join-Path $PSScriptRoot 'vlog.py') @VlogArguments
if ($LASTEXITCODE -ne 0) { throw ('브이로그 작업 실패 (종료 코드 ' + $LASTEXITCODE + '). 위 오류를 확인하세요.') }
