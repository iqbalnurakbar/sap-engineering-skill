# Modern ABAP Syntax (7.40 → 7.58 / ABAP Cloud)

> **Source**: ABAP Keyword Documentation (help.sap.com/doc/abapdocu_latest_index_htm), github.com/SAP/styleguides, github.com/SAP-samples/abap-cheat-sheets, SAP-samples RAP/Fiori reference apps, developers.sap.com tutorials.
> Confidence markers used below: `[OK]` = verified against an authoritative source cited inline; `[~]` = widely used and consistent with sources but not verbatim-confirmed; `[?]` = uncertain, verify in the target system before shipping.

## Contents

- [A. Modern ABAP Syntax Cheatsheet (7.40 → 7.58 / ABAP Cloud)](#a-modern-abap-syntax-cheatsheet-740-758-abap-cloud)
  - [A.0 Release mapping (needed for "can I use this?" answers)](#a0-release-mapping-needed-for-can-i-use-this-answers)
  - [A.1 Inline declarations](#a1-inline-declarations)
  - [A.2 Constructor expressions (complete set)](#a2-constructor-expressions-complete-set)
  - [A.3 Table comprehensions](#a3-table-comprehensions)
  - [A.4 String templates & expressions](#a4-string-templates-expressions)
  - [A.5 ABAP SQL, modern form](#a5-abap-sql-modern-form)
  - [A.6 Grouping (`LOOP AT ... GROUP BY`)](#a6-grouping-loop-at-group-by)
  - [A.7 Exception classes, RESUMABLE, ASSERT, MESSAGE INTO](#a7-exception-classes-resumable-assert-message-into)

---

## A. Modern ABAP Syntax Cheatsheet (7.40 → 7.58 / ABAP Cloud)

### A.0 Release mapping (needed for "can I use this?" answers)

| ABAP Platform / S/4HANA | ABAP language version |
|---|---|
| NW 7.40 (2012) | first constructor expressions, inline decls, string templates |
| NW 7.50 / 7.51 / 7.52 | `FILTER`, `REDUCE`, itab as SQL data source (7.52) |
| S/4HANA 1909 = AS ABAP 7.54 | `xsdbool` everywhere, CDS view entities groundwork |
| S/4HANA 2020 = 7.55 | **CDS view entities** (`DEFINE VIEW ENTITY`), `USING CLIENT` |
| S/4HANA 2021 = 7.56 | RAP maturity, `strict(1)` |
| S/4HANA 2022 = 7.57 | `strict(2)`, `ANNOTATE ENTITY` |
| S/4HANA 2023 = 7.58 | further RAP/CDS additions |

`[~]` This 1909→7.54 … 2023→7.58 mapping is the standard industry mapping. **`[?]`** Note the cheat sheet's *ABAP Release News* file uses a *different* numbering (7.84 / 7.87 / 7.90 / 7.93 / 7.96 mapped to 2202/2211/2308/2405) — that is the **ABAP Cloud / BTP steampunk** kernel line, not the on-premise line. Do not mix the two in the skill's guidance. Source: [33_ABAP_Release_News.md](https://github.com/SAP-samples/abap-cheat-sheets/blob/main/33_ABAP_Release_News.md).

Notable newer elements from that file `[✓]`:
- `FINAL` declaration operator (immutable inline variable) — ABAP Cloud 7.87 / 2202. **`[?]` verify on-prem availability.**
- `RETURN expr.` to assign the return value and exit in one statement — 7.90 / 2211.
- Dynamic component access `struc-(comp)` — 7.87 / 2202.
- Fully dynamic `SELECT` clauses — 7.96 / 2405.

### A.1 Inline declarations

```abap
" Local variable, type inferred at write position
DATA(lv_text) = `This is a string`.       " type string
DATA(lv_count) = 0.                        " type i

" Loop targets
LOOP AT lt_accounts INTO DATA(ls_account).
ENDLOOP.

LOOP AT lt_accounts ASSIGNING FIELD-SYMBOL(<ls_account>).
  <ls_account>-amount += 1.
ENDLOOP.

LOOP AT lt_accounts REFERENCE INTO DATA(lr_account).
  lr_account->amount += 1.
ENDLOOP.

" Method outputs
lo_reader->read( IMPORTING et_result = DATA(lt_result) ).

" SQL host expression (note the escaping @)
SELECT carrid, carrname
  FROM scarr
  WHERE carrid = @lv_carrid
  INTO TABLE @DATA(lt_carriers).

" Compound assignment operators (7.54+)
lv_count += 1.
lv_text  &&= ` more`.
```

Clean ABAP rules `[✓]`: prefer inline declaration to up-front `DATA` blocks; do **not** use Hungarian notation / type prefixes; do not use `MOVE`, `CREATE OBJECT`, `DESCRIBE TABLE ... LINES`, `GET REFERENCE OF` — use `=`, `NEW`, `lines( )`, `REF #( )`.

### A.2 Constructor expressions (complete set)

Verbatim patterns from [05_Constructor_Expressions.md](https://github.com/SAP-samples/abap-cheat-sheets/blob/main/05_Constructor_Expressions.md) `[✓]`:

```abap
" ---------- VALUE ----------
ls_struc = VALUE #( a = 1 b = 'aaa' ).
DATA(lt_tab) = VALUE ty_tab( ( a = 5 b = 'eee' )
                             ( a = 6 b = 'fff' ) ).

" BASE keeps existing content
ls_struc = VALUE #( BASE ls_struc b = 'bbb' ).
lt_tab   = VALUE #( BASE lt_tab ( a = 3 b = 'ccc' ) ).

" LINES OF appends whole tables / ranges
lt_tab = VALUE #( ( a = 1 b = 'aaa' )
                  ( LINES OF lt_other )
                  ( LINES OF lt_other FROM 2 TO 4 ) ).

" Nested structures
ls_nested = VALUE #( a = 1 struct = VALUE #( b = 1 c = 'aaa' ) ).

" "Grouped" short form: repeated component values hoisted
DATA(lt_grouped) = VALUE ty_tab( b = 'aaa' ( a = 1 c = `xxx` )
                                           ( a = 2 c = `yyy` )
                                 b = 'bbb' ( a = 3 )
                                           ( a = 4 ) ).

" Safe table read: OPTIONAL suppresses CX_SY_ITAB_LINE_NOT_FOUND
DATA(ls_line)  = VALUE #( lt_tab[ id = '4711' ] OPTIONAL ).
DATA(ls_line2) = VALUE #( lt_tab[ 1 ] DEFAULT VALUE #( a = 1 b = 'abc' ) ).

" ---------- NEW ----------
DATA(lo_obj)  = NEW zcl_worker( iv_id = '4711' ).
DATA(lr_int)  = NEW i( 456 ).
DATA(lr_tab)  = NEW string_table( VALUE #( ( `a` ) ( `b` ) ) ).
NEW zcl_worker( )->run( ).                        " chained, no variable

" ---------- CONV / EXACT ----------
DATA(lv_dec) = CONV decfloat34( 1 / 5 ).
TRY.
    DATA(lv_exact) = EXACT c3( 'abcd' ).          " lossless
  CATCH cx_sy_conversion_data_loss.
ENDTRY.
TRY.
    DATA(lv_calc) = EXACT p_dec2( 1 / 3 ).
  CATCH cx_sy_conversion_rounding.
ENDTRY.

" ---------- REF ----------
DATA(lr_line) = REF #( lt_tab[ 2 ] ).
DATA(lr_opt)  = REF #( lt_tab[ 6 ] OPTIONAL ).    " initial ref if absent

" ---------- CAST ----------
DATA(lo_sub) = CAST zcl_sub( lo_super ).
CAST zcl_sub( lo_super )->do_it( ).
DATA(lt_comp) = CAST cl_abap_structdescr(
                  cl_abap_typedescr=>describe_by_data( ls_struc ) )->components.

" ---------- COND / SWITCH ----------
DATA(lv_greeting) = COND #(
    LET lv_time = cl_abap_context_info=>get_system_time( ) IN
    WHEN lv_time BETWEEN '050001' AND '120000' THEN |Good morning|
    WHEN lv_time BETWEEN '120001' AND '180000' THEN |Good afternoon|
    ELSE |Good night| ).

DATA(lv_res) = SWITCH #( iv_operator
    WHEN '+' THEN iv_a + iv_b
    WHEN '-' THEN iv_a - iv_b
    ELSE THROW zcx_bad_operator( ) ).

" THROW / THROW SHORTDUMP inside COND/SWITCH
DATA(lv_div) = COND decfloat34( WHEN iv_b <> 0 THEN iv_a / iv_b
                                ELSE THROW cx_sy_zerodivide( ) ).

" ---------- FILTER ----------
DATA(lt_big)      = FILTER #( lt_src WHERE amount >= 4 ).
DATA(lt_bykey)    = FILTER #( lt_src USING KEY sec_key WHERE amount < 3 ).
DATA(lt_except)   = FILTER #( lt_src EXCEPT WHERE amount >= 4 ).
DATA(lt_bytab)    = FILTER #( lt_src IN lt_filter WHERE id = table_line ).
DATA(lt_bytab_ex) = FILTER #( lt_src EXCEPT IN lt_filter WHERE id = table_line ).

" ---------- REDUCE ----------
DATA(lv_sum) = REDUCE i( INIT sum = 0
                         FOR <ls> IN lt_tab
                         NEXT sum = sum + <ls>-amount ).

DATA(lv_max) = REDUCE i( INIT max = 0
                         FOR ls IN lt_tab
                         NEXT max = COND #( WHEN ls-amount > max
                                            THEN ls-amount ELSE max ) ).

DATA(lt_msgs) = REDUCE string_table(
    INIT r = VALUE string_table( )
    FOR ls IN lt_tab
    NEXT r = VALUE #( BASE r ( |Item { ls-id }: { ls-amount }| ) ) ).

" ---------- CORRESPONDING ----------
ls_target = CORRESPONDING #( ls_source ).
ls_target = CORRESPONDING #( BASE ( ls_target ) ls_source ).
ls_target = CORRESPONDING #( ls_source MAPPING dest_fld = src_fld ).
ls_target = CORRESPONDING #( ls_source EXCEPT b ).
ls_target = CORRESPONDING #( ls_source MAPPING d = c EXCEPT * ).   " only mapped
lt_target = CORRESPONDING #( lt_source DISCARDING DUPLICATES ).
ls_target = CORRESPONDING #( ls_source MAPPING id2 = id1
                                               b = DEFAULT `hallo`
                                               c = DEFAULT 1 + 5 ).
" Lookup-table variant (7.55+ [?]) — enrich a table from another
lt_a = CORRESPONDING #( lt_a FROM lt_lookup USING KEY sk c = a d = b
                             MAPPING f = g ).

" ---------- LET ----------
DATA(lv_hi) = CONV string(
  LET lv_user = cl_abap_context_info=>get_user_technical_name( )
      lv_date = cl_abap_context_info=>get_system_date( )
  IN |Hi { lv_user }. Today is { lv_date DATE = ISO }.| ).
```

### A.3 Table comprehensions

```abap
" FOR ... IN ... WHERE
DATA(lt_out) = VALUE ty_tab( FOR ls IN lt_in WHERE ( amount > 100 )
                             ( id = ls-id label = ls-name && '-x' ) ).

" FOR ... WHILE / UNTIL (index-driven generation)
DATA(lt_1) = VALUE ty_tab( FOR i = 1 WHILE i < 4 ( col1 = i col2 = i + 1 ) ).
DATA(lt_2) = VALUE ty_tab( FOR i = 10 UNTIL i > 12 ( col1 = i ) ).

" Table function shortcuts (Clean ABAP-preferred)
DATA(lv_lines)  = lines( lt_tab ).
IF line_exists( lt_tab[ id = 4711 ] ).
  DATA(lv_idx) = line_index( lt_tab[ id = 4711 ] ).
ENDIF.
DATA(lv_id) = lt_tab[ 5 ]-id.
```

### A.4 String templates & expressions

```abap
DATA(lv_msg) = |Order { lv_id ALPHA = OUT } created on { sy-datum DATE = USER }|
            && | for { lv_amount CURRENCY = 'EUR' NUMBER = USER }|.

" Common format options
|{ lv_ts    TIMESTAMP = ISO }|
|{ lv_date  DATE = ISO }|          " 2026-08-26
|{ lv_num   STYLE = SIMPLE }|      " no exponent, no leading spaces
|{ lv_x     WIDTH = 10 ALIGN = RIGHT PAD = '0' }|
|{ lv_text  CASE = UPPER }|
|{ to_upper( lv_text ) }|

" Prefer backquote literals over templates for constant text (perf) [✓]
DATA(lv_lit) = `ABAP literal`.

" String functions worth knowing
DATA(lv_a) = substring( val = lv_s off = 2 len = 3 ).
DATA(lv_b) = replace( val = lv_s sub = 'a' with = 'b' occ = 0 ).
DATA(lv_c) = condense( lv_s ).
DATA(lv_d) = segment( val = lv_s index = 2 sep = ',' ).
DATA(lv_e) = escape( val = lv_s format = cl_abap_format=>e_url_full ).
IF contains( val = lv_s sub = 'abc' ) OR matches( val = lv_s pcre = '^\d{4}$' ).
ENDIF.
```

### A.5 ABAP SQL, modern form

Verified against [03_ABAP_SQL.md](https://github.com/SAP-samples/abap-cheat-sheets/blob/main/03_ABAP_SQL.md) `[✓]`.

```abap
" Comma-separated field list, escaped host variables, inline target
SELECT carrid, connid, cityfrom
  FROM spfli
  WHERE carrid = @lv_carrid
    AND fltime > @( lv_base + 10 )      " host EXPRESSION uses @( ... )
  ORDER BY carrid, connid
  INTO TABLE @DATA(lt_flights).

" Strict "FIELDS" arrangement (INTO last) — recommended for readability
SELECT FROM spfli
  FIELDS carrid, connid
  WHERE carrid = @lv_carrid
  INTO TABLE @DATA(lt_2).

" SELECT SINGLE vs UP TO 1 ROWS
SELECT SINGLE FROM spfli FIELDS * WHERE carrid = @lv_c AND connid = @lv_n
  INTO @DATA(ls_one).                  " use ONLY with a fully-qualified key
SELECT FROM spfli FIELDS * WHERE carrid = @lv_c
  ORDER BY fltime DESCENDING
  INTO TABLE @DATA(lt_one) UP TO 1 ROWS.   " deterministic "first/best row"

" ORDER BY PRIMARY KEY
SELECT FROM spfli FIELDS carrid, connid ORDER BY PRIMARY KEY INTO TABLE @DATA(lt_3).

" JOINs
SELECT a~carrid, a~connid, b~fldate, b~seatsocc
  FROM spfli AS a
  INNER JOIN sflight AS b ON a~carrid = b~carrid AND a~connid = b~connid
  LEFT OUTER JOIN scarr AS c ON c~carrid = a~carrid
  WHERE a~carrid = @lv_carrid
  INTO TABLE @DATA(lt_join).

" CASE in the select list
SELECT carrid,
       CASE currcode WHEN 'EUR' THEN 'A'
                     WHEN 'USD' THEN 'B'
                     ELSE 'C' END AS bucket,
       CASE WHEN fltime > 500 THEN 'LONG' ELSE 'SHORT' END AS kind
  FROM scarr
  INTO TABLE @DATA(lt_case).

" Aggregates + GROUP BY + HAVING
SELECT carrid,
       COUNT(*)      AS cnt,
       AVG( fltime AS DEC( 10,2 ) ) AS avg_time,
       MAX( fltime ) AS max_time,
       SUM( distance ) AS total_dist
  FROM spfli
  GROUP BY carrid
  HAVING COUNT(*) > 5
  INTO TABLE @DATA(lt_agg).

" EXISTS / NOT EXISTS subquery — the FAE replacement
SELECT carrid, connid FROM spfli AS s
  WHERE EXISTS ( SELECT 'X' FROM sflight AS f
                 WHERE f~carrid = s~carrid AND f~connid = s~connid
                   AND f~seatsocc > 0 )
  INTO TABLE @DATA(lt_exists).

" UNION / UNION ALL
SELECT FROM spfli FIELDS carrid, connid WHERE carrid = 'AA'
UNION ALL
SELECT FROM spfli_arch FIELDS carrid, connid WHERE carrid = 'AA'
  INTO TABLE @DATA(lt_union).

" Common Table Expressions (WITH) — CTE names start with '+'
WITH
  +connections AS ( SELECT carrid, connid, cityfrom, cityto FROM spfli
                    WHERE carrid BETWEEN 'AA' AND 'JL' ),
  +counted AS ( SELECT carrid, COUNT(*) AS cnt FROM +connections GROUP BY carrid )
SELECT c~carrid, c~cnt, k~carrname
  FROM +counted AS c INNER JOIN scarr AS k ON k~carrid = c~carrid
  ORDER BY c~carrid
  INTO TABLE @DATA(lt_cte).

" Internal table as data source / join partner (7.52+)
SELECT t~carrid, s~carrname
  FROM @lt_keys AS t
  INNER JOIN scarr AS s ON s~carrid = t~carrid
  INTO TABLE @DATA(lt_itab_join).

" SQL functions & window expressions
SELECT SINGLE carrid,
       CAST( connid AS INT4 )                    AS connid_num,
       concat( carrid, carrname )                AS combined,
       coalesce( url, '-' )                      AS url_or_dash,
       dats_add_days( @sy-datum, 10, 'NULL' )    AS due_date,
       division( a, b, 2 )                       AS ratio,
       SUM( paymentsum ) OVER( PARTITION BY carrid )      AS carrier_total,
       ROW_NUMBER( ) OVER( PARTITION BY carrid ORDER BY connid ) AS rn
  FROM scarr WHERE carrid = 'AA' INTO @DATA(ls_fn).

" Set-based modification (always prefer over row-by-row)
INSERT ztab FROM TABLE @lt_new ACCEPTING DUPLICATE KEYS.
UPDATE ztab FROM TABLE @lt_chg.
MODIFY ztab FROM TABLE @lt_upsert.
UPDATE ztab SET status = 'X', changed_on = @sy-datum WHERE id < @lv_max.
DELETE FROM ztab WHERE carrid = @lv_carrid.
DELETE ztab FROM TABLE @lt_keys.
```

**FOR ALL ENTRIES — pitfalls and alternatives (high-value skill content)**

```abap
" The ONLY safe classic form
IF lt_keys IS NOT INITIAL.                     " else: FULL TABLE READ [✓]
  SELECT carrid, connid, fldate
    FROM sflight
    FOR ALL ENTRIES IN @lt_keys
    WHERE carrid = @lt_keys-carrid
    INTO TABLE @DATA(lt_res).
ENDIF.
```

Pitfalls to encode in the skill `[✓ / ~]`:
1. **Empty driver table ⇒ the WHERE clause is dropped ⇒ full table read.** Always guard. ([32_Performance_Notes.md](https://github.com/SAP-samples/abap-cheat-sheets/blob/main/32_Performance_Notes.md))
2. **Implicit DISTINCT on the result.** Rows that are identical across the selected field list are silently removed. If you don't select the full key, you lose data. Always select the complete key of the target table.
3. **The driver table is split into packages** (blocking factor, profile parameter `rsdb/max_blocking_factor`), so the statement is executed *n* times; result set order is undefined and DB statistics are per-package.
4. Cannot be combined with aggregate expressions, `GROUP BY`, `HAVING`, or `ORDER BY`. `[~]`
5. Driver field and DB field must be type-compatible; mismatched lengths cause silent truncation of the comparison.
6. **Preferred alternatives, in order:** (a) `INNER JOIN` / CDS view — push the join down; (b) `WHERE EXISTS ( subquery )`; (c) `SELECT ... FROM @lt_keys AS t INNER JOIN dbtab` (7.52+, itab is shipped to the DB — keep it small); (d) `FOR ALL ENTRIES` only if none of the above fit.

**Client handling** `[✓]`
- Automatic client handling is the default; do not add `MANDT`/`CLIENT` to the WHERE clause.
- Cross-client / explicit client: `USING CLIENT @lv_client`, `USING ALL CLIENTS` (7.55+). The older `CLIENT SPECIFIED` (with `mandt` in WHERE) is obsolete.
- **`USING CLIENT` is forbidden in ABAP for Cloud Development.** ([19_ABAP_for_Cloud_Development.md](https://github.com/SAP-samples/abap-cheat-sheets/blob/main/19_ABAP_for_Cloud_Development.md))
- DDIC: client field must be the first key field; CDS view entities use `@ClientHandling.type` / `.algorithm` rather than `@ClientDependent`. `[~]`

**Other SQL rules worth encoding**
- Never `SELECT *` when you need three columns; never `SELECT ... ENDSELECT` (use `INTO TABLE` or `PACKAGE SIZE`).
- `SELECT SINGLE` without a full key is **non-deterministic on HANA** — the classic #1 remediation finding. Use `UP TO 1 ROWS` + `ORDER BY` when you mean "the best row". ([SOH remediation rules](https://sapabapcentral.blogspot.com/2019/09/soh-abap-code-remediation-rules-to-be-followed.html))
- HANA returns rows in **no guaranteed order** without `ORDER BY`. Any code relying on implicit sorting is a defect.
- Avoid `EXEC SQL` / native SQL; use ADBC (`cl_sql_statement`) only when unavoidable, and never in ABAP Cloud.

### A.6 Grouping (`LOOP AT ... GROUP BY`)

From [11_Internal_Tables_Grouping.md](https://github.com/SAP-samples/abap-cheat-sheets/blob/main/11_Internal_Tables_Grouping.md) `[✓]`:

```abap
" Representative binding + member loop (replaces AT NEW / control breaks)
LOOP AT lt_spfli INTO DATA(ls_wa) GROUP BY ls_wa-carrid.
  LOOP AT GROUP ls_wa INTO DATA(ls_member).
    " ...
  ENDLOOP.
ENDLOOP.

" Group key binding, structured key, GROUP SIZE / GROUP INDEX, no member access
LOOP AT lt_spfli INTO DATA(ls_wa2)
     GROUP BY ( carrier = ls_wa2-carrid
                origin  = ls_wa2-airpfrom
                idx     = GROUP INDEX
                size    = GROUP SIZE )
     WITHOUT MEMBERS
     INTO DATA(ls_key).
  WRITE / |{ ls_key-carrier } { ls_key-origin }: { ls_key-size }|.
ENDLOOP.
```
`[?]` `ASCENDING/DESCENDING`, `REFERENCE INTO`, and `VALUE #( FOR GROUPS ... GROUP BY ... )` exist in the keyword docs but were **not** in the file I read — verify syntax before putting them in the skill as gospel.

### A.7 Exception classes, RESUMABLE, ASSERT, MESSAGE INTO

From [27_Exceptions.md](https://github.com/SAP-samples/abap-cheat-sheets/blob/main/27_Exceptions.md) `[✓]`:

```abap
" Hierarchy: CX_ROOT -> CX_STATIC_CHECK | CX_DYNAMIC_CHECK | CX_NO_CHECK
"  static  : must be declared & handled  -> recoverable, part of your contract
"  dynamic : declared, not forced        -> avoidable by the caller (bad input)
"  no_check: never declared              -> unrecoverable (out of memory, bugs)

CLASS zcx_order_invalid DEFINITION
  INHERITING FROM cx_static_check
  PUBLIC FINAL CREATE PUBLIC.
  PUBLIC SECTION.
    INTERFACES if_t100_message.
    INTERFACES if_t100_dyn_msg.          " needed for MESSAGE ID..TYPE..NUMBER
    CONSTANTS:
      BEGIN OF invalid_amount,
        msgid TYPE symsgid VALUE 'ZORDER',
        msgno TYPE symsgno VALUE '001',
        attr1 TYPE scx_attrname VALUE 'MV_AMOUNT',
        attr2 TYPE scx_attrname VALUE '',
        attr3 TYPE scx_attrname VALUE '',
        attr4 TYPE scx_attrname VALUE '',
      END OF invalid_amount.
    DATA mv_amount TYPE string READ-ONLY.
    METHODS constructor
      IMPORTING textid    LIKE if_t100_message=>t100key OPTIONAL
                previous  TYPE REF TO cx_root OPTIONAL
                iv_amount TYPE string OPTIONAL.
ENDCLASS.

" Raising
RAISE EXCEPTION TYPE zcx_order_invalid
  MESSAGE e001(zorder) WITH lv_amount.                 " needs IF_T100_MESSAGE
RAISE EXCEPTION TYPE zcx_order_invalid
  MESSAGE ID 'ZORDER' TYPE 'E' NUMBER '001' WITH lv_a lv_b.  " needs IF_T100_DYN_MSG
RAISE EXCEPTION TYPE zcx_order_invalid
  EXPORTING textid = zcx_order_invalid=>invalid_amount
            iv_amount = lv_amount.
RAISE EXCEPTION NEW zcx_order_invalid( iv_amount = lv_amount ).

" Reuse a message that was just put into SY-MSG*
MESSAGE e001(zorder) WITH lv_a INTO DATA(lv_dummy).
RAISE EXCEPTION TYPE zcx_order_invalid USING MESSAGE.

" Wrapping (Clean ABAP: wrap foreign exceptions, keep PREVIOUS)
TRY.
    lo_remote->call( ).
  CATCH cx_web_http_client_error INTO DATA(lx).
    RAISE EXCEPTION TYPE zcx_order_invalid
      EXPORTING previous = lx.
ENDTRY.

" Handling constructs
TRY.
    ...
  CATCH zcx_a zcx_b INTO DATA(lx1).
  CATCH cx_root INTO DATA(lx2).          " avoid; be specific
  CLEANUP.                               " runs when propagating outward
ENDTRY.

TRY.
    lv_r = lv_a / lv_b.
  CATCH cx_sy_zerodivide.
    lv_b = 1.
    RETRY.                               " re-runs the whole TRY block
ENDTRY.

" RESUMABLE: caller may continue after the raise point
METHODS process RAISING RESUMABLE(zcx_order_invalid).
METHOD process.
  IF lv_bad = abap_true.
    RAISE RESUMABLE EXCEPTION TYPE zcx_order_invalid.
  ENDIF.
  " execution continues here after RESUME
ENDMETHOD.

TRY.
    process( ).
  CATCH BEFORE UNWIND zcx_order_invalid INTO DATA(lx3).
    IF lx3->is_resumable = abap_true.
      RESUME.
    ENDIF.
ENDTRY.

" ASSERT — for programming errors / invariants only, NOT for input validation
ASSERT lt_items IS NOT INITIAL.
ASSERT ID zgroup SUBKEY 'order' FIELDS lv_id CONDITION lv_amount >= 0.
" failure = ASSERTION_FAILED short dump, uncatchable; can be switched off
" per checkpoint group (SAAB) when using ASSERT ID.

" Explicit dump
RAISE SHORTDUMP TYPE cx_sy_zerodivide.

" MESSAGE INTO — get text without any UI/dialog
MESSAGE e005(zorder) WITH lv_a lv_b INTO DATA(lv_text).
" sy-msgid / msgno / msgty / msgv1..4 are filled as a side effect
MESSAGE ID sy-msgid TYPE sy-msgty NUMBER sy-msgno
        WITH sy-msgv1 sy-msgv2 sy-msgv3 sy-msgv4 INTO lv_text.
```

Clean ABAP error-handling rules `[✓]`: class-based exceptions, never return codes; one abstraction level per method; "focus on the happy path **or** on error handling, but not both"; fail fast; don't use exceptions for regular control flow.

---
