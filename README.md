# isonomia-path-a

[![Software DOI](https://img.shields.io/badge/Software%20DOI-10.5281%2Fzenodo.21287288-1682D4.svg)](https://doi.org/10.5281/zenodo.21287288)
[![Preprint DOI](https://img.shields.io/badge/Preprint%20DOI-10.5281%2Fzenodo.21338480-B31B1B.svg)](https://doi.org/10.5281/zenodo.21338480)

**Agent-based simulation of the ISONOMIA Tier-1 launch economics** — Path A of the staged build
plan: validate the mutual-credit exchange design against its kill criteria *before* any
contract is written.

ISONOMIA is a constitutional design for an autonomous-agent labor exchange: a mutual-credit unit
("ergs") that exists only when work is demanded and settled, Harberger-priced listings,
non-transferable reputation, and self-governing institutions. This repository simulates the
Tier-1 launch economy (one mechanically-verified code-task category) and asks the five
questions the launch spec exists to answer — supply stability, Harberger convergence, fee
convergence, attack survival, and parameter calibration.

## Spec of record

The four frozen baseline documents in [docs/](docs/) are the authority for every mechanism here:

| Document | Role |
|---|---|
| [Path A Simulation Plan v0.1.2](docs/ISONOMIA_PathA_Simulation_Plan_v0.1.2.md) | Primary build spec: modules, agents, sweeps, attack scenarios |
| [Tier-1 Launch Spec v0.3.4](docs/ISONOMIA_Tier1_Launch_Spec_v0.3.4.md) | Contract-level rules; parameter registry (§8); implementation clarifications (§13); its Conflict Register governs conflicts. §10 codifies this repo's v3 kill-criterion formulation and names [killcriteria.py](src/isonomia/killcriteria.py) authoritative |
| [Whitepaper v0.6.3](docs/ISONOMIA_Whitepaper_v0.6.3.md) | Constitutional design rationale |
| [Feasibility Assessment](docs/ISONOMIA_Feasibility_Assessment.md) | Scope discipline: this is Path A only |

Where the specs are ambiguous, [DECISIONS.md](DECISIONS.md) records the interpretation and the
section it interprets. [PLAN.md](PLAN.md) is the implementation plan; [BLOCKERS.md](BLOCKERS.md)
records anything unresolved.

## Quick start

```powershell
# one-time setup
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# run the test suite (73 tests: ledger/escrow invariants, mechanism rules, determinism)
.\.venv\Scripts\python.exe -m pytest

# run the honest baseline (26 epochs, deterministic under the config's seed)
.\.venv\Scripts\python.exe run.py configs\baseline.yaml

# run one attack scenario, or all seven (Sim Plan §5)
Set-Location scenarios
..\.venv\Scripts\python.exe s1_wash_rush.py
..\.venv\Scripts\python.exe run_all.py
Set-Location ..

# smoke parameter sweep (~10 min on 16 cores; see CALIBRATION.md for the full sweep)
.\.venv\Scripts\python.exe sweep\run_sweep.py sweep\smoke.yaml
```

Outputs land in `results/<run_name>/` — per-epoch `epochs.csv`, event-level `events.jsonl`,
and `summary.md` / `summary.json` with the Sim Plan §6 metrics and the Launch Spec §10
kill-criteria verdict. Scenario reports land in `results/scenario_reports/`, sweep reports in
`results/sweep_reports/` (both committed).

## Repository layout

```
docs/          the four baseline documents (spec of record)
src/isonomia/     simulation modules, one per launch-spec contract (see PLAN.md)
scenarios/     the 7 scripted attacks from Sim Plan §5
sweep/         Latin-hypercube parameter sweep runner
tests/         invariant + mechanism test suite
configs/       baseline.yaml = Launch Spec §8 center values
results/       run outputs (per-epoch logs gitignored; summaries committed)
```

## Status

All six build milestones complete: monetary core with exact-integer zero-sum invariants,
full market/institution organs, the Sim Plan §3 behavior-policy population, all seven §5
attack scenarios with leakage reports, and the §4 Latin-hypercube sweep machinery with an
executed smoke sweep. See [CALIBRATION.md](CALIBRATION.md) for what the smoke sweep shows
and how to launch the full sweep; [DECISIONS.md](DECISIONS.md) for every interpretation the
specs left open (36 entries, each citing its governing section).

## Versioning, licensing & citation

Current repository documents: **Whitepaper v0.6.3**, **Tier-1 Launch Spec v0.3.4**, **Path A Simulation Plan v0.1.2**. See [VERSION_MANIFEST.md](VERSION_MANIFEST.md) for the full version and DOI scheme — the two separate tracks (living-repository versions vs. frozen DOI artifacts) and which identifier cites what.

**Licensing is split by content type** (see [LICENSE-DOCS](LICENSE-DOCS) for the file-level split):

- Prose, whitepaper, specifications, research documentation, simulation data, and generated results → **CC BY 4.0**.
- Software and executable code → **Apache License 2.0** (see [LICENSE](LICENSE)).

The archived software record therefore contains mixed-license material; `LICENSE-DOCS` controls the file-level split that the single Zenodo license field cannot express.

**DOIs** (distinct roles — see the manifest):

- Software concept DOI [10.5281/zenodo.21287288](https://doi.org/10.5281/zenodo.21287288) — the repository/software archive; resolves to the latest software release.
- Preprint concept DOI [10.5281/zenodo.21338480](https://doi.org/10.5281/zenodo.21338480) — the scholarly preprint, for citation.
- Exact v1.1.0 repository release DOI: [10.5281/zenodo.21348073](https://doi.org/10.5281/zenodo.21348073).
