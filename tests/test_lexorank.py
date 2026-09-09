"""Tests for LexoRank fractional indexing."""
from backend.services.rank_service import LexoRank


def test_initial_rank():
    rank = LexoRank.get_initial_rank()
    assert rank == "0|hzzzzz:"


def test_rank_between_inserts():
    first = "0|100000:"
    second = "0|300000:"
    mid = LexoRank.between(first, second)

    # Must sort strictly between first and second
    assert first < mid < second


def test_insert_at_top_and_bottom():
    current = "0|hzzzzz:"
    top = LexoRank.between(None, current)
    assert top < current

    bottom = LexoRank.between(current, None)
    assert bottom > current
