# Pull Request Checklist

## 1. Agent/Developer Role
<!-- Check the role that best fits this contribution -->
- [ ] Core Implementation Agent
- [ ] Layout Implementation Agent
- [ ] Renderer Implementation Agent
- [ ] Architecture/Docs Agent
- [ ] Other: ______

## 2. Context
<!-- Link to the issue or describe the task -->
- **Task/Issue**: #
- **Description**: 

## 3. Quality Assurance (Must Pass)
<!-- Ensure these commands run successfully in your local environment before submitting -->
- [ ] `uv run ruff check src tests` (Linting passed)
- [ ] `uv run mypy src` (Type check passed)
- [ ] `uv run pytest` (All tests passed, or xfail is expected)

## 4. Documentation
- [ ] `AGENTS.md` updated (if architectural changes were made)
- [ ] `docs/` updated (if design specs were changed)
- [ ] `project_state` / `bound_phase` impacted? (yes/no)

## 5. Architecture Compliance
<!-- Refer to AGENTS.md Section 3 -->
- [ ] No cross-layer violations (e.g., Model depending on Renderer)
- [ ] Ops protocol followed (Model only produces Ops, Layout injects Pos)
