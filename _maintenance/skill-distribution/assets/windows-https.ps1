function Receive-RuntimeArchive([string]$Uri, [string]$Destination) {
    if (-not $Uri.StartsWith('https://', [StringComparison]::OrdinalIgnoreCase)) { throw 'HTTPS 다운로드 주소가 필요합니다.' }
    try {
        Invoke-WebRequest -UseBasicParsing -Uri $Uri -OutFile $Destination -TimeoutSec 180
        return
    }
    catch {
        $WebFailure = $_
        # Optional existing Python fallback for restricted Windows Schannel
        # accounts. This Python only downloads uv; uv prepares the edit runtime.
        $PythonCommand = Get-Command python.exe -CommandType Application -All -ErrorAction SilentlyContinue |
            Where-Object { $_.Source -and $_.Source -notlike '*\WindowsApps\*' } | Select-Object -First 1
        if (-not $PythonCommand) {
            throw "[RUNTIME_DOWNLOAD_FAILED] Windows HTTPS 다운로드 실패. 대체 다운로드에 사용할 기존 Python도 없습니다. $($WebFailure.Exception.Message)"
        }
        Write-Host "Windows HTTPS 다운로드 실패: $($WebFailure.Exception.Message)"
        Write-Host '기존 Python의 인증서 검증 HTTPS로 재시도합니다. 다운로드 뒤 SHA256도 검증합니다.'
        $DownloadCode = @'
import shutil, ssl, sys, urllib.request
with urllib.request.urlopen(sys.argv[1], context=ssl.create_default_context(), timeout=60) as response:
    if not response.geturl().lower().startswith('https://'):
        raise ValueError('HTTPS redirect required')
    with open(sys.argv[2], 'wb') as output:
        shutil.copyfileobj(response, output)
'@
        try { & $PythonCommand.Source -I -c $DownloadCode $Uri $Destination }
        catch { throw "[RUNTIME_DOWNLOAD_FAILED] 기존 Python 실행 실패: $($_.Exception.Message). Windows HTTPS 원인: $($WebFailure.Exception.Message)" }
        if ($LASTEXITCODE -ne 0) { throw "[RUNTIME_DOWNLOAD_FAILED] Python 다운로드 재시도 실패 (종료 코드 $LASTEXITCODE). Windows HTTPS 원인: $($WebFailure.Exception.Message)" }
    }
}
