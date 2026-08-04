"""Development settings."""
from .base import *  # noqa: F401,F403
from .base import REST_FRAMEWORK

DEBUG = True

# Browsable API is convenient in dev.
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = (
    "rest_framework.renderers.JSONRenderer",
    "rest_framework.renderers.BrowsableAPIRenderer",
)

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
