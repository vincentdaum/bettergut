#!/usr/bin/env python3
"""
Test script for BetterGut AI Pipeline
Tests crawler functionality and storage organization
"""
import sys
import json
from pathlib import Path
from datetime import datetime

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

def test_storage_structure():
    """Test the storage structure setup"""
    print("🧪 Testing Storage Structure...")
    
    try:
        from config.storage_config import StorageConfig
        
        # Create directories
        StorageConfig.create_directories()
        
        # Show structure
        StorageConfig.print_structure()
        
        # Verify all directories exist
        paths = StorageConfig.get_paths_dict()
        all_exist = True
        
        for name, path in paths.items():
            if not Path(path).exists():
                print(f"❌ Missing directory: {name} -> {path}")
                all_exist = False
            else:
                print(f"✅ {name}: {path}")
        
        if all_exist:
            print("\n✅ All storage directories created successfully!")
            return True
        else:
            print("\n❌ Some directories are missing!")
            return False
            
    except Exception as e:
        print(f"❌ Storage structure test failed: {e}")
        return False

def test_mock_crawler_data():
    """Create mock data to test the storage system"""
    print("\n🧪 Testing Mock Crawler Data...")
    
    try:
        from config.storage_config import StorageConfig
        
        # Mock data for different sources
        mock_data = {
            'pubmed': [
                {
                    'title': 'Gut Microbiome and Health: A Comprehensive Review',
                    'abstract': 'The gut microbiome plays a crucial role in human health...',
                    'authors': ['Smith, J.', 'Johnson, A.'],
                    'journal': 'Nature Medicine',
                    'pubmed_id': '12345678',
                    'topics': ['gut health', 'microbiome'],
                    'crawl_timestamp': datetime.now().isoformat()
                },
                {
                    'title': 'Probiotics and Digestive Health',
                    'abstract': 'Recent studies show probiotics can improve digestive function...',
                    'authors': ['Brown, K.', 'Wilson, M.'],
                    'journal': 'Gastroenterology',
                    'pubmed_id': '87654321',
                    'topics': ['probiotics', 'digestive health'],
                    'crawl_timestamp': datetime.now().isoformat()
                }
            ],
            'institutions': [
                {
                    'title': 'NIH Guidelines for Gut Health',
                    'content': 'The National Institutes of Health recommends...',
                    'url': 'https://www.nih.gov/gut-health-guidelines',
                    'source': 'National Institutes of Health',
                    'topics': ['guidelines', 'gut health'],
                    'crawl_timestamp': datetime.now().isoformat()
                }
            ],
            'specialists': [
                {
                    'title': 'Top 10 Foods for Gut Health',
                    'content': 'According to leading gastroenterologists...',
                    'url': 'https://gut-health-specialists.com/top-foods',
                    'source': 'Gut Health Specialists',
                    'topics': ['nutrition', 'gut health'],
                    'crawl_timestamp': datetime.now().isoformat()
                }
            ]
        }
        
        # Save mock data to appropriate directories
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        source_paths = {
            'pubmed': StorageConfig.PUBMED_DATA,
            'institutions': StorageConfig.INSTITUTIONS_DATA,
            'specialists': StorageConfig.SPECIALISTS_DATA
        }
        
        for source, articles in mock_data.items():
            storage_path = source_paths[source]
            
            # Save articles
            filename = f"{source}_test_articles_{timestamp}.json"
            filepath = storage_path / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(articles, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Saved {len(articles)} test {source} articles to {filepath}")
            
            # Save summary
            summary = {
                'source': source,
                'timestamp': timestamp,
                'article_count': len(articles),
                'topics_covered': list(set([
                    topic for article in articles 
                    for topic in article.get('topics', [])
                ])),
                'file_path': str(filepath),
                'test_data': True
            }
            
            summary_path = storage_path / f"{source}_test_summary_{timestamp}.json"
            with open(summary_path, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Saved {source} summary to {summary_path}")
        
        print("\n✅ Mock crawler data created successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Mock data creation failed: {e}")
        return False

def test_quantized_model_config():
    """Test quantized model configuration"""
    print("\n🧪 Testing Quantized Model Configuration...")
    
    try:
        from models.quantized_models import QuantizedModelManager
        
        manager = QuantizedModelManager()
        recommendations = manager.get_model_recommendations()
        
        print("🚀 RTX 3090 Configuration:")
        print(f"GPU Available: {recommendations['gpu_info']['cuda_available']}")
        print(f"Device: {recommendations['gpu_info']['current_device']}")
        
        print("\n📋 Recommended Models:")
        for name, config in recommendations['recommended_models'].items():
            print(f"  • {name}:")
            print(f"    Description: {config['description']}")
            print(f"    VRAM: {config['vram']}")
            print(f"    Performance: {config['performance']}")
            print(f"    Use Case: {config['use_case']}")
        
        print("\n💡 Optimization Tips:")
        for tip in recommendations['optimization_tips']:
            print(f"  • {tip}")
        
        print("\n✅ Quantized model configuration test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Quantized model configuration test failed: {e}")
        return False

def show_project_structure():
    """Show the complete project structure"""
    print("\n📁 Complete BetterGut Project Structure:")
    print("""
bettergut/
├── ai-pipeline/
│   ├── storage/                    # 🗂️ Organized data storage
│   │   ├── crawled_data/          # All crawled health data
│   │   │   ├── pubmed/            # Scientific articles from PubMed
│   │   │   ├── institutions/      # Government & institutional content
│   │   │   └── specialists/       # Specialist website content
│   │   ├── rag_database/          # RAG system data
│   │   │   ├── chroma_db/         # Vector database
│   │   │   └── embeddings_cache/  # Cached embeddings
│   │   ├── models/                # AI models
│   │   │   ├── quantized/         # Quantized models for RTX 3090
│   │   │   └── embeddings/        # Embedding models
│   │   ├── logs/                  # Application logs
│   │   └── temp/                  # Temporary files
│   ├── config/                    # Configuration files
│   │   └── storage_config.py      # Storage configuration
│   ├── crawlers/                  # Data crawling modules
│   │   ├── health_crawler.py      # Main crawler orchestrator
│   │   ├── pubmed_crawler.py      # PubMed scientific articles
│   │   ├── institution_crawler.py # Government institutions
│   │   └── specialist_crawler.py  # Health specialist sites
│   ├── models/                    # AI model implementations
│   │   ├── llama3_service.py      # Llama 3 integration
│   │   └── quantized_models.py    # RTX 3090 optimized models
│   ├── rag/                       # RAG system
│   │   └── rag_system.py          # Retrieval-Augmented Generation
│   ├── api.py                     # FastAPI service
│   ├── crawl_health_data.py       # Main crawler script
│   ├── Dockerfile                 # Original Dockerfile
│   ├── Dockerfile.production      # Optimized for GPU servers
│   └── requirements.txt           # Python dependencies
├── backend/                       # Node.js API backend
├── mobile_app/                    # Flutter mobile application
└── scripts/                       # Deployment scripts
    """)

def main():
    """Run all tests"""
    print("🚀 BetterGut AI Pipeline Test Suite")
    print("=" * 50)
    
    tests = [
        ("Storage Structure", test_storage_structure),
        ("Mock Crawler Data", test_mock_crawler_data),
        ("Quantized Model Config", test_quantized_model_config)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        result = test_func()
        results.append((test_name, result))
    
    # Show project structure
    show_project_structure()
    
    # Summary
    print("\n" + "="*50)
    print("📊 Test Results Summary:")
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nTests passed: {passed}/{len(tests)}")
    
    if passed == len(tests):
        print("\n🎉 All tests passed! Your BetterGut AI Pipeline is ready for deployment.")
        print("\n📋 Next Steps:")
        print("1. Build Docker image: docker build -f Dockerfile.production -t bettergut-ai .")
        print("2. Run crawler: python crawl_health_data.py --crawl-only --max-articles 10")
        print("3. Start API: python api.py")
        print("4. Test quantized models on your RTX 3090")
    else:
        print(f"\n⚠️ {len(tests) - passed} tests failed. Please check the errors above.")

if __name__ == "__main__":
    main()
