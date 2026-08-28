import json
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Optional
from urllib.parse import quote

import requests

from .client import make_adt_request
from .config import PLATFORM_ECC, PLATFORM_S4, get_config, normalize_platform


@dataclass
class AdtResult:
    text: str
    is_error: bool = False


def _base() -> str:
    return get_config().base_url()


PLATFORM_HINT = (
    "Transport commands need to know the backend flavour, because ADT registers "
    "the CTS resources at different URLs on S/4HANA and on ECC. Ask the user "
    "which system this is, then run:  sap-adt-cli configure --platform s4|ecc"
)


def _platform() -> str:
    """Backend flavour ('s4' / 'ecc'), or '' when it has not been stated."""
    return normalize_platform(getattr(get_config(), "platform", ""))


def _enc(name: str) -> str:
    return quote(name, safe="")


def _ok(resp: requests.Response) -> AdtResult:
    return AdtResult(text=resp.text)


def _err(exc: Exception) -> AdtResult:
    if isinstance(exc, requests.HTTPError) and exc.response is not None:
        return AdtResult(
            text=f"HTTP {exc.response.status_code}: {exc.response.text or str(exc)}",
            is_error=True,
        )
    return AdtResult(text=str(exc), is_error=True)


def _xattr(s: str) -> str:
    """Escape a string for safe embedding inside a double-quoted XML attribute value."""
    return s.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")


def _xtext(s: str) -> str:
    """Escape a string for safe embedding as XML element content."""
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def get_program(program_name: str) -> AdtResult:
    try:
        return _ok(make_adt_request(f"{_base()}/sap/bc/adt/programs/programs/{_enc(program_name)}/source/main"))
    except Exception as e:
        return _err(e)


def get_class(class_name: str) -> AdtResult:
    try:
        return _ok(make_adt_request(f"{_base()}/sap/bc/adt/oo/classes/{_enc(class_name)}/source/main"))
    except Exception as e:
        return _err(e)


def get_function_group(function_group: str) -> AdtResult:
    try:
        return _ok(make_adt_request(f"{_base()}/sap/bc/adt/functions/groups/{_enc(function_group)}/source/main"))
    except Exception as e:
        return _err(e)


def get_function(function_name: str, function_group: str) -> AdtResult:
    try:
        url = (
            f"{_base()}/sap/bc/adt/functions/groups/{_enc(function_group)}"
            f"/fmodules/{_enc(function_name)}/source/main"
        )
        return _ok(make_adt_request(url))
    except Exception as e:
        return _err(e)


def get_structure(structure_name: str) -> AdtResult:
    try:
        return _ok(make_adt_request(f"{_base()}/sap/bc/adt/ddic/structures/{_enc(structure_name)}/source/main"))
    except Exception as e:
        return _err(e)


def get_table(table_name: str) -> AdtResult:
    try:
        return _ok(make_adt_request(f"{_base()}/sap/bc/adt/ddic/tables/{_enc(table_name)}/source/main"))
    except Exception as e:
        return _err(e)


def get_package(package_name: str) -> AdtResult:
    try:
        resp = make_adt_request(
            f"{_base()}/sap/bc/adt/repository/nodestructure",
            method="POST",
            params={
                "parent_type": "DEVC/K",
                "parent_name": _enc(package_name),
                "withShortDescriptions": "true",
            },
        )
        root = ET.fromstring(resp.text)
        ns_obj = "{http://www.sap.com/abapxml}"
        items = []
        for node in root.findall(f".//{ns_obj}SEU_ADT_REPOSITORY_OBJ_NODE"):
            name_el = node.find(f"{ns_obj}OBJECT_NAME")
            uri_el = node.find(f"{ns_obj}OBJECT_URI")
            if name_el is None or uri_el is None:
                continue
            type_el = node.find(f"{ns_obj}OBJECT_TYPE")
            desc_el = node.find(f"{ns_obj}DESCRIPTION")
            items.append({
                "OBJECT_TYPE": type_el.text if type_el is not None else "",
                "OBJECT_NAME": name_el.text,
                "OBJECT_DESCRIPTION": desc_el.text if desc_el is not None else "",
                "OBJECT_URI": uri_el.text,
            })
        return AdtResult(text=json.dumps(items, indent=2))
    except Exception as e:
        return _err(e)


