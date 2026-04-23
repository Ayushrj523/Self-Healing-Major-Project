FROM python:3.12-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.12-slim
LABEL maintainer="SENTINELS Team" service="prime-backend"
RUN groupadd -r appuser && useradd -r -g appuser -d /app appuser
WORKDIR /app
COPY --from=builder /install /usr/local
COPY main.py .
RUN chown -R appuser:appuser /app
USER appuser
EXPOSE 8020
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8020/health')" || exit 1
CMD ["gunicorn", "main:application", "--bind", "0.0.0.0:8020", "--workers", "1", "--timeout", "30"]
