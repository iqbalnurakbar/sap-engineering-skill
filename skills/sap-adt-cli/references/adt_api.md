# SAP ADT REST API — Quick Reference

SAP ABAP Development Tools (ADT) exposes a REST API under `/sap/bc/adt/`.
Authentication is HTTP Basic Auth with the `X-SAP-Client` header for client selection.

## Authentication

Every request requires:

```
Authorization: Basic base64(username:password)
X-SAP-Client: <client_number>
```

For POST/PUT requests, first fetch a CSRF token:

```
GET <any ADT URL>
x-csrf-token: fetch
→ Response header: x-csrf-token: <token>

Then include in POST/PUT:
x-csrf-token: <token>
```

## Source Code Endpoints (Read)

| Object Type | Method | URL Pattern |
|-------------|--------|-------------|
| Program (report) | GET | `/sap/bc/adt/programs/programs/{name}/source/main` |
| Class | GET | `/sap/bc/adt/oo/classes/{name}/source/main` |
| Interface | GET | `/sap/bc/adt/oo/interfaces/{name}/source/main` |
| Function Group | GET | `/sap/bc/adt/functions/groups/{fg_name}/source/main` |
| Function Module | GET | `/sap/bc/adt/functions/groups/{fg_name}/fmodules/{fm_name}/source/main` |
| Include | GET | `/sap/bc/adt/programs/includes/{name}/source/main` |
| CDS View (DDL) | GET | `/sap/bc/adt/ddic/ddl/sources/{name}/source/main` |
| Type Group | GET | `/sap/bc/adt/typegroups/groups/{name}/source/main` |
| DDIC Table | GET | `/sap/bc/adt/ddic/tables/{name}/source/main` |
| DDIC Structure | GET | `/sap/bc/adt/ddic/structures/{name}/source/main` |
| Domain | GET | `/sap/bc/adt/ddic/domains/{name}/source/main` |
| Data Element | GET | `/sap/bc/adt/ddic/dataelements/{name}` |

Object names must be URL-encoded. Responses are plain text (ABAP source) or XML.

## Write Source — Lock / PUT / Unlock

Three-step flow; unlock must always run (use `finally`).

### 1. Lock

```
POST /sap/bc/adt/{object_uri}?method=lock
X-sap-adt-sessiontype: stateful
→ Response header: com.sap.adt.lock.handle: <handle>
```

If the header is absent, fall back to parsing `<handle>` or `<lockHandle>` from the XML response body.

### 2. Write (PUT)

```
PUT /sap/bc/adt/{object_uri}/source/main
Content-Type: text/plain; charset=utf-8
X-sap-adt-lock-handle: <handle>

[optional] ?sap-cts-request=<TRKORR>    ← assign to specific transport
```

Body: plain text ABAP source.

### 3. Unlock

```
POST /sap/bc/adt/{object_uri}?method=unlock
X-sap-adt-lock-handle: <handle>
```

## Activation

```
POST /sap/bc/adt/activation
Content-Type: application/vnd.sap.adt.activation.request+xml; charset=utf-8

<?xml version="1.0" encoding="utf-8"?>
<adtcore:objectReferences xmlns:adtcore="http://www.sap.com/adt/core">
  <adtcore:objectReference adtcore:uri="{object_uri}" adtcore:name="{OBJECT_NAME}"/>
</adtcore:objectReferences>
```

Response: empty (200) = success. Non-empty XML body = activation errors — parse `severity`, `text` attributes.

## Syntax Check

```
POST /sap/bc/adt/abapsource/syntaxcheck
Content-Type: application/vnd.sap.adt.abapsource.syntaxcheckresult+xml; charset=utf-8

<?xml version="1.0" encoding="utf-8"?>
<adtcore:objectReferences xmlns:adtcore="http://www.sap.com/adt/core">
  <adtcore:objectReference adtcore:uri="{object_uri}" adtcore:name="{OBJECT_NAME}"/>
</adtcore:objectReferences>
```

Response: XML with `severity` (`error`/`warning`/`info`), `text`, and `line` attributes. Empty body = no issues.

## Where-Used

```
GET /sap/bc/adt/repository/informationsystem/whereused
    ?uri=<full_object_url>        ← full URL including scheme+host
    &maxResults=50
Accept: application/vnd.sap.adt.repository.informationsystem.whereused+xml
```

