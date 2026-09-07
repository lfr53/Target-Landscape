# Running this on Windows

Two files to double-click. No typing.

## Once: install Python

Windows does not ship it. About three minutes.

1. Go to **https://www.python.org/downloads/**
2. Click the big yellow **Download Python 3.x.x** button
3. Run the downloaded file
4. **Tick the box at the bottom of the first screen:**

   > ☑ **Add python.exe to PATH**

   This is the step everyone misses. Nothing works without it, and the fix is
   to run the installer again — so it is worth looking twice before clicking.
5. Click **Install Now** and wait

## Then: double-click `1-SETUP.bat`

Checks the three public APIs, builds the target index, fills the target
library, installs the two web packages. Takes 10–20 minutes, almost all of it
waiting on the APIs. Leave the window open.

Everything it prints is also written to `setup-log.txt`. If anything fails,
that file is the thing to send on — it names the exact field and file.

If Python is missing it says so and offers to open the download page, rather
than failing with something cryptic.

## Then: double-click `2-START-WEBSITE.bat`

Starts the site and opens the browser at http://127.0.0.1:8000 once the server
is actually answering.

Leave the window open while using the site. To stop it: click the window and
press **Ctrl+C**.

## 3-CHECK-UNIPROT.bat — optional, run once

The paragraph at the top of every target page is curated UniProt annotation.
Curated landscapes that were built before that source existed do not carry it,
and their headers fall back to the Open Targets function line and say so.

This launcher fills the gap, in two steps. It first prints the paragraph
BAFF-R and PD-1 would get and writes nothing, so the output can be read before
it is trusted; then it asks whether to write it into `data\curated`. Answer
`n` and nothing is changed.

What the printed paragraphs should look like:

* the right protein — BAFF-R first, PD-1 second;
* prose, with no `(PubMed:12345678)` or `{ECO:...}` left mid-sentence;
* PMIDs listed against the function and disease lines;
* roughly 100–200 words.

If anything there looks wrong, do not answer `y` — the parser needs fixing
first, and the page is honest without it.

## 4-ADD-TARGET.bat — build a target into the library

Type one or more symbols (aliases work: `PD-1`, `HER2`, `BAFF-R`). Each takes
20-40 seconds — three public APIs, in sequence. The result is committed to
`data/curated/`, which means that target then opens instantly and cannot fail,
because serving it touches no external API.

Worth doing for any target you might show someone. It also fills in the header
brief: the sentence saying what a target is being developed for is derived
from its asset table, so a target with no stored landscape cannot have one.

## 5-PUSH-GITHUB.bat — publish the project

Create an **empty** repository on github.com first — no README, no .gitignore,
no licence, since those already exist here and GitHub creating them makes the
first push conflict. Then run this: it shows what will be published, asks
before committing anything, and pushes.

Sign-in is handled by Git Credential Manager in its own browser window. This
project holds no API key of any kind, by design.

Run it again after later changes; it commits and pushes on top.

## 7-DEPLOY-SPACE.bat -- put it online

Publishes the site to a Hugging Face Space, so there is a link that opens the
running tool rather than a repository someone has to install.

Create the Space first at <https://huggingface.co/new-space>: **SDK Docker**,
template **Blank**, hardware **CPU basic** (free). Then run this and paste the
Space URL; it is remembered afterwards.

Sign-in there is an access token rather than a password. Make one with **write**
permission at <https://huggingface.co/settings/tokens>; the username is your
Hugging Face username. As with GitHub, this project holds no API key.

Two things it does that are worth knowing. It deploys the **last commit**, not
the working folder, and warns you if those differ -- so run 5-PUSH-GITHUB.bat
first. And it swaps `SPACE_README.md` in as `README.md`, because a Space reads
its build configuration from the first lines of that file; that block would sit
at the top of the GitHub page as a wall of YAML, which is why the two are
separate files. Nothing in your own repository is changed: the swap happens in
a temporary copy that is deleted afterwards.

The Space rebuilds the Docker image on each push, two or three minutes. The
Logs tab there says when the server is up.

## If something goes wrong

Send `setup-log.txt`. It has the full output including the error, which is
more useful than a description or a screenshot.

Common ones:

| What you see | What it means |
|---|---|
| `python is not recognized` | The PATH box was not ticked. Run the Python installer again and tick it |
| A window flashes and vanishes | Right-click the `.bat` → Run as administrator, or open PowerShell and run it from there so the error stays visible |
| `[ FAIL ] reachable` | Your network is blocking the APIs, or you are behind a VPN or institutional proxy. Try off the university network |
| `[ FAIL ]` on a specific field | One of the public APIs renamed a field. The line under it names the file to fix |
| The UniProt check prints `no reviewed human UniProt entry` | Expected on some genes; the page falls back to the Open Targets line and says so |
| The UniProt paragraph is about the wrong protein | A parser bug, not a data problem. Answer `n` and send me the printed output |
