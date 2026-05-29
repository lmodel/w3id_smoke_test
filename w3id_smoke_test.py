#!/usr/bin/env python3
# Requires Python 3.7+. If `python3` resolves to 3.6 on your system, invoke
# explicitly:  python3.11 w3id_smoke_test.py
"""Smoke test for lmodel/.htaccess routing rules.

For each case:
  1. Issue a request to the local Apache (BASE) with a given Accept header,
     verify the response status code (and Location header for redirects).
  2. Follow the Location to the upstream raw URL and verify it returns 200.

Stdlib only (urllib). No external deps.

Naming conventions (per linkml-schema skill + .htaccess):
  REPO   = URL segment / GitHub repo name (kebab-case)  -> common-domain-model
  STEM   = artifact filename stem        (snake_case)   -> common_domain_model
  BRANCH = git branch                                   -> master (FINOS upstream)

Env vars:
  BASE       (default http://localhost:18080/lmodel) -- local Apache root
  TIMEOUT    (default 10) -- per-request timeout in seconds
  NO_UPSTREAM=1           -- skip the upstream HEAD check (offline mode)
  ONLY=<substr>           -- run only cases whose description contains <substr>

Exit code: 0 on all pass, 1 on any failure.
"""

from __future__ import annotations

import os
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Optional

BASE = os.environ.get("BASE", "http://localhost:18080/lmodel").rstrip("/")
TIMEOUT = float(os.environ.get("TIMEOUT", "10"))
SKIP_UPSTREAM = os.environ.get("NO_UPSTREAM") == "1"
ONLY = os.environ.get("ONLY", "")

REPO = "common-domain-model"
STEM = "common_domain_model"
BRANCH = "master"
RAW = f"https://raw.githubusercontent.com/lmodel/{REPO}/{BRANCH}/project"
SRC = f"https://raw.githubusercontent.com/lmodel/{REPO}/{BRANCH}/src/{STEM}"


@dataclass
class Case:
    section: str
    desc: str
    url: str
    accept: str
    want_status: int
    want_loc: Optional[str] = None  # None = don't check Location body


@dataclass
class Result:
    case: Case
    got_status: int = 0
    got_loc: str = ""
    raw_status: str = "-"  # "-" if not checked, else stringified HTTP code or "ERR"
    ok: bool = False
    notes: list[str] = field(default_factory=list)


def _request(url: str, accept: str, method: str = "GET") -> tuple[int, str]:
    """Issue a single request without auto-following redirects. Returns (status, Location)."""

    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *_a, **_kw):
            return None

    opener = urllib.request.build_opener(NoRedirect)
    req = urllib.request.Request(url, method=method, headers={"Accept": accept})
    try:
        with opener.open(req, timeout=TIMEOUT) as resp:
            return resp.status, resp.headers.get("Location", "")
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get("Location", "") if e.headers else ""
    except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
        return 0, f"ERR: {e}"


def _head_upstream(url: str) -> str:
    """HEAD the upstream URL, following redirects. Returns status as string or 'ERR'."""
    if SKIP_UPSTREAM:
        return "-"
    if not url.startswith(("http://", "https://")):
        return "-"
    try:
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return str(resp.status)
    except urllib.error.HTTPError as e:
        return str(e.code)
    except Exception:
        return "ERR"


def run(case: Case) -> Result:
    r = Result(case=case)
    r.got_status, r.got_loc = _request(case.url, case.accept)

    ok = (r.got_status == case.want_status)
    if case.want_loc is not None and r.got_loc != case.want_loc:
        ok = False
        r.notes.append(f"loc mismatch: got={r.got_loc!r} want={case.want_loc!r}")

    if 300 <= case.want_status < 400 and r.got_loc.startswith("http"):
        r.raw_status = _head_upstream(r.got_loc)
        if not SKIP_UPSTREAM and r.raw_status != "200":
            ok = False
            r.notes.append(f"upstream {r.raw_status}")

    r.ok = ok
    return r


