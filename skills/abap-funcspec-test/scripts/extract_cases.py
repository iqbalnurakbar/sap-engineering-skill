#!/usr/bin/env python3
"""Turn a scenario sheet (UT-xx / BG-xx rows) into a structured cases.json.

What this handles that naive reading does not:

* Sparse layouts - blank spacer columns, merged title blocks, multiple header
  rows. Columns are mapped by header TEXT found on the header row immediately
  above the first ID row, never by column letter.
* Bilingual cells - the same sentence twice in one cell. The common separator
  is a line break (local language first, English second); some workbooks use
  " / ". Splitting on " / " blindly is wrong, because that sequence also occurs
  mid-sentence ("F4 / on-change", "invoice / payment"), so the default
  heuristic is line-break based and the raw text is always preserved.
* Appended as-built annotations - later spec revisions bolt a note onto the end
  of a cell after a blank line, saying what was really built. Paragraph 1 is
  returned as `primary`; paragraphs 2+ as `annotations`. Those have very
  different evidential status: the primary text is the scenario, the annotation
  is a CLAIM about the code that you still have to verify against the source.

Examples
--------
  python extract_cases.py "Funcspec v1.5.xlsx" \
      --sheet "09 Build Gates & Unit Test" --out cases.json

  # separate blocks in one sheet (gates and unit tests) into two files
  python extract_cases.py spec.xlsx --sheet "09 ..." --id-pattern "^BG-\\d+" \
      --out gates.json
  python extract_cases.py spec.xlsx --sheet "09 ..." --id-pattern "^UT-\\d+" \
      --out tests.json

The default --id-pattern matches UT-01, BG-7, TC-3, TS-12, and bare numbering
like "1." when --id-pattern is relaxed by hand.
"""

import argparse
import json
import re
import sys

try:
    from openpyxl import load_workbook
    from openpyxl.utils import get_column_letter
except ImportError:  # pragma: no cover
    sys.stderr.write("openpyxl is required: pip install openpyxl\n")
    raise SystemExit(2)

DEFAULT_ID_PATTERN = r"^(?:UT|BG|TC|TS|IT|FT)[-_ ]?\d+[a-z]?$"


def say(msg):
    sys.stdout.write(str(msg).encode("ascii", "replace").decode("ascii") + "\n")


def norm(value):
    if value is None:
        return ""
    return str(value).replace("\r\n", "\n").replace("\r", "\n").strip()


def paragraphs(text):
    """Split a cell into paragraphs on blank lines."""
    if not text:
        return []
    blocks, current = [], []
    for line in text.split("\n"):
        if line.strip():
            current.append(line.rstrip())
        elif current:
            blocks.append("\n".join(current))
            current = []
    if current:
        blocks.append("\n".join(current))
    return blocks


def split_bilingual(block, mode):
    """Return (local, english) for one paragraph, or (block, "") if unsure.

    Deliberately conservative: an unsplit paragraph costs a little redundancy,
    a wrong split silently truncates a test scenario.
    """
    if mode == "none" or not block:
        return block, ""

    lines = [ln for ln in block.split("\n") if ln.strip()]
    if mode in ("auto", "newline") and len(lines) == 2:
        return lines[0].strip(), lines[1].strip()
    if mode in ("auto", "newline") and len(lines) == 4:
        # two-line sentences in each language: halve it
        return ("\n".join(lines[:2]).strip(), "\n".join(lines[2:]).strip())

    if mode == "slash" and len(lines) == 1 and " / " in block:
        left, _, right = block.rpartition(" / ")
        return left.strip(), right.strip()

    return block, ""


def parse_cell(text, mode):
    blocks = paragraphs(norm(text))
    if not blocks:
        return {"raw": "", "primary": "", "primary_en": "", "annotations": []}
    local, english = split_bilingual(blocks[0], mode)
    annotations = []
    for block in blocks[1:]:
        a_local, a_en = split_bilingual(block, mode)
        annotations.append({"text": a_local, "text_en": a_en})
    return {
        "raw": norm(text),
        "primary": local,
        "primary_en": english,
        "annotations": annotations,
    }


