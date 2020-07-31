import typing as t

def sum_ints() -> t.Generator[int, int, None]:
    """Yields a running total from the underlying iterator"""
    total = 0
    num = yield total
    while True:
        total += num
        num = yield total

def test():
    # Sum the iterable (1, ...) where ... is the results
    # of that iterable, stored with the wrap method
    sums = sum_ints()
    next(sums)  # We can only send to yield lines, so advance to the first
    last = 1
    result = []
    for n in range(3):
        last = sums.send(last)
        result.append(last)
    assert result == [1, 2, 4]

    
test()

