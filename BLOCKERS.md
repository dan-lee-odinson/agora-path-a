# Blockers

> **Naming history:** this project was working-named AGORA during early development; renamed to ISONOMIA (The Isonomia Commons) in July 2026 due to a namespace collision. References to AGORA below are historical provenance and are preserved intentionally.

Items the build could not resolve autonomously. Per the build directive, nothing here stopped
the run — each item was documented, worked around, and the build continued.

## Open

- **Website publishing is deferred to the human by design (not a build blocker).** The public
  site is staged in `site/` (`index.html`, `polis.html`, `llms.txt`) with all figures updated
  to the final Path A numbers, but **GitHub Pages is intentionally not enabled** and the
  `<!-- PUBLICATION GATE -->` comment is left in place. Two human decisions remain before go-live:
  1. **DOI** — the Zenodo DOI is still "forthcoming"; the last publication-gate box cannot be
     checked until it is minted. Mint it, then update the two `#` DOI placeholders (site footer
     and, if desired, add to the docs).
  2. **Serving topology** — classic GitHub Pages serves only from repo root or `/docs`, not from
     an arbitrary `/site` folder. To publish `site/` either (a) add a Pages GitHub Actions
     workflow that deploys `site/`, or (b) move the three files to the chosen Pages source at
     publish time. Note that `llms.txt` follows the convention of living at the **served root**
     and its `./docs/...` links resolve relative to that root — so whichever source is chosen,
     `docs/` must be reachable as a sibling of `llms.txt` at the served root (a Pages workflow
     can copy `docs/` alongside the site, or the links can be repointed to absolute repo URLs).

## Resolved

- **Spec↔code control-taxonomy divergence (Step 4)** — Launch Spec v0.3.2 §10 mislabeled
  detection-disabled Sybil ring-farming as a positive control; the code correctly treats it as a
  negative control (DECISIONS #35). Resolved in **Launch Spec v0.3.3** §10, which rewrites
  standing rule (a) to classify ring-farming as a negative control (spec corrected in the code's
  favor; no code change). Closed.
- **GitHub authentication** — `gh auth login` was completed after the build finished; the
  repository was then published to <https://github.com/dan-lee-odinson/isonomia-path-a> with the
  full milestone commit history, and PLAN.md was mirrored as issue #1. During the build all
  milestones were committed locally, so no work was lost to the delay.
- *(everything else ran to completion; interpretation calls went to DECISIONS.md rather than
  blocking.)*
