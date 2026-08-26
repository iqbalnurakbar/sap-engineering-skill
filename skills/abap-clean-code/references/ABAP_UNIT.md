# ABAP Unit — Tests, Doubles, Injection

> **Source**: ABAP Keyword Documentation (help.sap.com/doc/abapdocu_latest_index_htm), github.com/SAP/styleguides, github.com/SAP-samples/abap-cheat-sheets, SAP-samples RAP/Fiori reference apps, developers.sap.com tutorials.
> Confidence markers used below: `[OK]` = verified against an authoritative source cited inline; `[~]` = widely used and consistent with sources but not verbatim-confirmed; `[?]` = uncertain, verify in the target system before shipping.

## Contents

- [H. ABAP Unit Testing](#h-abap-unit-testing)
  - [H.1 Test class skeleton](#h1-test-class-skeleton)
  - [H.2 Dependency injection styles `[✓]`](#h2-dependency-injection-styles)
  - [H.3 Test doubles](#h3-test-doubles)
  - [H.4 Practical rules](#h4-practical-rules)

---

## H. ABAP Unit Testing

`[✓]` [14_ABAP_Unit_Tests.md](https://github.com/SAP-samples/abap-cheat-sheets/blob/main/14_ABAP_Unit_Tests.md)

### H.1 Test class skeleton

```abap
CLASS ltc_order_calculator DEFINITION FINAL
  FOR TESTING
  RISK LEVEL HARMLESS          " HARMLESS | CRITICAL (system settings) | DANGEROUS (persistent data)
  DURATION SHORT.              " SHORT (seconds) | MEDIUM (minutes) | LONG (> 1 min)

  PRIVATE SECTION.
    DATA mo_cut          TYPE REF TO zcl_order_calculator.   " code under test
    DATA mo_price_double TYPE REF TO zif_price_provider.

    CLASS-METHODS class_setup.        " once, before all tests
    CLASS-METHODS class_teardown.     " once, after all tests
    METHODS setup.                    " before EACH test
    METHODS teardown.                 " after EACH test

    METHODS discount_applies_over_100 FOR TESTING RAISING cx_static_check.
    METHODS discount_not_under_100    FOR TESTING RAISING cx_static_check.
    METHODS zero_amount_raises        FOR TESTING RAISING cx_static_check.
ENDCLASS.

CLASS ltc_order_calculator IMPLEMENTATION.

  METHOD setup.
    mo_price_double = CAST zif_price_provider(
                        cl_abap_testdouble=>create( 'ZIF_PRICE_PROVIDER' ) ).
    mo_cut = NEW zcl_order_calculator( io_prices = mo_price_double ).
  ENDMETHOD.

  METHOD discount_applies_over_100.
    " GIVEN
    cl_abap_testdouble=>configure_call( mo_price_double )->returning( '150.00' ).
    mo_price_double->get_price( 'MAT-1' ).

    " WHEN
    DATA(lv_total) = mo_cut->total_for( iv_material = 'MAT-1' iv_qty = 1 ).

    " THEN
    cl_abap_unit_assert=>assert_equals(
      exp = CONV decfloat34( '135.00' )
      act = lv_total
      msg = '10% discount must apply above 100' ).
  ENDMETHOD.

  METHOD zero_amount_raises.
    TRY.
        mo_cut->total_for( iv_material = 'MAT-1' iv_qty = 0 ).
        cl_abap_unit_assert=>fail( 'Expected zcx_order_invalid' ).
      CATCH zcx_order_invalid.
        " expected
    ENDTRY.
  ENDMETHOD.

ENDCLASS.
```

Assertions `[✓]`: `assert_equals`, `assert_differs`, `assert_bound` / `assert_not_bound`, `assert_initial` / `assert_not_initial`, `assert_true` / `assert_false`, `assert_subrc`, `assert_char_cp` / `assert_char_np`, `assert_table_contains` / `assert_table_not_contains`, `assert_number_between`, `fail`, `skip` (test not executable — missing prerequisite), `abort`.

### H.2 Dependency injection styles `[✓]`

1. **Constructor injection** (preferred): dependency passed to `CONSTRUCTOR`, defaulted to the real implementation when omitted.
2. **Setter injection**: `set_price_provider( )` — use when the dependency is optional or changes at runtime.
3. **Parameter injection**: an optional method parameter — smallest blast radius, good for legacy code.
4. **Back-door injection**: `CLASS ltc_x DEFINITION ... .` + `CLASS zcl_prod DEFINITION LOCAL FRIENDS ltc_x.` to reach private members. Use sparingly; it couples the test to internals.

Clean ABAP testing rules `[✓]`: write testable code (interfaces at the seams); test the public API, not privates; use given/when/then; few, focused assertions per test; don't mock what you don't need; don't sub-class production classes to fake methods; don't build your own test framework.

### H.3 Test doubles

```abap
" ---- Interface double (ABAP Test Double Framework) ----
DATA(lo_double) = CAST zif_dep( cl_abap_testdouble=>create( 'ZIF_DEP' ) ).

" configure a return value for a specific input
cl_abap_testdouble=>configure_call( lo_double )->returning( '42' ).
lo_double->get_value( iv_key = 'A' ).            " "recording" call

" ignore the parameters, always return
cl_abap_testdouble=>configure_call( lo_double )->ignore_all_parameters( )->returning( '42' ).
lo_double->get_value( iv_key = 'X' ).

" raise an exception
cl_abap_testdouble=>configure_call( lo_double )->raise_exception( NEW zcx_dep_error( ) ).
lo_double->get_value( iv_key = 'BAD' ).

" verify interactions
cl_abap_testdouble=>configure_call( lo_double )->and_expect( )->is_called_times( 2 ).
lo_double->get_value( iv_key = 'A' ).
" ... exercise ...
cl_abap_testdouble=>verify_expectations( lo_double ).
```
`[~]` Method names (`create`, `configure_call`, `returning`, `raise_exception`, `ignore_all_parameters`, `and_expect`, `is_called_times`/`is_called_once`, `verify_expectations`) are the standard ATDF API. **`[?]`** confirm `and_expect( )->is_called_times( )` chaining shape for your release.

```abap
" ---- Hand-written double for an interface, without implementing everything ----
CLASS ltd_price DEFINITION FOR TESTING.
  PUBLIC SECTION.
    INTERFACES zif_price_provider PARTIALLY IMPLEMENTED.   " [✓]
ENDCLASS.

" ---- OSQL Test Double Framework: replace DB tables / CDS in ABAP SQL ----
CLASS ltc_repo DEFINITION FOR TESTING RISK LEVEL HARMLESS DURATION SHORT.
  PRIVATE SECTION.
    CLASS-DATA mo_osql TYPE REF TO if_osql_test_environment.
    CLASS-METHODS class_setup.
    CLASS-METHODS class_teardown.
    METHODS setup.
    METHODS reads_open_items FOR TESTING RAISING cx_static_check.
ENDCLASS.

CLASS ltc_repo IMPLEMENTATION.
  METHOD class_setup.
    mo_osql = cl_osql_test_environment=>create(
                i_dependency_list = VALUE #( ( 'ZTRAVEL' ) ( 'ZBOOKING' ) ) ).
  ENDMETHOD.
  METHOD class_teardown.
    mo_osql->destroy( ).
  ENDMETHOD.
  METHOD setup.
    mo_osql->clear_doubles( ).
    mo_osql->insert_test_data( VALUE ty_travels(
      ( travel_id = '001' agency_id = '070001' total_price = '1000' ) ) ).
  ENDMETHOD.
  METHOD reads_open_items.
    DATA(lt) = NEW zcl_travel_repo( )->read_all( ).
    cl_abap_unit_assert=>assert_equals( exp = 1 act = lines( lt ) ).
  ENDMETHOD.
ENDCLASS.

" ---- CDS Test Double Framework: stub the CDS entity's own data sources ----
DATA(lo_cds) = cl_cds_test_environment=>create( i_for_entity = 'ZI_TRAVEL' ).
lo_cds->clear_doubles( ).
lo_cds->insert_test_data( lt_source_rows ).
" ... SELECT FROM zi_travel now reads the doubles ...
lo_cds->destroy( ).

" ---- RAP BO test doubles ----
" transactional-buffer double (test a behavior pool against a fake buffer)
DATA(lo_env) = cl_botd_txbufdbl_bo_test_env=>prepare_for_test( ).
" mocked EML API (test a consumer of EML without the real BO)
DATA(lo_eml_env) = cl_botd_mockemlapi_bo_test_env=>prepare_for_test( ).
```
`[~]` `cl_osql_test_environment` / `cl_cds_test_environment` (`create`, `insert_test_data`, `clear_doubles`, `destroy`) confirmed. **`[?]`** `cl_botd_txbufdbl_bo_test_env` / `cl_botd_mockemlapi_bo_test_env` and the exact factory method (`prepare_for_test` vs `create`) — verify before documenting.

```abap
" ---- Test seams: last resort for untestable legacy code ----
" production:
TEST-SEAM read_config.
  SELECT SINGLE * FROM ztconfig INTO @ls_config WHERE id = @lv_id.
END-TEST-SEAM.

" test class:
TEST-INJECTION read_config.
  ls_config = VALUE #( id = 'X' threshold = 100 ).
END-TEST-INJECTION.
```
Use seams only when you cannot refactor (they leave test-only markers in production code and don't work with the OSQL framework's advantages).

### H.4 Practical rules
- `RISK LEVEL HARMLESS` + `DURATION SHORT` is the target for every unit test — anything else won't run in the CI gate.
- Tests must not depend on system data. If you find yourself needing a real material number, you need a double.
- Name tests as behavior statements: `discount_applies_over_100`, not `test_1`.
- Coverage: ADT → *Run As → ABAP Unit Test with Coverage*; ATC check for "class has no unit tests".
- In ABAP Cloud, `RISK LEVEL DANGEROUS` and real DB writes are effectively off the table — the OSQL/CDS double frameworks are mandatory.

---