Response: XML with `adtcore:objectReference` elements (namespace `http://www.sap.com/adt/core`), attributes: `adtcore:name`, `adtcore:type`, `adtcore:uri`.

## Open SQL Data Preview

```
GET /sap/bc/adt/datapreview/freestyle
    ?rowNumber=<max_rows>
    &sqlCommand=<url-encoded-SELECT>
Accept: application/xml
```

Response: XML with `<column name="...">` elements containing row data. Requires `/sap/bc/adt/datapreview` activated in SICF.

Only `SELECT` is valid. DML (`INSERT`, `UPDATE`, `DELETE`, `MERGE`, `MODIFY`, `TRUNCATE`) must be blocked at the CLI layer.

## Search

```
GET /sap/bc/adt/repository/informationsystem/search
    ?operation=quickSearch
    &query=<url-encoded-query>      ← supports * wildcard
    &maxResults=100
```

Response: XML with matching objects.

## Package Contents

```
POST /sap/bc/adt/repository/nodestructure
     ?parent_type=DEVC/K
     &parent_name=<url-encoded-package>
     &withShortDescriptions=true
```

Response: XML. Relevant nodes:
```xml
<SEU_ADT_REPOSITORY_OBJ_NODE>
  <OBJECT_TYPE>PROG</OBJECT_TYPE>
  <OBJECT_NAME>ZMYPROGRAM</OBJECT_NAME>
  <DESCRIPTION>My Program</DESCRIPTION>
  <OBJECT_URI>/sap/bc/adt/programs/programs/ZMYPROGRAM</OBJECT_URI>
</SEU_ADT_REPOSITORY_OBJ_NODE>
```

## Transaction Properties

```
GET /sap/bc/adt/repository/informationsystem/objectproperties/values
    ?uri=%2Fsap%2Fbc%2Fadt%2Fvit%2Fwb%2Fobject_type%2Ftrant%2Fobject_name%2F{tx_name}
    &facet=package
    &facet=appl
```

## Transport Requests

**The CTS endpoints are NOT the same on every backend.** ADT registers them in
`CL_CTS_ADT_RES_APP->register_resources`, which branches on whether the call
arrives over HTTP:

```abap
if ( me->http_call = abap_true ).     " base path /sap/bc/adt
    register /cts/transports
    register /cts/transportchecks
    return.                            " <- nothing else is registered
endif.
                                       " base path /sap/bc/cts (no ICF node)
    register /transportrequests ...
```

On newer releases (S/4HANA) the transport organizer is served under
`/sap/bc/adt/cts/transportrequests`. On ECC it is not registered over HTTP at
all. The CLI therefore requires `platform` (`s4` / `ecc`) to be configured, and
the skill must **ask the user** which it is rather than infer it.

Telling the two 404s apart:

| Body | Content-Type | Meaning |
|---|---|---|
| `No suitable resource found` | `text/plain` | ICF routing is fine; that URI is not registered for this release |
| `Service cannot be reached` (HTML page) | `text/html` | The ICF node itself is missing or unpublished |

### List transports — S/4HANA

```http
GET /sap/bc/adt/cts/transportrequests?user=<USER>&requestStatus=<D|R>
```

`requestStatus` must be sent server-side; otherwise only the released worklist
comes back.

### List transports — ECC

```http
GET /sap/bc/adt/cts/transports?_action=FIND&user=<USER>&trfunction=K
```

Handled by `CL_CTS_ADT_RES_OBJ_RECORD->find`, which calls
`CTS_WBO_API_READ_REQUESTS`. Response is `asx:abap` with one `CTS_REQ_HEADER`
element per request (`TRKORR`, `TRFUNCTION`, `TRSTATUS`, `TARSYSTEM`,
`AS4USER`, `AS4DATE`, `AS4TIME`, `AS4TEXT`, `CLIENT`). There is no server-side
status filter, so filter the parsed rows. It generally returns only modifiable
requests, so `--status R` is usually empty.

### Create transport — S/4HANA

```http
POST /sap/bc/adt/cts/transportrequests
Content-Type: application/vnd.sap.adt.transportorganizer.v1+xml
```

