from dataclasses import dataclass


@dataclass
class IntegrationEvent:
    source: str
    payload: dict


class LogsAdapter:
    def fetch(self) -> list[IntegrationEvent]:
        return [IntegrationEvent(source="logs", payload={"message": "Mock log entry"})]


class MetricsAdapter:
    def fetch(self) -> list[IntegrationEvent]:
        return [IntegrationEvent(source="metrics", payload={"cpu": 0.95})]


class TracesAdapter:
    def fetch(self) -> list[IntegrationEvent]:
        return [IntegrationEvent(source="traces", payload={"trace_id": "abc123"})]


class GitHubAdapter:
    def fetch_commits(self) -> list[IntegrationEvent]:
        return [IntegrationEvent(source="github", payload={"commit": "abc123", "summary": "Mock commit"})]


class JiraAdapter:
    def fetch_tickets(self) -> list[IntegrationEvent]:
        return [IntegrationEvent(source="jira", payload={"key": "OPS-1", "summary": "Mock ticket"})]


class ChangeRecordAdapter:
    def fetch_changes(self) -> list[IntegrationEvent]:
        return [IntegrationEvent(source="changeiq", payload={"crq": "CRQ-1", "summary": "Mock change"})]
