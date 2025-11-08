# Use lightweight Python base
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    OLLAMA_URL=http://localhost:11434 \
    LLM_MODEL=qwen2.5:1.5b \
    EMBED_MODEL=nomic-embed-text \
    CHROMA_DIR=/app/data/chroma \
    DB_PATH=/app/data/tasks.db

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
        && rm -rf /var/lib/apt/lists/*

# Create app directory and non-root user
WORKDIR /app
RUN adduser --disabled-password --gecos '' appuser

# Copy requirements and install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Change ownership to appuser
RUN chown -R appuser:appuser /app
USER appuser

# Create data directories
RUN mkdir -p data/chroma

# Expose ports: FastAPI (8000), Ollama (11434)
EXPOSE 8000 11434

# Healthcheck for FastAPI
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/docs || exit 1

# Start Ollama + FastAPI (in background)
CMD ["sh", "-c", "\
    echo 'Starting Ollama server...' && \
    curl -fsSL https://ollama.com/install.sh | sh && \
    echo 'Pulling models...' && \
    ollama serve & \
    sleep 5 && \
    ollama pull $LLM_MODEL && \
    ollama pull $EMBED_MODEL && \
    echo 'Starting FastAPI...' && \
    uvicorn src.api:app --host 0.0.0.0 --port 8000 \
"]