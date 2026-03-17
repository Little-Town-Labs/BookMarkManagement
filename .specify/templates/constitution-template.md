# Project Constitution

**Version:** 1.0.0
**Ratified:** [YYYY-MM-DD]
**Last Amended:** [YYYY-MM-DD]

## Preamble

This constitution establishes the foundational principles and architectural constraints for [PROJECT_NAME]. These principles are immutable unless explicitly amended through formal review.

## Article I: [PRINCIPLE_NAME]

**Rules:**
- [SPECIFIC RULE 1]
- [SPECIFIC RULE 2]
- [SPECIFIC RULE 3]

**Rationale:**
[Why this principle exists and what problems it prevents]

**Exceptions:**
[Documented exceptions to this principle, if any]

## Article II: Test-First Imperative

**Rules:**
- No implementation code shall be written before unit tests exist
- Tests must be validated and approved before implementation
- Tests must be confirmed to FAIL before writing implementation code
- Minimum 80% code coverage required for all features

**Rationale:**
Test-first development ensures code correctness, prevents regressions, and serves as living documentation. It forces thinking about interfaces and edge cases before implementation.

**Exceptions:**
- Exploratory spike code (must be discarded, not merged)
- Generated code from proven templates (must still have tests)

## Article III: Simplicity Enforcement

**Rules:**
- Favor minimal complexity over anticipated future needs
- Additional projects require documented justification
- Use framework features directly; avoid unnecessary abstraction
- Three or fewer projects until clear need for more

**Rationale:**
Over-engineering creates maintenance burden, cognitive overhead, and deployment complexity. Start simple, refactor when genuinely needed.

**Exceptions:**
[Document when added complexity is justified]

## Article IV: Security Standards

**Rules:**
- [SECURITY REQUIREMENT 1]
- [SECURITY REQUIREMENT 2]
- [COMPLIANCE REQUIREMENT]

**Rationale:**
[Security and compliance requirements]

## Article V: Performance Requirements

**Rules:**
- [PERFORMANCE SLA 1]
- [PERFORMANCE SLA 2]
- [SCALABILITY REQUIREMENT]

**Rationale:**
[Why these performance requirements matter]

## Article VI: Technology Constraints

**Rules:**
- [APPROVED TECHNOLOGY 1]
- [APPROVED TECHNOLOGY 2]
- [PROHIBITED TECHNOLOGY AND WHY]

**Rationale:**
[Why these technology choices were made]

## Amendment Process

Constitutional amendments require:
1. Written proposal with rationale
2. Impact analysis on existing specifications
3. Team review and approval
4. Version bump (MAJOR for breaking changes, MINOR for additions)
5. Update to all affected artifacts

## Compliance Validation

All specifications and implementation plans must validate against this constitution before execution. Use `/speckit-analyze` to verify compliance.