def find_header_row(rows, first_id_row, id_col):
    """Walk upward from the first ID row for a row that looks like headers."""
    for r in range(first_id_row - 1, max(0, first_id_row - 8), -1):
        values = rows[r - 1]
        filled = [c for c in values if norm(c)]
        if len(filled) >= 2 and norm(values[id_col - 1]):
            return r
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("workbook")
    ap.add_argument("--sheet", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--id-pattern", default=DEFAULT_ID_PATTERN,
                    help="regex an ID cell must match (default: %(default)s)")
    ap.add_argument("--bilingual", choices=["auto", "newline", "slash", "none"],
                    default="auto")
    ap.add_argument("--header-row", type=int, default=None,
                    help="override header row detection (1-based)")
    args = ap.parse_args()

    wb = load_workbook(args.workbook, read_only=True, data_only=True)
    if args.sheet not in wb.sheetnames:
        say("ERROR: no sheet %r. Available: %s" % (args.sheet, ", ".join(wb.sheetnames)))
        raise SystemExit(1)

    rows = [list(r) for r in wb[args.sheet].iter_rows(values_only=True)]
    width = max((len(r) for r in rows), default=0)
    rows = [list(r) + [None] * (width - len(r)) for r in rows]

    id_re = re.compile(args.id_pattern, re.IGNORECASE)
    hits = []
    for r_index, row in enumerate(rows, 1):
        for c_index, value in enumerate(row, 1):
            text = norm(value)
            if text and id_re.match(text):
                hits.append((r_index, c_index, text))
                break

    if not hits:
        say("ERROR: no cell matched %r on sheet %r." % (args.id_pattern, args.sheet))
        say("Dump the sheet with dump_spec.py and adjust --id-pattern.")
        raise SystemExit(1)

    id_col = hits[0][1]
    header_row = args.header_row or find_header_row(rows, hits[0][0], id_col)
    headers = {}
    if header_row:
        for c_index, value in enumerate(rows[header_row - 1], 1):
            text = norm(value)
            if text:
                local, english = split_bilingual(text, args.bilingual)
                headers[c_index] = {
                    "raw": text,
                    "label": local or text,
                    "label_en": english,
                    "column": get_column_letter(c_index),
                }

    cases = []
    for row_no, col_no, case_id in hits:
        row = rows[row_no - 1]
        fields = []
        for c_index, value in enumerate(row, 1):
            if c_index == col_no or not norm(value):
                continue
            header = headers.get(c_index, {"raw": "", "label": "col " + get_column_letter(c_index),
                                           "label_en": "", "column": get_column_letter(c_index)})
            parsed = parse_cell(value, args.bilingual)
            parsed["header"] = header["label"]
            parsed["header_en"] = header.get("label_en", "")
            parsed["column"] = header["column"]
            fields.append(parsed)
        cases.append({
            "id": case_id.upper().replace("_", "-").replace(" ", "-"),
            "row": row_no,
            "fields": fields,
            "has_annotations": any(f["annotations"] for f in fields),
        })

    payload = {
        "source": {
            "workbook": args.workbook,
            "sheet": args.sheet,
            "header_row": header_row,
            "id_pattern": args.id_pattern,
            "bilingual_mode": args.bilingual,
        },
        "headers": [headers[k] for k in sorted(headers)],
        "cases": cases,
    }

    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)

    annotated = sum(1 for c in cases if c["has_annotations"])
    say("extracted %d cases from sheet %r -> %s" % (len(cases), args.sheet, args.out))
    say("header row: %s" % (header_row or "not found - map columns by hand"))
    say("cases carrying as-built annotations: %d" % annotated)
    say("")
    say("IDs: " + ", ".join(c["id"] for c in cases))
    say("")
    say("Read the JSON file (do not cat it to a cp1252 console). Check the column")
    say("mapping and the bilingual split before you judge anything.")


if __name__ == "__main__":
    main()
