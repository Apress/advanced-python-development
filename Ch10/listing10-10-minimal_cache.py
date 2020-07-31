def convert_temperature_system(
    cleaner: DT_FLOAT_CLEANER, temperature_unit: str,
) -> DT_FLOAT_CLEANER:
    async def converter(datapoints: t.AsyncIterator[DataPoint],) -> CLEANED_DT_FLOAT:
        temperatures = {}
        results = cleaner(datapoints)
        async for date, temp_c in results:
            if temp_c in temperatures:
                temp_f = temperatures[temp_c]
            else:
                temp_f = temperatures[temp_c] = convert_temperature(temp_c, "degC", temperature_unit)
            yield date, temp_f

    return converter


