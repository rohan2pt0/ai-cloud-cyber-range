# Sovereign estate-sync: tiny, hardened, non-root, writes only to its /data volume.
FROM python:3.12-slim AS build
WORKDIR /src
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.12-slim
LABEL org.opencontainers.image.source="https://github.com/rohan2pt0/ai-cloud-cyber-range" \
      org.opencontainers.image.description="SecuRAX estate-sync (sovereign cross-device state store)"
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY --from=build /install /usr/local
WORKDIR /app
COPY syncsvc ./syncsvc
RUN useradd --uid 10002 --no-create-home --shell /usr/sbin/nologin estatesync \
    && mkdir -p /data && chown 10002 /data
USER 10002
EXPOSE 8089
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8089/healthz')"
CMD ["uvicorn", "syncsvc.main:app", "--host", "0.0.0.0", "--port", "8089", "--no-server-header"]
