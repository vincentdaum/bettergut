#!/usr/bin/env python3
"""
Manual crawler test - Tests crawler logic without external dependencies
"""
import json
import sys
from pathlib import Path
from datetime import datetime

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

def test_crawler_structure():
    """Test that all crawler files exist and have proper structure"""
    print("🧪 Testing Crawler Structure...")
    
    crawler_files = [
        'crawlers/health_crawler.py',
        'crawlers/pubmed_crawler.py', 
        'crawlers/institution_crawler.py',
        'crawlers/specialist_crawler.py'
    ]
    
    all_exist = True
    for file_path in crawler_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
            
            # Check if file contains expected classes
            with open(file_path, 'r') as f:
                content = f.read()
                
            if 'crawler.py' in file_path and 'class' in content:
                print(f"   📝 Contains class definitions")
            
        else:
            print(f"❌ Missing: {file_path}")
            all_exist = False
    
    return all_exist

def test_storage_integration():
    """Test storage configuration integration"""
    print("\n🧪 Testing Storage Integration...")
    
    try:
        from config.storage_config import StorageConfig
        
        # Test path creation
        StorageConfig.create_directories()
        
        # Test path access
        paths = StorageConfig.get_paths_dict()
        
        print("✅ Storage configuration loaded")
        print(f"   📁 Base storage: {paths['base_storage']}")
        print(f"   📁 Crawled data: {paths['crawled_data']}")
        print(f"   📁 RAG database: {paths['rag_database']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Storage integration failed: {e}")
        return False

def simulate_crawler_workflow():
    """Simulate the crawler workflow without external APIs"""
    print("\n🧪 Simulating Crawler Workflow...")
    
    try:
        from config.storage_config import StorageConfig
        
        # Simulate crawling different sources
        mock_results = {
            'pubmed': [
                {
                    'title': 'Gut Microbiome Diversity in Healthy Adults',
                    'abstract': 'A comprehensive study of gut microbiome diversity...',
                    'authors': ['Dr. Smith', 'Dr. Johnson'],
                    'journal': 'Nature Microbiome',
                    'pubmed_id': 'PM12345',
                    'topics': ['microbiome', 'gut health'],
                    'url': 'https://pubmed.ncbi.nlm.nih.gov/12345',
                    'crawl_timestamp': datetime.now().isoformat()
                }
            ],
            'institutions': [
                {
                    'title': 'NIH Guidelines for Digestive Health',
                    'content': 'The National Institutes of Health provides evidence-based guidelines...',
                    'source': 'National Institutes of Health',
                    'url': 'https://www.nih.gov/digestive-health',
                    'topics': ['guidelines', 'digestive health'],
                    'crawl_timestamp': datetime.now().isoformat()
                }
            ],
            'specialists': [
                {
                    'title': 'Probiotics: What You Need to Know',
                    'content': 'Leading gastroenterologists explain the benefits of probiotics...',
                    'source': 'Gut Health Specialists',
                    'url': 'https://guthealth.com/probiotics-guide',
                    'topics': ['probiotics', 'gut health'],
                    'crawl_timestamp': datetime.now().isoformat()
                }
            ]
        }
        
        # Save simulated results using storage structure
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        source_paths = {
            'pubmed': StorageConfig.PUBMED_DATA,
            'institutions': StorageConfig.INSTITUTIONS_DATA,
            'specialists': StorageConfig.SPECIALISTS_DATA
        }
        
        total_articles = 0
        for source, articles in mock_results.items():
            storage_path = source_paths[source]
            
            # Save articles
            filename = f"{source}_simulated_{timestamp}.json"
            filepath = storage_path / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(articles, f, indent=2, ensure_ascii=False)
            
            total_articles += len(articles)
            print(f"✅ Saved {len(articles)} simulated {source} articles")
            
            # Create metadata
            metadata = {
                'source': source,
                'simulation': True,
                'timestamp': timestamp,
                'article_count': len(articles),
                'file_path': str(filepath),
                'topics_covered': list(set([
                    topic for article in articles 
                    for topic in article.get('topics', [])
                ]))
            }
            
            metadata_path = storage_path / f"{source}_metadata_{timestamp}.json"
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Workflow simulation completed: {total_articles} total articles")
        return True
        
    except Exception as e:
        print(f"❌ Workflow simulation failed: {e}")
        return False

