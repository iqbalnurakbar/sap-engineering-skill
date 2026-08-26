# RICEFW Patterns and Pitfalls

> **Source**: ABAP Keyword Documentation (help.sap.com/doc/abapdocu_latest_index_htm), github.com/SAP/styleguides, github.com/SAP-samples/abap-cheat-sheets, SAP-samples RAP/Fiori reference apps, developers.sap.com tutorials.
> Confidence markers used below: `[OK]` = verified against an authoritative source cited inline; `[~]` = widely used and consistent with sources but not verbatim-confirmed; `[?]` = uncertain, verify in the target system before shipping.

## Contents

- [G. RICEFW patterns and pitfalls](#g-ricefw-patterns-and-pitfalls)
  - [G.1 Reports](#g1-reports)
  - [G.2 Interfaces](#g2-interfaces)
  - [G.3 Conversions / data loads](#g3-conversions-data-loads)
  - [G.4 Enhancements — the clean-core ranking](#g4-enhancements-the-clean-core-ranking)
  - [G.5 Forms](#g5-forms)
  - [G.6 Workflow](#g6-workflow)

---

## G. RICEFW patterns and pitfalls

### G.1 Reports

**Use SALV** (`cl_salv_table`) for new list output; `cl_gui_alv_grid` only when you need editable cells or full control inside a custom container; never `REUSE_ALV_GRID_DISPLAY` in new code `[~]`.

```abap
REPORT zmm_r_stock_overview.

TABLES: mara.                         " only for SELECT-OPTIONS typing

SELECTION-SCREEN BEGIN OF BLOCK sel WITH FRAME TITLE TEXT-b01.
  SELECT-OPTIONS: s_matnr FOR mara-matnr,
                  s_werks FOR t001w-werks OBLIGATORY.
  PARAMETERS:     p_date  TYPE dats DEFAULT sy-datum,
                  p_pkg   TYPE i DEFAULT 5000,
                  p_test  AS CHECKBOX DEFAULT 'X'.
SELECTION-SCREEN END OF BLOCK sel.

AT SELECTION-SCREEN ON s_werks.
  " validate here, not in START-OF-SELECTION
  SELECT SINGLE FROM t001w FIELDS @abap_true WHERE werks IN @s_werks
    INTO @DATA(lv_ok).
  IF lv_ok IS INITIAL.
    MESSAGE e001(zmm) WITH 'Plant'.
  ENDIF.

START-OF-SELECTION.
  " Thin report: delegate immediately to a testable class
  TRY.
      DATA(lo_app) = NEW zcl_mm_stock_overview( ).
      DATA(lt_out) = lo_app->run( it_matnr = s_matnr[]
                                  it_werks = s_werks[]
                                  iv_date  = p_date ).
    CATCH zcx_mm_error INTO DATA(lx).
      MESSAGE lx TYPE 'E'.            " MESSAGE <exception> works for T100 exceptions
  ENDTRY.

END-OF-SELECTION.
  TRY.
      cl_salv_table=>factory( IMPORTING r_salv_table = DATA(lo_alv)
                              CHANGING  t_table      = lt_out ).
    CATCH cx_salv_msg INTO DATA(lx_salv).
      MESSAGE lx_salv TYPE 'E'.
  ENDTRY.

  lo_alv->get_functions( )->set_all( abap_true ).
  lo_alv->get_columns( )->set_optimize( abap_true ).
  lo_alv->get_display_settings( )->set_list_header( 'Stock Overview' ).
  lo_alv->get_display_settings( )->set_striped_pattern( abap_true ).
  lo_alv->get_layout( )->set_key( VALUE #( report = sy-repid ) ).
  lo_alv->get_layout( )->set_save_restriction( if_salv_c_layout=>restrict_none ).
  lo_alv->get_selections( )->set_selection_mode( if_salv_c_selection_mode=>row_column ).

  DATA(lo_col) = lo_alv->get_columns( )->get_column( 'PRICE' ).
  lo_col->set_short_text( 'Price' ).
  lo_col->set_medium_text( 'Unit Price' ).
  " currency/quantity reference so SALV formats correctly
  CAST cl_salv_column_table( lo_col )->set_currency_column( 'WAERS' ).

  lo_alv->display( ).
```
`[~]` method names verified against common SALV usage; `set_key`/`set_save_restriction`/`set_currency_column` are the standard API. **`[?]`** `if_salv_c_layout=>restrict_none` exact constant.

**Progress indicator**
```abap
cl_progress_indicator=>progress_indicate(
  i_text               = |Processing { lv_i } of { lv_n }|
  i_processed          = lv_i
  i_total              = lv_n
  i_output_immediately = abap_true ).
```
`[~]` Also `CALL FUNCTION 'SAPGUI_PROGRESS_INDICATOR'`. Only meaningful in dialog; skip it in background (`sy-batch = abap_true`) and write to the job log instead (`MESSAGE ... TYPE 'S'` / `WRITE`).

**SUBMIT and background jobs**
```abap
" Synchronous submit with a saved variant
SUBMIT zmm_r_other WITH SELECTION-TABLE lt_rspar
                   USING SELECTION-SET 'DAILY'
                   AND RETURN.

" Background job (classic)
CALL FUNCTION 'JOB_OPEN'
  EXPORTING jobname  = |ZMM_STOCK_{ sy-datum }|
  IMPORTING jobcount = DATA(lv_jobcount)
  EXCEPTIONS OTHERS = 1.

SUBMIT zmm_r_stock_overview WITH SELECTION-TABLE lt_rspar
       USER sy-uname VIA JOB |ZMM_STOCK_{ sy-datum }| NUMBER lv_jobcount
       AND RETURN.

CALL FUNCTION 'JOB_CLOSE'
  EXPORTING jobcount  = lv_jobcount
            jobname   = |ZMM_STOCK_{ sy-datum }|
            strtimmed = abap_true
  EXCEPTIONS OTHERS = 1.
```
Cloud-ready alternative: **Application Jobs** — job catalog entry + job template (SJOBREPO / ADT) and `cl_apj_rt_api=>schedule_job( )`; the job class implements `if_apj_rt_exec_object` (`execute`) and `if_apj_dt_exec_object` (`get_parameters`, `check_parameters`). `[~]`

Report pitfalls: logic in `START-OF-SELECTION` instead of a class (untestable); `SELECT` inside `LOOP`; no `OBLIGATORY`/validation on selection screen → full-table scans; hard-coded `sy-uname`/plant/company code; `WRITE` output that nobody can download; no authorization check (`AUTHORITY-CHECK` on the org level) before selecting; running interactively what should be a job.

### G.2 Interfaces

**RFC / proxy**
- Synchronous RFC (`CALL FUNCTION ... DESTINATION`) only for short, idempotent, user-facing calls. Always `EXCEPTIONS system_failure = 1 MESSAGE lv_msg communication_failure = 2 MESSAGE lv_msg`.
- Web service consumption: generate a **consumer proxy** (SOAMANAGER logical port) and call it OO:
```abap
TRY.
    DATA(lo_proxy) = NEW zco_partner_service( destination = cl_proxy_destination=>create_by_url( ... ) ).
    lo_proxy->get_status( EXPORTING input = ls_in IMPORTING output = DATA(ls_out) ).
  CATCH cx_ai_system_fault cx_ai_application_fault INTO DATA(lx_ws).
ENDTRY.
```
- REST/JSON consumption (modern, cloud-ready):
```abap
TRY.
    DATA(lo_http) = cl_web_http_client_manager=>create_by_http_destination(
      cl_http_destination_provider=>create_by_url( 'https://api.example.com/v1/orders' ) ).
    DATA(lo_req) = lo_http->get_http_request( ).
    lo_req->set_header_fields( VALUE #( ( name = 'Content-Type' value = 'application/json' ) ) ).
    lo_req->set_text( /ui2/cl_json=>serialize( data = ls_payload
                                               pretty_name = /ui2/cl_json=>pretty_mode-camel_case ) ).
    DATA(lo_res) = lo_http->execute( if_web_http_client=>post ).
    DATA(lv_code) = lo_res->get_status( )-code.
    /ui2/cl_json=>deserialize( json = lo_res->get_text( ) CHANGING data = ls_result ).
  CATCH cx_web_http_client_error cx_http_dest_provider_error INTO DATA(lx_http).
ENDTRY.
```
`[~]` `/ui2/cl_json` is not released for ABAP Cloud; in cloud use `xco_cp_json` or `CALL TRANSFORMATION` / `cl_sxml_*`.

**File interfaces**
```abap
DATA lv_line TYPE string.

OPEN DATASET lv_path FOR INPUT IN TEXT MODE ENCODING UTF-8
     WITH SMART LINEFEED
     MESSAGE DATA(lv_msg).
IF sy-subrc <> 0.
  RAISE EXCEPTION TYPE zcx_file_error MESSAGE e010(zif) WITH lv_path lv_msg.
ENDIF.

DO.
  READ DATASET lv_path INTO lv_line.
  IF sy-subrc <> 0. EXIT. ENDIF.
  SPLIT lv_line AT cl_abap_char_utilities=>horizontal_tab INTO TABLE DATA(lt_fields).
  " validate, collect
ENDDO.
CLOSE DATASET lv_path.
```
Rules: always `MESSAGE` on `OPEN DATASET` and evaluate `sy-subrc`; always `CLOSE DATASET` (use `CLEANUP` or a wrapper class destructor); specify `ENCODING UTF-8` explicitly (default is non-Unicode-dependent and bites you); `SKIPPING BYTE-ORDER MARK` when consuming Windows-generated UTF-8; use a logical file path (FILE/`FILE_GET_NAME`) rather than a hard-coded AL11 directory; move the file to an `/archive` or `/error` subdirectory after processing so re-runs are safe; never leave PII on the app server unencrypted. `OPEN DATASET` is **not available in ABAP Cloud** — plan an inbound service / object store instead.

**IDoc**

Outbound: build `EDIDC` control record + `EDIDD` data records, then
```abap
CALL FUNCTION 'MASTER_IDOC_DISTRIBUTE'
  EXPORTING master_idoc_control            = ls_edidc
  TABLES    communication_idoc_control     = lt_edidc_out
            master_idoc_data               = lt_edidd
  EXCEPTIONS error_in_idoc_control          = 1
             error_writing_idoc_status      = 2
             error_in_idoc_data             = 3
             sending_logical_system_unknown = 4
             OTHERS                         = 5.
IF sy-subrc = 0.
  COMMIT WORK.                  " IDoc is only created on commit
ENDIF.
```

Inbound: a function module with the **ALE inbound interface** (registered in BD51, linked to a process code in WE42):
```abap
FUNCTION z_idoc_input_order.
*"  IMPORTING
*"     VALUE(INPUT_METHOD) TYPE  BDWFAP_PAR-INPUTMETHD
*"     VALUE(MASS_PROCESSING) TYPE  BDWFAP_PAR-MASS_PROC
*"  EXPORTING
*"     VALUE(WORKFLOW_RESULT) TYPE  BDWF_PARAM-RESULT
*"     VALUE(APPLICATION_VARIABLE) TYPE  BDWF_PARAM-APPL_VAR
*"     VALUE(IN_UPDATE_TASK) TYPE  BDWFAP_PAR-UPDATETASK
*"     VALUE(CALL_TRANSACTION_DONE) TYPE  BDWFAP_PAR-CALLTRANS
*"  TABLES
*"      IDOC_CONTRL STRUCTURE  EDIDC
*"      IDOC_DATA STRUCTURE  EDIDD
*"      IDOC_STATUS STRUCTURE  BDIDOCSTAT
*"      RETURN_VARIABLES STRUCTURE  BDWFRETVAR
*"      SERIALIZATION_INFO STRUCTURE  BDI_SER
*"  EXCEPTIONS
*"      WRONG_FUNCTION_CALLED
  LOOP AT idoc_contrl INTO DATA(ls_ctrl).
    " parse idoc_data segments for this docnum, post via BAPI
    IF lv_error = abap_true.
      APPEND VALUE #( docnum = ls_ctrl-docnum status = '51'
                      msgid = 'ZIF' msgno = '001' msgty = 'E'
                      msgv1 = lv_key ) TO idoc_status.
      workflow_result = '99999'.
    ELSE.
      APPEND VALUE #( docnum = ls_ctrl-docnum status = '53'
                      msgid = 'ZIF' msgno = '002' msgty = 'S' ) TO idoc_status.
      APPEND VALUE #( wf_param = 'Appl_Objects' doc_number = lv_doc ) TO return_variables.
      workflow_result = '0'.
    ENDIF.
  ENDLOOP.
ENDFUNCTION.
```
`[~]` This is the standard ALE inbound signature. Status codes: inbound **53** = posted, **51** = application error, **64** = ready to be transferred; outbound **03** = passed to port, **12** = dispatched OK, **16**/**26** = errors, **30** = ready for dispatch. Reprocess with BD87 / RBDMANI2 / RBDAGAIN. Never `COMMIT WORK` inside the inbound FM (the ALE layer owns the LUW) — post `IN UPDATE TASK` or via BAPI and let ALE commit.

**bgRFC / qRFC / tRFC** `[~]` ([RFC variants](https://help.sap.com/docs/ABAP_PLATFORM_NEW/753088fc00704d0a80e7fbd6803c8adb/4899b53cee2b73e7e10000000a42189b.html), [Introduction to bgRFC](https://integrtr.com/blog/introduction-to-bgrfc/))

| Variant | Guarantee | Status |
|---|---|---|
| sRFC | synchronous, no persistence | fine for short reads |
| aRFC | asynchronous, no persistence, no guarantee | avoid for business data |
| tRFC (`IN BACKGROUND TASK`) | exactly-once, no order | legacy |
| qRFC (`IN BACKGROUND TASK AS SEPARATE UNIT` + `TRFC_SET_QUEUE_NAME`) | exactly-once-in-order per queue | legacy |
| **bgRFC** (`IN BACKGROUND UNIT`) | exactly-once (type T) or exactly-once-in-order (type Q), better scheduling/monitoring, no `TRFC_SET_QUEUE_NAME` hacks | **SAP's recommendation for new development** |

```abap
TRY.
    DATA(lo_dest) = cl_bgrfc_destination_outbound=>create( 'ZTARGET' ).
    DATA(lo_unit) = lo_dest->create_qrfc_unit( ).   " or create_trfc_unit( )
    lo_unit->add_queue_name_outbound( 'ZORDER_' && lv_order_id ).
    CALL FUNCTION 'Z_SEND_ORDER' IN BACKGROUND UNIT lo_unit
      EXPORTING is_order = ls_order.
    COMMIT WORK.
  CATCH cx_bgrfc_invalid_destination cx_qrfc_invalid_queue_name INTO DATA(lx_bg).
ENDTRY.
```
**`[?]`** Verify `cl_bgrfc_destination_outbound=>create( )` signature and `add_queue_name_outbound` naming against your release. Monitoring: SBGRFCMON, SBGRFCCONF (must be configured with a supervisor destination or bgRFC silently doesn't run).

**Error / retry / idempotency rules for the skill**
- Every inbound message needs a **business key + a processing log table** (`message_id`, `external_key`, `status`, `retry_count`, `payload_hash`, `timestamps`). Reject or short-circuit a duplicate `message_id` — that *is* idempotency.
- Distinguish **technical** (retryable: network, lock, temporary) from **business** (non-retryable: bad master data) errors. Retry only the former, with backoff and a max count, then park in an error queue.
- Never swallow errors into a "log and continue" that nobody reads. Emit an alert (AIF, BPM, Application Log `BAL_LOG_*` / `cl_bali_*`, or an event) with the business key in the message.
- Use SLG1 / Application Log (`BAL_*` FMs, or the released `cl_bali_log`) rather than a Z-table with `WRITE` output.
- Prefer **SAP AIF** where it's licensed — it gives monitoring, retries, and error dashboards for free.
- One LUW per business document, not per file.

### G.3 Conversions / data loads

Tooling status `[✓]` ([SAP LTMC status](https://keyusertraining.com/en/sap-ltmc-legacy-transfer-migration-cockpit/)): **LSMW** is on the Simplification List, no further development, does not work with Fiori screens. **LTMC** deprecated since S/4HANA 2020, read-only from 2021. **"Migrate Your Data" Fiori app** is the successor (staging tables or direct transfer). **LTMOM** remains the modeling/extension tool. Old LTMC projects cannot be imported into the new app.

When you must write a custom load program, the canonical shape:

```abap
" Phase 1: LOAD  -> read source into a staging Z-table with a run id
" Phase 2: VALIDATE -> mark each row OK / ERROR with reasons; never post here
" Phase 3: POST   -> only OK rows, chunked, one commit per chunk
" Phase 4: REPORT -> ALV of results + downloadable error log

PARAMETERS: p_run   TYPE zload_run_id OBLIGATORY,
            p_mode  TYPE c LENGTH 1 DEFAULT 'V',   " V=validate P=post
            p_chunk TYPE i DEFAULT 500.

" --- POST phase ---
SELECT * FROM zload_staging
  WHERE run_id = @p_run AND status = 'V'      " validated OK, not yet posted
  ORDER BY seq_no
  INTO TABLE @DATA(lt_rows).

LOOP AT lt_rows INTO DATA(ls_row) GROUP BY
     ( chunk = ( sy-tabix - 1 ) DIV p_chunk ) INTO DATA(ls_grp).

  LOOP AT GROUP ls_grp INTO DATA(ls_item).
    CALL FUNCTION 'BAPI_MATERIAL_SAVEDATA'
      EXPORTING headdata = ls_item-headdata
      IMPORTING return   = DATA(ls_ret).

    IF ls_ret-type CA 'EA'.
      CALL FUNCTION 'BAPI_TRANSACTION_ROLLBACK'.
      UPDATE zload_staging SET status = 'E', msgtxt = @ls_ret-message
        WHERE run_id = @p_run AND seq_no = @ls_item-seq_no.
    ELSE.
      UPDATE zload_staging SET status = 'P', object_key = @ls_ret-message_v1
        WHERE run_id = @p_run AND seq_no = @ls_item-seq_no.
    ENDIF.
  ENDLOOP.

  CALL FUNCTION 'BAPI_TRANSACTION_COMMIT' EXPORTING wait = abap_true.
ENDLOOP.
```

Rules: **validate-then-post, always two phases**; per-row status in a staging table so the run is restartable and auditable; `BAPI_TRANSACTION_COMMIT`/`ROLLBACK` explicitly (BAPIs don't commit); `wait = abap_true` when a follow-on step reads what you just wrote; a test/simulation mode; number-range and lock contention handled by chunking on the natural key; **never** `CALL TRANSACTION`/BDC when a BAPI or a released API exists; if you must use BDC, use `MODE 'N' UPDATE 'S'` with a `bdcdata` message table and *never* rely on screen sequence across releases.

### G.4 Enhancements — the clean-core ranking

```
BEST   1. Standard configuration / SPRO
       2. Key-user extensibility: custom fields & logic, Custom CDS View,
          Custom Analytical Query, Fiori adaptation (UI Adaptation at runtime)
       3. Side-by-side on BTP: released OData/RAP APIs + business events
       4. Developer extensibility (ABAP Cloud, tier 1):
            - released BAdIs / extension points (cloud-released)
            - RAP behavior extension, CDS `extend view entity`
            - metadata extension (@Metadata.layer)
       5. Classic extensibility (tier 2/3), in this order:
            - new (enhancement-framework) BAdI via SE18/SE19, filter-based
            - explicit enhancement point / enhancement section
            - append structure / include structure (CI_/ZZ fields)
            - implicit enhancement (method/FM start/end, class end)
            - customer exit (SMOD/CMOD), classic user exit (SAPMV45A includes)
WORST  6. Modification / repair of SAP source (SSCR key), core mods  -> never
```
`[~]` synthesized from [SAP's extensibility guide](https://community.sap.com/t5/technology-blog-posts-by-sap/abap-extensibility-guide-clean-core-for-sap-s-4hana-cloud-august-2025/ba-p/14175399) and [S/4HANA extensibility options](https://community.sap.com/t5/enterprise-resource-planning-blog-posts-by-sap/sap-s-4hana-extensibility-options-for-clean-core-journey/ba-p/13568992).

New BAdI implementation shape:
```abap
" Consumer side (SAP code) calls:
GET BADI DATA(lo_badi) FILTERS flt_field = lv_bukrs.
CALL BADI lo_badi->check_document
  EXPORTING is_header = ls_header
  CHANGING  ct_items  = lt_items.

" Your implementing class:
CLASS zcl_badi_impl_doc_check DEFINITION PUBLIC FINAL CREATE PUBLIC.
  PUBLIC SECTION.
    INTERFACES if_ex_zdoc_check.
ENDCLASS.
```
Enhancement pitfalls: implicit enhancements are invisible in where-used and break on SAP upgrades — always add an ATC-visible comment and a functional-spec reference; never put a `COMMIT WORK` in an exit (you'll break the caller's LUW); never call a dialog/`MESSAGE` in an update-task or RFC-context exit; keep exits **thin** — delegate immediately to a Z class you can unit test; filter BAdIs so you don't run for every company code; check `sy-binpt`/`sy-batch` before anything interactive.

### G.5 Forms

`[✓]` [Adobe Forms vs SmartForms](https://www.erpvits.com/blog/adobe-forms-vs-smartforms-in-sap-abap/)

| | SmartForms (SMARTFORMS) | Adobe Forms / SFP |
|---|---|---|
| Designer | SAP Form Builder | Adobe LiveCycle Designer |
| Output | OTF → converted to PDF | native PDF |
| Interactive / fillable | no | yes |
| Digital signature | no | yes |
| SAP investment | limited | actively maintained |
| Prerequisite | none | ADS (Adobe Document Services) on AS Java or ADS-as-a-Service on BTP |

Recommendation: SAPscript = legacy only; SmartForms = acceptable for simple print output on existing ECC; **Adobe Forms (SFP) for new S/4HANA forms**, especially with interactivity, archiving, or exact-layout requirements.

**Separation of concerns — the single most important form pattern:**
```
Print program (Z class / FM)  ->  gathers and shapes ALL data
Form interface (SFP interface / SmartForm interface)  ->  the contract
Form layout  ->  presentation only, NO SELECTs, NO business logic
```

SmartForm invocation:
```abap
DATA lv_fm TYPE rs38l_fnam.
CALL FUNCTION 'SSF_FUNCTION_MODULE_NAME'
  EXPORTING formname = 'ZSD_INVOICE'
  IMPORTING fm_name  = lv_fm.

CALL FUNCTION lv_fm
  EXPORTING control_parameters = ls_ssfctrlop      " no_dialog, getotf, preview
            output_options     = ls_ssfcompop      " device, tddest, tdimmed
            user_settings      = space
            is_header          = ls_header
  IMPORTING job_output_info    = DATA(ls_otf)
  TABLES    it_items           = lt_items
  EXCEPTIONS formatting_error = 1 internal_error = 2 send_error = 3 user_canceled = 4.
```

Adobe Forms invocation (canonical — note the `FP_JOB_OPEN`/`FP_JOB_CLOSE` bracket, which the source snippet I found omitted):
```abap
DATA: ls_outputparams TYPE sfpoutputparams,
      ls_docparams    TYPE sfpdocparams,
      lv_fm           TYPE rs38l_fnam.

ls_outputparams-nodialog = abap_true.
ls_outputparams-getpdf   = abap_true.        " return PDF instead of printing
ls_outputparams-dest     = 'LP01'.

CALL FUNCTION 'FP_JOB_OPEN' CHANGING ie_outputparams = ls_outputparams
  EXCEPTIONS cancel = 1 usage_error = 2 system_error = 3 internal_error = 4.

CALL FUNCTION 'FP_FUNCTION_MODULE_NAME'
  EXPORTING i_name = 'ZSD_INVOICE_SFP'       " the FORM INTERFACE name
  IMPORTING e_funcname = lv_fm.

ls_docparams-langu   = 'E'.
ls_docparams-country = 'US'.
ls_docparams-fillable = abap_false.

CALL FUNCTION lv_fm
  EXPORTING /1bcdwb/docparams = ls_docparams
            is_header         = ls_header
            it_items          = lt_items
  IMPORTING /1bcdwb/formoutput = DATA(ls_formoutput)   " -pdf holds the XSTRING
  EXCEPTIONS usage_error = 1 system_error = 2 internal_error = 3.

CALL FUNCTION 'FP_JOB_CLOSE' IMPORTING e_result = DATA(ls_result)
  EXCEPTIONS usage_error = 1 system_error = 2 internal_error = 3.
```
`[~]` `FP_JOB_OPEN` / `FP_FUNCTION_MODULE_NAME` (importing parameter `i_name`, exporting `e_funcname`) / `FP_JOB_CLOSE` / `/1BCDWB/DOCPARAMS` / `/1BCDWB/FORMOUTPUT` are the standard ADS API. **`[?]`** Some releases use `FORMNAME` rather than `I_NAME` on `FP_FUNCTION_MODULE_NAME` — verify.

Form pitfalls: SELECTs in the form layout (unmaintainable, un-testable, slow); no `FP_JOB_CLOSE` on the error path (leaks the ADS job); hard-coded language/country instead of the partner's; text modules/standard texts not translated; missing `NO_DIALOG` in background → job hangs on a print dialog; output determination (NACE / BRFplus / Output Management in S/4) misconfigured so the form is never triggered.

### G.6 Workflow

`[~]` ([Explaining Flexible Workflow](https://learning.sap.com/courses/sap-workflow-overview-basics-strategy-and-extensibility/explaining-flexible-workflow), [Flexible Workflow — SAP Help](https://help.sap.com/docs/ABAP_PLATFORM_NEW/a602ff71a47c441bb3000504ec938fea/22a178c7929e439bb062017eda1e3643.html))

| | Classic Workflow (SWDD) | Flexible Workflow |
|---|---|---|
| Modeling | developer, SWDD workflow builder, transports | business user, Fiori "Manage Workflows" app, no transport |
| Scope | arbitrary graphs, loops, forks, deadlines | pre-delivered *scenarios* with configurable steps/conditions/agents |
| Agent determination | rules (PFAC), FMs, expressions | app-configured (user, role, team, expression) + BAdIs for custom agents |
| Business object | BOR object (SWO1) **or** an ABAP class implementing `IF_WORKFLOW` | scenario-provided |
| Fit | complex, non-standard processes; existing ECC WF | S/4HANA approvals (PO, PR, journal entry, supplier invoice…) — **first choice** |

Guidance: on S/4HANA, always check whether a **Flexible Workflow scenario** exists for the object before building a classic workflow. Extend it via its BAdIs/conditions. Build classic WF only when the process genuinely can't be expressed as a scenario. Both can coexist (activation is per-object). `[~]`

ABAP class as a business object (replaces BOR objects) — the class must implement `IF_WORKFLOW`, which bundles `BI_OBJECT` and `BI_PERSISTENT`:
```abap
CLASS zcl_wf_purchase_order DEFINITION PUBLIC CREATE PUBLIC.
  PUBLIC SECTION.
    INTERFACES if_workflow.               " -> bi_object + bi_persistent
    METHODS approve  RAISING zcx_wf_error.
    METHODS reject   RAISING zcx_wf_error.
    " bi_persistent~lpor / find_by_lpor / refresh must be implemented
ENDCLASS.
```
Pitfalls: business object methods that dump (workflow goes into error and stays there); no `COMMIT` semantics understanding (WF runs in its own LUW); container element typing mismatches; agent determination returning zero agents (item goes to the WF administrator and is silently ignored); no deadline/escalation; using `sy-uname` inside a WF step (it's WF-BATCH).

---
