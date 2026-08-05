# Reference: RICEFW Type "Form" (SAPscript / SmartForms / Adobe Forms)

Use this reference whenever the object being documented is a **Form** — any
development whose primary purpose is to produce a **printed, PDF, or
on-screen interactive output document** driven by SAP data: invoice,
delivery note, purchase order, picking list, dunning letter, label,
certificate, interactive approval form, etc.

This covers:

- **SmartForms** (`SMARTFORMS` transaction) — most common for new
  print-only output on ECC and S/4HANA on-prem
- **Adobe Forms** (Interactive or Print, via Adobe LiveCycle Designer /
  Adobe Document Services) — required for interactive (fillable, offline)
  forms, and increasingly preferred for print forms on newer S/4HANA
  releases
- **SAPscript** (`SE71`) — legacy technology; only document if the change
  is to an existing SAPscript form. Do not propose SAPscript for new
  development — flag this to the user and recommend SmartForms or Adobe
  Forms instead (see §2)

**Does not cover:** on-screen reports/lists with no print output (that's a
Report), data posted into SAP (that's an Enhancement or Interface), or
approval routing logic itself — a Form only covers the *layout and its
data feed*; if the same requirement also includes approval routing, that
routing belongs in a separate Workflow-type TDD (or Section 8 of this one,
if tightly coupled).

---

## 0. Required Inputs — Ask the User Before Drafting

A Form TDD cannot be responsibly filled from a generic Functional Design
alone: the layout, the data zones, and the trigger event are almost never
fully written down anywhere else. **Before drafting Section 7 (and the
Form-specific parts of Sections 1–5), ask the user for the following as one
grouped question** (skip any item the user has already supplied):

| # | Input | Why it's needed |
|---|-------|------------------|
| 1 | **Form technology** — SmartForms, Adobe Forms (Interactive or Print), or SAPscript (existing only) | Determines §2 architecture guidance and Section 7.2 wording |
| 2 | **Existing form name**, if this is a change to an existing form — or confirmation this is net-new | Whether Section 2.1 ("Current functionality") is `N/A` or describes the as-is form |
| 3 | **The layout itself** — preferably the form's **XML export** (SmartForms: `SMARTFORMS` → Utilities → Upload/Download, or the Adobe form's XDP/XFD export), which is the authoritative source for every field and zone. A PDF, print preview, scanned printout, or clear screenshot is an acceptable substitute if the XML export isn't available | **Mandatory.** This is the only reliable source for header/item/footer zones (7.2.1–7.2.3) — without it those sub-sections cannot be filled accurately |
| 4 | **Driver/print program** (if one already exists) — ABAP program or class that calls the form, or confirmation none exists yet | Feeds Section 4 (Technical Details) and Section 5.3 |
| 5 | **Business trigger** — how/when the form is generated: manual print from a transaction, automatic output on document save, background job, output via email/EDI | Section 1.2 (Trigger event) and Section 7.1 (Output Determination) |
| 6 | **Output determination approach** — classic NACE condition technique, or BRF+-based (common on S/4HANA) | Section 7.1 |
| 7 | **Data source(s) per zone** — which business object/table feeds the header, and which feeds the repeating item/line data | Section 7.2.1–7.2.2 |
| 8 | **Company branding assets**, if applicable — logo file, letterhead, specific fonts/colors mandated by corporate design | Only relevant to print layout construction; ask, don't assume standard SAP styling |
| 9 | **Multi-language requirement** — which languages the form must render in | Section 5.5 |
| 10 | **Interactive vs. print only** (Adobe Forms specifically) — does the user need to fill in data offline and have it processed back into SAP, or is this print/PDF-only output? | Determines whether an Adobe interactive form + processing class (§6 below) is needed at all |

**Fill Rule — hard gate, do not generate without this:** item 3 (the
layout — XML export or acceptable substitute) and items 1, 2, 5, and 6 are
the minimum required set. If the user cannot provide the layout, or leaves
any of these minimum items unanswered after being asked, **do not generate
the Form TDD.** Tell the user plainly which item(s) are still missing and
why they're required (per the "Why it's needed" column), and wait for them
to supply it. Do not proceed with a placeholder like
`[Insert screenshot of layout here — not yet available]` or a guessed
layout — an incomplete Section 7 misrepresents a document that's supposed
to be authoritative for development and review.

