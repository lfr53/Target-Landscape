# Publish the site to a Hugging Face Space. Run it by double-clicking
# 7-DEPLOY-SPACE.bat.
#
# A Space is its own git repository. It needs one thing this repository cannot
# have: a README.md that opens with the Space configuration block, which is
# what tells Hugging Face to build the Dockerfile and which port to serve. That
# block would sit at the top of the GitHub page as a wall of YAML, so it lives
# in SPACE_README.md and is swapped in here.
#
# Nothing is committed to your working repository. This exports the last commit
# to a temporary folder, swaps the README there, and pushes that.
#
# Sign-in: Hugging Face uses an access token as the password. Create one with
# WRITE permission at https://huggingface.co/settings/tokens. The username is
# your Hugging Face username. This script never sees or stores it.

$ErrorActionPreference = 'Continue'
Set-Location -LiteralPath $PSScriptRoot
Set-Location ..

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "Git is not installed." -ForegroundColor Red
    Read-Host "Press Enter to close"
    exit 1
}
if (-not (Test-Path ".git")) {
    Write-Host "No git repository here. Run 5-PUSH-GITHUB.bat first." -ForegroundColor Red
    Read-Host "Press Enter to close"
    exit 1
}
if (-not (Test-Path "SPACE_README.md")) {
    Write-Host "SPACE_README.md is missing - that file is the Space configuration." -ForegroundColor Red
    Read-Host "Press Enter to close"
    exit 1
}

# Uncommitted work would be silently left out: this pushes the last commit, not
# the working folder. Say so rather than deploying something older than what is
# on screen.
$dirty = git status --porcelain
if ($dirty) {
    Write-Host ""
    Write-Host "There are uncommitted changes here. This deploys the LAST COMMIT," -ForegroundColor Yellow
    Write-Host "so those changes would not appear on the Space." -ForegroundColor Yellow
    Write-Host ""
    $go = Read-Host "Deploy the last commit anyway? (y/N)"
    if ($go -notmatch '^[Yy]') {
        Write-Host "Cancelled. Run 5-PUSH-GITHUB.bat to commit first." -ForegroundColor Yellow
        Read-Host "Press Enter to close"
        exit 0
    }
}

$url = git config --get target-landscape.spaceurl
if (-not $url) {
    Write-Host ""
    Write-Host "Create the Space first, at https://huggingface.co/new-space" -ForegroundColor Cyan
    Write-Host "  Space SDK: Docker    Template: Blank    Hardware: CPU basic (free)" -ForegroundColor DarkGray
    Write-Host "Then paste its git URL below." -ForegroundColor Cyan
    Write-Host "  It looks like https://huggingface.co/spaces/<you>/target-landscape" -ForegroundColor DarkGray
    $url = Read-Host "Space URL"
    if (-not $url.Trim()) {
        Write-Host "No URL given. Nothing was deployed." -ForegroundColor Yellow
        Read-Host "Press Enter to close"
        exit 0
    }
    $url = $url.Trim()
    git config target-landscape.spaceurl $url
}
Write-Host ""
Write-Host "Space: $url" -ForegroundColor DarkGray

$stage = Join-Path ([System.IO.Path]::GetTempPath()) ("tl-space-" + (Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Path $stage | Out-Null
$tar = Join-Path $stage "repo.tar"

Write-Host "Exporting the last commit..." -ForegroundColor Cyan
git archive --format=tar -o $tar HEAD
if ($LASTEXITCODE -ne 0) {
    Write-Host "git archive failed. Nothing was deployed." -ForegroundColor Red
    Read-Host "Press Enter to close"
    exit 1
}
tar -xf $tar -C $stage
Remove-Item $tar -Force

# The swap. The Space reads its configuration from the first lines of README.md.
Copy-Item (Join-Path $stage "SPACE_README.md") (Join-Path $stage "README.md") -Force

$head = Get-Content (Join-Path $stage "README.md") -TotalCount 1
if ($head -ne '---') {
    Write-Host "SPACE_README.md does not start with the '---' configuration block," -ForegroundColor Red
    Write-Host "so Hugging Face would not know to build the Dockerfile." -ForegroundColor Red
    Read-Host "Press Enter to close"
    exit 1
}

$count = (Get-ChildItem -Path $stage -Recurse -File | Measure-Object).Count
Write-Host "$count files ready to publish." -ForegroundColor DarkGray
Write-Host ""
Write-Host "This replaces whatever is on the Space with this commit." -ForegroundColor Yellow
$go = Read-Host "Push? (y/N)"
if ($go -notmatch '^[Yy]') {
    Remove-Item $stage -Recurse -Force
    Write-Host "Cancelled. Nothing was pushed." -ForegroundColor Yellow
    Read-Host "Press Enter to close"
    exit 0
}

Push-Location $stage
git init --initial-branch=main | Out-Null
$email = git -C (Split-Path $PSScriptRoot -Parent) config user.email
$name = git -C (Split-Path $PSScriptRoot -Parent) config user.name
if ($email) { git config user.email $email }
if ($name) { git config user.name $name }
git add -A | Out-Null
git commit -m "target-landscape" | Out-Null
git remote add origin $url
Write-Host ""
Write-Host "Pushing. Username is your Hugging Face username; the password is an" -ForegroundColor Cyan
Write-Host "access token with write permission." -ForegroundColor Cyan
git push -f origin main
$ok = ($LASTEXITCODE -eq 0)
Pop-Location
Remove-Item $stage -Recurse -Force

Write-Host ""
if ($ok) {
    Write-Host "Pushed. The Space builds the Dockerfile now - two or three minutes." -ForegroundColor Green
    Write-Host "Watch the Logs tab there; when it says the server is running, open the app." -ForegroundColor DarkGray
} else {
    Write-Host "The push failed. Nothing on your machine changed." -ForegroundColor Red
    Write-Host "Most common causes:" -ForegroundColor DarkGray
    Write-Host "  * the token has read permission only - it needs write" -ForegroundColor DarkGray
    Write-Host "  * the Space URL is wrong, or the Space was never created" -ForegroundColor DarkGray
    Write-Host "  * Windows cached an old credential: clear it in Credential Manager" -ForegroundColor DarkGray
    Write-Host "To change the stored Space URL: git config --unset target-landscape.spaceurl" -ForegroundColor DarkGray
}
Read-Host "Press Enter to close"
