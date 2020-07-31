import itertools
import typing as t

def sum_ints(source: t.Iterable[int]) -> t.Iterator[int]:
    """Yields a running total from the underlying iterator"""
    total = 0
    for num in source:
        total += num
        yield total

def get_wrap_feedback_pair(initial=None):  # get_w_f_p(...) in the above diagram
    """Return a pair of external and internal wrap functions"""
    shared_state = initial
    # Note, feedback() and wrap(...) functions assume that
    # they are always in sync
    def feedback():
        while True:
            """Yield the last value of the wrapped iterator"""
            yield shared_state
    def wrap(wrapped):
        """Iterate over an iterable and stash each value"""
        nonlocal shared_state
        for item in wrapped:
            shared_state = item
            yield item
    return feedback, wrap

def test():
    feedback, wrap = get_wrap_feedback_pair(1)
    # Sum the iterable (1, ...) where ... is the results
    # of that iterable, stored with the wrap method
    sums = wrap(sum_ints(feedback()))
    # Limit to 3 items
    sums = itertools.islice(sums, 3)
    assert [a for a in sums] == [1, 2, 4]

