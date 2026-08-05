---
name: abap-tdd-generator
description: "Use this skill whenever the user wants to create, fill, or update an ABAP Technical Design Document (TDD) — including requests mentioning 'TDD', 'Technical Design Document', 'Technical Documentation', RICEFW object types (Report, Interface, Conversion, Enhancement, Form, Workflow), or a specific ABAP object (CDS View, Class, Function Module, SmartForm, Adobe Form, BAdI) that needs to be documented. Trigger this skill on any request that opens with or closely resembles 'Please create technical documentation...' (or 'create/generate/write/prepare technical documentation for...'), even without further detail — start the intake questions rather than asking the user to rephrase. Also use when the user references the TD_Report_Technical_Design_Document_Template.docx template, asks to generate a technical spec from a Functional Design or from existing ABAP code, or specifically asks to document a SmartForm or Adobe Form (print layout, output determination, header/item/footer logic)."
license: Internal use
---

# ABAP Technical Design Document (TDD) Generator

Generates and fills `TD_Report_Technical_Design_Document_Template.docx`
using the section-by-section rules in `references/general.md` plus a
RICEFW-type-specific reference doc (e.g. `references/report.md`).

---

## Required User Input

Before generating any TDD content, the AI **must** collect the following
minimum inputs from the user. If any of these are missing, ask
before proceeding.

| #   | Input                                                                                                                                                      | Why it's needed                                                                  |
| --- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| 1   | **RICEFW Type** — Report, Interface, Conversion, Enhancement, Form, Workflow, Class, or Function Module                                                    | Determines which reference doc to load and which sections are applicable vs. N/A |
| 2   | **Source Material** — at least one of: a Functional Design (FD) document, actual ABAP source/repository objects, or a short description of the requirement | Provides the content to fill sections 1–4 and beyond                             |
| 3   | **Project Name**                                                                                                                                           | Cover page and Section A                                                         |
| 4   | **Target System** — e.g. S/4HANA on-prem, S/4HANA Cloud, ECC 6.0                                                                                           | Drives architecture options in Section 3                                         |
| 5   | **Module/Business Area** — e.g. MM, SD, FI, WM                                                                                                             | Section A (Business Unit / Area)                                                 |

If the user's request is missing any of inputs 1–5, ask for them in a
single grouped question before starting the document.

---

## Golden Rule — Ask, Never Assume

- Never guess, infer, default, or invent a value for any field.
- If a reference doc suggests a "default" value, treat it as background
  context only — ask the user to confirm.
- The only time a field may be written without asking is when the Section
  Applicability Map says a section is structurally `N/A` for this RICEFW
  type.
- When in doubt about anything, ask.
- **Never cite this skill's own machinery in the document.** Section
  numbers like "§0" or "§1.5", filenames like `enhancement.md`, and
  phrases like "per the classification in..." or "bundled per §0" belong
  in *your* reasoning while drafting, never in the TDD itself. If a
  classification (e.g. "hybrid Enhancement development") is worth
  stating to the reader, state the conclusion and the SAP-facing reason
  for it (why no BAdI exists, why the exits were chosen) — not which
  reference-doc section told you to classify it that way.

---

## Output Location

Every generated/filled TDD `.docx` file must be saved into a folder named
**`ABAP Technical Documentation/`** — create it if it doesn't already exist.
Do not save output files to the working directory root or anywhere else.

- **Filename:** reuse the cover-page title from `general.md`'s Cover Page
  rule, as a filesystem-safe name:
  `Technical Documentation - <Program-Object Name> - V<Version>.docx`
  (e.g. `Technical Documentation - Program Upload Return - V1.0.docx`).
- **Regeneration/new versions:** when a document is regenerated with an
  incremented version (per `general.md` §B, Document History), save it as a
  new file in the same folder rather than overwriting the prior version —
  the version history should be recoverable from the folder itself, not
  just from Section B's table.
