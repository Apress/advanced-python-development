from concurrent.futures import ThreadPoolExecutor
import sys
import time
import threading


data = []
results = []
running = True
data_available = threading.Condition()
work_complete = threading.Condition()


def has_data():
    """ Return true if there is data in the data list """
    return bool(data)


def num_complete(n):
    """Return a function that checks if the results list has the length specified by n"""

    def finished():
        return len(results) >= n

    return finished


def calculate():
    while running:
        with data_available:
            # Acquire the data_available lock and wait for has_data
            print("Waiting for data")
            data_available.wait_for(has_data)
            time.sleep(1)
            i = data.pop()
        with work_complete:
            if i % 2:
                results.append(1)
            else:
                results.append(0)
            # Acquire the work_complete lock and wake listeners
            work_complete.notify_all()


if __name__ == "__main__":
    with ThreadPoolExecutor() as pool:
        # Schedule two worker functions
        workers = [pool.submit(calculate), pool.submit(calculate)]

        for i in range(200):
            with data_available:
                data.append(i)
                # After adding each piece of data wake the data_available lock
                data_available.notify()
        print("200 items submitted")

        with work_complete:
            # Wait for at least 5 items to be complete through the work_complete lock
            work_complete.wait_for(num_complete(5))

        for worker in workers:
            # Set a shared variable causing the threads to end their work
            running = False
        print("Stopping workers")

    print(f"{len(results)} items processed")
