# Project-Specific Rules

This project uses **Specification-Driven Development (SDD)** via spec-kit.

## Workflow

Always follow the spec-kit workflow for new features:

1. `/speckit-specify [N-feature-name]` - Define WHAT to build
2. `/speckit-clarify` - Resolve ambiguities (if needed)
3. `/speckit-plan` - Define HOW to build
4. `/speckit-analyze` - Validate consistency
5. `/speckit-tasks` - Break into tasks
6. `/speckit-implement` - Execute with TDD

See global `spec-driven.md` rule for complete methodology.

## Project Structure

- `.specify/memory/constitution.md` - Project governance
- `.specify/roadmap.md` - Feature roadmap from PRD
- `.specify/specs/[N-feature]/` - Feature specifications

## Key Principles

- Specifications before code
- Tests before implementation (TDD)
- Document all technical decisions in `research.md`
- Validate against constitution at each phase
