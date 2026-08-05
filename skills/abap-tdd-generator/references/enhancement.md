# Reference: RICEFW Type "Enhancement"

Use this reference whenever the object being documented is an
**Enhancement** — any development whose primary purpose is to **modify or
extend the behavior of an existing standard SAP process/transaction**
(Sales Order, Delivery, Billing, Purchase Order, etc.) without replacing
that standard transaction with a net-new program. The standard SAP flow
keeps running; the enhancement changes what happens at specific points
inside it.

This covers, in SAP's preferred order (prefer the top of this list over
the bottom whenever technically possible — see §2):

- **BAdI** (definition + implementation) — the modern, S/4HANA-preferred
  mechanism
- **Enhancement Spot / Enhancement Point** (implicit or explicit)
- **Classic Customer Exit (CMOD/SMOD)** — user exit, function exit, field
  exit, menu exit, screen exit, search-help exit
- **Direct modification of an SAP object** (access-key required) — last
  resort only, always flagged as high risk

**Does not cover:**

- **Net-new programs** whose entire purpose is to read/display data with
  no side effects on standard SAP transactions — that's a **Report**, even
  if it happens to sit near an enhancement in the same project.
- **Net-new data exchange with an external system/file** — that's an
  **Interface**, even if the inbound data is *consumed* by user exits once
  it lands in SAP (see the hybrid note below for how to handle this when
  the two are bundled).
- **One-time/cutover data loads** — that's a **Conversion**.
- **Printed/PDF output changes** — if the enhancement's only job is to
  affect what a Form prints (e.g. an output-determination BAdI), classify
  it as **Form**, and use this reference only if the enhancement also
  changes upstream document logic (pricing, item creation) beyond the
  print output itself.

---

## 0. Classification Note — Hybrid Developments (Enhancement + Interface + Report)

A very common real-world pattern is: an external system pushes data into
SAP via a **web-service/API class** (Interface-shaped), a **custom report**
then drives automated document creation using standard BAPIs (Report-shaped
at first glance, but really a batch driver), and that automated creation
relies on **user exits/BAdIs** to inject business logic that manual entry
wouldn't trigger (Enhancement-shaped). All three pieces exist to serve one
tightly-coupled business flow.

**Do not split this into three separate TDDs.** Per `general.md` General
Rule 2 ("one TDD = one tightly-coupled group of objects"), document the
whole flow as a **single Enhancement TDD** when the exits/BAdIs are where
the actual business logic and risk live (discount calculation, freegoods
allocation, pricing overrides) — the API class and driver report are then
just the *entry point* that reaches that logic, and get documented as
supporting objects within this same document:

- API/web-service class → Section 6 (Interface), using `interface.md` §6
  guidance for the sub-table, but staying inside this one document
- Driver/execution report → Section 5.3 (Reports/Module Pools)
- The exits/BAdIs themselves → Section 11 (Enhancement) — this is the core
  of the document

Ask the user to confirm this classification if it isn't obvious from their
request (e.g. if the API ingestion side is unusually large/complex in its
own right — many message types, heavy transformation — it may deserve its
own Interface TDD instead, cross-referenced from this one via Section C
Related Documents). Never decide a split silently — ask.

---

## 1. Required Inputs — Ask the User Before Drafting

Before drafting Sections 3, 4, and 11, ask the user for the following as
one grouped question (skip any item already supplied by the source
material):

