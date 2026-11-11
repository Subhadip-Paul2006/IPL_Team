# Scope: Git Commit All Uncommitted Files Separately, Push, and Create Pull Request

## Architecture
- Repository: https://github.com/Subhadip-Paul2006/IPL_Team
- Current Branch: docs/v2.2.0-pvre-dual-mode
- Base Branch: main
- User GPG pin: Shubh06
- Git Tooling: git, gpg, gh CLI
- Remote: origin (https://github.com/Subhadip-Paul2006/IPL_Team.git)

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Working Tree & Uncommitted Files Audit | Enumerate all uncommitted files, inspect git status, diffs, and verify GPG key & agent setup | M1 | ORIGINAL_REQUEST R1 |
| 2 | Separate GPG-Signed Commits | Commit all uncommitted files separately (1 commit per file) signed with GPG pin Shubh06 | M1 | ORIGINAL_REQUEST R1 |
| 3 | Push to Remote Branch | Push local branch docs/v2.2.0-pvre-dual-mode to origin/docs/v2.2.0-pvre-dual-mode | M1 | ORIGINAL_REQUEST R2 |
| 4 | Open Production Pull Request | Create PR from docs/v2.2.0-pvre-dual-mode to main using gh CLI with descriptive title and body | M1 | ORIGINAL_REQUEST R3 |
| 5 | Clean Working Tree & Verification | Verify git status --porcelain is empty, git log --show-signature confirms GPG signatures, and gh pr view confirms open PR | M1 | Acceptance Criteria |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Git Commit, Push & PR | Audit uncommitted files, commit separately with GPG signature (pin Shubh06), push to remote, and open PR | none | IN_PROGRESS |