def build_cases() -> list[Case]:
    cases: list[Case] = []

    def add(section: str, desc: str, url: str, accept: str, status: int, loc: Optional[str]) -> None:
        cases.append(Case(section, desc, url, accept, status, loc))

    # ---- Conneg (bare repo) ----
    s = "Conneg (bare repo)"
    add(s, "cdm turtle",        f"{BASE}/{REPO}", "text/turtle",             303, f"{RAW}/rdf/{STEM}.ttl")
    add(s, "cdm ld+json",       f"{BASE}/{REPO}", "application/ld+json",     303, f"{RAW}/jsonld/{STEM}.context.jsonld")
    add(s, "cdm schema+json",   f"{BASE}/{REPO}", "application/schema+json", 303, f"{RAW}/jsonschema/{STEM}.schema.json")
    add(s, "cdm shacl+turtle",  f"{BASE}/{REPO}", "application/shacl+turtle",303, f"{RAW}/shacl/{STEM}.shacl.ttl")
    add(s, "cdm shex",          f"{BASE}/{REPO}", "text/shex",               303, f"{RAW}/shex/{STEM}.shex")
    add(s, "cdm yaml",          f"{BASE}/{REPO}", "application/yaml",        303, f"{SRC}/schema/{STEM}.yaml")
    add(s, "cdm text/yaml",     f"{BASE}/{REPO}", "text/yaml",               303, f"{SRC}/schema/{STEM}.yaml")
    add(s, "cdm html",          f"{BASE}/{REPO}", "text/html",               303, f"https://lmodel.github.io/{REPO}")
    add(s, "cdm */*",           f"{BASE}/{REPO}", "*/*",                     302, f"https://lmodel.github.io/{REPO}")
    add(s, "cdm unsupported",   f"{BASE}/{REPO}", "application/zip",         406, None)

    # ---- Conneg (trailing slash) ----
    s = "Conneg (trailing slash)"
    add(s, "cdm/ turtle",       f"{BASE}/{REPO}/", "text/turtle", 303, f"{RAW}/rdf/{STEM}.ttl")
    add(s, "cdm/ html",         f"{BASE}/{REPO}/", "text/html",   303, f"https://lmodel.github.io/{REPO}/")

    # ---- Conneg (deep extensionless - class IRI) ----
    s = "Conneg (deep extensionless - class IRI)"
    add(s, "cdm/Trade turtle",  f"{BASE}/{REPO}/Trade", "text/turtle", 303, f"{RAW}/rdf/{STEM}.ttl")
    add(s, "cdm/Trade html",    f"{BASE}/{REPO}/Trade", "text/html",   303, f"https://lmodel.github.io/{REPO}/elements/Trade/")

    # ---- Schema routes ----
    s = "Schema routes"
    add(s, "schema yaml",       f"{BASE}/{REPO}/schema/{STEM}.yaml", "*/*", 303, f"{SRC}/schema/{STEM}.yaml")
    add(s, "schema bare path",  f"{BASE}/{REPO}/schema/anything",    "*/*", 303, f"{SRC}/schema/{STEM}.yaml")

    # ---- Multi-file schema (regression) ----
    s = "Multi-file schema (regression)"
    sub = "cdm_legaldocumentation_csa"
    add(s, "cdm sub-schema explicit", f"{BASE}/{REPO}/schema/{sub}.yaml", "*/*", 303, f"{SRC}/schema/{sub}.yaml")
    add(s, "cdm canonical schema",    f"{BASE}/{REPO}/schema/{STEM}.yaml", "*/*", 303, f"{SRC}/schema/{STEM}.yaml")
    add(s, "cdm /schema bare",        f"{BASE}/{REPO}/schema",             "*/*", 303, f"{SRC}/schema/{STEM}.yaml")

    # ---- Core artifacts (extension) ----
    s = "Core artifacts (extension)"
    add(s, ".ttl",                f"{BASE}/{REPO}/{STEM}.ttl",            "*/*", 303, f"{RAW}/rdf/{STEM}.ttl")
    add(s, ".owl",                f"{BASE}/{REPO}/{STEM}.owl",            "*/*", 303, f"{RAW}/owl/{STEM}.owl.ttl")
    add(s, ".jsonld",             f"{BASE}/{REPO}/{STEM}.jsonld",         "*/*", 303, f"{RAW}/jsonld/{STEM}.jsonld")
    add(s, ".context.jsonld",     f"{BASE}/{REPO}/{STEM}.context.jsonld", "*/*", 303, f"{RAW}/jsonld/{STEM}.context.jsonld")
    add(s, "context.jsonld bare", f"{BASE}/{REPO}/context.jsonld",        "*/*", 303, f"{RAW}/jsonld/{STEM}.context.jsonld")
    add(s, "context.json bare",   f"{BASE}/{REPO}/context.json",          "*/*", 303, f"{RAW}/jsonld/{STEM}.context.jsonld")
    add(s, ".schema.json",        f"{BASE}/{REPO}/{STEM}.schema.json",    "*/*", 303, f"{RAW}/jsonschema/{STEM}.schema.json")
    add(s, ".graphql",            f"{BASE}/{REPO}/{STEM}.graphql",        "*/*", 303, f"{RAW}/graphql/{STEM}.graphql")
    add(s, ".proto",              f"{BASE}/{REPO}/{STEM}.proto",          "*/*", 303, f"{RAW}/protobuf/{STEM}.proto")
    add(s, ".shacl.ttl",          f"{BASE}/{REPO}/{STEM}.shacl.ttl",      "*/*", 303, f"{RAW}/shacl/{STEM}.shacl.ttl")
    add(s, ".shex",               f"{BASE}/{REPO}/{STEM}.shex",           "*/*", 303, f"{RAW}/shex/{STEM}.shex")
    add(s, "linkml yaml",         f"{BASE}/{REPO}/{STEM}.merged.linkml.yaml", "*/*", 303, f"{RAW}/linkml/{STEM}.merged.linkml.yaml")
    add(s, "prefixmap yaml",      f"{BASE}/{REPO}/prefixmap/{STEM}.yaml", "*/*", 303, f"{RAW}/prefixmap/{STEM}.yaml")
    add(s, "sqlschema sql",       f"{BASE}/{REPO}/{STEM}.sql",            "*/*", 303, f"{RAW}/sqlschema/{STEM}.sql")

    # ---- Non-core artifacts (302) ----
    s = "Non-core artifacts (302)"
    add(s, ".xlsx",            f"{BASE}/{REPO}/{STEM}.xlsx",                 "*/*", 302, f"{RAW}/excel/{STEM}.xlsx")
    add(s, ".ts",              f"{BASE}/{REPO}/{STEM}.ts",                   "*/*", 302, f"{RAW}/typescript/{STEM}.ts")
    add(s, ".h",               f"{BASE}/{REPO}/{STEM}.h",                    "*/*", 302, f"{RAW}/cpp/{STEM}.h")
    add(s, ".csv",             f"{BASE}/{REPO}/{STEM}.csv",                  "*/*", 302, f"{RAW}/csv/{STEM}.csv")
    add(s, ".dbml",            f"{BASE}/{REPO}/{STEM}.dbml",                 "*/*", 302, f"{RAW}/dbml/{STEM}.dbml")
    add(s, ".er.md",           f"{BASE}/{REPO}/{STEM}.er.md",                "*/*", 302, f"{RAW}/erdiagram/{STEM}.er.md")
    add(s, ".go",              f"{BASE}/{REPO}/{STEM}.go",                   "*/*", 302, f"{RAW}/golang/{STEM}.go")
    add(s, "golr yaml",        f"{BASE}/{REPO}/golr/Trade_config.yaml",      "*/*", 302, f"{RAW}/golr/Trade_config.yaml")
    add(s, ".dot.dot",         f"{BASE}/{REPO}/{STEM}.dot.dot",              "*/*", 302, f"{RAW}/graphviz/{STEM}.dot.dot")
    add(s, "markdown-datadict",f"{BASE}/{REPO}/markdown-datadict/{STEM}.md", "*/*", 302, f"{RAW}/markdown-datadict/{STEM}.md")
    add(s, "mermaid md",       f"{BASE}/{REPO}/mermaid/Trade.md",            "*/*", 302, f"{RAW}/mermaid/Trade.md")
    add(s, "namespaces py",    f"{BASE}/{REPO}/namespaces/{STEM}.namespaces.py", "*/*", 302, f"{RAW}/namespaces/{STEM}.namespaces.py")
    add(s, "pandera py",       f"{BASE}/{REPO}/pandera/{STEM}_pandera.py",   "*/*", 302, f"{RAW}/pandera/{STEM}_pandera.py")
    add(s, ".plantuml",        f"{BASE}/{REPO}/{STEM}.plantuml",             "*/*", 302, f"{RAW}/plantuml/{STEM}.plantuml")
    add(s, "sqla py",          f"{BASE}/{REPO}/sqla/{STEM}_sqlalchemy.py",   "*/*", 302, f"{RAW}/sqla/{STEM}_sqlalchemy.py")
    add(s, "sqlvalidation",    f"{BASE}/{REPO}/sqlvalidation/{STEM}.sql",    "*/*", 302, f"{RAW}/sqlvalidation/{STEM}.sql")
    add(s, ".sssom.tsv",       f"{BASE}/{REPO}/{STEM}.sssom.tsv",            "*/*", 302, f"{RAW}/sssom/{STEM}.sssom.tsv")
    add(s, "summary tsv",      f"{BASE}/{REPO}/summary/{STEM}.summary.tsv",  "*/*", 302, f"{RAW}/summary/{STEM}.summary.tsv")
    add(s, "terminusdb json",  f"{BASE}/{REPO}/terminusdb/{STEM}.json",      "*/*", 302, f"{RAW}/terminusdb/{STEM}.json")
    add(s, ".tql",             f"{BASE}/{REPO}/{STEM}.tql",                  "*/*", 302, f"{RAW}/typedb/{STEM}.tql")
    add(s, "yaml dir",         f"{BASE}/{REPO}/yaml/{STEM}.yaml",            "*/*", 302, f"{RAW}/yaml/{STEM}.yaml")
    add(s, "rust Cargo",       f"{BASE}/{REPO}/rust/Cargo.toml",             "*/*", 302, f"{RAW}/rust/Cargo.toml")

    # ---- Deeper-pass fixes ----
    s = "Deeper-pass fixes"
    add(s, ".owl.ttl direct",   f"{BASE}/{REPO}/{STEM}.owl.ttl", "*/*", 303, f"{RAW}/owl/{STEM}.owl.ttl")
    add(s, "bare stem yaml",    f"{BASE}/{REPO}/{STEM}.yaml",    "*/*", 303, f"{SRC}/schema/{STEM}.yaml")
    add(s, "json conneg",       f"{BASE}/{REPO}", "application/json", 303, f"{RAW}/jsonld/{STEM}.context.jsonld")
    add(s, "schema bare narrow",f"{BASE}/{REPO}/schema/anyname", "*/*", 303, f"{SRC}/schema/{STEM}.yaml")

    # ---- Hyphenated repo: uco-core (single-hyphen STEM family) ----
    s = "Hyphenated repo: uco-core (single-hyphen STEM family)"
    uco_raw = "https://raw.githubusercontent.com/lmodel/uco-core/main/project"
    uco_src = "https://raw.githubusercontent.com/lmodel/uco-core/main/src/uco_core"
    add(s, "uco-core jsonld",        f"{BASE}/uco-core/uco_core.jsonld",          "*/*", 303, f"{uco_raw}/jsonld/uco_core.jsonld")
    add(s, "uco-core schema",        f"{BASE}/uco-core/schema/uco_core.yaml",     "*/*", 303, f"{uco_src}/schema/uco_core.yaml")
    add(s, "uco-core conneg ld+json",f"{BASE}/uco-core", "application/ld+json",          303, f"{uco_raw}/jsonld/uco_core.context.jsonld")
    add(s, "uco-core java",          f"{BASE}/uco-core/Annotation.java",          "*/*", 302, f"{uco_raw}/java/Annotation.java")
    add(s, "uco/core slash",         f"{BASE}/uco/core", "text/html",                    303, "https://lmodel.github.io/uco-core")

    # ---- Hyphenated repo: nist-ai-rmf (multi-hyphen STEM family) ----
    s = "Hyphenated repo: nist-ai-rmf (multi-hyphen STEM family)"
    nar_raw = "https://raw.githubusercontent.com/lmodel/nist-ai-rmf/main/project"
    nar_src = "https://raw.githubusercontent.com/lmodel/nist-ai-rmf/main/src/nist_ai_rmf"
    add(s, "nist-ai-rmf jsonld",       f"{BASE}/nist-ai-rmf/nist_ai_rmf.jsonld", "*/*", 303, f"{nar_raw}/jsonld/nist_ai_rmf.jsonld")
    add(s, "nist-ai-rmf conneg",       f"{BASE}/nist-ai-rmf", "application/yaml",       303, f"{nar_src}/schema/nist_ai_rmf.yaml")
    add(s, "nist-ai-600-1 alias jsonld", f"{BASE}/nist-ai-600-1/nist_ai_rmf.jsonld", "*/*", 303, f"{nar_raw}/jsonld/nist_ai_rmf.jsonld")
    add(s, "nist-ai-600-1 alias html",   f"{BASE}/nist-ai-600-1", "text/html",                303, "https://lmodel.github.io/nist-ai-rmf")

    # ---- Docs / gen-doc elements rule (text/html) ----
    s = "Docs / gen-doc elements rule (text/html)"
    docs = f"https://lmodel.github.io/{REPO}"
    add(s, "elements class",      f"{BASE}/{REPO}/Trade",           "text/html",             303, f"{docs}/elements/Trade/")
    add(s, "elements slot",       f"{BASE}/{REPO}/tradeIdentifier", "text/html",             303, f"{docs}/elements/tradeIdentifier/")
    add(s, "elements xhtml",      f"{BASE}/{REPO}/Account",         "application/xhtml+xml", 303, f"{docs}/elements/Account/")
    add(s, "elements trailing /", f"{BASE}/{REPO}/Party/",          "text/html",             303, f"{docs}/elements/Party/")
    add(s, "reserved about",      f"{BASE}/{REPO}/about",           "text/html",             303, f"{docs}/about")
    add(s, "reserved index",      f"{BASE}/{REPO}/index",           "text/html",             303, f"{docs}/index")
    add(s, "reserved elements",   f"{BASE}/{REPO}/elements",        "text/html",             303, f"{docs}/elements")
    add(s, "reserved schema",     f"{BASE}/{REPO}/schema",          "text/html",             303, f"{SRC}/schema/{STEM}.yaml")
    add(s, "docs repo root",      f"{BASE}/{REPO}",                 "text/html",             303, docs)
    add(s, "elements nist-ai-rmf",f"{BASE}/nist-ai-rmf/Risk",       "text/html",             303, "https://lmodel.github.io/nist-ai-rmf/elements/Risk/")

    return cases


