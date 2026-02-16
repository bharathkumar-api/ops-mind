from __future__ import annotations

import os
from abc import ABC, abstractmethod


class SecretManager(ABC):
    @abstractmethod
    def get_secret(self, key: str) -> str | None:
        raise NotImplementedError


class EnvSecretManager(SecretManager):
    def get_secret(self, key: str) -> str | None:
        return os.getenv(key)


class GCPSecretManager(SecretManager):
    """Placeholder implementation for GCP Secret Manager integration."""

    def __init__(self, project_id: str | None = None) -> None:
        self.project_id = project_id

    def get_secret(self, key: str) -> str | None:
        # Intentionally left as a placeholder to avoid hard dependency on GCP.
        return None