def get_type_info(type_name: str) -> AdtResult:
    try:
        return _ok(make_adt_request(f"{_base()}/sap/bc/adt/ddic/domains/{_enc(type_name)}/source/main"))
    except Exception:
        pass
    try:
        return _ok(make_adt_request(f"{_base()}/sap/bc/adt/ddic/dataelements/{_enc(type_name)}"))
    except Exception as e:
        return _err(e)


def get_include(include_name: str) -> AdtResult:
    try:
        return _ok(make_adt_request(f"{_base()}/sap/bc/adt/programs/includes/{_enc(include_name)}/source/main"))
    except Exception as e:
        return _err(e)


def get_interface(interface_name: str) -> AdtResult:
    try:
        return _ok(make_adt_request(f"{_base()}/sap/bc/adt/oo/interfaces/{_enc(interface_name)}/source/main"))
    except Exception as e:
        return _err(e)


def get_transaction(transaction_name: str) -> AdtResult:
    try:
        url = (
            f"{_base()}/sap/bc/adt/repository/informationsystem/objectproperties/values"
            f"?uri=%2Fsap%2Fbc%2Fadt%2Fvit%2Fwb%2Fobject_type%2Ftrant%2Fobject_name%2F{_enc(transaction_name)}"
            f"&facet=package&facet=appl"
        )
        return _ok(make_adt_request(url))
    except Exception as e:
        return _err(e)


def search_object(query: str, max_results: int = 100) -> AdtResult:
    try:
        url = (
            f"{_base()}/sap/bc/adt/repository/informationsystem/search"
            f"?operation=quickSearch&query={_enc(query)}&maxResults={max_results}"
        )
        return _ok(make_adt_request(url))
    except Exception as e:
        return _err(e)


def get_object_uri(object_type: str, object_name: str, group: Optional[str] = None) -> str:
    t = object_type.lower()
    if t == "program":
        return f"/sap/bc/adt/programs/programs/{_enc(object_name)}"
    elif t == "class":
        return f"/sap/bc/adt/oo/classes/{_enc(object_name)}"
    elif t == "interface":
        return f"/sap/bc/adt/oo/interfaces/{_enc(object_name)}"
    elif t == "include":
        return f"/sap/bc/adt/programs/includes/{_enc(object_name)}"
    elif t == "function":
        if not group:
            raise ValueError("--group is required for object type 'function'")
        return f"/sap/bc/adt/functions/groups/{_enc(group)}/fmodules/{_enc(object_name)}"
    else:
        raise ValueError(
            f"Unknown object type: {object_type!r}. "
            "Supported types: program, class, interface, include, function"
        )


def _flat_attribs(elem) -> dict:
    return {(k.split("}")[-1] if "}" in k else k): v for k, v in elem.attrib.items()}


def _tag_local(elem) -> str:
    return elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag


def _extract_lock_handle(resp: requests.Response) -> str:
    handle = resp.headers.get("com.sap.adt.lock.handle", "")
    if handle:
        return handle
    if resp.text:
        try:
            root = ET.fromstring(resp.text)
            for elem in root.iter():
                for k, v in elem.attrib.items():
                    kl = k.split("}")[-1] if "}" in k else k
                    if kl.replace("_", "").lower() in ("handle", "lockhandle"):
                        return v
                tl = _tag_local(elem)
                # ADT returns <LOCK_HANDLE> inside asx:abap/asx:values/DATA
                if tl.replace("_", "").lower() in ("handle", "lockhandle") and elem.text:
                    return elem.text.strip()
        except ET.ParseError:
            return resp.text.strip()
    return ""


