# Project Constitution: bookmark-cleaner

**Version:** 1.0.0
**Ratified:** 2026-03-17
**Last Amended:** 2026-03-17

## Preamble

This constitution establishes the foundational principles and architectural constraints for **bookmark-cleaner**, an open-source Python CLI tool that cleans, deduplicates, and organizes browser bookmark files. These principles are immutable unless explicitly amended through formal review.

bookmark-cleaner is a local-first, privacy-respecting utility designed for end users to download from GitHub and run immediately. Every design decision must optimize for simplicity, reliability, and ease of use.

## Article I: Lightweight-First Principle

**Rules:**
- The tool MUST be installable and runnable with `pip install bookmark-cleaner` or `uvx bookmark-cleaner` and nothing else
- Core functionality MUST depend only on Python stdlib plus at most three runtime dependencies (typer, rich, tomli)
- Optional features (LLM classification, dead link checking) MAY add dependencies but MUST be declared as pip extras (e.g., `pip install bookmark-cleaner[llm]`)
- The tool MUST NOT require configuration files, databases, environment variables, or network access for core operations (clean, classify with keywords, validate, convert, info)
- Sensible defaults SHALL make `bookmark-cleaner clean bookmarks.html` work with zero configuration
- Total installed package size SHOULD remain under 1MB (excluding optional extras)

**Rationale:**
This is a download-and-run utility for non-technical users cleaning up their bookmarks. Every additional dependency, config file, or setup step is a barrier to adoption. The tool should feel as simple as a Unix utility.

**Exceptions:**
- Development dependencies (pytest, ruff, mypy) are unrestricted
- Optional extras for advanced features (LLM, async HTTP) may add dependencies

## Article II: Test-First Imperative

**Rules:**
- No implementation code SHALL be written before tests exist for that functionality
- Tests MUST be confirmed to FAIL before writing implementation code (Red-Green-Refactor)
- Minimum 80% code coverage MUST be maintained across unit + integration tests
- Every parser MUST have roundtrip tests (parse -> export -> reparse = equivalent tree)
- Every operation MUST have tests verifying no data loss (unique URL count preserved)
- Real-world bookmark files from the `/test-fixtures/` directory MUST be used in integration tests

**Rationale:**
Bookmark files represent years of accumulated user data. Data loss is unacceptable. Test-first development ensures correctness and prevents regressions, especially for the many edge cases in browser-exported HTML.

**Exceptions:**
- Exploratory spike code (must be discarded, not merged)
- CLI glue code connecting tested components (must still have e2e tests)

## Article III: Simplicity Enforcement

**Rules:**
- The project MUST be a single Python package — no monorepo, no microservices, no separate frontend
- Favor flat module structure over deep nesting — no more than 3 directory levels under `src/`
- Three similar lines of code are better than a premature abstraction
- No class hierarchies deeper than 2 levels; prefer composition and protocols over inheritance
- No design patterns unless they solve a concrete, present problem (not a hypothetical future one)
- Configuration MUST work with zero config files — TOML config is optional enhancement, not required
- Built-in folder profiles MUST ship as a Python dict in source code, not a separate file that can go missing

**Rationale:**
Over-engineering kills open-source projects. Users read the source. Contributors need to understand the codebase quickly. A simple tool that works reliably is better than an elegant architecture that is hard to debug.

**Exceptions:**
- The plugin system (entry points) is justified complexity because it enables community classifiers without forking
- The parser/exporter abstraction is justified because three genuinely different formats exist

## Article IV: Non-Destructive Operation & Data Safety

**Rules:**
- The tool is strictly NON-DESTRUCTIVE — it MUST NEVER modify, overwrite, or delete the input file under any circumstances
- Output MUST always be written to a separate file (default: `<input>_cleaned.<ext>`, or explicit `--output` path)
- The original input file MUST remain byte-for-byte identical after the tool runs
- The tool MUST preserve every unique URL from input to output — URL count validation SHALL run automatically after every pipeline execution and report the result to the user
- `--dry-run` MUST be the encouraged default workflow — documentation and help text SHOULD suggest running with `--dry-run` first
- `--dry-run` MUST accurately reflect what the real run would produce
- The tool MUST NOT make network requests unless the user explicitly invokes a network feature (`--check-links`, `--strategy llm`)
- No telemetry, analytics, or data collection of any kind — EVER
- LLM classification (when used) MUST send only bookmark titles and URLs — never icons, file paths, or system information
- API keys MUST be read from environment variables, never stored in config files
- The tool MUST NOT write to any location outside the explicitly specified output path — no temp files in system directories, no hidden caches, no state files

