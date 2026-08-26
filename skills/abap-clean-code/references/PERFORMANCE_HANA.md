# Performance on SAP HANA — Code-to-Data

> **Source**: ABAP Keyword Documentation (help.sap.com/doc/abapdocu_latest_index_htm), github.com/SAP/styleguides, github.com/SAP-samples/abap-cheat-sheets, SAP-samples RAP/Fiori reference apps, developers.sap.com tutorials.
> Confidence markers used below: `[OK]` = verified against an authoritative source cited inline; `[~]` = widely used and consistent with sources but not verbatim-confirmed; `[?]` = uncertain, verify in the target system before shipping.

## Contents

- [B. Performance Rules for ABAP on HANA (code-to-data)](#b-performance-rules-for-abap-on-hana-code-to-data)
  - [B.1 The five golden rules of Open SQL (SAP's canonical list)](#b1-the-five-golden-rules-of-open-sql-saps-canonical-list)
  - [B.2 What to push down vs. keep in ABAP](#b2-what-to-push-down-vs-keep-in-abap)
  - [B.3 Internal table type and key selection `[✓]`](#b3-internal-table-type-and-key-selection)
  - [B.4 Loop and access rules `[✓]`](#b4-loop-and-access-rules)
  - [B.5 Package-size processing, restartability, parallelization](#b5-package-size-processing-restartability-parallelization)
  - [B.6 Analysis tooling to reference in the skill](#b6-analysis-tooling-to-reference-in-the-skill)

---

## B. Performance Rules for ABAP on HANA (code-to-data)

### B.1 The five golden rules of Open SQL (SAP's canonical list)

These predate HANA but SAP restates them for HANA; rules 1, 2 and 5 gain weight, rule 4 (index/search overhead) loses weight because HANA scans columns fast. `[~ / ✓]` — the wording below is the widely-published SAP formulation, cross-checked against [32_Performance_Notes.md](https://github.com/SAP-samples/abap-cheat-sheets/blob/main/32_Performance_Notes.md) and [SOH remediation](https://sapabapcentral.blogspot.com/2019/09/soh-abap-code-remediation-rules-to-be-followed.html).

1. **Keep the result set small** — WHERE clause on the DB, not `CHECK`/`EXIT` in the loop. Never fetch-then-discard.
2. **Minimize the amount of transferred data** — explicit field list (never `SELECT *`), aggregates on the DB, `UPDATE ... SET` instead of read-modify-write.
3. **Reduce the number of database accesses** — no SELECT inside LOOP; array/bulk operations (`INSERT ... FROM TABLE`); one JOIN instead of n singles.
4. **Minimize search overhead** — index-supporting WHERE conditions, correct field order; *less critical on HANA*.
5. **Keep unnecessary load away from the database** — use the table buffer, avoid `ORDER BY`/`DISTINCT` when the app server can do it cheaply, avoid `SELECT` on buffered tables with buffer-bypassing additions.

And the **HANA-specific additions** `[✓]`:
6. **`SELECT SINGLE` requires a unique WHERE** (all key fields, `=`) — otherwise the result is arbitrary.
7. **No implicit sort order** — add `ORDER BY` (or `ORDER BY PRIMARY KEY`) wherever order matters.
8. **Secondary indexes were largely dropped** in the HANA migration — remove `DB_EXISTS_INDEX`-style checks and index hints.
9. **Pool/cluster tables became transparent tables** — code that read them as clusters must be reworked.
10. **No native SQL** (`EXEC SQL`, DB-specific ADBC) — it is not portable and blocks cloud readiness.

### B.2 What to push down vs. keep in ABAP

**Push down to CDS / ABAP SQL / AMDP:**
- Joins across more than two tables; aggregation, grouping, `HAVING`
- Filtering and set arithmetic (`UNION`, `EXISTS`, `IN` subqueries)
- Calculated columns, `CASE`, currency/unit conversion (`CURRENCY_CONVERSION`, `UNIT_CONVERSION` CDS functions)
- Ranking / top-N / running totals (window expressions)
- Hierarchy processing (CDS hierarchies, `HIERARCHY( )`)
- Text/description joins via associations
- Anything that reduces row or column count before transfer

**Keep in ABAP:**
- Business rules, validations, workflow decisions, orchestration
- Anything requiring authorization objects beyond DCL, buffered config lookups, BAPI/BOR calls
- Logic that needs to be unit-tested with test doubles
- Small, per-instance calculations on already-fetched data
- Anything that would make the CDS view unmaintainable or non-reusable

**Rule of thumb for the skill:** ABAP SQL/CDS first → CDS table function/AMDP only when SQLScript features (imperative logic, `CE_` functions, procedures) are genuinely required. AMDP couples you to HANA and is harder to test; it is a last resort, not a first choice.

### B.3 Internal table type and key selection `[✓]`

| Need | Type |
|---|---|
| Sequential processing, small tables, append-heavy | `STANDARD` |
| Frequent key reads **and** sorted output, partially-qualified key access | `SORTED` (binary search, log n) |
| Very frequent single reads on the **full** key, rarely modified | `HASHED` (constant time) |

```abap
TYPES: BEGIN OF ty_row,
         carrid TYPE s_carr_id,
         connid TYPE s_conn_id,
         fldate TYPE s_date,
         price  TYPE s_price,
       END OF ty_row.

" Explicit keys — NEVER use DEFAULT KEY (Clean ABAP) [✓]
TYPES ty_sorted TYPE SORTED TABLE OF ty_row
       WITH UNIQUE KEY carrid connid fldate.

TYPES ty_hashed TYPE HASHED TABLE OF ty_row
       WITH UNIQUE KEY carrid connid fldate.

" Standard table + secondary key: read-optimized without losing append order
TYPES ty_std TYPE STANDARD TABLE OF ty_row
       WITH EMPTY KEY
       WITH NON-UNIQUE SORTED KEY by_carrier COMPONENTS carrid
       WITH UNIQUE HASHED KEY by_full       COMPONENTS carrid connid fldate.

READ TABLE lt_std WITH TABLE KEY by_full COMPONENTS
     carrid = 'AA' connid = '0017' fldate = lv_date INTO DATA(ls_hit).
LOOP AT lt_std USING KEY by_carrier WHERE carrid = 'AA' INTO DATA(ls_l).
ENDLOOP.
DATA(ls_x) = lt_std[ KEY by_full carrid = 'AA' connid = '0017' fldate = lv_date ].
```

Secondary keys: worth it when the table is **large, filled once, rarely modified, read often**; keep the number of key components low; every modification maintains all secondary keys (cost), and there is a lazy-update/"key administration" overhead. `[✓]`

### B.4 Loop and access rules `[✓]`

```abap
" DO: filter in the LOOP header
LOOP AT lt_sorted WHERE comp1 = 800 AND comp2 = '800'.   " key fields, '=' , AND
ENDLOOP.

" DON'T: fetch everything then CONTINUE
LOOP AT lt_std.
  IF comp1 > 800. CONTINUE. ENDIF.
ENDLOOP.

" Deep structures: use ASSIGNING / REFERENCE INTO, not INTO (avoids a copy)
LOOP AT lt_deep ASSIGNING FIELD-SYMBOL(<ls>) WHERE comp1 < 200.
  <ls>-counter += 1.                 " no MODIFY needed
ENDLOOP.

" If you must MODIFY, restrict the transfer
LOOP AT lt_deep INTO DATA(ls_d) WHERE comp1 < 400.
  ls_d-counter += 1.
  MODIFY lt_deep FROM ls_d TRANSPORTING counter.
ENDLOOP.

" Existence check: line_exists is cheaper than a full READ into a work area
IF line_exists( lt_tab[ id = lv_id ] ).

" SORT: always name the key explicitly
SORT lt_tab BY carrid ASCENDING connid DESCENDING.   " never bare SORT lt_tab

" Memory: CLEAR keeps allocated memory (good for refill), FREE releases it
CLEAR lt_tab.   " will be repopulated
FREE  lt_tab.   " done with it, large table
```

Also: prefer `INSERT INTO TABLE` over `APPEND TO` (works for all table kinds, Clean ABAP); pass large tables **by reference** (`TYPE`/`REFERENCE TO`), not `VALUE( )`; prefer static over dynamic (`('FIELDLIST')`) specifications; avoid regex (`FIND ... PCRE`) for fixed-string comparisons; avoid mixed-type arithmetic (implicit conversions).

### B.5 Package-size processing, restartability, parallelization

```abap
" Package-wise read: bounded memory for very large result sets
SELECT carrid, connid, fldate, price
  FROM sflight
  INTO TABLE @DATA(lt_pkg) PACKAGE SIZE 50000.
  PERFORM_transform_and_post( lt_pkg ).
  COMMIT WORK.                          " one LUW per package = restartable
  CLEAR lt_pkg.
ENDSELECT.
```

Notes for the skill:
- `PACKAGE SIZE` holds a **database cursor open** across the loop; do not issue a `COMMIT WORK` inside a `SELECT ... ENDSELECT` on all DBs — the cursor may be invalidated. `[?]` **Safer pattern:** read keys in chunks by key range (`WHERE id > @lv_last_id ... UP TO n ROWS ORDER BY id`), then process+commit per chunk. Verify the cursor/commit behavior for your DB before recommending the `ENDSELECT`+`COMMIT` shape.
- Keep the commit interval configurable via a selection-screen parameter (e.g. `p_pkg TYPE i DEFAULT 5000`).
- Persist a restart marker (last processed key) in a Z-table so a cancelled job resumes instead of restarting.
- **Parallelization options, in order of preference:**
  1. Push the work down so it doesn't need parallelizing.
  2. `SUBMIT ... VIA JOB` with disjoint key ranges (simple, transparent, restartable).
  3. bgRFC units (`CALL FUNCTION ... IN BACKGROUND UNIT`) — modern, monitorable in `SBGRFCMON`.
  4. `CALL FUNCTION ... STARTING NEW TASK ... DESTINATION IN GROUP ... CALLING <cb> ON END OF TASK` (aRFC) — needs manual resource management (`rzlli_apcl`, free-work-process checks) and is easy to get wrong. `[~]`
  5. `cl_abap_parallel` (7.54+) — the modern OO wrapper; subclass and implement `do( )`. `[?]` Verify availability/release for the target system.
  - Each parallel unit must be a **separate LUW with disjoint data**; number-range and lock contention is the usual killer.

### B.6 Analysis tooling to reference in the skill
- **SAT** (single transaction analysis, replaces SE30), **ST05** (SQL trace), **ST12**, **SQLM** + **SWLT** (SQL Monitor + Code Inspector worklist — the standard "find the expensive custom SQL in production" workflow), **ATC** (`S4HANA_READINESS`, `ABAP_CLOUD_READINESS` check variants), **SYCM** (Custom Code Migration app), **ADT ABAP Profiler**, **SE30/SAT runtime check**, HANA **PlanViz** for pushdown verification.

---
