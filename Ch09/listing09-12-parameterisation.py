import datetime
import pytest


class TestGetData:
    @pytest.fixture
    def mut(self):
        return get_data

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "filter,num_items_expected",
        [
            ({}, 9),
            ({"sensor_name": "Test"}, 7),
            ({"deployment_id": UUID("b4c68905-b1e4-4875-940e-69e5d27730fd")}, 5),
            ({"collected_after": datetime.datetime(2020, 4, 1, 12, 2, 1),}, 3),
            ({"collected_before": datetime.datetime(2020, 4, 1, 12, 2, 1),}, 4),
            (
                {
                    "collected_after": datetime.datetime(2020, 4, 1, 12, 2, 1),
                    "collected_before": datetime.datetime(2020, 4, 1, 12, 3, 5),
                },
                2,
            ),
        ],
    )
    async def test_iterate_over_items(
        self, mut, db_session, populated_db, filter, num_items_expected
    ):
        db_session_var.set(db_session)
        points = [dp async for dp in mut(**filter)]
        assert len(points) == num_items_expected