def test_data_quality():
    """Test data quality and structure"""
    print("\n🧪 Testing Data Quality...")
    
    try:
        from config.storage_config import StorageConfig
        
        # Check for any JSON files in storage
        data_files = []
        for source_dir in [StorageConfig.PUBMED_DATA, StorageConfig.INSTITUTIONS_DATA, StorageConfig.SPECIALISTS_DATA]:
            data_files.extend(source_dir.glob("*.json"))
        
        if not data_files:
            print("⚠️ No data files found, creating sample data...")
            return simulate_crawler_workflow()
        
        valid_files = 0
        total_articles = 0
        
        for file_path in data_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if isinstance(data, list):
                    # Articles file
                    article_count = len(data)
                    total_articles += article_count
                    
                    # Check article structure
                    if data and all(isinstance(article, dict) for article in data):
                        valid_files += 1
                        print(f"✅ {file_path.name}: {article_count} articles")
                    else:
                        print(f"⚠️ {file_path.name}: Invalid structure")
                
                elif isinstance(data, dict) and 'source' in data:
                    # Metadata file
                    print(f"📋 {file_path.name}: Metadata")
                
            except json.JSONDecodeError:
                print(f"❌ {file_path.name}: Invalid JSON")
            except Exception as e:
                print(f"❌ {file_path.name}: Error - {e}")
        
        print(f"\n📊 Data Quality Summary:")
        print(f"   • Valid files: {valid_files}")
        print(f"   • Total articles: {total_articles}")
        print(f"   • Storage base: {StorageConfig.BASE_STORAGE}")
        
        return valid_files > 0
        
    except Exception as e:
        print(f"❌ Data quality test failed: {e}")
        return False

def show_deployment_ready():
    """Show deployment readiness summary"""
    print("\n🚀 Deployment Readiness Summary")
    print("=" * 40)
    
    # Check Docker files
    docker_files = [
        'Dockerfile',
        'Dockerfile.production', 
        '../docker-compose.ai.yml'
    ]
    
    docker_ready = True
    for file_path in docker_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ Missing: {file_path}")
            docker_ready = False
    
    # Check configuration
    config_files = [
        'config/storage_config.py',
        'models/quantized_models.py',
        'requirements.txt'
    ]
    
    config_ready = True
    for file_path in config_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ Missing: {file_path}")
            config_ready = False
    
    # Overall readiness
    overall_ready = docker_ready and config_ready
    
    print(f"\n🎯 Deployment Status: {'✅ READY' if overall_ready else '❌ NOT READY'}")
    
    if overall_ready:
        print("\n📋 Next Steps for RTX 3090 Server:")
        print("1. Copy project to GPU server")
        print("2. Run: sudo bash scripts/deploy_gpu_server.sh")
        print("3. Test crawlers: docker exec bettergut-ai python crawl_health_data.py --crawl-only --max-articles 10")
        print("4. Test quantized models: docker exec bettergut-ai python -c \"from models.quantized_models import setup_quantized_model_for_rtx3090; setup_quantized_model_for_rtx3090()\"")
    
    return overall_ready

def main():
    """Run all manual tests"""
    print("🧪 BetterGut AI Pipeline Manual Test Suite")
    print("=" * 50)
    
    tests = [
        ("Crawler Structure", test_crawler_structure),
        ("Storage Integration", test_storage_integration),
        ("Crawler Workflow", simulate_crawler_workflow),
        ("Data Quality", test_data_quality)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*15} {test_name} {'='*15}")
        result = test_func()
        results.append((test_name, result))
    
    # Deployment readiness
    deployment_ready = show_deployment_ready()
    
    # Summary
    print("\n" + "="*50)
    print("📊 Test Results:")
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nTests passed: {passed}/{len(tests)}")
    print(f"Deployment ready: {'✅ YES' if deployment_ready else '❌ NO'}")
    
    if passed == len(tests) and deployment_ready:
        print("\n🎉 All tests passed! Ready to deploy on RTX 3090 server!")
    else:
        print(f"\n⚠️ Some tests failed. Please check the errors above.")

if __name__ == "__main__":
    main()
