# ABAP CDS, Fiori Elements Annotations, and RAP

> **Source**: ABAP Keyword Documentation (help.sap.com/doc/abapdocu_latest_index_htm), github.com/SAP/styleguides, github.com/SAP-samples/abap-cheat-sheets, SAP-samples RAP/Fiori reference apps, developers.sap.com tutorials.
> Confidence markers used below: `[OK]` = verified against an authoritative source cited inline; `[~]` = widely used and consistent with sources but not verbatim-confirmed; `[?]` = uncertain, verify in the target system before shipping.

## Contents

- [C. ABAP CDS](#c-abap-cds)
  - [C.1 View entity syntax (7.55+) — prefer over DDIC-based views](#c1-view-entity-syntax-755-prefer-over-ddic-based-views)
  - [C.2 View entity vs DDIC-based view — differences to encode `[~]`](#c2-view-entity-vs-ddic-based-view-differences-to-encode)
  - [C.3 VDM layering and naming](#c3-vdm-layering-and-naming)
  - [C.4 Fiori Elements annotations that matter](#c4-fiori-elements-annotations-that-matter)
  - [C.5 Access control (DCL)](#c5-access-control-dcl)
- [D. RAP (RESTful Application Programming Model)](#d-rap-restful-application-programming-model)
  - [D.1 Managed vs unmanaged — the decision](#d1-managed-vs-unmanaged-the-decision)
  - [D.2 Behavior definition (managed, draft, strict 2)](#d2-behavior-definition-managed-draft-strict-2)
  - [D.3 Behavior projection (the UI layer)](#d3-behavior-projection-the-ui-layer)
  - [D.4 Behavior implementation (ABAP behavior pool) skeleton](#d4-behavior-implementation-abap-behavior-pool-skeleton)
  - [D.5 EML — calling a RAP BO from ABAP](#d5-eml-calling-a-rap-bo-from-abap)
  - [D.6 Service definition & binding](#d6-service-definition-binding)
  - [D.7 Clean core / ABAP Cloud](#d7-clean-core-abap-cloud)
- [Z. Activation gotchas that bite most often](#z-activation-gotchas-that-bite-most-often)
  - [Z.1 A validation must clear its own state area](#z1-a-validation-must-clear-its-own-state-area)
  - [Z.2 `@UI.facet` belongs to the entity, not to an element](#z2-uifacet-belongs-to-the-entity-not-to-an-element)
  - [Z.3 A behavior projection must re-declare what it uses](#z3-a-behavior-projection-must-re-declare-what-it-uses)
  - [Z.4 Do not hand-type the draft table or the admin data elements](#z4-do-not-hand-type-the-draft-table-or-the-admin-data-elements)
  - [Z.5 Released-API assumptions](#z5-released-api-assumptions)

---

## C. ABAP CDS

### C.1 View entity syntax (7.55+) — prefer over DDIC-based views

```abap
@EndUserText.label: 'Travel — interface view'
@AccessControl.authorizationCheck: #CHECK
@Metadata.ignorePropagatedAnnotations: true
@ObjectModel.usageType: { serviceQuality: #X, sizeCategory: #S, dataClass: #TRANSACTIONAL }
define root view entity ZI_Travel
  as select from ztravel as Travel
  composition [0..*] of ZI_Booking as _Booking
  association [0..1] to /DMO/I_Agency  as _Agency
    on $projection.AgencyID = _Agency.AgencyID
  association [0..1] to I_Currency     as _Currency
    on $projection.CurrencyCode = _Currency.Currency
{
  key travel_id            as TravelID,
      agency_id            as AgencyID,
      customer_id          as CustomerID,
      begin_date           as BeginDate,
      end_date             as EndDate,
      @Semantics.amount.currencyCode: 'CurrencyCode'
      booking_fee          as BookingFee,
      @Semantics.amount.currencyCode: 'CurrencyCode'
      total_price          as TotalPrice,
      @Semantics.currencyCode: true
      currency_code        as CurrencyCode,
      overall_status       as OverallStatus,
      description          as Description,

      // calculated fields — pushed down
      case overall_status when 'A' then 3     // green
                          when 'X' then 1     // red
                          else 2 end          as StatusCriticality,
      cast( 0 as abap.dec(16,2) )             as Reserved,

      @Semantics.user.createdBy: true
      created_by           as CreatedBy,
      @Semantics.systemDateTime.createdAt: true
      created_at           as CreatedAt,
      @Semantics.user.lastChangedBy: true
      last_changed_by      as LastChangedBy,
      @Semantics.systemDateTime.lastChangedAt: true
      last_changed_at      as LastChangedAt,
      @Semantics.systemDateTime.localInstanceLastChangedAt: true
      local_last_changed_at as LocalLastChangedAt,

      // expose the associations
      _Booking,
      _Agency,
      _Currency
}
```

With parameters and a path expression:

```abap
define view entity ZI_TravelStats
  with parameters
    p_from : abap.dats,
    p_to   : abap.dats
  as select from ZI_Travel as t
{
  key t.AgencyID,
      t._Agency.Name              as AgencyName,   // path expression
      count( * )                  as TravelCount,
      sum( t.TotalPrice )         as Revenue,
      t.CurrencyCode
}
where t.BeginDate >= :p_from and t.BeginDate <= :p_to
group by t.AgencyID, t._Agency.Name, t.CurrencyCode
having count( * ) > 0
```

Projection view (RAP consumption layer):

```abap
@EndUserText.label: 'Travel — projection'
@AccessControl.authorizationCheck: #CHECK
@Metadata.allowExtensions: true
@ObjectModel.semanticKey: [ 'TravelID' ]
@Search.searchable: true
define root view entity ZC_Travel
  provider contract transactional_query
  as projection on ZI_Travel
{
  key TravelID,
      @Consumption.valueHelpDefinition: [{ entity: { name: '/DMO/I_Agency', element: 'AgencyID' } }]
      @ObjectModel.text.element: [ 'AgencyName' ]
      @Search.defaultSearchElement: true
      AgencyID,
      _Agency.Name as AgencyName,
      CustomerID,
      BeginDate,
      EndDate,
      BookingFee,
      TotalPrice,
      CurrencyCode,
      OverallStatus,
      StatusCriticality,
      Description,
      LocalLastChangedAt,
      /* associations */
      _Booking : redirected to composition child ZC_Booking,
      _Agency,
      _Currency
}
```

Extension: `extend view entity ZI_Travel with ZE_TravelFields { ... }`.
Custom entity (unmanaged query, e.g. remote data): `define custom entity ZI_Remote { ... }` + `@ObjectModel.query.implementedBy: 'ABAP:ZCL_Q'`. `[~]`
Table function: `define table function ZTF_X returns { ... } implemented by method zcl_amdp=>get_data;` with an AMDP method `FOR TABLE FUNCTION ZTF_X`. `[~]`

### C.2 View entity vs DDIC-based view — differences to encode `[~]`

| | DDIC-based view (`DEFINE VIEW`) | View entity (`DEFINE VIEW ENTITY`) |
|---|---|---|
| Requires `@AbapCatalog.sqlViewName` | Yes (creates a DDIC + DB view) | **No** — no separate SQL view object |
| Client handling | `@ClientDependent`, semantics can surprise | `@ClientHandling.type` / `.algorithm`, stricter defaults |
| Syntax strictness | permissive, many implicit casts | strict; explicit `cast( )`, no unnamed elements |
| Associations | supported | supported + **compositions**, `redirected to` |
| Projection views | no | `AS PROJECTION ON` |
| `PROVIDER CONTRACT` | no | yes (`transactional_query`, `transactional_interface`, `analytical_query`) |
| Optimizer / performance | older | better (SAP explicitly recommends migrating) |
| Usable where a DDIC view is required by legacy tooling | yes | **no** |

**Guidance for the skill:** new development uses view entities. Convert DDIC-based views only when there's a reason (ADT offers a conversion). Do not create new `@AbapCatalog.sqlViewName` views in 2020+ systems.

### C.3 VDM layering and naming

SAP's Virtual Data Model in S/4HANA layers views as `[~]`:
- **Basic / interface views** (`I_*`, `@VDM.viewType: #BASIC`) — one business entity, reusable, no UI annotations, released as public API (`C1`).
- **Composite views** (`@VDM.viewType: #COMPOSITE`) — join/aggregate several basic views, still reusable.
- **Consumption views** (`C_*`, `@VDM.viewType: #CONSUMPTION`) — bound to one app/service, carry `@UI` annotations, **not** meant for reuse.
- **Private views** (`P_*`) — internal helper, must not be consumed by other layers.
- **Extension include views** (`E_*`), remote/replication (`R_*` in analytics contexts).
- OData API entities in S/4HANA Cloud APIs appear as `A_*`.

Custom mirror of this (customer convention, **not** SAP-official):
```
Z*_I_*   interface / basic layer   e.g. ZFI_I_OpenItem
Z*_R_*   RAP base (root) BO view   e.g. ZFI_R_Invoice
Z*_C_*   consumption / projection  e.g. ZFI_C_Invoice
Z*_P_*   private helper
Z*_E_*   extension include
```
For **RAP** specifically, SAP's own tutorials/reference scenario use `ZR_` (base BO view), `ZC_` (projection), `ZI_` (reusable interface view), `ZBP_` (behavior pool), `ZUI_`/`ZAPI_` (service definitions). `[~]` — treat as SAP-tutorial convention, not a syntax rule.

Sources: [VDM overview](https://blog.sap-press.com/an-overview-of-the-sap-s4hana-vdm), [CDS VDM layering](https://software-heroes.com/en/blog/abap-cds-virtual-data-model).

### C.4 Fiori Elements annotations that matter

All snippets below are verbatim from SAP samples/tutorials `[✓]` — [abap-platform-fiori-feature-showcase](https://github.com/SAP-samples/abap-platform-fiori-feature-showcase/blob/main/01_general_features.md), [Refine the List Report](https://developers.sap.com/tutorials/fiori-tools-rap-modify-list-report..html), [Object Page facets](https://samplecodeabap.com/cds-fiori-elements-object-page-facets/), [Fiori Elements annotation cheat sheet](https://www.brandeis.de/en/blog/cheat-sheet-fiori-elements/), [Useful CDS annotations](https://www.sapdev.eu/useful-abap-cds-annotations/).

**Entity level**
```abap
@UI: {
  headerInfo: { typeName: 'Travel', typeNamePlural: 'Travels',
                title: { type: #STANDARD, value: 'TravelID' },
                description: { value: 'Description' } },
  presentationVariant: [{ sortOrder: [{ by: 'LocalLastChangedAt', direction: #DESC }],
                          visualizations: [{ type: #AS_LINEITEM }] }],
  selectionVariant: [{ qualifier: 'Open', text: 'Open only',
                       parameters: [{ name: 'OverallStatus', value: 'O' }] }]
}
@Search.searchable: true
@ObjectModel.semanticKey: [ 'TravelID' ]
@Metadata.allowExtensions: true
```

**List report columns & filters**
```abap
@UI.lineItem: [{ position: 10, importance: #HIGH, label: 'Travel' }]
@UI.selectionField: [{ position: 10 }]
@Search.defaultSearchElement: true
@Search.fuzzinessThreshold: 0.8
TravelID,

@UI.lineItem: [{ position: 80, criticality: 'OverallStatusCriticality' }]
OverallStatus,

// action button in the table toolbar / row
@UI.lineItem: [{ type: #FOR_ACTION, label: 'Change Criticality',
                 dataAction: 'changeCriticality', position: 10,
                 invocationGrouping: #CHANGE_SET }]
```

**Object page: facets, identification, field groups**
```abap
@UI.facet: [
  // header area
  { id: 'idPrice', purpose: #HEADER, type: #DATAPOINT_REFERENCE,
    targetQualifier: 'hdPrice', position: 10 },
  { id: 'idDates', purpose: #HEADER, type: #FIELDGROUP_REFERENCE,
    targetQualifier: 'hdDates', position: 20 },

  // body: collection groups reference facets
  { id: 'idGeneral', type: #COLLECTION, label: 'General Information', position: 10 },
  { id: 'idIdent',   type: #IDENTIFICATION_REFERENCE, label: 'Travel',
    parentId: 'idGeneral', position: 10 },
  { id: 'idAdmin',   type: #FIELDGROUP_REFERENCE, label: 'Administrative Data',
    targetQualifier: 'fgAdmin', parentId: 'idGeneral', position: 20 },

  // child list via composition/association
  { id: 'idBookings', type: #LINEITEM_REFERENCE, label: 'Bookings',
    position: 20, targetElement: '_Booking' },

  // quick view popover
  { type: #FIELDGROUP_REFERENCE, label: 'Agency',
    targetQualifier: 'qvAgency', purpose: #QUICK_VIEW }
]
```
```abap
@UI.identification: [{ position: 10, label: 'Travel ID' }]
@UI.identification: [{ type: #FOR_ACTION, label: 'Accept Travel', dataAction: 'acceptTravel' }]
@UI.fieldGroup: [{ qualifier: 'fgAdmin', position: 10 }]
@UI.dataPoint: { qualifier: 'hdPrice', title: 'Total Price',
                 criticality: 'StatusCriticality' }
@UI.multiLineText: true
@UI.hidden: true                      // or @UI.hidden: 'IsHiddenField' (dynamic)
@UI.textArrangement: #TEXT_ONLY       // #TEXT_FIRST, #TEXT_LAST, #TEXT_SEPARATE
@UI.adaptationHidden: true
```

**Text, semantics, search, object model**
```abap
@ObjectModel.text.element: [ 'AgencyName' ]
@ObjectModel.foreignKey.association: '_Agency'
@ObjectModel.resultSet.sizeCategory: #XS       // #XS #S #M #L #XL
@Semantics.amount.currencyCode: 'CurrencyCode'
@Semantics.quantity.unitOfMeasure: 'Unit'
@Semantics.currencyCode: true
@Semantics.unitOfMeasure: true
@Semantics.eMail.address: true
@Semantics.telephone.type: [#WORK]
@Semantics.booleanIndicator: true
@Semantics.timeZone: true
@Semantics.timeZoneReference: 'IANATimezone'
@Semantics.user.createdBy: true
@Semantics.systemDateTime.createdAt: true
@Semantics.user.lastChangedBy: true
@Semantics.systemDateTime.lastChangedAt: true
@Semantics.systemDateTime.localInstanceLastChangedAt: true
@EndUserText.label: 'Agency'
@EndUserText.quickInfo: 'Travel agency responsible for this booking'
```

**Value help — with additional binding (in/out mapping)**
```abap
// plain
@Consumption.valueHelpDefinition: [{ entity: { name: '/DMO/I_Agency', element: 'AgencyID' } }]

// filter the value list by another field of the local entity (IN parameter)
@Consumption.valueHelpDefinition: [{
  entity: { name: '/DMO/FSA_I_Contact', element: 'ID' },
  label: 'Contacts',
  additionalBinding: [{ element: 'Country', localElement: 'Country', usage: #FILTER }] }]

// also copy a value back on selection (OUT parameter)
@Consumption.valueHelpDefinition: [{
  entity: { name: 'I_RegionVH', element: 'Region' },
  qualifier: 'RegionValueHelp',
  useForValidation: true,
  additionalBinding: [{ element: 'Country', localElement: 'Country',
                        usage: #FILTER_AND_RESULT }] }]

@Consumption.valueHelpDefault.display: true
@Consumption.filter: { selectionType: #RANGE, multipleSelections: true, mandatory: false }
```

**Metadata extension (keeps UI annotations out of the data model)**
```abap
@Metadata.layer: #CORE          // #CORE < #LOCALIZATION < #INDUSTRY < #PARTNER < #CUSTOMER
annotate entity ZC_Travel with
{
  @UI.facet: [ { id: 'idGeneral', type: #COLLECTION, label: 'General', position: 10 } ]
  @UI.lineItem: [{ position: 10 }]
  @UI.selectionField: [{ position: 10 }]
  TravelID;
}
```
`[~]` `ANNOTATE ENTITY` is the form for view entities; `ANNOTATE VIEW` is the older form for DDIC-based views. The base view must carry `@Metadata.allowExtensions: true`. **`[?]` verify which keyword your release accepts.**

### C.5 Access control (DCL)

`[✓]` [ABAP CDS Access Control](https://sapabapcentral.blogspot.com/p/abap-cds-access-control.html), [25_Authorization_Checks.md](https://github.com/SAP-samples/abap-cheat-sheets/blob/main/25_Authorization_Checks.md).

```abap
@EndUserText.label: 'Travel access control'
@MappingRole: true
define role ZI_TRAVEL_ACC {
  grant select on ZI_Travel
    where ( AgencyID )   = aspect pfcg_auth( ZTRAVEL, ZAGENCY, ACTVT = '03' )
      and ( CurrencyCode ) = 'EUR';

  // inherit conditions from another entity's role instead of duplicating them
  grant select on ZI_Booking
    where inheriting conditions from entity ZI_Travel;
}
```

Rules `[✓]`:
- The view's `@AccessControl.authorizationCheck` controls enforcement: `#CHECK` (default, warn if no role), `#NOT_REQUIRED` (suppress the warning, control still applies if a role exists), `#NOT_ALLOWED` (no control; defining a role is a warning). **`[?]`** One source additionally lists `#MANDATORY`/`#PRIVILEGED_ONLY` — verify against your release's keyword docs before documenting them.
- Multiple roles on the same entity ⇒ conditions **OR**-ed together.
- Within a condition, `AND` binds tighter than `OR`; parentheses may **not** be nested, must contain exactly two subconditions, max four parenthesized groups.
- DCL only filters **read** access via CDS. Modify-side authorization is separate (RAP `authorization master` + `get_global_authorizations` / `get_instance_authorizations`, or `AUTHORITY-CHECK`).
- ABAP SQL bypasses DCL unless you read through the CDS entity **and** the entity is not accessed with `PRIVILEGED` mode; `SELECT` on the underlying table never applies DCL.

---

## D. RAP (RESTful Application Programming Model)

### D.1 Managed vs unmanaged — the decision

| | Use when |
|---|---|
| **Managed** | Greenfield BO, you own the persistence (a Z table), you want CRUD/draft/locking/etag/numbering for free. This is the default for new build. |
| **Managed with unmanaged save** (`with unmanaged save`) | Framework handles the transactional buffer and validations, but the final persistence must go through an existing API (BAPI/FM) rather than direct table writes. |
| **Managed with additional save** (`with additional save`) | Framework persists as usual **and** you need extra work in the save sequence (e.g. write a log, call a follow-on API). |
| **Unmanaged** | Wrapping a legacy application that already owns its buffer, locks and save logic (classic BAPI-based BO). You implement every operation: `FOR MODIFY`, `FOR READ`, `FOR LOCK`, `save_modified`, `cleanup`. Highest effort. |
| **Abstract / read-only (query)** | Analytical or list-only services; `provider contract transactional_query` with no behavior, or a custom entity + query implementation class. |

`[~]` classification; the `with additional save` / `with unmanaged save` keywords are confirmed by community sources and match the BDL grammar.

### D.2 Behavior definition (managed, draft, strict 2)

`[✓]` Confirmed from [36_RAP_Behavior_Definition_Language.md](https://github.com/SAP-samples/abap-cheat-sheets/blob/main/36_RAP_Behavior_Definition_Language.md) and [RAP Draft](https://software-heroes.com/en/blog/abap-rap-draft-en).

```abap
managed implementation in class zbp_i_travel unique;
strict ( 2 );
with draft;

define behavior for ZI_Travel alias Travel
persistent table ztravel
draft table ztravel_d
lock master
total etag LocalLastChangedAt
authorization master ( instance )
etag master LocalLastChangedAt
early numbering                       // or: late numbering
{
  field ( numbering : managed, readonly ) TravelUUID;
  field ( readonly ) TravelID, TotalPrice, OverallStatus,
                     CreatedBy, CreatedAt, LastChangedBy, LastChangedAt,
                     LocalLastChangedAt;
  field ( mandatory ) AgencyID, CustomerID, BeginDate, EndDate;
  field ( mandatory : create, readonly : update ) CurrencyCode;
  field ( features : instance ) BookingFee;

  create;
  update;
  delete;

  action ( features : instance ) acceptTravel result [1] $self;
  action ( features : instance ) rejectTravel result [1] $self;
  action deductDiscount parameter ZA_DiscountParam result [1] $self;
  static action createFromTemplate parameter ZA_Template result [1] $self;
  factory action copyTravel [1];
  internal action recalcTotalPrice;

  determination setInitialStatus on modify { create; }
  determination calcTotalPrice   on modify { field BookingFee; create; }
  determination setTravelID      on save   { create; }

  validation validateAgency   on save { create; field AgencyID; }
  validation validateCustomer on save { create; field CustomerID; }
  validation validateDates    on save { create; field BeginDate, EndDate; }

  side effects {
    field BookingFee    affects field TotalPrice;
    action acceptTravel affects field OverallStatus, LocalLastChangedAt;
    determine action Prepare affects messages;
  }

  draft action Resume;
  draft action Edit;
  draft action Activate optimized;
  draft action Discard;
  draft determine action Prepare {
    validation validateAgency;
    validation validateCustomer;
    validation validateDates;
  }

  mapping for ztravel corresponding
  {
    TravelUUID = travel_uuid;
    TravelID   = travel_id;
    AgencyID   = agency_id;
  }

  association _Booking { create; with draft; }
}

define behavior for ZI_Booking alias Booking
implementation in class zbp_i_booking unique
persistent table zbooking
draft table zbooking_d
lock dependent by _Travel
authorization dependent by _Travel
etag master LocalLastChangedAt
{
  field ( readonly ) TravelUUID, BookingUUID;
  update; delete;
  association _Travel { with draft; }
}
```

Draft admin include (required on the draft CDS entity) `[✓]`:
```abap
define view entity ZI_Travel_D as select from ztravel_d { ... }
// or, in the draft table definition / draft entity:
//   %admin : include sych_bdl_draft_admin_inc;
```
**`[?]`** The exact placement of `include sych_bdl_draft_admin_inc;` (draft *table* vs draft *entity*) should be verified — in current practice ADT generates the draft table for you via the quick-fix, which is the recommended route.

### D.3 Behavior projection (the UI layer)

```abap
projection;
strict ( 2 );
use draft;

define behavior for ZC_Travel alias Travel
use etag
{
  use create;
  use update;
  use delete;

  use action acceptTravel;
  use action rejectTravel;
  use action deductDiscount;
  use action Edit;
  use action Activate;
  use action Discard;
  use action Resume;
  use action Prepare;

  use association _Booking { create; with draft; }
}
```

### D.4 Behavior implementation (ABAP behavior pool) skeleton

```abap
CLASS lhc_travel DEFINITION INHERITING FROM cl_abap_behavior_handler.
  PRIVATE SECTION.
    METHODS get_instance_features FOR INSTANCE FEATURES
      IMPORTING keys REQUEST requested_features FOR Travel RESULT result.

    METHODS get_instance_authorizations FOR INSTANCE AUTHORIZATION
      IMPORTING keys REQUEST requested_authorizations FOR Travel RESULT result.

    METHODS get_global_authorizations FOR GLOBAL AUTHORIZATION
      IMPORTING REQUEST requested_authorizations FOR Travel RESULT result.

    METHODS setInitialStatus FOR DETERMINE ON MODIFY
      IMPORTING keys FOR Travel~setInitialStatus.

    METHODS calcTotalPrice FOR DETERMINE ON MODIFY
      IMPORTING keys FOR Travel~calcTotalPrice.

    METHODS validateAgency FOR VALIDATE ON SAVE
      IMPORTING keys FOR Travel~validateAgency.

    METHODS acceptTravel FOR MODIFY
      IMPORTING keys FOR ACTION Travel~acceptTravel RESULT result.

    METHODS copyTravel FOR MODIFY
      IMPORTING keys FOR ACTION Travel~copyTravel.
ENDCLASS.

CLASS lhc_travel IMPLEMENTATION.

  METHOD get_global_authorizations.
    IF requested_authorizations-%create = if_abap_behv=>mk-on.
      AUTHORITY-CHECK OBJECT 'ZTRAVEL' ID 'ZAGENCY' DUMMY ID 'ACTVT' FIELD '01'.
      result-%create = COND #( WHEN sy-subrc = 0 THEN if_abap_behv=>auth-allowed
                                                 ELSE if_abap_behv=>auth-unauthorized ).
    ENDIF.
  ENDMETHOD.

  METHOD validateAgency.
    " 1) read only the fields you need, in local mode
    READ ENTITIES OF ZI_Travel IN LOCAL MODE
      ENTITY Travel
        FIELDS ( AgencyID )
        WITH CORRESPONDING #( keys )
      RESULT DATA(lt_travels).

    " 2) one set-based check, not one SELECT per instance
    DATA(lt_agencies) = VALUE ty_agency_keys(
      FOR ls IN lt_travels ( agency_id = ls-AgencyID ) ).
    SORT lt_agencies BY agency_id.
    DELETE ADJACENT DUPLICATES FROM lt_agencies COMPARING agency_id.

    SELECT FROM /dmo/agency FIELDS agency_id
      FOR ALL ENTRIES IN @lt_agencies
      WHERE agency_id = @lt_agencies-agency_id
      INTO TABLE @DATA(lt_valid).

    " 3) report failures + messages
    LOOP AT lt_travels INTO DATA(ls_travel).
      IF ls_travel-AgencyID IS INITIAL
         OR NOT line_exists( lt_valid[ agency_id = ls_travel-AgencyID ] ).
        APPEND VALUE #( %tky = ls_travel-%tky ) TO failed-travel.
        APPEND VALUE #( %tky = ls_travel-%tky
                        %state_area = 'VALIDATE_AGENCY'
                        %msg = new_message( id       = 'ZTRAVEL'
                                            number   = '002'
                                            severity = if_abap_behv_message=>severity-error
                                            v1       = ls_travel-AgencyID )
                        %element-AgencyID = if_abap_behv=>mk-on
                      ) TO reported-travel.
      ENDIF.
    ENDLOOP.
  ENDMETHOD.

  METHOD acceptTravel.
    MODIFY ENTITIES OF ZI_Travel IN LOCAL MODE
      ENTITY Travel
        UPDATE FIELDS ( OverallStatus )
        WITH VALUE #( FOR key IN keys ( %tky          = key-%tky
                                        OverallStatus = 'A' ) )
      FAILED   failed
      REPORTED reported.

    READ ENTITIES OF ZI_Travel IN LOCAL MODE
      ENTITY Travel ALL FIELDS WITH CORRESPONDING #( keys )
      RESULT DATA(lt_travels).

    result = VALUE #( FOR ls IN lt_travels
                      ( %tky = ls-%tky %param = ls ) ).
  ENDMETHOD.

ENDCLASS.

" Saver class (only needed for unmanaged / additional / unmanaged save)
CLASS lsc_zi_travel DEFINITION INHERITING FROM cl_abap_behavior_saver.
  PROTECTED SECTION.
    METHODS finalize          REDEFINITION.
    METHODS check_before_save REDEFINITION.
    METHODS adjust_numbers    REDEFINITION.
    METHODS save              REDEFINITION.
    METHODS cleanup           REDEFINITION.
    METHODS cleanup_finalize  REDEFINITION.
ENDCLASS.
```

`[~]` Method names/`REDEFINITION` set of `cl_abap_behavior_saver` — `finalize`, `check_before_save`, `adjust_numbers`, `save`, `cleanup`, `cleanup_finalize` — matches current RAP; **`[?]`** `save_modified` (used in the *unmanaged/additional-save* saver, `cl_abap_behavior_saver_failed`? ) should be verified against the release.

### D.5 EML — calling a RAP BO from ABAP

`[✓]` [08_EML_ABAP_for_RAP.md](https://github.com/SAP-samples/abap-cheat-sheets/blob/main/08_EML_ABAP_for_RAP.md).

```abap
" ---- READ ----
READ ENTITIES OF ZI_Travel
  ENTITY Travel
    FIELDS ( TravelID AgencyID TotalPrice )
    WITH VALUE #( ( TravelUUID = lv_uuid ) )
  RESULT DATA(lt_travels)
  FAILED DATA(lt_failed)
  REPORTED DATA(lt_reported).

" read children by association
READ ENTITIES OF ZI_Travel
  ENTITY Travel BY \_Booking
    ALL FIELDS WITH VALUE #( ( TravelUUID = lv_uuid ) )
  RESULT DATA(lt_bookings)
  FAILED DATA(lt_failed2).

" ---- CREATE (short form: FIELDS ... WITH sets %control automatically) ----
MODIFY ENTITIES OF ZI_Travel
  ENTITY Travel
    CREATE FIELDS ( AgencyID CustomerID BeginDate EndDate CurrencyCode )
      WITH VALUE #( ( %cid = 'C1' AgencyID = '070001' CustomerID = '000001'
                      BeginDate = '20260901' EndDate = '20260910'
                      CurrencyCode = 'EUR' ) )
  MAPPED   DATA(ls_mapped)
  FAILED   DATA(ls_failed)
  REPORTED DATA(ls_reported).

DATA(lv_new_uuid) = ls_mapped-travel[ 1 ]-TravelUUID.   " %cid -> real key

" ---- CREATE BY ASSOCIATION (deep create) ----
MODIFY ENTITIES OF ZI_Travel
  ENTITY Travel
    CREATE BY \_Booking
      FIELDS ( BookingDate CarrierID ConnectionID FlightPrice CurrencyCode )
      WITH VALUE #( ( TravelUUID = lv_new_uuid
                      %target = VALUE #( ( %cid = 'B1' BookingDate = sy-datum
                                           CarrierID = 'LH' ConnectionID = '0400'
                                           FlightPrice = '1000' CurrencyCode = 'EUR' ) ) ) )
  MAPPED DATA(ls_m2) FAILED DATA(ls_f2) REPORTED DATA(ls_r2).

" ---- UPDATE / DELETE ----
MODIFY ENTITIES OF ZI_Travel
  ENTITY Travel
    UPDATE FIELDS ( BookingFee )
      WITH VALUE #( ( TravelUUID = lv_uuid BookingFee = '50' ) )
    DELETE FROM VALUE #( ( TravelUUID = lv_other ) )
  FAILED DATA(ls_f3) REPORTED DATA(ls_r3).

" ---- EXECUTE ACTION ----
MODIFY ENTITIES OF ZI_Travel
  ENTITY Travel
    EXECUTE acceptTravel FROM VALUE #( ( TravelUUID = lv_uuid ) )
  RESULT DATA(lt_action_result)
  FAILED DATA(ls_f4) REPORTED DATA(ls_r4).

" ---- PERMISSIONS (what may the caller do?) ----
GET PERMISSIONS OF ZI_Travel
  ENTITY Travel
    REQUEST VALUE #( %update = if_abap_behv=>mk-on
                     %action-acceptTravel = if_abap_behv=>mk-on )
    FILTER FROM VALUE #( ( TravelUUID = lv_uuid ) )
  RESULT DATA(lt_perm)
  FAILED DATA(ls_f5) REPORTED DATA(ls_r5).

" ---- COMMIT / ROLLBACK ----
COMMIT ENTITIES
  RESPONSE OF ZI_Travel
    FAILED   DATA(ls_commit_failed)
    REPORTED DATA(ls_commit_reported).

IF ls_commit_failed IS NOT INITIAL.
  ROLLBACK ENTITIES.
ENDIF.

" or aggregate over all BOs in the LUW
COMMIT ENTITIES RESPONSES
  FAILED   DATA(ls_all_failed)
  REPORTED DATA(ls_all_reported).
```

BDEF-derived types and component groups `[✓]`:
`TYPE TABLE FOR CREATE|UPDATE|DELETE|ACTION IMPORT|ACTION RESULT entity`, `TYPE STRUCTURE FOR READ RESULT|CREATE|...`, `TYPE RESPONSE FOR MAPPED|FAILED|REPORTED|PERMISSIONS entity`.
`%key`, `%tky` (key incl. `%is_draft`), `%data`, `%control`, `%cid`, `%cid_ref`, `%pid`, `%is_draft`, `%param`, `%target`, `%msg`, `%state_area`, `%element`, `%update`, `%delete`, `%action-<name>`, `%assoc-<name>`, `%fail-cause`.

`IN LOCAL MODE` — from inside a behavior pool: skips feature control, authorization and (per SAP) the projection layer, so you read/write the full base BO. Use it in every handler method that reads or writes its own BO.

### D.6 Service definition & binding

```abap
@EndUserText.label: 'Travel service — UI'
define service ZUI_TRAVEL {
  expose ZC_Travel      as Travel;
  expose ZC_Booking     as Booking;
  expose /DMO/I_Agency  as Agency;      // value help
  expose I_Currency     as Currency;
}
```

Service binding (ADT wizard, no source) — choose:

| Binding type | Use for |
|---|---|
| `OData V2 - UI` | Fiori Elements V2 apps, SAP GUI-era tooling, on-prem where V4 FE is not an option |
| `OData V4 - UI` | New Fiori Elements apps (the default choice for greenfield) |
| `OData V2 - Web API` | Machine-to-machine, integration; **publishes value helps automatically** `[✓]` |
| `OData V4 - Web API` | Machine-to-machine; **does not** publish value helps automatically `[✓]` |
| `InA - UI` | Analytical (Analytics Cloud / Query Browser) `[~]` |

Source: [rap-opensap week5/unit7](https://github.com/SAP-samples/abap-platform-rap-opensap/blob/main/week5/unit7.md).

Practical notes: only one binding may be *published* per service definition + protocol combination on a given system `[~]`; the binding creates the service URL `/sap/opu/odata4/sap/<binding>/srvd/sap/<service_def>/0001/`; local service endpoint publishing replaces `/IWFND/MAINT_SERVICE` for RAP V4.

### D.7 Clean core / ABAP Cloud

The 3-tier extensibility model `[✓]` ([ABAP Cloud 3-tier model](https://software-heroes.com/en/blog/abap-cloud-3-tier-model), [SAP ABAP Extensibility Guide](https://community.sap.com/t5/technology-blog-posts-by-sap/abap-extensibility-guide-clean-core-for-sap-s-4hana-cloud-august-2025/ba-p/14175399)):

- **Tier 1 — ABAP Cloud.** ABAP language version *ABAP for Cloud Development*. Only released (C1-contract) APIs and extension points. RAP, CDS, Fiori, Application Jobs, new Application Log. **No** SAP GUI, dynpro, `WRITE` lists, file system, direct SAP table reads. This is where new custom code belongs.
- **Tier 2 — the wrapper/API layer.** *Standard ABAP* language version. Thin wrappers/facades over non-released SAP objects (BAPIs, FMs, classes, CDS views) that tier 1 needs. The wrapper is itself C1-released so tier 1 may consume it. Document each wrapper as technical debt and file an influence request asking SAP to release the underlying API.
- **Tier 3 — classic ABAP.** Legacy: user exits, modifications, reports, dynpro, file access. Frozen; migrate upward as APIs become available.

Restrictions in *ABAP for Cloud Development* `[✓]` ([19_ABAP_for_Cloud_Development.md](https://github.com/SAP-samples/abap-cheat-sheets/blob/main/19_ABAP_for_Cloud_Development.md)):

| Forbidden / obsolete | Replacement |
|---|---|
| `MOVE ... TO` | `=` |
| `DESCRIBE TABLE ... LINES` | `lines( )` |
| `GET REFERENCE OF` | `REF #( )` |
| `WRITE`, classic lists, dynpro, `SUBMIT` executables | Fiori / RAP / Application Jobs |
| `CALL FUNCTION ... DESTINATION` | released comm-arrangement APIs, HTTP/OData client (`cl_web_http_client_manager`) |
| `OPEN DATASET` / `AL11` | `cl_fdt_...`? no — use the released file/blob APIs, BTP object store, or an inbound service `[?]` verify the current released alternative |
| `AUTHORITY-CHECK` | CDS DCL + RAP authorization; `[?]` a released authorization API exists in newer releases — verify name |
| classic `MESSAGE` dialog | `%msg` / `new_message( )`, message container |
| `USING CLIENT` in ABAP SQL | not available |
| `sy-datum`, `sy-uzeit`, `sy-timlo` | `cl_abap_context_info=>get_system_date( ) / get_system_time( )`, `xco_cp_time` |
| direct `SELECT` on SAP tables | released CDS views / released APIs only |
| SE80, SE24, SE38 | ADT only |

Finding released objects: ADT → *Released Objects* node in Project Explorer; check *Properties → API State*. Release contracts: **C0** (internal), **C1** (public API / use system-internally), **C2** (extend), **C3**? `[?]` — verify the full contract list before documenting it.

Extension ranking to encode in the skill (most → least preferred) `[~]`:
1. Configuration / standard customizing.
2. Key-user extensibility (custom fields & logic, Fiori adaptation, Custom CDS Views, Custom Analytical Queries).
3. Side-by-side on BTP consuming released APIs + events.
4. Developer extensibility in ABAP Cloud (tier 1) — released BAdIs/extension points, RAP extensions, CDS extend, metadata extensions.
5. Classic extensibility (tier 2/3), in order: **released** BAdI → classic BAdI/enhancement spot (explicit) → append/include structures → implicit enhancement → customer exit (SMOD/CMOD) / classic user exit.
6. **Never:** modification/repair of SAP objects, `%_HINTS`, access-key changes, writes to SAP tables.

---

---

## Z. Activation gotchas that bite most often

These are the mistakes that get past a plausible-looking draft and only surface as an
activation error or an empty Fiori screen. Check each one before handing over RAP code.

### Z.1 A validation must clear its own state area

Reporting a message is not enough. A draft keeps the previous run's messages until you
explicitly invalidate the state area, so a fixed record keeps showing the old error.
Report a key-only entry for the state area first, then the messages:

```abap
METHOD validateDuration.
  READ ENTITIES OF zr_pp_downtime IN LOCAL MODE
    ENTITY Downtime FIELDS ( StartTimestamp EndTimestamp )
    WITH CORRESPONDING #( keys )
    RESULT DATA(downtimes).

  LOOP AT downtimes INTO DATA(downtime).
    " 1) always clear the previous verdict for this key + state area
    APPEND VALUE #( %tky        = downtime-%tky
                    %state_area = 'VALIDATE_DURATION' ) TO reported-downtime.

    " 2) only now report a new failure, if there is one
    IF downtime-EndTimestamp <= downtime-StartTimestamp.
      APPEND VALUE #( %tky = downtime-%tky ) TO failed-downtime.
      APPEND VALUE #( %tky        = downtime-%tky
                      %state_area = 'VALIDATE_DURATION'
                      %msg        = new_message( id       = 'ZPP_DOWNTIME'
                                                 number   = '001'
                                                 severity = if_abap_behv_message=>severity-error )
                      %element-EndTimestamp = if_abap_behv=>mk-on
                    ) TO reported-downtime.
    ENDIF.
  ENDLOOP.
ENDMETHOD.
```

### Z.2 `@UI.facet` belongs to the entity, not to an element

In a metadata extension or a view, `@UI.facet` is an **entity-level** annotation. Put it
in the `annotate entity` header block (or directly above `define view entity`), not in
front of a field — Fiori Elements will not find it there and the object page renders
empty. Likewise `presentationVariant` takes `visualizations: [{ ... }]` (plural, array),
not `visualization: { }`.

### Z.3 A behavior projection must re-declare what it uses

The projection is an allow-list, not an inheritance. Every element of the base behavior
you want on the UI has to be named:

```abap
projection;
strict ( 2 );
use draft;

define behavior for ZC_PP_Downtime alias Downtime
{
  use etag;                      " required when the base declares etag master
  use create;
  use update;
  use delete;

  use action Edit;
  use action Activate;
  use action Discard;
  use action Resume;
  use action Prepare;
}
```

Two consequences worth remembering: `use etag` is not optional once the base BDEF has
`etag master`, and **new** behaviour in a projection — side effects, extra actions,
extra determinations — requires the `augmenting` form (`define behavior for ... alias ...
augmenting { ... }`). `use side effects { ... }` referring to something the base never
declared will not activate.

### Z.4 Do not hand-type the draft table or the admin data elements

Generate the draft table with the ADT quick-fix on the `draft table` clause in the BDEF.
The administrative field types (`abp_*` creation/change timestamp elements, `%admin`
structures) have names that differ by release, and getting them wrong from memory is
common — see `KNOWN_UNCERTAINTIES.md`. State the field's role and let ADT supply the
element, rather than asserting an element name.

### Z.5 Released-API assumptions

`I_Plant`, `I_PlantStdVH` and similar released CDS views exist on most S/4 systems, but
their release status, key element names and field names vary by release and by whether
the system is on-premise or Cloud. Check in ADT before making one a value-help provider
or a join partner, and say in the answer that it needs checking.