def _parse_syntax_check(xml_text: str) -> str:
    if not xml_text or not xml_text.strip():
        return "Syntax OK — no issues found."
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return xml_text

    messages = []
    for elem in root.iter():
        flat = _flat_attribs(elem)
        severity = flat.get("severity", "")
        text = flat.get("text", "") or flat.get("description", "")
        line = flat.get("line", "") or flat.get("offset", "")
        if not severity or not text:
            continue
        tag = severity.upper()
        if tag not in ("ERROR", "WARNING", "INFO"):
            continue
        line_str = f" line {line}:" if line and line != "0" else ""
        messages.append(f"[{tag}]{line_str} {text}")

    return "\n".join(messages) if messages else "Syntax OK — no issues found."


def _parse_activation_errors(xml_text: str) -> list:
    if not xml_text or not xml_text.strip():
        return []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []
    errors = []
    for elem in root.iter():
        flat = _flat_attribs(elem)
        tl = _tag_local(elem)
        severity = flat.get("severity", "")
        text = flat.get("text", "") or flat.get("description", "") or flat.get("shortText", "")
        if tl in ("error", "message", "checkResult") and text:
            prefix = f"[{severity.upper()}] " if severity else ""
            errors.append(f"{prefix}{text}")
    return errors


def _parse_where_used(xml_text: str) -> list:
    if not xml_text or not xml_text.strip():
        return []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []

    ns_core = "http://www.sap.com/adt/core"
    items = []
    for ref in root.iter(f"{{{ns_core}}}objectReference"):
        name = ref.get(f"{{{ns_core}}}name") or ref.get("name", "")
        type_ = ref.get(f"{{{ns_core}}}type") or ref.get("type", "")
        uri = ref.get(f"{{{ns_core}}}uri") or ref.get("uri", "")
        if name:
            items.append({"type": type_, "name": name, "uri": uri})
    if not items:
        for elem in root.iter():
            if _tag_local(elem) == "objectReference":
                flat = _flat_attribs(elem)
                name = flat.get("name", "")
                if name:
                    items.append({
                        "type": flat.get("type", ""),
                        "name": name,
                        "uri": flat.get("uri", ""),
                    })
    return items


def _parse_sql_result(xml_text: str) -> list:
    if not xml_text or not xml_text.strip():
        return []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []

    columns_ordered = []

    for elem in root.iter():
        if _tag_local(elem) != "columns":
            continue
        meta = next((c for c in elem if _tag_local(c) == "metadata"), None)
        if meta is None:
            continue
        col_name = _flat_attribs(meta).get("name", "")
        if not col_name:
            continue
        dataset = next((c for c in elem if _tag_local(c) == "dataSet"), None)
        values = []
        if dataset is not None:
            values = [d.text or "" for d in dataset if _tag_local(d) == "data"]
        columns_ordered.append((col_name, values))

    if not columns_ordered:
        for elem in root.iter():
            if _tag_local(elem) != "column":
                continue
            flat = _flat_attribs(elem)
            col_name = flat.get("name", "")
            if not col_name:
                continue
            rows = []
            for child in elem:
                cl = _tag_local(child)
                if cl in ("row", "cell", "value"):
                    rows.append(child.text or "")
            if not rows:
                for rows_elem in elem.iter():
                    if _tag_local(rows_elem) == "rows":
                        for row_elem in rows_elem:
                            rows.append(row_elem.text or "")
                        break
            columns_ordered.append((col_name, rows))

    if not columns_ordered:
        return []
    n_rows = max(len(v) for _, v in columns_ordered)
    result = []
    for i in range(n_rows):
        row = {}
        for col_name, values in columns_ordered:
            row[col_name] = values[i] if i < len(values) else ""
        result.append(row)
    return result


def _parse_transports(xml_text: str, status_filter: str = "") -> list:
    if not xml_text or not xml_text.strip():
        return []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []

    items = []
    for elem in root.iter():
        tl = _tag_local(elem)
        if tl not in ("workitem", "transport", "request"):
            continue
        flat = _flat_attribs(elem)
        attr_map = {}
        for child in elem.iter():
            if _tag_local(child) == "attribute":
                cf = _flat_attribs(child)
                aname = cf.get("name", "")
                avalue = cf.get("value", "")
                if aname:
                    attr_map[aname] = avalue

        trkorr = attr_map.get("TRKORR") or flat.get("number") or flat.get("TRKORR", "")
        desc = (attr_map.get("AS4TEXT") or flat.get("desc")
                or flat.get("description") or flat.get("AS4TEXT", ""))
        status = attr_map.get("TRSTATUS") or flat.get("status") or flat.get("TRSTATUS", "")
        owner = attr_map.get("AS4USER") or flat.get("owner") or flat.get("AS4USER", "")

        if not trkorr:
            continue
        if status_filter and status.upper() != status_filter.upper():
            continue
        items.append({
            "trkorr": trkorr,
            "description": desc,
            "status": status,
            "owner": owner,
        })
    return items