- This applies to every RICEFW type this skill produces (Report, Form, and
  any type added later) — the destination folder is not type-specific.

---

## Dependency Checks (run once, before drafting)

This skill needs `python-docx` (to place the process-flow image into the
`.docx` — see `scripts/insert_diagram.py`) and `matplotlib` (to render
that diagram — see `scripts/render_diagram_matplotlib.py`). Both are
pure pip packages with no separate OS-level installer to fight with, but
never assume either is present — check first, every time.

**Step 1 — find a real Python interpreter first.** Don't assume the
command `python` resolves to a working interpreter — on Windows in
particular, `python`/`python3` can silently be a Microsoft Store "App
Execution Alias" stub that isn't a real install and errors out (or
tries to open the Store) even when Python is installed elsewhere on the
machine. Try these in order and use the first one that actually runs
(e.g. responds to `--version` without the Store-redirect error):
1. `python3`
2. `python`
3. `py` (the Windows Python launcher — usually unaffected by the alias
   issue, since it's a separate executable from `python.exe`)

If a candidate fails with something like *"Python was not found; run
without arguments to install from the Microsoft Store..."*, that is the
alias stub, not "Python is missing" — don't try to install anything in
response to it, just move to the next candidate. If all three fail for
real (no Store-redirect message, just "command not found"), then Python
genuinely isn't on PATH — tell the user and ask them to point you to
their Python install (or confirm they want the Markdown fallback below).

Use whichever interpreter resolved for every subsequent command in this
skill (`check_dependencies.py`, `render_diagram_matplotlib.py`,
`insert_diagram.py`) — don't re-resolve per command and don't mix
interpreters within one run.

**Step 2 — run the dependency check:**

```
<resolved-python> scripts/check_dependencies.py
```

This prints a JSON status and, by default, tries to auto-install
whatever is missing (`pip install python-docx`, `pip install
matplotlib`) — a plain pip install, no admin rights or system package
manager needed on any OS. Always try the install before telling the
user something is missing — do not skip straight to reporting "not
available" without having attempted it. Read the result and branch:

- **Either dependency installed successfully** (`installed_now: true`):
  briefly mention it happened (e.g. "installed matplotlib, continuing")
  and proceed — no need to ask permission first, this is a benign local
  install of a well-known package.
- **`python_docx.available` is `false`** (even after the install
  attempt): do **not** attempt to hand-build a `.docx` another way.
  Show the user the `manual_instructions` from the JSON output so they
  can install it themselves if they want to try again, then tell them
  you'll produce the TDD as a **Markdown (`.md`) file** instead, using
  the same section structure and content rules from `general.md` and the
  type-specific reference doc. Save it into the same
  `ABAP Technical Documentation/` folder with the same filename pattern
  (swap `.docx` for `.md`). This is the only sanctioned trigger for the
  Markdown fallback — python-docx being unavailable, and nothing else.
  Never silently skip content or invent a workaround.
- **`matplotlib.available` is `false`** (even after the install
  attempt): the document still stays a `.docx`. Show the user the
  `manual_instructions` from the JSON output, then fill "1.5 High-Level
  Process Flow" with the ordered text list of the flow (the same
  system → action → hand-off list you'd have drawn from) instead of an
  image, clearly labeled so the user knows an image was intended but
  couldn't be rendered in this environment. This is the last resort, not
  the default — always attempt the pip install first.

Only proceed to normal `.docx` + diagram generation once both checks
pass.

---

## Workflow

1. **Identify the RICEFW type.**
   Load the matching file from `references/` (currently available:
   `references/report.md`, `references/form.md`,
   `references/interface.md`, and `references/enhancement.md`). If no
   reference doc exists for the stated type, tell the user and ask how to
   proceed.

2. **Gather source material.**
   Confirm the user has provided at least one source (FD, ABAP code, or
   requirement description). If none, ask.

   **If the RICEFW type is Form (SmartForm / SAPscript / Adobe Form),**
   also ask for the Form-specific inputs listed in `references/form.md` §0
   before drafting — Section 7 of the template cannot be filled responsibly
   from a generic FD alone (layout, header/item/footer zones, and output
   determination are usually undocumented anywhere else). Ask for these as
   one grouped question, the same way as the five inputs above. **This is
   a hard gate:** if the user cannot provide the form's layout (ideally its
   XML export, or a PDF/screenshot substitute) or any of the other minimum
   items listed in `references/form.md` §0, do not generate the TDD — tell
   the user what's missing and wait, rather than drafting around it with
   placeholders.

   **If the RICEFW type is Enhancement** (user exit, BAdI, enhancement
   spot/point, or direct modification), also ask for the
   Enhancement-specific inputs listed in `references/enhancement.md` §1
   before drafting — in particular the enhancement technique, the exact
   standard process/exit being modified, and the activation/gating logic.
   **This is a hard gate:** if the user cannot confirm the technique, the
   exact exit/BAdI being used, and the gating condition, do not generate
   the TDD — an Enhancement documented without a clear gating rule risks
   silently misrepresenting when standard SAP behavior is and isn't
   affected. Also apply `references/enhancement.md` §0's hybrid-development
   note when the enhancement is reached via a bundled API class or driver
   report — ask the user to confirm whether that belongs in the same
   document before drafting Section 6/5.3.

