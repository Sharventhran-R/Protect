"""Bounded frame buffer with explicit overflow policies and thread safety."""

import threading
import time
from collections import deque

from home_guard.camera.models import Frame, OverflowPolicy


class FrameBuffer:
    """Thread-safe bounded FIFO frame queue with configurable overflow policies."""

    def __init__(
        self,
        capacity: int = 30,
        overflow_policy: OverflowPolicy = OverflowPolicy.DROP_OLDEST,
    ) -> None:
        """Initialize bounded frame buffer.

        Args:
            capacity: Maximum number of frames the buffer can store (must be > 0).
            overflow_policy: Policy to apply when pushing to a full buffer.
        """
        if capacity <= 0:
            raise ValueError(f"Buffer capacity must be strictly positive, got {capacity}.")

        self._capacity = capacity
        self._overflow_policy = overflow_policy
        self._queue: deque[Frame] = deque()
        self._lock = threading.Lock()
        self._not_empty = threading.Condition(self._lock)

    @property
    def capacity(self) -> int:
        """Maximum frame capacity of this buffer."""
        return self._capacity

    @property
    def occupancy(self) -> int:
        """Current number of frames queued in the buffer."""
        with self._lock:
            return len(self._queue)

    @property
    def is_empty(self) -> bool:
        """Check whether the buffer contains zero frames."""
        with self._lock:
            return len(self._queue) == 0

    @property
    def is_full(self) -> bool:
        """Check whether the buffer has reached maximum capacity."""
        with self._lock:
            return len(self._queue) >= self._capacity

    @property
    def overflow_policy(self) -> OverflowPolicy:
        """The active overflow handling policy."""
        return self._overflow_policy

    def push(self, frame: Frame) -> bool:
        """Push a frame into the bounded buffer according to the overflow policy.

        Args:
            frame: Validated Frame instance to enqueue.

        Returns:
            bool: True if the frame was added without dropping any frame;
                  False if an overflow drop occurred.
        """
        with self._lock:
            if len(self._queue) >= self._capacity:
                if self._overflow_policy == OverflowPolicy.DROP_OLDEST:
                    self._queue.popleft()
                    self._queue.append(frame)
                    self._not_empty.notify()
                    return False
                else:  # REJECT_NEWEST
                    # Discard the incoming frame
                    return False

            self._queue.append(frame)
            self._not_empty.notify()
            return True

    def pop(self, timeout: float | None = None) -> Frame | None:
        """Retrieve and remove the oldest frame from the buffer.

        Args:
            timeout: Optional wait duration in seconds if empty.
                     If None or <= 0, operates in non-blocking mode.

        Returns:
            Frame: The next frame in sequence, or None if buffer remains empty.
        """
        with self._lock:
            if timeout is None or timeout <= 0.0:
                if not self._queue:
                    return None
                return self._queue.popleft()

            deadline = time.monotonic() + timeout
            while not self._queue:
                remaining = deadline - time.monotonic()
                if remaining <= 0.0:
                    return None
                if not self._not_empty.wait(timeout=remaining) and not self._queue:
                    return None

            return self._queue.popleft()

    def clear(self) -> None:
        """Purge all frames from the buffer and reset occupancy to zero."""
        with self._lock:
            self._queue.clear()
