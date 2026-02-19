from __future__ import annotations

import datetime as _dt
import random
from dataclasses import dataclass


@dataclass
class Rng:
    _r: random.Random

    @classmethod
    def from_seed(cls, seed: int) -> "Rng":
        return cls(random.Random(seed))

    def randint(self, a: int, b: int) -> int:
        return self._r.randint(a, b)

    def uniform(self, a: float, b: float) -> float:
        return self._r.uniform(a, b)

    def choice(self, seq):
        return self._r.choice(seq)

    def shuffle(self, seq) -> None:
        self._r.shuffle(seq)

    def sample(self, population, k: int):
        return self._r.sample(population, k)

    def random(self) -> float:
        return self._r.random()

    def paretovariate(self, alpha: float) -> float:
        return self._r.paretovariate(alpha)

    def date_between(self, start_ymd: str, end_ymd: str) -> str:
        start = _dt.date.fromisoformat(start_ymd)
        end = _dt.date.fromisoformat(end_ymd)
        if end < start:
            raise ValueError(f"Invalid date window: {start_ymd}..{end_ymd}")
        days = (end - start).days
        offset = self.randint(0, days)
        d = start + _dt.timedelta(days=offset)
        return d.isoformat()
