# UC2 use-case analysis

## Problem and bounded objective

UC2 asks how an operator can detect and categorize a nearby IoT-device hypothesis from incomplete multi-interface observations. The implemented vertical slice is deliberately passive: synthetic approved and unapproved emitters produce abstract 3GPP, Wi-Fi and BLE metadata; separate observers lose, delay or duplicate observations; analytics associates rotating pseudonyms, estimates a device class, checks a synthetic approval registry and raises an explainable alert for an unapproved hypothesis.

## Evidence and decision boundary

Hidden emitter identity/class is evaluation truth only. Operational components receive pseudonymous observations and declared registry state. Classification is probabilistic and exports alternatives. Unknown/stale registry and insufficient evidence fail to review rather than certainty. The policy can observe, request review, pause the simulated scene or quarantine a hypothesis object; it cannot transmit, intercept, deauthenticate or affect radio devices.

## Stakeholders and unresolved facts

FMI/CIVIPOL and SUNERIS roles are proposal-level placeholders. Experts must confirm lawful/ethical collection scope, permitted fields, interface taxonomy, scene topology, device classes, registry governance, classifier calibration, response authority, evidence retention and DS2/DS3 access. Synthetic defaults are not field-performance claims.

## Acceptance argument

Traceability is supplied by source/status fields and assumptions; structural consistency by strict schemas and graph validation; behavioral consistency by deterministic runs; safety/privacy by zero-active-RF and zero-disclosure invariants; robustness by nine branches and 100 samples; and reproducibility by JUnit and a verified manifest.
