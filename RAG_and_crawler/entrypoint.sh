#!/bin/bash
"""
Simple entrypoint for RAG and Crawler container
Runs crawling and RAG building without LLM components
"""

echo "🚀 BetterGut RAG & Crawler System Starting"
echo "📦 Container: bettergut-crawler-rag"
echo "🎯 Mode: Crawling + RAG Building Only"

# Set Python path
export PYTHONPATH=/app:$PYTHONPATH
export PYTHONUNBUFFERED=1

# Print environment info
echo "🔧 Environment Configuration:"
echo "   STORAGE_BASE: ${STORAGE_BASE:-/app/storage}"
echo "   MAX_CRAWL_ARTICLES: ${MAX_CRAWL_ARTICLES:-100}"
echo "   VECTOR_DB_COLLECTION: ${VECTOR_DB_COLLECTION:-gut_health_knowledge}"
echo "   EMBEDDING_MODEL: ${EMBEDDING_MODEL:-all-MiniLM-L6-v2}"

# Create directories
echo "📁 Creating storage directories..."
python -c "
from config.storage_config import StorageConfig
StorageConfig.create_directories()
"

# Start health monitoring API in background
echo "🔍 Starting health monitoring API..."
python -c "
import uvicorn
from health_api import app
uvicorn.run(app, host='0.0.0.0', port=8001, log_level='info')
" &

# Give API time to start
sleep 5

# Test health endpoint
curl -f http://localhost:8001/health || echo "⚠️ Health API not responding yet"

echo "📊 Starting data crawling and RAG building pipeline..."

# Run the main crawling and RAG pipeline
python crawl_health_data.py \
    --max-articles ${MAX_CRAWL_ARTICLES:-100} \
    --topics "gut health" "microbiome" "nutrition" "digestive health" "probiotics" "fiber" \
    --output-dir "${CRAWL_DATA_DIR:-/app/data/crawled}" \
    --rag-db-path "${VECTOR_DB_PATH:-/app/data/chroma_db}"

PIPELINE_EXIT_CODE=$?

if [ $PIPELINE_EXIT_CODE -eq 0 ]; then
    echo "✅ Pipeline completed successfully!"
    echo "📊 Knowledge base is ready"
    echo "🔗 Health API: http://localhost:8001/health"
    echo "📈 Status: http://localhost:8001/status"
else
    echo "❌ Pipeline failed with exit code: $PIPELINE_EXIT_CODE"
fi

echo "🔄 Keeping container alive for monitoring..."
# Keep container running
tail -f /dev/null
