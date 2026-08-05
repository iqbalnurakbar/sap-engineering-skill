# Filling Guidance — ABAP Technical Design Document (TDD) Template

This guide explains **what to write in each section** of
`TD_Report_Technical_Design_Document_Template.docx`. It is the reference
content behind `SKILL.md`, which lets an AI assistant help fill the template
from a Functional Design (FD), a set of ABAP objects, or a short developer
brief — **by asking the user for anything that isn't already clearly stated
in the supplied source material.** See `SKILL.md`'s Golden Rule: the AI never
guesses, defaults, or invents a value — it asks.

Each section below follows the same structure:

- **Purpose** — why the section exists
- **Fill with** — exactly what content goes in it
- **Source** — where that content typically comes from
- **Fill rule** — how to get from source material to a filled field: what
  counts as "clearly stated" (safe to write directly), what's structurally
  `N/A` (safe to write directly), and what must be asked of the user
- **Example** — a realistic filled example (for illustration only — never
  copy example values into a real document)

---

## General Rules (apply to the whole document)

1. **Never leave a cell blank.** If a sub-topic does not apply, write `N/A` —
   never delete the row/section or leave it empty. This preserves the
   template structure for review/audit.
2. **One TDD = one technical object or one tightly-coupled group of objects**
   (e.g. one CDS-based Fiori report, one interface, one enhancement). Do not
   merge unrelated developments into one document.
3. **Naming conventions** follow the customer/project namespace, typically:
   - Custom objects: `Z` or `Y` prefix
   - CDS Views: `ZI_<NUMBER>_<SHORT_NAME>` (interface/basic view),
     `ZC_<NUMBER>_<SHORT_NAME>` (consumption view)
   - Classes: `ZCL_<SHORT_NAME>`
   - Function Modules: `Z_<SHORT_NAME>`
   - Structures/Tables: `ZST_<SHORT_NAME>` / `ZTB_<SHORT_NAME>`
   - Programs/Reports: `Z<MODULE>_<SHORT_NAME>` (e.g. `ZMM_UPLOAD_RETURN`)
4. **Tone**: written in the imperative/descriptive third person, past-neutral
   ("The report retrieves...", not "I retrieve..."). No first-person language.
5. **Traceability**: every object listed in section 4 (Technical Details) and
   5 (Program Objects) must also appear, where relevant, in sections 6–12.
   Do not introduce an object in one section without registering it elsewhere.