def syntax_check(
    object_type: str,
    object_name: str,
    group: Optional[str] = None,
) -> AdtResult:
    try:
        uri = get_object_uri(object_type, object_name, group=group)
        body = (
            '<?xml version="1.0" encoding="utf-8"?>'
            '<adtcore:objectReferences xmlns:adtcore="http://www.sap.com/adt/core">'
            f'<adtcore:objectReference adtcore:uri="{_xattr(uri)}" adtcore:name="{_xattr(object_name.upper())}"/>'
            '</adtcore:objectReferences>'
        ).encode("utf-8")
        resp = make_adt_request(
            f"{_base()}/sap/bc/adt/abapsource/syntaxcheck",
            method="POST",
            data=body,
            extra_headers={
                "Content-Type": (
                    "application/vnd.sap.adt.abapsource.syntaxcheckresult+xml; charset=utf-8"
                )
            },
        )
        return AdtResult(text=_parse_syntax_check(resp.text))
    except ValueError as e:
        return AdtResult(text=str(e), is_error=True)
    except Exception as e:
        return _err(e)


def get_cds_view(name: str) -> AdtResult:
    try:
        return _ok(make_adt_request(
            f"{_base()}/sap/bc/adt/ddic/ddl/sources/{_enc(name)}/source/main"
        ))
    except Exception as e:
        return _err(e)


def get_type_group(name: str) -> AdtResult:
    try:
        return _ok(make_adt_request(
            f"{_base()}/sap/bc/adt/typegroups/groups/{_enc(name)}/source/main"
        ))
    except Exception as e:
        return _err(e)


def where_used(
    object_type: str,
    object_name: str,
    max_results: int = 50,
    group: Optional[str] = None,
) -> AdtResult:
    try:
        uri = get_object_uri(object_type, object_name, group=group)
        full_uri = f"{_base()}{uri}"
        resp = make_adt_request(
            f"{_base()}/sap/bc/adt/repository/informationsystem/whereused",
            params={"uri": full_uri, "maxResults": max_results},
            extra_headers={
                "Accept": (
                    "application/vnd.sap.adt.repository.informationsystem.whereused+xml"
                )
            },
        )
        items = _parse_where_used(resp.text)
        return AdtResult(text=json.dumps(items, indent=2))
    except ValueError as e:
        return AdtResult(text=str(e), is_error=True)
    except Exception as e:
        return _err(e)


def run_sql(sql: str, max_rows: int = 100) -> AdtResult:
    url = f"{_base()}/sap/bc/adt/datapreview/freestyle"
    try:
        try:
            resp = make_adt_request(
                url,
                params={"rowNumber": max_rows, "sqlCommand": sql},
                extra_headers={"Accept": "application/vnd.sap.adt.datapreview.table.v1+xml"},
            )
        except requests.HTTPError as e:
            if e.response is None or e.response.status_code != 405:
                raise
            resp = make_adt_request(
                url,
                method="POST",
                params={"rowNumber": max_rows},
                data=sql.encode("utf-8"),
                extra_headers={
                    "Content-Type": "text/plain",
                    "Accept": "application/vnd.sap.adt.datapreview.table.v1+xml",
                },
                timeout=60,
            )
        rows = _parse_sql_result(resp.text)
        return AdtResult(text=json.dumps(rows, indent=2))
    except Exception as e:
        return _err(e)


