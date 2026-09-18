# verdicts.json — schema and workbook layout

`build_report.py` reads one JSON file and writes the workbook. This is the
contract.

## Top level

```json
{
  "meta":        { ... },
  "unit_tests":  [ case, case, ... ],
  "build_gates": [ gate, gate, ... ]
}
```

`test_cases` is accepted as an alias for `unit_tests`. Either list may be empty.

## meta

Every field is optional, but the ones about *provenance* are what make the
report defensible later — a verdict means nothing unless the reader knows which
source revision it was made against.

| Key | Example |
|---|---|
| `run_date` | `"2026-09-14"` (defaults to today) |
| `program` | `"ZKSNI002_NEW_20260901"` |
| `tcode` | `"ZINV_002_NEW"` |
| `spec_file` | `"Funcspec ... v1.5 - As-Built 20260908.xlsx"` |
| `spec_sheet` | `"09 Build Gates & Unit Test"` |
| `spec_version` | `"v1.5, dated 2026-09-08"` |
| `source_root` | `"BUILD 20260911 EDITABLE"` |
| `source_revision` | `"r42; files dated 2026-09-11"` |
| `method` | defaults to "source code reading (not executed in SAP)" |
| `tester` | who or what performed the assessment |

Unknown keys are written to the Summary sheet as extra rows, so project-specific
provenance (transport number, branch, ticket) can be added freely.

## A case / gate object

```json
{
  "id": "UT-05",
  "case": "Posting blocked when no assessment exists",
  "covers": "DD-04, Section 2.3",
  "expected": "Posting is refused with message E-12",
  "verdict": "SPEC_STALE",
  "evidence": [
    { "file": "ZKSNI002_NEW_20260901_F01.abap", "line": 1842,
      "code": "IF lv_assmt_guid IS INITIAL." },
    { "file": "ZKSNI002_NEW_20260901_F01.abap", "line": 1845,
      "code": "MESSAGE 'Enter the invoice number.' TYPE 'W'." }
  ],
  "notes": "Spec expects hard block E-12; code warns (TYPE 'W') and lets the "
           "user continue. Changed in r38 per FINDINGS note.",
  "test_steps": [
    "ZINV_002_NEW for vendor 0001000123 with no staged assessment",
    "Press Save and observe whether the document posts"
  ]
}
```

Field notes:

- `case` — for gates use `gate`; `title` and `name` also work. One object shape
  for both sheets keeps the scripts simple.
- `covers` — the spec's cross-reference (Task ID, DD-xx, section number). Only
  used on the test-case sheet.
- `verdict` — one of `PASS`, `FAIL`, `NA`, `NEEDS_SYSTEM`, `SPEC_STALE`,
  `BLOCKED`. `"N/A"` is normalised to `NA`; spaces and hyphens to underscores.
- `evidence` — a list. Each entry needs `file`, `line` (integer, 1-based, as
  SE38/ADT numbers it) and `code` (the line verbatim, trimmed). Quote the line
  that *decides* the claim.
- `notes` — deviations, doubts, why a stronger verdict was not available. This
  is where "the code does X but X looks wrong" belongs.
- `test_steps` — string or list. Required for `NEEDS_SYSTEM`; useful anywhere.
  They appear on the row and in the manual-test queue on the Summary sheet.

## Enforced rules

The script exits non-zero rather than writing a misleading workbook when:

- a verdict is outside the vocabulary, or an `id` is missing or duplicated;
- `PASS` / `FAIL` / `NA` / `SPEC_STALE` has no evidence, or an evidence entry is
  missing its file, line, or quoted code;
- `NEEDS_SYSTEM` has no test steps;
- `SPEC_STALE` has no notes.

`--allow-incomplete` turns these into warnings printed on the Summary sheet.
Use it for a work-in-progress draft, never for a deliverable.

## Sheets produced

**Summary** — title, provenance block, a verdict tally (live `COUNTIF`
formulas over the other two sheets, so hand-edits keep the totals honest), then
the SPEC STALE findings, the NEEDS SYSTEM queue, any BLOCKED items, and any
data-quality warnings.

**Test Cases** — `No | Test Case | Covers | Expected Result | Verdict |
Evidence (file:line) | Code Quote | Notes / Deviation`. Frozen header,
autofilter, wrapped text.

**Build Gates** — `No | Gate | Verdict | Evidence (file:line) | Code Quote |
Notes`.

With `--lang id` the sheets are named `Ringkasan` / `Unit Test` / `Build Gates`
and the headers and verdict labels are Indonesian (`LULUS`, `GAGAL`, `N/A`,
`PERLU SISTEM`, `SPEC BASI`, `TERBLOKIR`).

Verdict cells are filled with a colour *and* carry the label as text. Colour is
an aid; the text is the record. Never ship a report where the verdict is only
legible in colour.
