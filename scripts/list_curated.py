#!/usr/bin/env python3
"""Print the symbols already in the curated tier, one line, comma separated.

This exists as a file rather than as a ``python -c`` one-liner because the
one-liner did not survive the trip through cmd.exe. PowerShell passed the
inline program to Python as a single argument, Windows re-parsed it on the way
across the process boundary, and the quotes around ``"."`` were stripped:

    sys.path.insert(0, .)
                       ^
    SyntaxError: invalid syntax

Which the launcher printed where the list of curated targets should have been.
A script file has no quoting to lose.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from landscape import store  # noqa: E402


def main() -> int:
    try:
        symbols = store.curated_symbols()
    except Exception as exc:  # the launcher should say what broke, not vanish
        print(f"  (could not read the curated library: {exc})")
        return 1
    print("  " + (", ".join(symbols) if symbols else "(none)"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