def _parse_transports_ecc(xml_text: str, status_filter: str = "") -> list:
    """Parse the ECC FIND payload: asx:abap > DATA > CTS_REQ_HEADER rows."""
    if not xml_text or not xml_text.strip():
        return []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []

    items = []
    for elem in root.iter():
        if _tag_local(elem) != "CTS_REQ_HEADER":
            continue
        get = lambda tag: (elem.findtext(tag) or "").strip()
        trkorr = get("TRKORR")
        if not trkorr:
            continue
        status = get("TRSTATUS")
        if status_filter and status.upper() != status_filter.upper():
            continue
        items.append({
            "trkorr": trkorr,
            "description": get("AS4TEXT"),
            "status": status,
            "owner": get("AS4USER"),
            "target": get("TARSYSTEM"),
        })
    return items


def list_transports(user: str, status: str = "D") -> AdtResult:
    platform = _platform()
    if not platform:
        return AdtResult(text=f"ERROR: platform not configured. {PLATFORM_HINT}", is_error=True)
    try:
        if platform == PLATFORM_ECC:
            # ECC exposes only /cts/transports over HTTP; listing is the FIND
            # action on it. It cannot filter by status server-side, so the
            # status filter is applied to the parsed rows.
            resp = make_adt_request(
                f"{_base()}/sap/bc/adt/cts/transports",
                params={"_action": "FIND", "user": user, "trfunction": "K"},
                timeout=60,
            )
            items = _parse_transports_ecc(resp.text, status_filter=status)
        else:
            resp = make_adt_request(
                f"{_base()}/sap/bc/adt/cts/transportrequests",
                # requestStatus must be sent server-side: without it ADT returns
                # only the released worklist, so a client-side "D" filter can
                # never match. D = modifiable, R = released.
                params={"user": user, "requestStatus": status},
            )
            items = _parse_transports(resp.text, status_filter=status)
        return AdtResult(text=json.dumps(items, indent=2))
    except Exception as e:
        return _err(e)


def set_program_logical_database(
    program_name: str,
    logical_database: str = "",
    transport: str = "",
) -> AdtResult:
    """Set or blank the logical database in a program's attributes.

    The attribute lives in the program's metadata document, not in its source:

        <program:logicalDatabase>
          <program:ref adtcore:name="D$S"/>
        </program:logicalDatabase>

    SAP can derive one automatically from TABLES declarations (a report
    declaring TABLES for SD tables picks up the dummy LDB "D$S"), which shows
    up as TRDIR-LDBNAME. Passing an empty ``logical_database`` blanks it.

    Flow: GET metadata -> rewrite the block -> lock -> PUT -> unlock.
    """
    name = program_name.upper()
    uri = f"/sap/bc/adt/programs/programs/{_enc(name)}"
    media = "application/vnd.sap.adt.programs.programs.v2+xml"

    try:
        doc = make_adt_request(
            f"{_base()}{uri}", extra_headers={"Accept": media}
        ).text
    except Exception as e:
        return _err(e)

    block = (
        "<program:logicalDatabase>"
        f'<program:ref adtcore:name="{_xattr(logical_database)}"/>'
        "</program:logicalDatabase>"
    )
    if "<program:logicalDatabase" in doc:
        new_doc = re.sub(
            r"<program:logicalDatabase>.*?</program:logicalDatabase>",
            block, doc, flags=re.S,
        )
    elif not logical_database:
        return AdtResult(
            text=f"{name}: no logical database is set - nothing to do."
        )
    else:
        new_doc = doc.replace(
            "</program:abapProgram>", block + "</program:abapProgram>"
        )

    lock = lock_object(uri)
    if lock.is_error:
        return lock
    handle = lock.text
    try:
        params = {"lockHandle": handle}
        if transport:
            params["corrNr"] = transport
        make_adt_request(
            f"{_base()}{uri}",
            method="PUT",
            data=new_doc.encode("utf-8"),
            params=params,
            extra_headers={"Content-Type": media},
        )
        shown = logical_database or "(blank)"
        return AdtResult(text=f"Logical database of {name} set to {shown}.")
    except Exception as e:
        return _err(e)
    finally:
        unlock_object(uri, handle)