```xml
<tm:root xmlns:tm="http://www.sap.com/cts/adt/tm" tm:useraction="newrequest">
  <tm:request tm:desc="<DESCRIPTION>" tm:type="K" tm:target="<TARGET>" tm:cts_project="">
    <tm:task tm:owner="<USER>"/>
  </tm:request>
</tm:root>
```

`tm:type` is `K` for Workbench, `W` for Customizing. The target system is chosen
by the user — never defaulted, even when the value help offers one candidate:

```http
GET /sap/bc/adt/cts/transportrequests/valuehelp/target?maxItemCount=50
```

### Create transport — ECC

```http
POST /sap/bc/adt/cts/transports
Content-Type: application/vnd.sap.as+xml; charset=UTF-8; dataname=com.sap.adt.CreateCorrectionRequest
```

```xml
<asx:abap xmlns:asx="http://www.sap.com/abapxml" version="1.0"><asx:values><DATA>
  <DEVCLASS><PACKAGE></DEVCLASS>
  <REQUEST_TEXT><DESCRIPTION></REQUEST_TEXT>
</DATA></asx:values></asx:abap>
```

Handled by `CL_CTS_ADT_RES_OBJ_RECORD->post` (`CO_RESOURCE_ID = 'TransportRequest'`),
which reads a `SADT_CREATE_CORR_REQUEST` and calls
`TR_INSERT_REQUEST_WITH_TASKS`, then `TR_INSERT_NEW_COMM` for the task.
Consequences:

- **The target is not passed.** The backend derives it from the package via
  `TR_DEVCLASS_GET` then `TR_GET_TRANSPORT_TARGET`, falling back to `LOCAL`.
  So the package is mandatory and `--target` is meaningless.
- **The type is hardcoded to `K`** (Workbench); Customizing is not selectable.
- **The response is `text/plain`** — a URI whose last segment is the `TRKORR`,
  not XML and not a `Location` header.
- An empty or unknown `DEVCLASS` fails in `TR_DEVCLASS_GET` and surfaces as
  HTTP 500 `Resource   could not be successfully created.`

### Which transports may an object go into (both platforms)

```http
POST /sap/bc/adt/cts/transportchecks
Content-Type: application/vnd.sap.as+xml; charset=UTF-8; dataname=com.sap.adt.transport.service.checkData
```

```xml
<asx:abap xmlns:asx="http://www.sap.com/abapxml" version="1.0"><asx:values><DATA>
  <PGMID>R3TR</PGMID><OBJECT>PROG</OBJECT><OBJECTNAME><NAME></OBJECTNAME>
  <DEVCLASS><PACKAGE></DEVCLASS><OPERATION>I</OPERATION>
  <URI>/sap/bc/adt/programs/programs/<name></URI>
</DATA></asx:values></asx:abap>
```

Read-only. Returns the package text, `KORRFLAG` (transportable), `RESULT` (`S` =
the object may be created there), `EXISTING_REQ_ONLY`, and a `REQUESTS` list of
candidate requests. Useful for validating a package and offering the user real
choices before any write.

### Release transport

```http
POST /sap/bc/adt/cts/transports/{TRKORR}?action=release
```

**S/4HANA only.** On ECC the `/transports/{requestnumber}` URI template is
registered only on the non-HTTP branch, whose base path `/sap/bc/cts` has no ICF
node — so no HTTP URL reaches the release handler. Release in SE01/SE09 instead.

## SICF Service Activation

Activate in transaction `SICF` before use:

| Service path | Required for |
|---|---|
| `/sap/bc/adt` | All ADT endpoints |
| `/sap/bc/adt/datapreview` | `run-sql` (Open SQL Data Preview) |

## Common HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 401 | Wrong credentials |
| 403 | Missing authorization OR expired CSRF token |
| 404 | Object not found |
| 503 | ADT service not activated in SICF |

## Required Authorizations

| Operation | Authorization objects |
|---|---|
| All read operations | `S_ADT_RES`, `S_RFC` (ADT function groups) — or role `SAP_ADT_BASE` |
| `write-source`, `activate` | `S_DEVELOP` with `ACTVT=02` on relevant object types |
| `create-transport`, `release-transport` | `S_CTS_ADMI` or equivalent transport authorization |
| `list-transports` | Covered by `SAP_ADT_BASE` — no additional flag needed |
