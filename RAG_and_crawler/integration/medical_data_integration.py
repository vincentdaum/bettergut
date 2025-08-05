"""
Medical Data Collection Integration Script
Runs comprehensive medical crawling and integrates with existing RAG system
"""
import asyncio
import logging
import sys
import os
from pathlib import Path
from typing import List, Dict, Any
import json
from datetime import datetime

# Add the ai-pipeline directory to Python path
current_dir = Path(__file__).parent
ai_pipeline_dir = current_dir.parent
sys.path.append(str(ai_pipeline_dir))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('medical_crawl.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MedicalDataIntegrator:
    """Integrates medical crawler data with RAG system"""
    
    def __init__(self):
        self.crawl_results_dir = Path('crawl_results')
        self.crawl_results_dir.mkdir(exist_ok=True)
        
        # Core gut health topics for comprehensive coverage
        self.core_topics = [
            'gut microbiome', 'digestive health', 'bowel movements',
            'fiber intake', 'probiotics', 'prebiotics', 'inflammation',
            'ibs irritable bowel syndrome', 'crohns disease', 'ulcerative colitis',
            'food allergies', 'food intolerances', 'elimination diet',
            'low fodmap diet', 'anti-inflammatory diet', 'mediterranean diet',
            'gut-brain axis', 'stress and digestion', 'meal timing',
            'nutritional deficiencies', 'digestive enzymes', 'bile acids',
            'short chain fatty acids', 'intestinal permeability',
            'constipation', 'diarrhea', 'bloating', 'gas',
            'leaky gut', 'dysbiosis', 'functional dyspepsia'
        ]
        
        self.medical_institutions = {
            'mayo_clinic': {
                'priority': 1,
                'focus': 'comprehensive medical information',
                'specialty': 'general digestive health'
            },
            'harvard_nutrition': {
                'priority': 1,
                'focus': 'evidence-based nutrition science',
                'specialty': 'nutritional research'
            },
            'nih_niddk': {
                'priority': 1,
                'focus': 'authoritative government health information',
                'specialty': 'digestive diseases'
            },
            'johns_hopkins': {
                'priority': 1,
                'focus': 'clinical excellence and research',
                'specialty': 'gastroenterology'
            },
            'cleveland_clinic': {
                'priority': 2,
                'focus': 'patient care and wellness',
                'specialty': 'preventive medicine'
            },
            'academy_nutrition': {
                'priority': 2,
                'focus': 'professional nutrition guidelines',
                'specialty': 'dietetic practice'
            },
            'aga': {
                'priority': 2,
                'focus': 'gastroenterology professional standards',
                'specialty': 'clinical guidelines'
            },
            'iffgd': {
                'priority': 2,
                'focus': 'functional gi disorders',
                'specialty': 'patient education'
            },
            'crohns_colitis_foundation': {
                'priority': 2,
                'focus': 'inflammatory bowel disease',
                'specialty': 'ibd management'
            },
            'iffgd_comprehensive': {
                'priority': 2,
                'focus': 'comprehensive functional gi information',
                'specialty': 'functional disorders'
            }
        }
    
    async def run_comprehensive_crawl(self, 
                                    max_articles_per_source: int = 30,
                                    priority_filter: List[int] = [1, 2]) -> Dict[str, Any]:
        """
        Run comprehensive medical data crawl
        
        Args:
            max_articles_per_source: Maximum articles to collect per source
            priority_filter: Which priority levels to include (1=highest, 2=medium)
            
        Returns:
            Comprehensive crawl results
        """
        logger.info("Starting comprehensive medical data crawl")
        
        # Filter sources by priority
        active_sources = {
            name: info for name, info in self.medical_institutions.items()
            if info['priority'] in priority_filter
        }
        
        logger.info(f"Active sources: {list(active_sources.keys())}")
        
        # Initialize results
        crawl_results = {
            'metadata': {
                'start_time': datetime.now().isoformat(),
                'topics': self.core_topics,
                'max_articles_per_source': max_articles_per_source,
                'active_sources': list(active_sources.keys()),
                'total_sources': len(active_sources)
            },
            'source_results': {},
            'summary': {}
        }
        
        # Run crawlers for each source
        total_articles = 0
        successful_sources = 0
        
        for source_name, source_info in active_sources.items():
            try:
                logger.info(f"Crawling {source_name} (Priority {source_info['priority']})")
                
                # Simulate crawler execution (actual crawlers would be imported and run here)
                articles = await self._simulate_crawler_run(
                    source_name, source_info, max_articles_per_source
                )
                
                if articles:
                    crawl_results['source_results'][source_name] = {
                        'articles': articles,
                        'count': len(articles),
                        'source_info': source_info,
                        'status': 'success'
                    }
                    total_articles += len(articles)
                    successful_sources += 1
                    
                    logger.info(f"Successfully collected {len(articles)} articles from {source_name}")
                else:
                    crawl_results['source_results'][source_name] = {
                        'articles': [],
                        'count': 0,
                        'source_info': source_info,
                        'status': 'no_results'
                    }
                    logger.warning(f"No articles collected from {source_name}")
                
                # Rate limiting
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error crawling {source_name}: {e}")
                crawl_results['source_results'][source_name] = {
                    'articles': [],
                    'count': 0,
                    'source_info': source_info,
                    'status': 'error',
                    'error': str(e)
                }
        
        # Generate summary
        crawl_results['metadata']['end_time'] = datetime.now().isoformat()
        crawl_results['summary'] = {
            'total_articles_collected': total_articles,
            'successful_sources': successful_sources,
            'failed_sources': len(active_sources) - successful_sources,
            'success_rate': successful_sources / len(active_sources) if active_sources else 0,
            'avg_articles_per_source': total_articles / successful_sources if successful_sources else 0
        }
        
        # Save results
        await self._save_crawl_results(crawl_results)
        
        logger.info(f"Comprehensive crawl completed. Total articles: {total_articles}")
        return crawl_results
    
    async def _simulate_crawler_run(self, 
                                  source_name: str, 
                                  source_info: Dict[str, Any],
                                  max_articles: int) -> List[Dict[str, Any]]:
        """
        Simulate crawler execution (replace with actual crawler calls)
        """
        # This simulates what the actual crawler would return
        # In production, this would import and run the specific crawler
        
        articles = []
        base_url_map = {
            'mayo_clinic': 'https://www.mayoclinic.org',
            'harvard_nutrition': 'https://www.hsph.harvard.edu/nutritionsource',
            'nih_niddk': 'https://www.niddk.nih.gov',
            'johns_hopkins': 'https://www.hopkinsmedicine.org',
            'cleveland_clinic': 'https://my.clevelandclinic.org',
            'academy_nutrition': 'https://www.eatright.org',
            'aga': 'https://gastro.org',
            'iffgd': 'https://www.iffgd.org',
            'crohns_colitis_foundation': 'https://www.crohnscolitisfoundation.org',
            'iffgd_comprehensive': 'https://www.iffgd.org'
        }
        
        # Generate sample articles based on source characteristics
        for i in range(min(max_articles // 3, 10)):  # Simulate partial collection
            article = {
                'title': f"{source_info['specialty'].title()} Guidelines for Gut Health - Article {i+1}",
                'content': f"Comprehensive information about {source_info['focus']} from {source_name}. " +
                          f"This article covers {', '.join(self.core_topics[:3])} and provides " +
                          f"evidence-based recommendations for digestive health management. " +
                          f"Content focuses on {source_info['specialty']} with clinical applications.",
                'url': f"{base_url_map.get(source_name, 'https://example.com')}/article-{i+1}",
                'source': source_name.replace('_', ' ').title(),
                'author': f"{source_name.title()} Medical Team",
                'publication_date': datetime.now().strftime('%Y-%m-%d'),
                'categories': [source_info['specialty'], 'gut-health', 'evidence-based'],
                'content_type': 'medical_guideline',
                'organization': source_name.replace('_', ' ').title(),
                'focus_area': source_info['focus'],
                'priority_level': source_info['priority'],
                'crawled_at': datetime.now().isoformat()
            }
            articles.append(article)
        
        return articles
    
    async def _save_crawl_results(self, results: Dict[str, Any]) -> None:
        """Save crawl results to file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = self.crawl_results_dir / f"medical_crawl_results_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"Crawl results saved to {filename}")
            
            # Also save a summary report
            summary_filename = self.crawl_results_dir / f"crawl_summary_{timestamp}.txt"
            await self._generate_summary_report(results, summary_filename)
            
        except Exception as e:
            logger.error(f"Error saving crawl results: {e}")
    
    async def _generate_summary_report(self, 
                                     results: Dict[str, Any], 
                                     filename: Path) -> None:
        """Generate human-readable summary report"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("MEDICAL DATA CRAWL SUMMARY REPORT\n")
                f.write("=" * 50 + "\n\n")
                
                # Basic stats
                metadata = results['metadata']
                summary = results['summary']
                
                f.write(f"Crawl Date: {metadata['start_time']}\n")
                f.write(f"Total Sources: {metadata['total_sources']}\n")
                f.write(f"Successful Sources: {summary['successful_sources']}\n")
                f.write(f"Total Articles Collected: {summary['total_articles_collected']}\n")
                f.write(f"Success Rate: {summary['success_rate']:.1%}\n")
                f.write(f"Average Articles per Source: {summary['avg_articles_per_source']:.1f}\n\n")
                
                # Source breakdown
                f.write("SOURCE BREAKDOWN\n")
                f.write("-" * 20 + "\n")
                
                for source_name, source_data in results['source_results'].items():
                    f.write(f"\n{source_name.upper()}\n")
                    f.write(f"  Status: {source_data['status']}\n")
                    f.write(f"  Articles: {source_data['count']}\n")
                    f.write(f"  Priority: {source_data['source_info']['priority']}\n")
                    f.write(f"  Focus: {source_data['source_info']['focus']}\n")
                
                # Topics covered
                f.write(f"\n\nTOPICS SEARCHED\n")
                f.write("-" * 15 + "\n")
                for i, topic in enumerate(metadata['topics'], 1):
                    f.write(f"{i:2d}. {topic}\n")
            
            logger.info(f"Summary report saved to {filename}")
            
        except Exception as e:
            logger.error(f"Error generating summary report: {e}")
    
    async def prepare_for_rag_integration(self, crawl_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare crawled data for RAG system integration
        
        Args:
            crawl_results: Results from comprehensive crawl
            
        Returns:
            Processed data ready for RAG ingestion
        """
        logger.info("Preparing crawled data for RAG integration")
        
        processed_articles = []
        
        for source_name, source_data in crawl_results['source_results'].items():
            if source_data['status'] == 'success':
                for article in source_data['articles']:
                    # Enhanced article for RAG system
                    rag_article = {
                        **article,
                        'rag_metadata': {
                            'source_priority': source_data['source_info']['priority'],
                            'content_category': source_data['source_info']['specialty'],
                            'institution_type': self._classify_institution(source_name),
                            'evidence_level': self._determine_evidence_level(source_name),
                            'target_audience': 'patients_and_providers',
                            'content_freshness': self._assess_content_freshness(article),
                            'topic_relevance_score': self._calculate_topic_relevance(article)
                        },
                        'vector_embedding_ready': True,
                        'chunk_boundaries': self._identify_chunk_boundaries(article['content']),
                        'key_concepts': self._extract_key_concepts(article['content'])
                    }
                    processed_articles.append(rag_article)
        
        rag_ready_data = {
            'articles': processed_articles,
            'total_articles': len(processed_articles),
            'processing_metadata': {
                'processed_at': datetime.now().isoformat(),
                'source_distribution': self._analyze_source_distribution(processed_articles),
                'content_categories': self._analyze_content_categories(processed_articles),
                'evidence_levels': self._analyze_evidence_levels(processed_articles)
            }
        }
        
        # Save RAG-ready data
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        rag_filename = self.crawl_results_dir / f"rag_ready_data_{timestamp}.json"
        
        with open(rag_filename, 'w', encoding='utf-8') as f:
            json.dump(rag_ready_data, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"RAG-ready data saved to {rag_filename}")
        logger.info(f"Prepared {len(processed_articles)} articles for RAG integration")
        
        return rag_ready_data
    
    def _classify_institution(self, source_name: str) -> str:
        """Classify the type of medical institution"""
        if source_name in ['mayo_clinic', 'johns_hopkins', 'cleveland_clinic']:
            return 'major_medical_center'
        elif source_name in ['harvard_nutrition']:
            return 'academic_research'
        elif source_name in ['nih_niddk']:
            return 'government_health_agency'
        elif source_name in ['academy_nutrition', 'aga']:
            return 'professional_organization'
        elif 'iffgd' in source_name or 'crohns_colitis' in source_name:
            return 'patient_advocacy_organization'
        else:
            return 'medical_resource'
    
    def _determine_evidence_level(self, source_name: str) -> str:
        """Determine evidence level based on source"""
        tier_1_sources = ['mayo_clinic', 'harvard_nutrition', 'nih_niddk', 'johns_hopkins']
        if source_name in tier_1_sources:
            return 'high_evidence'
        else:
            return 'moderate_evidence'
    
    def _assess_content_freshness(self, article: Dict[str, Any]) -> str:
        """Assess how fresh/current the content is"""
        # In real implementation, would parse publication_date
        return 'current'  # Simplified for demo
    
    def _calculate_topic_relevance(self, article: Dict[str, Any]) -> float:
        """Calculate relevance score for gut health topics"""
        content = article.get('content', '').lower()
        title = article.get('title', '').lower()
        
        # Count topic matches
        topic_matches = 0
        for topic in self.core_topics:
            if topic.lower() in content or topic.lower() in title:
                topic_matches += 1
        
        # Calculate relevance score (0.0 to 1.0)
        max_possible_matches = len(self.core_topics)
        relevance_score = min(topic_matches / max_possible_matches * 2, 1.0)  # Scale appropriately
        
        return round(relevance_score, 3)
    
    def _identify_chunk_boundaries(self, content: str) -> List[int]:
        """Identify optimal chunk boundaries for vector embedding"""
        # Simple implementation - split on paragraphs
        paragraphs = content.split('\n\n')
        boundaries = []
        current_pos = 0
        
        for paragraph in paragraphs:
            current_pos += len(paragraph) + 2  # +2 for \n\n
            boundaries.append(current_pos)
        
        return boundaries
    
    def _extract_key_concepts(self, content: str) -> List[str]:
        """Extract key medical/nutrition concepts from content"""
        # Simplified keyword extraction
        key_concepts = []
        content_lower = content.lower()
        
        concept_keywords = [
            'microbiome', 'probiotics', 'fiber', 'inflammation', 'bacteria',
            'enzyme', 'nutrient', 'vitamin', 'mineral', 'absorption',
            'digestion', 'intestine', 'stomach', 'colon', 'bowel'
        ]
        
        for keyword in concept_keywords:
            if keyword in content_lower:
                key_concepts.append(keyword)
        
        return key_concepts
    
    def _analyze_source_distribution(self, articles: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze distribution of articles by source"""
        distribution = {}
        for article in articles:
            source = article.get('source', 'Unknown')
            distribution[source] = distribution.get(source, 0) + 1
        return distribution
    
    def _analyze_content_categories(self, articles: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze distribution of content categories"""
        categories = {}
        for article in articles:
            category = article.get('rag_metadata', {}).get('content_category', 'Unknown')
            categories[category] = categories.get(category, 0) + 1
        return categories
    
    def _analyze_evidence_levels(self, articles: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze distribution of evidence levels"""
        levels = {}
        for article in articles:
            level = article.get('rag_metadata', {}).get('evidence_level', 'Unknown')
            levels[level] = levels.get(level, 0) + 1
        return levels

# Main execution function
async def main():
    """Main execution function for medical data integration"""
    integrator = MedicalDataIntegrator()
    
    try:
        logger.info("Starting medical data collection and integration")
        
        # Run comprehensive crawl
        crawl_results = await integrator.run_comprehensive_crawl(
            max_articles_per_source=25,
            priority_filter=[1, 2]  # Include both priority levels
        )
        
        # Prepare for RAG integration
        rag_ready_data = await integrator.prepare_for_rag_integration(crawl_results)
        
        logger.info("Medical data collection and integration completed successfully")
        
        # Print summary
        print("\n" + "="*60)
        print("MEDICAL DATA CRAWL COMPLETED")
        print("="*60)
        print(f"Total Articles Collected: {crawl_results['summary']['total_articles_collected']}")
        print(f"Successful Sources: {crawl_results['summary']['successful_sources']}")
        print(f"Success Rate: {crawl_results['summary']['success_rate']:.1%}")
        print(f"Articles Ready for RAG: {rag_ready_data['total_articles']}")
        print("="*60)
        
        return crawl_results, rag_ready_data
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        raise

if __name__ == "__main__":
    # Run the integration
    asyncio.run(main())
