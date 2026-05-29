# Example Smoke Test Report

This is an example of the output produced by `w3id_smoke_test.py` /
`podman_smoke.sh` against a local `.htaccess`. Do not add to commit
as w3id.org is persistent-identifier service only (no human content).

**Run:** 2026-05-29 10:24 UTC
**Subject:** `../../w3id.org/lmodel/.htaccess`
**Runner:** `bash ./podman_smoke.sh ../../w3id.org/lmodel/.htaccess`
**Result:** **PASS = 78 / 78** (FAIL = 0, exit `0`)

## How to reproduce

```bash
# From this repo
bash ./podman_smoke.sh path/to/lmodel/.htaccess

# Variants
NO_UPSTREAM=1 bash ./podman_smoke.sh path/to/lmodel/.htaccess   # offline (skip GitHub HEAD)
ONLY=conneg   bash ./podman_smoke.sh path/to/lmodel/.htaccess   # filter by substring
BASE=https://w3id.org/lmodel python3 w3id_smoke_test.py         # test production directly
```

Each case issues a no-redirect request against the local Apache, checks
`status` + `Location`, then HEADs the upstream `Location` and expects `200`.

## Coverage summary

| # | Section | Cases | Status |
|---|---|---:|---|
| 1 | Conneg (bare repo) | 10 | PASS |
| 2 | Conneg (trailing slash) | 2 | PASS |
| 3 | Conneg (deep extensionless — class IRI) | 2 | PASS |
| 4 | Schema routes | 2 | PASS |
| 5 | Multi-file schema (regression) | 3 | PASS |
| 6 | Core artifacts (extension) | 13 | PASS |
| 7 | Non-core artifacts (302) | 22 | PASS |
| 8 | Deeper-pass fixes | 4 | PASS |
| 9 | Hyphenated repo: `uco-core` (single-hyphen STEM family) | 5 | PASS |
| 10 | Hyphenated repo: `nist-ai-rmf` (multi-hyphen STEM family) | 4 | PASS |
| 11 | Docs / gen-doc elements rule (`text/html`) | 10 | PASS |
| | **Total** | **78** | **PASS** |

## Worked examples

The shapes the tester verifies. Status, `Location`, and the upstream HEAD
result are all checked.

### Content negotiation on a repo root

```http
GET /lmodel/common-domain-model
Accept: text/turtle
-> 303 https://raw.githubusercontent.com/lmodel/common-domain-model/master/project/rdf/common_domain_model.ttl

GET /lmodel/common-domain-model
Accept: application/ld+json
-> 303 https://raw.githubusercontent.com/lmodel/common-domain-model/master/project/jsonld/common_domain_model.context.jsonld

GET /lmodel/common-domain-model
Accept: text/html
-> 303 https://lmodel.github.io/common-domain-model

GET /lmodel/common-domain-model
Accept: */*
-> 302 https://lmodel.github.io/common-domain-model

GET /lmodel/common-domain-model
Accept: application/zip
-> 406 Not Acceptable
```

### Class / slot IRI -> gen-doc elements page

```http
GET /lmodel/common-domain-model/Trade
Accept: text/html
-> 303 https://lmodel.github.io/common-domain-model/elements/Trade/

GET /lmodel/common-domain-model/tradeIdentifier
Accept: text/html
-> 303 https://lmodel.github.io/common-domain-model/elements/tradeIdentifier/

GET /lmodel/common-domain-model/Trade
Accept: text/turtle
-> 303 https://raw.githubusercontent.com/lmodel/common-domain-model/master/project/rdf/common_domain_model.ttl
```

### Reserved single-segment names pass through

```http
GET /lmodel/common-domain-model/about    -> 303 https://lmodel.github.io/common-domain-model/about
GET /lmodel/common-domain-model/index    -> 303 https://lmodel.github.io/common-domain-model/index
GET /lmodel/common-domain-model/elements -> 303 https://lmodel.github.io/common-domain-model/elements
```

### Extension-driven artifact redirects

