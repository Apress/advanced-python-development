CLEANED_DT_FLOAT = t.AsyncIterator[t.Tuple[datetime.datetime, float]]
CLEANED_COORD_FLOAT = t.AsyncIterator[t.Tuple[t.Tuple[float, float], float]]

DT_FLOAT_CLEANER = t.Callable[[t.AsyncIterator[DataPoint]], CLEANED_DT_FLOAT]
COORD_FLOAT_CLEANER = t.Callable[[t.AsyncIterator[DataPoint]], CLEANED_COORD_FLOAT]


def convert_temperature(magnitude: float, origin_unit: str, target_unit: str) -> float:
    temp = ureg.Quantity(magnitude, origin_unit)
    return temp.to(target_unit).magnitude


def convert_temperature_system(
    cleaner: DT_FLOAT_CLEANER, temperature_unit: str,
) -> DT_FLOAT_CLEANER:
    async def converter(datapoints: t.AsyncIterator[DataPoint],) -> CLEANED_DT_FLOAT:
        results = cleaner(datapoints)
        reveal_type(temperature_unit)
        reveal_type(convert_temperature)
        async for date, temp_c in results:
            yield date, convert_temperature(temp_c, "degC", temperature_unit)

    return converter

