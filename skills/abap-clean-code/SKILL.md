---
name: abap-clean-code
description: "Write new SAP ABAP or refactor existing ABAP into Clean ABAP with modern 7.40+ syntax, across all RICEFW objects (reports and ALV, RFC/file/IDoc/OData interfaces, data loads, BAdI and enhancements, SmartForms and Adobe Forms, workflow) and Fiori (CDS view entities, Fiori Elements annotations, RAP, SEGW DPC_EXT, freestyle UI5 back ends). Use whenever the user wants ABAP written, generated, fixed, cleaned up, modernized or optimized: 'write a report that...', 'create a class / function module / CDS view / BAdI implementation', 'refactor this ABAP', 'convert to new syntax', 'why is this SELECT slow', 'add unit tests to this class' — or when they just paste ABAP and ask for improvement, even without saying 'Clean ABAP'. Use it too when ABAP is one deliverable inside a larger task. Not for a formal pre-transport sign-off report (abap-code-review), technical design documents (abap-tdd-generator) or transport release gates (sap-transport-gate)."
metadata:
  version: "1.0.0"
  type: docs
  valid_until: "evergreen"
  source_urls:
    - "https://github.com/SAP/styleguides/blob/main/clean-abap/CleanABAP.md"
    - "https://help.sap.com/doc/abapdocu_latest_index_htm/latest/en-US/index.htm"
  output_schema:
    format: text
    description: "ABAP source in fenced code blocks plus a short rationale and a pre-activation checklist, delivered in the conversation; written to files only when the user asks for files."
  permissions:
    read_paths: ["<skill_dir>/references/"]
    write_paths: []
    network_endpoints: []
    requires_elevation: false
    accesses_env_vars: []
---

# ABAP Clean Code

Produce ABAP that a senior SAP developer would approve in review: correct for the
target release, structured so it can be tested, and clean in the sense SAP's own
style guide means. Two entry paths — **write new code** or **refactor existing
code** — share the same grounding step, the same core rules and the same output
shape.

The references in this skill are the authority. Prefer them over recollection,
especially for syntax availability, CDS annotations, RAP artefacts and SAP API
signatures.

---

## Step 1 — Ground yourself before writing a line

Three facts change the output. Get them from the conversation or from the code in
front of you; ask only when you cannot infer and the answer would change the code.

1. **Release and stack.** ECC 6.0 (treat as 7.40-7.52 subset), on-premise S/4HANA
   (7.55+), or ABAP Cloud / BTP (restricted language, released APIs only).
   `index += 1` needs 7.54, `DEFINE VIEW ENTITY` needs 7.55, `RAISE EXCEPTION NEW`
   needs 7.52 — generating those into an older system is a syntax error, not a
   style debate. If nothing indicates otherwise, assume **on-premise S/4HANA,
   7.55+, classic ABAP permitted**, and say so in one line rather than blocking on
   a question.
2. **The shop's conventions.** Prefixes, namespace, message class, object naming.
   Mirror what you can see in the surrounding code — see *The prefix question*
   below. A technically perfect class that breaks the customer's naming standard
   gets sent back.
3. **The object and its caller.** A report run in background, an RFC called by a
   middleware, a CDS view consumed by a Fiori Elements list — each carries
   different obligations (no dialog messages in RFC, `@ObjectModel` and UI
   annotations for Fiori, restartability for a load program).

State assumptions compactly at the top of your answer. Guessing silently is what
produces code that cannot be activated.

---

## Step 2 — Load only the reference you need

The always-on rules below are enough for a small ask. Read further when the task
touches these areas:

| The task involves | Read |
|---|---|
| Naming, method design, classes, error handling, comments, formatting, refactoring order, enterprise naming table | `references/CLEAN_ABAP.md` |
| Constructor expressions, table comprehensions, `VALUE`/`REDUCE`/`FILTER`/`CORRESPONDING`, modern ABAP SQL, exception classes, "is this available in my release" | `references/MODERN_SYNTAX.md` |
| A slow program, mass data, code pushdown, internal table type or key choice, chunking, parallelization | `references/PERFORMANCE_HANA.md` |
| CDS views, Fiori Elements annotations, VDM layering, DCL, RAP (managed/unmanaged, BDEF, determinations, validations, actions, draft, EML), service binding, clean core | `references/CDS_AND_RAP.md` |
| SEGW / `*_DPC_EXT`, `GET_ENTITYSET`, paging and filtering, deep insert, batch, CSRF, message container, UI5 back-end obligations | `references/ODATA_CLASSIC.md` |
| Report/ALV, file or RFC or IDoc interface, data load program, BAdI and enhancement choice, SmartForm or Adobe Form, workflow | `references/RICEFW_PATTERNS.md` |
| Writing or improving ABAP Unit tests, test doubles, injection, `cl_osql_test_environment` | `references/ABAP_UNIT.md` |
| You are about to state an SAP API signature you are not certain of | `references/KNOWN_UNCERTAINTIES.md` |

