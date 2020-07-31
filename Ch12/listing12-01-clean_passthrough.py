async def clean_passthrough(
    datapoints: t.AsyncIterator[DataPoint],
) -> CLEANED_DT_FLOAT:
    async for datapoint in datapoints:
        if datapoint.data is None:
            continue
        else:
            yield datapoint.collected_at, datapoint.data

