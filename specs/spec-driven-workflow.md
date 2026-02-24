# Spec-Driven Workflow

## Status

Draft

## Overview

Establish a spec-driven development workflow where every feature begins with a written spec in `specs/`
before any code is written. The spec acts as the single source of truth for requirements, design
decisions, and acceptance criteria throughout the feature lifecycle.

## Goals

- Ensure features are well-understood before implementation begins
- Provide a lightweight paper trail for architectural decisions
- Make acceptance criteria explicit and testable
- Reduce back-and-forth during code review by aligning on intent upfront

## Workflow

```
1. Create a branch:  feat/<feature-name>
2. Add a spec file:  specs/<feature-name>.md  (Status: Draft)
3. Review and agree on the spec before writing any code
4. Implement against the spec
5. Update spec status → Implemented
6. Open PR — spec is included in the diff for reviewers
```

## Spec File Structure

Every spec in `specs/` must include:

| Section | Description |
|---|---|
| **Status** | `Draft` → `Agreed` → `Implemented` |
| **Overview** | One paragraph summary of what and why |
| **Goals** | Bullet list of outcomes |
| **Non-goals** | What is explicitly out of scope |
| **Design** | Key decisions, data flow, API surface changes |
| **Acceptance criteria** | Testable conditions that define done |
| **Open questions** | Unresolved decisions (cleared before `Agreed`) |

## Non-goals

- This workflow does not replace in-code documentation or tests
- Specs are not user-facing documents — they can be informal
- No tooling enforcement in CI (at least initially)

## Acceptance Criteria

- [ ] `specs/` directory exists at the repo root
- [ ] This spec file is merged into `main` on the feature branch
- [ ] `CLAUDE.md` references the spec workflow so it is followed in future sessions
- [ ] A spec template is available for reuse

## Open Questions

- Should spec status be enforced in CI (e.g. no `Draft` specs on `main`)?
- Should specs be linked from PR descriptions?
