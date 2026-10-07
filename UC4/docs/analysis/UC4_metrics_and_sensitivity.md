# UC4 metrics, Monte Carlo, and sensitivity contract

## Purpose and interpretation boundary

Stage 10 evaluates the implemented UC4 hybrid model under controlled synthetic uncertainty. It does not report measurements from a SALUS pilot, certify legal compliance, establish evidentiary admissibility, or validate the fidelity of any real device. The generated results are engineering evidence for the behavior of this implementation only.

The analysis has two components in a fixed order:

1. execute the lawful-incident configuration once as the deterministic nominal example;
2. execute the versioned Monte Carlo design and aggregate its outcomes without selecting or discarding seeds.

## Metric definitions

| Metric | Numerator / computation | Denominator / undefined rule |
|---|---|---|
| Evidence capture recall | preserved authorized relevant records | relevant observable records available at collection; `null` when none exist |
| Evidence precision | relevant preserved evidence | all preserved evidence; `null` when nothing is preserved |
| Unauthorized disclosure | count and bytes released by deny decisions | absolute safety count; expected zero |
| Collection latency | acquisition timestamp minus request timestamp | median, p95, and maximum are `null` with no evidence |
| Investigation latency | report-ready time minus case-trigger time | `null` if no report-ready transition occurs |
| Loss by source/cause | losses recorded at observation, presence, queue, availability, or retention boundaries | absolute counts; zero means no modeled loss of that cause |
| Reconstruction recall | type-matched reconstructed relevant events | hidden relevant ground-truth events; `null` when none exist |
| Reconstruction precision | type-matched reconstructed relevant events | reconstructed relevant observations; `null` when none exist |
| Timestamp error | mean absolute matched-event time error | `null` when no events match |
| Custody failures | detected content or custody-chain verification failures | absolute count |
| Twin lag | mean accepted synchronization ingest-time minus device event-time | `null` when no twin update is accepted |
| Twin stale fraction | accumulated post-threshold stale time | horizon multiplied by configured twin count |
| Network metrics | modeled utilization, queue peak, dropped bytes, and loss rate, including acquisition-specific fields | a rate is `null` when no bytes/capacity form a denominator |
| Assumption coverage | records grouped by provenance status | enabled entity and relationship model records |

Ground truth enters only the post-reconstruction evaluator. It is never an investigator-visible reconstruction input.

## Uncertainty design

[`configs/uc4/monte_carlo.yaml`](../../configs/uc4/monte_carlo.yaml) declares 100 samples, master seed `20260908`, and the complete consecutive simulation seed set `44000` through `44099`. Independent uniform draws cover observation loss, clock-offset bound, background network load, sensor error, and delayed collection. The sample count was fixed before examining the results and is not tuned to achieve a favorable outcome.

Each sample records the five drawn values, simulation seed, canonical simulation hash, and a hash of its complete sample row. The aggregate records a hash over the ordered sample ledger.

## Statistical method

- Continuous outcomes use a two-sided 95% normal-approximation confidence interval for the mean with the sample standard deviation.
- Binary success proportions use a two-sided 95% Wilson score interval.
- Undefined values remain JSON `null`, are excluded from continuous means, and are counted explicitly.
- Sensitivity uses pairwise Pearson correlation between each uncertain input and each defined numerical output. It is descriptive, univariate, and not a causal or variance-decomposition result.

Run the analysis with:

```powershell
salus-mathsim analyze --design configs/uc4/monte_carlo.yaml --output reports/generated/uc4/monte_carlo
```

The output contains the full nominal run package, `monte_carlo_samples.jsonl`, `monte_carlo_summary.json`, `monte_carlo_report.md`, and `sensitivity.svg`.

## Reading the committed result

The collection-delay input dominates collection and investigation latency by construction and also reduces capture once delayed collection crosses authorization or retention boundaries. Clock-offset magnitude primarily affects twin lag. Background load affects the abstract acquisition utilization. Correlations close to zero can indicate a weak effect, a constant output, event sparsity, interactions, or inadequate sensitivity of the present abstraction; they must not be treated as proof that an input is operationally irrelevant.

The committed run observed zero policy-bypass disclosure bytes and no custody failures across its 100 tested paths. These are bounded software-path results. They do not establish GDPR compliance, lawful authority, chain-of-custody admissibility, or pilot KPI attainment.

## Mapping to proposal objectives

| Proposal-facing objective | Evidence produced here | Claim that is not made |
|---|---|---|
| Privacy-preserving, lawful investigation | deny decisions release zero bytes; field minimization is applied before evidence creation | legal or GDPR compliance certification |
| Trustworthy evidence handling | content hashes and modeled custody links verify in nominal and Monte Carlo runs | admissibility under any jurisdiction |
| Digital Twin situational representation | synchronization lag and stale-state fraction are measured | fidelity against deployed pilot twins |
| Reconstructable incident chronology | event recall/precision and timestamp error are scored against isolated truth | identity, intent, guilt, or complete real-world reconstruction |
| Repeatable experimentation | exact design, master seed, simulation seeds, per-sample hashes, and aggregate hash are retained | generalization beyond the declared parameter ranges and model abstraction |