def main() -> int:
    cases = build_cases()
    if ONLY:
        cases = [c for c in cases if ONLY.lower() in c.desc.lower()]
        if not cases:
            print(f"ONLY={ONLY!r} matched no cases", file=sys.stderr)
            return 2

    current_section = ""
    pass_count = 0
    fail_count = 0
    failures: list[Result] = []

    for c in cases:
        if c.section != current_section:
            if current_section:
                print()
            print(f"## {c.section} ##")
            current_section = c.section

        r = run(c)
        tag = "PASS" if r.ok else "FAIL"
        loc = r.got_loc or "-"
        print(f"{tag}  {c.desc:<32}  status={r.got_status}  loc={loc}  raw={r.raw_status}"
              + (f"  [{'; '.join(r.notes)}]" if r.notes else ""))

        if r.ok:
            pass_count += 1
        else:
            fail_count += 1
            failures.append(r)

    print()
    print("=" * 60)
    print(f"PASS={pass_count} FAIL={fail_count}  (total={pass_count + fail_count})")
    if failures:
        print("Failures:")
        for r in failures:
            print(f"  - [{r.case.section}] {r.case.desc}: "
                  f"status={r.got_status}/want={r.case.want_status} raw={r.raw_status}"
                  + (f" {r.notes}" if r.notes else ""))
    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
