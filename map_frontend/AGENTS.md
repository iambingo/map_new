# MAP Frontend

## Mandatory Intranet Deployment Rules

These rules apply to all development, maintenance, and release tasks in this repository:

1. **Do not modify `package.json` or `package-lock.json`.**
   - The dependency manifest and lockfile are maintained by the frontend deployment team and must remain unchanged.
   - Do not add, remove, upgrade, downgrade, regenerate, format, or otherwise rewrite either file.
   - If a requirement appears to need a new dependency, use the existing dependency set or stop and ask the project owner and frontend deployment team to handle the dependency change.
   - Before delivery, verify that both files have no unintentional Git changes.

2. **Only package files required for the intranet build and runtime.**
   - Source delivery packages must contain the frontend source code, required environment/configuration files, and the existing `package.json` and `package-lock.json`.
   - Exclude files that are not needed by the intranet build or deployed application, including `.git/`, `node_modules/`, `dist/`, `release/`, screenshots, local virtual environments, editor/agent metadata, historical patch directories, old archives, temporary files, test artifacts, and unrelated documentation or reference material.
   - Inspect the archive contents before delivery. The archive root and `relative_path` must place `package.json` where the release pipeline expects it.

## Agent Skills

This project uses [agent-skills](https://github.com/addyosmani/agent-skills) for structured engineering workflows.

**Skills directory:** `agent-skills/skills/` — read the relevant `SKILL.md` when the trigger matches.

### Available Slash Commands

| Command | Purpose |
|---------|---------|
| `/spec` | Define what to build (PRD before code) |
| `/plan` | Break work into small, verifiable tasks |
| `/build` | Implement one slice at a time |
| `/test` | Prove it works with tests |
| `/review` | Code review and quality gate |
| `/code-simplify` | Reduce complexity without changing behavior |
| `/ship` | Ship to production safely |

### Skills by Phase

- **Define:** `spec-driven-development`, `idea-refine`
- **Plan:** `planning-and-task-breakdown`
- **Build:** `incremental-implementation`, `test-driven-development`, `context-engineering`, `source-driven-development`, `frontend-ui-engineering`, `api-and-interface-design`
- **Verify:** `browser-testing-with-devtools`, `debugging-and-error-recovery`
- **Review:** `code-review-and-quality`, `code-simplification`, `security-and-hardening`, `performance-optimization`
- **Ship:** `git-workflow-and-versioning`, `ci-cd-and-automation`, `deprecation-and-migration`, `documentation-and-adrs`, `shipping-and-launch`
