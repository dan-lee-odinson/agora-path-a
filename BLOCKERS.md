# Blockers

Items the build could not resolve autonomously. Per the build directive, nothing here stopped
the run — each item was documented, worked around, and the build continued.

## Open

*(none)*

## Resolved

- **GitHub authentication** — `gh auth login` was completed after the build finished; the
  repository was then published to <https://github.com/dan-lee-odinson/agora-path-a> with the
  full milestone commit history, and PLAN.md was mirrored as issue #1. During the build all
  milestones were committed locally, so no work was lost to the delay.
- *(everything else ran to completion; interpretation calls went to DECISIONS.md rather than
  blocking.)*
