# DAWES Benchmark V2 Upgrade Plan

Created from the 2026-06-12 continuous improvement audit.

## Current verified state

- This repository publishes the DAWES benchmark methodology and contains the public mastery-gate runner/watchdog code.
- The sensitive question bank is intentionally absent and must remain air-gapped.
- Judge/model API integrations are placeholders; CI must not require provider API keys or live model calls.
- The README referenced `docs/relayforge-logo.png`, but the asset is not present in this repository.
- No CI workflow, unit tests, or V2 plan existed before this audit pass.

## Linear tracking

- Portfolio parent: not linked in this repair pass.
- DAWES Benchmark V2 follow-up: not created in this repair pass.

## V2 scope

1. Keep CI limited to pure runner/watchdog logic and syntax checks, with no live API calls and no question-bank exposure.
2. Add fixture-based tests for judge retries, multi-judge disagreement, blind judging, result versioning, and result persistence.
3. Keep public docs truthful: methodology can be public, protected questions and raw answer keys cannot.
4. Add a dry-run CLI mode that validates configuration without requiring model providers.
5. Split private operational assets into the private training/runtime repositories, leaving this repo as the public methodology surface.

## Done means

- Default branch has a green non-secret CI gate.
- Public README has no broken local assets.
- Pure benchmark logic is covered without exposing the private question bank.
- Live provider calls remain explicit runtime operations, never default CI behavior.

