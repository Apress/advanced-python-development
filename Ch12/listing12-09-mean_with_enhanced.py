import typing as t


def mean_ints() -> t.Generator[t.Optional[float], float, None]:
    running_total = 0.0
    num_items = 0
    to_add = yield None
    while True:
        running_total += to_add
        num_items += 1
        to_add = yield running_total / num_items

def test():
    # Recursive mean from initial data
    mean = mean_ints()
    next(mean)
    to_add = 1
    for n in range(3):
        current_mean = mean.send(to_add)
        to_add = current_mean
    assert current_mean == 1.0

    # Mean of a concrete data list
    # wrap_enhanced_generator would also work here
    mean = mean_ints()
    next(mean)
    for to_add in [1, 2, 3]:
        current_mean = mean.send(to_add)
    assert current_mean == 2.0

