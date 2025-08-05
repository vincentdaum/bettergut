"""
Medical Crawler Orchestrator - Manages all specialized medical data crawlers
for comprehensive gut health and nutrition information collection
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

# Import all specialized crawlers
from .mayo_clinic_crawler import MayoClinicCrawler
from .harvard_nutrition_crawler import HarvardNutritionCrawler
from .academy_nutrition_crawler import AcademyNutritionCrawler
from .nih_niddk_crawler import NIHNIDDKCrawler
from .iffgd_crawler import IFFGDCrawler
from .johns_hopkins_crawler import JohnsHopkinsCrawler
from .cleveland_clinic_crawler import ClevelandClinicCrawler
from .aga_crawler import AGACrawler
from .crohns_colitis_foundation_crawler import CrohnsColitisFoundationCrawler
from .iffgd_comprehensive_crawler import IFFGDComprehensiveCrawler

# Import existing crawlers
from .pubmed_crawler import PubMedCrawler
from .nutrition_crawler import NutritionCrawler

# Import database utilities
from ..database.database_utils import store_crawled_data

logger = logging.getLogger(__name__)

class MedicalCrawlerOrchestrator:
    """Orchestrates all medical crawlers for comprehensive data collection"""
    
    def __init__(self):
        self.crawlers = {
            'mayo_clinic': MayoClinicCrawler(),
            'harvard_nutrition': HarvardNutritionCrawler(),
            'academy_nutrition': AcademyNutritionCrawler(),
            'nih_niddk': NIHNIDDKCrawler(),
            'iffgd': IFFGDCrawler(),
            'johns_hopkins': JohnsHopkinsCrawler(),
            'cleveland_clinic': ClevelandClinicCrawler(),
            'aga': AGACrawler(),
            'crohns_colitis_foundation': CrohnsColitisFoundationCrawler(),
            'iffgd_comprehensive': IFFGDComprehensiveCrawler(),
            'pubmed': PubMedCrawler(),
            'nutrition_general': NutritionCrawler()
        }
        
        self.crawler_priorities = {
            'tier_1': [
                'mayo_clinic', 'harvard_nutrition', 'nih_niddk', 'johns_hopkins'
            ],
            'tier_2': [
                'cleveland_clinic', 'academy_nutrition', 'aga', 'iffgd',
                'crohns_colitis_foundation', 'iffgd_comprehensive'
            ],
            'tier_3': [
                'pubmed', 'nutrition_general'
            ]
        }
        
        self.gut_health_topics = [
            'gut microbiome', 'digestive health', 'bowel movements',
            'fiber intake', 'probiotics', 'prebiotics', 'inflammation',
            'ibs management', 'crohns disease', 'ulcerative colitis',
            'food allergies', 'food intolerances', 'elimination diet',
            'low fodmap diet', 'anti-inflammatory diet', 'mediterranean diet',
            'gut-brain axis', 'stress and digestion', 'meal timing',
            'nutritional deficiencies', 'digestive enzymes', 'bile acids',
            'short chain fatty acids', 'intestinal permeability'
        ]
    
    async def crawl_all_sources(self,
                              topics: Optional[List[str]] = None,
                              max_articles_per_source: int = 50,
                              priority_tiers: Optional[List[str]] = None,
                              store_in_database: bool = True) -> Dict[str, List[Dict]]:
        """
        Crawl all medical sources for comprehensive gut health information
        
        Args:
            topics: Specific topics to search for (defaults to gut_health_topics)
            max_articles_per_source: Maximum articles per crawler
            priority_tiers: Which priority tiers to crawl ('tier_1', 'tier_2', 'tier_3')
            store_in_database: Whether to store results in database
            
        Returns:
            Dictionary mapping source names to collected articles
        """
        if topics is None:
            topics = self.gut_health_topics
        
        if priority_tiers is None:
            priority_tiers = ['tier_1', 'tier_2']
        
        logger.info(f"Starting comprehensive medical crawl for {len(topics)} topics across priority tiers: {priority_tiers}")
        
        # Determine which crawlers to run
        active_crawlers = []
        for tier in priority_tiers:
            if tier in self.crawler_priorities:
                active_crawlers.extend(self.crawler_priorities[tier])
        
        results = {}
        total_articles = 0
        
        # Process each crawler
        for crawler_name in active_crawlers:
            if crawler_name not in self.crawlers:
                logger.warning(f"Crawler {crawler_name} not found")
                continue
            
            try:
                logger.info(f"Starting crawl with {crawler_name}")
                
                crawler = self.crawlers[crawler_name]
                articles = await self._run_crawler(
                    crawler, crawler_name, topics, max_articles_per_source
                )
                
                if articles:
                    results[crawler_name] = articles
                    total_articles += len(articles)
                    
                    logger.info(f"Collected {len(articles)} articles from {crawler_name}")
                    
                    # Store in database if requested
                    if store_in_database:
                        await self._store_articles(articles, crawler_name)
                else:
                    logger.warning(f"No articles collected from {crawler_name}")
                
                # Rate limiting between crawlers
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Error crawling {crawler_name}: {e}")
                results[crawler_name] = []
        
        logger.info(f"Comprehensive crawl completed. Total articles collected: {total_articles}")
        
        # Generate summary report
        await self._generate_crawl_report(results, topics, priority_tiers)
        
        return results
    
    async def _run_crawler(self,
                         crawler: Any,
                         crawler_name: str,
                         topics: List[str],
                         max_articles: int) -> List[Dict]:
        """Run a specific crawler based on its type"""
        try:
            # Determine crawler method based on crawler name
            if hasattr(crawler, f'crawl_{crawler_name}'):
                method = getattr(crawler, f'crawl_{crawler_name}')
            elif hasattr(crawler, 'crawl_mayo_clinic') and 'mayo' in crawler_name:
                method = crawler.crawl_mayo_clinic
            elif hasattr(crawler, 'crawl_harvard_nutrition') and 'harvard' in crawler_name:
                method = crawler.crawl_harvard_nutrition
            elif hasattr(crawler, 'crawl_academy_nutrition') and 'academy' in crawler_name:
                method = crawler.crawl_academy_nutrition
            elif hasattr(crawler, 'crawl_nih_niddk') and 'nih' in crawler_name:
                method = crawler.crawl_nih_niddk
            elif hasattr(crawler, 'crawl_iffgd') and 'iffgd' in crawler_name and 'comprehensive' not in crawler_name:
                method = crawler.crawl_iffgd
            elif hasattr(crawler, 'crawl_iffgd_comprehensive') and 'comprehensive' in crawler_name:
                method = crawler.crawl_iffgd_comprehensive
            elif hasattr(crawler, 'crawl_johns_hopkins') and 'johns' in crawler_name:
                method = crawler.crawl_johns_hopkins
            elif hasattr(crawler, 'crawl_cleveland_clinic') and 'cleveland' in crawler_name:
                method = crawler.crawl_cleveland_clinic
            elif hasattr(crawler, 'crawl_aga') and 'aga' in crawler_name:
                method = crawler.crawl_aga
            elif hasattr(crawler, 'crawl_crohns_colitis_foundation') and 'crohns' in crawler_name:
                method = crawler.crawl_crohns_colitis_foundation
            elif hasattr(crawler, 'search_pubmed') and 'pubmed' in crawler_name:
                method = crawler.search_pubmed
            elif hasattr(crawler, 'crawl_nutrition_sites') and 'nutrition' in crawler_name:
                method = crawler.crawl_nutrition_sites
            else:
                logger.error(f"No suitable method found for crawler {crawler_name}")
                return []
            
            # Run the crawler method
            if 'pubmed' in crawler_name:
                # PubMed crawler has different parameters
                articles = await method(query=' OR '.join(topics[:5]), max_results=max_articles)
            else:
                articles = await method(topics=topics, max_articles=max_articles)
            
            return articles if articles else []
            
        except Exception as e:
            logger.error(f"Error running crawler {crawler_name}: {e}")
            return []
    
    async def _store_articles(self, articles: List[Dict], source: str) -> None:
        """Store articles in the database"""
        try:
            # Prepare articles for database storage
            processed_articles = []
            for article in articles:
                processed_article = {
                    **article,
                    'crawler_source': source,
                    'crawl_batch_id': datetime.now().strftime('%Y%m%d_%H%M%S'),
                    'processed_at': datetime.now().isoformat()
                }
                processed_articles.append(processed_article)
            
            # Store using existing database utilities
            await store_crawled_data(processed_articles)
            
            logger.info(f"Stored {len(processed_articles)} articles from {source} in database")
            
        except Exception as e:
            logger.error(f"Error storing articles from {source}: {e}")
    
    async def _generate_crawl_report(self,
                                   results: Dict[str, List[Dict]],
                                   topics: List[str],
                                   priority_tiers: List[str]) -> None:
        """Generate a comprehensive crawl report"""
        try:
            report = {
                'crawl_summary': {
                    'timestamp': datetime.now().isoformat(),
                    'topics_searched': topics,
                    'priority_tiers': priority_tiers,
                    'total_sources': len(results),
                    'total_articles': sum(len(articles) for articles in results.values())
                },
                'source_breakdown': {},
                'topic_coverage': {},
                'content_types': {},
                'quality_metrics': {}
            }
            
            # Source breakdown
            for source, articles in results.items():
                report['source_breakdown'][source] = {
                    'article_count': len(articles),
                    'avg_content_length': sum(len(a.get('content', '')) for a in articles) / len(articles) if articles else 0,
                    'unique_authors': len(set(a.get('author', 'Unknown') for a in articles)),
                    'date_range': self._get_date_range(articles)
                }
            
            # Topic coverage analysis
            for topic in topics:
                topic_articles = []
                for articles in results.values():
                    topic_articles.extend([
                        a for a in articles 
                        if topic.lower() in a.get('content', '').lower() or 
                           topic.lower() in a.get('title', '').lower()
                    ])
                report['topic_coverage'][topic] = len(topic_articles)
            
            # Content type analysis
            content_types = {}
            for articles in results.values():
                for article in articles:
                    content_type = article.get('content_type', 'unknown')
                    content_types[content_type] = content_types.get(content_type, 0) + 1
            report['content_types'] = content_types
            
            # Quality metrics
            all_articles = [article for articles in results.values() for article in articles]
            report['quality_metrics'] = {
                'avg_content_length': sum(len(a.get('content', '')) for a in all_articles) / len(all_articles) if all_articles else 0,
                'articles_with_authors': sum(1 for a in all_articles if a.get('author') and a['author'] != 'Unknown'),
                'articles_with_dates': sum(1 for a in all_articles if a.get('publication_date')),
                'peer_reviewed_articles': sum(1 for a in all_articles if 'peer_reviewed' in a.get('content_type', '').lower())
            }
            
            # Save report
            report_filename = f"medical_crawl_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_filename, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            logger.info(f"Crawl report saved to {report_filename}")
            
        except Exception as e:
            logger.error(f"Error generating crawl report: {e}")
    
    def _get_date_range(self, articles: List[Dict]) -> Dict[str, str]:
        """Get date range from articles"""
        dates = [a.get('publication_date') for a in articles if a.get('publication_date')]
        if not dates:
            return {'earliest': 'Unknown', 'latest': 'Unknown'}
        
        try:
            parsed_dates = [datetime.fromisoformat(d.replace('Z', '+00:00')) for d in dates if d]
            if parsed_dates:
                return {
                    'earliest': min(parsed_dates).strftime('%Y-%m-%d'),
                    'latest': max(parsed_dates).strftime('%Y-%m-%d')
                }
        except:
            pass
        
        return {'earliest': min(dates), 'latest': max(dates)}
    
    async def crawl_priority_tier(self, tier: str, **kwargs) -> Dict[str, List[Dict]]:
        """Crawl a specific priority tier"""
        if tier not in self.crawler_priorities:
            raise ValueError(f"Invalid tier: {tier}. Available: {list(self.crawler_priorities.keys())}")
        
        return await self.crawl_all_sources(
            priority_tiers=[tier],
            **kwargs
        )
    
    async def crawl_specific_sources(self, 
                                   source_names: List[str],
                                   **kwargs) -> Dict[str, List[Dict]]:
        """Crawl specific sources by name"""
        # Temporarily modify crawler priorities
        original_priorities = self.crawler_priorities.copy()
        self.crawler_priorities = {'custom': source_names}
        
        try:
            results = await self.crawl_all_sources(
                priority_tiers=['custom'],
                **kwargs
            )
        finally:
            # Restore original priorities
            self.crawler_priorities = original_priorities
        
        return results
    
    def get_available_crawlers(self) -> Dict[str, List[str]]:
        """Get list of available crawlers by priority tier"""
        return self.crawler_priorities.copy()
    
    def get_crawler_info(self, crawler_name: str) -> Dict[str, Any]:
        """Get information about a specific crawler"""
        if crawler_name not in self.crawlers:
            return {'error': f'Crawler {crawler_name} not found'}
        
        crawler = self.crawlers[crawler_name]
        
        # Find which tier this crawler belongs to
        tier = None
        for tier_name, crawlers in self.crawler_priorities.items():
            if crawler_name in crawlers:
                tier = tier_name
                break
        
        return {
            'name': crawler_name,
            'class': crawler.__class__.__name__,
            'priority_tier': tier,
            'base_url': getattr(crawler, 'base_url', 'Unknown'),
            'description': crawler.__class__.__doc__ or 'No description available'
        }
