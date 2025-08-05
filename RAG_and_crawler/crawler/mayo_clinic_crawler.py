"""
Mayo Clinic Crawler - Fetches digestive health and nutrition information
from Mayo Clinic's evidence-based consumer health resources
"""
import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
from datetime import datetime

logger = logging.getLogger(__name__)

class MayoClinicCrawler:
    """Crawler for Mayo Clinic digestive health and nutrition content"""
    
    def __init__(self):
        self.base_url = "https://www.mayoclinic.org"
        self.digestive_sections = [
            "/diseases-conditions/digestive-system",
            "/healthy-lifestyle/nutrition-and-healthy-eating",
            "/diseases-conditions/irritable-bowel-syndrome",
            "/diseases-conditions/inflammatory-bowel-disease",
            "/diseases-conditions/gastroesophageal-reflux-disease",
            "/diseases-conditions/celiac-disease",
            "/diseases-conditions/crohns-disease",
            "/diseases-conditions/ulcerative-colitis"
        ]
        
        self.session_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    async def crawl_mayo_clinic(self, 
                               topics: List[str], 
                               max_articles: int = 100) -> List[Dict]:
        """
        Crawl Mayo Clinic for digestive health and nutrition articles
        
        Args:
            topics: List of topics to search for
            max_articles: Maximum number of articles to collect
            
        Returns:
            List of article dictionaries
        """
        logger.info(f"Starting Mayo Clinic crawl for topics: {topics}")
        
        articles = []
        
        async with aiohttp.ClientSession(
            headers=self.session_headers,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as session:
            
            # Crawl each digestive health section
            for section in self.digestive_sections:
                if len(articles) >= max_articles:
                    break
                    
                section_articles = await self._crawl_section(
                    session, section, topics, max_articles - len(articles)
                )
                articles.extend(section_articles)
                
                # Rate limiting
                await asyncio.sleep(1)
            
            # Search for specific topics
            for topic in topics:
                if len(articles) >= max_articles:
                    break
                    
                search_articles = await self._search_topic(
                    session, topic, max_articles - len(articles)
                )
                articles.extend(search_articles)
                
                await asyncio.sleep(1)
        
        logger.info(f"Mayo Clinic crawl completed. Collected {len(articles)} articles")
        return articles[:max_articles]
    
    async def _crawl_section(self, 
                           session: aiohttp.ClientSession,
                           section_path: str,
                           topics: List[str],
                           max_articles: int) -> List[Dict]:
        """Crawl a specific Mayo Clinic section"""
        articles = []
        
        try:
            url = urljoin(self.base_url, section_path)
            async with session.get(url) as response:
                if response.status != 200:
                    logger.warning(f"Failed to fetch section {section_path}: {response.status}")
                    return articles
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Find article links
                article_links = self._extract_article_links(soup, section_path)
                
                # Process each article
                for link in article_links[:max_articles]:
                    if len(articles) >= max_articles:
                        break
                        
                    article = await self._fetch_article(session, link, topics)
                    if article:
                        articles.append(article)
                        
                    await asyncio.sleep(0.5)
                    
        except Exception as e:
            logger.error(f"Error crawling Mayo Clinic section {section_path}: {e}")
        
        return articles
    
    def _extract_article_links(self, soup: BeautifulSoup, section_path: str) -> List[str]:
        """Extract article links from a section page"""
        links = []
        
        # Mayo Clinic uses various selectors for article links
        selectors = [
            'a[href*="/diseases-conditions/"]',
            'a[href*="/healthy-lifestyle/"]',
            'a[href*="/nutrition-and-healthy-eating/"]',
            '.content-module a',
            '.index-list a',
            '.cmp-content-list a'
        ]
        
        for selector in selectors:
            link_elements = soup.select(selector)
            for link_elem in link_elements:
                href = link_elem.get('href')
                if href:
                    full_url = urljoin(self.base_url, href)
                    if self._is_relevant_article(full_url):
                        links.append(full_url)
        
        return list(set(links))  # Remove duplicates
    
    def _is_relevant_article(self, url: str) -> bool:
        """Check if URL is relevant for gut health and nutrition"""
        relevant_patterns = [
            r'/diseases-conditions/',
            r'/healthy-lifestyle/',
            r'/nutrition',
            r'/digestive',
            r'/gut',
            r'/microbiome',
            r'/probiotic',
            r'/fiber',
            r'/irritable-bowel',
            r'/inflammatory-bowel',
            r'/gastro',
            r'/celiac',
            r'/crohn'
        ]
        
        return any(re.search(pattern, url, re.IGNORECASE) for pattern in relevant_patterns)
    
    async def _search_topic(self, 
                          session: aiohttp.ClientSession,
                          topic: str,
                          max_articles: int) -> List[Dict]:
        """Search Mayo Clinic for a specific topic"""
        articles = []
        
        try:
            # Mayo Clinic search URL
            search_url = f"{self.base_url}/search/search-results"
            params = {
                'q': topic,
                'page': 1
            }
            
            async with session.get(search_url, params=params) as response:
                if response.status != 200:
                    return articles
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Extract search result links
                result_links = soup.select('.search-result a[href]')
                
                for link_elem in result_links[:max_articles]:
                    href = link_elem.get('href')
                    if href:
                        full_url = urljoin(self.base_url, href)
                        if self._is_relevant_article(full_url):
                            article = await self._fetch_article(session, full_url, [topic])
                            if article:
                                articles.append(article)
                                
                            await asyncio.sleep(0.5)
                            
        except Exception as e:
            logger.error(f"Error searching Mayo Clinic for topic {topic}: {e}")
        
        return articles
    
    async def _fetch_article(self, 
                           session: aiohttp.ClientSession,
                           url: str,
                           topics: List[str]) -> Optional[Dict]:
        """Fetch and parse a Mayo Clinic article"""
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    return None
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Extract article content
                title = self._extract_title(soup)
                if not title:
                    return None
                
                content = self._extract_content(soup)
                if not content or len(content) < 200:
                    return None
                
                # Check relevance
                if not self._is_content_relevant(content, topics):
                    return None
                
                # Extract metadata
                author = self._extract_author(soup)
                date = self._extract_date(soup)
                categories = self._extract_categories(soup, url)
                
                return {
                    'title': title,
                    'content': content,
                    'url': url,
                    'source': 'Mayo Clinic',
                    'author': author,
                    'publication_date': date,
                    'categories': categories,
                    'content_type': 'medical_article',
                    'crawled_at': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error fetching Mayo Clinic article {url}: {e}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article title"""
        selectors = [
            'h1.content-title',
            'h1.page-title',
            'h1',
            '.main-title',
            '.article-title'
        ]
        
        for selector in selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                return title_elem.get_text().strip()
        
        return None
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Extract main article content"""
        content_parts = []
        
        # Mayo Clinic content selectors
        content_selectors = [
            '.content-body',
            '.article-body',
            '.main-content',
            '.content-module',
            '[data-module="BodyText"]'
        ]
        
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                # Remove unwanted elements
                for unwanted in content_elem.select('script, style, .advertisement, .social-share'):
                    unwanted.decompose()
                
                text = content_elem.get_text().strip()
                if text:
                    content_parts.append(text)
        
        # Fallback: get all paragraphs
        if not content_parts:
            paragraphs = soup.select('p')
            content_parts = [p.get_text().strip() for p in paragraphs if p.get_text().strip()]
        
        return '\n\n'.join(content_parts)
    
    def _extract_author(self, soup: BeautifulSoup) -> str:
        """Extract article author"""
        author_selectors = [
            '.byline .author',
            '.article-author',
            '.content-author',
            '[data-author]'
        ]
        
        for selector in author_selectors:
            author_elem = soup.select_one(selector)
            if author_elem:
                return author_elem.get_text().strip()
        
        return "Mayo Clinic Staff"
    
    def _extract_date(self, soup: BeautifulSoup) -> str:
        """Extract publication or update date"""
        date_selectors = [
            '.content-date',
            '.last-updated',
            '.publish-date',
            '[data-date]',
            'time[datetime]'
        ]
        
        for selector in date_selectors:
            date_elem = soup.select_one(selector)
            if date_elem:
                date_text = date_elem.get('datetime') or date_elem.get_text()
                if date_text:
                    return date_text.strip()
        
        return datetime.now().strftime('%Y-%m-%d')
    
    def _extract_categories(self, soup: BeautifulSoup, url: str) -> List[str]:
        """Extract article categories"""
        categories = []
        
        # Extract from URL path
        if '/diseases-conditions/' in url:
            categories.append('diseases-conditions')
        if '/healthy-lifestyle/' in url:
            categories.append('healthy-lifestyle')
        if '/nutrition' in url:
            categories.append('nutrition')
        
        # Extract from breadcrumbs or navigation
        breadcrumb_selectors = [
            '.breadcrumb a',
            '.navigation a',
            '.category-link'
        ]
        
        for selector in breadcrumb_selectors:
            links = soup.select(selector)
            for link in links:
                text = link.get_text().strip().lower()
                if text and text not in categories:
                    categories.append(text)
        
        # Add gut health specific categories
        gut_health_keywords = [
            'digestive health', 'gut microbiome', 'nutrition',
            'probiotics', 'fiber', 'inflammatory bowel disease',
            'irritable bowel syndrome', 'gastroesophageal reflux'
        ]
        
        categories.extend(gut_health_keywords)
        
        return list(set(categories))
    
    def _is_content_relevant(self, content: str, topics: List[str]) -> bool:
        """Check if content is relevant to gut health topics"""
        content_lower = content.lower()
        
        # Primary gut health keywords
        gut_keywords = [
            'digestive', 'gut', 'intestine', 'microbiome', 'probiotic',
            'fiber', 'nutrition', 'diet', 'food', 'stomach', 'bowel',
            'gastro', 'colon', 'digestion', 'absorption', 'metabolism'
        ]
        
        # Check for topic relevance
        topic_match = any(topic.lower() in content_lower for topic in topics)
        keyword_match = any(keyword in content_lower for keyword in gut_keywords)
        
        return topic_match or keyword_match
