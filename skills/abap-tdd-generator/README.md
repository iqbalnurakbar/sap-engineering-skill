# ABAP TDD Generator

An AI agent skill that generates and fills SAP ABAP **Technical Design Documents (TDDs)** from a Functional Design, existing ABAP source code, or a plain-language requirement description — output as a polished `.docx` using the standard `TD_Report_Technical_Design_Document_Template.docx`.

Works with any SKILL-spec compatible agent framework (Claude Code, OpenCode, Cursor, etc.).

## What It Does

Point the skill at a RICEFW object — Report, Interface, Conversion, Enhancement, Form, Workflow, Class, or Function Module — and it will:

- Ask for the minimum required inputs (RICEFW type, source material, project name, target system, module/business area)
- Load the correct section-by-section fill rules for that object type
- Draft the TDD section by section from your source material
- **Never guess or invent values** — if something isn't in the source material, it asks instead of assuming
- Detect incomplete source (e.g. `INCLUDE`s, custom Z/Y function modules or classes referenced but not provided) and ask for the missing pieces before drafting
- Save the finished `.docx` into an `ABAP Technical Documentation/` folder, versioned by filename

## Supported RICEFW Types

| Type | Reference | Notes |
|---|---|---|
| Report | `references/report.md` | Covers both Fiori (RAP/CDS/OData) and Classic ABAP (ALV/list) |
| Form | `references/form.md` | SAPscript / SmartForms / Adobe Forms — has a hard input gate before drafting Section 7 |
| Interface | `references/interface.md` | ALE/IDoc, proxy, REST/OData, file-based |
| Enhancement | `references/enhancement.md` | BAdI, enhancement spot/point, classic exits, modifications — has a hard gate on gating logic |
| Conversion, Workflow, Class, Function Module | *(planned)* | Reference docs not yet added |

## Repo Structure

```
abap-tdd-generator/
├── SKILL.md                 # Skill definition, trigger conditions, workflow
├── templates/
│   └── TD_Report_Technical_Design_Document_Template.docx
└── references/
    ├── general.md            # Universal fill rules for every TDD
    ├── report.md
    ├── form.md
    ├── interface.md
    └── enhancement.md
```

## Golden Rule

**Ask, never assume.** No field is filled with a guessed, inferred, or "reasonable default" value — every value not explicitly present in the source material is confirmed with the user first. The only exception is sections marked structurally `N/A` for a given RICEFW type.

## Usage

Trigger the skill with a request like:

> "Please create technical documentation for this BAdI enhancement"
> "Generate a TDD for this CDS-based report"
> "Document this SmartForm using the TD template"

The skill will ask a single grouped question for any missing required inputs, then draft the document section by section, flagging open items for you to resolve before finalizing.

## License

Internal use.
