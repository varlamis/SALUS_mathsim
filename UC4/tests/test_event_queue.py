import pytest

from salus_t43.uc4.event_queue import EventQueue
from salus_t43.uc4.identifiers import IdentifierFactory


def test_queue_orders_by_time_then_insertion_sequence():
    queue = EventQueue()
    second = queue.schedule(2.0, "second", "UC4-D01")
    first_a = queue.schedule(1.0, "first-a", "UC4-D01")
    first_b = queue.schedule(1.0, "first-b", "UC4-D01")
    assert [queue.pop(), queue.pop(), queue.pop()] == [first_a, first_b, second]


def test_queue_rejects_negative_time_and_ids_are_stable():
    queue = EventQueue()
    with pytest.raises(ValueError):
        queue.schedule(-0.1, "invalid", "UC4-D01")
    first = IdentifierFactory()
    second = IdentifierFactory()
    assert [first.next("event"), first.next("event")] == [second.next("event"), second.next("event")]
