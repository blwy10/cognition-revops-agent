from __future__ import annotations

from typing import Any, Optional

from PySide6.QtCore import QObject, Signal


class _RuleSettings(QObject):
    changed = Signal(str, object)

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._values: dict[str, Any] = {}

    def get(self, key: str, default: Any = None) -> Any:
        return self._values.get(key, default)

    def set(self, key: str, value: Any) -> None:
        current = self._values.get(key)
        if current == value and key in self._values:
            return
        self._values[key] = value
        self.changed.emit(key, value)

    def __getitem__(self, key: str) -> Any:
        return self._values[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.set(key, value)

    def to_dict(self) -> dict[str, Any]:
        return dict(self._values)


RuleSettings = _RuleSettings()