---

## 1. Section Applicability Map

| Section | Applies to Form? | Notes |
|---|---|---|
| A–D (Admin) | Always | No change from general guidance |
| 1. Description and Purpose | **Core** | State which business document is being produced and what triggers it |
| 1.1 Dependencies/Constraints | **Core** | Name the business document (order/delivery/invoice) this form depends on |
| 1.2 Trigger event | **Core** | Never `N/A` for a Form — always ask (see §0 item 5) |
| 1.5 High-Level Process Flow | **Core** | Output determination → print program/driver → layout technology → printed/PDF output, as boxes |
| 2. Functional Details | **Core** | 2.2 lists each layout zone as a discrete capability (see §3 below) |
| 3. Technical Solution | **Core** | Pick SmartForms vs. Adobe Forms — see §2 below |
| 4. Technical Details + 4.1 Pseudo code | **Core** | Driver program logic + form-calling logic (see §4 below) |
| 5.1–5.2 Package / T-code | Fill if a custom driver program/T-code is created; `N/A` if the form is called only from a standard output determination step | |
| 5.3 Reports/Module Pools | Fill with the driver program name, if any | |
| 5.4 Selection-Screen | Usually `N/A` — forms are rarely launched via a selection screen; describe the triggering document instead (already covered in 1.2) | |
| 5.5 Translations | **Core** — almost every printed form is multi-language in practice; confirm, don't assume single-language | |
| 6. Interface | `N/A` unless the form output is also transmitted via IDoc/EDI/email as part of the same development | |
| 7. Forms | **Core — this is the primary section for this RICEFW type.** See §5 below | |
| 8. Workflow | `N/A` unless an interactive Adobe form's submission triggers SAP Business Workflow approval steps | |
| 9. Classes | Fill if a custom print/processing class exists (see §6 below); `N/A` for pure declarative SmartForm + standard driver | |
| 10. Web Services | `N/A` unless the form is generated via a dedicated exposed service (rare) | |
| 11. Enhancement | Fill only if a BAdI is used for print-condition or output-control logic (e.g. `BADI_TEMSE_FLIST` or a custom print BAdI); otherwise `N/A` | |
| 12. DB Dictionary Objects | Fill only if new Z-structures were created for the form interface/data structure | |
| 13. Error Handling | **Core** — missing mandatory data, empty item table, print/spool failure handling | |
| 14. Security | Fill if the form or output device access is authorization-restricted; otherwise confirm with user before writing `N/A` | |
| 17. Transport Requests | Always | |
| 19. ATC Check | Always | |

---

## 2. Architecture Decision (fill Section 3)

**Do not pick a technology yourself.** Present the relevant options below —
based on the form technology the user stated in §0 item 1 — and ask them to
confirm before writing Section 3.

| Situation | Option to present |
|---|---|
| New print-only output (invoice, delivery note, label, etc.), no offline data entry needed | **SmartForms**: `SMARTFORMS` layout + a driver program/class that assembles the data and calls the generated function module |
| Interactive form — user must fill in data offline (PDF) and have it read back into SAP | **Adobe Interactive Forms**: Adobe LiveCycle Designer layout (XDP) + ABAP interface (context) + processing class to read submitted form data back via `FP_JOB_OPEN`/`FP_FUNCTION_MODULE_NAME`/`FP_JOB_CLOSE` |
| New print-only output, but project standard mandates Adobe over SmartForms (common on newer S/4HANA releases) | **Adobe Print Forms**: same call pattern as SmartForms but layout built in Adobe LiveCycle Designer instead |
| Change request against an existing SAPscript form | **Modify SAPscript in place** — do not migrate to SmartForms/Adobe as a side effect of an unrelated change request unless the user explicitly asks for a technology migration; if they raise migration as an option, present it as a separate, larger-scope decision |

Once the user confirms a technology, confirm this design point in Section 3
rather than leaving it as an open question:

- Whether the form must support print preview (`FP_JOB_OPEN` with
  `PREVIEW = 'X'` for Adobe, or standard SmartForms preview) before
  finalizing the driver program interface.

---

