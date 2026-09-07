# Calibrating the density bands

The competitive-density score is a phase-weighted count. On its own a number
like `4.8` means nothing; it only becomes a judgement once you know what 4.8
looks like next to a saturated target and next to an empty one. That is what
this directory is for.

## Procedure

```bash
python -m landscape --calibrate --out out/calibration
open out/calibration/index.html
```

The index ranks every target by score and draws them on one scale.

1. **Check retrieval before you touch the thresholds.** If a target lands far
   from its annotation in `targets.txt`, open its memo first. An unexpectedly
   low score is usually missing data, not a wrong threshold — an empty asset
   table with no warnings is the signature of API drift, and
   `python -m landscape doctor` will say which field moved.
2. **Then set the thresholds** in `config.py` (`CROWDING_BANDS`) so the bands
   separate the annotated groups. Aim for boundaries that sit in the gaps
   between clusters rather than through the middle of one.
3. **Record the run** — date and the resulting scores — in `results.md`, and
   update the "Last full run" line at the top of `targets.txt`.

## What this does not do

It does not make the bands objective. They remain a convention: a defensible
one once it is derived from a spread of real targets and written down, but a
convention. Every memo prints the thresholds it used for exactly that reason.

A more rigorous version would define the bands against an outcome — say, the
probability that a new entrant at a given phase reaches approval — rather than
against a count. That needs outcome data this tool does not have.