```http
GET /lmodel/common-domain-model/common_domain_model.ttl
  -> 303 https://raw.githubusercontent.com/lmodel/common-domain-model/master/project/rdf/common_domain_model.ttl

GET /lmodel/common-domain-model/common_domain_model.owl
  -> 303 https://raw.githubusercontent.com/lmodel/common-domain-model/master/project/owl/common_domain_model.owl.ttl

GET /lmodel/common-domain-model/context.jsonld
  -> 303 https://raw.githubusercontent.com/lmodel/common-domain-model/master/project/jsonld/common_domain_model.context.jsonld

GET /lmodel/common-domain-model/common_domain_model.schema.json
  -> 303 https://raw.githubusercontent.com/lmodel/common-domain-model/master/project/jsonschema/common_domain_model.schema.json

GET /lmodel/common-domain-model/common_domain_model.xlsx
  -> 302 https://raw.githubusercontent.com/lmodel/common-domain-model/master/project/excel/common_domain_model.xlsx
```

### Multi-file schema (regression)

```http
GET /lmodel/common-domain-model/schema/cdm_legaldocumentation_csa.yaml
  -> 303 https://raw.githubusercontent.com/lmodel/common-domain-model/master/src/common_domain_model/schema/cdm_legaldocumentation_csa.yaml

GET /lmodel/common-domain-model/schema
  -> 303 https://raw.githubusercontent.com/lmodel/common-domain-model/master/src/common_domain_model/schema/common_domain_model.yaml
```

### Hyphenated repos (STEM normalization)

`uco-core` (single hyphen, default `main` branch):

```http
GET /lmodel/uco-core/uco_core.jsonld
  -> 303 https://raw.githubusercontent.com/lmodel/uco-core/main/project/jsonld/uco_core.jsonld

GET /lmodel/uco/core
Accept: text/html
  -> 303 https://lmodel.github.io/uco-core
```

`nist-ai-rmf` (multi-hyphen). `nist-ai-100-1` and `nist-ai-600-1` are
independent repos with their own STEMs (not aliases of `nist-ai-rmf`):

```http
GET /lmodel/nist-ai-rmf/nist_ai_rmf.jsonld
  -> 303 https://raw.githubusercontent.com/lmodel/nist-ai-rmf/main/project/jsonld/nist_ai_rmf.jsonld

GET /lmodel/nist-ai-600-1/nist_ai_600_1.jsonld
  -> 303 https://raw.githubusercontent.com/lmodel/nist-ai-600-1/main/project/jsonld/nist_ai_600_1.jsonld

GET /lmodel/nist-ai-rmf
Accept: application/yaml
  -> 303 https://raw.githubusercontent.com/lmodel/nist-ai-rmf/main/src/nist_ai_rmf/schema/nist_ai_rmf.yaml
```

## Full case-by-case results

