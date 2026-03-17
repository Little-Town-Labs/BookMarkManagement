# [CHECKLIST_TYPE] Checklist: [FEATURE_NAME]

**Feature Number:** [N]
**Type:** [domain].md (e.g., ux.md, api.md, security.md, performance.md)
**Created:** [YYYY-MM-DD]
**Feature:** [Link to spec.md]

## Purpose: Unit Tests for Requirements

**CRITICAL CONCEPT**: Checklists are **UNIT TESTS FOR REQUIREMENTS WRITING** — they validate the quality, clarity, and completeness of requirements in a given domain.

If your spec is code written in English, this checklist is its unit test suite. You're testing whether the *requirements* are well-written, complete, unambiguous, and ready for implementation — NOT whether the *implementation* works.

---

## Quality Dimensions

Items are organized by requirement quality dimension:

### Requirement Completeness
Are all necessary requirements present?

- [ ] CHK001 - Are [requirement type] defined for all [scenarios]? [Completeness, Spec §X.Y]
- [ ] CHK002 - Are [edge case] requirements documented? [Gap]
- [ ] CHK003 - Are error handling requirements defined for all failure modes? [Completeness]

### Requirement Clarity
Are requirements unambiguous and specific?

- [ ] CHK004 - Is '[vague term]' quantified with specific criteria? [Clarity, Spec §X.Y]
- [ ] CHK005 - Are '[ambiguous adjective]' requirements measurable? [Ambiguity, Spec §X.Y]

### Requirement Consistency
Do requirements align without conflicts?

- [ ] CHK006 - Do [area] requirements align across all [sections]? [Consistency, Spec §X.Y]
- [ ] CHK007 - Are [component] requirements consistent between [section A] and [section B]? [Consistency]

### Acceptance Criteria Quality
Are success criteria measurable?

- [ ] CHK008 - Can [requirement] be objectively measured/verified? [Measurability, Spec §X.Y]
- [ ] CHK009 - Are success criteria technology-agnostic? [Acceptance Criteria]

### Scenario Coverage
Are all flows/cases addressed?

- [ ] CHK010 - Are requirements defined for [primary scenario]? [Coverage]
- [ ] CHK011 - Are [alternate flow] scenarios addressed? [Coverage, Gap]
- [ ] CHK012 - Are requirements specified for [error/exception] scenarios? [Coverage, Exception Flow]
- [ ] CHK013 - Are [recovery/rollback] requirements defined? [Coverage, Recovery]

### Edge Case Coverage
Are boundary conditions defined?

- [ ] CHK014 - Are requirements defined for zero-state scenarios? [Edge Case, Gap]
- [ ] CHK015 - Are concurrent user interaction scenarios addressed? [Edge Case]

### Non-Functional Requirements
Are performance, security, accessibility specified?

- [ ] CHK016 - Are performance requirements quantified with specific metrics? [Clarity]
- [ ] CHK017 - Are security requirements specified for all protected resources? [Coverage]
- [ ] CHK018 - Are accessibility requirements defined for interactive UI? [Gap]

### Dependencies & Assumptions
Are they documented and validated?

- [ ] CHK019 - Are external dependency requirements documented? [Dependency, Gap]
- [ ] CHK020 - Are assumptions explicitly stated and validated? [Assumption]

---

## Writing Checklist Items

### Required Patterns
- "Are [requirement type] defined/specified/documented for [scenario]?"
- "Is [vague term] quantified/clarified with specific criteria?"
- "Are requirements consistent between [section A] and [section B]?"
- "Can [requirement] be objectively measured/verified?"
- "Does the spec define [missing aspect]?"

### Prohibited Patterns (these test implementation, NOT requirements)
- "Verify the button clicks correctly"
- "Test error handling works"
- "Confirm the API returns 200"
- "Check that the component renders"
- Any item starting with "Verify", "Test", "Confirm", "Check" + implementation behavior

### Traceability Requirements
- MINIMUM: ≥80% of items MUST include at least one traceability reference
- Reference spec sections: `[Spec §X.Y]`
- Use markers: `[Gap]`, `[Ambiguity]`, `[Conflict]`, `[Assumption]`

### Content Consolidation
- Soft cap: If raw candidate items > 40, prioritize by risk/impact
- Merge near-duplicates checking the same requirement aspect
- If >5 low-impact edge cases, create one item: "Are edge cases X, Y, Z addressed? [Coverage]"

---

## File Handling

- **New file**: Create and number items starting from CHK001
- **Existing file**: Append new items, continuing from last CHK ID
- **Never** delete or replace existing checklist content — always preserve and append
- Use short, descriptive filenames: `ux.md`, `api.md`, `security.md`, `performance.md`

---

## Sign-Off

**Reviewer:** [Name]
**Date:** [YYYY-MM-DD]
**Status:** PASS | FAIL

**Notes:**
[Reviewer comments]

---

## Remediation

If checklist items fail, document remediation:

### Failed Items
1. [CHK###]: [Reason — what's missing or unclear in the spec]

### Remediation Plan
1. [Action to improve the specification]

### Target
**Completion:** [Date]