## 3. Section 2 (Functional Details) — Form-Specific Guidance

**2.1 Current functionality**: for a net-new form, `N/A`. If replacing/
modifying an existing form, name it (e.g. "Modifies SmartForm `ZINVOICE_01`")
and state what's changing.

**2.2 Required functionality** — structure as one bullet per layout zone,
naming each zone consistently so it can be reused in Section 7:

```
- Header zone: <what it shows, e.g. "company letterhead, invoice number, customer address, invoice date">
- Item/line zone: <repeating table content, e.g. "material, description, quantity, unit price, line total">
- Footer zone: <what it shows, e.g. "subtotal, tax breakdown, grand total, payment terms">
- Output trigger: <e.g. "automatic on billing document save, output type ZINV">
```

If the form has multiple pages or a distinct first-page/continuation-page
layout, call that out as its own bullet — it drives a design decision in
Section 7.2.

---

## 4. Section 4.1 (Pseudo Code) — Form-Specific Style

Write the pseudo-code for the **driver program/class**, not the layout tool
itself (the layout's own conditional logic is described in Section 7.2, not
here). Group in this order, skipping groups that don't apply:

1. **Entry point** — how the driver is invoked (output determination call,
   manual print program execution, Adobe `FP_JOB_OPEN` sequence)
2. **Header data retrieval** — source document/table read for header zone
3. **Item data retrieval** — source table(s) for the repeating line items,
   including any joins/calculations needed before handing off to the form
4. **Business calculations** — one line per formula (totals, tax,
   discounts), written out in full
5. **Form/function module call** — name of the generated function module
   (SmartForms) or `FP_FUNCTION_MODULE_NAME` result (Adobe), and the
   interface parameters passed
6. **Output handling** — spool request creation, print immediately vs.
   preview, or (Adobe interactive) capturing the submitted PDF data back
   into an ABAP structure
7. **Exception path** — missing mandatory header/item data, form-generation
   failure, print/spool error

---

## 5. Section 7 (Forms) — Detailed Guidance

This is the section this reference type exists to support. Fill every
sub-section using the inputs gathered in §0; do not leave any of them as a
bare `N/A` without asking first.

**7.1 Output Determination**
Fill with: output type code, the print program (if classic) or driver
class, and the layout set name (the actual SmartForm/Adobe form technical
name). State whether determination is via classic condition technique
(NACE) or BRF+, per §0 item 6.

**7.2 SMART-Form/Script/Adobe**
State the layout technology chosen in Section 3, and the technical form
name (e.g. `ZSF_INVOICE_01` for SmartForms, or the Adobe form's interface
name).

