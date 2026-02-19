from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QObject
from PySide6.QtWidgets import (
    QFormLayout,
    QLineEdit,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from models import Issue


class IssueDetailPanel(QWidget):
    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        self.form = QFormLayout()
        self.form.setContentsMargins(12, 12, 12, 12)
        self.form.setHorizontalSpacing(10)
        self.form.setVerticalSpacing(8)
        self.form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        self.severity_edit = QLineEdit()
        self.severity_edit.setReadOnly(True)
        self.name_edit = QLineEdit()
        self.name_edit.setReadOnly(True)
        self.account_name_edit = QLineEdit()
        self.account_name_edit.setReadOnly(True)
        self.opportunity_name_edit = QLineEdit()
        self.opportunity_name_edit.setReadOnly(True)
        self.category_edit = QLineEdit()
        self.category_edit.setReadOnly(True)
        self.owner_edit = QLineEdit()
        self.owner_edit.setReadOnly(True)
        self.status_edit = QLineEdit()
        self.status_edit.setReadOnly(True)
        self.timestamp_edit = QLineEdit()
        self.timestamp_edit.setReadOnly(True)
        self.fields_edit = QLineEdit()
        self.fields_edit.setReadOnly(True)
        self.metric_name_edit = QLineEdit()
        self.metric_name_edit.setReadOnly(True)
        self.metric_value_edit = QTextEdit()
        self.metric_value_edit.setReadOnly(True)
        self.explanation_edit = QTextEdit()
        self.explanation_edit.setReadOnly(True)
        self.resolution_edit = QTextEdit()
        self.resolution_edit.setReadOnly(True)

        for w in (
            self.severity_edit,
            self.name_edit,
            self.account_name_edit,
            self.opportunity_name_edit,
            self.category_edit,
            self.owner_edit,
            self.status_edit,
            self.timestamp_edit,
            self.fields_edit,
            self.metric_name_edit,
        ):
            w.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        for w in (self.metric_value_edit, self.explanation_edit, self.resolution_edit):
            w.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.form.addRow("Severity", self.severity_edit)
        self.form.addRow("Name", self.name_edit)
        self.form.addRow("Account", self.account_name_edit)
        self.form.addRow("Opportunity", self.opportunity_name_edit)
        self.form.addRow("Category", self.category_edit)
        self.form.addRow("Owner", self.owner_edit)
        self.form.addRow("Status", self.status_edit)
        self.form.addRow("Timestamp", self.timestamp_edit)
        self.form.addRow("Fields", self.fields_edit)
        self.form.addRow("Metric Name", self.metric_name_edit)
        self.form.addRow("Metric Value", self.metric_value_edit)
        self.form.addRow("Explanation", self.explanation_edit)
        self.form.addRow("Resolution", self.resolution_edit)

        layout.addLayout(self.form, 1)

    def set_issue(self, issue: Issue) -> None:
        self.severity_edit.setText(str(issue.severity))
        self.name_edit.setText(str(issue.name))
        self.account_name_edit.setText(str(issue.account_name))
        self.opportunity_name_edit.setText(str(issue.opportunity_name))
        self.category_edit.setText(str(issue.category))
        self.owner_edit.setText(str(issue.owner))
        self.status_edit.setText(str(issue.status))
        ts = issue.timestamp
        self.timestamp_edit.setText(ts.toString("yyyy-MM-dd") if ts else "")
        fields = issue.fields
        if isinstance(fields, (list, tuple)):
            self.fields_edit.setText(", ".join(str(f) for f in fields))
        elif fields is None:
            self.fields_edit.setText("")
        else:
            self.fields_edit.setText(str(fields))
        self.metric_name_edit.setText(str(issue.metric_name))
        metric_value = issue.metric_value
        self.metric_value_edit.setText("" if metric_value is None else str(metric_value))
        self.explanation_edit.setPlainText(str(issue.explanation))
        self.resolution_edit.setPlainText(str(issue.resolution))

    def clear(self) -> None:
        self.severity_edit.clear()
        self.name_edit.clear()
        self.account_name_edit.clear()
        self.opportunity_name_edit.clear()
        self.category_edit.clear()
        self.owner_edit.clear()
        self.status_edit.clear()
        self.timestamp_edit.clear()
        self.fields_edit.clear()
        self.metric_name_edit.clear()
        self.metric_value_edit.clear()
        self.explanation_edit.clear()
        self.resolution_edit.clear()
