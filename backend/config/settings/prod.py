"""Production settings."""
from .base import *  # noqa: F401,F403

DEBUG = False

SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", True)  # noqa: F405
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_CONTENT_TYPE_NOSNIFF = True

REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = (  # noqa: F405
    "rest_framework.renderers.JSONRenderer",
)

# --- Serve the built Vite SPA via WhiteNoise ------------------------------
SERVE_SPA = True
WHITENOISE_ROOT = FRONTEND_DIST_DIR  # noqa: F405 — serves index.html + /assets/* at root
WHITENOISE_INDEX_FILE = True

# The prod domain(s) come from env; be strict about secret + hosts.
if SECRET_KEY == "insecure-dev-key-change-me":  # noqa: F405
    raise RuntimeError("DJANGO_SECRET_KEY must be set in production.")
