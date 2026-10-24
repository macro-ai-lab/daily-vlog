# Dependency-free regression checks. On non-Windows hosts only the platform
# guard is omitted in a temporary fixture; Windows ACL semantics are not tested.
param([string]$PythonExecutable, [switch]$NetworkDownload)
$ErrorActionPreference = 'Stop'
$Repo = Split-Path $PSScriptRoot -Parent
$Checks = @()
function Check([string]$Name, [bool]$Condition) {
    if (-not $Condition) { throw "CHECK FAILED: $Name" }
    $script:Checks += $Name
}
function Expect-Error([string]$Name, [scriptblock]$Action, [string]$Pattern) {
    $Message = $null
    try { & $Action | Out-Null } catch { $Message = $_.Exception.Message }
    Check $Name ($Message -and $Message -match $Pattern)
}
function Parse-Script([string]$Path) {
    $Tokens = $null; $Errors = $null
    $Result = [Management.Automation.Language.Parser]::ParseFile($Path, [ref]$Tokens, [ref]$Errors)
    if ($Errors.Count) { throw ($Errors | Out-String) }
    return $Result
}
$InstallerPath = Join-Path $Repo 'install-windows.ps1'
$LauncherPath = Join-Path $Repo 'reels-maker/scripts/run.ps1'
$InstallerAst = Parse-Script $InstallerPath
$LauncherAst = Parse-Script $LauncherPath
Check 'PowerShell scripts parse' $true
$Work = Join-Path ([IO.Path]::GetTempPath()) ('daily-vlog-install-check-' + [guid]::NewGuid().ToString('N'))
[IO.Directory]::CreateDirectory($Work) | Out-Null
try {
    $Bundle = Join-Path $Work 'bundle'; [IO.Directory]::CreateDirectory($Bundle) | Out-Null
    $Text = [IO.File]::ReadAllText($InstallerPath)
    if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
        $Guard = $InstallerAst.FindAll({param($n) $n -is [Management.Automation.Language.IfStatementAst] -and $n.Clauses[0].Item1.Extent.Text.Contains('[Environment]::OSVersion.Platform')}, $true)[0]
        $Text = $Text.Remove($Guard.Extent.StartOffset, $Guard.Extent.EndOffset - $Guard.Extent.StartOffset)
    }
    $FixtureInstaller = Join-Path $Bundle 'install-windows.ps1'
    [IO.File]::WriteAllText($FixtureInstaller, $Text, (New-Object Text.UTF8Encoding($true)))
    $Skill = Join-Path $Bundle 'reels-maker'
    [IO.Directory]::CreateDirectory((Join-Path $Skill 'scripts')) | Out-Null
    [IO.File]::WriteAllText((Join-Path $Skill 'SKILL.md'), 'fixture')
    [IO.File]::WriteAllText((Join-Path $Skill 'scripts/run.ps1'), '[IO.File]::AppendAllText($env:INSTALL_TEST_LOG, ($args[0] + "`n"))')
    $env:INSTALL_TEST_LOG = Join-Path $Work 'calls.txt'
    $env:CODEX_HOME = Join-Path $Work 'Codex config'
    $env:CLAUDE_CONFIG_DIR = Join-Path $Work 'Claude config'
    $env:PROCESSOR_ARCHITECTURE = 'AMD64'; $env:PROCESSOR_ARCHITEW6432 = ''
    $env:DAILY_VLOG_RUNTIME = Join-Path $Work 'runtime'
    $Profile = Join-Path $env:CODEX_HOME 'daily-vlog/user-overrides.json'
    [IO.Directory]::CreateDirectory((Split-Path $Profile -Parent)) | Out-Null
    [IO.File]::WriteAllText($Profile, 'private fixture profile')
    $Before = (Get-FileHash -LiteralPath $Profile).Hash
    foreach ($Client in @('codex', 'claude-code')) {
        $Project = Join-Path $Work ($Client + ' project'); [IO.Directory]::CreateDirectory($Project) | Out-Null
        & $FixtureInstaller -Client $Client -ProjectPath $Project
        $Skills = Join-Path (Join-Path $Project $(if ($Client -eq 'codex') {'.agents'} else {'.claude'})) 'skills'
        $Target = Join-Path $Skills 'reels-maker'
        Check "$Client new project" (Test-Path -LiteralPath (Join-Path $Target 'SKILL.md'))
        & $FixtureInstaller -Client $Client -ProjectPath $Project
        Check "$Client identical retry" $true
        $Marker = Join-Path $Skills '.reels-maker-install'
        $MarkerBefore = [IO.File]::ReadAllText($Marker)
        [IO.File]::WriteAllText($Marker, "skill-install-v1`nother-client`nproject`n")
        Expect-Error "$Client conflicting marker preserved" { & $FixtureInstaller -Client $Client -ProjectPath $Project } 'INSTALL_CONTEXT_CONFLICT'
        Check "$Client conflicting marker unchanged" ([IO.File]::ReadAllText($Marker).Contains('other-client'))
        [IO.File]::WriteAllText($Marker, $MarkerBefore)
        $Lock = [IO.File]::Open((Join-Path $Skills '.reels-maker-install.lock'), [IO.FileMode]::OpenOrCreate, [IO.FileAccess]::ReadWrite, [IO.FileShare]::None)
        try { Expect-Error "$Client existing lock respected" { & $FixtureInstaller -Client $Client -ProjectPath $Project } 'INSTALL_LOCK_OR_PERMISSION' }
        finally { $Lock.Dispose() }
        [IO.File]::WriteAllText((Join-Path $Target 'SKILL.md'), 'user modification')
        Expect-Error "$Client modified skill refused" { & $FixtureInstaller -Client $Client -ProjectPath $Project } 'EXISTING_SKILL_DIFFERS'
        Check "$Client modified skill preserved" ([IO.File]::ReadAllText((Join-Path $Target 'SKILL.md')) -eq 'user modification')
    }
    Check 'existing personal profile preserved' ((Get-FileHash -LiteralPath $Profile).Hash -eq $Before)
    $Helper = $LauncherAst.FindAll({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq 'Receive-RuntimeArchive'}, $true)[0]
    . ([scriptblock]::Create($Helper.Extent.Text))
    # Test dispatch deterministically; optional network test invokes the actual
    # isolated Python code against the official pinned archive.
    $script:WebMode = 'success'; $script:PythonChoices = @(); $script:PythonLookups = 0
    function Invoke-WebRequest {
        param([switch]$UseBasicParsing, [string]$Uri, [string]$OutFile, [int]$TimeoutSec)
        if ($script:WebMode -eq 'failure') { throw 'fixture SEC_E_NO_CREDENTIALS' }
        [IO.File]::WriteAllText($OutFile, 'normal HTTPS fixture')
    }
    function Get-Command {
        param([string]$Name, [string]$CommandType, [switch]$All, [string]$ErrorAction)
        if ($Name -ne 'python.exe') { throw 'Unexpected command lookup' }
        $script:PythonLookups += 1
        return $script:PythonChoices
    }
    $Archive = Join-Path $Work 'download.zip'
    Receive-RuntimeArchive 'https://example.com/archive.zip' $Archive
    Check 'normal HTTPS does not require Python' ($script:PythonLookups -eq 0 -and [IO.File]::ReadAllText($Archive) -eq 'normal HTTPS fixture')
    Expect-Error 'non-HTTPS initial URL refused' { Receive-RuntimeArchive 'http://example.com/archive.zip' $Archive } 'HTTPS'
    $script:WebMode = 'failure'
    Expect-Error 'HTTPS failure without Python reported' { Receive-RuntimeArchive 'https://example.com/archive.zip' $Archive } 'RUNTIME_DOWNLOAD_FAILED.*SEC_E_NO_CREDENTIALS'
    $script:PythonChoices = @([pscustomobject]@{Source='C:\Users\test\AppData\Local\Microsoft\WindowsApps\python.exe'})
    Expect-Error 'WindowsApps store alias excluded' { Receive-RuntimeArchive 'https://example.com/archive.zip' $Archive } 'RUNTIME_DOWNLOAD_FAILED'
    # The exact production Python literal is checked separately by Python tests.
    $DownloadLiteral = $Helper.FindAll({param($n) $n -is [Management.Automation.Language.StringConstantExpressionAst] -and $n.Value.Contains('import shutil, ssl, sys, urllib.request')}, $true)[0]
    Check 'isolated Python download code found' ($null -ne $DownloadLiteral)
    $HashGuard = $LauncherAst.FindAll({param($n) $n -is [Management.Automation.Language.IfStatementAst] -and $n.Extent.Text.Contains('[ARCHIVE_HASH_MISMATCH]') -and $n.Clauses[0].Item1.Extent.Text.Contains('Get-FileHash')}, $true)[0]
    $Expected = '3b2661a463a5baea7f5076ea2b25ab71d77f36a6c0d809e5350651792f80a672'
    Expect-Error 'tampered download refused before archive extraction' { . ([scriptblock]::Create($HashGuard.Extent.Text)) } 'ARCHIVE_HASH_MISMATCH'
    if ($NetworkDownload) {
        if (-not $PythonExecutable -or -not (Test-Path -LiteralPath $PythonExecutable -PathType Leaf)) { throw 'Supply an existing PythonExecutable for the optional network test' }
        $script:PythonChoices += [pscustomobject]@{Source=$PythonExecutable}
        Receive-RuntimeArchive 'https://github.com/astral-sh/uv/releases/download/0.13.1/uv-x86_64-pc-windows-msvc.zip' $Archive
        . ([scriptblock]::Create($HashGuard.Extent.Text))
        Check 'real existing Python fallback and pinned archive SHA256' $true
    }
    [pscustomobject]@{status='passed';host=[Environment]::OSVersion.Platform.ToString();native_windows=([Environment]::OSVersion.Platform -eq [PlatformID]::Win32NT);network_fallback_executed=[bool]$NetworkDownload;check_count=$Checks.Count;checks=$Checks} | ConvertTo-Json -Depth 4
}
finally { Remove-Item -LiteralPath $Work -Recurse -Force }
