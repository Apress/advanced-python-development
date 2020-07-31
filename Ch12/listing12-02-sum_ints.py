import typing as t

def sum_ints(source: t.Iterable[int]) -> t.Iterator[int]:
    """Yields a running total from the underlying iterator"""
    total = 0
    for num in source:
        total += num
        yield total

def numbers() -> t.Iterator[int]:
    yield 1
    yield 1
    yield 1

def test():
    sums = sum_ints(numbers())
    assert [a for a in sums] == [1, 2, 3]

