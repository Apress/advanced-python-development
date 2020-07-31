import dataclasses
import logging

import aiohttp

from apd.aggregation.actions.base import Action
from apd.aggregation.database import DataPoint

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class WebhookAction(Action):
    """An action that runs a webhook"""
    uri: str

    async def start(self) -> None:
        return

    async def handle(self, datapoint: DataPoint) -> bool:
        async with aiohttp.ClientSession() as http:
            async with http.post(
                self.uri,
                json={
                    "value1": datapoint.sensor_name,
                    "value2": str(datapoint.data),
                    "value3": datapoint.deployment_id.hex,
                },
            ) as request:
                logger.info(
                    f"Made webhook request for {datapoint} with status {request.status}"
                )
                return request.status == 200

