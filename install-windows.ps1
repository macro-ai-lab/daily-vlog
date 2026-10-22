param([ValidateSet('auto','codex','claude-code')][string]$Client = 'auto', [string]$ProjectPath, [switch]$UserScope)
$ErrorActionPreference = 'Stop'
$Name = 'daily-vlog'
if ($Client -eq 'auto') { $Client = $env:AI_SKILL_CLIENT }
switch ($Client) {
    'codex' { $ClientDir = '.agents'; $ConfigBase = $env:CODEX_HOME; if (-not $ConfigBase) { $ConfigBase = Join-Path $env:USERPROFILE '.codex' } }
    'claude-code' { $ClientDir = '.claude'; $ConfigBase = $env:CLAUDE_CONFIG_DIR; if (-not $ConfigBase) { $ConfigBase = Join-Path $env:USERPROFILE '.claude' } }
    default { throw '[CLIENT_REQUIRED] 현재 에이전트가 -Client codex 또는 -Client claude-code를 지정해야 합니다. 설치 파일은 만들지 않았습니다.' }
}
$Client = $Client.ToLowerInvariant()
if (-not [IO.Path]::IsPathRooted($ConfigBase)) { throw '클라이언트 설정 폴더는 절대경로여야 합니다.' }
if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) { throw 'README의 환경 분기를 따라 이 환경에 맞는 설치기를 사용하세요.' }
if ($ProjectPath -and $UserScope) { throw '설치 범위는 하나만 선택하세요.' }
# Account and owner names do not establish filesystem access. Let the actual
# directory creation, exclusive lock and staged copy report permission failures.
if ($Name -eq 'daily-vlog') {
    $NativeArch = $env:PROCESSOR_ARCHITEW6432
    if (-not $NativeArch) { $NativeArch = $env:PROCESSOR_ARCHITECTURE }
    if ($NativeArch -ne 'AMD64') { throw '현재 편집 런타임은 Windows x64만 지원합니다.' }
}
$Source = Join-Path $PSScriptRoot $Name
if (-not (Test-Path -LiteralPath (Join-Path $Source 'SKILL.md') -PathType Leaf)) { throw '스킬 파일이 없습니다. 압축을 완전히 해제하세요.' }
function Assert-RealDirectory([string]$Path) {
    if (Test-Path -LiteralPath $Path) {
        $Item = Get-Item -LiteralPath $Path -Force
        if (-not $Item.PSIsContainer -or ($Item.Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw "설치 경로가 폴더가 아니거나 링크입니다: $Path" }
    }
}
if ($ProjectPath) {
    $Scope = 'project'
    $ProjectPath = (Resolve-Path -LiteralPath $ProjectPath).ProviderPath
    Assert-RealDirectory $ProjectPath
    $ClientRoot = Join-Path $ProjectPath $ClientDir
    Assert-RealDirectory $ClientRoot
    $Skills = Join-Path $ClientRoot 'skills'
}
else { $Scope = 'user'; Assert-RealDirectory $ConfigBase; $Skills = Join-Path $ConfigBase 'skills' }
Assert-RealDirectory $Skills
try { [IO.Directory]::CreateDirectory($Skills) | Out-Null }
catch { throw "[INSTALL_PATH_DENIED] 설치 위치에 쓸 수 없습니다: $Skills. $($_.Exception.Message)" }
$Target = Join-Path $Skills $Name
$Marker = Join-Path $Skills ('.' + $Name + '-install')
$Stage = $null; $LockStream = $null; $MarkerTemp = $null
try {
    try { $LockStream = [IO.File]::Open((Join-Path $Skills ('.' + $Name + '-install.lock')), [IO.FileMode]::OpenOrCreate, [IO.FileAccess]::ReadWrite, [IO.FileShare]::None) }
    catch { throw '[INSTALL_LOCK_OR_PERMISSION] 다른 설치 또는 쓰기 권한을 확인하세요. 기존 잠금은 삭제하지 않았습니다.' }
    $ExpectedMarker = "skill-install-v1`n$Client`n$Scope`n"
    if (Test-Path -LiteralPath $Marker) {
        $Item = Get-Item -LiteralPath $Marker -Force
        if ($Item.PSIsContainer -or ($Item.Attributes -band [IO.FileAttributes]::ReparsePoint) -or [IO.File]::ReadAllText($Marker).Replace("`r`n", "`n") -ne $ExpectedMarker) { throw '[INSTALL_CONTEXT_CONFLICT] 기존 설치 기록이 다르거나 링크입니다. 기록은 보존했습니다.' }
    }
    if (Test-Path -LiteralPath $Target) {
        Assert-RealDirectory $Target
        $Files = @(Get-ChildItem -LiteralPath $Source -File -Recurse -Force)
        $ExistingFiles = @(Get-ChildItem -LiteralPath $Target -File -Recurse -Force)
        if ($Files.Count -ne $ExistingFiles.Count) { throw '[EXISTING_SKILL_DIFFERS] 다른 버전 또는 수정본이 있어 덮어쓰지 않았습니다.' }
        foreach ($File in $Files) {
            $Relative = $File.FullName.Substring($Source.Length + 1)
            $Existing = Join-Path $Target $Relative
            if (-not (Test-Path -LiteralPath $Existing -PathType Leaf) -or (Get-FileHash -LiteralPath $Existing).Hash -ne (Get-FileHash -LiteralPath $File.FullName).Hash) { throw '[EXISTING_SKILL_DIFFERS] 다른 버전 또는 수정본이 있어 덮어쓰지 않았습니다.' }
        }
        Write-Host '같은 스킬이 있습니다. 남은 점검을 이어갑니다.'
    }
    else {
        $Stage = Join-Path $Skills ('.' + $Name + '-install-' + [Guid]::NewGuid().ToString('N'))
        [IO.Directory]::CreateDirectory($Stage) | Out-Null
        foreach ($Entry in (Get-ChildItem -LiteralPath $Source -Force)) { Copy-Item -LiteralPath $Entry.FullName -Destination $Stage -Recurse -Force }
        [IO.Directory]::Move($Stage, $Target); $Stage = $null
    }
    if (-not (Test-Path -LiteralPath $Marker)) {
        $MarkerTemp = Join-Path $Skills ('.' + $Name + '-context-' + [Guid]::NewGuid().ToString('N'))
        [IO.File]::WriteAllText($MarkerTemp, $ExpectedMarker, (New-Object System.Text.UTF8Encoding($false)))
        [IO.File]::Move($MarkerTemp, $Marker); $MarkerTemp = $null
    }
    $env:AI_SKILL_CLIENT = $Client
    Write-Host "스킬 파일 확인 완료: $Target"
    Write-Host "설치 클라이언트: $Client / 범위: $Scope"
    if ($Name -eq 'daily-vlog') {
        if ($ProjectPath -and -not $env:DAILY_VLOG_RUNTIME) { $env:DAILY_VLOG_RUNTIME = Join-Path $ProjectPath '.daily-vlog-runtime\v1' }
        try { & (Join-Path $Target 'scripts\run.ps1') doctor }
        catch { throw "[RUNTIME_CHECK_FAILED] 스킬 파일은 복사됐지만 편집 도구 점검이 실패했습니다. $($_.Exception.Message)" }
        $CheckRoot = Join-Path $env:DAILY_VLOG_RUNTIME 'checks'
        try { & (Join-Path $Target 'scripts\run.ps1') smoke --output-dir (Join-Path $CheckRoot ('check-' + [Guid]::NewGuid().ToString('N'))) }
        catch { throw "[VIDEO_CHECK_FAILED] 테스트 영상 생성·읽기 점검이 실패했습니다. $($_.Exception.Message)" }
        Write-Host '편집 도구와 테스트 영상 읽기 점검 완료. 에이전트의 이미지 열람 가능 여부는 별도로 확인하세요.'
    }
    else { Write-Host "개인 지침 위치: $(Join-Path $ConfigBase 'naver-blog-draft\preferences.md')"; Write-Host '스킬 파일 설치 완료. 컴퓨터 유즈·파일 첨부·로그인은 현재 채팅에서 별도로 확인하세요.' }
    if ($ProjectPath) { Write-Host "사용 범위: 이 프로젝트($ProjectPath). 런타임과 개인 자료는 Git에 올리지 마세요." }
    Write-Host '현재 채팅에서 스킬 인식을 먼저 확인하세요. 목록에 없을 때만 같은 프로젝트의 새 채팅을 여세요.'
}
finally {
    if ($Stage -and (Test-Path -LiteralPath $Stage)) { Remove-Item -LiteralPath $Stage -Recurse -Force }
    if ($MarkerTemp -and (Test-Path -LiteralPath $MarkerTemp)) { Remove-Item -LiteralPath $MarkerTemp -Force }
    if ($LockStream) { $LockStream.Dispose() }
}