```
## Conneg (bare repo) ##
PASS  cdm turtle                        303  -> .../master/project/rdf/common_domain_model.ttl
PASS  cdm ld+json                       303  -> .../master/project/jsonld/common_domain_model.context.jsonld
PASS  cdm schema+json                   303  -> .../master/project/jsonschema/common_domain_model.schema.json
PASS  cdm shacl+turtle                  303  -> .../master/project/shacl/common_domain_model.shacl.ttl
PASS  cdm shex                          303  -> .../master/project/shex/common_domain_model.shex
PASS  cdm yaml                          303  -> .../master/src/common_domain_model/schema/common_domain_model.yaml
PASS  cdm text/yaml                     303  -> .../master/src/common_domain_model/schema/common_domain_model.yaml
PASS  cdm html                          303  -> https://lmodel.github.io/common-domain-model
PASS  cdm */*                           302  -> https://lmodel.github.io/common-domain-model
PASS  cdm unsupported                   406  (no Location)

## Conneg (trailing slash) ##
PASS  cdm/ turtle                       303  -> .../master/project/rdf/common_domain_model.ttl
PASS  cdm/ html                         303  -> https://lmodel.github.io/common-domain-model/

## Conneg (deep extensionless - class IRI) ##
PASS  cdm/Trade turtle                  303  -> .../master/project/rdf/common_domain_model.ttl
PASS  cdm/Trade html                    303  -> https://lmodel.github.io/common-domain-model/elements/Trade/

## Schema routes ##
PASS  schema yaml                       303  -> .../master/src/common_domain_model/schema/common_domain_model.yaml
PASS  schema bare path                  303  -> .../master/src/common_domain_model/schema/common_domain_model.yaml

## Multi-file schema (regression) ##
PASS  cdm sub-schema explicit           303  -> .../master/src/common_domain_model/schema/cdm_legaldocumentation_csa.yaml
PASS  cdm canonical schema              303  -> .../master/src/common_domain_model/schema/common_domain_model.yaml
PASS  cdm /schema bare                  303  -> .../master/src/common_domain_model/schema/common_domain_model.yaml

## Core artifacts (extension) ##
PASS  .ttl                              303  -> .../master/project/rdf/common_domain_model.ttl
PASS  .owl                              303  -> .../master/project/owl/common_domain_model.owl.ttl
PASS  .jsonld                           303  -> .../master/project/jsonld/common_domain_model.jsonld
PASS  .context.jsonld                   303  -> .../master/project/jsonld/common_domain_model.context.jsonld
PASS  context.jsonld bare               303  -> .../master/project/jsonld/common_domain_model.context.jsonld
PASS  context.json bare                 303  -> .../master/project/jsonld/common_domain_model.context.jsonld
PASS  .schema.json                      303  -> .../master/project/jsonschema/common_domain_model.schema.json
PASS  .graphql                          303  -> .../master/project/graphql/common_domain_model.graphql
PASS  .proto                            303  -> .../master/project/protobuf/common_domain_model.proto
PASS  .shacl.ttl                        303  -> .../master/project/shacl/common_domain_model.shacl.ttl
PASS  .shex                             303  -> .../master/project/shex/common_domain_model.shex
PASS  linkml yaml                       303  -> .../master/project/linkml/common_domain_model.merged.linkml.yaml
PASS  prefixmap yaml                    303  -> .../master/project/prefixmap/common_domain_model.yaml
PASS  sqlschema sql                     303  -> .../master/project/sqlschema/common_domain_model.sql

## Non-core artifacts (302) ##
PASS  .xlsx                             302  -> .../master/project/excel/common_domain_model.xlsx
PASS  .ts                               302  -> .../master/project/typescript/common_domain_model.ts
PASS  .h                                302  -> .../master/project/cpp/common_domain_model.h
PASS  .csv                              302  -> .../master/project/csv/common_domain_model.csv
PASS  .dbml                             302  -> .../master/project/dbml/common_domain_model.dbml
PASS  .er.md                            302  -> .../master/project/erdiagram/common_domain_model.er.md
PASS  .go                               302  -> .../master/project/golang/common_domain_model.go
PASS  golr yaml                         302  -> .../master/project/golr/Trade_config.yaml
PASS  .dot.dot                          302  -> .../master/project/graphviz/common_domain_model.dot.dot
PASS  markdown-datadict                 302  -> .../master/project/markdown-datadict/common_domain_model.md
PASS  mermaid md                        302  -> .../master/project/mermaid/Trade.md
PASS  namespaces py                     302  -> .../master/project/namespaces/common_domain_model.namespaces.py
PASS  pandera py                        302  -> .../master/project/pandera/common_domain_model_pandera.py
PASS  .plantuml                         302  -> .../master/project/plantuml/common_domain_model.plantuml
PASS  sqla py                           302  -> .../master/project/sqla/common_domain_model_sqlalchemy.py
PASS  sqlvalidation                     302  -> .../master/project/sqlvalidation/common_domain_model.sql
PASS  .sssom.tsv                        302  -> .../master/project/sssom/common_domain_model.sssom.tsv
PASS  summary tsv                       302  -> .../master/project/summary/common_domain_model.summary.tsv
PASS  terminusdb json                   302  -> .../master/project/terminusdb/common_domain_model.json
PASS  .tql                              302  -> .../master/project/typedb/common_domain_model.tql
PASS  yaml dir                          302  -> .../master/project/yaml/common_domain_model.yaml
PASS  rust Cargo                        302  -> .../master/project/rust/Cargo.toml

## Deeper-pass fixes ##
PASS  .owl.ttl direct                   303  -> .../master/project/owl/common_domain_model.owl.ttl
PASS  bare stem yaml                    303  -> .../master/src/common_domain_model/schema/common_domain_model.yaml
PASS  json conneg                       303  -> .../master/project/jsonld/common_domain_model.context.jsonld
PASS  schema bare narrow                303  -> .../master/src/common_domain_model/schema/common_domain_model.yaml

## Hyphenated repo: uco-core (single-hyphen STEM family) ##
PASS  uco-core jsonld                   303  -> .../uco-core/main/project/jsonld/uco_core.jsonld
PASS  uco-core schema                   303  -> .../uco-core/main/src/uco_core/schema/uco_core.yaml
PASS  uco-core conneg ld+json           303  -> .../uco-core/main/project/jsonld/uco_core.context.jsonld
PASS  uco-core java                     302  -> .../uco-core/main/project/java/Annotation.java
PASS  uco/core slash                    303  -> https://lmodel.github.io/uco-core

## Hyphenated repo: nist-ai-rmf (multi-hyphen STEM family) ##
PASS  nist-ai-rmf jsonld                303  -> .../nist-ai-rmf/main/project/jsonld/nist_ai_rmf.jsonld
PASS  nist-ai-rmf conneg                303  -> .../nist-ai-rmf/main/src/nist_ai_rmf/schema/nist_ai_rmf.yaml
PASS  nist-ai-600-1 jsonld              303  -> .../nist-ai-600-1/main/project/jsonld/nist_ai_600_1.jsonld
PASS  nist-ai-600-1 html                303  -> https://lmodel.github.io/nist-ai-600-1

## Docs / gen-doc elements rule (text/html) ##
PASS  elements class                    303  -> https://lmodel.github.io/common-domain-model/elements/Trade/
PASS  elements slot                     303  -> https://lmodel.github.io/common-domain-model/elements/tradeIdentifier/
PASS  elements xhtml                    303  -> https://lmodel.github.io/common-domain-model/elements/Account/
PASS  elements trailing /               303  -> https://lmodel.github.io/common-domain-model/elements/Party/
PASS  reserved about                    303  -> https://lmodel.github.io/common-domain-model/about
PASS  reserved index                    303  -> https://lmodel.github.io/common-domain-model/index
PASS  reserved elements                 303  -> https://lmodel.github.io/common-domain-model/elements
PASS  reserved schema                   303  -> .../master/src/common_domain_model/schema/common_domain_model.yaml
PASS  docs repo root                    303  -> https://lmodel.github.io/common-domain-model
PASS  elements nist-ai-rmf              303  -> https://lmodel.github.io/nist-ai-rmf/elements/Risk/

============================================================
PASS=78 FAIL=0  (total=78)
```

