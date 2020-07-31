import typing as t


input_type = t.TypeVar("input_type")
output_type = t.TypeVar("output_type")


def wrap_enhanced_generator(
    input_generator: t.Callable[[], t.Generator[output_type, input_type, None]]
) -> t.Callable[[t.Iterable[input_type]], t.Iterator[output_type]]:
    underlying = input_generator()
    next(underlying)  # Advance the underlying generator to the first yield

    def inner(data: t.Iterable[input_type]) -> t.Iterator[output_type]:
        for item in data:
            yield underlying.send(item)

    return inner


def sum_ints() -> t.Generator[int, int, None]:
    """Yields a running total from the underlying iterator"""
    total = 0
    num = yield total
    while True:
        total += num
        num = yield total

def numbers() -> t.Iterator[int]:
    yield 1
    yield 1
    yield 1


def test() -> None:
    # Start with 1, feed output back in, limit to 3 items
    recursive_sum = sum_ints()
    next(recursive_sum)
    result = []
    last = 1
    for i in range(3):
        last = recursive_sum.send(last)
        result.append(last)
    assert result == [1, 2, 4]

    # Add 3 items from a standard iterable
    simple_sum = wrap_enhanced_generator(sum_ints)
    result_iter = simple_sum(numbers())
    assert [a for a in result_iter] == [1, 2, 3]

