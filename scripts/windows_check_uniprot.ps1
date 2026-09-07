# Check the UniProt brief, then optionally write it into the stored
# landscapes. Run it by double-clicking 3-CHECK-UNIPROT.bat.
#
# Two steps on purpose. The first prints the paragraph two targets would get
# and writes nothing, because a parser against a live API should be checked by
# reading its output rather than trusted. The second applies it, and only
# after the reader has said the output looked right.

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
Write-Host "=== Step 1 of 2: what the header brief would say ===" -ForegroundColor Cyan
Write-Host "Nothing is written in this step." -ForegroundColor DarkGray
Write-Host ""

foreach ($symbol in @('TNFRSF13C', 'PDCD1')) {
    Write-Host ("-" * 66) -ForegroundColor DarkGray
    & $python.exe @($python.args + @('scripts\backfill_annotation.py', '--show', $symbol))
    Write-Host ""
}

Write-Host ("-" * 66) -ForegroundColor DarkGray
Write-Host ""
Write-Host "Read the two paragraphs above before answering. They should:" -ForegroundColor Cyan
Write-Host "  * describe the right protein - BAFF-R, then PD-1;"
Write-Host "  * read as prose, with no '(PubMed:12345678)' or '{ECO:...}' left in;"
Write-Host "  * carry PMIDs on the function and disease lines;"
Write-Host "  * run about 100-200 words."
Write-Host ""

$answer = Read-Host "Write these into the stored landscapes? (y/N)"
if ($answer -notmatch '^[Yy]') {
    Write-Host ""
    Write-Host "Nothing written. Close this window." -ForegroundColor Yellow
    Read-Host "Press Enter to close"
    exit 0
}

Write-Host ""
Write-Host "=== Step 2 of 2: writing the annotation into data\curated ===" -ForegroundColor Cyan
Write-Host ""
& $python.exe @($python.args + @('scripts\backfill_annotation.py'))

Write-Host ""
Write-Host "Done. Start the site with 2-START-WEBSITE.bat to see it." -ForegroundColor Green
Read-Host "Press Enter to close"
