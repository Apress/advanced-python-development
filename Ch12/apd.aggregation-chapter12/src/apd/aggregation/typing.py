import datetime
import typing as t
from typing_extensions import Protocol

from apd.aggregation.database import DataPoint


# Aliases for common types
# These type variables allow for generic functions. T_key represents the place
# in a chart that an item will be placed, and T_value the kind of data that is plotted.
T_key = t.TypeVar("T_key")
T_value = t.TypeVar("T_value")

# Cleaned is a placeholder type, representing an async iterator of key and value functions
# Cleaned[float, float] is equivalent to typing.AsyncIterator[Tuple[builtins.float, builtins.float]]
Cleaned = t.AsyncIterator[t.Tuple[T_key, T_value]]

# T_cleaned represents a placeholder for the result of a cleaner function, and is *covariant*
# because it can accept compatible types (such as ints where floats were declared).
# It is bound to Cleaned, so only items that match the specification for Cleaned (for any values
# of T_key or T_value) are valid
T_cleaned = t.TypeVar("T_cleaned", covariant=True, bound=Cleaned)


# CleanerFunc is a generic protocol, it matches any Callable that converts an async iterator
# of datapoints to its type. So, CleanerFunc[float] would be equivalent to t.Callable[[t.AsyncIterator[DataPoint]], float]
class CleanerFunc(Protocol[T_cleaned]):
    def __call__(self, datapoints: t.AsyncIterator[DataPoint]) -> T_cleaned:
        ...


# CLEANED_DT_FLOAT is a Cleaned represents datetime/float pairs, for simple charts
CLEANED_DT_FLOAT = Cleaned[datetime.datetime, float]
# and CLEANED_COORD_FLOAT represents (lat/lon), float pairs
CLEANED_COORD_FLOAT = Cleaned[t.Tuple[float, float], float]

# The _CLEANER variants are functions that return their matching iterators from above
DT_FLOAT_CLEANER = CleanerFunc[CLEANED_DT_FLOAT]
COORD_FLOAT_CLEANER = CleanerFunc[CLEANED_COORD_FLOAT]


# When drawing a map we will be building a dictionary of UUID to dictionary
# That inner dictionary should contain coord (float, float)
# and value (float) only. Either or both can be None.
# This class is abstract, it's just for type checking.
class IntermediateMapData(t.TypedDict):
    coord: t.Optional[t.Tuple[float, float]]
    value: t.Optional[float]
