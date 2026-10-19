$ErrorActionPreference = 'Stop'
if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) { throw '이 설치기는 Windows용입니다.' }
$NativeArch = $env:PROCESSOR_ARCHITEW6432
if (-not $NativeArch) { $NativeArch = $env:PROCESSOR_ARCHITECTURE }
if ($NativeArch -ne 'AMD64') { throw '현재 Windows x64만 지원합니다.' }
$Source = Join-Path $PSScriptRoot 'daily-vlog'
if (-not (Test-Path -LiteralPath (Join-Path $Source 'SKILL.md'))) { throw 'ZIP을 완전히 압축 해제한 뒤 다시 실행하세요.' }
$Base = $env:CODEX_HOME
if (-not $Base) { $Base = Join-Path $env:USERPROFILE '.codex' }
$Skills = Join-Path $Base 'skills'
$Target = Join-Path $Skills 'daily-vlog'
[IO.Directory]::CreateDirectory($Skills) | Out-Null
if (Test-Path -LiteralPath $Target) {
    # Retry after an interrupted setup only if this exact skill is already copied.
    foreach ($File in (Get-ChildItem -LiteralPath $Source -File -Recurse)) {
        $Relative = $File.FullName.Substring($Source.Length + 1)
        $Existing = Join-Path $Target $Relative
        if (-not (Test-Path -LiteralPath $Existing) -or (Get-FileHash -LiteralPath $Existing).Hash -ne (Get-FileHash -LiteralPath $File.FullName).Hash) {
            throw '다른 버전 또는 수정된 스킬이 있습니다. 덮어쓰지 않았습니다. 에이전트에게 갱신을 요청하세요.'
        }
    }
    Write-Host '같은 스킬이 있습니다. 중단된 도구 준비를 이어갑니다.'
}
else {
    # Stage first; a failed copy cannot leave a half-copied installed skill.
    $Stage = Join-Path $Skills ('daily-vlog-install-' + [Guid]::NewGuid().ToString('N'))
    try {
        [IO.Directory]::CreateDirectory($Stage) | Out-Null
        foreach ($Entry in (Get-ChildItem -LiteralPath $Source -Force)) { Copy-Item -LiteralPath $Entry.FullName -Destination $Stage -Recurse -Force }
        [IO.Directory]::Move($Stage, $Target)
    }
    finally { if (Test-Path -LiteralPath $Stage) { Remove-Item -LiteralPath $Stage -Recurse -Force } }
}
Write-Host '스킬을 추가했습니다. 전용 편집 도구를 준비합니다.'
& (Join-Path $Target 'scripts\run.ps1') doctor
Write-Host '준비됐습니다. 새 Codex 채팅에서 영상을 첨부하고 콘티부터 요청하세요.'
