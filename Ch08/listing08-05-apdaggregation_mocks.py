from unittest.mock import patch, Mock, AsyncMock

import pytest

import apd.aggregation.collect


class TestGetDataPoints:
    @pytest.fixture
    def mut(self):
        return apd.aggregation.collect.get_data_points

    @pytest.mark.asyncio
    async def test_get_data_points(
        self, mut, mockclient: FakeAIOHttpClient, data
    ) -> None:
        datapoints = await mut("http://localhost", "", mockclient)

        assert len(datapoints) == len(data["sensors"])
        for sensor in data["sensors"]:
            assert sensor["value"] in (datapoint.data for datapoint in datapoints)
            assert sensor["id"] in (datapoint.sensor_name for datapoint in datapoints)

class TestAddDataFromSensors:
    @pytest.fixture
    def mut(self):
        return apd.aggregation.collect.add_data_from_sensors

    @pytest.fixture(autouse=True)
    def patch_aiohttp(self, mockclient):
        # Ensure all tests in this class use the mockclient
        with patch("aiohttp.ClientSession") as ClientSession:
            ClientSession.return_value.__aenter__ = AsyncMock(return_value=mockclient)
            yield ClientSession

    @pytest.fixture
    def db_session(self):
        return Mock()

    @pytest.mark.asyncio
    async def test_datapoints_are_added_to_the_session(self, mut, db_session) -> None:
        # The only times data should be added to the session are when running the MUT
        assert db_session.add.call_count == 0
        datapoints = await mut(db_session, ["http://localhost"], "")
        assert db_session.add.call_count == len(datapoints)

