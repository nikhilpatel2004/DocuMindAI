"""Application exception hierarchy.

Each exception maps to a consistent JSON error response with a stable
``error_code`` so clients can branch on the failure type without parsing
human-readable messages.
"""
from __future__ import annotations


class AppError(Exception):
    """Base application error."""

    def __init__(self, message: str, status_code: int = 400, error_code: str = "APP_ERROR") -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code


class ValidationError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=422, error_code="VALIDATION_ERROR")


class AuthenticationError(AppError):
    def __init__(self, message: str = "Invalid credentials") -> None:
        super().__init__(message, status_code=401, error_code="AUTH_ERROR")


class TokenError(AppError):
    def __init__(self, message: str = "Invalid or expired token") -> None:
        super().__init__(message, status_code=401, error_code="TOKEN_ERROR")


class ForbiddenError(AppError):
    def __init__(self, message: str = "Forbidden") -> None:
        super().__init__(message, status_code=403, error_code="FORBIDDEN")


class NotFoundError(AppError):
    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(message, status_code=404, error_code="NOT_FOUND")


class ConflictError(AppError):
    def __init__(self, message: str = "Resource already exists") -> None:
        super().__init__(message, status_code=409, error_code="CONFLICT")


class PayloadTooLargeError(AppError):
    def __init__(self, message: str = "File too large") -> None:
        super().__init__(message, status_code=413, error_code="PAYLOAD_TOO_LARGE")


class UnsupportedMediaTypeError(AppError):
    def __init__(self, message: str = "Unsupported file type") -> None:
        super().__init__(message, status_code=415, error_code="UNSUPPORTED_MEDIA_TYPE")


class ProcessingError(AppError):
    def __init__(self, message: str = "Document processing failed") -> None:
        super().__init__(message, status_code=422, error_code="PROCESSING_ERROR")


class InsufficientContextError(AppError):
    """Raised when retrieved context is not sufficient to answer."""

    def __init__(self, message: str = "The uploaded documents do not contain the answer") -> None:
        super().__init__(message, status_code=200, error_code="INSUFFICIENT_CONTEXT")


class ModelUnavailableError(AppError):
    def __init__(self, message: str = "AI model service is unavailable") -> None:
        super().__init__(message, status_code=503, error_code="MODEL_UNAVAILABLE")


class ModelNotDownloadedError(AppError):
    def __init__(self, message: str = "Model is not downloaded") -> None:
        super().__init__(message, status_code=503, error_code="MODEL_NOT_DOWNLOADED")


class TimeoutError(AppError):
    def __init__(self, message: str = "Model inference timed out") -> None:
        super().__init__(message, status_code=504, error_code="MODEL_TIMEOUT")
