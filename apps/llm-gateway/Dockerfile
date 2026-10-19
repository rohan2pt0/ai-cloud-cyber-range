# Distroless-style hardening: pinned base, non-root, read-only FS friendly, no shell needed at runtime.
FROM python:3.12-slim AS build
WORKDIR /src
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.12-slim
LABEL org.opencontainers.image.source="https://github.com/rohan2pt0/ai-cloud-cyber-range" \
      org.opencontainers.image.description="AI Guardrail Gateway (PEP for LLM traffic)"
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
# Product version + build commit, injected at build time (see .github/workflows/release.yml).
ARG SECURAX_VERSION=0.0.0-dev
ARG GIT_COMMIT=unknown
ENV SECURAX_VERSION=${SECURAX_VERSION} GIT_COMMIT=${GIT_COMMIT}
COPY --from=build /install /usr/local
WORKDIR /app
COPY app ./app
RUN useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin gateway \
 && mkdir -p /var/lib/securax && chown 10001 /var/lib/securax   # AI allowance spend survives restarts (a volume)
USER 10001
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8080/healthz')"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--no-server-header"]
