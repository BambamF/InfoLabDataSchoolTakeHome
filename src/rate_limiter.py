from threading import Lock
from collections import deque
import time

class RateLimiter:

    def __init__(self, time_frame: float, max_calls: int = 500):
        self.max_calls = max_calls
        self.time_frame = time_frame
        self.calls_deque: deque = deque()
        self.wait_calls = 0
        self.lock = Lock()

    def acquire(self):
        with self.lock:
            now = time.monotonic()
            while self.calls_deque and self.calls_deque[0] <= now - self.time_frame:
                    self.calls_deque.popleft()
            if len(self.calls_deque) >= self.max_calls:
                sleep_time = self.time_frame - (now - self.calls_deque[0])
                self.wait_calls += 1
            else:
                sleep_time = 0
        if sleep_time > 0:
            time.sleep(sleep_time)
        self.calls_deque.append(time.monotonic())
                