3. **Check the provided source is actually complete.**
   If the user provided ABAP source code (a program, class, etc.) rather
   than just an FD or description, scan it for references to other custom
   development objects that were **not** provided:
   - `INCLUDE` statements
   - `PERFORM ... IN PROGRAM` / subroutine pools
   - `CALL FUNCTION` targeting a custom (Z*/Y*) function module
   - Instantiation of or calls to a custom (Z*/Y*) class
   - Any other custom (Z*/Y*) object referenced but not in what was
     supplied (custom table, BAdI implementation, etc.)

   If any are found, list them by name and ask the user to also provide
   their source before drafting sections that depend on that logic
   (typically Section 4.1 Pseudo Code and Section 9 Classes). Documenting
   what an unprovided include/FM/class does from its name alone is a guess,
   which the Golden Rule below prohibits — ask instead of inferring.
   Standard SAP objects (non-Z/Y, e.g. `BAPI_MATERIAL_SAVEDATA`) don't need
   their source provided — describe their use as normal.

4. **Load the baseline rules.**
   Read `references/general.md` for universal fill rules, then the
   type-specific reference doc for its Section Applicability Map.

5. **Draft section by section.**
   - Source material clearly states the answer → write it.
   - Source material is silent or ambiguous → ask the user. Batch related
     questions together per section.
   - Section is structurally `N/A` per the applicability map → write `N/A`.
   - **Section 4.1 Pseudo Code:** attach real ABAP code per numbered
     step, not language-agnostic description — see `general.md` §4.1.
   - **Section 12.1 (and non-trivial 12.3):** for every custom table,
     add the full field-level table + Purpose + Key Design detail block
     described in `general.md` §12, not just a one-line summary row.