- **7.2.1 Header Logic** — describe what data populates the header zone and
  any conditional logic (e.g. "Company logo and address shown only if
  Sales Organization = 1000; otherwise show plant address").
- **7.2.2 Item Logic** — describe the repeating item table: source, key
  fields displayed, subtotal/grouping logic (e.g. "Grouped by material
  group, subtotal per group").
- **7.2.3 Footer Logic** — totals, legal text, signature line, page
  numbering (e.g. "Page X of Y" placement).
- **7.2.4 Screen Shot of Layout** — insert the sample output supplied in
  §0 item 3 (rendered from the XML export if that's what was provided, or
  the PDF/screenshot substitute). Since §0 makes the layout a mandatory
  input, this sub-section should never need a placeholder — if you reach
  this step without a layout in hand, stop and go back to §0 rather than
  fabricating a mock image.

**Fill Rule:** every field named in 7.2.1–7.2.3 must trace back to the
driver program's data retrieval in Section 4.1 — do not introduce a field
in the layout description that the pseudo-code never retrieves.

---

## 6. Section 9 (Classes) — Form-Specific Guidance

Fill only if a custom class exists beyond a simple driver program:

| Element | Fill with |
|---|---|
| Class name | `ZCL_<SHORT_NAME>_FORM` |
| Purpose | e.g. "Assembles header/item data and calls the Adobe form interactive processing sequence" |
| Key methods | One row per method: data retrieval, calculation, form-call, and (for Adobe Interactive) submitted-data parsing |

For Adobe Interactive Forms specifically, document the method that reads
the submitted PDF data back into ABAP (typically via the generated
interface's import/changing parameters) — this is a common point of defects
if under-documented.

If the form is called from a simple driver program with no custom class,
state that explicitly rather than leaving the section blank: _"No custom
class required — driver program `Z<...>` calls the SmartForms function
module directly."_ Confirm this with the user rather than deciding it
yourself, per `general.md`'s Golden Rule.

---

## 7. Section 13 (Error Handling) — Form-Specific Guidance

At minimum, cover:

- Missing mandatory header data (e.g. "If customer address is blank, raise
  error message and stop output determination")
- Empty item table (should the form still print with a "no items" note, or
  should output be suppressed entirely? — ask the user, don't assume)
- Form-generation/spool failure (e.g. `FP_JOB_OPEN` or SmartForms function
  module call returns an error) — how is the failure surfaced to the user
  or logged?

---

## 8. Section 14 (Security) — Form-Specific Guidance

Ask the user whether:

- Output device / printer assignment is restricted by user or organizational
  unit
- The form exposes sensitive data (pricing, personal data) that needs
  field-level authorization beyond standard document authorization

Write `N/A` only once the user confirms there is no additional check beyond
standard document-level authorization — do not decide this yourself.

---

## 9. Worked Example (illustrative — generic names)

> **1. Description and Purpose**
> Design and develop a SmartForm-based Customer Invoice output, triggered
> automatically when a billing document is released, showing header
> (customer/company data), a line-item table with tax breakdown, and a
> footer with payment terms.
>
> **3. Technical Solution**
>
> - SmartForms (confirmed with user — no offline/interactive requirement)
> - Custom driver program `Z_INVOICE_PRINT_DRIVER` retrieves and assembles
>   data; layout logic is presentation-only
> - Output determination via classic NACE condition technique, output type
>   `ZINV`
>
> **4. Technical Details**
>
> - Driver Program: `Z_INVOICE_PRINT_DRIVER`
> - SmartForm: `ZSF_INVOICE_01`
>
> **4.1 Pseudo code (excerpt)**
>
> 1. Output determination calls `Z_INVOICE_PRINT_DRIVER` with billing
>    document number
> 2. Read header data from `VBRK`/`VBRP` for the given billing document
> 3. Read customer address via `ADRC` using the billing document's
>    ship-to partner
> 4. Read line items from `VBRP`, calculate line tax via `PRICING_UPDATE`
>    result table
> 5. Calculate invoice total = sum of line totals + total tax
> 6. Call function module generated from `ZSF_INVOICE_01`, passing header,
>    item table, and totals structure
> 7. If billing document has zero line items, raise error and suppress
>    output rather than printing a blank invoice
> 8. Create spool request; return success/failure to output determination
>
> **7.2 SmartForm**
>
> - 7.2.1 Header: company logo (fixed per Sales Org), customer name/address
>   from `ADRC`, invoice number and date
> - 7.2.2 Item: material, description, quantity, unit price, line total,
>   grouped by nothing (flat list), one row per `VBRP` line
> - 7.2.3 Footer: subtotal, tax breakdown by tax code, grand total, payment
>   terms text, page X of Y
> - 7.2.4 Screenshot: [layout rendered from the SmartForm's XML export, attached]

---

## 10. Final Checklist Before Marking a Form TDD Complete

- [ ] All ten §0 inputs were asked for; items 1, 2, 3, 5, and 6 were
      actually supplied before drafting began — if any were missing,
      generation was paused and the user was asked, not guessed around
- [ ] Section 3 states one explicit technology (SmartForms / Adobe / kept
      as SAPscript) — never "TBD"
- [ ] Section 7.2.1–7.2.3 each trace back to a data-retrieval step in
      Section 4.1 — no field appears in the layout description that isn't
      retrieved by the driver program
- [ ] Section 7.2.4 shows the actual layout (from the XML export or the
      PDF/screenshot substitute) — never a fabricated mock image
- [ ] Section 13 covers at minimum: missing mandatory header data + empty
      item table handling + form-generation/spool failure
- [ ] Section 5.5 (Translations) is confirmed with the user, not assumed
      single-language
- [ ] Section 19 left as `[Insert ATC check result screenshot here]` until
      code actually exists
