# One-shot setup for Windows. Run it by double-clicking 1-SETUP.bat.
#
# Everything the tool needs after Python itself: it finds the interpreter,
# checks the three public APIs, builds the target index, and fills the target
# library. Every line is echoed to the screen and appended to setup-log.txt,
# so a failure can be sent on verbatim rather than described from memory.

$ErrorActionPreference = 'Continue'
Set-Location -LiteralPath $PSScriptRoot
Set-Location ..

$log = Join-Path (Get-Location) 'setup-log.txt'
"=== target-landscape setup - $(Get-Date -Format 'yyyy-MM-dd HH:mm') ===" |
    Tee-Object -FilePath $log

function Say($text, $colour = 'White') {
    Write-Host ""
    Write-Host $text -ForegroundColor $colour
    "" | Out-File -FilePath $log -Append
    $text | Out-File -FilePath $log -Append
}

function Run($label, $exe, $argumentList) {
    Say "--- $label ---" 'Cyan'
    & $exe @argumentList 2>&1 | Tee-Object -FilePath $log -Append
    return $LASTEXITCODE
}

# ---------------------------------------------------------------------------
# 1. Find Python
# ---------------------------------------------------------------------------
# Three ways it can be present, and one way it can look present but not be:
# the Microsoft Store stub answers `python` but exits non-zero and prints
# nothing, so the version string is checked rather than just the command.

$python = $null
foreach ($candidate in @(
    @{ exe = 'py';     args = @('-3') },
    @{ exe = 'python'; args = @() },
    @{ exe = 'python3'; args = @() }
)) {
    try {
        $version = & $candidate.exe @($candidate.args + '--version') 2>&1 | Out-String
    } catch {
        continue
    }
    if ($version -match 'Python 3\.(\d+)') {
        if ([int]$Matches[1] -lt 9) {
            Say "Found $($version.Trim()), but this needs Python 3.9 or newer." 'Yellow'
            continue
        }
        $python = $candidate
        Say "Python found: $($version.Trim())" 'Green'
        break
    }
}

if (-not $python) {
    Say "PYTHON IS NOT INSTALLED" 'Red'
    Write-Host @"

Nothing else can run until it is. It takes about three minutes:

  1. Go to  https://www.python.org/downloads/
  2. Click the big yellow button at the top
  3. Run the installer, and TICK THE BOX AT THE BOTTOM:
         [x] Add python.exe to PATH
     This is the step everyone misses. Without it, nothing below works.
  4. Click "Install Now", wait for it to finish
  5. Double-click 1-SETUP.bat again

"@ -ForegroundColor Yellow
    $open = Read-Host "Open the download page now? (y/n)"
    if ($open -eq 'y') { Start-Process 'https://www.python.org/downloads/' }
    Write-Host ""
    Read-Host "Press Enter to close"
    exit 1
}

$exe = $python.exe
$base = $python.args

# ---------------------------------------------------------------------------
# 2. Health check, index, library
# ---------------------------------------------------------------------------

$doctor = Run 'Checking the three public APIs' $exe ($base + @('-m', 'landscape', 'doctor'))
if ($doctor -ne 0) {
    Say "Some checks failed. This is the useful kind of failure - the output above names the field that moved and the file to fix." 'Yellow'
    Say "Send the contents of setup-log.txt back and it can be fixed." 'Yellow'
    Say "Continuing anyway: the parts that do work will still be built." 'Yellow'
}

Run 'Building the target index (about a minute)' $exe ($base + @('scripts/build_target_index.py')) | Out-Null

Say "The next step fetches 15 targets from three APIs and takes 10-20 minutes." 'Cyan'
Say "It is safe to leave it running. Do not close this window." 'Cyan'
Run 'Filling the target library' $exe ($base + @('scripts/precompute.py', '--set', 'calibration/targets.txt', '--skip-existing')) | Out-Null

# ---------------------------------------------------------------------------
# 3. Web dependencies
# ---------------------------------------------------------------------------

Run 'Installing the two web packages' $exe ($base + @('-m', 'pip', 'install', '--quiet', 'fastapi', 'uvicorn')) | Out-Null

Say "=== DONE ===" 'Green'
Write-Host @"

Next: double-click  2-START-WEBSITE.bat

A full log of everything above is in:
  $log

If anything went wrong, send that file - it has the exact error.

"@ -ForegroundColor Green
Read-Host "Press Enter to close"