## Environment

| | |
|---|---|
| OS | Linux |
| Container engine | `podman` |
| Image | `docker.io/library/httpd:2.4.62` |
| `mod_rewrite` | loaded, `AllowOverride All` on `/usr/local/apache2/htdocs` |
| Python | 3.12 (auto-picked by `podman_smoke.sh`) |
| Upstream HEAD check | enabled (every redirect target verified `200`) |

## Notes & caveats

- `cdm */*` returns **302** (docs treated as an information resource); `cdm html` returns **303** via the explicit `text/html` conneg rule. Same destination, different semantics — by design.
- `Accept: application/zip` against an extensionless URL returns **406 Not Acceptable** (Accept present and specific, no rule matches, `*/*` absent).
- The deep-extensionless HTML conneg uses three ordered rules so that (1) reserved names (`about|index|elements`) pass through unchanged, (2) `<repo>/<Name>[/]` resolves to `…github.io/<repo>/elements/<Name>/` (matches `gen-doc` layout), and (3) `<repo>[/]` resolves to the docs root.
- `nist-ai-100-1` and `nist-ai-600-1` are independent repos (not aliases of `nist-ai-rmf`): each has its own hyphen->underscore `STEM` (`nist_ai_100_1`, `nist_ai_600_1`) and publishes its own artifacts under `lmodel/<repo>/…`.
- Upstream `200`s are checked against `raw.githubusercontent.com` / `lmodel.github.io`, so a green run depends on the relevant `project/` artifacts being published. Re-run with `NO_UPSTREAM=1` for offline verification of the rules themselves.