6. **Source priority order** when filling this document:
   1. Functional Design document (if supplied)
   2. Actual ABAP source / repository objects (if supplied)
   3. Developer's short brief / chat description already given
   4. If none of the above clearly cover a field → **ask the user directly**.
      Never invent data, and never silently write a default or a plausible
      guess. Write `N/A` only when the field is structurally not applicable
      (see each reference doc's Section Applicability Map) — not as a
      stand-in for "unknown."

---

## Cover Page

| Field      | Fill with                                                      | Source                       | Fill Rule                                                                                                                                                                                                                                                             |
| ---------- | -------------------------------------------------------------- | ---------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Title      | `Technical Documentation – <Program/Object Name> – V<Version>` | RICEFW object name + version | This is the main title, bold, largest text on the page. `<Program/Object Name>` should be the plain business/technical name of the object (e.g. "Program Upload Return"), not a coded ID. `<Version>` starts at `1.0` and increments per Document History (Section B) |
| Release    | Release/version identifier of the target system landscape      | Project convention           | Ask user if unknown; do not guess a number                                                                                                                                                                                                                            |
| Project    | Project/programme name                                         | User input                   | Required — ask if missing                                                                                                                                                                                                                                             |
| Month/Year | Document creation date                                         | Current date                 | Use current date unless user specifies                                                                                                                                                                                                                                |

**Note:** earlier versions of this template used a coded `Document ID` (e.g.
`TD_MM_R_R4.7_112_Vendor_Balance_Report-V1.0`). This has been **removed** —
the document title now carries that information in plain language instead.
Do not reintroduce a coded Document ID field.

**Example:**

```
Technical Documentation – Program Upload Return – V1.0
Release 4.7
Project "PHOENIX"
March 2026
```

---

## A. Document Information

| Field                    | Fill with                                                                                                                                                          | Source                 | Fill Rule                                                                                                                                                                                                                                                                                                                                                      |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Business Unit / Area     | Functional module(s) impacted (MM, SD, WM, FI...) and plant/site scope if relevant                                                                                 | FD                     | If the FD clearly states this, list all modules (or write "Global" for cross-module scope). If not stated, ask the user                                                                                                                                                                                                                                        |
| Team                     | Functional/technical team name                                                                                                                                     | FD / project org chart | Ask the user if not stated in the FD — do not write `N/A` for "unknown," only if the user confirms no team is assigned yet                                                                                                                                                                                                                                     |
| Business / Process Owner | Name(s) of business stakeholder(s) who approve the requirement                                                                                                     | FD                     | List one per line exactly as given. Never invent names — if not in the FD, ask the user                                                                                                                                                                                                                                                                        |
| Functional Designer      | Author of the FD                                                                                                                                                   | FD                     | Use the FD's stated author. If missing, ask the user                                                                                                                                                                                                                                                                                                           |
| Technical Lead           | ABAP developer/lead accountable for this TDD                                                                                                                       | Developer input        | Ask the user — this is rarely in the FD                                                                                                                                                                                                                                                                                                                        |
| Status                   | One of: Allocate / Draft Functional Design / P2P Review / Business Review / Update Functional Design / Approved — **bold the current status, keep the rest plain** | Project workflow       | Ask the user which status applies. Do not assume "Draft Functional Design" — confirm it, since the document may be regenerated mid-workflow                                                                                                                                                                                                                    |
| Priority                 | High / Medium / Low                                                                                                                                                | FD                     | Ask the user. If the FD implies urgency language, mention what you read and let the user confirm the rating — don't set it yourself                                                                                                                                                                                                                            |
| Complexity               | Simple / Medium / Complex / Very Complex                                                                                                                           | Technical judgment     | You may calculate a **suggested** rating using this heuristic — 1-3 objects & no integration = Simple; 4-8 objects or 1 integration = Medium; >8 objects or multiple integrations = Complex; cross-module/cross-system with heavy custom logic = Very Complex — but present it as a suggestion and ask the user to confirm before writing it into the document |

---

## B. Document History

**Fill with:** one row per version, oldest first.
**Source:** version control / manual tracking.
**Fill Rule:** on first generation, create exactly one row: current date, `V1.0`, author name, `Initial Document`. On regeneration, append a new row — never overwrite prior rows.

---

## C. Related Documents

**Fill with:** the FD this TDD implements, plus any other TDD/interfaces it depends on.
**Source:** FD document ID/title.
**Fill Rule:** always list the source FD as the first row. If no other document exists, second row = `N/A`.

---

## D. Approval Details

**Fill with:** left blank until formal sign-off; only Sr. No. is pre-numbered.
**Fill Rule:** never auto-fill names/signatures — this section is filled manually after human review, not by AI.

---

## 1. Description and Purpose

**Purpose:** the single most important section — a reviewer should understand the _what_ and _why_ from this alone.

**Fill with:** 2–5 sentences or a short bullet list covering:

- What business problem/requirement this solves
- What the solution is, at a high level (report / interface / conversion / enhancement / form / workflow)
- Key business rules in one line each (details go in Section 4)

**Source:** FD "Business Requirement" / "Overview" section.

**Fill Rule:** paraphrase the FD's requirement in the developer's own words — do not copy the FD verbatim. If no FD was provided, ask the user for a one-paragraph description before proceeding.

### 1.1 Dependencies / Constraints

**Fill with:** custom or standard tables/objects this development reads from or requires to already exist (e.g. "Depends on ZTB_COUNTREQ custom table"), plus any technical constraints (performance, authorization, data volume ceiling).
**Fill Rule:** derive from the object list in Section 4/12; do not repeat the full technical design here — one line per dependency.

### 1.2 Trigger event

**Fill with:** what starts the process — user action (Fiori app launch, transaction execution), a batch job, an IDoc/interface inbound, a workflow event.
**Fill Rule:** `N/A` only if genuinely a pure on-demand report with no trigger logic.

### 1.3 Volume

**Fill with:** expected data volume (records/day, file size, concurrent users) if it affects design decisions (e.g. parallel processing, indexing).
**Fill Rule:** `N/A` if not provided by FD/business; do not estimate.

### 1.4 Execution type, Frequency and planning

**Fill with:** Manual / Background job / Real-time, plus frequency (on-demand, daily, hourly) and any scheduling variant name.
**Fill Rule:** ask the user how the process is triggered and how often it runs. Do not assume "Manual execution by business users" just because it's a Fiori app — confirm it.

### 1.5 High-Level Process Flow

**Purpose:** give a reviewer the whole flow at a glance — every moving
part (external systems, staging tables, programs, exits/BAdIs, standard
BAPIs) and how data/control passes between them — before they read a
single line of Section 4's detail. The diagram must cover the **complete
start-to-end process**: from the initial trigger (job, transaction,
inbound call, exit entry point) through every intermediate hand-off to
the final outcome (document created, file written, response returned,
error raised). A diagram that stops partway through the flow — because
the rest wasn't clear from the code — is incomplete and must not be
shipped as if it were the full picture.

**Fill with:** an actual diagram image (boxes/arrows), not prose and not
ASCII art pasted as text. One box per system/program/major processing
step, in the order execution actually happens, with the trigger or data
artifact labeled on each connecting arrow (e.g. "JSON payload", "INSERT
to staging table", "BAPI_SALESORDER_CREATEFROMDAT2").

**Source:** the object list being assembled for Section 4, plus the
trigger chain the user confirms in 1.2 / (for Enhancements)
`enhancement.md` §1 item 3.

**Fill Rule — how to build it:**

1. Draft the flow as a short ordered list first (system/program → what it
   does → what it hands off to next), tracing it all the way from the
   entry trigger to the final outcome. **If the provided code/source
   doesn't make some part of that trace clear — a hand-off, a branch, what
   happens after a given step — stop and ask the user rather than guessing
   or quietly ending the diagram at the last step you were sure of.** This
   applies mid-flow just as much as at the edges: a diagram that is
   confident about steps 1–3 but silently omits an unclear step 4 is as
   much a guess as inventing step 4 outright. The Golden Rule applies to a
   diagram exactly as it does to a text field: never invent, and never
   truncate, a box or an arrow that isn't backed by the source material or
   a user answer.
2. Render it as an image with matplotlib
   (`scripts/render_diagram_matplotlib.py`) — a plain pip package with no
   separate OS-level installer to fight with. Confirm it's available
   first via `scripts/check_dependencies.py` (see `SKILL.md`); if it
   isn't (and can't be pip-installed), use the text-list fallback
   described there instead. Keep it to a single flow (one diagram, not a
   diagram-per-object); if the flow is genuinely long, split into stages
   with sub-headings under 1.5 rather than one overcrowded diagram.
3. Insert the rendered PNG into the placeholder paragraph at "1.5
   High-Level Process Flow" using `scripts/insert_diagram.py` — do not
   hand-edit the OOXML drawing/relationship parts. Run it after the rest
   of the document's text has been filled (see `SKILL.md` Workflow).
4. If the user cannot yet confirm the full hand-off chain end-to-end,
   write `[To be completed]` and flag it in the pre-finalization summary
   — do not ship a partially-guessed or partially-truncated diagram.

**Fill Rule — N/A:** only for RICEFW types/documents with a genuinely
single-step flow and no external hand-offs (e.g. a simple on-demand
display-only report reading one CDS view). Ask before writing `N/A` here;
do not default to it just because building the diagram takes more effort.

---

## 2. Functional Details

### 2.1 Current functionality

**Fill with:** how the process works _today_ (standard SAP / legacy custom object / manual process). Write `N/A` for net-new developments.
**Source:** FD "As-Is" section.

### 2.2 Required functionality

**Fill with:** bullet list of functional capabilities to be built — selection criteria, views/outputs, calculations, validations. This is the functional-to-technical bridge; keep it capability-level, not code-level.
**Source:** FD "To-Be"/requirements section.
**Fill Rule:** one bullet per discrete capability; each bullet should map to at least one pseudo-code step in Section 4.1.

---

## 3. Technical Solution

**Fill with:** the architecture approach in 3–6 bullets — e.g. "ABAP RAP-based Fiori report", "CDS Views for data model", "ALV via Fiori Elements List Report", "Classic ALV via REUSE_ALV_GRID_DISPLAY", "Enhancement via BAdI XYZ".
**Fill Rule:** present the architecture options relevant to this RICEFW type (see the type-specific reference doc, e.g. `report.md` §2) and ask the user to pick one — do not choose the pattern yourself, even if one option seems obviously more modern or appropriate.

---

## 4. Technical Details

**Fill with:** the definitive list of every object to be created or changed, grouped by type:

- Data Definitions (CDS)
- Service Definition / Service Binding
- Classes
- Function Modules / Includes
- BSP/UI Application (if Fiori)

**Fill Rule:** this list is the single source of truth — every object named here must be echoed in the relevant sub-table of Section 5 or 12. Use final Z/Y naming even in draft, and flag names as "(proposed)" only if not yet reserved in the transport system.

### 4.1 Pseudo Code

**Purpose:** numbered, step-by-step processing logic — detailed enough,
with real code attached, that another developer could review or maintain
the object without reading the FD or the source repository again.

**Fill with:** a numbered list covering, in order:

1. Entry point / how the request is received
2. Input parameters and selection/filter handling
3. Data retrieval logic (source tables/CDS views, joins, key calculations)
4. Business rule / calculation logic (formulas spelled out, e.g. "Accuracy = (1 − |Difference| / Total) × 100")
5. Output/result construction
6. Sorting, paging, aggregation if applicable
7. Error/exception handling path

**Fill Rule:**

- Write one logical action per numbered step, as a short heading/label
  (matches the style already used in the source document: `"Read X from
  Y"`, `"Calculate Z as ..."`, `"If condition, do action"`).
- **Attach the actual ABAP code for that step directly under its label,**
  in a fixed-width code block — not a language-agnostic paraphrase. If
  the object is being documented from supplied ABAP source, the code
  block must be the real excerpt from that source (trimmed to the
  relevant lines, e.g. the body of the `FORM`, method, or `IF`/`SELECT`
  block for that step) — do not paraphrase code that already exists. If
  the object is still being designed and no code exists yet, write the
  block as a realistic ABAP draft consistent with the naming/technique
  already confirmed for this object, and label it clearly as a draft,
  e.g. a leading comment `"* draft — not yet implemented`.
- Keep each code block focused on that one step (a handful of lines to
  ~20); if a step's real logic is long, excerpt the decision-relevant
  lines and note "(excerpt)" in the step title, the way
  `enhancement.md` §9's worked example does.
- Include actual field/table/formula names once known — do not stay
  abstract once technical analysis is done.
- **Formatting in the .docx:** render each code block as its own
  paragraph, font `Consolas` or `Courier New`, no italics, in a
  light-gray-shaded single-cell table (or shaded paragraph border) so it
  reads as code rather than body text — do not just italicize it the way
  placeholder text is styled elsewhere in this template.
- If UI screenshots exist, reference them ("Front-end of the Fiori app: see attached screenshot") rather than describing UI positioning in prose.
- This section should be regenerated whenever the design changes; keep it in sync with Section 4's object list and with the 1.5 process flow diagram.

---

## 5. Program Objects

### 5.1 Package

**Fill with:** the development package and its superordinate package.
**Fill Rule:** use the project's standard custom package (e.g. `Z_S4HANA_<MODULE>`); ask if unknown — do not invent a package name.

### 5.2 Transaction Code

**Fill with:** custom T-code if one is created (rare for Fiori apps — usually `N/A`).

### 5.3 Reports / Module Pools / Function Groups

**Fill with:** classic report program / module pool / function group names, if any. `N/A` for pure RAP/CDS/Fiori developments.

### 5.4 Report/Selection-Screen

**Fill with:** one row per selection-screen field — table/field, S(elect-option) or P(arameter), range/single/mandatory behavior, default value.
**Fill Rule:** derive directly from Section 2.2's selection criteria bullets. `N/A` if there is no classic selection screen (e.g. OData $filter-driven Fiori app — describe filters here instead of a selection screen).

### 5.5 Translations

**Fill with:** state whether UI texts / labels require translation and which languages are in scope.
**Fill Rule:** ask the user which languages, if any, are in scope. Write `N/A` only if the user confirms this is single-language.

---

## 6. Interface

Fill only the sub-sections that apply; mark the rest `N/A`. Do not invent interface details.

- **6.1 BAPI** — only if a BAPI/BOR object is created or reused as an interface entry point.
- **6.2 ALE Configuration** — only for IDoc-based interfaces; logical system, partner profile, message type.
- **6.3 IDOC Type Structure** — Basic IDoc type + extension, only if IDoc-based.
- **6.4 File Interface** — file name/type/location/delimiter, for file-based inbound/outbound interfaces.
- **6.5 Conversion (LSMW/BDC)** — only for data migration/conversion objects.

**Fill Rule:** if the object being documented is a Fiori analytical report (like the source example), sections 6.1–6.5 are almost always `N/A` — do not force content here.

---

## 7. Forms

Fill only if the object produces a printed/PDF output (invoice, delivery note, label, etc.).

- **7.1 Output Determination** — output type, print program, layout set (NACE/BRF+ config).
- **7.2 SMART-Form/Script/Adobe** — layout technology used.
  - **7.2.1–7.2.3 Header/Item/Footer Logic** — describe what data populates each layout zone.
  - **7.2.4 Screen Shot of Layout** — insert an image of the actual/mock layout.

**Fill Rule:** `N/A` entirely for non-print developments (reports, interfaces without printed output).

---

## 8. Workflow

Fill only if SAP Business Workflow is used.

- **8.1 Event Linkage** — business object, delegate object, triggering event, workflow template ID.
- **8.2 List of Tasks** — task names in the workflow.

**Fill Rule:** `N/A` for anything that isn't workflow-driven (the large majority of Fiori/report developments).

---

## 9. Classes

**Fill with:** one block per custom class — attributes (name, type, visibility) and methods (name, type, visibility, one-line description of what the method does).
**Fill Rule:** only list _public and protected_ interface-relevant members unless the audience is purely technical; every method listed should trace back to a pseudo-code step in 4.1.

---

## 10. Web Services

**Fill with:** web service name, binding, description — only if a SOAP/REST service (outside of the OData service already covered in Section 4) is exposed.
**Fill Rule:** an OData service already declared in Section 4 (Service Definition/Binding) does not need to be repeated here; this section is for _additional_ web services only.

---

## 11. Enhancement Section

Fill only the sub-type actually used; all others `N/A`.

| Sub-section                         | When to fill                                                                                                                                                              |
| ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 11.1 Customer Exits (CMOD)          | Classic customer exit used                                                                                                                                                |
| 11.1.1 SAP-User Exits               | Specific user-exit include modified                                                                                                                                       |
| 11.1.2 SAP-Function Exits           | Function-exit modules called                                                                                                                                              |
| 11.1.3 SAP-Field Exits              | Field exit on a specific screen field                                                                                                                                     |
| 11.1.4 SAP-Menu Exits               | Menu/transaction-code level exit                                                                                                                                          |
| 11.1.5 SAP-Screen Exits             | Custom subscreen added to standard screen                                                                                                                                 |
| 11.1.6 SAP-Search Help Exits        | Custom logic on an F4 search help                                                                                                                                         |
| 11.1.7 BADI                         | BAdI definition + implementation + methods used — **this is the most common S/4HANA enhancement type; prefer BAdI over classic exits when both are technically possible** |
| 11.1.8 Modifications to SAP Objects | Direct SAP object modification (requires access key) — flag as high risk; should be last resort                                                                           |

**Fill Rule:** always check whether a BAdI exists before recommending a classic user/function/menu/screen exit; the latter should only be documented if no BAdI is available for the enhancement spot.

---

## 12. Newly Created Database Dictionary Objects

Fill only the sub-tables with actual new DDIC objects; `N/A` the rest.

| Sub-section            | Fill with                                            |
| ---------------------- | ---------------------------------------------------- |
| 12.1 Tables            | Custom transparent tables — see detail requirement below |
| 12.2 Views             | Classic DDIC views (not CDS — CDS goes in Section 4) |
| 12.3 Structure         | Custom structures and their use                      |
| 12.4 Append Structure  | Structure name + table it's appended to              |
| 12.5 Include Structure | Structure name + table it's included in              |
| 12.6 Table Types       | Table type + line type                               |
| 12.7 Search Helps      | Custom F4 search helps                               |
| 12.8 Lock Objects      | Lock object, locked table, parameters                |

**Fill Rule:** cross-check against Section 4 — every custom table/structure referenced there must have a corresponding row here.

**12.1 Tables — detail requirement:** the template's summary table (Table
/ Description) stays as a one-row-per-table index, but every **custom**
table must additionally get its own detail block directly underneath the
summary table, in this order:

