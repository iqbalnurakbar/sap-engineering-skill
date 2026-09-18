---
name: abap-funcspec-test
description: >-
  Test a SAP ABAP program by reading its SOURCE CODE instead of running it in
  SAP: every test case gets a verdict backed by file:line evidence, written to
  an Excel workbook. Use whenever someone asks for unit test results, a UT/BG
  (build gate) report, a test execution report, test evidence, a verification
  or traceability matrix, a desk-check or static test of test cases, or to
  "test this program from the source" - for any Z* report, module pool,
  function group, class or includes. Use it when the scenarios come from a
  funcspec, FS workbook, test-case sheet, as-built document or any sheet of
  UT-xx / BG-xx rows, and for Bahasa Indonesia requests too ("laporan hasil
  testing", "hasil unit test", "uji program ABAP dari source code", "buat
  laporan pengujian ke Excel", "verifikasi spec ke source"). Trigger even if
  "skill" or "Excel" never appear, as long as the deliverable is a
  per-test-case verdict grounded in source code.
---

# Funcspec scenarios, tested against ABAP source

You are producing a **desk-check test report**: someone hands you a set of test
scenarios (usually from a funcspec) and the ABAP source of the program those
scenarios describe, and you decide — from the code alone — which scenarios the
code satisfies, which it contradicts, and which simply cannot be settled without
a running SAP system. The result is an Excel workbook that a tester, a lead, or
an auditor can filter, read, and act on.

The value of this report lives entirely in its honesty. A workbook full of green
PASS cells that nobody can trace back to a line of code is worse than no report,
because it will be believed. So the whole method below is built around one idea:
**a verdict is a claim, and a claim needs evidence or it needs to be downgraded.**

## Non-negotiables

These are the rules that make the report trustworthy. Everything else is
judgement.

1. **Read-only.** Never modify, reformat or "fix" a source file, and never touch
   the spec workbook. You are a reviewer, not a developer, in this task.
2. **Every row carries evidence**: file name, line number, and the actual line of
   code quoted. If you cannot point at a line, you do not have a finding.
3. **Separate "the code does X" from "X is correct."** Your job is the first one.
   Put doubts about the second in the notes column — that is where a reviewer's
   judgement belongs, and it is often the most useful thing in the report.
4. **Never PASS something the source cannot decide.** Posting behaviour, lock
   contention, reversal flows, config-dependent values, authorization objects,
   number ranges, printing — these need a system. Say so, and write the steps.
5. **When torn between two verdicts, choose the weaker one.** An
   over-cautious NEEDS SYSTEM costs someone ten minutes in SAP. A wrong PASS
   costs a production defect.

## Workflow

### Phase 0 — Find and confirm the inputs

Establish four things before analysing anything:

- **The spec**: which workbook, which sheet holds the test scenarios, and what
  date/version it carries.
- **The source**: which folder holds the *active* build. Projects like this often
  keep several build snapshots side by side (`BUILD 20260901`, `BUILD 20260909`,
  `BUILD 20260911 EDITABLE`, …). Ask or infer which one is under test and record
  it in the report — a verdict is only meaningful against a named revision.
- **The side documents**: `*.md`, findings notes, change logs, README files
  sitting next to the source. Read these *first*. They usually explain the
  deviations that the spec has not caught up with, and they will save you from
  reporting a deliberate design change as a defect.
- **The gap**: compare the spec's date to the source's. If the source is newer,
  assume the spec has drifted and expect SPEC STALE findings.

Then **dump the scenario sheet and show the user the extraction before you start
judging**. Twenty-odd rows of misread input produce twenty-odd worthless
verdicts, and the user is the cheapest possible check on whether the parse is
right. Use `scripts/dump_spec.py` and `scripts/extract_cases.py`.

### Phase 1 — Understand the spec sheet's shape

Spec workbooks are written for humans, and they carry three recurring traps.
`scripts/extract_cases.py` handles the mechanics; you still need to read the
result with your eyes open.

**Bilingual cells.** One cell often holds the same sentence twice, in two
languages. The separator varies: usually a line break (Indonesian line, then
English line), sometimes `" / "`. Do not split on `" / "` blindly — that
sequence also appears mid-sentence in things like `F4 / on-change` or
`invoice / payment`. The extractor defaults to the line-break heuristic and
leaves the raw text intact so nothing is lost.

**Appended as-built annotations.** Later spec revisions frequently bolt a note
onto the end of a cell, after a blank line, saying what was *actually* built —
"this was never built", "block DD-04 was dropped", "no freshness gate exists".
The extractor separates paragraph 1 (`primary`, the original scenario) from
paragraphs 2+ (`annotations`). This matters because those two things have very
different status, which brings us to the next point.

**Annotations are claims, not facts.** An as-built note is someone's summary of
the code at some earlier moment. Test it against the source like everything else.
Three outcomes, all useful:

| Annotation says | Source shows | Verdict |
|---|---|---|
| not built | genuinely absent | `NA` — now *confirmed*, not merely asserted |
| not built | it exists | `SPEC_STALE` — the most valuable kind of finding |
| built as described | it changed since | `SPEC_STALE` — describe the delta |

Reporting a scenario as N/A purely because the spec said so is exactly the
failure mode this skill exists to prevent.

**Sparse layouts.** These sheets typically have blank spacer columns, merged
title blocks, and several header rows. Column letters mean nothing; find the
header row *above* the first ID row and map by header text.

### Phase 2 — Map the source

Before judging individual cases, spend a little time building a mental index of
the program, because you will query it twenty times:

- Which include holds declarations (`_TOP`), which holds the subroutines
  (`_F01`), which hold screen flow logic (`_PBO`, `_PAI`), which is the Screen
  Painter export.
- The names of the FORMs / METHODs and roughly what each does.
- Where the validations live, where the database writes live, where the external
  calls (BAPI, RFC, FM) live.

`references/evidence-patterns.md` is the lookup table for "the expected result
talks about X — where in ABAP does X leave a trace?". Read it when a scenario's
subject is not obviously located: locking, commit/rollback, authority checks,
number ranges, F4 help, ALV events, message handling, BDC, update task,
selection screens, conversion exits. Consult it rather than guessing.

Use `scripts/find_evidence.py` for the searches — it reports `file:line:code`,
is CRLF-safe, and crucially can **exclude or isolate ABAP comments**. That
distinction decides real verdicts: code commented out with `*` in column 1 is
*absence of behaviour*, and citing it as if it were live code is a serious
error. Conversely, `--only-comments` is the fastest way to confirm a feature was
deliberately disabled rather than never written.

### Phase 3 — Adjudicate

For each scenario, in order:

1. Restate the expected result as one or more **checkable claims**. If the
   expected result bundles three independent behaviours, treat them as three —
   and if they land on different verdicts, split the row (`UT-06a`, `UT-06b`)
   rather than averaging them into a mush. Good specs already do this ("two
   variants: (a) lock collision, (b) stale lookup").
2. Search for each claim's trace in the source.
3. Assign the verdict from the vocabulary below.
4. Record evidence: every claim you settled gets at least one `file:line` plus
   the quoted line. Quote the line that *decides* it, not its neighbour.
5. Write the note: the deviation, the doubt, the dependency, the reason a
   stronger verdict was not available.

#### Verdict vocabulary

Six codes; use these exact codes in the JSON. The workbook renders them in the
report language.

| Code | Indonesian label | English label | Meaning |
|---|---|---|---|
| `PASS` | LULUS | PASS | Source proves the behaviour matches the expected result |
| `FAIL` | GAGAL | FAIL | Source proves the behaviour contradicts it |
| `NA` | N/A | N/A | The feature genuinely was not built — **confirmed in source**, not merely claimed by the spec |
| `NEEDS_SYSTEM` | PERLU SISTEM | NEEDS SYSTEM | Undecidable from source; test steps supplied |
| `SPEC_STALE` | SPEC BASI | SPEC STALE | The spec row no longer matches the code because the code moved on; the delta is explained |
| `BLOCKED` | TERBLOKIR | BLOCKED | Cannot be assessed at all — the relevant source was not provided |

`BLOCKED` is for missing inputs (an include you were never given, a called
function module outside the folder). It is not a softer `NEEDS_SYSTEM`; it is an
admission that the analysis has a hole, and it tells the user exactly which file
to hand over.

`NEEDS_SYSTEM` rows must carry **concrete, executable test steps** — transaction,
data conditions, what to do, what to observe. "Test this in SAP" helps nobody.
Write what you would write for a tester who has never read the spec.

`SPEC_STALE` rows are the ones people actually read the report for. Spell out
three things: what the spec expects, what the code does now, and — if you can
find it in the side documents or the code comments — why it changed.

### Phase 4 — Build the workbook

Write a `verdicts.json` (schema in `references/report-format.md`) and run:

```bash
python scripts/build_report.py verdicts.json --out "Test Report.xlsx" --lang id
```

The script builds all three sheets, applies filters, freeze panes, wrapping and
verdict colouring, and **refuses to write a workbook whose rows break the
evidence rules** — a `PASS`/`FAIL`/`NA`/`SPEC_STALE` row with no evidence, or a
`NEEDS_SYSTEM` row with no test steps, is an error rather than a warning. That
check exists because those are precisely the rows that get quietly waved through
under time pressure. If a row genuinely cannot carry evidence, that is what
`BLOCKED` is for.

Use `--lang id` when the user writes in Indonesian, `--lang en` otherwise. The
language only affects headings and verdict labels; your prose goes in the JSON
in whatever language the user is using.

### Phase 5 — Report back

In chat, keep it short and lead with what changes someone's plans:

- the verdict tallies for test cases and gates,
- every `SPEC_STALE` finding, one line each — this is the headline,
- the size of the manual test queue,
- anything `BLOCKED` and which file would unblock it.

Do not paste the whole table into chat; that is what the workbook is for.

## Output workbook

Three sheets. Sheet and column names follow `--lang`.

**Summary** — run date, program, transaction, spec file/sheet/version, source
folder and revision; verdict counts for test cases and for gates, side by side;
the SPEC STALE findings list; the NEEDS SYSTEM queue; and any BLOCKED items. The
counts are live `COUNTIF` formulas, so they stay correct if someone edits a
verdict in place.

**Test Cases** — `No | Test Case | Covers | Expected Result | Verdict | Evidence
(file:line) | Code Quote | Notes / Deviation`

**Build Gates** — `No | Gate | Verdict | Evidence | Notes`

Build gates are usually about SAP configuration rather than code — tax-type
settings, posting-time classification, authorization, number ranges. Most will
legitimately be `NEEDS_SYSTEM`. Say so plainly; a gate sheet that is honestly
mostly "check this in the system" is more useful than one padded with
speculation. Where the code *does* imply something about a gate (a hardcoded
filter, a selection on a config table), cite it — that is real evidence about
what the program assumes the configuration to be.

Verdicts live in their own column so the sheet can be filtered. Colour is applied
as a reading aid only; the text always states the verdict, because colour does
not survive printing, copy-paste, or colour-blind readers.

## Environment notes

These have cost real time before.

- **Terminal encoding.** Windows consoles are frequently cp1252 and will crash on
  the em-dashes, arrows and curly quotes that live in spec cells. Never `print()`
  spreadsheet content. The bundled scripts write UTF-8 files and keep stdout
  ASCII-safe; read the file afterwards.
- **openpyxl**: `load_workbook(path, read_only=True, data_only=True)` — read-only
  for speed on large workbooks, `data_only` so you get cached values rather than
  formula strings. Note that `read_only=True` does not expose merged-cell ranges;
  `dump_spec.py --no-readonly` covers the rare case where you need them.
- **ABAP sources are CRLF.** Read with universal newlines; if you ever write ABAP
  back out (you should not, in this task), use `newline='\r\n'`.
- **Create scripts with the Write tool**, not shell heredocs. Repeated heredoc
  quoting through PowerShell/Git-Bash layers mangles files, and a silently
  corrupted analysis script is hard to notice.
- **Line numbers are 1-based** and must match what the user sees in SE38/ADT.
  The bundled scripts already do this; if you hand-count, check against the
  script.

## Bundled resources

| Path | Use it when |
|---|---|
| `scripts/dump_spec.py` | First contact with a spec workbook: list sheets, dump any sheet to a UTF-8 text file you can read safely |
| `scripts/extract_cases.py` | Turn a scenario sheet into `cases.json` — IDs, columns mapped by header, bilingual split, primary vs as-built annotations |
| `scripts/find_evidence.py` | Search the ABAP tree for `file:line:code` evidence, with comment-aware filtering |
| `scripts/build_report.py` | Write the final workbook from `verdicts.json`, with rule enforcement |
| `references/report-format.md` | The `verdicts.json` schema and workbook layout details |
| `references/evidence-patterns.md` | "Where does this kind of expected result leave a trace in ABAP?" — read when a scenario's subject is not obviously located |

Run any script with `--help` for its full options.
