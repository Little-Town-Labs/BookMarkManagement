# Implementation Plan: [FEATURE_NAME]

**Feature Number:** [N]
**Specification:** [Link to spec.md]
**Created:** [YYYY-MM-DD]
**Last Updated:** [YYYY-MM-DD]

## Executive Summary

[Brief overview of the technical approach chosen to implement this feature]

## Technical Context

Evaluate the current state of knowledge for implementation. Mark unknowns:

- [ ] Language/runtime: [Known | NEEDS CLARIFICATION]
- [ ] Primary framework: [Known | NEEDS CLARIFICATION]
- [ ] Database/storage: [Known | NEEDS CLARIFICATION]
- [ ] Authentication: [Known | NEEDS CLARIFICATION]
- [ ] Deployment target: [Known | NEEDS CLARIFICATION]
- [ ] External integrations: [Known | NEEDS CLARIFICATION]
- [ ] Testing framework: [Known | NEEDS CLARIFICATION]

## Constitution Check

Validate plan against project constitution (`/memory/constitution.md`):

- [ ] All MUST principles satisfied
- [ ] No principle violations without documented justification
- [ ] Technology choices align with constitutional constraints

**Gate Status:** PASS | ERROR (if violations, document in Complexity Tracking below)

## Architecture Overview

### System Components
```
[ASCII diagram or description of major components]
```

### Technology Stack
- **Frontend:** [Framework, libraries]
- **Backend:** [Framework, language, runtime]
- **Database:** [Database system, ORM]
- **Infrastructure:** [Hosting, services]

**Rationale:** [Why these technologies were chosen]

## Technical Decisions

### Decision 1: [Technology/Approach Choice]
**Context:** [What decision needed to be made]

**Options Considered:**
1. **Option A:** [Description]
   - Pros: [Advantages]
   - Cons: [Disadvantages]
2. **Option B:** [Description]
   - Pros: [Advantages]
   - Cons: [Disadvantages]