5.1. **Build and insert the 1.5 High-Level Process Flow diagram.**
   Do this after the rest of the document's text is filled and saved.
   Draft the flow as boxes/arrows per `general.md` §1.5, tracing the
   **complete process from the initial trigger to the final outcome** —
   not just the portion you're confident about. If the provided code or
   source material doesn't make some step or hand-off clear, ask the
   user before drawing it; do not guess, and do not simply stop the
   diagram at the last step that was clear and present that as the full
   picture. Save the drafted flow as a small JSON step list (see
   `scripts/render_diagram_matplotlib.py`'s docstring for the shape),
   then render it:
   ```
   <resolved-python> scripts/render_diagram_matplotlib.py <steps.json> <output.png>
   ```
   and insert the PNG with
   `<resolved-python> scripts/insert_diagram.py <docx_path> <image_path>`
   (the same interpreter resolved in Dependency Checks) to place it into
   the "1.5 High-Level Process Flow" placeholder — do not hand-edit the
   OOXML drawing/relationship parts. Re-render the doc to PDF and view it
   afterward to confirm the image landed in the right place. If
   `matplotlib.available` was `false` in the Dependency Checks, follow
   the text-list fallback described there instead of this step.

6. **Always ask explicitly for:**
   - D. Approval Details (names, roles, signatures)
   - A. Business/Process Owner, Functional Designer, Technical Lead names
   - Priority / Complexity ratings
   - Formal Status changes
   - Architecture pattern choice (Section 3) — present options, let user pick
   - Any value not clearly stated in the source material

7. **Before presenting the document, re-read it for leaked meta/instructional text.**
   Go section by section and ask: *would a client reading this be able to
   tell a reference doc or an internal skill produced it?* Specifically
   look for and rewrite/remove:
   - Section-symbol references like `§0` or `§1.5`, or filenames like
     `enhancement.md`, `general.md`, `report.md`, `form.md`,
     `interface.md`
   - Phrases like "per the classification in...", "bundled per §0",
     "golden rule", "ask the user", "the AI assistant"
   - Any leftover `[To be completed]` placeholder that was never resolved

   If a classification (e.g. "this is a hybrid Enhancement development")
   is worth stating to the reader, state the conclusion and the
   SAP-facing reason for it (why no BAdI exists, why these exits were
   chosen) — never which reference-doc section told you to classify it
   that way. This is a real re-read of the drafted text, not a mental
   note made while writing it — the two are different passes and the
   first one is exactly what missed this before.

8. **Before finalizing, summarize open items.**
   List any section still marked `[To be completed]` and ask the user to
   resolve them.

---

## Files in This Skill

| File                                                          | Purpose                                                                                         |
| ------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| `templates/TD_Report_Technical_Design_Document_Template.docx` | The blank template to fill — includes a "1.5 High-Level Process Flow" placeholder for the diagram image |
| `scripts/check_dependencies.py`                               | Run first, every time. Checks for `python-docx` and `matplotlib`, both plain pip packages; auto-installs whichever is missing (no admin/system package manager needed) and returns manual install instructions when it can't. Reports JSON status so the AI can decide between normal `.docx`+diagram generation and the Markdown/text-list fallbacks |
| `scripts/insert_diagram.py`                                   | Inserts a rendered diagram PNG into the "1.5 High-Level Process Flow" placeholder using python-docx; see `general.md` §1.5. Requires `python-docx` (checked/installed by `check_dependencies.py`) |
| `scripts/render_diagram_matplotlib.py`                        | Renders the process-flow diagram as a top-to-bottom box/arrow PNG using matplotlib — no Graphviz or other OS-level binary needed. See its docstring for the input JSON shape (ordered list of `{label, edge_label}` steps) |
| `references/general.md`                                       | Section-by-section fill rules for every TDD regardless of RICEFW type — including §1.5 (process flow diagram), §4.1 (pseudo code with real ABAP), and §12 (full field-level custom table docs) |
| `references/report.md`                                        | Report guidance — covers both **Fiori** (RAP/CDS/OData) and **Classic ABAP** (ALV/list) flavors; §0 has the flavor-clarification question |
| `references/form.md`                                          | Form-specific guidance for SAPscript/SmartForms/Adobe Forms — includes the required-inputs checklist (§0) to ask the user before drafting Section 7 |
| `references/interface.md`                                     | Interface-specific guidance (inbound/outbound, ALE/IDoc, proxy, REST/OData, file-based) — includes the required-inputs checklist (§0) |
| `references/enhancement.md`                                   | Enhancement-specific guidance (BAdI, enhancement spot/point, classic user/function/field/menu/screen/search-help exits, modifications) — includes the required-inputs checklist (§1) and the hybrid-development classification note (§0) |
| `references/<type>.md`                                        | (To be added) Conversion, Workflow, Class, Function Module                          |
