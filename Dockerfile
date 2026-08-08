FROM python@sha256:67a1e1f215ccda113cfc024e8639049257e88f273898f595b61476d128d387e8 AS build
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PATH="/opt/build-venv/bin:$PATH"
WORKDIR /app
RUN python -m venv /opt/build-venv
COPY requirements/locks/build.txt requirements/locks/runtime.txt /app/requirements/locks/
RUN python -m pip install --disable-pip-version-check --require-hashes \
    -r requirements/locks/build.txt
COPY pyproject.toml README.md manage.py /app/
COPY src /app/src
RUN python -m build --wheel --no-isolation --outdir /app/dist

FROM python@sha256:67a1e1f215ccda113cfc024e8639049257e88f273898f595b61476d128d387e8 AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PATH="/opt/venv/bin:$PATH" PYTHONPATH="/app/src"
WORKDIR /app
RUN python -m venv /opt/venv
COPY requirements/locks/runtime.txt /app/requirements/locks/runtime.txt
RUN python -m pip install --disable-pip-version-check --require-hashes \
    -r requirements/locks/runtime.txt
COPY --from=build /app/dist/*.whl /tmp/eod/
RUN mkdir -p /app/src \
    && python -m pip install --disable-pip-version-check --no-deps --target /app/src /tmp/eod/*.whl \
    && rm -rf /tmp/eod
COPY src/static /app/src/static
COPY src/templates /app/src/templates
COPY manage.py /app/manage.py
COPY scripts/container-entrypoint.sh /app/scripts/container-entrypoint.sh
RUN chmod +x /app/scripts/container-entrypoint.sh \
    && mkdir -p /app/data /app/media /app/staticfiles /app/logs \
    && chown -R 10001:10001 /app
USER 10001:10001
EXPOSE 8765
ENTRYPOINT ["/app/scripts/container-entrypoint.sh"]
CMD ["gunicorn", "eod_config.wsgi:application", "--bind", "0.0.0.0:8765", "--workers", "2", "--access-logfile", "-", "--error-logfile", "-"]
