# UC4 simulation results

The retained nominal 1,800-second synthetic run models warm-up, unauthorized entry, door-sensor tampering, a separate case trigger and a scoped acquisition. It collected and verified 17/17 relevant evidence items, released zero unauthorized bytes and supported three strong claims. Reconstruction recall against isolated synthetic truth was 1.0, precision 0.5 and timestamp mean absolute error 0.0424 seconds. The imperfect precision is retained as a limitation rather than hidden by nominal recall.

All 16 experiment branches passed their declared assertions. Missing, invalid, expired or revoked authority released no evidence. CPE capacity loss reduced capture; content/custody tamper caused quarantine; Home Assistant loss removed its dependent claim; and clock skew widened uncertainty. The 100-sample analysis reported mean evidence-capture recall 0.899 and mean reconstruction recall 0.665. These are internally validated synthetic results, not real-case admissibility, GDPR compliance or pilot performance.

The final UC4 suite reports 47 passing tests. Detailed machine-readable metrics, experiment comparison and Monte Carlo samples are under `reports/generated/uc4`; JUnit and stage reports are retained beside this summary.
