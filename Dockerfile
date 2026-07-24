FROM python:3.13-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN addgroup --system eod \
    && adduser --system --ingroup eod --home /app eod

WORKDIR /app

COPY --chown=eod:eod pyproject.toml manage.py ./
COPY --chown=eod:eod src ./src
COPY --chown=eod:eod scripts/container-entrypoint.sh ./scripts/container-entrypoint.sh

RUN python -m pip install --upgrade pip setuptools wheel \
    && python -m pip install . \
    && chmod 0755 /app/scripts/container-entrypoint.sh \
    && mkdir -p /app/staticfiles \
    && chown -R eod:eod /app/staticfiles

USER eod

EXPOSE 8765

ENTRYPOINT ["/app/scripts/container-entrypoint.sh"]
CMD ["gunicorn", "--bind", "0.0.0.0:8765", "--workers", "2", "--threads", "4", "--timeout", "60", "--access-logfile", "-", "--error-logfile", "-", "eod_config.wsgi:application"]