def create_program(
    program_name: str,
    description: str,
    package: str,
    transport: str = "",
    program_type: str = "executableProgram",
) -> AdtResult:
    """Create an ABAP program (report) shell.

    Contract from /sap/bc/adt/discovery: the collection
    /sap/bc/adt/programs/programs declares
        <app:accept>application/vnd.sap.adt.programs.programs.v2+xml</app:accept>
    so a POST of that media type creates a member of the collection.

    The transport is passed as the ``corrNr`` query parameter. A local
    ($TMP) package needs none.

    The created program has no source yet -- follow up with put_source
    (the ``write-source`` command) and then activate it.
    """
    name = program_name.upper()
    try:
        body = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<program:abapProgram'
            ' xmlns:program="http://www.sap.com/adt/programs/programs"'
            ' xmlns:adtcore="http://www.sap.com/adt/core"'
            f' adtcore:name="{_xattr(name)}"'
            ' adtcore:type="PROG/P"'
            f' adtcore:description="{_xattr(description)}"'
            f' program:programType="{_xattr(program_type)}">'
            f'<adtcore:packageRef adtcore:name="{_xattr(package.upper())}"/>'
            "</program:abapProgram>"
        ).encode("utf-8")
        params = {"corrNr": transport} if transport else None
        resp = make_adt_request(
            f"{_base()}/sap/bc/adt/programs/programs",
            method="POST",
            data=body,
            params=params,
            extra_headers={
                "Content-Type": (
                    "application/vnd.sap.adt.programs.programs.v2+xml; charset=UTF-8"
                ),
            },
        )
        return AdtResult(
            text=(f"Created PROGRAM {name} in package {package.upper()} "
                  f"(HTTP {resp.status_code}). Check the source with get-program: "
                  f"some backends (ECC) seed a header comment plus a REPORT "
                  f"statement and are activatable as-is, others leave it empty - "
                  f"use write-source to load it, then activate.")
        )
    except Exception as e:
        return _err(e)


def lock_object(object_uri: str) -> AdtResult:
    try:
        resp = make_adt_request(
            f"{_base()}{object_uri}",
            method="POST",
            # ADT lock contract: _action=LOCK&accessMode=MODIFY. A bodyless
            # POST still needs a Content-Type or SAP answers HTTP 400
            # contentTypeMissing. The handle comes back in <LOCK_HANDLE>.
            params={"_action": "LOCK", "accessMode": "MODIFY"},
            extra_headers={
                "X-sap-adt-sessiontype": "stateful",
                "Accept": (
                    "application/vnd.sap.as+xml;charset=UTF-8;"
                    "dataname=com.sap.adt.lock.Result"
                ),
                "Content-Type": "application/vnd.sap.as+xml; charset=UTF-8",
            },
        )
        handle = _extract_lock_handle(resp)
        if not handle:
            return AdtResult(text="Lock succeeded but no handle returned by SAP — cannot proceed with write.", is_error=True)
        return AdtResult(text=handle)
    except Exception as e:
        return _err(e)


def put_source(
    object_uri: str,
    content: str,
    lock_handle: str,
    transport: Optional[str] = None,
) -> AdtResult:
    try:
        extra: dict = {
            "Content-Type": "text/plain; charset=utf-8",
        }
        # ADT takes BOTH the lock handle and the transport as query
        # parameters on the source PUT:
        #   lockHandle - passing it only as the X-sap-adt-lock-handle header
        #                yields HTTP 400 ExceptionParameterNotFound
        #   corrNr     - the transport request; the older "sap-cts-request"
        #                name fails the same way
        params: dict = {"lockHandle": lock_handle}
        if transport:
            params["corrNr"] = transport
        make_adt_request(
            f"{_base()}{object_uri}/source/main",
            method="PUT",
            data=content.encode("utf-8"),
            params=params,
            extra_headers=extra,
        )
        return AdtResult(text="OK")
    except Exception as e:
        return _err(e)


