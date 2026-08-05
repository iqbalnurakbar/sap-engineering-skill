# Reference: RICEFW Type "Interface"

Use this reference whenever the object being documented is an **Interface**
— any development whose primary purpose is to **exchange data between SAP
and something outside the specific transaction/report being run**: another
system, a middleware layer, or a file (including a file a business user
uploads/downloads as part of normal recurring operations).

This covers:

- **Inbound** — data entering SAP: IDoc, proxy (SOAP/REST), RFC call from
  an external system, or a file read and posted via BAPI/`CALL TRANSACTION`
- **Outbound** — data leaving SAP: IDoc, proxy, RFC call to an external
  system, or a file generated and sent (SFTP, email attachment, AL11
  directory for pickup)
- **Bidirectional** — request/response pattern (synchronous RFC/proxy
  call-and-wait, or an outbound message with a corresponding inbound
  acknowledgment)

**Does not cover:**
- **One-time/cutover data loads** (legacy migration, go-live master/
  transactional data load run once or a handful of times and then
  retired) — that's a **Conversion**, even if it technically uses the same
  BAPI-call pattern. Ask the user: *"Will this run repeatedly as part of
  normal operations, or is it a one-off/cutover load?"* — recurring →
  Interface, one-off → Conversion.
- **Read-only data retrieval with no external exchange** (a program that
  only reads SAP data and displays/downloads it, with nothing being posted
  anywhere) — that's a **Report**, even if the output happens to be an
  Excel file. The distinguishing question is direction of data flow: does
  anything get *written* to SAP or to an external system/file as a result
  of this program running? If yes → Interface. If it's purely SAP → local
  file with no write-back and no repeated exchange, it's a Report.
- **Printed/PDF output** — that's a Form, even if data is pulled from
  multiple systems to build it.

If a single program does both (e.g. downloads current data to Excel for
the user to edit, then re-uploads it via BAPI), classify the whole
development as an **Interface** (the write side is the one that carries
data-integrity risk and needs the fuller error-handling treatment) and
document the download step as a supporting feature within Section 2.

---

## 0. Required Inputs — Ask the User Before Drafting

An Interface TDD depends on details that are rarely fully captured in a
generic FD. **Before drafting Sections 3, 4, 6, and 13, ask the user for
the following as one grouped question** (skip any item already supplied):

| # | Input | Why it's needed |
|---|-------|------------------|
| 1 | **Direction** — Inbound, Outbound, or Bidirectional | Determines the whole shape of Section 3 and 4.1 |
| 2 | **Technology** — IDoc/ALE, proxy (SOAP/REST via PI/PO, CPI, or API Management), direct RFC, or file-based (SFTP/AL11 + BAPI/`CALL TRANSACTION`) | Determines §2 architecture options and Section 6 wording |
| 3 | **Source and target systems** — the actual system names/IDs on both ends, not just "SAP" and "external system" | Section 1 and Section 6 |
| 4 | **Trigger** — real-time/event-driven, scheduled batch job, or manual execution | Section 1.2 and Section 4.1 entry point |
| 5 | **Message/file structure** — IDoc basic type + segments, XSD/WSDL, or file layout (field list, delimiters, header/trailer records) | Section 6 (mapping table) and Section 12 if custom structures are created |
| 6 | **Field mapping** — source field → target field, including any transformation/lookup rules (e.g. unit-of-measure conversion, code-value mapping) | Section 4.1 step-by-step and Section 6 |
| 7 | **Volume and frequency** — records per run, runs per day/hour | Section 1.3 and informs whether background job scheduling needs discussion |
| 8 | **Error handling & reprocessing expectations** — should failed records stop the whole run or be skipped and logged for reprocessing? Is there an existing monitoring transaction/report the business already uses? | Section 13 — this is usually the most safety-critical part of an Interface TDD |
| 9 | **Middleware involved**, if any (PI/PO, CPI, API Management, or none/direct) | Section 6 and Section 3 |
| 10 | **Authentication/security mechanism** — technical user, certificate, OAuth, trusted RFC connection | Section 14 |

**Fill Rule — hard gate, do not generate without this:** items 1, 2, 3,
4, and 8 are the minimum required set. If the user leaves any of these
unanswered after being asked, **do not generate the Interface TDD.** Tell
the user plainly which item(s) are still missing and why they matter, and
wait — do not draft around missing direction, technology, or error-handling
expectations with a placeholder.

