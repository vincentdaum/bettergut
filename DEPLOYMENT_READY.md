# 🚀 BetterGut AI Pipeline - Ready for RTX 3090 Deployment

## 📁 Clean File Structure (After Cleanup)

**Core Files (All Needed):**
```
ai-pipeline/
├── 📄 api.py                          # FastAPI service
├── 📄 crawl_health_data.py           # Main crawler script  
├── 📄 requirements.txt               # Python dependencies
├── 📄 Dockerfile.production          # Optimized for GPU servers
├── 📄 README.md                      # Documentation
└── 📄 .env.example                   # Environment template

📂 crawlers/                          # Data collection modules
├── 📄 health_crawler.py              # Main orchestrator
├── 📄 pubmed_crawler.py              # Scientific articles (PubMed)
├── 📄 institution_crawler.py         # Government sources (NIH, CDC)
└── 📄 specialist_crawler.py          # Health specialist websites

📂 models/                            # AI model implementations
├── 📄 llama3_service.py              # Llama 3 integration
└── 📄 quantized_models.py            # RTX 3090 optimized models

📂 rag/                               # Retrieval-Augmented Generation
└── 📄 rag_system.py                  # Vector database & embeddings

📂 config/                            # Configuration management
└── 📄 storage_config.py              # Centralized storage paths

📂 storage/                           # Organized data storage
├── 📂 crawled_data/                  # Raw collected data
│   ├── 📂 pubmed/                    # Scientific articles
│   ├── 📂 institutions/              # Government content
│   └── 📂 specialists/               # Expert content
├── 📂 rag_database/                  # RAG system data
│   ├── 📂 chroma_db/                 # Vector database
│   └── 📂 embeddings_cache/          # Cached embeddings
├── 📂 models/                        # AI models cache
│   ├── 📂 quantized/                 # RTX 3090 models
│   └── 📂 embeddings/                # Embedding models
├── 📂 logs/                          # Application logs
└── 📂 temp/                          # Temporary files

📂 test scripts/ (Development only)
├── 📄 test_setup.py                  # Complete test suite
├── 📄 test_manual.py                 # Manual testing
└── 📄 docker_test_simulation.sh      # Docker simulation
```

## 🗑️ Files Removed for Clean Structure

- ❌ `data/` directory (replaced by organized `storage/`)
- ❌ `analyze_files.py` (cleanup script, no longer needed)

## 🐳 Docker Deployment Commands

### Method 1: Docker Compose (Recommended)
```bash
# Navigate to project root
cd /path/to/bettergut

# Deploy with GPU support
docker-compose -f docker-compose.ai.yml up --build

# Check container status
docker-compose -f docker-compose.ai.yml ps

# View logs
docker-compose -f docker-compose.ai.yml logs -f bettergut-ai
```

### Method 2: Manual Docker Build
```bash
# Build the image
docker build -f ai-pipeline/Dockerfile.production -t bettergut-ai ai-pipeline/

# Run with GPU support
docker run --gpus all \
  -p 8001:8001 \
  -v $(pwd)/ai-pipeline/storage:/app/storage \
  -e CUDA_VISIBLE_DEVICES=0 \
  -e MAX_CRAWL_ARTICLES=50 \
  --name bettergut-ai \
  bettergut-ai
```

### Method 3: One-Command Deployment Script
```bash
# Run the automated deployment script
sudo bash scripts/deploy_gpu_server.sh
```

## 🧪 Testing the Crawlers

### Test Crawler Functionality
```bash
# Test with small dataset
docker exec bettergut-ai python crawl_health_data.py --crawl-only --max-articles 10

# Test with more comprehensive dataset
docker exec bettergut-ai python crawl_health_data.py --crawl-only --max-articles 50

# Full pipeline (crawl + build RAG database)
docker exec bettergut-ai python crawl_health_data.py --max-articles 50
```

### Monitor GPU Usage
```bash
# Check GPU utilization
nvidia-smi -l 1

# Check container GPU access
docker exec bettergut-ai nvidia-smi

# Monitor memory usage
docker exec bettergut-ai python -c "import torch; print(f'GPU Memory: {torch.cuda.memory_allocated()/1024**3:.2f}GB')"
```

## 📊 Expected Crawler Output

### Data Collection Sources:
1. **PubMed** (Scientific Literature)
   - Recent gut health research papers
   - Abstracts and metadata
   - Saved as: `storage/crawled_data/pubmed/pubmed_articles_YYYYMMDD_HHMMSS.json`

2. **Health Institutions** (Government Sources)  
   - NIH, CDC, Harvard Nutrition guidelines
   - Evidence-based health information
   - Saved as: `storage/crawled_data/institutions/institutions_articles_YYYYMMDD_HHMMSS.json`

3. **Specialist Websites** (Expert Content)
   - Gastroenterologist recommendations
   - Nutrition specialist advice
   - Saved as: `storage/crawled_data/specialists/specialists_articles_YYYYMMDD_HHMMSS.json`

### Data Format Example:
```json
{
  "title": "Gut Microbiome and Digestive Health",
  "content": "Scientific content...",
  "source": "PubMed",
  "url": "https://pubmed.ncbi.nlm.nih.gov/...",
  "topics": ["gut health", "microbiome"],
  "crawl_timestamp": "2025-08-03T13:45:00Z"
}
```

## 🔧 RTX 3090 Optimizations

### Quantized Models Available:
- **Llama 3 8B (4-bit)**: ~6GB VRAM, excellent quality
- **Mistral 7B (4-bit)**: ~5GB VRAM, fast inference  
- **CodeLlama 7B (4-bit)**: ~5GB VRAM, structured outputs

### GPU Configuration:
```yaml
environment:
  - CUDA_VISIBLE_DEVICES=0
  - GPU_MEMORY_FRACTION=0.8
  - QUANTIZED_MODEL_PATH=/app/storage/models/quantized
```

## 🔍 Health Check & Monitoring

### API Endpoints:
- **Health Check**: `http://localhost:8001/health`
- **API Docs**: `http://localhost:8001/docs`
- **Start Crawling**: `POST http://localhost:8001/crawl/start`

### Storage Monitoring:
```bash
# Check storage usage
docker exec bettergut-ai du -h /app/storage

# Count crawled articles
docker exec bettergut-ai find /app/storage/crawled_data -name "*.json" | wc -l

# View latest crawl results
docker exec bettergut-ai ls -la /app/storage/crawled_data/pubmed/
```

## ✅ Deployment Readiness Checklist

- ✅ Clean file structure (no unused files)
- ✅ Docker configuration with GPU support
- ✅ Storage organization system
- ✅ RTX 3090 optimized models
- ✅ Automated deployment script
- ✅ Comprehensive testing suite
- ✅ Health monitoring endpoints
- ✅ Documentation and examples

## 🎯 Next Steps

1. **Copy project to RTX 3090 server**
2. **Run deployment**: `sudo bash scripts/deploy_gpu_server.sh`
3. **Test crawlers**: `docker exec bettergut-ai python crawl_health_data.py --crawl-only --max-articles 10`
4. **Monitor GPU usage**: `nvidia-smi`
5. **Scale up**: Increase `--max-articles` as needed
6. **Integrate with your app**: Use API endpoints for health insights

---

**🚀 Your BetterGut AI Pipeline is ready for production deployment on RTX 3090!**
