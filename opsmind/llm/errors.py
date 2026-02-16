from __future__ import annotations


class OpsMindLLMError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        provider: str | None = None,
        retryable: bool = False,
        http_status: int = 500,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.provider = provider
        self.retryable = retryable
        self.http_status = http_status


class AuthError(OpsMindLLMError):
    def __init__(self, message: str, provider: str | None = None) -> None:
        super().__init__("auth_error", message, provider=provider, retryable=False, http_status=401)


class RateLimitError(OpsMindLLMError):
    def __init__(self, message: str, provider: str | None = None) -> None:
        super().__init__("rate_limit", message, provider=provider, retryable=True, http_status=429)


class TimeoutError(OpsMindLLMError):
    def __init__(self, message: str, provider: str | None = None) -> None:
        super().__init__("timeout", message, provider=provider, retryable=True, http_status=504)


class BadRequestError(OpsMindLLMError):
    def __init__(self, message: str, provider: str | None = None) -> None:
        super().__init__("bad_request", message, provider=provider, retryable=False, http_status=400)


class ProviderUnavailableError(OpsMindLLMError):
    def __init__(self, message: str, provider: str | None = None) -> None:
        super().__init__(
            "provider_unavailable",
            message,
            provider=provider,
            retryable=True,
            http_status=503,
        )


class BudgetExceededError(OpsMindLLMError):
    def __init__(self, message: str, provider: str | None = None) -> None:
        super().__init__(
            "budget_exceeded",
            message,
            provider=provider,
            retryable=False,
            http_status=402,
        )