---

## 1. Section Applicability Map

| Section | Applies to Interface? | Notes |
|---|---|---|
| A–D (Admin) | Always | No change from general guidance |
| 1. Description and Purpose | **Core** | State direction, source/target systems, and business purpose of the exchange |
| 1.2 Trigger event | **Core** | Never `N/A` — real-time, scheduled, or manual, per §0 item 4 |
| 1.5 High-Level Process Flow | **Core** | Source system → transport (IDoc/proxy/file/API) → SAP inbound processing → target object, as boxes |
| 2. Functional Details | **Core** | One bullet per data object exchanged + the mapping/transformation rules |
| 3. Technical Solution | **Core** | Pick architecture pattern — see §2 below |
| 4. Technical Details + 4.1 Pseudo code | **Core** | The most detailed section — see §4 below |
| 5.1–5.2 Package / T-code | Fill if a custom monitoring T-code/report is built; otherwise `N/A` | |
| 5.3 Reports/Module Pools | Fill with driver/monitoring program names, if any | |
| 5.4 Selection-Screen | Fill only if there's a manual-execution/monitoring selection screen; `N/A` for pure event-driven interfaces | |
| 5.5 Translations | Fill only if the interface produces user-facing text (e.g. error messages shown in a monitor); often `N/A` | |
| 6. Interface | **Core — this is the primary section for this RICEFW type.** See §5 below | |
| 7. Forms | `N/A` unless the interface also triggers a printed form as a side effect | |
| 8. Workflow | `N/A` unless a failed/exception record triggers an SAP Business Workflow task for manual resolution | |
| 9. Classes | Fill if custom mapping/processing classes exist (proxy implementation class, IDoc processing class); otherwise `N/A` | |
| 10. Web Services | **Core** if the technology is a proxy/REST/SOAP service; `N/A` for IDoc or pure file-based | |
| 11. Enhancement | Fill only if a BAdI/user-exit is used for mapping enrichment (e.g. IDoc extension BAdI); otherwise `N/A` | |
| 12. DB Dictionary Objects | Fill if new Z-structures/tables were created for staging, mapping, or logging | |
| 13. Error Handling | **Core** — this section carries the most weight for an Interface; see §7 below | |
| 14. Security | **Core** — authentication mechanism and authorization for the technical/communication user | |
| 17. Transport Requests | Always | |
| 19. ATC Check | Always | |

---

## 2. Architecture Decision (fill Section 3)

**Do not pick a technology yourself.** Present the relevant options below —
based on the direction and technology stated in §0 — and ask the user to
confirm before writing Section 3.

| Situation | Option to present |
|---|---|
| Exchange with another SAP system, or a non-SAP system that supports IDoc | **ALE/IDoc**: outbound via message type + partner profile (`WE20`), inbound via IDoc posting program; confirm basic type and any extension needed |
| Exchange with a non-SAP system, synchronous request/response needed | **Proxy (SOAP/REST) or direct RFC**, typically via middleware (PI/PO, CPI) if the project uses one, or a direct connection if not |
| Exchange with a non-SAP system, asynchronous / no synchronous response needed, no middleware in place | **File-based**: SFTP/AL11 pickup, driver program reads and posts (inbound) or extracts and writes (outbound) |
| Recurring business-user-driven upload (user prepares a file locally, uploads periodically) | **File-based inbound**: user-triggered upload (`GUI_UPLOAD`/`CL_GUI_FRONTEND_SERVICES` or an app-based upload) → validation → BAPI call; confirm this is recurring (Interface) not one-off (Conversion) per the scope note above |

Once the user confirms a technology, note in Section 3 whether middleware
(PI/PO, CPI, API Management) is involved or the connection is direct —
this materially changes what Section 6 needs to document (middleware
mapping/routing vs. direct point-to-point mapping).

---

## 3. Section 2 (Functional Details) — Interface-Specific Guidance

**2.1 Current functionality**: for a net-new interface, `N/A`. If replacing
an existing interface, name it and state what's changing.

**2.2 Required functionality** — structure as one bullet per data object
exchanged:

