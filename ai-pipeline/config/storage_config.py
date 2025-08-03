"""
Storage Configuration for BetterGut AI Pipeline
Centralized configuration for all data storage paths
"""
import os
from pathlib import Path
from typing import Dict, Any

class StorageConfig:
    """Centralized storage configuration"""
    
    # Base storage directory
    BASE_STORAGE = Path("./storage")
    
    # Crawled data storage
    CRAWLED_DATA = BASE_STORAGE / "crawled_data"
    PUBMED_DATA = CRAWLED_DATA / "pubmed"
    INSTITUTIONS_DATA = CRAWLED_DATA / "institutions" 
    SPECIALISTS_DATA = CRAWLED_DATA / "specialists"
    
    # RAG system storage
    RAG_DATABASE = BASE_STORAGE / "rag_database"
    VECTOR_DB = RAG_DATABASE / "chroma_db"
    EMBEDDINGS_CACHE = RAG_DATABASE / "embeddings_cache"
    
    # Model storage
    MODELS = BASE_STORAGE / "models"
    QUANTIZED_MODELS = MODELS / "quantized"
    EMBEDDING_MODELS = MODELS / "embeddings"
    
    # Logs and temporary files
    LOGS = BASE_STORAGE / "logs"
    TEMP = BASE_STORAGE / "temp"
    
    @classmethod
    def create_directories(cls):
        """Create all storage directories"""
        directories = [
            cls.BASE_STORAGE,
            cls.CRAWLED_DATA,
            cls.PUBMED_DATA,
            cls.INSTITUTIONS_DATA,
            cls.SPECIALISTS_DATA,
            cls.RAG_DATABASE,
            cls.VECTOR_DB,
            cls.EMBEDDINGS_CACHE,
            cls.MODELS,
            cls.QUANTIZED_MODELS,
            cls.EMBEDDING_MODELS,
            cls.LOGS,
            cls.TEMP
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def get_paths_dict(cls) -> Dict[str, str]:
        """Get all paths as a dictionary"""
        return {
            'base_storage': str(cls.BASE_STORAGE),
            'crawled_data': str(cls.CRAWLED_DATA),
            'pubmed_data': str(cls.PUBMED_DATA),
            'institutions_data': str(cls.INSTITUTIONS_DATA),
            'specialists_data': str(cls.SPECIALISTS_DATA),
            'rag_database': str(cls.RAG_DATABASE),
            'vector_db': str(cls.VECTOR_DB),
            'embeddings_cache': str(cls.EMBEDDINGS_CACHE),
            'models': str(cls.MODELS),
            'quantized_models': str(cls.QUANTIZED_MODELS),
            'embedding_models': str(cls.EMBEDDING_MODELS),
            'logs': str(cls.LOGS),
            'temp': str(cls.TEMP)
        }
    
    @classmethod
    def print_structure(cls):
        """Print the storage structure"""
        print("📁 BetterGut AI Pipeline Storage Structure:")
        print("storage/")
        print("├── crawled_data/           # All crawled health data")
        print("│   ├── pubmed/            # Scientific articles from PubMed")
        print("│   ├── institutions/      # Government & institutional content")
        print("│   └── specialists/       # Specialist website content")
        print("├── rag_database/          # RAG system data")
        print("│   ├── chroma_db/         # Vector database")
        print("│   └── embeddings_cache/  # Cached embeddings")
        print("├── models/                # AI models")
        print("│   ├── quantized/         # Quantized models for RTX 3090")
        print("│   └── embeddings/        # Embedding models")
        print("├── logs/                  # Application logs")
        print("└── temp/                  # Temporary files")

# Environment variables for Docker
def get_storage_config_from_env() -> Dict[str, Any]:
    """Get storage configuration from environment variables"""
    return {
        'base_storage': os.getenv('STORAGE_BASE', './storage'),
        'max_crawl_articles': int(os.getenv('MAX_CRAWL_ARTICLES', '100')),
        'vector_db_collection': os.getenv('VECTOR_DB_COLLECTION', 'gut_health_knowledge'),
        'embedding_model': os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2'),
        'quantized_model_path': os.getenv('QUANTIZED_MODEL_PATH', './storage/models/quantized'),
        'gpu_memory_fraction': float(os.getenv('GPU_MEMORY_FRACTION', '0.8')),
    }

if __name__ == "__main__":
    # Initialize storage structure
    StorageConfig.create_directories()
    StorageConfig.print_structure()
    print("\n✅ Storage directories created successfully!")