| # | Input | Why it's needed |
|---|-------|------------------|
| 1 | **Enhancement technique(s)** — BAdI, enhancement spot/point, classic user/function/field/menu/screen/search-help exit, or direct modification (per §2's preference order) | Determines Section 11 sub-section(s) and the architecture write-up |
| 2 | **Standard transaction/process being enhanced** — e.g. VA01/VA02 Sales Order, Outbound Delivery, Billing (VF01) — and the exact include/BAdI/user-exit name | Section 1 and Section 11's core table |
| 3 | **Activation/gating logic** — is the enhancement always active, or gated by a switch (custom control table, TVARVC entry, feature flag)? What determines when it fires vs. falls through to existing/standard logic? | Section 1.2, Section 4.1 guard-clause step, and Section 13 |
| 4 | **Fallback behavior** — what happens for the cases the enhancement does *not* apply to (must existing/standard behavior remain provably unchanged)? | Section 4.1 and the Final Checklist below |
| 5 | **Bundled supporting objects** — is this enhancement reached via a custom API class, driver report, or other entry point that should be documented in this same TDD (see §0), or does it purely fire inside standard T-codes with no custom entry point? | Section 5.3 / Section 6 |
| 6 | **Standard objects touched** — which existing includes/programs are being modified (even via exit, this still means listing them) | Section 4 and Section 12 traceability |

**Fill Rule — hard gate:** items 1, 2, and 3 are the minimum required set.
If the user leaves any of these unanswered after being asked, **do not
generate the Enhancement TDD.** State plainly which item(s) are missing
and why, and wait — an enhancement without a stated activation/gating rule
is exactly the kind of ambiguity that causes standard-process regressions,
so don't draft around it with a placeholder.

---

## 2. Architecture Decision (fill Section 3) — Technique Preference Order

**Do not pick a technique yourself.** Present the applicable options below
and ask the user to confirm before writing Section 3. Always check whether
a BAdI exists for the enhancement spot before recommending a classic exit
(per `general.md` §11's Fill Rule) — state in Section 3 that this check was
done, e.g. *"No BAdI available for this exit point as of \<release\>;
classic user exit \<name\> used instead."*

| Situation | Option to present |
|---|---|
| A BAdI definition exists at the needed spot (check via `SE18`/`SPRO` enhancement implementations) | **BAdI implementation** — preferred; note single-use vs. multi-use and filter values if any |
| No BAdI exists, but an implicit enhancement point/section is available at the needed spot | **Implicit enhancement** (`ENHANCEMENT-POINT`/`ENHANCEMENT-SECTION`) — lower risk than a classic exit or modification since it doesn't touch the original code |
| No BAdI, needed spot is a known classic customer exit (CMOD-manageable) | **Classic customer exit** — specify the type (user/function/field/menu/screen/search-help exit) and the exact include/function module name |
| Needed spot is inside a standard include that predates exits and has no BAdI/enhancement point (e.g. legacy `MV45AFZZ`/`RV60AFZC`-style includes) | **Direct FORM/include enhancement within a designated customer include** — this is standard SAP practice for these specific includes, not a "modification"; only flag as a true **modification** (access-key required) if code outside a customer include must change |
| Enhancement is reached from a custom entry point (API class, driver report) rather than firing purely inside a standard T-code | Note this explicitly in Section 3 and cross-reference Section 6/5.3 per §0 above |

---

## 3. Section 1 (Description and Purpose) / 1.2 (Trigger) — Enhancement-Specific Guidance

**1. Description and Purpose** must state, at minimum: which standard
process is affected, what changes for the user/system when the enhancement
fires, and — critically — confirmation that standard behavior is preserved
when it doesn't fire (per §1 item 4).

**1.2 Trigger event:** never `N/A` for an Enhancement. State the exact
condition that causes the exit/BAdI logic to execute (e.g. "Sales Order
saved via `BAPI_SALESORDER_CREATEFROMDAT2` from program `ZEDTUPLOAD_EXEC`
AND plant+sales org combination flagged active in control table"). If the
enhancement is gated by a control/switch table, name it here and describe
its purpose in one line (full field-level detail belongs in Section 12 if
the table is newly created).

---

## 4. Section Applicability Map

| Section | Applies to Enhancement? | Notes |
|---|---|---|
| A–D (Admin) | Always | No change from general guidance |
| 1. Description and Purpose | **Core** | State affected process + confirm fallback/legacy behavior preserved |
| 1.2 Trigger event | **Core** | Never `N/A` — exact firing condition, see §3 above |
| 1.5 High-Level Process Flow | **Core** | One box per system/program/exit in firing order — see `general.md` §1.5. For the §0 hybrid pattern, this is usually the clearest way to show the API/report/exit hand-off chain in one picture |
| 2. Functional Details | **Core** | One bullet per business rule being injected into the standard process |
| 3. Technical Solution | **Core** | Pick technique per §2's preference order |
| 4. Technical Details + 4.1 Pseudo code | **Core** | One pseudo-code block per exit/BAdI method — see §5 below |
| 5.1–5.2 Package / T-code | Fill if a custom monitoring/driver T-code exists; otherwise `N/A` | |
| 5.3 Reports/Module Pools | Fill if a driver/execution report is bundled per §0; otherwise `N/A` | |
| 5.4 Selection-Screen | Fill only if the bundled driver report has a manual selection screen | |
| 5.5 Translations | Fill only if the enhancement introduces new user-facing text (custom error messages, etc.) | |
| 6. Interface | Fill if an API/web-service class is bundled per §0; otherwise `N/A` | |
| 7. Forms | `N/A` unless the enhancement changes what a Form prints, beyond just upstream data | |
| 8. Workflow | `N/A` unless a failed enhancement path triggers an SAP Business Workflow task | |
| 9. Classes | Fill for any custom class involved (API class, BAdI implementation class, helper/mapping class) | |
| 10. Web Services | Fill only if the bundled entry point (§0) is a SOAP/REST service beyond what's already in Section 6 | |
| 11. Enhancement | **Core — this is the primary section for this RICEFW type.** See §6 below | |
| 12. DB Dictionary Objects | Fill for any new control/staging tables (switch tables, mapping tables) | |
| 13. Error Handling | **Core** — see §7 below | |
| 14. Security | **Core** — authorization checks for the enhanced transaction + any custom access-control table | |
| 17. Transport Requests | Always | |
| 19. ATC Check | Always | |

---

## 5. Section 4.1 (Pseudo Code) — Enhancement-Specific Style

Because an Enhancement typically touches **multiple exit points** rather
than one linear flow, write **one complete numbered sequence per exit/BAdI
method**, back to back, each following this shape:

1. **Guard clause** — the condition(s) that determine whether the
   enhancement logic runs at all here (control table check, calling
   program check, document type check). State explicitly what happens if
   the guard clause fails — must fall through to existing/standard logic,
   never silently skip a step the standard process expects.
2. **Data retrieval** — what additional data this exit reads (staging
   tables, config tables) beyond what standard SAP already passed in.
3. **Business rule / calculation logic** — the actual injected logic,
   spelled out with real field/table names once known.
4. **Write-back** — exactly which standard structure/table this exit
   modifies (e.g. `XKOMV`, an item table via `APPEND`) and how — this is
   the highest-risk part of any exit and must be unambiguous.
5. **Exception/fallback path** — what happens if the injected logic itself
   fails (e.g. lookup misses) — does it abort the standard transaction, or
   degrade gracefully to standard behavior?

**Fill Rule:** label each sequence with the exit/BAdI name as a sub-heading
(e.g. "`apply_discount2` — eDOT PH branch") so a reader can map pseudo-code
directly to Section 11's table. Do not interleave steps from different
exits into one numbered list.

---

## 6. Section 11 (Enhancement) — Core Section, Detailed Guidance

Fill only the sub-type(s) actually used (per `general.md` §11's table);
`N/A` the rest. For each exit/BAdI used, build one row in a summary table
before the detailed narrative:

| Standard Process | Exit/BAdI Type | Include / Class / Method | Purpose (one line) |
|---|---|---|---|
| e.g. Sales Order Pricing | Classic user exit | `MV45AFZZ` → `FORM apply_discount2` | Route to custom discount logic when control table flag is active |

Then, for each row, provide the narrative detail:

- **Exit/BAdI identification**: exact include/function module/BAdI
  definition + implementation name, and the standard program it belongs to
- **Enhancement Spot / BAdI**: if applicable, the enhancement spot name and
  whether the implementation is filter-based
- **What standard behavior is being extended**, in plain language, and
  **confirmation the standard path is untouched when the guard clause
  doesn't apply** — this must be explicit, not implied
- **Modification risk flag**: if this is a true modification (not exit,
  not enhancement point) requiring an access key, call this out prominently
  and note the SAP Note/OSS component if one exists, since this carries
  upgrade risk that the reviewer needs to see at a glance

**Fill Rule:** every exit/BAdI named in Section 4's object list must appear
here; every one named here must trace back to a pseudo-code sequence in
Section 4.1 (per `general.md` General Rule 5, Traceability).

---

## 7. Section 13 (Error Handling) — Enhancement-Specific Guidance

At minimum, cover:

- **Guard-clause failure behavior** — confirm explicitly that when the
  gating condition isn't met, the standard SAP process runs completely
  unmodified (this is the single most important thing a reviewer checks
  for an Enhancement)
- **Injected-logic failure behavior** — what happens if the custom logic
  itself hits an error (missing config, failed lookup): does it raise an
  error that stops the standard transaction, or log and degrade to
  standard/default behavior? State which, and confirm it was a deliberate
  choice, not a side effect
- **Regression risk on the standard process** — note any scenario where
  the enhancement could affect users/transactions *outside* its intended
  scope (e.g. a badly-scoped guard clause that fires for the wrong plant)
  and how that risk is mitigated

---

## 8. Section 14 (Security) — Enhancement-Specific Guidance

State explicitly:

- Whether the enhancement introduces any **new access-control logic** on
  top of standard authorization (e.g. a custom table restricting who may
  edit an enhancement-originated document in the standard transaction) —
  document the table, its key fields, and the fallback for users not
  listed in it
- Whether standard authorization objects checked by the base transaction
  remain fully in effect (they normally do, since exits run inside the
  standard transaction) — confirm with the user rather than assuming
- Any authorization check specific to the custom entry point, if one is
  bundled per §0 (e.g. who can trigger the driver report/API)

Write `N/A` only once the user confirms there's no additional check beyond
what standard authorization already provides — do not decide this yourself.

---

## 9. Worked Example (illustrative — generic names)

> **1. Description and Purpose**
> Extend standard Sales Order pricing and item creation to support
> discount and freegoods data originating from an external order-capture
> platform, while leaving manually-created Sales Orders (outside the
> flagged plant/sales-org combinations) completely unaffected.
>
> **1.2 Trigger event**
> Fires when a Sales Order is created via `BAPI_SALESORDER_CREATEFROMDAT2`
> from driver program `ZEXT_ORDER_EXEC` **and** the plant + sales org
> combination is flagged active in control table `ZCTRL_LIVE` (`FLAG = 'X'`).
> All other Sales Order creation (manual `VA01`, other driver programs)
> falls through to existing/standard pricing logic unchanged.
>
> **3. Technical Solution**
>
> - Classic customer exit (no BAdI available for this legacy pricing exit
>   point, confirmed via `SE18`) — `FORM apply_discount2` in `MV45AFZZ`
> - Guard clause checks calling program + `ZCTRL_LIVE` before branching to
>   custom logic; standard/NDS logic paths remain fully intact
> - Custom API class `ZCL_WS_ORDER_STAGING` (bundled per §0) is the
>   external entry point that populates the staging tables this exit reads
>
> **4.1 Pseudo code — `apply_discount2` (excerpt)**
>
> 1. **Guard clause** — if `sy-cprog = 'ZEXT_ORDER_EXEC'`, check
>    `ZCTRL_LIVE` for `WERKS`/`VKORG`; if flag not set, or calling program
>    differs, fall through to existing NDS/legacy branch unchanged
>    ```abap
>    IF sy-cprog EQ 'ZEXT_ORDER_EXEC'.
>      SELECT SINGLE werks INTO lv_ext_live
>        FROM zctrl_live
>        WHERE flag  EQ 'X'
>          AND werks EQ ls_vbap-werks
>          AND vkorg EQ xvbak-vkorg.
>    ENDIF.
>    ```
> 2. **Read discount lines** for the current order from staging table
>    `ZEXT_SO_DISC` once the flag is set
>    ```abap
>    IF lv_ext_live IS NOT INITIAL.
>      SELECT * INTO TABLE lt_disc
>        FROM zext_so_disc
>        WHERE id EQ xvbak-bstkd.
>    ENDIF.
>    ```
> 3. **Calculate and write back** the negative pricing amount per
>    discount line into the `XKOMV` condition table
>    ```abap
>    LOOP AT lt_disc INTO ls_disc.
>      wa_komv-kschl = ls_disc-condition_type_id.
>      wa_komv-kbetr = ls_disc-value * -1.
>      wa_komv-kpein = 1.
>      APPEND wa_komv TO xkomv.
>    ENDLOOP.
>    ```
> 4. **Fallback on empty lookup** — if the staging read returns no rows
>    for an order expected to have discounts, log a warning and continue
>    with zero discount rather than aborting order creation
>    ```abap
>    IF lt_disc[] IS INITIAL.
>      MESSAGE s001(zext_so) WITH xvbak-bstkd INTO sy-msgli.
>      PERFORM write_applog USING sy-msgli.
>    ENDIF.
>    ```
>
> This same excerpt-per-step-with-code pattern also drives the "Step 1 /
> Step 2 / Step 3" boxes in the 1.5 High-Level Process Flow diagram —
> each box in the diagram should be traceable to one of these numbered
> steps (or its equivalent in the sibling exit/report).
>
> **11. Enhancement**
>
> | Standard Process | Exit/BAdI Type | Include / Class / Method | Purpose |
> |---|---|---|---|
> | Sales Order Pricing | Classic user exit | `MV45AFZZ` → `apply_discount2` | Apply external discount data when control flag active |
> | Sales Order Item Creation | Classic user exit | `MV45AFZZ` → `apply_freegoods_ext` | Add freegoods line items from staging table |
>
> Modification risk: none — both are designated customer-exit FORMs
> within `MV45AFZZ`, not direct modifications to SAP-delivered code.

---

## 10. Final Checklist Before Marking an Enhancement TDD Complete

- [ ] All six §1 inputs were asked for; items 1, 2, and 3 were actually
      supplied before drafting began — if any were missing, generation was
      paused and the user was asked, not guessed around
- [ ] §0's hybrid-classification question was asked (or was clearly
      unambiguous) before deciding whether bundled API/report objects live
      in this document or a separate Interface/Report TDD
- [ ] Section 3 states one explicit technique per exit, following the
      BAdI-first preference order, with the "no BAdI available" check
      stated where a classic exit was chosen instead
- [ ] Every exit/BAdI in Section 4's object list appears in Section 11's
      summary table and traces to a Section 4.1 pseudo-code sequence
- [ ] Section 13 explicitly confirms standard-process behavior is
      unaffected when the guard clause doesn't apply — this is not optional
- [ ] Section 14 states the authorization/access-control approach or
      explicitly confirms none beyond standard authorization
- [ ] Any true modification (access-key required, not an exit/enhancement
      point) is flagged prominently as high risk, not buried in prose
- [ ] Section 19 left as `[Insert ATC check result screenshot here]` until
      code actually exists
