import typing as t


def mean_ints_split_initial() -> t.Tuple[float, int]:
    return 0.0, 0


def mean_ints_split(
    to_add: float, current_mean: float, num_items: int
) -> t.Tuple[float, int]:
    running_total = current_mean * num_items
    running_total += to_add
    num_items += 1
    current_mean = running_total / num_items
    return current_mean, num_items


def test():
    # Recursive mean from initial data
    to_add, current_mean, num_items = mean_ints_split_initial()
    for n in range(3):
        current_mean, num_items = mean_ints_split(to_add, current_mean, num_items)
        to_add = current_mean
    assert current_mean == 1.0
    assert num_items == 3

    # Mean of concrete data list
    current_mean = num_items = 0
    for to_add in [1, 2, 3]:
        current_mean, num_items = mean_ints_split(to_add, current_mean, num_items)
    assert current_mean == 2.0
    assert num_items == 3

