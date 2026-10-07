"""Deterministic, run-local identifiers."""

from __future__ import annotations

from collections import defaultdict


class IdentifierFactory:
    """Issue stable identifiers in creation order; never consult wall-clock time."""

    _prefixes = {
        "event": "UC4-EVT",
        "record": "UC4-SRC",
        "policy": "UC4-PD",
        "evidence": "UC4-EV",
        "custody": "UC4-CUST",
        "correlation": "UC4-CORR",
        "claim": "UC4-CLAIM",
    }

    def __init__(self) -> None:
        self._counters: dict[str, int] = defaultdict(int)

    def next(self, namespace: str) -> str:
        if namespace not in self._prefixes:
            raise KeyError(f"unknown identifier namespace: {namespace}")
        self._counters[namespace] += 1
        return f"{self._prefixes[namespace]}-{self._counters[namespace]:06d}"