def unlock_object(object_uri: str, lock_handle: str) -> AdtResult:
    try:
        make_adt_request(
            f"{_base()}{object_uri}",
            method="POST",
            params={"_action": "UNLOCK", "lockHandle": lock_handle},
            extra_headers={
                "X-sap-adt-sessiontype": "stateful",
                "Content-Type": "application/vnd.sap.as+xml; charset=UTF-8",
            },
        )
        return AdtResult(text="OK")
    except Exception:
        return AdtResult(text="unlock error (ignored)", is_error=False)


def activate_object(
    object_type: str,
    object_name: str,
    group: Optional[str] = None,
) -> AdtResult:
    try:
        uri = get_object_uri(object_type, object_name, group=group)
        body = (
            '<?xml version="1.0" encoding="utf-8"?>'
            '<adtcore:objectReferences xmlns:adtcore="http://www.sap.com/adt/core">'
            f'<adtcore:objectReference adtcore:uri="{_xattr(uri)}" adtcore:name="{_xattr(object_name.upper())}"/>'
            '</adtcore:objectReferences>'
        ).encode("utf-8")
        resp = make_adt_request(
            f"{_base()}/sap/bc/adt/activation",
            method="POST",
            data=body,
            # The activation resource requires method=activate; without it
            # SAP answers HTTP 400 ExceptionParameterNotFound for "method".
            params={"method": "activate", "preauditRequested": "true"},
            extra_headers={
                "Content-Type": (
                    "application/vnd.sap.adt.activation.request+xml; charset=utf-8"
                )
            },
        )
        if resp.text and resp.text.strip():
            errors = _parse_activation_errors(resp.text)
            if errors:
                return AdtResult(text="\n".join(errors), is_error=True)
        return AdtResult(text=f"Activated {object_type.upper()} {object_name.upper()}.")
    except ValueError as e:
        return AdtResult(text=str(e), is_error=True)
    except Exception as e:
        return _err(e)


_TRKORR_RE = re.compile(r"[A-Z][A-Z0-9]{2}K[0-9]{6}")


def _extract_trkorr(resp) -> str:
    """Pull the transport number from a Location header, else from the body."""
    location = resp.headers.get("Location", "")
    if location:
        candidate = location.rstrip("/").rsplit("/", 1)[-1]
        if _TRKORR_RE.fullmatch(candidate):
            return candidate
    match = _TRKORR_RE.search(resp.text or "")
    return match.group(0) if match else ""


def list_transport_targets() -> list:
    """Valid transport targets for this system, from the ADT value help.

    S/4HANA only. On ECC the target is not chosen by the caller at all - the
    backend derives it from the package's transport layer - so this returns [].
    """
    if _platform() == PLATFORM_ECC:
        return []
    resp = make_adt_request(
        f"{_base()}/sap/bc/adt/cts/transportrequests/valuehelp/target",
        params={"maxItemCount": "50"},
    )
    root = ET.fromstring(resp.text)
    return [e.text or "" for e in root.iter() if _tag_local(e) == "name"]


def _create_transport_ecc(description: str, package: str) -> AdtResult:
    """Create a transport request on ECC.

    ECC registers only /cts/transports and /cts/transportchecks under
    /sap/bc/adt (see CL_CTS_ADT_RES_APP->register_resources, which returns
    early on the HTTP branch). POSTing to /cts/transports runs
    CL_CTS_ADT_RES_OBJ_RECORD->post, which reads a SADT_CREATE_CORR_REQUEST
    and calls TR_INSERT_REQUEST_WITH_TASKS.

    Two consequences for the caller:
      * the target system is NOT passed - the backend derives it from the
        package via TR_DEVCLASS_GET + TR_GET_TRANSPORT_TARGET, so the package
        is mandatory here;
      * the request type is hardcoded to 'K' (Workbench).

    The response body is plain text: a URI whose last segment is the number.
    """
    if not package:
        return AdtResult(
            text=("ERROR: --package is required on ECC. The backend derives the "
                  "transport target from the package's transport layer, so it "
                  "cannot create the request without one."),
            is_error=True,
        )
    body = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<asx:abap xmlns:asx="http://www.sap.com/abapxml" version="1.0">'
        "<asx:values><DATA>"
        f"<DEVCLASS>{_xtext(package)}</DEVCLASS>"
        f"<REQUEST_TEXT>{_xtext(description)}</REQUEST_TEXT>"
        "</DATA></asx:values></asx:abap>"
    ).encode("utf-8")
    resp = make_adt_request(
        f"{_base()}/sap/bc/adt/cts/transports",
        method="POST",
        data=body,
        extra_headers={
            "Content-Type": (
                "application/vnd.sap.as+xml; charset=UTF-8; "
                "dataname=com.sap.adt.CreateCorrectionRequest"
            ),
        },
        timeout=60,
    )
    trkorr = _extract_trkorr(resp)
    if not trkorr:
        return AdtResult(
            text=("Transport POST returned no parseable request number. "
                  f"Status {resp.status_code}. Body: {(resp.text or '')[:300]}"),
            is_error=True,
        )
    return AdtResult(text=f"Created transport: {trkorr}")


