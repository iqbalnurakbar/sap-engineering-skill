# Clean ABAP — Rules for Writing New Code

> **Source**: SAP official style guide — github.com/SAP/styleguides/blob/main/clean-abap/CleanABAP.md (CC BY 4.0), plus its sub-sections AvoidEncodings.md and Enumerations.md. Section headings are quoted from the guide so every rule is traceable back to it.
> Confidence markers used below: `[OK]` = verified against an authoritative source cited inline; `[~]` = widely used and consistent with sources but not verbatim-confirmed; `[?]` = uncertain, verify in the target system before shipping.

# Clean ABAP — Rules for Writing New Code

Source: SAP/styleguides `clean-abap/CleanABAP.md` (main branch, as of 2026-08-26). Section titles below are quoted from the guide so each rule is traceable.

---

## Contents

- [0. Two global caveats the guide puts before everything else](#0-two-global-caveats-the-guide-puts-before-everything-else)
- [1. Names](#1-names)
- [2. Language choices — old → new pairs the guide actually names](#2-language-choices-old-new-pairs-the-guide-actually-names)
- [3. Constants & literals](#3-constants-literals)
- [4. Variables](#4-variables)
- [5. Tables](#5-tables)
- [6. Strings](#6-strings)
- [7. Booleans](#7-booleans)
- [8. Conditions](#8-conditions)
- [9. Ifs](#9-ifs)
- [10. Regular expressions](#10-regular-expressions)
- [11. Classes](#11-classes)
- [12. Methods](#12-methods)
- [13. Error handling](#13-error-handling)
- [14. Comments](#14-comments)
- [15. Formatting](#15-formatting)
- [16. Testing](#16-testing)
- [17. "How to" / severity & adoption guidance](#17-how-to-severity-adoption-guidance)
- [Explicit gaps — rules you asked about that are NOT in the guide](#explicit-gaps-rules-you-asked-about-that-are-not-in-the-guide)
- [I. Naming conventions](#i-naming-conventions)

---

## 0. Two global caveats the guide puts before everything else

**"Mind the legacy"** — many rules use relatively new syntax. *"Validate the guidelines you want to follow on the oldest release you must support. Do not simply discard Clean Code as a whole - the vast majority of rules (e.g. naming, commenting) will work in any ABAP version."*

**"Mind the performance"** — *"we strongly recommend to not optimize prematurely, based on obscure fears."* ABAP compares data types when calling a method, *"such that splitting a single large method into many sub-methods may make the code slower."* As little as 10% of code accounts for 90% of runtime; in ABAP a large share is DB time. Only after an actual measurement should you discard selected rules.

Release markers the guide itself gives (useful for generation targeting):
- `index += 1` — >= NW 7.54 (below that: `index = index + 1`)
- `TYPES BEGIN OF ENUM` — >= 7.51
- `RAISE EXCEPTION NEW` — >= 7.52
- `RAISE SHORTDUMP TYPE` — >= 7.53 (below: `MESSAGE x666(general)`)
- Field-symbol-free generic/dynamic access — ABAP Platform 2021+

---

## 1. Names

**Use descriptive names.** Names convey content and meaning; *"Do not focus on the data type or technical encoding. They hardly contribute to understanding the code."*

```ABAP
CONSTANTS max_wait_time_in_seconds TYPE i ...
DATA customizing_entries TYPE STANDARD TABLE ...
METHODS read_user_preferences ...
CLASS /clean/user_preference_reader ...

" anti-pattern
CONSTANTS sysubrc_04 TYPE sysubrc ...
DATA iso3166tab TYPE STANDARD TABLE ...
METHODS read_t005 ...
CLASS /dirty/t005_reader ...
```

**Prefer solution domain and problem domain terms.** Business-like layers → problem domain ("account", "ledger"); technical layers (factories, abstract algorithms) → solution domain ("queue", "tree"). *"do not attempt to make up your own language."*

**Use plural.** Against the SAP legacy singular habit: *"There is a legacy practice at SAP to name tables of things in singular, for example `country` for a 'table of countries' ... We therefore recommend to prefer `countries` instead."* Explicit scope note: *"This advice primarily targets things like variables and properties. For development objects, there may be competing patterns ... for example the widely used convention to name database tables ('transparent tables') in singular."*

**Use pronounceable names** — `detection_object_types`, not `dobjt`.

**Use snake_case.** ABAP is case-insensitive, so snake_case consistently. At the 30-character limit, *"don't fall back to using `flatcase` or `UPPERCASE`. Try to conscientiously use abbreviations instead."*

```ABAP
DATA max_response_time_in_millisec TYPE i.
" anti-pattern
DATA maxresponsetimeinmilliseconds TYPE i.
```

**Avoid abbreviations.** *"If you have enough space, write out names in full. Start abbreviating only if you exceed length limitations. If you do have to abbreviate, start with the unimportant words."* Rationale: *"does the 'cust' in `cust` mean 'customizing', 'customer', or 'custom'? All three are common in SAP applications."*

**Use same abbreviations everywhere.** Always "dobjt" for "detection object type" — never mix "dot", "dotype", "detobjtype". People search by keyword.

**Use nouns for classes and verbs for methods.**

```ABAP
CLASS /clean/account
CLASS /clean/user_preferences
INTERFACE /clean/customizing_reader

METHODS withdraw
METHODS add_message
METHODS read_entries

IF is_empty( table ).          " is_ / has_ prefixes for Boolean methods
FUNCTION /clean/read_alerts    " name functions like methods
```

**Avoid noise words such as "data", "info", "object".** `account` not `account_data`; `alert` not `alert_object`; or replace with something specific: `user_preferences` not `user_info`, `response_time_in_seconds` not `response_time_variable`.

**Pick one word per concept.** `read_this / read_that / read_those`, not `read_this / retrieve_that / query_those`. *"Synonyms will make the reader waste time on finding a difference that's not there."*

**Use pattern names only if you mean them.** Don't call a class `file_factory` unless it implements the factory pattern. (Named patterns: singleton, factory, facade, composite, decorator, iterator, observer, strategy.)

**Avoid obscuring built-in functions.** Within a class, a method with the same name as a built-in always obscures the function, regardless of parameter count/type. Don't name methods `lines`, `line_exists`, `condense`, `strlen`, etc.

### Hungarian notation / prefixes — the guide's actual position

Headline rule: **"Avoid encodings, esp. Hungarian notation and prefixes"** — *"We encourage you to get rid of **all** encoding prefixes."*

```ABAP
METHOD add_two_numbers.
  result = a + b.
ENDMETHOD.

" anti-pattern
METHOD add_two_numbers.
  rv_result = iv_a + iv_b.
ENDMETHOD.
```

The strength and the caveats matter for code generation:

- The guide **openly declares this a contradiction of the ABAP Programming Guidelines** sections *Names of Repository Objects* and *Program-Internal Names*, which recommend prefixes: *"We think that avoiding prefixes is the more modern and readable variant and that the guideline should be adjusted."* It also calls prefixing *"one of the most controversially discussed topics in ABAP."*
- Arguments given: 30-char budget; prefix disputes not worth it; five dimensions (kind, direction, scope, type, mutability) can't fit in 2 chars; team styles conflict (`lr_` = object ref or range table?); prefixes can mislead (`id_business_partner` is not an ID); `STANDARD`→`SORTED` shouldn't force `lt_`→`lts_`; `gt_sum`/`lt_sum` is worse than `total_sum`/`partial_sum`; the ABAP foundation itself no longer prefixes (see `cl_abap_math`); *"If you follow Clean Code, your methods will become so short (3-5 statements) that prefixing is no longer necessary."*
- **The only mandated prefix is your application's namespace.**
- **Explicit sanctioned compromise:** *"Avoid encodings in local contexts (within a method body, method parameters, local classes, etc.), and apply them only to global objects that are stored in the same global Dictionary namespace."* And: prefixes *"may be your only remaining lifeline in a thousand-line legacy function with cryptic variable names."*
- **Legacy caveat in "How to Refactor Legacy Code":** for legacy projects the Names section *"is very demanding ... up to a degree where sections like Avoid encodings ... are better ignored."* Also: don't mix styles inside one development object (don't mix `REF TO`/`FIELD-SYMBOL` loop targets, `NEW`/`CREATE OBJECT`, `RETURNING`/`EXPORTING` for single-output methods).
- Name-clash resolution once prefixes are gone: name the **interface generic, implementing classes specific**:

```ABAP
INTERFACE game_board. ... ENDINTERFACE.
CLASS game_board_as_list DEFINITION.  PUBLIC SECTION. INTERFACES game_board. ...
CLASS game_board_as_array DEFINITION. PUBLIC SECTION. INTERFACES game_board. ...
```
  and for parameter-vs-attribute clashes use `me->x_dimension = x_dimension.`; for structure-vs-table use singular/plural (`coordinate` / `coordinates`).

**On `get_`:** there is **no rule against `get_`** in this guide. `get_name`, `get_large_table`, `get_instance_for` appear in *good* examples. What exists is the adjacent rule **"Consider using immutable instead of getter"** (public `READ-ONLY` attributes instead of `get_a/get_b/get_c` for objects that never change after construction) and the creation-method verb guidance below. Do not generate a "never use get_" rule from this guide.

**Creation-method verbs:** *"Good words to start creation methods are `new_`, `create_`, and `construct_`"* — they compose into `new_from_template`, `create_as_copy`, `create_by_name`. Anti-pattern: `create_1 / create_2 / create_3`.

### Constant naming

**"Constants also need descriptive names"** — *"There is a historic tendency in ABAP to wrap every literal in constants, often with names that merely repeat their content or even just their type."*

```ABAP
" anti-pattern
CONSTANTS:
  c_01 TYPE spart VALUE '01',
  c_mmsta TYPE mmsta VALUE '90'.

" good — describes meaning, not content
CONSTANTS status_inactive TYPE mmsta VALUE '90'.

" acceptable — the value is already descriptive
CONSTANTS status_cancelled TYPE sww_wistat value 'CANCELLED'.
```

*"if the value ever needs to change then a constant named by its value must also be renamed."*

---

## 2. Language choices — old → new pairs the guide actually names

**"Prefer functional to procedural language constructs"** — *"They are usually shorter and come more natural to modern programmers."* This is the guide's own consolidated table (its comment lines are the obsolete forms):

```ABAP
DATA(variable) = 'A'.
" MOVE 'A' TO variable.

DATA(uppercase) = to_upper( lowercase ).
" TRANSLATE lowercase TO UPPER CASE.

index += 1.         " >= NW 7.54
index = index + 1.  " < NW 7.54
" ADD 1 TO index.

DATA(object) = NEW /clean/my_class( ).
" CREATE OBJECT object TYPE /dirty/my_class.

result = VALUE #( FOR row IN input ( row-text ) ).
" LOOP AT input INTO DATA(row).
"  INSERT row-text INTO TABLE result.
" ENDLOOP.

DATA(line) = value_pairs[ name = 'A' ].                      " entry must exist
DATA(line) = VALUE #( value_pairs[ name = 'A' ] OPTIONAL ).  " entry can be missing
" READ TABLE value_pairs INTO DATA(line) WITH KEY name = 'A'.

DATA(exists) = xsdbool( line_exists( value_pairs[ name = 'A' ] ) ).
IF line_exists( value_pairs[ name = 'A' ] ).
" READ TABLE value_pairs TRANSPORTING NO FIELDS WITH KEY name = 'A'.
" DATA(exists) = xsdbool( sy-subrc = 0 ).
```

*"Many of the detailed rules below are just specific reiterations of this general advice."*

Other named old→new pairs scattered through the guide:
| Prefer | Instead of |
|---|---|
| `NEW /clean/x( )` | `CREATE OBJECT x EXPORTING ...` (exception: dynamic types → `CREATE OBJECT ... TYPE (dynamic_type)`) |
| `RAISE EXCEPTION NEW cx_x( previous = e )` | `RAISE EXCEPTION TYPE cx_x EXPORTING previous = e` (but keep `TYPE` when you make massive use of the `MESSAGE` addition) |
| `xsdbool( … )` | `IF…THEN…ELSE` assignment; also better than `boolc`/`boolx` (they *"produce different types and add an unnecessary implicit type conversion"*); `COND abap_bool( WHEN … THEN abap_true )` is the accepted secondary form |
| class-based exceptions (`TRY … CATCH cx_…`) | `get_component_types( EXCEPTIONS has_deep_components = 1 OTHERS = 2 )` — *"The outdated non-class-based exceptions have the same features as return codes and shouldn't be used anymore."* |
| `@`-escaped host variables in ABAP SQL | unescaped host variables (the guide's flagship "obsolete element" example) |
| `INSERT … INTO TABLE` | `APPEND … TO` (see Tables) |
| `line_exists( t[ k = 'A' ] )` | `READ TABLE … TRANSPORTING NO FIELDS` + `sy-subrc` |
| `result = dref->*` | `ASSIGN dref->* TO <fs>` + `result = <fs>` |
| functional method call `obj->meth( a = 1 )` | `CALL METHOD obj->meth EXPORTING a = 1` (procedural style only when dynamic typing forbids functional) |
| pragma `##NEEDED` | pseudo comment `"#EC NEEDED` |
| `IF … CONTINUE` in loops | `CHECK` inside a loop |
| ABAP `ENUM` (>=7.51) | constants interfaces |
| `\|text { var }\|` | `` ` `` … `&&` concatenation |
| `RAISE SHORTDUMP TYPE cx_…` (>=7.53) | `MESSAGE x666(general)` |

**"Avoid obsolete language elements"** — *"When upgrading your ABAP version, make sure to check for obsolete language elements and refrain from using them."* Reasons given: newer alternatives improve readability, *"reduce design conflicts with modern programming paradigms"*; *"While continuing to work, obsolete elements may stop benefitting from optimizations in terms of processing speed and memory consumption"*; and onboarding — young ABAPers *"may no longer be familiar with the outdated constructs because they are no longer taught in SAP's trainings."* The guide links the NetWeaver documentation's stable "obsolete language elements" list for 7.50–7.57 rather than enumerating elements itself.

**"Prefer object orientation to procedural programming."** Classes/interfaces are better segmented, refactorable, testable. Where you must ship a procedural object (function for an RFC, program for a transaction), it *"should do little more than call a corresponding class that provides the actual feature"*:

```ABAP
FUNCTION check_business_partner [...].
  DATA(validator) = NEW /clean/biz_partner_validator( ).
  result = validator->validate( business_partners ).
ENDFUNCTION.
```

**"Use design patterns wisely"** — *"Where they are appropriate and provide noticeable benefit. Don't apply design patterns everywhere just for the sake of it."*

**Not in the guide** (do not invent these as Clean ABAP rules): `MOVE-CORRESPONDING` vs `CORRESPONDING #( )` — the word `CORRESPONDING` never appears as a rule. `COLLECT` — never mentioned. `APPEND INITIAL LINE` — never mentioned (the closest is the `VALUE #( FOR … )` vs `LOOP`/`INSERT` pair above). `DESCRIBE TABLE … LINES` vs `lines( )` — no such rule; `lines( )` appears only in "avoid obscuring built-in functions" and "assert content, not quantity". A "CASE vs COND" rule does not exist; `COND` appears only as the secondary alternative to `xsdbool`, and `SWITCH` never appears. `REDUCE` never appears.

---

## 3. Constants & literals

**"Use constants instead of magic numbers."**

```ABAP
IF abap_type = cl_abap_typedescr=>typekind_date.
" anti-pattern
IF abap_type = 'D'.
```

**"Prefer ENUM to constants interfaces."** Native `ENUM` from 7.51:

```ABAP
CLASS /clean/message_severity DEFINITION PUBLIC ABSTRACT FINAL.
  PUBLIC SECTION.
    TYPES: BEGIN OF ENUM type,
             warning,
             error,
           END OF ENUM type.
ENDCLASS.
```

instead of *"mixing unrelated things or misleading people to the conclusion that constants collections could be 'implemented'"*:

```ABAP
" anti-pattern
INTERFACE /dirty/common_constants.
  CONSTANTS:
    warning      TYPE symsgty VALUE 'W',
    transitional TYPE i       VALUE 1,
    error        TYPE symsgty VALUE 'E',
    persisted    TYPE i       VALUE 2.
ENDINTERFACE.
```

**"If you don't use ENUM or enumeration patterns, group your constants"** with `BEGIN OF … END OF` blocks (`message_severity`, `message_lifespan`), which *"also allows you group-wise access, for example for input validation"* via `ASSIGN message_severity-(sy-index)`.

From the `Enumerations.md` sub-section (the guide's deeper enum guidance):
- *"Starting with release 7.51 native enumerated types are available and should be preferred where applicable."* Declare **one enumeration per class, without the `STRUCTURE` addition** (STRUCTURE widens the API surface and adds a redundant grouping level: `…=>severity-warning` repeats "severity").
- Legacy interop: `BEGIN OF ENUM type BASE TYPE symsgty, info VALUE 'I', undefined VALUE IS INITIAL, …` plus `CONV` at every boundary (legacy APIs, ABAP SQL).
- If `ENUM` isn't available, use the **constant pattern** (`CLASS … PUBLIC ABSTRACT FINAL` holding `CONSTANTS`) or the **object pattern** (`CREATE PRIVATE FINAL`, `CLASS-DATA … READ-ONLY` instances built in `class_constructor`, `DATA value … READ-ONLY`). The **interface pattern** is *"acceptable, but has some slight drawbacks"* — labeled *"inferior pattern"*. The **collection pattern** (grouped constants in one interface) — *"Think twice… it harbors the danger of degrading into a mess."*
- Guidelines: **one development object per enumeration** (so people can find it and stop re-creating constants); **prefer classes to interfaces** because classes let you add `is_valid`, `equals`, `contains`, `to_string`, `is_more_severe_than`; **try to enforce type safety**.

**String literals:** see §6.

---

## 4. Variables

**"Prefer inline to up-front declarations."** *"If you follow these guidelines, your methods will become so short (3-5 statements) that declaring variables inline at first occurrence will look more natural."*

```ABAP
METHOD do_something.
  DATA(name) = 'something'.
  DATA(reader) = /clean/reader=>get_instance_for( name ).
  result = reader->read_it( ).
ENDMETHOD.

" anti-pattern
METHOD do_something.
  DATA:
    name   TYPE seoclsname,
    reader TYPE REF TO /dirty/reader.
  name = 'something'.
  reader = /dirty/reader=>get_instance_for( name ).
  result = reader->read_it( ).
ENDMETHOD.
```

**"Do not use variables outside of the statement block they are declared in."** A variable declared inside `IF`/`LOOP` survives the block, *"This is confusing for readers"*. If it's needed outside, declare it beforehand.

```ABAP
" anti-pattern
IF has_entries = abap_true.
  DATA(value) = 1.
ELSE.
  value = 2.
ENDIF.

" good
DATA value TYPE i.
IF has_entries = abap_true.
  value = 1.
ELSE.
  value = 2.
ENDIF.
```

**"Do not chain up-front declarations."** One `DATA` statement per variable. *"Chaining suggests the defined variables are related on a logical level"*, and it *"needlessly complicates reformatting and refactoring because each line looks different and changing them requires meddling with colons, dots, and commas."* Concession: *"If chaining of data declaration is used, then use one chain for each group of variables belonging together."* (Note the tension with **"Optimize for reading, not for writing"** in Formatting, which shows a chained `DATA: a TYPE b, c TYPE d, e TYPE f.` as the good form of a chained declaration — that example is about comma placement, not about whether to chain.)

**"Do not use field symbols for dynamic data access."** *"Starting in ABAP Platform 2021, there are almost no places left where using a field symbol is necessary"* for generically typed variables or dynamic component access.

```ABAP
" anti-pattern
ASSIGN dref->* TO <fs>.
result = <fs>.
" good
result = dref->*.
```

**"Choose the right targets for your loops."** Three targets, three intents:
- **Field symbols** (`LOOP AT table ASSIGNING FIELD-SYMBOL(<line>)`) — *"when you want to read or manipulate the data being iterated over."*
- **Data references** (`LOOP AT table REFERENCE INTO DATA(line)`) — *"when you need to access these references outside of the current loop"*, e.g. pass into reference parameters or keep them after the loop.
- **Data objects** (`LOOP AT table INTO DATA(line)`) — when you need a copy, or the line type is already a reference.

References can also read/manipulate, so almost all field symbols can be replaced by references; but references add dereferencing (`line->*`) and *"data access via field symbols is slightly faster."* The guide names **two consistent styles**: reference-based if the context is mostly objects/references and small loop costs don't matter; field-symbol-based if the context manipulates plain data heavily or loop performance matters.

---

## 5. Tables

**"Use the right table type"** (the guide calls these *"only rough guidelines"*):
- `HASHED` — **large** tables, **filled in a single step**, **never modified**, **read often by their key**. *"Each change to the table's content requires expensive recalculation of the hash."*
- `SORTED` — **large** tables that must be **sorted at all times**, are **filled bit by bit** or **need to be modified**, and **read often by one or more full or partial keys** or processed in a certain order. *"Sorted tables demonstrate their value only for large numbers of read accesses."*
- `STANDARD` — **small** tables *"where indexing produces more overhead than benefit"*, and **"arrays"** where you don't care about order or want exactly append order; also when mixed access is needed (indexed plus sorted via `SORT` + `BINARY SEARCH`).

**"Avoid DEFAULT KEY."**

```ABAP
" anti-pattern
DATA itab TYPE STANDARD TABLE OF row_type WITH DEFAULT KEY.
" good
DATA itab2 TYPE STANDARD TABLE OF row_type WITH NON-UNIQUE KEY comp1 comp2.
DATA itab1 TYPE STANDARD TABLE OF row_type WITH EMPTY KEY.
```

*"Default keys are often only added to get the newer functional statements working. The keys themselves in fact are usually superfluous and waste resources for nothing. They can even lead to obscure mistakes because they ignore numeric data types."* `SORT` and `DELETE ADJACENT` without an explicit field list fall back to the primary key — with `DEFAULT KEY` that yields *"very unexpected results"*, especially with numeric key components combined with `READ TABLE … BINARY`. **Caution given:** `SORT` on an `EMPTY KEY` table without explicit sort fields *"will not sort at all"* (syntax warnings when emptiness is statically determinable).

**"Prefer INSERT INTO TABLE to APPEND TO."** `INSERT VALUE #( ... ) INTO TABLE itab.` — *"`INSERT INTO TABLE` works with all table and key types, thus making it easier for you to refactor the table's type and key definitions if your performance requirements change. Use `APPEND TO` only if you use a `STANDARD` table in an array-like fashion, if you want to stress that the added entry shall be the last row."*

**"Prefer LINE_EXISTS to READ TABLE or LOOP AT."**

```ABAP
IF line_exists( my_table[ key = 'A' ] ).

" anti-patterns
READ TABLE my_table TRANSPORTING NO FIELDS WITH KEY key = 'A'.
IF sy-subrc = 0.

LOOP AT my_table REFERENCE INTO DATA(line) WHERE key = 'A'.
  line_exists = abap_true.
  EXIT.
ENDLOOP.
```

**"Prefer READ TABLE to LOOP AT."** `READ TABLE my_table REFERENCE INTO DATA(line) WITH KEY key = 'A'.` beats a `LOOP … WHERE … EXIT` and beats a `LOOP` with an inner `IF … EXIT`.

**"Prefer LOOP AT WHERE to nested IF."** `LOOP AT my_table REFERENCE INTO DATA(line) WHERE key = 'A'.` rather than looping everything and filtering with an inner `IF`.

**"Avoid unnecessary table reads."** *"In case you expect a row to be there, read once and react to the exception"*:

```ABAP
TRY.
    DATA(row) = my_table[ key = input ].
  CATCH cx_sy_itab_line_not_found.
    RAISE EXCEPTION NEW /clean/my_data_not_found( ).
ENDTRY.

" anti-pattern — double read litters and slows the main control flow
IF NOT line_exists( my_table[ key = input ] ).
  RAISE EXCEPTION NEW /clean/my_data_not_found( ).
ENDIF.
DATA(row) = my_table[ key = input ].
```

Table-expression forms from the Language section: `t[ name = 'A' ]` when the row must exist; `VALUE #( t[ name = 'A' ] OPTIONAL )` when it may be missing.

**Nested loops:** the guide has **no rule named "avoid nested loops"**. The nesting rules it has are about `IF` nesting ("Keep the nesting depth low") and about replacing inner filtering `IF`s with `LOOP AT … WHERE`. Don't attribute an anti-nested-loop rule to Clean ABAP.

---

## 6. Strings

**"Use ` to define literals."**

```ABAP
CONSTANTS some_constant TYPE string VALUE `ABC`.
DATA(some_string) = `ABC`.  " --> TYPE string
```

*"Refrain from using `'`, as it adds a superfluous type conversion and confuses the reader whether he's dealing with a `CHAR` or `STRING`"*. And: *"`|` is generally okay, but cannot be used for `CONSTANTS` and adds needless overhead when specifying a fixed value"* — so `DATA(some_string) = |ABC|.` is an anti-pattern.

**"Use | to assemble text."**

```ABAP
DATA(message) = |Received HTTP code { status_code } with message { text }|.

" anti-pattern
DATA(message) = `Received an unexpected HTTP ` && status_code && ` with message ` && text.
```

*"String templates highlight better what's literal and what's variable, especially if you embed multiple variables in a text."*

---

## 7. Booleans

**"Use Booleans wisely."** *"Generally, Booleans are a bad choice to distinguish types of things because you will nearly always encounter cases that are not exclusively one or the other."*

```ABAP
" anti-pattern
is_archived = abap_true.
" until a change of viewpoint suggests an enumeration
archiving_status = /clean/archivation_status=>archiving_in_process.
```

The illustrating smell: `document->is_archived( ) = abap_true AND document->is_partially_archived( ) = abap_true`.

**"Use ABAP_BOOL for Booleans."** `DATA has_entries TYPE abap_bool.` Don't use generic `char1` (*"technically compatible it obscures the fact that we're dealing with a Boolean"*). Avoid other Boolean types — *"`boolean` supports a third value 'undefined' that results in subtle programming errors."* For DDIC needs (e.g. DynPro fields) `abap_bool` can't be used (it lives in type pool `abap`, not the dictionary) → use `abap_boolean`; create your own data element if you need a custom description.

**"Use ABAP_TRUE and ABAP_FALSE for comparisons."**

```ABAP
has_entries = abap_true.
IF has_entries = abap_false.

" anti-patterns
has_entries = 'X'.
IF has_entries = space.
IF has_entries IS NOT INITIAL.   " forces readers to recollect abap_bool's default
```

**"Use XSDBOOL to set Boolean variables."**

```ABAP
DATA(has_entries) = xsdbool( line IS NOT INITIAL ).

" anti-pattern
IF line IS INITIAL.
  has_entries = abap_false.
ELSE.
  has_entries = abap_true.
ENDIF.
```

*"`xsdbool` is the best method for our purpose, as it directly produces a `char1`, which fits our boolean type `abap_bool` best. The equivalent functions `boolc` and `boolx` produce different types and add an unnecessary implicit type conversion."* The guide concedes *"the name `xsdbool` is unlucky and misleading"*. Secondary alternative: `COND abap_bool( WHEN line IS NOT INITIAL THEN abap_true )` — intuitive but longer and requires knowing the implicit `abap_false` default.

**Boolean parameters as a code smell:** see §12 ("Split method instead of Boolean input parameter").

---

## 8. Conditions

**"Try to make conditions positive."** `IF has_entries = abap_true.` over `IF has_no_entries = abap_false.` — but *"The 'try' in the section title means you shouldn't force this up to the point where you end up with something like empty IF branches."*

**"Prefer IS NOT to NOT IS."** *"Negation is logically equivalent but requires a 'mental turnaround' that makes it harder to understand."*

```ABAP
IF variable IS NOT INITIAL.
IF variable NP 'TODO*'.
IF variable <> 42.

" anti-patterns
IF NOT variable IS INITIAL.
IF NOT variable CP 'TODO*'.
IF NOT variable = 42.
```

**"Consider using predicative method calls for boolean methods."** `IF [ NOT ] condition_is_fulfilled( ).` over `IF condition_is_fulfilled( ) = abap_true / abap_false.` Important caveat: the predicative call is shorthand for `… IS NOT INITIAL`, *"This is why the short form should only be used for methods returning types where the non-initial value has the meaning of 'true' and the initial value has the meaning of 'false'."*

**"Consider decomposing complex conditions"** into named booleans:

```ABAP
DATA(example_provided) = xsdbool( example_a IS NOT INITIAL OR
                                  example_b IS NOT INITIAL ).
DATA(one_example_fits) = xsdbool( applies( example_a ) = abap_true OR
                                  applies( example_b ) = abap_true OR
                                  fits( example_b ) = abap_true ).
IF example_provided = abap_true AND
   one_example_fits = abap_true.
```

**"Consider extracting complex conditions"** to methods — *"It's nearly always a good idea"*:

```ABAP
IF is_provided( example ).

METHOD is_provided.
  DATA(is_filled) = xsdbool( example IS NOT INITIAL ).
  DATA(is_working) = xsdbool( applies( example ) = abap_true OR
                              fits( example ) = abap_true ).
  result = xsdbool( is_filled = abap_true AND
                    is_working = abap_true ).
ENDMETHOD.
```

**Comparison order** (e.g. "put the variable left, the constant right", Yoda conditions): **not a rule in this guide.**

---

## 9. Ifs

**"No empty IF branches."**

```ABAP
IF has_entries = abap_false.
  " do some magic
ENDIF.

" anti-pattern
IF has_entries = abap_true.
ELSE.
  " do some magic
ENDIF.
```

**"Prefer CASE to ELSE IF for multiple alternative conditions."**

```ABAP
CASE type.
  WHEN type-some_type.
    " ...
  WHEN type-some_other_type.
    " ...
  WHEN OTHERS.
    RAISE EXCEPTION NEW /clean/unknown_type_failure( ).
ENDCASE.
```

*"`CASE` makes it easy to see a set of alternatives that exclude each other. It can be faster than a series of `IF`s because it can translate to a different microprocessor command… You can introduce new cases quickly, without having to repeat the discerning variable over and over again. The statement even prevents some errors that can occur when accidentally nesting the `IF`-`ELSEIF`s."*

**"Keep the nesting depth low."** *"Nested `IF`s get hard to understand very quickly and require an exponential number of test cases for complete coverage. Decision trees can usually be taken apart by forming sub-methods and introducing boolean helper variables."* Merge where possible: `IF <this> AND <that>.` rather than nesting the two.

---

## 10. Regular expressions

**"Prefer simpler methods to regular expressions."**

```ABAP
IF input IS NOT INITIAL.
" IF matches( val = input  regex = '.+' ).

WHILE contains( val = input  sub = 'abc' ).
" WHILE contains( val = input  regex = 'abc' ).
```

*"Regular expressions become hard to understand very quickly… also usually consume more memory and processing time because they need to be parsed into an expression tree and compiled at runtime into an executable matcher."*

**"Prefer basis checks to regular expressions."** Use the platform's own check instead of reinventing it:

```ABAP
CALL FUNCTION 'SEO_CLIF_CHECK_NAME'
  EXPORTING cls_name = class_name
  EXCEPTIONS ...

" anti-pattern
DATA(is_valid) = matches( val     = class_name
                          pattern = '[A-Z][A-Z0-9_]{0,29}' ).
```

*"There seems to be a natural tendency to turn blind to the Don't-Repeat-Yourself (DRY) principle when there are regular expressions around."*

**"Consider assembling complex regular expressions"** from named pieces:

```ABAP
CONSTANTS class_name TYPE string VALUE `CL\_.*`.
CONSTANTS interface_name TYPE string VALUE `IF\_.*`.
DATA(object_name) = |{ class_name }\|{ interface_name }|.
```

**PCRE vs POSIX:** **not mentioned anywhere in the guide.** There is no PCRE guidance to cite.

---

## 11. Classes

**"Prefer objects to static classes."** *"Static classes give up all advantages gained by object orientation in the first place. They especially make it nearly impossible to replace dependencies with test doubles in unit tests. If you think about whether to make a class or method static, the answer will nearly always be: no."* One accepted exception: **plain type utils classes** — *"not only completely stateless, but so basic that they look like ABAP statements or built-in functions"*, whose consumers *"actually don't want to mock them"*:

```ABAP
CLASS /clean/string_utils DEFINITION [...].
  CLASS-METHODS trim
   IMPORTING string        TYPE string
   RETURNING VALUE(result) TYPE string.
ENDCLASS.
```

**"Prefer composition to inheritance."** *"Avoid building hierarchies of classes with inheritance. Instead, favor composition."* Reasons: Liskov substitution is hard to respect; hierarchies require digesting guiding principles; *"Inheritance reduces reuse because methods tend to be made available only to sub-classes"*; refactoring ripples through the tree. *"Composition may produce more classes, but has otherwise no further disadvantages."* Not absolute — Composite is a good application — *"If in doubt, composition generally is the safer choice."*

**"Don't mix stateful and stateless in the same class."** Stateless: methods take input, produce output, *"without any side effects"* (example: `/clean/xml_converter` with a single `convert` method, `FINAL CREATE PUBLIC`). Stateful: *"we manipulate the internal state of objects through their methods, meaning it is full of side effects"* (example: `/clean/log` with `add_message` and private `messages`). *"Both paradigms are okay… However, mixing them in the same object produces code that is hard to understand and sure to fail with obscure carry-over errors and synchronicity problems. Don't do that."*

**"Global by default, local only where appropriate."** Local classes are suited for (1) very specific private data structures (e.g. an iterator), (2) extracting a complex private algorithm, (3) enabling mocking (e.g. extracting all DB access to a local class replaceable by a test double). Otherwise *"Local classes hinder reuse… people will usually fail to even find them, leading to undesired code duplication."* ABAP locks on include level, so parallel work is blocked. Reconsider if the include spans dozens of classes and thousands of lines, if you think of global classes as "packages", if globals *"degenerate into empty hulls"*, if duplicates appear across local includes, if developers lock each other out, or if estimates go sky-high.

**"FINAL if not designed for inheritance."** *"Make classes that are not explicitly designed for inheritance `FINAL`."* Enabling inheritance *"requires you to think about things like `PROTECTED` vs. `PRIVATE` and the Liskov substitution principle, and freezes a lot of design internals."* Notable exception: *"Unclean classes that don't implement interfaces should be left non-`FINAL` to allow consumers mocking them in their unit tests."*

**"Members PRIVATE by default, PROTECTED only if needed."** *"Make them only `PROTECTED` if you want to enable sub-classes that override them. Internals of classes should be made available to others only on a need-to-know basis. This includes not only outside callers but also sub-classes."*

**"Consider using immutable instead of getter."** For objects that never change after construction, public `READ-ONLY` attributes beat getters:

```ABAP
CLASS /clean/some_data_container DEFINITION.
  PUBLIC SECTION.
    METHODS constructor IMPORTING a TYPE i
                                  b TYPE c
                                  c TYPE d.
    DATA a TYPE i READ-ONLY.
    DATA b TYPE c READ-ONLY.
    DATA c TYPE d READ-ONLY.
ENDCLASS.
```

**Caution given:** *"For objects which do have changing values, do not use public read-only attributes. Otherwise this attributes always have to be kept up to date, regardless if their value is needed by any other code or not."*

**"Use READ-ONLY sparingly."** Only available in the `PUBLIC SECTION`, *"reducing its applicability drastically"*, and it *"works subtly different from what people might expect… READ-ONLY data can still be modified freely from any method within the class itself, its friends, and its sub-classes."*

**"Prefer NEW to CREATE OBJECT."**

```ABAP
DATA object TYPE REF TO /clean/some_number_range.
object = NEW #( '/CLEAN/CXTGEN' )
DATA(object) = NEW /clean/some_number_range( '/CLEAN/CXTGEN' ).
DATA(object) = CAST /clean/number_range( NEW /clean/some_number_range( '/CLEAN/CXTGEN' ) ).
```

Exception: dynamic types still need `CREATE OBJECT number_range TYPE (dynamic_type) EXPORTING …`.

**"If your global class is CREATE PRIVATE, leave the CONSTRUCTOR public."**

```ABAP
CLASS /clean/some_api DEFINITION PUBLIC FINAL CREATE PRIVATE.
  PUBLIC SECTION.
    METHODS constructor.
```

*"We agree that this contradicts itself. However, according to … the ABAP Help, specifying the `CONSTRUCTOR` in the `PUBLIC SECTION` is required to guarantee correct compilation and syntax validation. This applies only to global classes. In local classes, make the constructor private, as it should be."*

**"Prefer multiple static creation methods to optional parameters."** *"ABAP does not support overloading. Use name variations and not optional parameters."*

```ABAP
CLASS-METHODS describe_by_data IMPORTING data TYPE any [...]
CLASS-METHODS describe_by_name IMPORTING name TYPE any [...]
CLASS-METHODS describe_by_object_ref IMPORTING object_ref TYPE REF TO object [...]

" anti-pattern
METHODS constructor
  IMPORTING data TYPE any OPTIONAL
            name TYPE any OPTIONAL
            object_ref TYPE REF TO object OPTIONAL
            data_ref TYPE REF TO data OPTIONAL
```

*"Consider resolving complex constructions to a multi-step construction with the Builder design pattern."*

**"Make singletons only where multiple instances don't make sense."**

```ABAP
METHOD new.
  IF singleton IS NOT BOUND.
    singleton = NEW /clean/my_class( ).
  ENDIF.
  result = singleton.
ENDMETHOD.
```

*"Do not use the singleton pattern out of habit or because some performance rule tells you so. It is the most overused and wrongly applied pattern and produces unexpected cross-effects and needlessly complicates testing. If there are no design-driven reasons for a unitary object, leave that decision to the consumer."*

**Interfaces — the guide's position is the opposite of "don't create an interface for every class."** The rule is **"Public instance methods should be part of an interface"**: *"Public instance methods should always be part of an interface. This decouples dependencies and simplifies mocking them in unit tests."* Implementation reads `METHOD /clean/blog_post~publish.` *"In clean object orientation, having a method public without an interface does not make much sense - with few exceptions such as enumeration classes which will never have an alternative implementation and will never be mocked in test cases."* If your skill wants an "avoid interface bloat" rule, it does **not** come from Clean ABAP.

---

## 12. Methods

*"These rules apply to methods in classes and function modules."*

### Calls
- **"Don't call static methods through instance variables"** — `cl_my_class=>static_method( )`, not `lo_my_instance->static_method( )`. Within a *static* method you may call sibling statics unqualified; within an *instance* method, still qualify: `cl_my_class=>a_static_method( ).`
- **"Don't access types through instance variables"** — `TYPES blah TYPE lcl=>foo.`, never via an instance reference.
- **"Prefer functional to procedural calls"** — `modify->update( node = … key = … )` over `CALL METHOD modify->update EXPORTING …`. Procedural style only when dynamic typing forbids functional (`CALL METHOD modify->(method_name)`).
- **"Omit RECEIVING"** — `DATA(sum) = aggregate_values( values ).`
- **"Omit the optional keyword EXPORTING"**.
- **"Omit the parameter name in single parameter calls"** — `remove_duplicates( list )`. But *"There are cases, however, where the method name alone is not clear enough and repeating the parameter name may further understandability"*: `car->drive( speed = 50 ).`, `update( asynchronous = abap_true ).`
- **"Omit the self-reference me when calling an instance attribute or method"** — unless *"there is a scope conflict between a local variable or importing parameter and an instance attribute"*: `me->logger = logger.`

### Static vs instance
**"Prefer instance to static methods."** *"Methods should be instance members by default. Instance methods better reflect the 'object-hood' of the class. They can be mocked easier in unit tests… Methods should be static only in exceptional cases, such as static creation methods."*

### Parameter number — the guide's actual numbers
**"Aim for few IMPORTING parameters, at best less than three."** *"Too many input parameters let the complexity of a method explode because it needs to handle an exponential number of combinations. Many parameters are an indicator that the method may do more than one thing. You can reduce the number of parameters by combining them into meaningful sets with structures and objects."* (The anti-pattern shown is the 10-parameter `seo_class_copy`, mostly Boolean flags.)

**"Split methods instead of adding OPTIONAL parameters."**

```ABAP
METHODS do_one_thing IMPORTING what_i_need TYPE string.
METHODS do_another_thing IMPORTING something_else TYPE i.

" anti-pattern
METHODS do_one_or_the_other
  IMPORTING what_i_need    TYPE string OPTIONAL
            something_else TYPE i OPTIONAL.
```

*"Optional parameters confuse callers: Which ones are really required? Which combinations are valid? Which ones exclude each other?"*

**"Use PREFERRED PARAMETER sparingly"** — *"makes it hard to see which parameter is actually supplied."*

**"RETURN, EXPORT, or CHANGE exactly one parameter."** *"A good method does one thing, and that should be reflected by the method also returning exactly one thing. If the output parameters of your method do not form a logical entity, your method does more than one thing and you should split it."* Multiple related outputs → return a structure or object:

```ABAP
TYPES:
  BEGIN OF check_result,
    result      TYPE result_type,
    failed_keys TYPE /bobf/t_frw_key,
    messages    TYPE /bobf/t_frw_message,
  END OF check_result.

METHODS check_business_partners
  IMPORTING business_partners TYPE business_partners
  RETURNING VALUE(result)     TYPE check_result.
```

*"this allows people to use the functional call style, spares you having to think about `IS SUPPLIED` and saves people from accidentally forgetting to retrieve a vital `ERROR_OCCURRED` information."* Instead of multiple optional outputs, split along meaningful call patterns (`check` / `check_and_report`).

### Parameter types
**"Prefer RETURNING to EXPORTING."** *"`RETURNING` not only makes the call shorter, it also allows method chaining and prevents same-input-and-output errors."*

**"RETURNING large tables is usually okay."** *"we rarely encounter cases where handing over a large or deeply-nested table in a VALUE parameter really causes performance problems."* Only with *"actual proof (= a bad performance measurement)"* should you fall back to `EXPORTING`. The guide flags this as a deliberate deviation: *"This section contradicts the ABAP Programming Guidelines and Code Inspector checks."*

**"Use either RETURNING or EXPORTING or CHANGING, but not a combination."** *"Different sorts of output parameters is an indicator that the method does more than one thing."* Acceptable exception: builders that consume their input while building output (`CHANGING tokens` + `RETURNING tree`) — *"even those can be made clearer by objectifying the input"* (`IMPORTING tokens TYPE REF TO token_stack`).

**"Use CHANGING sparingly, where suited."** Reserved for *"cases where an existing local variable that is already filled is updated in only some places."* *"Do not force your callers to introduce unnecessary local variables only to supply your `CHANGING` parameter. Do not use `CHANGING` parameters to initially fill a previously empty variable."*

**"Split method instead of Boolean input parameter."** *"Boolean input parameters are often an indicator that a method does two things instead of one."*

```ABAP
" anti-pattern
METHODS update IMPORTING do_save TYPE abap_bool.
update( abap_true ).  " what does 'true' mean? synchronous? simulate? commit?

" good
update_without_saving( ).
update_and_save( ).
```

*"Common perception suggests that setters for Boolean variables are okay"*: `METHODS set_is_deleted IMPORTING new_value TYPE abap_bool.`

### Parameter names
**"Consider calling the RETURNING parameter RESULT."** *"Good method names are usually so good that the `RETURNING` parameter does not need a name of its own… Repeating a member name can even produce conflicts that need to be resolved by adding a superfluous `me->`"* (`name = me->name.`). *"In these cases, simply call the parameter `RESULT`, or something like `RV_RESULT` if you prefer Hungarian notation."* Do name it when it isn't obvious — *"for example in methods that return `me` for method chaining, or in methods that create something but don't return the created entity but only its key."*

### Parameter initialization
**"Clear or overwrite EXPORTING reference parameters"** — reference parameters may already be filled; `CLEAR result.` or overwrite in one statement. **"Take care if input and output could be the same"** — an early `CLEAR` would destroy the input when caller passes one variable for both. *"Consider redesigning such methods by replacing `EXPORTING` with `RETURNING`… If neither fits, resort to a late `CLEAR`."* **"Don't clear VALUE parameters"** — VALUE (and therefore all `RETURNING`) parameters are new, empty memory areas.

### Method body
**"Do one thing, do it well, do it only."** The checklist: few input parameters; no Boolean parameters; exactly one output parameter; small; descends one level of abstraction; throws only one type of exception; *"you cannot extract meaningful other methods"*; *"you cannot meaningfully group its statements into sections."*

**"Focus on the happy path or error handling, but not both."** Split validation out:

```ABAP
METHOD append_xs.
  validate( input ).
  DATA(remainder) = input.
  WHILE remainder > 0.
    result = result && `X`.
    remainder = remainder - 1.
  ENDWHILE.
ENDMETHOD.

METHOD validate.
  IF input = 0.
    RAISE EXCEPTION /dirty/sorry_cant_do( ).
  ELSEIF input < 0.
    RAISE EXCEPTION cx_sy_illegal_argument( ).
  ENDIF.
ENDMETHOD.
```

**"Descend one level of abstraction."** *"Statements in a method should be one level of abstraction below the method itself. Correspondingly, they should all be on the same level of abstraction."*

```ABAP
METHOD create_and_publish.
  post = create_post( user_input ).
  post->publish( ).
ENDMETHOD.

" anti-pattern — mixes low level (trim, to_upper) with high level (publish)
METHOD create_and_publish.
  post = NEW blog_post( ).
  DATA(user_name) = trim( to_upper( sy-uname ) ).
  post->set_author( user_name ).
  post->publish( ).
ENDMETHOD.
```

Heuristic offered: *"Let the method's author explain what the method does in few, short words, without looking at the code. The bullets (s)he numbers are the sub-methods the method should call."*

**"Keep methods small" — the guide's actual numbers: "Methods should have less than 20 statements, optimal around 3 to 5 statements."**

```ABAP
METHOD read_and_parse_version_filters.
  DATA(active_model_version) = read_random_version_under( model_guid ).
  DATA(filter_json) = read_model_version_filters( active_model_version-guid ).
  result = parse_model_version_filters( filter_json ).
ENDMETHOD.
```

Exception acknowledged: a long but focused `CASE` mapping is *"perfectly okay as long as the method remains focused on one thing"* — though *"it still makes sense to validate whether the verbose code hides a more suitable pattern"* (`result = VALUE #( spare_time_activities[ temperature = temperature ] OPTIONAL ).`). And the performance caveat: *"Cutting methods very small can have bad impact on performance because it increases the number of method calls."*

### Control flow
**"Fail fast."** Validate at the top, before building expensive objects. *"Later validations are harder to spot and understand and may have already wasted resources to get there."*

**"CHECK vs. RETURN."** *"There is no consensus on whether you should use `CHECK` or `RETURN` to exit a method if the input doesn't meet expectations."* `CHECK keys IS NOT INITIAL.` is shorter, but *"the statement's name doesn't reveal what happens if the condition fails, such that people will probably understand the long form better"* (`IF keys IS INITIAL. RETURN. ENDIF.`). Wrapping the whole body in a positive `IF` is *"considered to be an anti-pattern because it introduces unnecessary nesting depth."* And: *"consider whether returning nothing is really the appropriate behavior. Methods should provide a meaningful result, meaning either a filled return parameter, or an exception. Returning nothing is in many cases similar to returning `null`, which should be avoided."*

**"Avoid CHECK in other positions."** *"Do not use `CHECK` outside of the initialization section of a method. The statement behaves differently in different positions."* `CHECK` in a `LOOP` ends the current iteration — *"Prefer using an `IF` statement in combination with `CONTINUE` instead."*

**Method chaining:** mentioned only twice, both incidentally (RETURNING enables it; name the RETURNING parameter when returning `me` for chaining). There is **no prescriptive rule for or against fluent chaining.**

---

## 13. Error handling

**"Make messages easy to find."** For where-used from SE91:

```ABAP
MESSAGE e001(ad) INTO DATA(message).
MESSAGE e001(ad) INTO DATA(message) ##NEEDED.   " when 'message' isn't needed

" anti-pattern — unreachable code, tests a condition that can never be true
IF 1 = 2. MESSAGE e001(ad). ENDIF.
```

**"Prefer exceptions to return codes."** `RAISE EXCEPTION NEW cx_failed( ).` rather than `error_occurred = abap_true.` Four advantages given: signatures stay clean (`RETURNING` the result *and* throwing); the caller needn't react immediately and can write the happy path with `CATCH` at the end or outside; exceptions carry detail in attributes and methods; *"The environment reminds the caller with syntax errors to handle exceptions. Return codes can be accidentally ignored without anybody noticing."*

**"Don't let failures slip through."** When you must consume return codes (older FMs), check them and convert: `IF response-type = 'E'. RAISE EXCEPTION NEW /clean/some_error( ). ENDIF.`

**"Exceptions are for errors, not for regular cases."**

```ABAP
" anti-pattern
METHODS entry_exists_in_db IMPORTING key TYPE char10 RAISING cx_not_found_exception.
" good
METHODS entry_exists_in_db IMPORTING key TYPE char10 RETURNING VALUE(result) TYPE abap_bool.
" good — a real error situation
METHODS assert_user_input_is_valid IMPORTING user_input TYPE string RAISING cx_bad_user_input.
```

*"Misusing exceptions misguides the reader into thinking something went wrong… Exceptions are also much slower than regular code."*

**"Use class-based exceptions"** — non-class-based `EXCEPTIONS has_deep_components = 1 OTHERS = 2` *"have the same features as return codes and shouldn't be used anymore."*

**"Use own super classes."**

```ABAP
CLASS cx_fra_static_check DEFINITION ABSTRACT INHERITING FROM cx_static_check.
CLASS cx_fra_no_check DEFINITION ABSTRACT INHERITING FROM cx_no_check.
```

*"Allows you to `CATCH` all your exceptions. Enables you to add common functionality to all exceptions… `ABSTRACT` prevents people from accidentally using these non-descriptive errors directly."*

**"Throw one type of exception."** *"In the vast majority of cases, throwing multiple types of exceptions has no use. The caller usually is neither interested nor able to distinguish the error situations… and if this is the case, why distinguish them in the first place?"* Anti-pattern: `RAISING cx_abap_generation cx_hdbr_access_error cx_model_read_error.`

**"Use sub-classes to enable callers to distinguish error situations."** One declared type, optional discrimination via sub-classes:

```ABAP
CLASS cx_bad_generation_variable DEFINITION INHERITING FROM cx_generation_error.
CLASS cx_bad_code_composer_template DEFINITION INHERITING FROM cx_generation_error.
METHODS generate RAISING cx_generation_error.

TRY.
    generator->generate( ).
  CATCH cx_bad_generation_variable.
    log_failure( ).
  CATCH cx_bad_code_composer_template INTO DATA(bad_template_exception).
    show_error_to_user( bad_template_exception ).
  CATCH cx_generation_error INTO DATA(other_exception).
    RAISE EXCEPTION NEW cx_application_error( previous = other_exception ).
ENDTRY.
```

*"If there are many different error situations, use error codes instead"* — a `BEGIN OF error_code_enum` constants group plus `DATA error_code` on the exception class, dispatched with `CASE exception->error_code.`

**Exception category guidance:**
- **`CX_STATIC_CHECK` for manageable exceptions** — *"If an exception can be expected to occur and be reasonably handled by the receiver… failing user input validation, missing resource for which there are fallbacks."* *"This exception type must be given in method signatures and must be caught or forwarded to avoid syntax errors. It is therefore plain to see for the consumer."* The guide flags: *"This is in sync with the ABAP Programming Guidelines but contradicts Robert C. Martin's Clean Code, which recommends to prefer unchecked exceptions."*
- **`CX_NO_CHECK` for usually unrecoverable situations** — *"failure to read a must-have resource, failure to resolve the requested dependency."* *"`CX_NO_CHECK` cannot be declared in method signatures, such that its occurrence will come as a bad surprise to the consumer. In the case of unrecoverable situations, this is okay."* But a caller may still legitimately want to catch it (the "test report instantiating everything" example).
- **`CX_DYNAMIC_CHECK` — consider it for avoidable exceptions.** *"Use cases for `CX_DYNAMIC_CHECK` are rare, and in general we recommend to resort to the other exception types."* Consider it as a replacement for `CX_STATIC_CHECK` *"if the caller has full, conscious control over whether an exception can occur"* — the `cl_abap_math=>get_db_length_decs` example, where the dynamic exception *"would enable the caller to omit the unnecessary `CATCH` clause."*
- **"Dump for totally unrecoverable situations"** — *"failure to acquire memory, failed index reads on a table that must be filled"*, or anything *"that clearly indicates a programming error"*: `RAISE SHORTDUMP TYPE cx_sy_create_object_error.` (>= 7.53) / `MESSAGE x666(general).` (< 7.53). *"This behavior will prevent any kind of consumer from doing anything useful afterwards. Use this only if you are sure about that."*

**"Prefer RAISE EXCEPTION NEW to RAISE EXCEPTION TYPE"** (>= 7.52) — *"However, if you make massive use of the addition `MESSAGE`, you may want to stick with the `TYPE` variant."*

**"Wrap foreign exceptions instead of letting them invade your code."**

```ABAP
METHODS generate RAISING cx_generation_failure.

METHOD generate.
  TRY.
      generator->generate( ).
    CATCH cx_amdp_generation_failure INTO DATA(exception).
      RAISE EXCEPTION NEW cx_generation_failure( previous = exception ).
  ENDTRY.
ENDMETHOD.
```

*"The Law of Demeter recommends de-coupling things. Forwarding exceptions from other components violates this principle."*

**Not in the guide:** there is **no rule about empty `CATCH` blocks**, **no "don't catch what you can't handle"** rule, and **no `CLEANUP` guidance** (the word never appears). Note that the "Use class-based exceptions" good example itself shows an empty `CATCH`. The nearest testing-side rule is "Forward unexpected exceptions instead of catching and failing" (§16).

---

## 14. Comments

- **"Express yourself in code, not in comments."** The illustrative refactoring turns a heavily commented `fix_day_overflow` into `correct_day_to_last_in_month` / `is_invalid` / `reduce_day_by_one`. *"Clean Code does not forbid you to comment your code - it encourages you to exploit better means, and resort to comments only if that fails."* (With an honest performance footnote: the clean variant measured 2.13× slower, 9.6 vs 4.5 microseconds.)
- **"Comments are no excuse for bad names."** `DATA(input_has_entries) = has_entries( input ).` instead of `" checks whether the table input contains entries` + `DATA(result) = check_table( input ).`
- **"Use methods instead of comments to segment your code."** `DATA(statement) = build_statement( ). DATA(data) = execute_statement( statement ).` instead of banner comments — *"it also avoids carry-over errors when temporary variables aren't properly cleared between the sections."*
- **"Write comments to explain the why, not the what."** Good: `" can't fail, existence of >= 1 row asserted above`. Bad: `" select alert root from database by key`.
- **"Design goes into the design documents, not the code."** *"Nobody reads that - seriously. If people need to read a textbook to be able to use your code, this may be an indicator that your code has severe design issues."* Link the design document instead.
- **"Comment with ", not with *."** Quote comments indent with their statements; asterisked comments *"tend to indent to weird places."*
- **"Put comments before the statement they relate to"** — not after it, and not trailing (*"less invasive than"* trailing, but before is clearest).
- **"Delete code instead of commenting it."** *"When you find something like this, delete it. The code is obviously not needed because your application works and all tests are green. Deleted code can be reproduced from the version history."* If you must keep it, copy to a file or `$TMP`/`HOME` object.
- **"Don't do manual versioning."** No `* ticket 800034775 ABC ++ Start/End` markers. *"versioning is already done by source code management. Transport order texts are much more suitable for describing why something was adapted."*
- **"Use FIXME, TODO, and XXX and add your ID."** `" XXX FH delete this method - it does nothing`. *"`FIXME` points to errors that are too small or too much in-the-making for internal incidents. `TODO`s are places where you want to complete something in the near(!) future. `XXX` marks code that works but could be better."* Always add your nick/initials/user.
- **"Don't add method signature and end-of comments."** No `* <SIGNATURE>---…` blocks — modern IDEs show signatures (SE24/SE80 *Signature* button; ADT F2 / *ABAP Element Info*). Likewise no `ENDIF. " IF has_entries = abap_false` / `ENDMETHOD. " get_kpi_calc`.
- **"Don't duplicate message texts as comments."** *"Messages change independently from your code, and nobody will remember adjusting the comment."* If you want it explicit, extract the message into its own method (`create_alert_not_found_message`).
- **"ABAP Doc only for public APIs."** *"Write ABAP Doc to document public APIs, meaning APIs that are intended for developers in other teams or applications. Don't write ABAP Doc for internal stuff. ABAP Doc suffers from the same weaknesses as all comments, that is, it outdates quickly and then becomes misleading… you should employ it only where it makes sense, not enforce writing ABAP Doc for each and everything."*
- **"Prefer pragmas to pseudo comments."** *"Pseudo comments have mostly become obsolete and have been replaced by pragmas."* `##NEEDED` over `"#EC NEEDED`. Find the mapping via program `ABAP_SLIN_PRAGMAS` or table `SLIN_DESC`.

---

## 15. Formatting

Preamble: the suggestions are *"optimized for reading, not for writing"*; the ABAP Formatter doesn't cover them, so some create manual rework — *"if you want to avoid this, consider dropping rules like Align assignments to the same object."*

- **"Be consistent."** Same formatting across the project; *"If you edit foreign code, adhere to that project's formatting style instead of insisting on your personal style."*
- **"Optimize for reading, not for writing."** `DATA: a TYPE b, c TYPE d, e TYPE f.` over leading-comma hacks (`,c TYPE d`).
- **"Use the ABAP Formatter before activating."** Shift+F1 in SE80/SE24/ADT. *"Note: ABAP Formatter is known as Pretty Printer in SAP GUI."* On large unformatted legacy code, format only selected lines to avoid huge change lists; consider formatting the whole object in a separate Transport Request or Note.
- **"Use your team's ABAP Formatter settings."** *"Set _Indent_ and _Convert Uppercase/Lowercase_ > _Uppercase Keyword_ as agreed in your team."* **The guide deliberately gives no keyword-case ruling** — *"[Upper vs. Lower Case] explains why we do not give clear guidance for the type case of keywords."* So: do not claim Clean ABAP mandates uppercase keywords. (The guide's own examples use uppercase keywords + lowercase identifiers.)
- **"No more than one statement per line."**
- **"Stick to a reasonable line length" — "Adhere to a maximum line length of 120 characters."** *"The 80 or even 72 characters limit originating in the old terminal devices is a little too restrictive. While 100 characters are often recommended and a viable choice, 120 characters seem to work a little better for ABAP, maybe because of the general verbosity of the language."*
- **"Condense your code."** `DATA(result) = calculate( items ).` not `DATA(result)        =      calculate(    items =   items )   .`
- **"Add a single blank line to separate things, but not more."** *"The urge to add separating blank lines may be an indicator that your method doesn't do one thing."*
- **"Don't obsess with separating blank lines."** No blank line after `METHOD` / before `ENDMETHOD` for two-statement bodies; never a blank line *inside* a statement (*"this can easily be misunderstood as a new statement when skimming"*). *"Blank lines actually only make sense if you have statements that span multiple lines."*
- **"Align assignments to the same object, but not to different ones."**

```ABAP
structure-type = 'A'.
structure-id   = '4711'.
" or even better
structure = VALUE #( type = 'A'
                     id   = '4711' ).
" but leave unrelated things ragged
customizing_reader = fra_cust_obj_model_reader=>s_get_instance( ).
hdb_access = fra_hdbr_access=>s_get_instance( ).
```

- **"Close brackets at line end."** `changed_fields = changed_fields ).` — never a dangling `)` on its own line.
- **"Keep single parameter calls on one line."**
- **"Keep parameters behind the call"** — `add_two_numbers( value_1 = 5` then aligned `value_2 = 6 ).`; break to the next line when lines get very long.
- **"If you break, indent parameters under the call"** (under the opening `(`, not at a fixed small indent). *"However, this is the best pattern if you want to avoid the formatting to be broken by a name length change."*
- **"Line-break multiple parameters"** — one per line. *"Yes, this wastes space. However, otherwise, it's hard to spot where one parameter ends and the next starts."*
- **"Align parameters"** — align the `=` column. *"Ragged margins make it hard to see where the parameter ends and its value begins."*
- **"Break the call to a new line if the line gets too long."**
- **"Indent and snap to tab"** — *"Indent parameter keywords by 2 spaces and parameters by 4 spaces"*; with no keywords, indent parameters by 4. *"Use the Tab key to indent. It's okay if this adds one more space than needed."*

```ABAP
DATA(sum) = add_two_numbers(
              EXPORTING
                value_1 = 5
                value_2 = 6
              CHANGING
                errors  = errors ).
```

- **"Indent in-line declarations like method calls"** — `VALUE`/`NEW` constructor arguments align like call parameters.
- **"Don't align type clauses."**

```ABAP
DATA name TYPE seoclsname.
DATA reader TYPE REF TO /clean/reader.

" anti-pattern
DATA name   TYPE seoclsname.
DATA reader TYPE REF TO /clean/reader.
```

*"A variable and its type belong together and should therefore be visually grouped in close proximity. Aligning the `TYPE` clauses draws attention away from that."*
- **"Don't chain assignments."** `var1 = var2 = var3.` is an anti-pattern — *"the inline declaration doesn't work in any position of a multiple assignment"*, and it looks like a comparison (`a = ( b == c )` in JavaScript).

---

## 16. Testing

### Principles
- **"Write testable code."** *"Write all code in a way that allows you to test it in an automatic fashion. If this requires refactoring your code, do it. Do that first, before you start adding other features."*
- **"Enable others to mock you"** — interfaces in all outward-facing places, helpful test doubles, dependency inversion so consumers can substitute config.
- **"Readability rules."** *"Make your test code even more readable than your production code… Keep your test code so simple and stupid that you will still understand it in a year from now."*
- **"Don't make copies or write test reports."** No `$TMP` playground copies; no manual test reports verified by eye — *"This is poor man's testing."*
- **"Test publics, not private internals."** Publics and interfaces are stable; internals change with every refactoring. *"An urgent need to test private or protected methods may be an early warning sign for several kinds of design flaws"* — buried concept wanting its own class; domain logic not separated from glue code (BOPF actions/determinations/validations, generated `*_DPC_EXT` classes); interfaces too complicated to mock.
- **"Don't obsess about coverage."** *"Code coverage is there to help you find code you forgot to test, not to meet some random KPI… Better leave things untested to make transparent that you cannot safely refactor them. You can have < 100% coverage and still have perfect tests."*

### Test classes
**"Call local test classes by their purpose"** — name by the *when* or the *given*:

```ABAP
CLASS ltc_<public method name> DEFINITION FOR TESTING ...
CLASS ltc_<common setup semantics> DEFINITION FOR TESTING ...

" anti-patterns
CLASS ltc_fra_online_detection_api DEFINITION FOR TESTING ... " We know that's the class under test - why repeat it?
CLASS ltc_test DEFINITION FOR TESTING ...                     " Of course it's a test, what else should it be?
```

(Note: the guide's own test examples do use `ltc_` / `lth_` prefixes, despite the general anti-prefix stance.)

**"Put tests in local classes."** Unit tests go in the **local test include of the class under test** — *"This ensures that people find these tests when refactoring the class and allows them to run all associated tests with a single key press."* Component/integration/system tests go in the local test include of a **separate global class**, *"Mark this global test class as `FOR TESTING` and `ABSTRACT` to avoid that it is accidentally referenced in production code."* Use **test relations** to document what's covered:

```abap
"! @testing recruting
"! @testing candidate
class hiring_test definition
  for testing risk level dangerous duration medium
  abstract.
  ...
endclass.
```

**"Put help methods in help classes."** Shared helpers in a help class, reached by inheritance (is-a) or delegation (has-a):

```abap
CLASS lth_unit_tests DEFINITION ABSTRACT.
  PROTECTED SECTION.
    CLASS-METHODS assert_activity_entity
      IMPORTING actual_activity_entity   TYPE REF TO zcl_activity_entity
                expected_activity_entity TYPE REF TO zcl_activity_entity.
ENDCLASS.

CLASS ltc_unit_tests DEFINITION INHERITING FROM lth_unit_tests FINAL FOR TESTING
  DURATION SHORT
  RISK LEVEL HARMLESS.
```

**RISK LEVEL / DURATION:** these appear **only inside examples** (`RISK LEVEL HARMLESS` + `DURATION SHORT` for a unit test class; `risk level dangerous duration medium` for an integration test class). The guide states **no prescriptive rule** about which level/duration to choose. Report it as convention-by-example, not as a rule.

**"How to execute test classes"** (ADT; `Cmd` on macOS): `Ctrl+Shift+F9` preview all tests incl. test relations · `F10` run all tests in a class · `F11` + coverage · `F12` + tests in test-relation classes.

### Code under test
**"Name the code under test meaningfully, or default to CUT."** `DATA blog_post TYPE REF TO …`, not `DATA clean_fra_blog_post …`. Describe varying state when there are several setups: `empty_blog_post`, `simple_blog_post`, `very_long_blog_post`. *"If you have problems finding a meaningful name, resort to `cut` as a default."*

**"Test against interfaces, not implementations."** `DATA code_under_test TYPE REF TO some_interface.` not `… TYPE REF TO some_class.`

**"Extract the call to the code under test to its own method"** when it needs many parameters, defaulting the uninteresting ones:

```ABAP
METHODS map_xml_to_itab
  IMPORTING xml_string TYPE string
            config     TYPE /clean/xml2itab_config DEFAULT default_config
            format     TYPE /clean/xml2itab_format DEFAULT default_format.

METHOD map_xml_to_itab.
  result = cut->map_xml_to_itab( xml_string = xml_string
                                 config     = config
                                 format     = format ).
ENDMETHOD.

DATA(itab) = map_xml_to_itab( '<xml></xml>' ).
```

### Injection
**"Use dependency inversion to inject test doubles."** *"Dependency inversion means that you hand over all dependencies to the constructor."*

```ABAP
METHODS constructor IMPORTING customizing_reader TYPE REF TO if_fra_cust_obj_model_reader.
METHOD constructor.
  me->customizing_reader = customizing_reader.
ENDMETHOD.
```

*"Don't use setter injection. It enables using the production code in ways that are not intended."* *"Don't use FRIENDS injection. It will initialize dependencies before they are replaced, with probably unexpected consequences. It will break as soon as you rename the internals. It also circumvents initializations in the constructor."*

**"Consider to use the tool ABAP test double."**

```ABAP
DATA(customizing_reader) = CAST /clean/customizing_reader( cl_abap_testdouble=>create( '/clean/default_custom_reader' ) ).
cl_abap_testdouble=>configure_call( customizing_reader )->returning( sub_claim_customizing ).
customizing_reader->read( 'SOME_ID' ).
```

*"Shorter and easier to understand than custom test doubles."*

**"Exploit the test tools"** — *"a clean programming style will let you do much of the work with standard ABAP unit tests and test doubles"* (links SAP-samples/abap-test-isolation-examples).

**"Use test seams as temporary workaround."** *"If all other techniques fail, or when in dangerous shallow waters of legacy code, refrain to test seams… Although they look comfortable at first sight, test seams are invasive and tend to get entangled in private dependencies, such that they are hard to keep alive and stable in the long run. We therefore recommend to refrain to test seams only as a temporary workaround to allow you refactoring the code into a more testable form."*

**"Use LOCAL FRIENDS to access the dependency-inverting constructor"** — legitimate use, for `CREATE PRIVATE` classes:

```ABAP
CLASS /clean/class_under_test DEFINITION LOCAL FRIENDS unit_tests.

METHOD setup.
  DATA(mock) = cl_abap_testdouble=>create( '/clean/some_mock' ).
  cut = NEW /clean/class_under_test( mock ).
ENDMETHOD.
```

**"Don't misuse LOCAL FRIENDS to invade the tested code"** — `cut->some_private_member = 'AUNIT_DUMMY'.` is fragile.

**"Don't add features to production code that are only intended for use during automated testing."** `IF is_unit_test_running = abap_true.` is an anti-pattern. Caveat: *"test features intended to be executed by an end user, e.g. simulated posting or running a report in test mode, form part of the application domain and remain a valid use case."*

**"Don't sub-class to mock methods."** *"it is fragile because the tests break easily when refactoring… It also enables real consumers to inherit your class."* For legacy, prefer test seams; for new code, *"take this testability issue into account directly when designing the class"* — use other test tools or extract the problem method to a separate class with its own interface.

**"Don't mock stuff that's not needed."** *"Define your givens as precisely as possible: don't set data that your test doesn't need, and don't mock objects that are never called."* Pass `VALUE #( )` for unused dependencies. Sometimes mock nothing — data structures/containers (e.g. a `transient_log`) can be used in their production version.

**"Don't build test frameworks."** *"Unit tests - in contrast to integration tests - should be data-in-data-out, with all test data being defined on the fly as needed."* No "test case ID" dispatch (`test_double->set_test_case( 1 ).` + `CASE test_case.`).

### Test methods
**"Test method names: reflect what's given and expected."**

```ABAP
METHOD reads_existing_entry.
METHOD throws_on_invalid_key.
METHOD detects_invalid_input.

" anti-patterns
METHOD get_conversion_exits.   " What's expected, success or failure?
METHOD test_loop.              " It's a test method, what else should it do but "test"?
METHOD parameterized_test.     " So it's parameterized, but what is its aim?
METHOD get_attributes_wo_w.    " What's "_wo_w" supposed to mean?
```

*"As ABAP allows only 30 characters in method names, it's fair to add an explanatory comment if the name is too short to convey enough meaning. ABAP Doc or the first line in the test method may be an appropriate choice."* And: *"Having lots of test methods whose names are too long may be an indicator that you should split your single test class into several ones and express the differences in the givens in the class's names."*

**"Use given-when-then."** *"First, initialize stuff in a given section ('given'), second call the actual tested thing ('when'), third validate the outcome ('then'). If the given or then sections get so long that you cannot visually separate the three sections anymore, extract sub-methods. Blank lines or comments as separators may look good at first glance but don't really reduce the visual clutter. Still they are helpful for the reader and the novice test writer to separate the sections."* (The guide's own examples use `" when` / `" then` comments.)

**'"When" is exactly one call.'**

```ABAP
METHOD rejects_invalid_input.
  " when
  DATA(is_valid) = cut->is_valid_input( 'SOME_RANDOM_ENTRY' ).
  " then
  cl_abap_unit_assert=>assert_false( is_valid ).
ENDMETHOD.
```

*"Calling multiple things indicates that the method has no clear focus and tests too much… was it the first, second, or third call that caused the failure?"*

**"Don't add a TEARDOWN unless you really need it."** *"`teardown` methods are usually only needed to clear up database entries or other external resources in integration tests. Resetting members of the test class, esp. `cut` and the used test doubles, is superfluous; they are overwritten by the `setup` method."*

### Test data
**"Make it easy to spot meaning."**

```ABAP
DATA(alert_id) = '42'.                             " well-known meaningless numbers
DATA(detection_object_type) = '?=/"&'.             " 'keyboard accidents'
CONSTANTS some_random_number TYPE i VALUE 782346.  " revealing variable names

" anti-pattern — don't trick people into believing this connects to real objects
DATA(alert_id) = '00000001223678871'.
DATA(detection_object_type) = 'FRA_SCLAIM'.
CONSTANTS memory_limit TYPE i VALUE 4096.
```

**"Make it easy to spot differences"** — *"Don't force readers to compare long meaningless strings to spot tiny differences"* (the `…END1` / `…END2` suffix trick).

**"Use constants to describe purpose and importance of test data"** — `CONSTANTS some_nonsense_key TYPE char8 VALUE 'ABCDEFGH'.`

### Assertions
**"Few, focused assertions"** — note the guide says *few and focused*, **not** literally "one assert per test": *"Assert only exactly what the test method is about, and this with a small number of assertions. Asserting too much is an indicator that the method has no clear focus. This couples production and test code in too many places."*

**"Use the right assert type."** `cl_abap_unit_assert=>assert_equals( act = table exp = test_data ).` — *"Asserts often do more than meets the eye, for example `assert_equals` includes type matching and providing precise descriptions if values differ. Using the wrong, too-common asserts will force you into the debugger immediately."* Anti-pattern: `assert_true( xsdbool( act = exp ) )`.

**"Assert content, not quantity."** `assert_contains_exactly( actual = table expected = VALUE string_table( ( `ABC` ) ( `DEF` ) ( `GHI` ) ) )` instead of `assert_equals( act = lines( log_messages ) exp = 3 )`.

**"Assert quality, not content"** when you care about a meta-property: `assert_all_lines_shorter_than( actual_lines = table expected_max_length = 80 )` instead of pinning the exact content.

**"Use FAIL to check for expected exceptions."**

```ABAP
METHOD throws_on_empty_input.
  TRY.
      " when
      cut->do_something( '' ).
      cl_abap_unit_assert=>fail( ).
    CATCH /clean/some_exception.
      " then
  ENDTRY.
ENDMETHOD.
```

**"Forward unexpected exceptions instead of catching and failing."**

```ABAP
METHODS reads_entry FOR TESTING RAISING /clean/some_exception.

METHOD reads_entry.
  "when
  DATA(entry) = cut->read_something( ).
  "then
  cl_abap_unit_assert=>assert_not_initial( entry ).
ENDMETHOD.
```

*"Your test code remains focused on the happy path"* — as opposed to `TRY … CATCH … fail( unexpected_exception->get_text( ) )`.

**"Write custom asserts to shorten code and avoid duplication"** — e.g. an `assert_contains` that does `actual_entries[ key = expected_key ]` inside `TRY`/`CATCH cx_sy_itab_line_not_found` + `fail( |Couldn't find the key { expected_key }| )`, *"Instead of copy-pasting this over and over again."*

---

## 17. "How to" / severity & adoption guidance

The guide has no numeric severity scale — but it does rank topics by adoption difficulty, which is the closest thing to severity and is directly useful for ordering a generation skill's rules:

**"How to Get Started with Clean Code":**
- Start with *"things that are easily understood and broadly accepted, such as Booleans, Conditions, and Ifs."*
- *"You will probably benefit most from the section Methods, especially Do one thing, do it well, do it only and Small, because these tremendously improve the overall structure of your code."*
- *"Continue to these more controversial topics later; especially **Comments, Names, and Formatting** can lead to near-religious disputes and should only be addressed by teams that already saw proof of Clean Code's positive effects."*

**"How to Refactor Legacy Code":** Booleans / Conditions / Ifs / Methods are *"most rewarding"* on legacy because *"they can be applied to new code without conflicts."* Names is *"very demanding"* — Avoid encodings *"better ignored"* there. **Don't mix development styles within one development object** (the explicit list: `REF TO` vs `FIELD-SYMBOL` loop targets; `NEW` vs `CREATE OBJECT`; `RETURNING` vs `EXPORTING` for single-output methods). Four-step plan: get the team aboard (*"start with an undisputed small subset"*); boy scout rule (*"always leave the code you edit a little cleaner than you found it"*, without sinking hours); build *"clean islands"*; talk about it.

**"How to Check Automatically":** code pal for ABAP (*"a comprehensive suite of automatic checks for Clean ABAP"*), ATC / Code Inspector / Extended Check / Checkman, abapOpenChecks, abaplint.

**"How to Relate to Other Guides":** follows the *spirit* of Clean Code with ABAP-specific adjustments; *"mostly compatible"* with the ABAP Programming Guidelines with **deviations explicitly marked** — the four marked deviations worth encoding: (1) no prefixes vs. the Guidelines' prefix recommendation; (2) `RETURNING` large tables vs. Guidelines/Code Inspector; (3) `CX_STATIC_CHECK` preference vs. Martin's unchecked-exception preference; (4) `CHECK` outside init vs. the keyword reference for `CHECK` in loops (and `CHECK` vs `RETURN`, where the Guidelines recommend `CHECK`). Also respects DSAG's recommendations, *"although we are more precise in most details."* *"Clean ABAP has become a reference guide for many of SAP's in-house development teams, including the several hundred coders that work on S/4HANA."*

**"How to Disagree":** *"One of the pillars of Clean Code is that the team rules. Just be sure to give things a fair chance before you discard them."*

---

## Explicit gaps — rules you asked about that are NOT in the guide

Flagging these so the skill doesn't attribute them to Clean ABAP:

1. **`MOVE-CORRESPONDING` / `CORRESPONDING #( )`** — no guidance at all.
2. **`COLLECT`** — never mentioned.
3. **`APPEND INITIAL LINE`** (vs `VALUE`/`INSERT`) — never mentioned; the related rules are "Prefer INSERT INTO TABLE to APPEND TO" and the `VALUE #( FOR … )` vs `LOOP`+`INSERT` pair.
4. **`DESCRIBE TABLE … LINES` vs `lines( )`** — no such rule.
5. **`CASE` vs `COND`/`SWITCH`** — no such rule; `COND` appears only as the secondary alternative to `xsdbool`, `SWITCH` and `REDUCE` never appear as guidance.
6. **PCRE vs POSIX regex** — the word PCRE does not appear.
7. **"Don't create an interface for every class"** — the guide says the **opposite**: "Public instance methods should always be part of an interface."
8. **"Don't use `get_`"** — no such rule; `get_*` appears in good examples. The adjacent rule is "Consider using immutable instead of getter" (public `READ-ONLY` attributes for immutables).
9. **Comparison order / Yoda conditions** — not addressed.
10. **Avoid nested loops** — not a rule (only nested `IF` depth, and `LOOP AT … WHERE` over inner filtering `IF`s).
11. **No empty `CATCH` / "don't catch what you can't handle" / `CLEANUP`** — none of these exist in the guide.
12. **Keyword case (upper vs lower)** — deliberately **not** ruled on; deferred to team ABAP Formatter settings.
13. **`RISK LEVEL` / `DURATION` choice** — only shown in examples, never prescribed.
14. **"One assert per test"** — the actual rule is "Few, focused assertions."
15. **Method chaining** — no rule for or against; mentioned only as a side benefit of `RETURNING`.

---

## I. Naming conventions

**SAP-official (enforced by the system):**
- Customer objects live in `Y`/`Z` or a registered namespace `/NSPC/`. Non-negotiable.
- Length limits: report 40 (practically 30), class/interface 30, CDS entity 30, DDIC table/view 16 (30 for view entities), FM 30, package 30.
- Some object types have technical prefix requirements (e.g. RAP behavior pool must be `<something>` matching the BDEF's `implementation in class`; message class, transaction codes must be in the customer namespace).

**Clean ABAP (SAP's own style guide) — explicitly *against* prefixes** `[✓]`:
> Use descriptive names. Do not focus on data types or technical encoding. Do not use Hungarian notation or prefixes.

So `lv_`, `lt_`, `ls_`, `gv_`, `mo_`, `io_`, `is_`, `et_`, `cv_` are **convention, not SAP guidance** — modern SAP style guides discourage them. This is the single most contentious point in enterprise shops. The skill should: follow the project's existing convention when editing existing code, and flag the Clean ABAP position when writing new code, rather than silently picking a side.

**Enterprise conventions (widespread, NOT SAP-official)** — document these as "typical, verify against the customer's standards document":

| Object | Typical convention |
|---|---|
| Executable report | `Z<MM><T><nnnn>` e.g. `ZMMR0002` — module (MM/SD/FI), type (`R`=report, `I`=interface, `C`=conversion, `E`=enhancement, `F`=form, `W`=workflow), 4-digit serial. Also seen: `Z_MM_STOCK_OVERVIEW`. |
| Include | `Z...TOP` (data), `Z...F01` (forms/subroutines), `Z...O01` (PBO), `Z...I01` (PAI), `Z...CLS` (local classes) |
| Module pool | `SAPMZ...` |
| Function group | `Z<MODULE>_<TOPIC>` ; function module `Z_<VERB>_<NOUN>` |
| Global class | `ZCL_<AREA>_<NOUN>` |
| Interface | `ZIF_<AREA>_<NOUN>` |
| Exception class | `ZCX_<AREA>_<NOUN>` |
| Local test class | `LTC_<subject>`; test doubles `LTD_<subject>`; local class `LCL_` |
| DDIC table | `Z<MODULE>_<NOUN>`; structure `ZS_`/`Z..._S`; table type `ZTT_`/`Z..._T`; data element `ZDE_`/`Z...`; domain `ZDO_` |
| CDS interface/basic | `Z<AREA>_I_<Noun>` (or `ZI_<Noun>`) |
| CDS consumption | `Z<AREA>_C_<Noun>` (or `ZC_<Noun>`) |
| CDS RAP base/root | `ZR_<Noun>` (SAP tutorial convention) |
| CDS private | `Z<AREA>_P_<Noun>` |
| CDS extension | `Z<AREA>_E_<Noun>` |
| Metadata extension | same name as the view it annotates |
| Behavior definition | same name as the CDS entity |
| Behavior pool | `ZBP_<entity>` / `ZBP_R_<Noun>` |
| Service definition | `ZUI_<Noun>` (UI) / `ZAPI_<Noun>` (Web API) |
| Service binding | `ZUI_<Noun>_O4` / `_O2` |
| DCL role | `Z<view>_ACC` / `ZI_<Noun>_ACCESS` |
| Message class | `Z<MODULE>` or `Z<MODULE>_<TOPIC>` |
| Package | `Z<MODULE>_<AREA>`, structure package → main package → development packages; `$TMP` never transported |
| Transaction | `Z<MODULE><nn>` |
| SmartForm / Adobe Form | `Z<MODULE>_<DOC>` / `Z<MODULE>_<DOC>_SFP` |
| Search help | `ZH_<Noun>` / `ZSH_<Noun>` |
| Lock object | `EZ<TABLE>` (SAP *requires* the `E` prefix — this one **is** official) |
| Append structure | `ZZ<TABLE>` ; appended fields `ZZ<FIELD>` (customer field prefix `ZZ`/`YY` **is** SAP guidance for appends) |
| Number range object | `Z<NAME>` |
| CDS enum / abstract entity | `Z<AREA>_A_<Noun>` / `Z..._ENUM` `[?]` no established convention |

Sources for the CDS layer prefixes: [ABAP CDS naming conventions](https://community.sap.com/t5/application-development-and-automation-blog-posts/abap-cds-views-development-guidelines-and-naming-conventions/ba-p/13394061), [ABAP naming conventions (software-heroes)](https://software-heroes.com/en/blog/abap-naming-conventions), [abapGit agent naming conventions](https://sylvoscai.github.io/abapgit-agent/abap/guidelines/objects.html).

---