---

## The core that applies to every line

These hold regardless of object type, so apply them without loading anything.

**Names.** Descriptive, intention-revealing, one word per concept, classes are
nouns and methods are verbs. No technical encoding in the name itself
(`sysubrc_04`, `method_a`). Constants instead of magic numbers and literals.

**Declarations.** Declare where you use, inline (`DATA(x) = `, `INTO TABLE @DATA(t)`)
rather than a block at the top; no chained `DATA: a, b, c`; smallest possible scope.

**Methods.** One thing, done well, done only. Short — if a method needs a comment to
explain its middle, that middle is a method. Few parameters; `RETURNING` over
`EXPORTING` for a single output; avoid boolean input parameters (they usually mean
the method does two things).

**Layers stay apart.** Selection/input, data retrieval, business logic, output. This
is the single decision that determines whether the code can be unit tested at all:
logic that reaches out to the database itself cannot be tested without one.

**Errors.** Raise exceptions for your own failures rather than passing return codes
around; check `sy-subrc` (or catch) immediately after every call that sets it —
`SELECT SINGLE`, `READ TABLE`, `CALL FUNCTION`, `OPEN DATASET`, `AUTHORITY-CHECK`.
Never leave a `CATCH` block that swallows an exception without deciding something.

**Database.** No `SELECT` inside a `LOOP`. Explicit field list, never `SELECT *`
when you need three fields. Host variables escaped with `@`. `WHERE` clause that a
real index can serve. Aggregate, join and calculate in the database rather than
looping in ABAP. Choose the internal table kind by how it will be read
(`STANDARD` for sequential, `SORTED` for range and partial key, `HASHED` for unique
single-record access).

**Modern over obsolete.** String templates over `CONCATENATE`, table expressions
over `READ TABLE ... INTO`, `NEW` over `CREATE OBJECT`, `xsdbool` over `boolc`,
`VALUE`/`FOR` over loop-and-append — subject to the release ceiling from Step 1.

**Conditions.** Positive form, shallow nesting, no empty branches, `CASE` where a
chain of `IF`s is really one decision.

**Nothing hardcoded that belongs to the business.** Company code, plant, document
type, user name, file path, date — these come from customizing, a constant, a
selection screen or a parameter table. A hardcoded `bukrs` is the defect most
likely to survive to production and hurt.

**Security is not optional.** `AUTHORITY-CHECK` before reading or writing business
data, and check its `sy-subrc`. `ENQUEUE` before an update, released with the
matching `DEQUEUE`. No dynamic `WHERE` built from user input, no credentials in
source.

**Texts come from the dictionary.** Column headers, field labels and messages come from
data element labels, text symbols or a message class — not from English literals baked
into the code. A hardcoded label is a defect the moment a second language logs on.

**No dead code.** Delete commented-out blocks instead of shipping them; version
history is the archive.

---

## Path W — writing new code

1. **Restate the requirement** in one or two sentences and list the objects you
   intend to create. If the requirement is ambiguous in a way that changes the
   design (mass data or a handful of rows? online or background? does it post?),
   ask now — one round, not five.
2. **Choose the shape before typing.** Class-based logic with a thin report as
   caller beats a report full of `FORM`s. Push selection and aggregation into CDS
   or SQL rather than ABAP loops. For a Fiori app on S/4, RAP over SEGW unless the
   stack forces otherwise. For an enhancement, work down the clean-core ranking
   (released BAdI → other BAdI → enhancement spot → implicit enhancement →
   modification) and stop at the first that works. `references/RICEFW_PATTERNS.md`
   and `references/CDS_AND_RAP.md` carry these decisions in detail.
3. **Skeleton first, then flesh.** Class definition or CDS entity or behavior
   definition, then the implementations. It keeps the interface honest.
4. **Errors, authorization and locks as you go**, not as a later pass — they are
   where retrofitted code goes wrong.
5. **Tests.** When the logic is non-trivial, write the ABAP Unit test class along
   with the code; when it is trivial, say that a test would add nothing rather than
   producing a ceremonial one. See `references/ABAP_UNIT.md`.
6. **Run the self-check**, then present in the output format below.

## Path R — refactoring existing code

1. **Read all of it first** and be able to say what it does. Refactoring code whose
   behaviour you have not understood is how silent regressions happen.
2. **Behaviour preservation is the contract.** Clean without changing what the
   program does. If you find an actual bug — an unchecked `sy-subrc` that swallows a
   failure, a `COMMIT` inside a loop, a missing authorization check — surface it as
   a separate, explicit finding and let the developer decide, rather than quietly
   fixing it inside a cleanup.