```
- Object: <e.g. "Sales Order confirmation">
- Direction: <Inbound/Outbound>
- Trigger: <e.g. "Real-time on goods issue posting">
- Key fields exchanged: <field list or reference to Section 6 mapping table>
- Volume: <records per run, frequency>
```

If multiple data objects are exchanged by the same interface (e.g. header
+ line items as separate IDoc segments, or multiple message types), list
each as its own bullet block — this naming must be reused consistently in
Sections 4 and 6.

---

## 4. Section 4.1 (Pseudo Code) — Interface-Specific Style

Write the pseudo-code as a **numbered list of atomic actions**, grouped in
this order (skip groups that don't apply):

1. **Entry point** — how the interface is triggered (IDoc inbound process
   code, proxy method call, scheduled job `START-OF-SELECTION`, or file
   pickup)
2. **Data extraction/reading** — for outbound: source data selection; for
   inbound: reading the IDoc segments, proxy payload, or file content
3. **Validation** — mandatory field checks, format checks, duplicate
   checks — **before** any mapping or posting is attempted
4. **Mapping/transformation** — one line per field mapping or
   transformation rule, referencing the Section 6 mapping table rather
   than repeating it in full
5. **Target call** — the BAPI/function module call (inbound) or the
   message/file construction and send (outbound); name the actual
   BAPI/IDoc type/proxy operation once known
6. **Success handling** — commit, status update, acknowledgment sent (if
   bidirectional)
7. **Exception path** — what happens per validation/mapping/posting
   failure: does the run stop, or is the record skipped and logged? This
   must match what the user confirmed in §0 item 8 — do not assume
   "skip and continue" or "stop on first error" without asking
8. **Logging** — where results are logged (application log via `BAL`,
   custom Z-table, or standard IDoc/monitoring transaction) so the error
   handling described in step 7 is actually traceable

**Fill Rule:** if the interface handles multiple data objects (per §3),
write one complete numbered sequence per object, back to back.

---

## 5. Section 6 (Interface) — Detailed Guidance

This is the section this reference type exists to support.

- **Systems involved**: name source and target systems explicitly (per §0
  item 3), and the middleware layer if any.
- **Message/file structure**: IDoc basic type + segments, or WSDL/XSD
  reference, or file layout — reuse whatever the user supplied in §0 item 5.
- **Field mapping table**: one row per field — Source Field / Target Field
  / Transformation or Lookup Rule / Mandatory (Y/N). This table is the
  single source of truth that Section 4.1 step 4 should point back to,
  not duplicate.
- **Frequency/volume**: restate from §0 item 7 for a reader who only reads
  this section.

---

## 6. Section 9 (Classes) / Section 10 (Web Services) — Interface-Specific Guidance

Fill Section 9 if a custom class exists (e.g. a proxy implementation class,
a custom IDoc processing class, or a mapping/helper class):

| Element | Fill with |
|---|---|
| Class name | `ZCL_<SHORT_NAME>_IF` |
| Purpose | e.g. "Implements inbound proxy interface, validates and posts via BAPI_SALESORDER_CREATEFROMDAT2" |
| Key methods | One row per method: validation, mapping, posting, error logging |

Fill Section 10 if the technology is a proxy/REST/SOAP service — name the
service, operation(s), and whether it's synchronous or asynchronous. Leave
`N/A` for IDoc or pure file-based interfaces.

If no custom class is needed (e.g. a simple IDoc posting using a standard
function module with no custom wrapper), state that explicitly rather than
leaving the section blank — confirm with the user rather than deciding it
yourself, per `general.md`'s Golden Rule.

---

## 7. Section 13 (Error Handling) — Interface-Specific Guidance

This section carries more weight for an Interface than for most other
RICEFW types, because a silent failure here means lost or duplicated
business data. At minimum, cover:

- **Validation failures** — which checks run before posting, and what
  happens to a record that fails one (per §0 item 8 and pseudo-code step 7)
- **Partial-run behavior** — does one bad record stop the whole batch, or
  does the batch continue and log the bad record for reprocessing?
- **Duplicate handling** — how does the interface avoid processing the
  same inbound message/file twice (idempotency check, sequence number,
  status flag)?
- **Reprocessing mechanism** — how does the business reprocess a failed
  record: manual re-trigger, standard IDoc reprocessing (`BD87`), or a
  custom monitoring report?
- **Monitoring/alerting** — who gets notified on failure, and how (email,
  application log, dashboard)? Confirm with the user rather than assuming
  none exists.

---

## 8. Section 14 (Security) — Interface-Specific Guidance

State explicitly:

- The authentication mechanism for the connection (technical user +
  password, certificate-based, OAuth, trusted RFC destination)
- Whether the technical/communication user's authorization is scoped
  narrowly to only what this interface needs, or reuses a broader existing
  user — flag the latter to the user as something they may want to revisit
- Any data sensitivity considerations (PII, financial data) that affect
  transport security (e.g. must the connection be encrypted/TLS)

Write `N/A` only if the user confirms there's genuinely no additional
security consideration beyond standard RFC/HTTP connection security — do
not decide this yourself.

---

## 9. Worked Example (illustrative — generic names)

> **1. Description and Purpose**
> Design and develop an inbound interface to receive Sales Order
> confirmations from a 3rd-party e-commerce platform via REST proxy in
> real time, and post them into SAP using `BAPI_SALESORDER_CREATEFROMDAT2`.
>
> **3. Technical Solution**
>
> - Inbound REST proxy via SAP API Management (no PI/PO in this
>   landscape, per user confirmation)
> - Custom class `ZCL_ECOM_ORDER_IF` implements the proxy interface,
>   validates payload, maps fields, and calls the BAPI
> - Failed records logged to the application log (`BAL`) and skipped;
>   batch continues — confirmed with user as the required behavior
>
> **4. Technical Details**
>
> - Proxy service: `Z_ECOM_ORDER_INBOUND`
> - Class: `ZCL_ECOM_ORDER_IF`
> - BAPI: `BAPI_SALESORDER_CREATEFROMDAT2`
>
> **4.1 Pseudo code (excerpt)**
>
> 1. Proxy method `CREATE_ORDER` receives JSON payload
> 2. Deserialize payload into internal structure
> 3. Validate mandatory fields (Customer Number, Material, Quantity); if
>    any missing, log to application log and return error response —
>    do not stop the interface for other incoming calls
> 4. Check for duplicate order (external order ID already processed) via
>    `Z_ECOM_ORDER_LOG` lookup; if duplicate, log and skip
> 5. Map external Customer ID to SAP Customer Number via lookup table
>    `ZECOM_CUST_MAP`
> 6. Call `BAPI_SALESORDER_CREATEFROMDAT2` with mapped header and item data
> 7. If BAPI returns error, log full error message to application log
>    with external order ID for reprocessing reference
> 8. If successful, commit and write success entry to `Z_ECOM_ORDER_LOG`
>    with SAP Sales Order number
> 9. Return synchronous response (success + SAP order number, or error) to
>    the calling e-commerce platform
>
> **6. Interface**
>
> - Systems: `ECOM-PLATFORM` (source) → `S4H-PRD` (target), via SAP API
>   Management (no additional middleware transformation)
> - Field mapping: External Customer ID → Customer Number (via
>   `ZECOM_CUST_MAP`), External SKU → Material Number (direct 1:1),
>   Quantity → Order Quantity (unit conversion EA→SAP base UoM)
> - Volume: ~500 orders/day, real-time, no batching

---

## 10. Final Checklist Before Marking an Interface TDD Complete

- [ ] All ten §0 inputs were asked for; items 1, 2, 3, 4, and 8 were
      actually supplied before drafting began — if any were missing,
      generation was paused and the user was asked, not guessed around
- [ ] Section 3 states one explicit technology and direction — never "TBD"
- [ ] Section 6's field mapping table is the single source of truth;
      Section 4.1 references it rather than duplicating it
- [ ] Section 13 covers at minimum: validation failure handling +
      partial-run/duplicate/reprocessing behavior, matching what the user
      confirmed (not assumed)
- [ ] Section 14 states the authentication/authorization approach or
      explicitly confirms none beyond standard connection security
- [ ] If this development also reads/downloads data (not just posts it),
      confirm it's still correctly classified as Interface (write side
      dominates) rather than incorrectly split into a separate Report doc
- [ ] Section 19 left as `[Insert ATC check result screenshot here]` until
      code actually exists
