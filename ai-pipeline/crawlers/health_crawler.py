"""
Health Data Crawler - Collects nutrition and gut health information
from scientific and institutional sources for RAG pipeline
"""
import asyncio
import aiohttp
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlparse
import json
import time

from bs4 import BeautifulSoup
import feedparser
import requests
from tqdm import tqdm

from .pubmed_crawler import PubMedCrawler
from .institution_crawler import InstitutionCrawler
from .specialist_crawler import SpecialistCrawler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HealthDataCrawler:
    """Main orchestrator for health data collection"""
    
    def __init__(self, output_dir: str = "./data/crawled"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize specialized crawlers
        self.pubmed_crawler = PubMedCrawler()
        self.institution_crawler = InstitutionCrawler()
        self.specialist_crawler = SpecialistCrawler()
        
        # Crawling configuration
        self.session = None
        self.crawl_config = {
            'max_concurrent': 5,
            'delay_between_requests': 1.0,
            'timeout': 30,
            'max_retries': 3
        }
        
    async def __aenter__(self):
        """Async context manager entry"""
        connector = aiohttp.TCPConnector(limit=self.crawl_config['max_concurrent'])
        timeout = aiohttp.ClientTimeout(total=self.crawl_config['timeout'])
        self.session = aiohttp.ClientSession(connector=connector, timeout=timeout)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def crawl_all_sources(self, 
                               topics: List[str] = None,
                               max_articles_per_source: int = 100) -> Dict[str, List[Dict]]:
        """
        Crawl all configured health data sources
        
        Args:
            topics: List of health topics to focus on
            max_articles_per_source: Maximum articles per source
            
        Returns:
            Dictionary with source names and their collected articles
        """
        if topics is None:
            topics = [
                "gut health", "microbiome", "nutrition", "digestive health",
                "probiotics", "prebiotics", "fiber", "intestinal health",
                "food sensitivity", "IBS", "IBD", "gut-brain axis"
            ]
        
        logger.info(f"Starting health data crawl for topics: {topics}")
        
        results = {}
        
        # 1. Crawl Scientific Literature (API-based)
        logger.info("Crawling scientific literature...")
        try:
            pubmed_articles = await self.pubmed_crawler.search_articles(
                topics, max_results=max_articles_per_source
            )
            results['pubmed'] = pubmed_articles
            logger.info(f"Collected {len(pubmed_articles)} PubMed articles")
        except Exception as e:
            logger.error(f"PubMed crawling failed: {e}")
            results['pubmed'] = []
        
        # 2. Crawl Health Institutions (Sitemap-based)
        logger.info("Crawling health institutions...")
        try:
            institution_articles = await self.institution_crawler.crawl_institutions(
                topics, max_articles_per_source
            )
            results['institutions'] = institution_articles
            logger.info(f"Collected {len(institution_articles)} institutional articles")
        except Exception as e:
            logger.error(f"Institution crawling failed: {e}")
            results['institutions'] = []
        
        # 3. Crawl Specialist Sites (Focused crawling)
        logger.info("Crawling specialist sites...")
        try:
            specialist_articles = await self.specialist_crawler.crawl_specialist_sites(
                topics, max_articles_per_source
            )
            results['specialists'] = specialist_articles
            logger.info(f"Collected {len(specialist_articles)} specialist articles")
        except Exception as e:
            logger.error(f"Specialist crawling failed: {e}")
            results['specialists'] = []
        
        # Save results
        await self._save_crawl_results(results)
        
        total_articles = sum(len(articles) for articles in results.values())
        logger.info(f"Crawling completed. Total articles collected: {total_articles}")
        
        return results
    
    async def _save_crawl_results(self, results: Dict[str, List[Dict]]):
        """Save crawling results to JSON files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for source, articles in results.items():
            if articles:
                filename = f"{source}_articles_{timestamp}.json"
                filepath = self.output_dir / filename
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(articles, f, indent=2, ensure_ascii=False, default=str)
                
                logger.info(f"Saved {len(articles)} {source} articles to {filepath}")
    
    def get_crawl_statistics(self) -> Dict:
        """Get statistics about crawled data"""
        stats = {
            'total_files': 0,
            'total_articles': 0,
            'sources': {},
            'latest_crawl': None
        }
        
        for file_path in self.output_dir.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                source = file_path.stem.split('_')[0]
                article_count = len(data)
                
                stats['total_files'] += 1
                stats['total_articles'] += article_count
                stats['sources'][source] = stats['sources'].get(source, 0) + article_count
                
                # Update latest crawl time from filename
                try:
                    timestamp_str = '_'.join(file_path.stem.split('_')[-2:])
                    file_time = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                    if stats['latest_crawl'] is None or file_time > stats['latest_crawl']:
                        stats['latest_crawl'] = file_time
                except:
                    pass
                        
            except Exception as e:
                logger.warning(f"Could not read stats from {file_path}: {e}")
        
        return stats

# Standalone crawler functions for direct use
async def crawl_health_data(topics: List[str] = None, 
                           max_articles: int = 100,
                           output_dir: str = "./data/crawled") -> Dict[str, List[Dict]]:
    """
    Convenience function to crawl health data
    
    Args:
        topics: Health topics to search for
        max_articles: Maximum articles per source
        output_dir: Directory to save results
        
    Returns:
        Crawled articles by source
    """
    async with HealthDataCrawler(output_dir) as crawler:
        return await crawler.crawl_all_sources(topics, max_articles)

if __name__ == "__main__":
    # Example usage
    import sys
    
    topics = [
        "gut microbiome", "digestive health", "nutrition absorption",
        "probiotics", "fiber intake", "gut-brain connection"
    ]
    
    if len(sys.argv) > 1:
        max_articles = int(sys.argv[1])
    else:
        max_articles = 50
    
    print(f"Starting health data crawl for {max_articles} articles per source...")
    
    # Run the crawler
    results = asyncio.run(crawl_health_data(topics, max_articles))
    
    total = sum(len(articles) for articles in results.values())
    print(f"\n✅ Crawling completed!")
    print(f"📊 Total articles collected: {total}")
    
    for source, articles in results.items():
        print(f"   • {source}: {len(articles)} articles")
