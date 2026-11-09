FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy local wheel if present and install dependencies
COPY wheels/ /app/wheels/
RUN pip install --no-cache-dir /app/wheels/*.whl uvicorn fastapi httpx pydantic sqlalchemy asyncpg

# Copy application source code
COPY src/ /app/src/

EXPOSE 8000

CMD ["uvicorn", "main:app", "--app-dir", "src", "--host", "0.0.0.0", "--port", "8000"]
