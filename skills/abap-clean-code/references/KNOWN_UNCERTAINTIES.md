# Known Uncertainties — Verify Before You Activate

The reference files in this skill were compiled from SAP's own style guide, the
SAP-samples repositories and the ABAP keyword documentation. A handful of details
could not be verified against a primary source. They are marked `[?]` where they
appear. Read this file before you hand over generated code that depends on one of
them, and tell the developer which signature to confirm in their own system
(SE24 / SE11 / ADT code completion or F1 on the keyword is faster than guessing).

## Signatures and value lists to confirm in the target system

- `cl_abap_behavior_saver` — the exact set of methods available for redefinition in
  an unmanaged / additional-save RAP implementation.
- `cl_botd_*` (ABAP Test Double Framework) — factory method names differ between
  the classic `cl_abap_testdouble` API and the newer `cl_botd_txbufdbl` /
  `cl_botd_bufdbl` RAP test doubles.
- `FP_FUNCTION_MODULE_NAME` — parameter names of the generated Adobe Forms
  interface function module.
- `cl_bgrfc_destination_outbound` — constructor and unit-creation signature.
- `@AccessControl.authorizationCheck` — the complete list of accepted values
  (`#CHECK`, `#NOT_REQUIRED`, `#NOT_ALLOWED`, `#PRIVILEGED_ONLY`) and which are
  allowed in your release.
- `ANNOTATE VIEW` vs `ANNOTATE ENTITY` — availability depends on release; metadata
  extensions also require `@Metadata.allowExtensions: true` on the view.
- `/iwbep/if_mgw_req_entityset` accessor names (e.g. the search-string getter) vary
  by SAP_GWFND level.
- The ABAP Cloud replacements for `OPEN DATASET` and `AUTHORITY-CHECK` — in ABAP
  Cloud these statements are not released; the substitute API depends on your
  platform version.

## Genuinely release- and database-dependent

- `SELECT ... PACKAGE SIZE` combined with `COMMIT WORK` inside the loop: whether the
  open cursor survives the commit is release- and DB-dependent. Prefer chunking by
  an explicit key range and issuing one `COMMIT WORK` per chunk outside any cursor.
- Release numbering: the ABAP Cloud kernel line (7.84 / 7.87 / 7.90 / 7.93 / 7.96)
  is not the same series as the on-premise line (7.40 - 7.58). Do not answer "is
  this available in my system?" by comparing across the two series.

## Where the mapping is convention rather than SAP rule

Naming conventions for reports, includes, CDS layers and RAP artefacts (the table in
`CLEAN_ABAP.md`) are industry-typical, not SAP-mandated. Only the customer namespace
(`Y`/`Z`/`/NSPC/`), the `E` prefix on lock objects and the `ZZ`/`YY` prefix on append
fields are actually enforced or documented by SAP. Everything else should yield to the
customer's own standards document.
