from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RuleSettingField:
    key: str
    label: str
    default: int
    minimum: int
    maximum: int
