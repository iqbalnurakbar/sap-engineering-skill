# Where does this expected result leave a trace in ABAP?

A lookup table for Phase 2/3: you have a scenario, you need the line of code
that settles it. Each entry gives the search terms, what a hit proves, and —
more importantly — what a hit does *not* prove, because that boundary is where
the difference between `PASS` and `NEEDS_SYSTEM` lives.

## Contents

1. [Program layout: which include holds what](#1-program-layout)
2. [Screen behaviour, field rules, mandatory fields](#2-screen-behaviour)
3. [Validation and messages](#3-validation-and-messages)
4. [Database reads and selection logic](#4-database-reads)
5. [Database writes, commit, rollback, atomicity](#5-database-writes)
6. [Locking and concurrency](#6-locking-and-concurrency)
7. [Calls out: BAPI, RFC, function modules, BDC](#7-calls-out)
8. [Authorization](#8-authorization)
9. [ALV grids and events](#9-alv-grids-and-events)
10. [Arithmetic, rounding, currency decimals](#10-arithmetic-and-currency)
11. [Configuration-dependent behaviour](#11-configuration-dependent-behaviour)
12. [Proving absence: how to be sure something was never built](#12-proving-absence)
13. [What source can never decide](#13-what-source-can-never-decide)

---

## 1. Program layout

Classic module-pool / report builds split into includes by convention:

| Suffix | Holds | Search here for |
|---|---|---|
| `_TOP` | `DATA`, `TABLES`, `CONSTANTS`, `TYPES`, screen field declarations | field existence, types, initial values, constants that encode business rules |
| `_F01`, `_FXX` | `FORM` / `PERFORM` subroutines | virtually all business logic |
| `_PBO`, `_O01` | `MODULE ... OUTPUT` | field visibility, greying out, titles, GUI status |
| `_PAI`, `_I01` | `MODULE ... INPUT` | ok_code handling, mandatory checks, navigation |
| `_9001` (bare number) | Screen Painter export | the screen's actual field list and attributes |
| `_CL01` / local classes | event handlers, ALV handlers | `handle_data_changed`, `handle_toolbar` |

Start by listing `FORM `, `MODULE `, `METHOD ` across the tree — that index pays
for itself over twenty scenarios:

```bash
python scripts/find_evidence.py --root <src> -p "^\s*(FORM|MODULE|METHOD)\s" --skip-comments
```

A Screen Painter export is the authority on which fields *exist on the screen*.
If the spec talks about a field and the export does not contain it, that is
strong evidence — stronger than the absence of the field in the ABAP, because
a field can exist on screen and simply not be referenced.

## 2. Screen behaviour

| Scenario talks about | Search | Caveat |
|---|---|---|
| field mandatory | `LOOP AT SCREEN`, `screen-required`, `obligatory` | screen-painter "required" attribute lives in the `_9001` export, not the ABAP — check both |
| field hidden/greyed | `screen-input`, `screen-invisible`, `screen-active`, `MODIFY SCREEN` | usually inside `LOOP AT SCREEN ... ENDLOOP` in PBO |
| title / header text | `SET TITLEBAR`, `SET PF-STATUS` | the text itself lives in a text element, not the code — a title claim may need the system |
| button / menu function | `ok_code`, `sy-ucomm`, `CASE ok_code` | the function code is in the GUI status (SE41), invisible in source. A missing `WHEN 'XYZ'` proves the program ignores it; a present one does not prove the button exists |
| F4 help | `F4IF_INT_TABLE_VALUE_REQUEST`, `PROCESS ON VALUE-REQUEST`, `VALUE-REQUEST FOR` | |
| tabstrip / subscreen | `CALL SUBSCREEN`, `TABSTRIP`, `SUBSCREEN` | |
| field removed from screen | absent from the `_9xxx` export **and** commented out in the ABAP | this pair is the cleanest possible "not built any more" evidence |

## 3. Validation and messages

Search `MESSAGE`, `MESSAGE ... TYPE`, `RAISE`, `SET CURSOR`, `FIELD ... MODULE`.

The **message type letter decides the behaviour**, and this is a frequent source
of `SPEC_STALE` findings:

- `TYPE 'E'` in a PAI module — blocks, returns to the field.
- `TYPE 'W'` — warns; the user presses Enter and continues. If the spec says
  "posting is blocked" and the code says `TYPE 'W'`, the spec is wrong or the
  code is — either way it is a finding, not a PASS.
- `TYPE 'S'` — status line only, never blocks.
- `TYPE 'A'` / `'X'` — abort / dump.
- `MESSAGE ... RAISING` inside a function module — the exception matters more
  than the text.

Watch for literal message texts (`MESSAGE 'Enter the invoice number.' TYPE 'W'`)
versus message-class references (`MESSAGE e012(zfi)`). Literals are fully
verifiable from source; class references need SE91 to confirm the text, so quote
the line and note that the wording needs the system.

## 4. Database reads

Search `SELECT`, `SELECT SINGLE`, `FOR ALL ENTRIES`, `READ TABLE`, table names.

What a `SELECT` proves: which table, which key fields, which filter. That is
often exactly what a scenario asks ("only invoice-time types are staged" →
find the `WHERE` clause pinning the posting-time field).

What it does not prove: that the data exists, that the index is used, that the
result is non-empty in the test client.

Look hard at `WHERE` clauses that encode business rules as literals — a
hardcoded `WT_POSTM = '1'` *is* the rule, and citing it is much stronger
evidence than citing a comment that describes the rule.

## 5. Database writes

Search `INSERT`, `UPDATE`, `MODIFY`, `DELETE`, `COMMIT WORK`, `ROLLBACK WORK`,
`IN UPDATE TASK`, `PERFORM ... ON COMMIT`, `SET UPDATE TASK LOCAL`.

Atomicity scenarios turn on the *ordering*: is the status flag updated before or
after the document posts, and are both inside the same LUW? You can read the
ordering from source and should report it. You cannot read what happens when the
update task fails halfway — that is `NEEDS_SYSTEM`.

`COMMIT WORK AND WAIT` versus plain `COMMIT WORK` matters whenever a scenario
says "the next step immediately sees the result".

## 6. Locking and concurrency

Search `ENQUEUE_`, `DEQUEUE_`, `CALL FUNCTION 'ENQUEUE_E`, `_SCOPE`,
`FOREIGN_LOCK`, `SY-SUBRC` right after an enqueue.

Source proves: that a lock is requested, on which object, with which scope, and
whether `sy-subrc <> 0` is actually handled (a lock whose return code is ignored
is a genuine `FAIL` you can prove).

Source cannot prove: who wins a real race, whether the lock granularity is
sufficient under load, what a second user sees. Concurrency scenarios are
`NEEDS_SYSTEM` almost every time — but the *steps* you write should name the
lock object you found, which makes the manual test much faster.

## 7. Calls out

| Kind | Search | Notes |
|---|---|---|
| BAPI | `CALL FUNCTION 'BAPI_`, `BAPI_TRANSACTION_COMMIT` | check whether `RETURN` is inspected for `TYPE = 'E'`; an ignored RETURN table is a provable defect |
| RFC | `DESTINATION`, `CALL FUNCTION ... DESTINATION` | destination names are config — note it |
| Custom FM | `CALL FUNCTION 'Z` | if the FM source is in the folder, follow it; if not, that part of the scenario may be `BLOCKED` |
| BDC | `BDC_DYNPRO`, `BDCDATA`, `CALL TRANSACTION`, `MODE`, `UPDATE` | BDC behaviour depends on the target screen sequence; source proves the intent, not the outcome |
| Batch input session | `BDC_OPEN_GROUP`, `BDC_INSERT`, `BDC_CLOSE_GROUP` | |
| Email / output | `SO_NEW_DOCUMENT`, `cl_bcs`, `NAST`, `OPEN_FORM`, `FP_JOB_OPEN` | |

## 8. Authorization

Search `AUTHORITY-CHECK`, `OBJECT '`, `ID '`, `FIELD `, and `sy-subrc` handling
straight after.

Source proves which object and fields are checked and whether the return code is
evaluated. It cannot prove which roles a tester has. Authorization scenarios are
usually a split: the *check exists* half is provable, the *user X is refused*
half is `NEEDS_SYSTEM`.

## 9. ALV grids and events

Search `cl_gui_alv_grid`, `set_table_for_first_display`, `refresh_table_display`,
`register_edit_event`, `handle_data_changed`, `check_changed_data`,
`get_selected_rows`, `SET HANDLER`, field catalog build (`lvc_s_fcat`, `edit = 'X'`).

Editable-column scenarios hinge on the field catalog `edit` flag plus a
registered `data_changed` event. Both must be present; one without the other is
a provable defect.

Scenarios about "the total updates when I tick the box" usually resolve to a
round-trip trick — an event handler injecting an ok_code, or
`check_changed_data` being called before recalculation. Find that mechanism and
quote it; it is the kind of evidence that reads as genuinely informed.

## 10. Arithmetic and currency

Search the calculation FORM, plus `ROUND`, `CEIL`, `FLOOR`, `DIV`, `MOD`,
`CURRENCY_AMOUNT_SAP_TO_BAPI`, `BAPI_CURRENCY_CONV_TO_EXTERNAL`,
`CURRENCY_CONVERSION`, `TCURX`.

Decimal-shift scenarios (currencies with 0 decimals like IDR and JPY) are the
classic trap: an amount moved between an internal `CURR` field and a BAPI
structure without the conversion FM shifts by a factor of 100. If the conversion
call is absent on a path that needs it, that is a provable `FAIL`; if present,
quote it and let the numeric proof be `NEEDS_SYSTEM`.

Also check *which field* feeds the base of a calculation. Scenarios often say
"base is the goods value, never the gross" — that is a one-line proof in the
calculation FORM, and one of the most valuable things a source review can settle.

## 11. Configuration-dependent behaviour

Tax codes, withholding types, posting-time classification, tolerance groups,
number ranges, document types, output determination — the program *reads* these;
it does not define them.

Source can prove: which config table is read, which fields are filtered, what
the program does for each value it handles, and what it does with values it does
not handle (silently ignoring an unexpected value is a real finding).

Source cannot prove: what the config actually contains in any client. That half
is `NEEDS_SYSTEM`, and the test step should name the exact table and key
(`T059Z`, `V_T001WT`, `TNRO`, …) so the tester can go straight there.

Most build gates live in this section. That is why a gate sheet that is honestly
mostly `NEEDS_SYSTEM` is correct rather than lazy — as long as each row names
the table or transaction to check.

## 12. Proving absence

Concluding "this was never built" is a positive claim and needs the same rigour
as any other. Before writing `NA`:

1. Search for every plausible spelling — the object name, the field name, the
   flag name, the message number, the transaction code, the title text.
2. Search with `--only-comments`. A commented-out block means the feature was
   built and then disabled: the evidence is the commented line, and the verdict
   is usually `NA` *with a note that it was removed*, or `SPEC_STALE` if the
   spec still promises it.
3. Check the screen export as well as the ABAP.
4. Record the searches you ran in the notes. "No hit for `ZINV_VER_NFP`,
   `gv_nonfp`, or `Non Faktur Pajak` in any include" is evidence; silence is
   not.

## 13. What source can never decide

Write `NEEDS_SYSTEM` and useful steps for anything that depends on:

- actual posting, document numbers, reversal (MR8M, FB08) and re-posting;
- concurrent users, lock collisions, stale-read races;
- config content: rates, tax types, tolerance, number ranges, account
  determination;
- authorization objects assigned to a real user;
- data-dependent outcomes (does this vendor have an open GR? is this invoice
  already assessed?);
- performance, dialog timeouts, background scheduling;
- anything rendered by SAPscript / Smart Forms / Adobe output;
- GUI status and titlebar texts maintained outside the source.

A good `NEEDS_SYSTEM` row names the transaction, the data precondition, the
action, and the observation. If you found the lock object, the config table or
the message id while searching, put it in the steps — the tester should not have
to repeat your search.
