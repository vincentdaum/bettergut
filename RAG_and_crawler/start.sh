#!/bin/bash
"""
Startup script for RAG and Crawler container
Starts health API and runs crawling pipeline
"""

echo "🚀 Starting BetterGut RAG and Crawler System"
echo "📁 Container: bettergut-crawler-rag"
echo "🔧 Mode: Crawling + RAG Building (No LLM)"

# Set environment variables
export PYTHONPATH=/app
export PYTHONUNBUFFERED=1

# Create directories if they don't exist
mkdir -p /app/data/crawled
mkdir -p /app/data/chroma_db
mkdir -p /app/storage/crawled_data
mkdir -p /app/storage/vector_db
mkdir -p /app/storage/logs
mkdir -p /app/logs

echo "📊 Starting health monitoring API on port 8001..."
# Start health API in background
python health_api.py &
HEALTH_API_PID=$!

# Wait a moment for API to start
sleep 3

echo "🔍 Starting medical data crawling process..."
echo "📍 Max articles per source: ${MAX_CRAWL_ARTICLES:-100}"
echo "🎯 Topics: gut health, microbiome, nutrition, digestive health"

# Run the crawling and RAG building pipeline
python crawl_health_data.py \
    --max-articles ${MAX_CRAWL_ARTICLES:-100} \
    --topics "gut health" "microbiome" "nutrition" "digestive health" "probiotics" "fiber" "inflammation" \
    --output-dir /app/data/crawled \
    --rag-db-path /app/data/chroma_db

CRAWL_EXIT_CODE=$?

if [ $CRAWL_EXIT_CODE -eq 0 ]; then
    echo "✅ Crawling and RAG building completed successfully!"
    echo "📊 Knowledge base ready for use"
    echo "🔗 Health API available at http://localhost:8001/health"
    echo "📈 Status endpoint: http://localhost:8001/status"
else
    echo "❌ Crawling failed with exit code $CRAWL_EXIT_CODE"
fi

# Keep health API running
echo "🔄 Keeping health API running for monitoring..."
wait $HEALTH_API_PID
