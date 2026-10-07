from dataclasses import dataclass, field


@dataclass
class IdentifierFactory:
    counters: dict[str, int] = field(default_factory=dict)

    def next(self, kind: str) -> str:
        self.counters[kind] = self.counters.get(kind, 0) + 1
        return f"UC5-{kind}-{self.counters[kind]:06d}"

