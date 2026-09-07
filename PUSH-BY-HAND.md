# Pushing to GitHub by hand

Use this if `5-PUSH-GITHUB.bat` will not run. The launcher does nothing the
five commands below do not do; it only asks the questions for you and checks
the answers. Nothing here needs PowerShell, so it still works when a script is
blocked by antivirus or by an execution policy.

## Open a terminal in this folder

Git installs **Git Bash**. Open the Start menu, type `Git Bash`, press Enter,
then paste this (one line):

```bash
cd /c/Users/lfr53/Downloads/target-landscape_4
```

`pwd` should answer `/c/Users/lfr53/Downloads/target-landscape_4`. If it does
not, the rest will act on the wrong folder — stop and check the path.

## The five commands

Paste them one at a time and read what each one says before the next.

```bash
git init --initial-branch=main
git config user.email "fl455@cam.ac.uk"
git config user.name "Fangrui Liu"
git add -A
git commit -m "target-landscape: a public-record view of drug targets"
```

Then connect it to the empty repository and push. Replace `<you>` with your
GitHub username:

```bash
git remote add origin https://github.com/<you>/target-landscape.git
git push -u origin main
```

A browser window opens for GitHub sign-in. That is Git Credential Manager,
which is part of Git — the password goes to GitHub, not into this project, and
nothing in this folder ever holds it.

## Every time after this

Only three commands, and no repository URL — git remembers it:

```bash
git add -A
git commit -m "what changed this time"
git push
```

Nothing is automatic. GitHub changes when you push and at no other moment.

## If the push is refused

**`Updates were rejected`** or a mention of a non-fast-forward: the repository
on GitHub was created with a README, a .gitignore or a licence, so it holds a
commit yours does not build on. Join the two histories once:

```bash
git pull --rebase origin main
git push -u origin main
```

**`Authentication failed`**: the sign-in window was closed or cancelled. Run
`git push` again and complete it.

**`fatal: not a git repository`**: the `cd` did not land in this folder. Check
`pwd` and start again.

## What gets published

Everything in the folder except what `.gitignore` excludes: the virtual
environment, `__pycache__`, the HTTP cache, the setup log and the exported
demo page. To see the list before committing:

```bash
git add -A
git status --short
```

`git reset` puts it back if you would rather not commit yet.
