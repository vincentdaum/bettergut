# BetterGut RAG & Crawler System

**Lightweight data crawling and RAG knowledge base builder** - This container focuses on collecting medical data and building vector databases without heavy LLM dependencies.

## 🎯 Purpose

- **Crawl medical data** from 10+ authoritative sources (Mayo Clinic, Harvard, NIH, etc.)
- **Build RAG knowledge base** using ChromaDB and sentence transformers  
- **Prepare data** for separate LLM inference system
- **Monitor progress** through health check API
- **No GPU requirements** - CPU-only for crawling and embeddings

## 🐳 Quick Start

```bash
# Start the complete crawling and RAG building process
docker-compose -f docker-compose.ai.yaml up -d

# Monitor progress
docker logs -f bettergut-crawler-rag

# Check health and status
curl http://localhost:8001/health
curl http://localhost:8001/status
```
├── logs/                  # Application logs
└── temp/                  # Temporary files
```

## 🚀 Quick Start

### 1. Test Setup (No Dependencies)
```bash
cd ai-pipeline
python test_setup.py
```

### 2. Docker Deployment (Recommended)
```bash
# Build and run with GPU support
docker-compose -f docker-compose.ai.yml up --build

# Or run just the AI pipeline
docker build -f ai-pipeline/Dockerfile.production -t bettergut-ai ai-pipeline/
docker run --gpus all -p 8001:8001 -v $(pwd)/ai-pipeline/storage:/app/storage bettergut-ai
```

### 3. Manual Setup
```bash
cd ai-pipeline
pip install -r requirements.txt
python crawl_health_data.py --crawl-only --max-articles 10
python api.py
```

## 🤖 RTX 3090 Optimized Models

The pipeline includes optimized quantized models for RTX 3090 (24GB VRAM):

### Recommended Models:
- **Llama 3 8B (4-bit)**: Best balance of performance and quality (~6GB VRAM)
- **Mistral 7B (4-bit)**: Fast inference for real-time responses (~5GB VRAM)
- **CodeLlama 7B (4-bit)**: Structured outputs and JSON responses (~5GB VRAM)

### Model Selection:
```python
from models.quantized_models import QuantizedModelManager

manager = QuantizedModelManager()
# Load optimized model for RTX 3090
model, tokenizer = manager.load_quantized_model('llama3_8b_4bit')
```

## 📊 Data Crawling

### Crawl Health Data:
```bash
# Crawl data only
python crawl_health_data.py --crawl-only --max-articles 50

# Build RAG database only
python crawl_health_data.py --build-only

# Full pipeline
python crawl_health_data.py --max-articles 100
```

### Data Sources:
1. **PubMed**: Scientific articles from NCBI
2. **Health Institutions**: NIH, CDC, Harvard Nutrition
3. **Specialist Sites**: Gut health specialist websites

## 🧠 RAG System

The RAG system provides context-aware health insights:

```python
from rag.rag_system import HealthRAGSystem

rag = HealthRAGSystem(chroma_db_path="./storage/rag_database/chroma_db")
context = rag.get_context_for_query("What foods improve gut microbiome?")
```

## 🔧 Configuration

### Environment Variables:
```bash
CUDA_VISIBLE_DEVICES=0              # Use first GPU
STORAGE_BASE=./storage              # Storage base directory
MAX_CRAWL_ARTICLES=100              # Articles per source
GPU_MEMORY_FRACTION=0.8             # GPU memory allocation
QUANTIZED_MODEL_PATH=./storage/models/quantized
```

### Storage Configuration:
Edit `config/storage_config.py` to customize storage paths.

## 📡 API Endpoints

Start the API server:
```bash
python api.py
# or
uvicorn api:app --host 0.0.0.0 --port 8001
```

### Key Endpoints:
- `GET /health` - Health check
- `POST /crawl/start` - Start data crawling
- `POST /rag/query` - Query RAG system
- `POST /llm/health-insights` - Generate health insights

## 🧪 Testing

### Run All Tests:
```bash
python test_setup.py
```

### Test Individual Components:
```bash
# Test storage structure
python -c "from config.storage_config import StorageConfig; StorageConfig.create_directories(); StorageConfig.print_structure()"

# Test quantized models
python -c "from models.quantized_models import setup_quantized_model_for_rtx3090; setup_quantized_model_for_rtx3090()"

# Test crawler
python crawl_health_data.py --crawl-only --max-articles 5
```

## 🚀 Deployment

### GPU Server Requirements:
- **GPU**: RTX 3090 (24GB VRAM) or better
- **RAM**: 32GB+ recommended
- **Storage**: 100GB+ free space
- **CUDA**: 12.1+
- **Docker**: With nvidia-container-toolkit

### Docker Deployment:
```bash
# Clone repository
git clone https://github.com/vincentdaum/bettergut.git
cd bettergut

# Deploy with GPU support
docker-compose -f docker-compose.ai.yml up -d

# Check logs
docker-compose -f docker-compose.ai.yml logs -f bettergut-ai
```

## 🔍 Monitoring

### GPU Usage:
```bash
# Monitor GPU memory and utilization
nvidia-smi -l 1

# Check model memory usage
docker exec bettergut-ai python -c "import torch; print(f'GPU Memory: {torch.cuda.memory_allocated()/1024**3:.2f}GB')"
```

### Storage Usage:
```bash
# Check storage usage
du -h storage/
```

## 🛠️ Development

### Add New Crawlers:
1. Create crawler in `crawlers/`
2. Update `health_crawler.py`
3. Add storage path in `storage_config.py`

### Customize Models:
1. Add model config in `quantized_models.py`
2. Update model recommendations
3. Test with benchmark function

## 📚 Documentation

- [Deployment Guide](DEPLOYMENT.md)
- [API Documentation](http://localhost:8001/docs) (when running)
- [Model Benchmarks](storage/logs/benchmarks.json)

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-crawler`
3. Test changes: `python test_setup.py`
4. Submit pull request

## 📄 License

MIT License - see LICENSE file for details.

---

**Ready to deploy on your RTX 3090 server!** 🚀
