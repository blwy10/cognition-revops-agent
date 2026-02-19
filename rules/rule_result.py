from datetime import datetime

class RuleResult:
    def __init__(
        self,
        name: str,
        category: str,
        account_name: str,
        opportunity_name: str,
        responsible: str,
        fields: tuple[str, ...],
        metric_name: str,
        metric_value: float,
        formatted_metric_value: str,
        timestamp: datetime,
        explanation: str,
        resolution: str,
        severity: str,
    ) -> None:
        self._name = name
        self._category = category
        self._account_name = account_name
        self._opportunity_name = opportunity_name
        self._responsible = responsible
        self._fields = fields
        self._metric_name = metric_name
        self._metric_value = metric_value
        self._formatted_metric_value = formatted_metric_value
        self._timestamp = timestamp
        self._explanation = explanation
        self._resolution = resolution
        self._severity = severity

    @property
    def name(self) -> str:
        return self._name

    @property
    def category(self) -> str:
        return self._category

    @property
    def account_name(self) -> str:
        return self._account_name

    @property
    def opportunity_name(self) -> str:
        return self._opportunity_name

    @property
    def responsible(self) -> str:
        return self._responsible

    @property
    def fields(self) -> tuple[str, ...]:
        return self._fields

    @property
    def metric_name(self) -> str:
        return self._metric_name

    @property
    def metric_value(self) -> float:
        return self._metric_value

    @property
    def formatted_metric_value(self) -> str:
        return self._formatted_metric_value

    @property
    def timestamp(self) -> datetime:
        return self._timestamp

    @property
    def explanation(self) -> str:
        return self._explanation

    @property
    def resolution(self) -> str:
        return self._resolution

    @property
    def severity(self) -> str:
        return self._severity