**Chosen:** Option [A/B]
**Rationale:** [Why this was chosen]
**Tradeoffs:** [What we're accepting]

### Decision 2: [Another Decision]
[Continue for all major technical decisions...]

## Data Model

See `data-model.md` for complete database schema.

**Key Entities:**
- **[Entity 1]:** [Purpose, key attributes]
- **[Entity 2]:** [Purpose, key attributes]

**Relationships:**
- [Entity 1] → [Entity 2]: [Relationship type and rationale]

## API Design

See `contracts/` directory for complete API specifications.

### Endpoints Overview

**Authentication & Authorization:**
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/refresh` - Token refresh

**[Feature Area 1]:**
- `GET /api/[resource]` - List resources
- `POST /api/[resource]` - Create resource
- `GET /api/[resource]/:id` - Get resource
- `PUT /api/[resource]/:id` - Update resource
- `DELETE /api/[resource]/:id` - Delete resource

## Phase 0: Research & Unknowns

Resolve all NEEDS CLARIFICATION items from Technical Context before design.

### Research Tasks
For each unknown:
1. **[Unknown 1]:** Research [topic] for [feature context]
2. **[Unknown 2]:** Find best practices for [tech] in [domain]

### Research Findings
See `research.md` for complete findings in Decision/Rationale/Alternatives format.

**Status:** All unknowns resolved | [N] remaining

## Phase -1: Pre-Implementation Gates

Constitutional enforcement checkpoints. Gate failures require documented justification.

### Simplicity Gate (Article VII)
- [ ] Solution uses ≤3 projects/packages?
- [ ] No speculative future-proofing?
- [ ] Complexity justified by current requirements?

### Anti-Abstraction Gate (Article VIII)
- [ ] Using framework features directly (no unnecessary wrappers)?
- [ ] Single model representation (no redundant DTOs)?
- [ ] No premature abstraction layers?

### Integration-First Gate (Article IX)
- [ ] Interface contracts defined in `contracts/`?
- [ ] Contract tests planned (not just unit tests)?
- [ ] Integration points documented?

**Gate Status:** PASS | FAIL (see Complexity Tracking)

## Complexity Tracking

Document any gate failures or constitutional exceptions here:

### Exception 1: [Gate that failed]
**Principle:** [Which constitutional article]
**Justification:** [Why this exception is necessary]
**Mitigation:** [How complexity is managed]

---

## Implementation Phases

### Phase 1: Foundation
**Duration:** [Estimated time]
**Goals:**
- Set up project structure
- Configure development environment
- Implement data models
- Create database migrations

**Deliverables:**
- Database schema implemented
- Basic project skeleton
- Development environment documented

### Phase 2: Core Functionality
**Duration:** [Estimated time]
**Goals:**
- Implement core business logic
- Create API endpoints
- Write comprehensive tests

**Deliverables:**
- All API endpoints functional
- 80%+ test coverage
- Unit and integration tests passing

### Phase 3: Integration & Polish
**Duration:** [Estimated time]
**Goals:**
- Frontend integration
- Error handling
- Performance optimization

**Deliverables:**
- Complete feature working end-to-end
- Error handling comprehensive
- Performance requirements met

## Security Considerations

### Authentication & Authorization
- [How authentication is implemented]
- [Authorization strategy]
- [Token/session management]

### Data Protection
- [Encryption at rest]
- [Encryption in transit]
- [Sensitive data handling]

### Input Validation
- [Validation strategy]
- [SQL injection prevention]
- [XSS prevention]

### OWASP Top 10 Mitigation
- [How each OWASP risk is addressed]

## Performance Strategy

### Caching
- **What:** [What data is cached]
- **Where:** [Caching layer]
- **TTL:** [Cache expiration]

### Database Optimization
- **Indexes:** [Key indexes]
- **Query Optimization:** [Strategy]
- **Connection Pooling:** [Configuration]

### Scalability
- **Horizontal Scaling:** [How]
- **Load Balancing:** [Strategy]
- **Rate Limiting:** [Approach]

## Error Handling & Monitoring

### Error Handling
- **Client Errors (4xx):** [How handled]
- **Server Errors (5xx):** [How handled]
- **External Service Failures:** [Fallback strategy]

### Monitoring & Logging
- **Metrics:** [What to monitor]
- **Logging:** [What to log, log levels]
- **Alerting:** [Alert conditions]

## Testing Strategy

### Unit Tests
- **Coverage Target:** 80%+
- **Framework:** [Testing framework]
- **Focus Areas:** [What to test]

### Integration Tests
- **Approach:** [Integration testing strategy]
- **External Services:** [How to handle]

### End-to-End Tests
- **Critical Flows:** [User journeys to test]
- **Framework:** [E2E testing tool]

## Deployment Strategy

### Environments
- **Development:** [Setup]
- **Staging:** [Setup]
- **Production:** [Setup]

### CI/CD Pipeline
1. Code commit
2. Run tests (unit, integration)
3. Build artifacts
4. Deploy to staging
5. Run E2E tests
6. Manual approval
7. Deploy to production

### Rollback Plan
[How to rollback if deployment fails]

## Dependencies

### External Dependencies
- [Library/Service 1]: [Version, purpose]
- [Library/Service 2]: [Version, purpose]

### Internal Dependencies
- [Other feature/system]: [What we depend on]

## Risks & Mitigation

### Risk 1: [Description]
**Probability:** High | Medium | Low
**Impact:** High | Medium | Low
**Mitigation:** [How to reduce or handle this risk]

### Risk 2: [Description]
[Continue for all identified risks...]

## Constitutional Compliance

### Compliance Check
- [x] Test-first imperative followed
- [x] Simplicity enforced (no over-engineering)
- [x] Security standards met
- [x] Performance requirements addressed
- [x] Technology constraints respected

### Exceptions
[Document any constitutional exceptions with justification]

## Next Steps

1. Review and approve this plan
2. Generate task breakdown (`/speckit-tasks`)
3. Validate with `/speckit-analyze`
4. Begin implementation (`/speckit-implement`)

## References

- [Link to specification]
- [Link to research]
- [Link to design documents]
- [Link to API contracts]
