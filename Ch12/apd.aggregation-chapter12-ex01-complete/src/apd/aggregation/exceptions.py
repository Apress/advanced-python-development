class NoDataForTrigger(ValueError):
    """An error that's raised when a trigger is passed
    a data point that cannot be handled due to an incompatible
    value being stored"""

    pass


class IncompatibleTriggerError(NoDataForTrigger):
    """An error that's raised when a trigger is passed
    a data point that cannot be handled due to an incompatible
    value being stored"""

    pass
