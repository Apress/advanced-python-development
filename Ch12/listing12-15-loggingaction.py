import dataclasses
import logging

from apd.aggregation.actions.base import Action
from apd.aggregation.database import DataPoint

logger = logging.getLogger(__name__)


class LoggingAction(Action):
    """An action that stores any generated data points back to the DB"""

    async def start(self) -> None:
        return

    async def handle(self, datapoint: DataPoint) -> bool:
        logger.warn(datapoint)
        return True

