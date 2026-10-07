# UC3 assumption and calibration register

All values are replaceable configuration inputs. None describes an operational facility.

| ID | Assumption/default | Value/range | Impact and replacement |
|---|---|---|---|
| ASSUMPTION-UC3-001 | Field zone is logical | synthetic | Replace from approved topology. |
| ASSUMPTION-UC3-002 | Control zone is logical | synthetic | Replace from partner architecture. |
| ASSUMPTION-UC3-003 | Supervisory zone exists | synthetic | Replace from testbed design. |
| ASSUMPTION-UC3-004 | One-vessel surrogate | area 10 m²; level 2–8 m | Recalibrate only with approved non-sensitive model. |
| ASSUMPTION-UC3-005 | Generic level sensor | noise 0–0.05 m; bias ±0.1 m | Replace from documented sensor characteristics. |
| ASSUMPTION-UC3-006 | Generic pump/valve | flow 0.2 m³/s | Replace from safe test model. |
| ASSUMPTION-UC3-007 | PLC scan and interlocks | 1 s; deterministic | Replace from abstract testbed contract, never plant secrets. |
| ASSUMPTION-UC3-008 | HMI role | supervisory only | Confirm with UkrNS. |
| ASSUMPTION-UC3-009 | Engineering workstation | authorized abstract endpoint | Confirm scope and ownership. |
| ASSUMPTION-UC3-010 | Historian exists | synthetic log store | Replace with approved schema. |
| ASSUMPTION-UC3-011 | Gateway supports abstract actions | drop/rate-limit/isolate | Replace through T4.2 capability discovery. |
| ASSUMPTION-UC3-012 | Passive observation | probability 0.7–1.0 | Calibrate from monitoring validation. |
| ASSUMPTION-UC3-013 | Attack is symbolic | 6 requests at 5/s nominal | Replace with approved safe scenario parameters. |
| ASSUMPTION-UC3-014 | Detector is weighted rules | threshold 0.3–0.7 | Replace via T3.3 contract and calibration. |
| ASSUMPTION-UC3-015 | Policy service available | delay 0.01–0.5 s | Replace via T4.2 integration tests. |
| ASSUMPTION-UC3-016 | Evidence allowlist/retention | metadata; 3600 s | Replace after legal/partner classification. |
| ASSUMPTION-UC3-017 | Human roles are synthetic | operator/analyst/investigator | Map only after workflow confirmation. |
| ASSUMPTION-UC3-018 | DS4 unavailable | no committed data | Add only with licence/checksum/mapping. |
| ASSUMPTION-UC3-019 | DS5 unavailable | no committed data | Add only with licence/checksum/minimization. |

Owners are the responsible UC3/WP6 or technical-interface partner. Unknown values remain TBD rather than being promoted to pilot facts.
