"""Test settings — fast, isolated, eager Celery."""
from .base import *  # noqa: F401,F403

DEBUG = False
CELERY_TASK_ALWAYS_EAGER = True

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Allow tests to run against a local Postgres without the docker hostnames.
DATABASES["default"]["HOST"] = env_str("POSTGRES_HOST", "localhost")  # noqa: F405
