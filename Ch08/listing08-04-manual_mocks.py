import contextlib
from dataclasses import dataclass
import typing as t

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


@dataclass
class FakeAIOHttpClient:
    data: t.Any

    @contextlib.asynccontextmanager
    async def get(self, url: str, headers: t.Optional[t.Dict[str, str]]=None) -> FakeAIOHttpResponse:
        yield FakeAIOHttpResponse(json_data=self.data, status=200)


@dataclass
class FakeAIOHttpResponse:
    json_data: t.Any
    status: int

    async def json(self) -> t.Any:
        return self.json_data

@pytest.fixture
def mockclient(data) -> FakeAIOHttpClient:
    return FakeAIOHttpClient(data)