**Rationale:**
Users are trusting this tool with their complete browsing history — often the only copy they have. One bad run that corrupts or deletes bookmarks destroys trust permanently. Non-destructive, local-first, privacy-respecting behavior is the core promise of this tool.

**Exceptions:**
- None. Data safety has no exceptions.

## Article V: No Formal Performance SLAs

**Rules:**
- The tool SHOULD process typical bookmark files (under 5,000 bookmarks) in a few seconds — no formal SLA required
- Performance optimization SHOULD NOT be pursued unless a real user reports a problem with a real file
- Algorithmic complexity SHOULD be reasonable (no O(n^3) operations on bookmark lists) but micro-optimization is prohibited
- Dead link checking MAY be slow (network-bound) — this is expected and acceptable

**Rationale:**
This is a CLI tool users run once or twice a year. Startup time, memory usage, and throughput are not critical. Correctness and simplicity always win over performance.

**Exceptions:**
- If profiling reveals a specific bottleneck causing >30 second processing on a 10,000-bookmark file, targeted optimization is permitted

## Article VI: Technology Constraints

**Rules:**
- Language: Python 3.10+ (for broad compatibility with `match` statements, union types, and ParamSpec)
- CLI framework: Typer (type-hint driven, auto-completion, minimal boilerplate)
- Terminal output: Rich (colored output, tables, trees, progress indicators)
- TOML parsing: tomli (backport for 3.10; stdlib tomllib for 3.11+)
- HTML parsing: stdlib `html.parser.HTMLParser` — no BeautifulSoup, no lxml, no external HTML parsers
- HTTP (optional): httpx for async dead link checking — declared as pip extra
- LLM (optional): anthropic/openai SDKs — declared as pip extra
- Testing: pytest + pytest-cov
- Linting: ruff (replaces flake8, isort, black)
- Type checking: mypy in strict mode
- Packaging: pyproject.toml with hatchling
- The project MUST NOT depend on Node.js, Rust, C extensions, or any non-Python tooling at runtime

**Rationale:**
Python stdlib has everything needed for HTML parsing and file I/O. External HTML parsers (BeautifulSoup, lxml) are overkill for the well-structured Netscape bookmark format and add heavy dependencies. Typer + Rich provide excellent CLI UX with minimal code.

**Exceptions:**
- None for core dependencies. Optional extras may use additional Python packages.

## Article VII: Immutable Data Model

**Rules:**
- Bookmark tree nodes MUST be immutable (frozen dataclasses or equivalent)
- Operations MUST return new trees, never mutate existing ones
- Every operation MUST produce a structured change log alongside the new tree
- The change log is what powers `--dry-run` — no separate "preview" code path

**Rationale:**
The ad-hoc scripts that preceded this project mutated trees in place, making it impossible to preview changes or debug incorrect results. Immutability makes operations composable, testable, and previewable for free.

**Exceptions:**
- Internal builder patterns during parsing may use mutable state, but MUST produce an immutable tree as output

## Article VIII: Browser Compatibility

**Rules:**
- Netscape HTML output MUST import successfully into Chrome, Firefox, Edge, and Brave without errors or data loss
- The tool MUST preserve all standard bookmark attributes (HREF, ADD_DATE, ICON, LAST_MODIFIED)
- HTML entities MUST be properly escaped in output (&amp;, &lt;, &gt;, &quot;)
- Output MUST use consistent 4-space indentation
- The tool MUST handle malformed input gracefully with clear error messages rather than crashes

**Rationale:**
The entire value proposition depends on clean import into the user's browser. If the output file fails to import, the tool is useless regardless of how well it deduplicates.

**Exceptions:**
- Browser-specific non-standard attributes (e.g., Edge's PERSONAL_TOOLBAR_FOLDER) SHOULD be preserved but are not guaranteed across format conversions

## Amendment Process

Constitutional amendments require:
1. Written proposal with rationale
2. Impact analysis on existing specifications and implementations
3. Maintainer review and approval
4. Version bump (MAJOR for breaking changes, MINOR for additions, PATCH for clarifications)
5. Update to all affected spec-kit artifacts

## Compliance Validation

All specifications and implementation plans MUST validate against this constitution before execution. Use `/speckit-analyze` to verify compliance.
