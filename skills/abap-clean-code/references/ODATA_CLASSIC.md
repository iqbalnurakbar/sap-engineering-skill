# Classic SEGW OData and Fiori Freestyle (ECC / on-prem S/4)

> **Source**: ABAP Keyword Documentation (help.sap.com/doc/abapdocu_latest_index_htm), github.com/SAP/styleguides, github.com/SAP-samples/abap-cheat-sheets, SAP-samples RAP/Fiori reference apps, developers.sap.com tutorials.
> Confidence markers used below: `[OK]` = verified against an authoritative source cited inline; `[~]` = widely used and consistent with sources but not verbatim-confirmed; `[?]` = uncertain, verify in the target system before shipping.

## Contents

- [E. Classic Fiori / SEGW OData (ECC & on-prem S/4)](#e-classic-fiori-segw-odata-ecc-on-prem-s4)
  - [E.1 DPC_EXT patterns](#e1-dpcext-patterns)
  - [E.2 Common SEGW mistakes (skill checklist)](#e2-common-segw-mistakes-skill-checklist)
- [F. Fiori Freestyle (SAPUI5) — what the ABAP side must deliver](#f-fiori-freestyle-sapui5-what-the-abap-side-must-deliver)

---

## E. Classic Fiori / SEGW OData (ECC & on-prem S/4)

### E.1 DPC_EXT patterns

```abap
CLASS zcl_zsrv_dpc_ext DEFINITION
  INHERITING FROM zcl_zsrv_dpc
  PUBLIC CREATE PUBLIC.
  PROTECTED SECTION.
    METHODS productset_get_entityset  REDEFINITION.
    METHODS productset_get_entity     REDEFINITION.
    METHODS productset_create_entity  REDEFINITION.
    METHODS productset_update_entity  REDEFINITION.
    METHODS productset_delete_entity  REDEFINITION.
    METHODS /iwbep/if_mgw_appl_srv_runtime~create_deep_entity REDEFINITION.
    METHODS /iwbep/if_mgw_appl_srv_runtime~changeset_begin    REDEFINITION.
    METHODS /iwbep/if_mgw_appl_srv_runtime~changeset_end      REDEFINITION.
    METHODS /iwbep/if_mgw_appl_srv_runtime~changeset_process   REDEFINITION.
ENDCLASS.
```

**GET_ENTITYSET — paging, filtering, $inlinecount, $orderby, navigation**

```abap
METHOD productset_get_entityset.

  " ---- 1) filters: let the framework build the WHERE clause ----
  DATA(lv_where) = io_tech_request_context->get_osql_where_clause( ).
  " alternatively, typed access:
  DATA(lt_so)    = io_tech_request_context->get_filter( )->get_filter_select_options( ).
  DATA(lv_fstr)  = io_tech_request_context->get_filter( )->get_filter_string( ).
  DATA(lv_search) = io_tech_request_context->get_search_string( ).

  " ---- 2) navigation: called via an association? ----
  DATA(lv_source) = io_tech_request_context->get_source_entity_type_name( ).
  IF lv_source IS NOT INITIAL.
    io_tech_request_context->get_converted_source_keys(
      IMPORTING es_key_values = DATA(ls_parent_key) ).
  ENDIF.

  " ---- 3) $inlinecount BEFORE paging ----
  IF io_tech_request_context->has_inlinecount( ) = abap_true.
    SELECT COUNT(*) FROM zproduct
      WHERE (lv_where)
      INTO @es_response_context-inlinecount.
  ENDIF.

  " ---- 4) $skip / $top pushed to the DB (never fetch-all-then-slice) ----
  DATA(lv_skip) = is_paging-skip.
  DATA(lv_top)  = is_paging-top.

  SELECT product_id, description, price, currency
    FROM zproduct
    WHERE (lv_where)
    ORDER BY product_id
    INTO CORRESPONDING FIELDS OF TABLE @et_entityset
    UP TO @( COND i( WHEN lv_top > 0 THEN lv_skip + lv_top ELSE 0 ) ) ROWS.

  IF lv_skip > 0.
    DELETE et_entityset TO lv_skip.
  ENDIF.

  " ---- 5) $orderby (framework-parsed) ----
  LOOP AT it_order INTO DATA(ls_order).
    " ls_order-property / ls_order-order ('asc'/'desc')
  ENDLOOP.

ENDMETHOD.
```
`[~]` `get_osql_where_clause( )`, `has_inlinecount( )`, `is_paging-top/skip`, `it_order`, `it_filter_select_options`, `get_source_entity_type_name( )`, `get_converted_source_keys( )` are the standard `/IWBEP/IF_MGW_REQ_ENTITYSET` API. **`[?]` `get_search_string( )`** — verify the exact method name (`get_search_string` vs the `iv_search_string` importing parameter) in your release.

Best practice: `$skip`+`$top` should become a DB-side window (`ORDER BY ... UP TO n ROWS` + `OFFSET` where available), not `DELETE et_entityset`. On 7.51+ ABAP SQL supports `OFFSET`, which makes this exact and cheap `[~]`.

**GET_ENTITY**

```abap
METHOD productset_get_entity.
  io_tech_request_context->get_converted_keys(
    IMPORTING es_key_values = DATA(ls_key) ).

  SELECT SINGLE product_id, description, price, currency
    FROM zproduct
    WHERE product_id = @ls_key-product_id
    INTO CORRESPONDING FIELDS OF @er_entity.

  IF sy-subrc <> 0.
    RAISE EXCEPTION TYPE /iwbep/cx_mgw_busi_exception
      EXPORTING textid = /iwbep/cx_mgw_busi_exception=>resource_not_found.
  ENDIF.
ENDMETHOD.
```

**CREATE_ENTITY with the message container**

```abap
METHOD productset_create_entity.
  io_data_provider->read_entry_data( IMPORTING es_data = DATA(ls_in) ).

  CALL FUNCTION 'ZPRODUCT_CREATE'
    EXPORTING is_product = ls_in
    IMPORTING et_return  = DATA(lt_bapiret).

  IF line_exists( lt_bapiret[ type = 'E' ] ) OR line_exists( lt_bapiret[ type = 'A' ] ).
    DATA(lo_msg) = me->mo_context->get_message_container( ).
    lo_msg->add_messages_from_bapi(
      it_bapi_messages         = lt_bapiret
      iv_determine_leading_msg = /iwbep/if_message_container=>gcs_leading_msg_search_option-first ).
    RAISE EXCEPTION TYPE /iwbep/cx_mgw_busi_exception
      EXPORTING message_container = lo_msg.
  ENDIF.

  CALL FUNCTION 'BAPI_TRANSACTION_COMMIT' EXPORTING wait = abap_true.
  er_entity = ls_in.
ENDMETHOD.
```
`[~]` `mo_context->get_message_container( )`, `add_messages_from_bapi`, `add_message`, `add_message_text_only`, `gcs_leading_msg_search_option-first`, and `/iwbep/cx_mgw_busi_exception=>business_error / resource_not_found` are the standard API ([`/IWBEP/IF_MESSAGE_CONTAINER`](https://help.sap.com/doc/saphelp_nw74/7.4.16/en-US/01/a226519eff236ee10000000a445394/content.htm), [message container blog](https://fiori-copy-paste.blogspot.com/2016/10/message-containers-to-show-error.html)). **`[?]`** the exact constant path for the leading-message option.

**Deep insert**

```abap
METHOD /iwbep/if_mgw_appl_srv_runtime~create_deep_entity.
  CASE iv_entity_set_name.
    WHEN 'OrderSet'.
      DATA ls_deep TYPE zcl_zsrv_mpc_ext=>ty_order_deep.   " header + items table
      io_data_provider->read_entry_data( IMPORTING es_data = ls_deep ).

      " post header + items in ONE LUW
      " ... call BAPI / EML ...

      copy_data_to_ref( EXPORTING is_data = ls_deep
                        CHANGING  cr_data = er_deep_entity ).
    WHEN OTHERS.
      super->/iwbep/if_mgw_appl_srv_runtime~create_deep_entity(
        EXPORTING iv_entity_name = iv_entity_name ... ).
  ENDCASE.
ENDMETHOD.
```
The deep structure must be defined in the **MPC_EXT** (a structure whose item component is typed as the child entity's table type) and registered in `define`/`DEFINE` so the framework can deserialize the nested payload. `[~]`

**$batch / changesets = the transactional boundary**

```abap
METHOD /iwbep/if_mgw_appl_srv_runtime~changeset_begin.
  cv_defer_mode = abap_true.          " queue operations instead of executing them
ENDMETHOD.

METHOD /iwbep/if_mgw_appl_srv_runtime~changeset_process.
  LOOP AT it_changeset_request INTO DATA(ls_req).
    " ls_req-operation_type / entity_type / entry_provider / content_id
    " execute, then append the result to ct_changeset_response
  ENDLOOP.
ENDMETHOD.

METHOD /iwbep/if_mgw_appl_srv_runtime~changeset_end.
  COMMIT WORK AND WAIT.
ENDMETHOD.
```
`[✓]` [Batch Management ($batch)](https://discoveringabap.com/2022/11/28/building-odata-services-21-batch-management-batch/). All operations inside one changeset are atomic; operations in different changesets of one `$batch` are independent. `Content-ID` referencing (`$1`) lets a POST reference the entity created by an earlier POST in the same changeset.

### E.2 Common SEGW mistakes (skill checklist)
1. `COMMIT WORK` inside `CREATE_ENTITY`/`UPDATE_ENTITY` while a changeset is active → breaks atomicity. Commit only in `changeset_end` (or rely on the framework).
2. Ignoring `is_paging` and `it_filter_select_options` → the whole table is read on every list request; the app "works" in dev and dies in prod.
3. Building a `WHERE` clause by string concatenation from `$filter` → SQL-injection-ish and unmaintainable; use `get_osql_where_clause( )` or the select-options table.
4. `$inlinecount` computed *after* applying `$top`/`$skip` → wrong total, broken scrolling.
5. Raising `/iwbep/cx_mgw_tech_exception` for business errors → the UI shows a 500 with no usable text. Use `/iwbep/cx_mgw_busi_exception` + message container.
6. Returning `E` messages in a `RETURN` table without raising → the UI thinks the call succeeded.
7. Forgetting `BAPI_TRANSACTION_COMMIT`/`ROLLBACK` around BAPI calls (BAPIs don't commit themselves).
8. No ETag on updatable entities → lost updates. Mark the change-timestamp property as ETag in SEGW so Gateway emits `ETag` and validates `If-Match`. `[?]` verify the exact SEGW switch name and the resulting `precondition_failed` behaviour.
9. Regenerating the runtime artifacts and losing hand-written `_EXT` code (never edit the base `_DPC`/`_MPC`, only `_DPC_EXT`/`_MPC_EXT`).
10. Not caching the metadata (`/IWFND/CACHE_CLEANUP` needed after model change) — stale `$metadata` in the browser.
11. Not implementing `GET_EXPANDED_ENTITYSET`/`GET_EXPANDED_ENTITY` → `$expand` degenerates into n+1 round trips inside the backend.
12. Using SEGW for **new** development on S/4HANA when RAP is available. SEGW is legacy; keep it for ECC and for extending existing services.

---

## F. Fiori Freestyle (SAPUI5) — what the ABAP side must deliver

1. **Correct, stable `$metadata`.** Entity types, keys, nullability, `sap:label`, `sap:creatable/updatable/deletable/filterable/sortable/required-in-filter`, `sap:unit`/`sap:text` for currency/UoM and text pairs, navigation properties with correct multiplicity. Freestyle apps bind to these; wrong multiplicity breaks `bindElement`/`bindItems`.
2. **Server-side paging, filtering, sorting.** `sap.m.Table`/`sap.ui.table` growing and `$count`/`$inlinecount` require the backend to honour `$top`, `$skip`, `$filter`, `$orderby`, `$inlinecount=allpages`. Without it, "growing" is a lie.
3. **`$expand` support** for the master-detail read the app actually does, so one round trip suffices.
4. **`$batch`** support and correct changeset semantics — `ODataModel` with `submitChanges()`/`setDeferredGroups()` puts all pending changes into one changeset and expects all-or-nothing.
5. **ETag / optimistic locking.** Property marked as ETag → Gateway returns `ETag` header; UI5 stores it and sends `If-Match` on `PUT`/`MERGE`/`DELETE`. Backend must return `412 Precondition Failed` on mismatch so UI5 can surface a conflict instead of silently overwriting. `[~]`
6. **CSRF token.** `[✓]` ([X-CSRF Tokens](https://discoveringabap.com/2022/11/26/building-odata-services-19-x-csrf-tokens/)) A modifying request (`POST`/`PUT`/`MERGE`/`DELETE`) requires a valid `X-CSRF-Token`. Client flow: send a `GET` (typically `$metadata` or the service document) with header `X-CSRF-Token: fetch`; read the token from the response header; send it on every subsequent modifying request. Missing/expired token ⇒ **HTTP 403 "CSRF token validation failed"**. `sap.ui.model.odata.v2.ODataModel` does this automatically (`refreshSecurityToken()` is available for manual refresh). External callers (Postman, non-UI5 clients) must do it by hand, and must carry the session cookies (`SAP_SESSIONID_*`) along with the token — token and session must belong to the same session. For the V4 model, token handling differs and standard V4 services without CSRF support have known issues ([openui5#2288](https://github.com/UI5/openui5/issues/2288)).
7. **Message handling.** Return SAP messages through the Gateway message container so they land in the OData `sap-message` header / error payload; UI5 surfaces them in `sap.ui.core.message.MessageManager` and `sap.m.MessageBox`/`MessageStrip`/`MessagePopover` automatically. Rules:
   - Use `/IWBEP/IF_MESSAGE_CONTAINER` (`add_message`, `add_messages_from_bapi`, `add_message_text_only`) rather than plain text in the exception.
   - Set `is_leading_message`/the leading-message option so the UI shows the right headline.
   - Attach a `target` (entity/property path) to a message so UI5 can bind it to the offending field. `[~]`
   - Success/info messages must still be returned via the container (they arrive in the `sap-message` header on a 2xx), not raised as exceptions.
8. **Value helps** as separate filterable, pageable entity sets (or `sap:value-list` annotations / a local annotation file).
9. **Media/streams** (`$value`) for attachments: implement `/IWBEP/IF_MGW_APPL_SRV_RUNTIME~GET_STREAM` / `CREATE_STREAM`. `[~]`
10. **Deep insert** if the app creates header+items in one shot.
11. **Consistent typing:** `Edm.Decimal` scale/precision, `Edm.DateTime` vs `Edm.DateTimeOffset` (`sap:display-format=Date` for pure dates — otherwise UI5 shows time-zone-shifted dates), `Edm.Boolean` vs `flag` chars.

---
