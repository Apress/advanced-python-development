class MeanFinder:
    def __init__(self):
        self.running_total = 0
        self.num_items = 0

    def add_item(self, num: float):
        self.running_total += num
        self.num_items += 1

    @property
    def mean(self):
        return self.running_total / self.num_items

def test():
    # Recursive mean from initial data
    mean = MeanFinder()
    to_add = 1
    for n in range(3):
        mean.add_item(to_add)
        to_add = mean.mean
    assert mean.mean == 1.0

    # Mean of a concrete data list
    mean = MeanFinder()
    for to_add in [1, 2, 3]:
        mean.add_item(to_add)
    assert mean.mean == 2.0


