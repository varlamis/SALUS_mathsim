"""Append-only deterministic custody hash chain."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib


def _hash_parts(*parts: object) -> str:
    return hashlib.sha256("|".join(str(part) for part in parts).encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class CustodyRecord:
    custody_id: str
    sequence: int
    evidence_id: str
    evidence_hash: str
    action: str
    action_time: float
    actor_id: str
    previous_hash: str
    chain_hash: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


class CustodyChain:
    def __init__(self, run_id: str, case_id: str, schema_version: str) -> None:
        self.genesis_hash = _hash_parts(run_id, case_id, schema_version)
        self.records: list[CustodyRecord] = []

    def append(
        self, custody_id: str, evidence_id: str, evidence_hash: str,
        action: str, action_time: float, actor_id: str,
    ) -> CustodyRecord:
        previous = self.records[-1].chain_hash if self.records else self.genesis_hash
        chain_hash = _hash_parts(previous, evidence_hash, action, action_time, actor_id)
        record = CustodyRecord(
            custody_id, len(self.records), evidence_id, evidence_hash, action,
            action_time, actor_id, previous, chain_hash,
        )
        self.records.append(record)
        return record

    def verify(self, records: list[CustodyRecord] | None = None) -> bool:
        candidate = records if records is not None else self.records
        previous = self.genesis_hash
        for sequence, record in enumerate(candidate):
            if record.sequence != sequence or record.previous_hash != previous:
                return False
            expected = _hash_parts(previous, record.evidence_hash, record.action, record.action_time, record.actor_id)
            if record.chain_hash != expected:
                return False
            previous = record.chain_hash
        return True
