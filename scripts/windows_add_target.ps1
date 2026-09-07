# Build a target into the curated tier. Run it by double-clicking
# 4-ADD-TARGET.bat.
#
# A curated landscape opens instantly and cannot fail, because serving it
# touches no external API. That is what makes a demo safe on a strange network
# - and it is also what the header brief needs, since the sentence saying what
# a target is being developed for is derived from its asset table.
#
# One target takes 20-40 seconds: three public APIs, in sequence.

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
Write-Host "Add a target to the curated library" -ForegroundColor Cyan
Write-Host "Already curated:" -ForegroundColor DarkGray
# Called as a script file, not as `python -c '...'`. The inline form did not
# survive the trip through cmd.exe: Windows re-parsed the program on the way
# across the process boundary and stripped the quotes around ".", so the
# launcher printed a SyntaxError where the list of curated targets belongs.
& $python.exe @($python.args + @('scripts/list_curated.py'))

Write-Host ""
Write-Host "Type one or more gene symbols separated by spaces." -ForegroundColor Cyan
Write-Host "Aliases work: PD-1, HER2, BAFF-R all resolve." -ForegroundColor DarkGray
Write-Host "Each one takes 20-40 seconds." -ForegroundColor DarkGray
Write-Host ""
$answer = Read-Host "Symbols (blank to cancel)"
if (-not $answer.Trim()) {
    Write-Host "Cancelled." -ForegroundColor Yellow
    Read-Host "Press Enter to close"
    exit 0
}

$symbols = $answer.Trim() -split '\s+'

Write-Host ""
Write-Host "=== Building ===" -ForegroundColor Cyan
& $python.exe @($python.args + @('scripts/precompute.py') + $symbols)
$buildFailed = ($LASTEXITCODE -ne 0)

# The landscape is built; the curated file now needs its UniProt annotation,
# or the header falls back to the Open Targets function line.
Write-Host ""
Write-Host "=== Adding the curated protein annotation ===" -ForegroundColor Cyan
& $python.exe @($python.args + @('scripts/backfill_annotation.py') + $symbols)

Write-Host ""
Write-Host "=== The header these targets will show ===" -ForegroundColor Cyan
foreach ($symbol in $symbols) {
    Write-Host ""
    & $python.exe @($python.args + @('scripts/backfill_annotation.py', '--show', $symbol))
}

Write-Host ""
if ($buildFailed) {
    # Saying "Done" over a failed build is worse than saying nothing: the next
    # thing that happens is she opens the site and the target is not there.
    Write-Host "The build reported an error above and some targets may be missing." -ForegroundColor Red
    Write-Host "Most often this is the network: the three APIs are called live." -ForegroundColor DarkGray
    Write-Host "Running this again is safe - targets already built are rebuilt, not duplicated." -ForegroundColor DarkGray
} else {
    Write-Host "Done. Start the site with 2-START-WEBSITE.bat." -ForegroundColor Green
}
Write-Host ""
Write-Host "Now curated:" -ForegroundColor DarkGray
& $python.exe @($python.args + @('scripts/list_curated.py'))
Read-Host "Press Enter to close"
