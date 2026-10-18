"""A small model the exploration notebook can grow: a first-order sensor response and the
decisions the firmware makes on it. Keep this module free of hardware imports so tests and tools
can use it too."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Sensor:
    """A first-order sensor: the reading approaches the input with a time constant."""

    time_constant_s: float
    noise: float = 0.0
    value: float = 0.0

    def step(self, target: float, dt_s: float, noise: float = 0.0) -> float:
        """Advance the model by one sample and return the new reading."""
        alpha = min(1.0, dt_s / max(self.time_constant_s, dt_s))
        self.value += alpha * (target - self.value)
        self.value += noise
        return self.value


def crosses_threshold(readings: list[float], threshold: float) -> int | None:
    """The index of the first reading above the threshold, or None."""
    for index, reading in enumerate(readings):
        if reading > threshold:
            return index
    return None
