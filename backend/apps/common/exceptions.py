"""Standardized error envelope for all API responses."""
from rest_framework.views import exception_handler


def standardized_exception_handler(exc, context):
    """Wrap DRF errors in a consistent shape:

    {"error": {"code": "...", "message": "...", "details": {...}}}
    """
    response = exception_handler(exc, context)
    if response is None:
        return response

    code = getattr(exc, "default_code", "error")
    detail = response.data
    message = "Request failed."
    details = {}

    if isinstance(detail, dict):
        if "detail" in detail:
            message = str(detail["detail"])
        else:
            details = detail
            message = "Validation failed."
    elif isinstance(detail, list):
        details = {"non_field_errors": detail}
        message = "Validation failed."

    response.data = {
        "error": {
            "code": code,
            "message": message,
            "details": details,
            "status": response.status_code,
        }
    }
    return response
