from __future__ import annotations


class IdentifierFactory:
    def __init__(self) -> None:
        self._event = 0
        self._evidence = 0
        self._custody = 0

    def event(self) -> str:
        self._event += 1
        return f"UC1-EVT-{self._event:06d}"

    def evidence(self) -> str:
        self._evidence += 1
        return f"UC1-EV-{self._evidence:06d}"

    def custody(self) -> str:
        self._custody += 1
        return f"UC1-CUS-{self._custody:06d}"

