# Task Breakdown: [FEATURE_NAME]

**Feature Number:** [N]
**Plan:** [Link to plan.md]
**Generated:** [YYYY-MM-DD]
**Status:** Not Started | In Progress | Completed

## Task Format

Every task MUST follow this strict checklist format:

```text
- [ ] [TaskID] [P?] [Story?] Description with file path
```

**Components:**
1. **Checkbox**: Always `- [ ]` (mark `- [X]` when completed)
2. **Task ID**: Sequential (T001, T002, T003...) in execution order
3. **[P] marker**: Include ONLY if parallelizable (different files, no dependencies)
4. **[Story] label**: REQUIRED for user story phases (`[US1]`, `[US2]`, etc.)
5. **Description**: Clear action with exact file path

---

## Phase 1: Setup

- [ ] T001 Create project structure per implementation plan
- [ ] T002 [P] Configure development environment and dependencies
- [ ] T003 [P] Initialize database schema from data-model.md

---

## Phase 2: Foundational (blocking prerequisites)

- [ ] T004 [P] Set up test framework and utilities in tests/
- [ ] T005 [P] Create shared types/interfaces in src/types/
- [ ] T006 Configure CI/CD pipeline for automated testing

---

## Phase 3: User Story 1 — [US1 Title] (P1)

**Story Goal:** [What this user story achieves]
**Independent Test Criteria:** [How to verify this story works in isolation]

- [ ] T007 [US1] Create [Entity] model in src/models/[entity].py
- [ ] T008 [P] [US1] Create [Entity]Service in src/services/[entity]_service.py
- [ ] T009 [US1] Implement [endpoint] in src/routes/[resource].py
- [ ] T010 [US1] Write integration tests for [US1] in tests/test_[feature].py

---

## Phase 4: User Story 2 — [US2 Title] (P2)

**Story Goal:** [What this user story achieves]
**Independent Test Criteria:** [How to verify this story works in isolation]

- [ ] T011 [P] [US2] Create [Entity2] model in src/models/[entity2].py
- [ ] T012 [P] [US2] Create [Entity2]Service in src/services/[entity2]_service.py
- [ ] T013 [US2] Implement [endpoint] in src/routes/[resource2].py
- [ ] T014 [US2] Write integration tests for [US2] in tests/test_[feature2].py

---

## Phase 5: User Story 3 — [US3 Title] (P3)

[Continue pattern for all user stories from spec.md...]

---

## Final Phase: Polish & Cross-Cutting Concerns

- [ ] T0XX Run `/code-review` on all implemented code
- [ ] T0XX Run `/security-review` on authentication and sensitive code
- [ ] T0XX Verify test coverage ≥ 80% with `/test-coverage`
- [ ] T0XX Create E2E tests for critical user flows with `/e2e`
- [ ] T0XX Performance testing and optimization
- [ ] T0XX Documentation and deployment preparation

---

## Dependencies

### Story Completion Order
```
Phase 1 (Setup) → Phase 2 (Foundational) → Phase 3 (US1) → Phase 4 (US2) → ...
```

### Parallel Opportunities per Story
- **US1**: T007 and T008 can run in parallel (different files)
- **US2**: T011 and T012 can run in parallel (different files)
- **Across stories**: US2 can start if US1 is NOT a dependency

---

## Implementation Strategy

### MVP First (Recommended)
Implement User Story 1 (Phase 3) first as MVP:
1. Complete Phase 1 + Phase 2
2. Implement Phase 3 (US1 only)
3. Validate MVP works end-to-end
4. Continue with remaining stories

### Incremental Delivery
Each user story phase produces a complete, independently testable increment.

---

## Summary

### Metrics
- **Total Tasks:** [count]
- **Tasks per Story:** US1: [N], US2: [N], US3: [N]
- **Parallel Opportunities:** [count]

### Quality Gates
- [ ] All tasks in strict checklist format (checkbox, ID, labels, file paths)
- [ ] Story-based organization (primary axis)
- [ ] Each story is independently testable
- [ ] Parallelization marked with [P]
- [ ] All tests written before implementation (TDD)
- [ ] 80%+ test coverage maintained

### Notes

**Task Completion:** Mark tasks as `- [X]` in this file when completed during `/speckit-implement`.

**Story Independence:** Most user stories should be implementable independently. If a story depends on another, document the dependency explicitly.
