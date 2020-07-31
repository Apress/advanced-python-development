from datetime import datetime
import random
import time

from apd.aggregation.database import DataPoint


def generate_points(time_to_wait):
    while True:
        time.sleep(time_to_wait)
        yield DataPoint(
            sensor_name="Fake",
            collected_at=datetime.now(),
            data=random.choice([1, 2, 3])
        )

def get_points_on_odd_seconds():
    points = generate_points(1)
    odd_seconds = filter(lambda point: point.collected_at.second % 2, points)
    yield from odd_seconds

def print_points(points):
    for point in points:
        print(point.sensor_name, point.collected_at, point.data)

if __name__ == "__main__":
    print_points(get_points_on_odd_seconds())