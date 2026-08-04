# Production image: build the Vite SPA, then run Django with Gunicorn serving
# both the API and the built frontend (via WhiteNoise + SPA catch-all).

FROM node:22-slim AS frontend-build
WORKDIR /app
COPY frontend/package.json ./frontend/
WORKDIR /app/frontend
RUN npm install
COPY frontend ./
# Same-origin API in production → empty base means the client calls "/api/v1".
ENV VITE_API_BASE_URL=""
RUN npm run build


FROM python:3.13-slim AS runtime
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    DJANGO_SETTINGS_MODULE=config.settings.prod

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY backend/requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY backend ./
# The built SPA lands where SERVE_SPA / WHITENOISE_ROOT expect it.
COPY --from=frontend-build /app/frontend/dist ./frontend_dist

COPY deploy/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120", "--log-file", "-"]
