FROM python:3.12-slim

# stream python output immediately — container logs must not lag behind reality
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv

# Copy dependency files first for layer caching
COPY pyproject.toml .

# Install dependencies (production only)
RUN uv sync --no-dev

# Copy application source, migrations, and ops scripts
COPY app ./app
COPY alembic.ini ./
COPY alembic ./alembic
COPY scripts ./scripts
COPY start.sh ./
RUN chmod +x start.sh

EXPOSE 8000

CMD ["./start.sh"]
