import itertools
import typing as t

def sum_ints(start: int) -> t.Iterator[int]:
    """Yields a running total with a given start value"""
    total = start
    while True:
        yield total
        total += total

def test():
    sums = sum_ints(1)
    # Limit an infinite iterator to the first 3 items
    # itertools.islice(iterable, [start,] stop, [step])
    sums = itertools.islice(sums, 3)
    assert [a for a in sums] == [1, 2, 4]

