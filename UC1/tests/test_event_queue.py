import pytest

from salus_t43.uc1.event_queue import EventQueue


def test_queue_orders_by_time_then_sequence():
    queue = EventQueue()
    queue.push(2.0, "late", {})
    queue.push(1.0, "first", {})
    queue.push(1.0, "second", {})
    assert [queue.pop().kind, queue.pop().kind, queue.pop().kind] == ["first", "second", "late"]


def test_queue_rejects_negative_time():
    with pytest.raises(ValueError):
        EventQueue().push(-1, "bad", {})

