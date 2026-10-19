FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir "fastmcp>=2.10"
COPY gateway.py /app/gateway.py
WORKDIR /app
CMD ["python", "gateway.py"]
