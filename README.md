# DAWES Benchmark
### Domain-Adaptive Weights for Expert Systems

**A public benchmark for I&C (Instrumentation & Controls) domain knowledge in AI models.**

Built by Ryan Anderson — I&C instructor at Bellingham Technical College, 20 years in oil refining.

---

## What Is DAWES?

No public AI benchmark tests whether a model actually knows industrial instrumentation and controls — the real-world knowledge that keeps refineries, power plants, and process facilities running safely.

DAWES fills that gap. It tests AI models on the same material a working I&C technician needs to know: loop calibration, process measurement, troubleshooting, control systems, electrical theory, and safety standards.

**If an AI is going to work in industrial environments, it needs to actually know the domain — not hallucinate ISA standards or fabricate setpoints. DAWES is how we prove or disprove that.**

---

## Benchmark Structure

- **560-question protected bank** — never published, never used for training
- **60-question evaluation sample** — drawn from the bank at runtime per test run
- **5 tiers of difficulty:**
  - T1: Recall — definitions, units, standards
  - T2: Comprehension — explain concepts, identify components
  - T3: Application — calculate, configure, select
  - T4: Analysis — troubleshoot, diagnose, compare
  - T5: Synthesis — design, evaluate, justify

**Scoring:** Each question scored 0–3 (0=wrong, 1=partial, 2=correct, 3=correct+reasoning). Max score: 180. Results reported as percentage.

---

## Anti-Contamination Protocol

The 560Q bank is **read-only and air-gapped from all training pipelines**.

Before any training job:
1. SHA-256 fingerprint check: every training example hashed and compared against the 560Q bank
2. Canary string search: `InstrumentUberkind`, `IUK-T1-` through `IUK-T5-`, `IUK-CANARY`
3. ANY match = HARD STOP

Honeypot fabricated references are embedded in T4 questions. If a trained model cites them specifically, it has been contaminated.

---

## Current Leaderboard

*Last updated: 2026-04-09 | 72hr benchmark run in progress*

| Model | Score | Runs | Notes |
|-------|-------|------|-------|
| Qwen 2.5 32B (local) | TBD | — | Pending 72hr run |
| Qwen 2.5 14B (base) | 53.5% | 1 | DAWES-IC-v1 baseline |
| Qwen 2.5 14B (DAWES-IC-v1 LoRA) | TBD | — | Fine-tuned, pending eval |
| Claude 3.5 Sonnet | 52.3% | 1 | API baseline |
| Qwen 2.5 32B | 60.0% | 1 | Current leader (local) |
| GPT-4o | TBD | — | Pending 72hr run |
| Grok | TBD | — | Pending 72hr run |
| Gemma 4 E2B | 6.9% | 1 | Possible format issue — retesting |

*3-run averages with variance analysis. σ > 5% triggers additional runs.*

---

## Methodology

Full methodology: [docs/methodology.md](docs/methodology.md)

**Quick summary:**
- Questions drawn from BTC INST/ELTR curriculum, Kuphaldt textbooks, ISA standards, CSB incident reports
- Each model tested under identical conditions: same question order, same temperature (0.0), same system prompt
- Scoring automated + spot-checked by domain expert (Ryan Anderson)
- Results published after each phase with full run logs

---

## Hardware

| Device | Spec | Role |
|--------|------|------|
| RTX 3090 | 24GB VRAM | Primary training + heavy inference |
| RTX 4060 Ti | 16GB VRAM | Parallel eval + continuous inference |
| Mac Studio M1 Max | 32GB RAM | Orchestration + scoring |

---

## Repository Structure

```
dawes-benchmark/
├── README.md                    # This file
├── docs/
│   ├── methodology.md           # Full scoring rubric and protocol
│   ├── contamination-protocol.md # Air-gap and anti-leakage rules
│   └── hardware-setup.md        # Lab configuration
├── results/
│   ├── 2026-04-05-baseline.json # First trained model results
│   └── 2026-04-09-72hr-run/     # Current 72hr benchmark run (in progress)
├── scripts/
│   ├── run_benchmark.py         # Benchmark runner
│   ├── score.py                 # Automated scorer
│   └── fingerprint_check.py    # Contamination detection
└── leaderboard.json             # Machine-readable scores
```

---

## Status

🔴 **72hr benchmark run in progress** — started 2026-04-09

Results will be published here in full when complete, including:
- Per-model, per-tier breakdown
- 3-run variance analysis
- Before/after comparison for DAWES-fine-tuned models
- Full methodology and run logs

---

## About

Built by [Ryan Anderson](https://github.com/ryan10sa-star) as part of the [RelayForge](https://relayforge.tools) project.

The trades built everything you're standing in. They deserve AI tools that actually work.

*Issues and discussion welcome. Questions about methodology? Open an issue.*
