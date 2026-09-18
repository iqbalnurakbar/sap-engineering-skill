#!/usr/bin/env python3
"""Dump sheets of a spec workbook to a UTF-8 text file you can read safely.

Spreadsheet cells written for humans are full of em-dashes, arrows and curly
quotes. Printing them to a cp1252 Windows console raises UnicodeEncodeError and
kills the run, so this script never prints cell content: it writes a file and
tells you (in ASCII) where the file is.

Examples
--------
  # what sheets are in here?
  python dump_spec.py "Funcspec v1.5.xlsx" --list

  # dump one sheet
  python dump_spec.py "Funcspec v1.5.xlsx" --sheet "09 Build Gates & Unit Test" \
      --out dump.txt

  # dump everything, one file per sheet, into a folder
  python dump_spec.py "Funcspec v1.5.xlsx" --all --out-dir dumps/

Output format, one line per non-empty row:

  R021 | B: UT-01 | D: Non FP button ... <NL> Non FP was never built ...

Cell line breaks become " <NL> " so that one sheet row stays one text line and
the row/column structure remains greppable. Use --raw to keep real newlines
instead (better for reading long narrative cells, worse for grepping).
"""

import argparse
import os
import sys

try:
    from openpyxl import load_workbook
    from openpyxl.utils import get_column_letter
except ImportError:  # pragma: no cover
    sys.stderr.write("openpyxl is required: pip install openpyxl\n")
    raise SystemExit(2)


def say(msg):
    """Print ASCII-only, so a cp1252 console can never choke on it."""
    sys.stdout.write(str(msg).encode("ascii", "replace").decode("ascii") + "\n")


def cell_text(value, raw):
    if value is None:
        return ""
    text = str(value).strip()
    if not raw:
        text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", " <NL> ")
    return text


def dump_sheet(ws, out_path, raw=False, max_rows=None):
    written = 0
    with open(out_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("SHEET: %s\n" % ws.title)
        fh.write("=" * 70 + "\n\n")
        for r, row in enumerate(ws.iter_rows(values_only=False), 1):
            if max_rows and r > max_rows:
                break
            parts = []
            for cell in row:
                text = cell_text(cell.value, raw)
                if text:
                    parts.append("%s: %s" % (get_column_letter(cell.column), text))
            if not parts:
                continue
            fh.write("R%04d | %s\n" % (r, " | ".join(parts)))
            written += 1
    return written


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("workbook")
    ap.add_argument("--sheet", action="append", default=[],
                    help="sheet name to dump; repeatable")
    ap.add_argument("--all", action="store_true", help="dump every sheet")
    ap.add_argument("--list", action="store_true",
                    help="just list sheet names and row counts")
    ap.add_argument("--out", help="output file (single sheet)")
    ap.add_argument("--out-dir", help="output folder (one file per sheet)")
    ap.add_argument("--raw", action="store_true",
                    help="keep real newlines inside cells instead of ' <NL> '")
    ap.add_argument("--max-rows", type=int, default=None)
    ap.add_argument("--no-readonly", action="store_true",
                    help="load fully (slower) so merged-cell ranges are available")
    args = ap.parse_args()

    wb = load_workbook(args.workbook,
                       read_only=not args.no_readonly,
                       data_only=True)

    if args.list or (not args.sheet and not args.all):
        say("sheets in %s:" % os.path.basename(args.workbook))
        for name in wb.sheetnames:
            say("  - %s" % name)
        if not args.list:
            say("")
            say("pick one with --sheet, or dump everything with --all")
        return

    if args.all:
        names = list(wb.sheetnames)
    else:
        names = []
        for want in args.sheet:
            if want not in wb.sheetnames:
                say("ERROR: no sheet named %r. Available: %s"
                    % (want, ", ".join(wb.sheetnames)))
                raise SystemExit(1)
            names.append(want)

    if len(names) == 1 and args.out:
        targets = [(names[0], args.out)]
    else:
        out_dir = args.out_dir or "spec_dump"
        os.makedirs(out_dir, exist_ok=True)
        targets = []
        for name in names:
            safe = "".join(ch if (ch.isalnum() or ch in " -_") else "_" for ch in name)
            targets.append((name, os.path.join(out_dir, safe.strip() + ".txt")))

    for name, path in targets:
        rows = dump_sheet(wb[name], path, raw=args.raw, max_rows=args.max_rows)
        say("wrote %d non-empty rows -> %s" % (rows, path))

    if args.no_readonly:
        for name, _ in targets:
            merged = getattr(wb[name], "merged_cells", None)
            if merged and merged.ranges:
                say("merged ranges in %s: %s"
                    % (name, ", ".join(str(rng) for rng in merged.ranges)))

    say("")
    say("Read those files with your file-reading tool. Do NOT cat them to a")
    say("cp1252 console if they contain dashes or arrows.")


if __name__ == "__main__":
    main()
