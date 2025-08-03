"""
Institution Crawler - Fetches health information from government
and institutional health websites using sitemap-based crawling
"""
import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse
import xml.etree.ElementTree as ET
import time
import re

logger = logging.getLogger(__name__)

class InstitutionCrawler:
    """Crawler for health institutions and government sites"""
    
    def __init__(self):
        self.institutions = {
            'nih': {
                'name': 'National Institutes of Health',
                'base_url': 'https://www.nih.gov',
                'sitemap_url': 'https://www.nih.gov/sitemap.xml',
                'health_paths': ['/health-information', '/news-events/news-releases'],
                'content_selectors': ['article', '.page-content', '.content-area']
            },
            'cdc': {
                'name': 'Centers for Disease Control',
                'base_url': 'https://www.cdc.gov',
                'sitemap_url': 'https://www.cdc.gov/sitemap.xml',
                'health_paths': ['/nutrition', '/healthyeating', '/digestive'],
                'content_selectors': ['.module-content', '.card-body', '.col-md-9']
            },
            'nccih': {
                'name': 'National Center for Complementary Health',
                'base_url': 'https://www.nccih.nih.gov',
                'sitemap_url': 'https://www.nccih.nih.gov/sitemap.xml',
                'health_paths': ['/health', '/research'],
                'content_selectors': ['main', '.content', '.page-content']
            },
            'harvard_nutrition': {
                'name': 'Harvard Nutrition Source',
                'base_url': 'https://www.hsph.harvard.edu',
                'sitemap_url': 'https://www.hsph.harvard.edu/sitemap.xml',
                'health_paths': ['/nutritionsource'],
                'content_selectors': ['.entry-content', '.post-content', 'article']
            }
        }
    
    async def crawl_institutions(self, 
                               topics: List[str], 
                               max_articles: int = 100) -> List[Dict]:
        """
        Crawl all configured institutions for health content
        
        Args:
            topics: List of health topics to search for
            max_articles: Maximum articles per institution
            
        Returns:
            List of articles from all institutions
        """
        all_articles = []
        
        async with aiohttp.ClientSession() as session:
            for inst_id, config in self.institutions.items():
                try:
                    logger.info(f"Crawling {config['name']}...")
                    
                    articles = await self._crawl_institution(
                        session, inst_id, config, topics, max_articles
                    )
                    
                    all_articles.extend(articles)
                    logger.info(f"Collected {len(articles)} articles from {config['name']}")
                    
                    # Rate limiting between institutions
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Error crawling {config['name']}: {e}")
        
        return all_articles
    
    async def _crawl_institution(self, 
                               session: aiohttp.ClientSession,
                               inst_id: str,
                               config: Dict,
                               topics: List[str],
                               max_articles: int) -> List[Dict]:
        """Crawl a single institution"""
        articles = []
        
        try:
            # Get relevant URLs from sitemap
            urls = await self._get_relevant_urls(session, config, topics)
            
            # Limit URLs to process
            urls = urls[:max_articles]
            
            # Process URLs in batches
            batch_size = 5
            for i in range(0, len(urls), batch_size):
                batch_urls = urls[i:i + batch_size]
                
                batch_articles = await asyncio.gather(
                    *[self._scrape_article(session, url, config, inst_id) 
                      for url in batch_urls],
                    return_exceptions=True
                )
                
                # Filter out exceptions and None results
                for article in batch_articles:
                    if isinstance(article, dict):
                        articles.append(article)
                
                # Rate limiting between batches
                await asyncio.sleep(1)
        
        except Exception as e:
            logger.error(f"Error in institution crawl for {inst_id}: {e}")
        
        return articles
    
    async def _get_relevant_urls(self, 
                               session: aiohttp.ClientSession,
                               config: Dict,
                               topics: List[str]) -> List[str]:
        """Extract relevant URLs from sitemap"""
        relevant_urls = []
        
        try:
            # Fetch sitemap
            async with session.get(config['sitemap_url']) as response:
                if response.status == 200:
                    sitemap_content = await response.text()
                    
                    # Parse sitemap XML
                    root = ET.fromstring(sitemap_content)
                    
                    # Extract URLs
                    urls = []
                    for url_elem in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}url'):
                        loc_elem = url_elem.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
                        if loc_elem is not None:
                            urls.append(loc_elem.text)
                    
                    # Filter URLs based on health paths and topics
                    relevant_urls = self._filter_health_urls(urls, config, topics)
                    
        except Exception as e:
            logger.error(f"Error fetching sitemap for {config['name']}: {e}")
            
            # Fallback: construct URLs manually
            relevant_urls = self._construct_fallback_urls(config, topics)
        
        return relevant_urls
    
    def _filter_health_urls(self, 
                          urls: List[str], 
                          config: Dict, 
                          topics: List[str]) -> List[str]:
        """Filter URLs for health-related content"""
        relevant_urls = []
        
        # Create search patterns
        health_keywords = [
            'nutrition', 'digestive', 'gut', 'microbiome', 'probiotic',
            'fiber', 'diet', 'food', 'eating', 'stomach', 'intestine',
            'digestion', 'health', 'wellness'
        ] + [topic.lower().replace(' ', '-') for topic in topics]
        
        for url in urls:
            url_lower = url.lower()
            
            # Check if URL contains health paths
            path_match = any(health_path in url_lower for health_path in config['health_paths'])
            
            # Check if URL contains health keywords
            keyword_match = any(keyword in url_lower for keyword in health_keywords)
            
            if path_match or keyword_match:
                relevant_urls.append(url)
        
        return relevant_urls
    
    def _construct_fallback_urls(self, config: Dict, topics: List[str]) -> List[str]:
        """Construct URLs manually as fallback"""
        fallback_urls = []
        base_url = config['base_url']
        
        # Common health page patterns
        health_patterns = [
            '/health', '/nutrition', '/digestive-health', '/gut-health',
            '/microbiome', '/probiotics', '/fiber', '/diet'
        ]
        
        for pattern in health_patterns:
            fallback_urls.append(urljoin(base_url, pattern))
        
        # Add specific health paths from config
        for health_path in config['health_paths']:
            fallback_urls.append(urljoin(base_url, health_path))
        
        return fallback_urls
    
    async def _scrape_article(self, 
                            session: aiohttp.ClientSession,
                            url: str,
                            config: Dict,
                            inst_id: str) -> Optional[Dict]:
        """Scrape content from a single article URL"""
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    return None
                
                html_content = await response.text()
                
                # Parse HTML content
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Extract title
                title = self._extract_title(soup)
                if not title:
                    return None
                
                # Extract main content
                content = self._extract_content(soup, config['content_selectors'])
                if not content or len(content) < 100:  # Minimum content length
                    return None
                
                # Extract metadata
                publication_date = self._extract_date(soup)
                author = self._extract_author(soup)
                
                article = {
                    'source': f'institution_{inst_id}',
                    'institution': config['name'],
                    'title': title,
                    'content': content,
                    'url': url,
                    'author': author,
                    'publication_date': publication_date,
                    'categories': ['institutional', 'health_authority'],
                    'language': 'en',
                    'content_type': 'health_information',
                    'crawl_timestamp': time.time()
                }
                
                return article
                
        except Exception as e:
            logger.warning(f"Error scraping {url}: {e}")
            return None
    
    def _extract_title(self, soup) -> Optional[str]:
        """Extract article title"""
        # Try multiple selectors for title
        title_selectors = ['h1', 'title', '.page-title', '.entry-title', 'h2']
        
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element and element.get_text(strip=True):
                return element.get_text(strip=True)
        
        return None
    
    def _extract_content(self, soup, content_selectors: List[str]) -> Optional[str]:
        """Extract main article content"""
        content_parts = []
        
        # Try each content selector
        for selector in content_selectors:
            elements = soup.select(selector)
            for element in elements:
                # Remove unwanted elements
                for unwanted in element.select('nav, footer, aside, .sidebar, .menu'):
                    unwanted.decompose()
                
                text = element.get_text(strip=True)
                if text and len(text) > 50:
                    content_parts.append(text)
        
        if content_parts:
            # Join and clean content
            full_content = '\n\n'.join(content_parts)
            # Remove excessive whitespace
            full_content = re.sub(r'\n\s*\n', '\n\n', full_content)
            return full_content.strip()
        
        return None
    
    def _extract_date(self, soup) -> Optional[str]:
        """Extract publication date"""
        # Try multiple date selectors
        date_selectors = [
            'time[datetime]',
            '.date',
            '.published',
            '.post-date',
            'meta[name="publication-date"]'
        ]
        
        for selector in date_selectors:
            element = soup.select_one(selector)
            if element:
                # Try to get datetime attribute first
                date_value = element.get('datetime') or element.get('content')
                if date_value:
                    return date_value
                
                # Fall back to text content
                date_text = element.get_text(strip=True)
                if date_text:
                    return date_text
        
        return None
    
    def _extract_author(self, soup) -> Optional[str]:
        """Extract author information"""
        author_selectors = [
            '.author',
            '.byline',
            'meta[name="author"]',
            '.post-author'
        ]
        
        for selector in author_selectors:
            element = soup.select_one(selector)
            if element:
                author = element.get('content') or element.get_text(strip=True)
                if author:
                    return author
        
        return None
