#!/usr/bin/env python3
"""Export the site as one self-contained HTML file.

    python scripts/make_static_demo.py --out out/demo.html

The same interface, the same code, with the curated payloads inlined and the
API calls short-circuited (see the static shim in web/static/app.js). No
server, no dependencies, no cold start — it opens from a file path or any
static host.

It exists for the case the deployed version handles badly: showing the tool to
someone on a laptop with bad wifi, or linking it somewhere it has to still work
in six months. Live lookup is the one thing it cannot do, and it says so.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from landscape import store, targets as target_index  # noqa: E402
from landscape.analysis import showcase as showcase_mod  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC = os.path.join(ROOT, "web", "static")


def read(name: str) -> str:
    with open(os.path.join(STATIC, name), "r", encoding="utf-8") as fh:
        return fh.read()


def build(symbols: list[str] | None = None, split: bool = False) -> tuple[str, dict]:
    """The page, and the per-target records.

    ``split=False`` inlines every record: one file, opens from a file path, and
    the right thing to email someone. It stops scaling at a few dozen targets,
    because the reader downloads all of them to look at one.

    ``split=True`` leaves the records out and lets the page fetch the one it
    needs from ``targets/<SYMBOL>.json``. The first paint is then the shell and
    the index -- tens of kilobytes -- whatever the library holds. It needs to be
    served over http, which is what the published site is.
    """
    library = store.index()
    if symbols:
        wanted = {s.upper() for s in symbols}
        library = [row for row in library if row["symbol"].upper() in wanted]
    if not library:
        raise SystemExit(
            "Nothing to export — the curated tier is empty.\n"
            "Seed it first: python scripts/precompute.py --set calibration/targets.txt"
        )

    targets = {}
    for row in library:
        found = store.load(row["symbol"])
        if not found:
            continue
        landscape, meta = found
        payload = landscape.to_dict()
        payload["meta"] = meta
        assets = payload["assets"]
        payload["facets"] = {
            "phases": sorted({a["max_phase"] for a in assets}, reverse=True),
            "modalities": sorted({a["modality"] for a in assets if a["modality"]}),
            "mechanisms": sorted({a["mechanism_class"] for a in assets if a["mechanism_class"]}),
            "sponsors": sorted({a["sponsor"] for a in assets if a["sponsor"]}),
            "indications": sorted({i for a in assets for i in a["indications"]}),
        }
        targets[row["symbol"].upper()] = payload

    # The index ships too, trimmed: search and browse are the point of the
    # page, and a static build that can only find its own curated targets is
    # a much weaker demo than one that can show the whole index and say which
    # entries are already built.
    index_rows = [
        {
            "symbol": r["symbol"],
            "name": r.get("name", ""),
            "aliases": (r.get("aliases") or [])[:4],
            "areas": r.get("areas") or [],
        }
        for r in target_index.browse(limit=5000)
    ]

    # The landing page's six tiles come from the API in the served build. The
    # static export was not carrying them, so the demo opened on a search box
    # and an index and showed none of the six answers it exists to show.
    showcase = None
    pick = showcase_mod.pick([row["symbol"] for row in library])
    if pick and pick.upper() in targets:
        found = store.load(pick)
        if found:
            landscape, _meta = found
            showcase = {"symbol": pick, "tiles": showcase_mod.tiles(landscape)}

    html = read("index.html")
    payload = {
        "library": library,
        "showcase": showcase,
        "index": index_rows,
        "areas": target_index.areas(),
    }
    if split:
        # The names only. The page needs to know which targets it can open
        # before it opens any of them -- the search list marks them.
        payload["built"] = sorted(targets)
        payload["data_base"] = "targets/"
    else:
        payload["targets"] = targets
    data = json.dumps(payload, ensure_ascii=False)

    # Inline the stylesheet and script, and drop in the payload before the app
    # runs so the static shim is active from the first line.
    html = html.replace(
        '<link rel="stylesheet" href="/static/styles.css">',
        "<style>\n" + read("styles.css") + "\n</style>",
    )
    # Only app.js. This used to look for an i18n.js tag beside it, and when the
    # language layer was removed from index.html the replacement stopped
    # matching -- silently, because str.replace does not complain. The export
    # kept being written, 48 KB of shell with no payload and no application in
    # it, and the only sign was a page that opened to nothing.
    marker = '<script src="/static/app.js"></script>'
    if marker not in html:
        raise SystemExit(
            "index.html no longer loads /static/app.js the way this exporter "
            "expects, so the payload would not be inlined. Fix the marker here "
            "rather than shipping an empty page."
        )
    html = html.replace(
        marker,
        "<script>window.TL_STATIC = " + data + ";</script>\n"
        + "<script>\n" + read("app.js") + "\n</script>",
    )
    # Routing under the static build is handled in app.js itself, keyed off the
    # TL_STATIC payload. It used to be three str.replace calls patching the
    # router from out here, and when the router was edited two of them stopped
    # matching -- silently, which is what str.replace does -- and the export
    # shipped with a router that could not open a target.
    html = html.replace(
        '<span class="brand-name">Target Landscape</span>',
        '<span class="brand-name">Target Landscape</span>'
        '<span class="chip" style="margin-left:8px">static demo</span>',
    )
    return html, targets


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export the site as static files.")
    parser.add_argument("symbols", nargs="*", help="limit to these curated targets")
    parser.add_argument("--out", default="out/demo.html",
                        help="one self-contained file, for sending to someone")
    parser.add_argument("--out-dir",
                        help="a directory to serve: index.html plus one file per "
                             "target, fetched on demand")
    args = parser.parse_args(argv)

    if args.out_dir:
        html, targets = build(args.symbols or None, split=True)
        data_dir = os.path.join(args.out_dir, "targets")
        os.makedirs(data_dir, exist_ok=True)
        total = 0
        for symbol, record in sorted(targets.items()):
            path = os.path.join(data_dir, symbol + ".json")
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(record, fh, ensure_ascii=False, separators=(",", ":"))
            total += os.path.getsize(path)
        index = os.path.join(args.out_dir, "index.html")
        with open(index, "w", encoding="utf-8") as fh:
            fh.write(html)
        if "TL_STATIC" not in html:
            raise SystemExit("The payload did not make it into the page.")
        print(f"{index} — {len(html) / 1024:.0f} KB shell, "
              f"{len(targets)} targets in {data_dir} — {total / 1024 / 1024:.1f} MB")
        return 0

    html, _targets = build(args.symbols or None)
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(html)
    print(f"{args.out} — {len(html) / 1024:.0f} KB, "
          f"{'payload inlined' if 'TL_STATIC' in html else 'NO PAYLOAD'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
