# Version Manifest — The Isonomia Commons

This project maintains **two deliberately separate version tracks**: a *living repository* that evolves, and *frozen DOI artifacts* that do not. They are different objects with different identifiers. This manifest exists so that a living-repository version (e.g. whitepaper v0.6.3) is never mistaken for an obsolete copy of a frozen preprint snapshot (v1.0).

## The two tracks

**Living repository (this repo).** Working specifications under continuous revision. Point-versioned; each release is tagged. These are the authoritative *current* documents.

**Frozen DOI artifacts (Zenodo).** Citable snapshots that never change after minting. A frozen artifact may embed a living document at the version current when the artifact was cut; that embedded version does not advance when the repository does.

## Current versions

| Object | Version | Track | Identifier |
|---|---|---|---|
| Repository whitepaper | v0.6.3 | Living | identified by the repository release DOI (whole release): [10.5281/zenodo.21348073](https://doi.org/10.5281/zenodo.21348073) (v1.1.0) |
| Repository launch spec | v0.3.4 | Living | identified by the repository release DOI (whole release): [10.5281/zenodo.21348073](https://doi.org/10.5281/zenodo.21348073) (v1.1.0) |
| Repository simulation plan | v0.1.2 | Living | identified by the repository release DOI (whole release): [10.5281/zenodo.21348073](https://doi.org/10.5281/zenodo.21348073) (v1.1.0) |
| Repository calibration record | (tracks release) | Living | pinned to release v1.0.0, commit `ba3ddb5` for evidence |
| DOI preprint package | v1.1 | Frozen | version DOI [10.5281/zenodo.21343917](https://doi.org/10.5281/zenodo.21343917) |
| Whitepaper snapshot inside the preprint | v1.0 | Frozen | (embedded in the preprint package) |
| Software project (as a whole) | — | — | concept DOI [10.5281/zenodo.21287288](https://doi.org/10.5281/zenodo.21287288) |
| Software release snapshot | v1.0.0 | Frozen | commit `ba3ddb5`; version DOI [10.5281/zenodo.21287289](https://doi.org/10.5281/zenodo.21287289), under software concept DOI [10.5281/zenodo.21287288](https://doi.org/10.5281/zenodo.21287288) (evidence baseline) |
| Repository documentation release | v1.1.0 | Frozen on release tag | Tag `v1.1.0` (release commit `def8f298625a5be621c8395dce0294a89878f8e7`); version DOI [10.5281/zenodo.21348073](https://doi.org/10.5281/zenodo.21348073), under software concept DOI [10.5281/zenodo.21287288](https://doi.org/10.5281/zenodo.21287288). Documentation and claim-discipline changes only — no code, simulation, data, or results changed. Simulation evidence remains pinned to v1.0.0 / `ba3ddb5`. |

## The DOI scheme (which identifier cites what)

| To cite… | Use | Notes |
|---|---|---|
| The preprint, in general | preprint **concept** DOI `10.5281/zenodo.21338480` | Resolves to the latest preprint version |
| An exact preprint version | that version's DOI (e.g. `10.5281/zenodo.21343917` = v1.1) | Pins wording |
| The software project, in general | software **concept** DOI `10.5281/zenodo.21287288` | Resolves to latest software release |
| Exact code / calibration data | the repository **version** DOI for release `v1.0.0`: [10.5281/zenodo.21287289](https://doi.org/10.5281/zenodo.21287289) (commit `ba3ddb5`) | Pins the executable and data |
| This exact repository whitepaper (v0.6.3) | the repository release DOI for the release containing whitepaper v0.6.3: [10.5281/zenodo.21348073](https://doi.org/10.5281/zenodo.21348073) (v1.1.0) | A release DOI identifies the whole release, not an independently minted whitepaper DOI |

**Why v0.6.3 ≠ v1.0.** The preprint renumbered its embedded snapshot as v1.0, while the repository retained its independent v0.x document sequence. They share ancestry but are different objects: cite the preprint DOI for the frozen scholarly artifact, and — for the living specification — the repository release DOI for the release containing whitepaper v0.6.3.

## Relationship to the corpus

The whitepaper is one member of a corpus on human–machine peership. ISONOMIA is **one implementation hypothesis** within the peership framework; the philosophy neither entails it nor stands or falls with it.

## Licensing

Two licenses apply by content type (see `LICENSE-DOCS`):

- **Prose, whitepaper, specifications, research documentation** → Creative Commons Attribution 4.0 International (CC BY 4.0).
- **Software and executable code** → Apache License 2.0.
