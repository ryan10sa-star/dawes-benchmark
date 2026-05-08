# DAWES Benchmark
### Domain-Adaptive Weights for Expert Systems

**A public benchmark program for industrial instrumentation and controls AI.**

Built by Ryan Anderson — I&C instructor at Bellingham Technical College, with 20 years in oil refining and industrial work.

---

## What DAWES Is

Most public AI benchmarks do not tell you whether a model can safely help with real industrial instrumentation and controls work.

DAWES exists to close that gap. It is designed to measure whether a model can reason about the same material a working I&C technician or engineer needs to understand: loop calibration, process measurement, troubleshooting, control systems, electrical theory, and safety-critical judgment.

If an AI is going to work in industrial environments, it needs to actually know the domain instead of hallucinating standards, procedures, or setpoints. DAWES is how RelayForge intends to prove or disprove that claim.

---

## Benchmark Ladder

DAWES is moving toward a governed benchmark ladder rather than a single exposed score target.

- **Public recurring screen** — controlled public comparison layer
- **Protected 700-bank** — qualification backbone for long-term comparison
- **Protected 560-question expert gate** — harder private promotion test
- **Air-gapped 1000-question final gate** — strongest proof asset

### Why this structure exists

The public screen makes repeated comparisons possible.

The protected 700-bank and 560 gate keep the benchmark from collapsing into a simple tuning target.

The 1000-question air-gapped gate is there so the lab can still ask the hardest question later: is the model genuinely expert-grade, or just optimized toward the visible surface?

---

## Current Public Record

The public DAWES leaderboard should preserve the currently published run history and the last public benchmark runs already made public.

That means:

- preserve published scores carefully
- do not backfill history loosely from memory
- add new results only when run metadata is known
- keep benchmark claims conservative when evidence is incomplete

For the live public page, see: <https://relayforge.tools/dawes/>

---

## Historical v1.x Public Protocol

The currently published DAWES v1.x public record came from the earlier benchmark protocol:

- **560-question protected bank**
- **60-question evaluation sample** drawn at runtime per run
- **5 tiers of difficulty**
  - T1: Recall
  - T2: Comprehension
  - T3: Application
  - T4: Analysis
  - T5: Synthesis

This earlier public run history is still part of the DAWES story and should be preserved as public record rather than overwritten.

---

## Anti-Contamination Protocol

Protected benchmark content is not allowed to enter training or validation corpora.

The benchmark posture is intentionally strict:

1. Fingerprint checks should be run before training exports.
2. Canary strings should remain in use for contamination detection.
3. Any detected overlap between protected benchmark content and training data is a hard stop.
4. Near-duplicate leakage across train, validation, and benchmark lanes is not acceptable.

The benchmark only matters if it remains harder to game than to actually earn.

---

## Publication Standard

A DAWES result should not be published as a serious benchmark result unless the run record includes:

- model name
- model snapshot or provider tag
- benchmark slice used
- run date
- judge method
- scoring rule
- operator notes where relevant

That publication discipline matters because the benchmark is part of the product and trust story, not just an internal toy.

---

## Hardware Context

| Device | Spec | Role |
|--------|------|------|
| RTX 3090 | 24GB VRAM | Primary heavy local training and inference |
| RTX 4060 Ti | 16GB VRAM | Secondary local support |
| Mac Studio M1 Max | 32GB RAM | Orchestration, scoring, lighter support tasks |

---

## Repository Structure

```text
dawes-benchmark/
├── README.md
├── docs/
├── results/
├── scripts/
└── leaderboard.json
```

Treat this repository as benchmark governance and benchmark publication infrastructure, not merely a dump of scores.

---

## Why This Matters

RelayForge wants to build enterprise software powered by a genuinely capable local-first I&C model.

If Dawes reaches the top of this ladder honestly, the benchmark becomes one of the strongest assets behind the product claim. That makes DAWES valuable not just as an evaluation harness, but as a public industrial AI standard people recognize and want to beat.

---

## About

Built by [Ryan Anderson](https://github.com/ryan10sa-star) as part of the [RelayForge](https://relayforge.tools) project.

The trades built everything you're standing in. They deserve AI tools that actually work.
