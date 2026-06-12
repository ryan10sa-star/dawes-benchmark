<h1 align="center">📊 DAWES</h1>

<h3 align="center">Domain Anchored Workplace Expertise Standard<br/>The industrial AI benchmark that publishes honest failure data.</h3>

<p align="center">
  <a href="https://relayforge.tools/dawes">Results</a> •
  <a href="https://relayforge.tools">RelayForge</a> •
  <a href="https://relayforge.tools/whitepaper">Whitepaper</a> •
  <a href="https://discord.gg/relayforge">Discord</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-v1.2-C45E2A?style=flat-square" alt="v1.2" />
  <img src="https://img.shields.io/badge/questions-560Q_master_bank-F5F0E8?style=flat-square&labelColor=0A0A0A" alt="560Q" />
  <img src="https://img.shields.io/badge/judges-5_frontier_models-4CAF50?style=flat-square" alt="Multi-judge" />
  <img src="https://img.shields.io/badge/question_bank-air--gapped-C45E2A?style=flat-square" alt="Air-gapped" />
</p>

---

> **A benchmark where everyone scores high is worthless.** DAWES exists to prove that no current model is ready for unassisted industrial deployment. The honest failure data is the product.

---

## Why DAWES Exists

Every major AI lab publishes benchmarks showing their models are great at reasoning. None of them publish benchmarks showing their models can't reliably recall that a NAMUR NE43 signal of 3.6mA means "above measurement range" — the kind of knowledge a first-year instrument tech carries in their head.

**The entire business case is a knowledge injection problem, not a reasoning problem.** All models score well on reasoning. All models collapse at domain-specific recall. DAWES proves this with data.

<br/>

## Methodology

### Question Bank

- **560 master questions** covering Instrumentation & Controls (I&C) domain knowledge
- **1,000 adversarial questions** designed to expose confident-but-wrong model behavior
- **Air-gapped** on two physical laptops — never exposed to any model instance, never uploaded to any cloud service
- Written and validated by a 20-year certified ISA CCST technician

### Multi-Judge Panel (v1.2)

Five frontier model providers serve as independent judges via OpenRouter:

| Judge | Provider |
|:------|:---------|
| Claude | Anthropic |
| GPT | OpenAI |
| Gemini | Google |
| Grok | xAI |
| Mistral | Mistral |

Each run produces per-judge scores and raw run URLs for full transparency.

### What Gets Tested

| Category | Examples |
|:---------|:---------|
| **Signal interpretation** | NAMUR NE43, 4-20mA ranges, thermocouple types |
| **Standards recall** | ISA standards, NAMUR recommendations, NEC codes |
| **Fault diagnosis** | Instrument failure modes, calibration procedures |
| **Safety protocols** | LOTO procedures, SIS logic, hazardous area classification |
| **Notation literacy** | Ω, Δ, τ, Boolean overbar — what real field docs actually contain |

<br/>

## Key Findings

### What v1.0 Established

1. **Sanitized benchmark questions are easier than real field documents.** Engineers must read Ω, Δ, τ, Boolean overbar notation in practice. V1.0 scores are generous baselines.
2. **All models score well on reasoning but collapse at recall.** The gap isn't thinking — it's knowing.
3. **Cross-model "confident output without verified source" failure.** Every model tested exhibited this pattern. They don't say "I don't know." They say something plausible and wrong.

### Why This Matters Commercially

If you're an industrial enterprise evaluating AI tools for your technicians, you need to know what the model *can't* do — not just what the vendor *says* it can do.

DAWES credibility comes from rigorous methodology and published failures. That honest failure data is the credibility asset that funds everything else RelayForge builds.

<br/>

## Security

The question bank is the most sensitive asset in the RelayForge ecosystem.

- Master bank (560Q) and adversarial set (1,000Q) are **physically air-gapped**
- Stored on two dedicated laptops, never connected to the internet during testing
- **No agent instance** — including RelayForge's own internal agents — has ever seen the questions
- Questions are never referenced, suggested, or exposed in any prompt or conversation

This isn't paranoia. It's methodology. A leaked question bank is a useless benchmark.

<br/>

## Using DAWES

DAWES is a RelayForge benchmark, not an open dataset. The methodology is published; the questions are not.

If you're an enterprise evaluating AI for industrial deployment, [contact us](https://relayforge.tools/contact) about running DAWES against your candidate models.

<br/>

## Related Repositories

| Repo | Purpose |
|:-----|:--------|
| [relayforge](https://github.com/ryan10sa-star/relayforge) | Main site, trust layer docs |
| [relayforge-calclaw](https://github.com/ryan10sa-star/relayforge-calclaw) | Industrial calculation tool (I&C) |
| [lobster-runtime](https://github.com/ryan10sa-star/lobster-runtime) | Agent runtime engine |

<br/>

---

<p align="center">
  <sub>Part of <a href="https://relayforge.tools">RelayForge</a> · Built by a 20-year ISA CCST certified refinery technician · Anacortes, WA</sub>
</p>
