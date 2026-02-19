from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Iterable, Optional

from .rule_result import RuleResult
from .severity import Severity


class Rule:
    def __init__(
        self,
        rule_type: str = "opportunity",
        *,
        settings_id: str = "",
        name: str = "",
        category: str = "",
        responsible: Callable[[Any], str] | None = None,
        metric_name: str = "",
        metric: Callable[[Any], Any] | None = None,
        format_metric_value: Callable[[Any], str] | None = None,
        condition: Callable[[Any], Severity] | None = None,
        fields: Iterable[str] = (),
        explanation: Callable[[str, Any], str] | None = None,
        resolution: str = "",
    ) -> None:
        self._settings_id = settings_id
        self._name = name
        self._category = category
        self._rule_type = rule_type
        self._responsible = responsible or (lambda obj: "")
        self._metric_name = metric_name
        self._metric = metric or (lambda obj: 0.0)
        self._format_metric_value = format_metric_value or (lambda value: str(value))
        self._condition = condition or (lambda value: Severity.NONE)
        self._fields = list(fields)
        self._explanation = explanation or (lambda metric_name, value: "")
        self._resolution = resolution

    @property
    def settings_id(self) -> str:
        return self._settings_id

    @settings_id.setter
    def settings_id(self, value: str) -> None:
        self._settings_id = value

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._name = value

    @property
    def category(self) -> str:
        return self._category

    @category.setter
    def category(self, value: str) -> None:
        self._category = value

    @property
    def rule_type(self) -> str:
        return self._rule_type

    @rule_type.setter
    def rule_type(self, value: str) -> None:
        self._rule_type = value

    @property
    def responsible(self) -> Callable[[Any], str]:
        return self._responsible

    @responsible.setter
    def responsible(self, value: Callable[[Any], str]) -> None:
        self._responsible = value

    @property
    def metric_name(self) -> str:
        return self._metric_name

    @metric_name.setter
    def metric_name(self, value: str) -> None:
        self._metric_name = value

    @property
    def metric(self) -> Callable[[Any], Any]:
        return self._metric

    @metric.setter
    def metric(self, value: Callable[[Any], Any]) -> None:
        self._metric = value

    @property
    def condition(self) -> Callable[[Any], Severity]:
        return self._condition

    @condition.setter
    def condition(self, value: Callable[[Any], Severity]) -> None:
        self._condition = value

    @property
    def fields(self) -> list[str]:
        return self._fields

    @fields.setter
    def fields(self, value: list[str]) -> None:
        self._fields = value

    @property
    def resolution(self) -> str:
        return self._resolution

    @resolution.setter
    def resolution(self, value: str) -> None:
        self._resolution = value

    def run(self, obj: Any, *, other_context: Any = None) -> RuleResult | None:
        if other_context is None:
            metric_value = self.metric(obj)
        else:
            metric_value = self.metric(obj, other_context)
        severity = self.condition(metric_value)
        if severity == Severity.NONE:
            return None

        if self._format_metric_value is not None:
            formatted_metric_value = self._format_metric_value(metric_value)
        else:
            formatted_metric_value = metric_value
        explanation = self._explanation(self.metric_name, metric_value)

        if self.rule_type == "opportunity":
            account_name = getattr(obj, "account_name", "") if hasattr(obj, "account_name") else ""
            opportunity_name = getattr(obj, "name", "") if hasattr(obj, "name") else ""
        elif self.rule_type == "account":
            account_name = getattr(obj, "name", "") if hasattr(obj, "name") else ""
            opportunity_name = ""
        else:
            account_name = ""
            opportunity_name = ""

        return RuleResult(
            name=self.name,
            category=self.category,
            account_name=account_name,
            opportunity_name=opportunity_name,
            responsible=self.responsible(obj),
            severity=severity.value if hasattr(severity, "value") else str(severity),
            fields=tuple(self.fields),
            metric_name=self.metric_name,
            metric_value=metric_value,
            formatted_metric_value=formatted_metric_value,
            timestamp=datetime.now(),
            resolution=self.resolution,
            explanation=explanation,
        )
