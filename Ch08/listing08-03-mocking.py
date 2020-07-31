from unittest.mock import Mock, MagicMock, AsyncMock

import pytest


@pytest.fixture
def data() -> t.Any:
    return {
        "sensors": [
            {
                "human_readable": "3.7",
                "id": "PythonVersion",
                "title": "Python Version",
                "value": [3, 7, 2, "final", 0],
            },
            {
                "human_readable": "Not connected",
                "id": "ACStatus",
                "title": "AC Connected",
                "value": False,
            },
        ]
    }

@pytest.fixture
def mockclient(data):
    client = MagicMock()
    response = Mock()
    response.json = AsyncMock(return_value=data)
    response.status = 200
    client.get.return_value.__aenter__ = AsyncMock(return_value=response)
    return client

