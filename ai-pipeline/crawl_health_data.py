#!/usr/bin/env python3
"""
Main script to crawl health data and build RAG knowledge base
"""
import asyncio
import logging
import argparse
import sys
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

try:
    from crawlers.health_crawler import crawl_health_data
    from rag.rag_system import build_knowledge_base
except ImportError as e:
    print(f"Warning: Could not import modules: {e}")
    print("Please install requirements: pip install -r requirements.txt")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('./logs/crawler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def main():
    """Main function to orchestrate data crawling and knowledge base building"""
    parser = argparse.ArgumentParser(description='BetterGut Health Data Crawler')
    parser.add_argument('--max-articles', type=int, default=100,
                       help='Maximum articles per source (default: 100)')
    parser.add_argument('--topics', nargs='+', 
                       default=['gut health', 'microbiome', 'nutrition', 'digestive health'],
                       help='Health topics to search for')
    parser.add_argument('--crawl-only', action='store_true',
                       help='Only crawl data, do not build knowledge base')
    parser.add_argument('--build-only', action='store_true',
                       help='Only build knowledge base from existing data')
    parser.add_argument('--output-dir', default='./data/crawled',
                       help='Output directory for crawled data')
    parser.add_argument('--rag-db-path', default='./data/chroma_db',
                       help='Path for RAG vector database')
    
    args = parser.parse_args()
    
    logger.info("🚀 Starting BetterGut Health Data Pipeline")
    logger.info(f"Topics: {args.topics}")
    logger.info(f"Max articles per source: {args.max_articles}")
    
    # Create directories
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    Path(args.rag_db_path).mkdir(parents=True, exist_ok=True)
    Path('./logs').mkdir(parents=True, exist_ok=True)
    
    try:
        # Phase 1: Data Crawling
        if not args.build_only:
            logger.info("📊 Phase 1: Crawling health data from scientific sources...")
            
            results = await crawl_health_data(
                topics=args.topics,
                max_articles=args.max_articles,
                output_dir=args.output_dir
            )
            
            total_articles = sum(len(articles) for articles in results.values())
            logger.info(f"✅ Crawling completed! Total articles: {total_articles}")
            
            # Show breakdown by source
            for source, articles in results.items():
                logger.info(f"   • {source}: {len(articles)} articles")
        
        # Phase 2: Knowledge Base Building
        if not args.crawl_only:
            logger.info("🧠 Phase 2: Building RAG knowledge base...")
            
            rag_system = await build_knowledge_base(
                data_dir=args.output_dir,
                chroma_db_path=args.rag_db_path
            )
            
            # Show statistics
            stats = rag_system.get_collection_stats()
            logger.info(f"✅ Knowledge base built successfully!")
            logger.info(f"   • Total chunks: {stats['total_chunks']}")
            logger.info(f"   • Sources: {list(stats['sources'].keys())}")
            
            # Test the knowledge base
            logger.info("🧪 Testing knowledge base...")
            test_queries = [
                "What foods improve gut microbiome?",
                "How does fiber affect digestive health?",
                "What are the benefits of probiotics?"
            ]
            
            for query in test_queries:
                context = rag_system.get_context_for_query(query)
                context_length = len(context)
                logger.info(f"   • Query: '{query}' → {context_length} chars of context")
        
        logger.info("🎉 Pipeline completed successfully!")
        
        if not args.crawl_only and not args.build_only:
            logger.info("\n📋 Next steps:")
            logger.info("1. Start the AI pipeline API: python api.py")
            logger.info("2. Start the backend API: cd ../backend && npm run dev")
            logger.info("3. Start developing your Flutter app!")
            logger.info("\n💡 The knowledge base is ready for LLM-powered health insights!")
    
    except KeyboardInterrupt:
        logger.info("\n⏹️ Pipeline interrupted by user")
    except Exception as e:
        logger.error(f"❌ Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Run the pipeline
    asyncio.run(main())
