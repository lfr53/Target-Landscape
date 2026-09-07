# Start the site. Run it by double-clicking 2-START-WEBSITE.bat.
#
# Opens the browser once the server is actually answering, rather than
# immediately - a browser that opens onto a connection error looks like a
# broken tool even when nothing is wrong.

$ErrorActionPreference = 'Continue'
Set-Location -LiteralPath $PSScriptRoot
Set-Location ..

$python = $null
foreach ($candidate in @(
    @{ exe = 'py';      args = @('-3') },
    @{ exe = 'python';  args = @() },
    @{ exe = 'python3'; args = @() }
)) {
    try {
        $version = & $candidate.exe @($candidate.args + '--version') 2>&1 | Out-String
    } catch { continue }
    if ($version -match 'Python 3\.') { $python = $candidate; break }
}

if (-not $python) {
    Write-Host "Python is not installed. Run 1-SETUP.bat first." -ForegroundColor Red
    Read-Host "Press Enter to close"
    exit 1
}

Write-Host ""
Write-Host "Starting the site at http://127.0.0.1:8000" -ForegroundColor Cyan
Write-Host "Leave this window open while you use it." -ForegroundColor Cyan
Write-Host "To stop: click this window and press Ctrl+C." -ForegroundColor Cyan
Write-Host ""

# Open the browser only once the port answers, in a background job so the
# server itself stays in the foreground where its log is visible.
Start-Job -ScriptBlock {
    for ($i = 0; $i -lt 60; $i++) {
        Start-Sleep -Milliseconds 500
        try {
            $probe = Invoke-WebRequest -Uri 'http://127.0.0.1:8000/api/health' `
                -UseBasicParsing -TimeoutSec 2
            if ($probe.StatusCode -eq 200) {
                Start-Process 'http://127.0.0.1:8000'
                return
            }
        } catch { }
    }
} | Out-Null

& $python.exe @($python.args + @('-m', 'uvicorn', 'web.app:app', '--host', '127.0.0.1', '--port', '8000'))

Write-Host ""
Read-Host "Server stopped. Press Enter to close"
