# Use Python 3.11 slim image for lightweight container
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (no GPU drivers needed for crawling/RAG only)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model for text processing
RUN python -m spacy download en_core_web_sm

# Copy source code
COPY . .

# Create necessary directories for crawling and RAG storage
RUN mkdir -p \
    data/crawled \
    data/chroma_db \
    storage/crawled_data \
    storage/vector_db \
    storage/logs \
    logs

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose port for health checks and potential API access
EXPOSE 8001

# Health check for container monitoring
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8001/health || exit 1

# Copy and make startup scripts executable
COPY start.sh /app/start.sh
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/start.sh /app/entrypoint.sh

# Start command: Run entrypoint script for complete pipeline
CMD ["/app/entrypoint.sh"]
