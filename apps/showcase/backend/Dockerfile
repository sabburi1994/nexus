FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=8080

# Unprivileged runtime user (fixed uid so file ownership is predictable).
RUN groupadd --system --gid 10001 nexus \
    && useradd --system --uid 10001 --gid nexus --home-dir /home/nexus --create-home --shell /usr/sbin/nologin nexus

# Copy the locally built framework wheel and install dependencies as root.
COPY wheels/ /app/wheels/
RUN pip install --no-cache-dir /app/wheels/*.whl uvicorn fastapi httpx pydantic sqlalchemy asyncpg \
    && rm -rf /app/wheels

# Application source stays root owned and read only for the runtime user.
COPY src/ /app/src/

USER nexus:nexus

EXPOSE 8080

CMD ["sh", "-c", "exec uvicorn main:app --app-dir src --host 0.0.0.0 --port ${PORT:-8080} --no-server-header"]