def create_transport(
    description: str,
    category: str = "Workbench",
    username: str = "",
    target: str = "",
    package: str = "",
) -> AdtResult:
    """Create a transport request via the ADT transport organizer.

    S/4HANA contract, taken from /sap/bc/adt/discovery, where the collection
    /sap/bc/adt/cts/transportrequests declares
        <app:accept>application/vnd.sap.adt.transportorganizer.v1+xml</app:accept>
    and the POST body must be rooted at {http://www.sap.com/cts/adt/tm}root.
    There ``target`` is the transport target system (see
    list_transport_targets) and ``package`` is ignored.

    ECC uses a different resource entirely - see _create_transport_ecc, where
    ``package`` is required and ``target``/``category`` do not apply.
    """
    platform = _platform()
    if not platform:
        return AdtResult(text=f"ERROR: platform not configured. {PLATFORM_HINT}", is_error=True)
    try:
        if platform == PLATFORM_ECC:
            return _create_transport_ecc(description, package)

        request_type = "W" if category.upper().startswith("CUST") else "K"
        body = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<tm:root xmlns:tm="http://www.sap.com/cts/adt/tm"'
            ' tm:useraction="newrequest">'
            f'<tm:request tm:desc="{_xattr(description)}"'
            f' tm:type="{request_type}"'
            f' tm:target="{_xattr(target)}"'
            ' tm:cts_project="">'
            f'<tm:task tm:owner="{_xattr(username)}"/>'
            "</tm:request>"
            "</tm:root>"
        ).encode("utf-8")
        resp = make_adt_request(
            f"{_base()}/sap/bc/adt/cts/transportrequests",
            method="POST",
            data=body,
            extra_headers={
                "Content-Type": "application/vnd.sap.adt.transportorganizer.v1+xml",
            },
        )
        trkorr = _extract_trkorr(resp)
        if not trkorr:
            body_snippet = (resp.text or "")[:300]
            return AdtResult(
                text=("Transport POST returned no parseable request number. "
                      f"Status {resp.status_code}. Body: {body_snippet}"),
                is_error=True,
            )
        return AdtResult(text=f"Created transport: {trkorr}")
    except Exception as e:
        return _err(e)


def release_transport(trkorr: str) -> AdtResult:
    platform = _platform()
    if not platform:
        return AdtResult(text=f"ERROR: platform not configured. {PLATFORM_HINT}", is_error=True)
    if platform == PLATFORM_ECC:
        # The /cts/transports/{requestnumber} URI template is registered only
        # on the non-HTTP branch of CL_CTS_ADT_RES_APP->register_resources, and
        # that branch's base path (/sap/bc/cts) has no ICF node. So no HTTP URL
        # on ECC reaches the release handler.
        return AdtResult(
            text=("ERROR: release-transport is not available over ADT on ECC - the "
                  "backend does not expose a release endpoint on the HTTP branch. "
                  "Release the request in SE01/SE09 instead."),
            is_error=True,
        )
    try:
        make_adt_request(
            f"{_base()}/sap/bc/adt/cts/transports/{_enc(trkorr)}?action=release",
            method="POST",
        )
        return AdtResult(text=f"Released transport: {trkorr}")
    except Exception as e:
        return _err(e)