1. **Field-level table** — one row per field: Field Name, Key (X/blank),
   Type, Length, Data Element, Description. Pull this from the actual
   DDIC definition if the user supplied it (SE11 export, `CREATE TABLE`
   DDL, or a screenshot); ask the user for it if the table is being
   newly designed and the field list isn't in the FD yet — never invent
   field names, types, or lengths.
2. **Purpose** — one short paragraph: what the table stores, which
   process writes to it and which reads from it, and any fields that are
   populated later as a status/tracking mechanism (e.g. "the SAP document
   number fields are filled in by `<program>` after successful posting").
3. **Key Design** — one line naming the composite key and why (e.g.
   "Composite key of TOKEN + ID uniquely identifies one inbound order").
4. **Technical Settings / Fixed Values**, only if relevant — data class,
   size category, buffering, logging, and the meaning of any indicator
   field's fixed values (e.g. `FLAG`: space = inactive, `X` = active).
   Omit this sub-item entirely (don't write `N/A` for it) if there's
   nothing beyond DDIC defaults to call out.

Apply the same field-level-table-plus-purpose treatment to 12.3
(Structure) when the structure is non-trivial (more than a couple of
fields); a simple 1–2 field structure can stay as a one-line description
in the summary table.

**Fill Rule — source priority:** exactly as in the General Rules above —
FD → supplied DDIC export/DDL → developer's stated field list → ask.
A table whose fields the AI cannot confirm from one of the first three
sources does not get a field-level table written on assumption; ask the
user for the field list first.

---

## 13. Error Handling

**Fill with:** bullet list of validation rules and their corresponding error/warning messages, e.g. "If Plant is initial, raise error message /message class/number/".
**Source:** FD validation rules + technical exception handling (RAP exceptions, `TRY/CATCH` blocks).
**Fill Rule:** every mandatory field from Section 5.4/2.2 should have at least one corresponding validation rule here.

---

## 14. Security Requirements / Authorization Details

**Fill with:** authorization objects checked (standard or custom), PFCG role dependencies, field-level security (e.g. plant/company-code authorization checks).
**Fill Rule:** ask the user whether any authorization object/field-level check applies beyond standard Fiori catalog/role security. Write `N/A` only once the user confirms there's no additional check — do not decide this yourself, even if the object looks display-only.

---

## 15. Additional Information and Attachments

**Fill with:** references to any supporting file (mockups, sample data files, external specs) not already captured elsewhere.
**Fill Rule:** `N/A` if none provided.

---

## 16. To Be Processed After Transport / Before Going Live

**Fill with:** manual post-transport steps — e.g. number range maintenance, master data setup, job scheduling, authorization role assignment, cache invalidation for Fiori launchpad tiles.
**Fill Rule:** based on the objects in Section 4/12, identify candidate manual steps (e.g. new business catalogs, new PFCG roles, new number ranges) and ask the user to confirm which actually apply — do not write them into the document as fact without confirmation.

---

## 17. Transport Requests

**Fill with:** one row per transport request — number and short description, in chronological order.
**Fill Rule:** append new rows as development progresses; never remove historical entries.

---

## 18. Glossary

**Fill with:** project- or domain-specific terms/acronyms used in this document that a new reader might not know (e.g. "ALV", "RICEFW", or a business-specific term).
**Fill Rule:** scan the document for acronyms not already expanded on first use; list those. `N/A` if the document uses only common SAP terminology.

---

## 19. ATC Check

**Fill with:** screenshot or summary of the ABAP Test Cockpit result confirming the code passes the project's quality gate (no priority 1/2 findings).
**Fill Rule:** this section is filled **after** development is complete, not during design — leave as `[Insert ATC check result screenshot here]` until code exists.

---

## Quick Reference: Safe-to-Write Directly vs. Must Always Ask

| Safe to write directly                                                                                                                     | Must always ask the user                                                                               |
| ------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------ |
| Content the FD, supplied ABAP code, or the user's own prior answers already state clearly                                                  | D. Approval Details (names/signatures)                                                                 |
| Sections that are structurally `N/A` for this RICEFW type, per the reference doc's applicability map (e.g. Workflow sections for a Report) | A. Business/Process Owner, Functional Designer, Technical Lead names                                   |
| Section 17 transport numbers, once the user has actually created them                                                                      | Priority / Complexity ratings (a suggested Complexity rating may be calculated, but must be confirmed) |
| Section 4 object naming, once the user has confirmed the convention to use                                                                 | Formal Status changes (e.g. → "Approved")                                                              |
|                                                                                                                                            | Architecture pattern choice (Section 3) — present options, let the user pick                           |
|                                                                                                                                            | Anything the source material doesn't clearly state                                                     |

If a field doesn't clearly fall into the left column, treat it as belonging
in the right column — when unsure, ask.

---

_This guidance is the functional basis for a future `SKILL.md` that will let an AI assistant auto-populate `TD_Report_Technical_Design_Document_Template.docx` from a Functional Design and/or a set of ABAP objects._
