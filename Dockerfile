FROM python:3.11-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt fastapi uvicorn

# Copy app code
COPY . .

# Seed the database
RUN python scripts/seed_db.py

EXPOSE 8501

# Ollama must be accessible at OLLAMA_BASE_URL (default: http://host.docker.internal:11434)
ENV OLLAMA_BASE_URL=http://host.docker.internal:11434
ENV MODEL_NAME=qwen3:4b

CMD ["uvicorn", "api.server:app", "--host", "0.0.0.0", "--port", "8501"]
