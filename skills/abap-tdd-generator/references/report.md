# Reference: RICEFW Type "Report"

Use this reference whenever the object being documented is a **Report** —
any development whose primary purpose is to _retrieve and display data_ to a
business user, with no data being created/changed in SAP as a side effect.

**This single reference deliberately covers two distinct flavors of
Report**, because they share the same TDD purpose (read-only data
retrieval/display) even though the underlying technology is different:

- **Fiori Report** — Fiori Elements List Report / Analytical List Page
  (RAP-based, OData V4), or a classic Fiori report via SAP Gateway (OData
  V2, CDS-based)
- **Classic ABAP Report** — classic ALV (`CL_SALV_TABLE`,
  `REUSE_ALV_GRID_DISPLAY`), or a simple classic list report (`WRITE`
  statements — legacy, avoid for new dev)

They are **not interchangeable in the document** — Sections 3, 5.3–5.4,
and 9 are written differently depending on which flavor applies. See §0.

**Does not cover:** anything that posts/changes data (that's an Enhancement
or an Interface), printed output (that's a Form), or approval routing
(that's a Workflow) — even if it also displays data along the way. If the
program both reads/displays data *and* posts changes via a BAPI (e.g. an
upload tool that also lets users download the current data first),
classify the whole development by the write side (Interface or
Enhancement) instead — see `general.md`'s classification guidance — and
only use this Report reference for the read-only portion's Section 2
sub-bullet.

---

## 0. Clarify Which Flavor Applies — Ask First

Before filling Section 3 or the applicability map below, confirm with the
user (if not already obvious from their request or source material) which
flavor this is: **Fiori Report** or **Classic ABAP Report (ALV/list)**.
This single question determines how Sections 3, 5.1–5.4, and 9 get filled,
so don't guess it from the target system alone — S/4HANA projects still
sometimes build classic ALV reports by explicit choice.

---

## 1. Section Applicability Map

Not every TDD section applies equally to a Report. Use this table to decide
what to actively fill vs. mark `N/A` — rows marked **[Fiori]** / **[Classic]**
depend on the flavor confirmed in §0:

| Section                                | Applies to Report?                                                                                                                             | Notes                                                          |
| -------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| A–D (Admin)                            | Always                                                                                                                                         | No change from general guidance                                |
| 1. Description and Purpose             | **Core**                                                                                                                                       | State the KPI/data being reported and the decision it supports |
| 1.5 High-Level Process Flow            | **Core** unless purely single-step (see `general.md` §1.5's N/A rule)                                                                          | Source(s)/CDS/tables → retrieval/calc steps → output view, as boxes |
| 2. Functional Details                  | **Core**                                                                                                                                       | Selection criteria + one row per output view (ALV1, ALV2, ...) |
| 3. Technical Solution                  | **Core**                                                                                                                                       | Pick architecture pattern for the flavor confirmed in §0 — see §2 below |
| 4. Technical Details + 4.1 Pseudo code | **Core**                                                                                                                                       | The most detailed section for a Report                         |
| 5.1–5.2 Package / T-code               | **[Fiori]** Usually `N/A` (Launchpad tile replaces T-code) — **[Classic]** Fill                                                                | |
| 5.3 Reports/Module Pools               | **[Classic]** Fill — **[Fiori]** `N/A`                                                                                                          | |
| 5.4 Selection-Screen                   | **[Classic]** Fill the table as normal — **[Fiori]** replace with OData filter bullet list (see §5)                                            |                                                                |
| 5.5 Translations                       | Fill if UI text/labels are user-facing in multiple languages                                                                                   |                                                                |
| 6. Interface                           | `N/A` unless the report also calls an external system for lookups                                                                              |                                                                |
| 7. Forms                               | `N/A` (a Report ≠ a printed Form; if the report needs a PDF export, keep to "Fiori standard export to Excel/PDF" — no custom SmartForm needed) |                                                                |
| 8. Workflow                            | `N/A`                                                                                                                                          |                                                                |
| 9. Classes                             | **Core** — provider/handler classes; differs by flavor, see §6                                                                                  |                                                                |
| 10. Web Services                       | `N/A` unless exposing the report data externally beyond the app itself                                                                         |                                                                |
| 11. Enhancement                        | `N/A` unless the report needs a BAdI for customer-specific filters/columns                                                                     |                                                                |
| 12. DB Dictionary Objects              | Fill only if new **classic** tables/structures are created (not CDS — CDS goes in §4)                                                          |                                                                |
| 13. Error Handling                     | **Core** — mandatory field checks, empty-result handling                                                                                       |                                                                |
| 14. Security                           | **Core** — authorization checks per selection field (plant, company code, etc.)                                                                |                                                                |
| 17. Transport Requests                 | Always                                                                                                                                         |                                                                |
| 19. ATC Check                          | Always                                                                                                                                         |                                                                |

---

## 2. Architecture Decision (fill Section 3)

**Do not pick a pattern yourself.** Present the relevant options below to
the user — based on their stated target system and requirements — and ask
them to choose. Only write the chosen pattern into Section 3 once confirmed.

| Target system                                                     | Option to present                                                                                                                                                                                                       |
| ----------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| S/4HANA (on-prem or cloud), new development                       | **RAP-based Fiori report**: CDS View(s) → Service Definition → Service Binding (OData V4) → optional custom handler class for complex logic                                                                             |
| S/4HANA, simple read-only analytics, no custom logic needed       | **CDS View exposed directly** via Service Binding, `@OData.publish: true` or annotation-based — no custom class required                                                                                                |
| ECC / no Fiori stack available                                    | **Classic ALV** via `CL_SALV_TABLE=>FACTORY` (generally preferred over `REUSE_ALV_GRID_DISPLAY` for new code — object-oriented, less parameter clutter — but confirm with the user if the project has its own standard) |
| Multiple result views needed (detail + aggregate, like ALV1/ALV2) | Multiple CDS Views / multiple Service Definitions bound to one Service Binding, each with a dedicated entity                                                                                                            |

---

## 3. Section 2 (Functional Details) — Report-Specific Guidance

**2.1 Current functionality**: for a net-new report, `N/A`. If replacing an
existing report/transaction, name it and note what's changing (e.g. "Replaces
transaction ZMM_STOCK_RPT — adds cycle-count accuracy KPI not available
today").

**2.2 Required functionality** — structure as:

```
- Selection by <mandatory fields> (mandatory)
- Optional filters: <field list>
- View 1 (<name>): <one-line purpose, e.g. "line-level detail">
- View 2 (<name>): <one-line purpose, e.g. "aggregated statistics">
```

If there's only one output view, still name it (e.g. "ALV1: Line-level
detail") — this name must be reused consistently in Sections 4 and 9.

---

## 4. Section 4.1 (Pseudo Code) — Report-Specific Style

Write pseudo-code as a **numbered list of atomic actions**, grouped in this
order (skip groups that don't apply):

1. **Entry / request handling** — how the request reaches the logic (RAP
   `GET_ENTITYSET`, OData request, or classic `START-OF-SELECTION`)
2. **Paging & sorting** — how page size/offset and sort fields from the
   request are captured and normalized
3. **Filter mapping** — one line per selection field, mapping UI filter →
   internal range table (`LS_FILTERS-<FIELD>`)
4. **Data retrieval** — the core query: source CDS/tables, joins, window
   functions, key calculations. Name the actual field/table/CDS names once
   known
5. **Business calculations** — one line per formula, written out in full,
   e.g. `"Calculate Accuracy = (1 − |Difference| / Total) × 100"`
6. **Result construction** — how the final output structure/table is built
   per view
7. **Sorting/paging application** — applied _after_ calculation, before
   return
8. **Exception path** — what happens on empty result set or runtime error
   (must always return a valid empty result, never let an unhandled
   exception propagate to the Fiori UI)

**Fill Rule:** if there are multiple views (ALV1/ALV2 pattern), write one
complete numbered sequence per view, back to back — do not interleave steps
from different views in one sequence.

---

## 5. Section 5.4 (Selection-Screen) — or Fiori Filter Equivalent

For classic reports, fill the table as normal (Table Field / S or P /
Range-Single-Multiple / Mandatory / Default).

For Fiori/RAP reports with no classic selection screen, **replace the table
with a bullet list of OData `$filter`-exposed fields** instead of writing
`N/A`:

```
- Plant (mandatory, single value, from @Consumption.filter.mandatory)
- Fulfilment Date (mandatory, range)
- Material (optional, multiple)
- Storage Location / Warehouse / Storage Type (optional, multiple)
```

---

## 6. Section 9 (Classes) — Report-Specific Guidance

For a RAP-based report, document the **provider/handler class** (if any
custom logic exists beyond what CDS annotations can express):

| Element               | Fill with                                                                                  |
| --------------------- | ------------------------------------------------------------------------------------------ |
| Class name            | `ZCL_<SHORT_NAME>`                                                                         |
| Interface implemented | e.g. `IF_RAP_QUERY_PROVIDER` for custom query logic                                        |
| Key methods           | `SELECT` (entry point), plus one row per private helper method with a one-line description |

For classic ALV, document the report's local classes/includes if logic is
modularized (event handler class for `CL_SALV_EVENTS_TABLE`, etc.). If, after
confirming with the user, the report needs no custom classes (pure CDS +
Fiori Elements, zero custom logic), state that explicitly: _"No custom class
required — fully declarative via CDS annotations."_ Do not leave the section
blank without that explanation, and don't conclude "no custom class needed"
on your own — confirm it.

---

## 7. Section 13 (Error Handling) — Report-Specific Guidance

At minimum, cover:

- Mandatory field validation (e.g. "If Plant is initial, raise error
  message")
- Empty result-set handling (must return `total number of records = 0`
  gracefully, not an exception)
- Any business-rule validation that filters out invalid combinations (e.g.
  incompatible Plant + Storage Location)

---

## 8. Section 14 (Security) — Report-Specific Guidance

State the authorization object(s) checked and on which selection field,
e.g.:

```
- M_MSEG_WMB checked on Plant + Storage Location
- Data restricted to plants assigned to the user's authorization profile
```

If the user confirms the report inherits security purely from the Fiori
catalog/role assignment with no additional field-level check, state that
explicitly rather than leaving blank. Do not make this determination
yourself — ask, per `general.md` §14.

---

## 9. Worked Example (illustrative — generic names)

> **1. Description and Purpose**
> Design and develop a Fiori Analytical Report to support Inventory Accuracy
> KPI analysis, including quantity variance, amount variance, and compliance
> analysis. The report provides two views (ALV1: detail, ALV2: aggregated
> statistics).
>
> **3. Technical Solution**
>
> - RAP-based Fiori Report
> - CDS Views for the data model, aggregation pushed to the database
> - ALV via Fiori Elements List Report Page
>
> **4. Technical Details**
>
> - Data Definitions (CDS): `ZI_INV_KPI`, `ZI_INV_KPI_STAT`
> - Service Definition: `ZR_INV_KPI`
> - Service Binding: `ZUI_INV_KPI`
> - Class: `ZCL_INV_KPI` (custom query provider for paging/sorting only — all aggregation done in CDS)
>
> **4.1 Pseudo code (excerpt)**
>
> 1. Read entity name from RAP request
> 2. If entity is `ZI_INV_KPI`, process ALV1 (detail)
> 3. If entity is `ZI_INV_KPI_STAT`, process ALV2 (aggregated)
> 4. Read paging info; default page size to 0 if negative
> 5. Map UI filters (Plant, Fulfilment Date, Material, Storage Location) to `LS_FILTERS`
> 6. Call CDS-based query, which computes Book Qty via `FIRST_VALUE()` and Difference Qty via `SUM()`, both partitioned by inventory key — no ABAP-side aggregation
> 7. If result is empty, return empty set with total records = 0
> 8. Apply requested sort and paging to the final result
> 9. Return result and total record count

---

## 10. Final Checklist Before Marking a Report TDD Complete

- [ ] Section 3 states one explicit architecture pattern (not "TBD")
- [ ] Every CDS View / Service Definition / Service Binding / Class named in Section 4 also appears in Section 9 (if a class exists) or Section 12 (if classic DB objects exist)
- [ ] Section 4.1 pseudo-code has a numbered exception-path step
- [ ] Section 13 covers at least: mandatory-field validation + empty-result handling
- [ ] Section 14 states the authorization check or explicitly says none beyond Fiori catalog/role
- [ ] Section 19 left as `[Insert ATC check result screenshot here]` until code actually exists
