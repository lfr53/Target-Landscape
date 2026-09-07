# Re-run the current rules over every curated target. Run it by
# double-clicking 6-REFRESH-LIBRARY.bat.
#
# Curated files are stored fully computed, which is what makes a target open
# instantly and never fail. The cost is that a target built last week still
# carries last week's wording and last week's rules. This pass fixes that
# without rebuilding anything: it re-runs the analysis over the records
# already in each file.
#
# No network. About a second per target, against 20-40 seconds for a rebuild.
# Nothing is fetched, so nothing can go stale or fail here.

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
Write-Host "Refresh the curated library" -ForegroundColor Cyan
Write-Host "Re-runs the current rules over every target you have already built." -ForegroundColor DarkGray
Write-Host "No network, no rebuild - about a second each." -ForegroundColor DarkGray
Write-Host ""

& $python.exe @($python.args + @('scripts/recompute_curated.py'))
$failed = ($LASTEXITCODE -ne 0)

Write-Host ""
if ($failed) {
    Write-Host "At least one target failed above and still holds its older output." -ForegroundColor Red
    Write-Host "The traceback says which target and which rule." -ForegroundColor DarkGray
} else {
    Write-Host "Done. Start the site with 2-START-WEBSITE.bat." -ForegroundColor Green
}
Read-Host "Press Enter to close"