3. **A cleanup is not a re-platforming.** Leave the working framework in place: do not
   trade `REUSE_ALV_GRID_DISPLAY` for `cl_salv_table`, a `FORM`-based report for a class
   hierarchy, or a SmartForm for an Adobe Form as a side effect of tidying up. Do not drop
   fields the program collects, even ones the current layout does not show — a user layout
   or a variant may depend on them. Each of those is a design change with its own test
   effort and its own risk of a user complaint; name it as an optional follow-up and let
   the developer schedule it. "Keep the same output" includes *how* the output is
   produced.
4. **Do not mix development styles inside one object.** SAP's guide is explicit:
   `REF TO` vs `FIELD-SYMBOL` loop targets, `NEW` vs `CREATE OBJECT`, `RETURNING`
   vs `EXPORTING` for a single output — pick the object's existing style or convert
   the whole object, never half.
5. **Refactor in the order that pays.** Booleans, conditions and `IF`s first, then
   methods (do one thing, small), then error handling, then names, then formatting.
   That order is deliberate: the early items are cheap and uncontroversial, while
   renaming and reformatting create the largest diff and the loudest disagreement,
   so they earn their place last — or get left alone in code you are only visiting.
6. **Respect the release ceiling.** Modernizing syntax that the system cannot
   compile is not an improvement.
7. **Scope honestly.** A large legacy program rarely needs — or survives — a total
   rewrite in one transport. Leaving the part you touched cleaner than you found it
   is the standard; say plainly what you left alone and why.

---

## The prefix question

Clean ABAP argues against Hungarian prefixes (`lv_`, `lt_`, `ls_`, `mo_`, `is_`,
`et_`); most enterprise SAP shops mandate them in a standards document. Both
positions are held by serious people, and this skill does not adjudicate.

Operationally: **mirror the code around you.** Editing an object full of `lv_`?
Keep `lv_`. Greenfield with no signal? Follow Clean ABAP (no prefixes) and note the
choice in a single line so the developer can overrule it — many will, and that is
fine. Never rewrite prefixes across an existing object purely to comply: it is
churn with no functional gain and it violates the "don't mix styles" rule above.

---

## Output format

```
### What I built            (or: What changed)
One to three sentences. Object names and purpose.
Assumptions on release/stack/conventions, if any, in one line.

### Code
One fenced ```abap block per object, each headed by a comment with the object name.

### Why these choices
3-8 bullets. Each names the decision and the payoff.

### Before you activate
The things only the developer can verify in their own system.
```

Keep *Why these choices* about decisions a reviewer would question — the table kind,
the pushdown, the exception class, the BAdI you picked over another. It is not a
restatement of the code, and it is not a lecture on Clean ABAP; two sentences of
reasoning beats a rule citation. Cite a rule name only where it settles a genuine
disagreement.

---

## Self-check before presenting

Walk this list against what you just wrote. Fix what fails; where you cannot fix it,
move it into *Before you activate* so it is visible rather than buried.

- Every statement that sets `sy-subrc` — handled, or deliberately and visibly not?
- Any `SELECT` inside a loop, `SELECT *` where a field list would do, unescaped host
  variable, or `WHERE` no index can serve?
- Internal table kind and key matched to how the table is actually read?
- Would a developer who has never seen this program guess what each name means?
- Any method past roughly 20 statements, taking a boolean input, or doing two things?
- Any hardcoded company code, plant, document type, user, path or date?
- Authorization checked before business data is read or written; lock taken before
  update; `COMMIT WORK` outside every loop?
- Does every syntax construct compile on the release you assumed in Step 1?
- Any method declaring both `RETURNING` and `EXPORTING`, or a signature ABAP will
  reject for another reason? Read each signature back once — it is the cheapest bug to
  catch here and the most annoying one to hit in ADT.
- Any user-visible text as a literal instead of a data element label, text symbol or
  message?
- Refactoring: same output mechanism, same columns, same fields collected, same row
  order as before — and if any of those did change, is it stated plainly?
- Is every SAP standard object you referenced — function module, class, method,
  table, CDS view, BAdI — one whose existence and signature you are actually sure
  of?

That last one matters more than the rest. A fabricated `CALL FUNCTION` or a method
that does not exist costs the developer a debug cycle in a system you cannot see,
and it is the failure they will remember. When you are unsure, still write the
pattern, but flag it in one clause — "confirm the parameter names of
`FP_JOB_OPEN` in SE37" — instead of asserting it. `references/KNOWN_UNCERTAINTIES.md`
lists the signatures already known to be shaky in these references.

---

## Related skills

Hand off rather than duplicate:

- Formal pre-release security and quality assessment with a sign-off report →
  `abap-code-review`
- Technical Design Document for a RICEFW object → `abap-tdd-generator`
- Reading or writing real objects in a live SAP system, syntax check, where-used,
  transports → `sap-adt-cli`
- Release readiness of a transport request → `sap-transport-gate`
- Integrating an external system with SAP, seen from the non-SAP side →
  `sap-integration-wiki`

Never write into a customer system as a side effect of this skill. Produce the source
here; activation and transport stay with the developer.
