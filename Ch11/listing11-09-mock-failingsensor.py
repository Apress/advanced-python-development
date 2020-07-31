from apd.sensors.base import Sensor
from apd.sensors.exceptions import IntermittentSensorFailureError

FailingSensor = mock.MagicMock(spec=Sensor)
FailingSensor.title = "Sensor which fails"
FailingSensor.name = "FailingSensor"
FailingSensor.value.side_effect = IntermittentSensorFailureError("Failing sensor")
FailingSensor.__str__.side_effect = IntermittentSensorFailureError("Failing sensor")

