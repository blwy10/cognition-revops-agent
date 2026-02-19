from .rule_result import RuleResult
from .severity import Severity
from datetime import datetime

class Rule:
    def __init__(self):
        self._name: str = ""
        self._category: str = ""
        self._responsible: callable = lambda obj: ""
        self._metric_name: str = ""
        self._metric: callable = lambda obj: 0.0
        self._condition: callable = lambda obj: Severity.NONE
        self._fields: list[str] = []
        self._resolution: str = ""
        self._other_context: dict = {}
    
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
    def responsible(self) -> callable:
        return self._responsible

    @responsible.setter
    def responsible(self, value: callable) -> None:
        self._responsible = value

    @property
    def metric_name(self) -> str:
        return self._metric_name

    @metric_name.setter
    def metric_name(self, value: str) -> None:
        self._metric_name = value

    @property
    def metric(self) -> callable:
        return self._metric

    @metric.setter
    def metric(self, value: callable) -> None:
        self._metric = value
    
    @property
    def condition(self) -> callable:
        return self._condition

    @condition.setter
    def condition(self, value: callable) -> None:
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

    @property
    def other_context(self) -> dict:
        return self._other_context
    
    @other_context.setter
    def other_context(self, value: dict) -> None:
        self._other_context = value
    
    def run(self, obj: dict) -> RuleResult | None:
        metric_value = self.metric(obj)
        severity =  self.condition(metric_value)
        if severity == Severity.NONE:
            return None
        
        return RuleResult(
            name=self.name,
            category=self.category,
            responsible=self.responsible(obj),
            severity=severity,
            fields=self.fields,
            metric_name=self.metric_name,
            metric_value=metric_value,
            timestamp=datetime.now(),
            resolution=self.resolution,
        )
