# Put the project on GitHub. Run it by double-clicking 5-PUSH-GITHUB.bat.
#
# Sign-in is handled by Git Credential Manager, which opens its own browser
# window. Nothing in this script ever sees or stores a password or a token,
# and it should stay that way.
#
# Before running: create an EMPTY repository on github.com - no README, no
# .gitignore, no licence. Those files already exist here, and letting GitHub
# create them makes the first push conflict.

$ErrorActionPreference = 'Continue'
Set-Location -LiteralPath $PSScriptRoot
Set-Location ..

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "Git is not installed." -ForegroundColor Red
    Write-Host "Install it from https://git-scm.com/download/win, then run this again."
    Read-Host "Press Enter to close"
    exit 1
}

# A repository here is a fresh one on the first run and an existing one after.
if (-not (Test-Path ".git")) {
    Write-Host "Creating a git repository here..." -ForegroundColor Cyan
    git init --initial-branch=main | Out-Null
} else {
    Write-Host "Using the git repository already in this folder." -ForegroundColor DarkGray
}

# Identity has to be set or the commit is refused. Only set it if it is missing.
if (-not (git config user.email)) {
    $email = Read-Host "Your email for git commits"
    $name = Read-Host "Your name for git commits"
    git config user.email $email
    git config user.name $name
}

Write-Host ""
Write-Host "=== What will be published ===" -ForegroundColor Cyan
git add -A
$staged = git diff --cached --name-only
$count = ($staged | Measure-Object).Count
Write-Host "$count files. The largest:" -ForegroundColor DarkGray
git diff --cached --name-only | ForEach-Object {
    if (Test-Path $_) { [PSCustomObject]@{ KB = [math]::Round((Get-Item $_).Length / 1KB); Path = $_ } }
} | Sort-Object KB -Descending | Select-Object -First 8 | Format-Table -AutoSize

Write-Host "Ignored, and staying local: the HTTP cache, __pycache__, the venv," -ForegroundColor DarkGray
Write-Host "the setup log, and the exported demo page." -ForegroundColor DarkGray
Write-Host ""
Write-Host "This repository is public if you made it public. Nothing here holds" -ForegroundColor Yellow
Write-Host "an API key - there is no key in this project by design - but check the" -ForegroundColor Yellow
Write-Host "list above before continuing." -ForegroundColor Yellow
Write-Host ""

$go = Read-Host "Continue? (y/N)"
if ($go -notmatch '^[Yy]') {
    git reset | Out-Null
    Write-Host "Cancelled. Nothing was committed." -ForegroundColor Yellow
    Read-Host "Press Enter to close"
    exit 0
}

$message = Read-Host "Commit message (blank for a default)"
if (-not $message.Trim()) { $message = "target-landscape: competitive landscape memos for drug targets" }
git commit -m $message

$existing = git remote get-url origin 2>$null
if ($existing) {
    Write-Host ""
    Write-Host "Remote already set: $existing" -ForegroundColor DarkGray
} else {
    Write-Host ""
    Write-Host "Paste the URL of the EMPTY GitHub repository you created." -ForegroundColor Cyan
    Write-Host "It looks like https://github.com/<you>/target-landscape.git" -ForegroundColor DarkGray
    $url = Read-Host "Repository URL"
    if (-not $url.Trim()) {
        Write-Host "No URL given. Committed locally, nothing pushed." -ForegroundColor Yellow
        Read-Host "Press Enter to close"
        exit 0
    }
    git remote add origin $url.Trim()
}

Write-Host ""
Write-Host "Pushing. A browser window may open for GitHub sign-in." -ForegroundColor Cyan
git push -u origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "Pushed." -ForegroundColor Green
    Write-Host "Later changes: run this again - it commits and pushes on top." -ForegroundColor DarkGray
} else {
    Write-Host ""
    Write-Host "The push failed. The commit is safe locally; nothing is lost." -ForegroundColor Red
    Write-Host ""
    Write-Host "Almost always this means GitHub has a commit yours does not build on:" -ForegroundColor DarkGray
    Write-Host "a file was edited on github.com, or the repository was created with a" -ForegroundColor DarkGray
    Write-Host "README. Git will not guess; it wants your commit replayed on top of" -ForegroundColor DarkGray
    Write-Host "theirs. That touches your files only where the same lines were edited" -ForegroundColor DarkGray
    Write-Host "in both places, and it stops and asks if they were." -ForegroundColor DarkGray
    Write-Host ""
    $again = Read-Host "Pull their changes and push again? (y/N)"
    if ($again -eq "y" -or $again -eq "Y") {
        Write-Host ""
        git pull --rebase origin main
        if ($LASTEXITCODE -ne 0) {
            Write-Host ""
            Write-Host "The replay stopped: the same lines were edited in both places." -ForegroundColor Red
            Write-Host "Put it back as it was with" -ForegroundColor DarkGray
            Write-Host "    git rebase --abort" -ForegroundColor DarkGray
            Write-Host "and send setup-log.txt -- nothing is lost either way." -ForegroundColor DarkGray
        } else {
            git push -u origin main
            if ($LASTEXITCODE -eq 0) {
                Write-Host ""
                Write-Host "Pushed." -ForegroundColor Green
            } else {
                Write-Host ""
                Write-Host "Still refused. Sign-in was cancelled, or the URL is wrong." -ForegroundColor Red
            }
        }
    } else {
        Write-Host ""
        Write-Host "Nothing pushed. Your commit is still here; run this again when ready." -ForegroundColor Yellow
    }
}
Read-Host "Press Enter to close"
