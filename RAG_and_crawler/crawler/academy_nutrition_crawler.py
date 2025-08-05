"""
Academy of Nutrition and Dietetics Crawler - Fetches evidence-based nutrition information
from the largest organization of nutrition professionals
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

class AcademyNutritionCrawler:
    """Crawler for Academy of Nutrition and Dietetics content"""
    
    def __init__(self):
        self.base_url = "https://www.eatright.org"
        self.nutrition_sections = [
            "/health/digestive-health",
            "/health/wellness/digestive-health",
            "/food/vitamins-and-supplements/nutrient-rich-foods",
            "/food/planning-and-prep",
            "/health/diseases-and-conditions",
            "/food/food-safety",
            "/health/lifestyle"
        ]
        
        self.session_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }
    
    async def crawl_academy_nutrition(self, 
                                    topics: List[str], 
                                    max_articles: int = 100) -> List[Dict]:
        """
        Crawl Academy of Nutrition and Dietetics for professional nutrition guidance
        
        Args:
            topics: List of topics to search for
            max_articles: Maximum number of articles to collect
            
        Returns:
            List of article dictionaries
        """
        logger.info(f"Starting Academy of Nutrition crawl for topics: {topics}")
        
        articles = []
        
        async with aiohttp.ClientSession(
            headers=self.session_headers,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as session:
            
            # Crawl health and food sections
            for section in self.nutrition_sections:
                if len(articles) >= max_articles:
                    break
                    
                section_articles = await self._crawl_section(
                    session, section, topics, max_articles - len(articles)
                )
                articles.extend(section_articles)
                
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
        
        logger.info(f"Academy of Nutrition crawl completed. Collected {len(articles)} articles")
        return articles[:max_articles]
    
    async def _crawl_section(self, 
                           session: aiohttp.ClientSession,
                           section_path: str,
                           topics: List[str],
                           max_articles: int) -> List[Dict]:
        """Crawl a specific Academy section"""
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
                article_links = self._extract_article_links(soup)
                
                # Process each article
                for link in article_links[:max_articles]:
                    if len(articles) >= max_articles:
                        break
                        
                    article = await self._fetch_article(session, link, topics)
                    if article:
                        articles.append(article)
                        
                    await asyncio.sleep(0.5)
                    
        except Exception as e:
            logger.error(f"Error crawling Academy section {section_path}: {e}")
        
        return articles
    
    async def _search_topic(self, 
                          session: aiohttp.ClientSession,
                          topic: str,
                          max_articles: int) -> List[Dict]:
        """Search Academy website for a specific topic"""
        articles = []
        
        try:
            # Academy search URL
            search_url = f"{self.base_url}/search"
            params = {
                'query': topic,
                'page': 1
            }
            
            async with session.get(search_url, params=params) as response:
                if response.status != 200:
                    return articles
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Extract search result links
                result_selectors = [
                    '.search-result a[href]',
                    '.result-item a',
                    '.content-item a'
                ]
                
                for selector in result_selectors:
                    result_links = soup.select(selector)
                    
                    for link_elem in result_links[:max_articles]:
                        href = link_elem.get('href')
                        if href:
                            full_url = urljoin(self.base_url, href)
                            if self._is_relevant_url(full_url):
                                article = await self._fetch_article(session, full_url, [topic])
                                if article:
                                    articles.append(article)
                                    
                                await asyncio.sleep(0.5)
                                
        except Exception as e:
            logger.error(f"Error searching Academy for topic {topic}: {e}")
        
        return articles
    
    def _extract_article_links(self, soup: BeautifulSoup) -> List[str]:
        """Extract article links from a section page"""
        links = []
        
        # Academy of Nutrition selectors
        selectors = [
            'a[href*="/health/"]',
            'a[href*="/food/"]',
            '.article-link',
            '.content-item a',
            '.tile-content a',
            '.resource-link'
        ]
        
        for selector in selectors:
            link_elements = soup.select(selector)
            for link_elem in link_elements:
                href = link_elem.get('href')
                if href:
                    full_url = urljoin(self.base_url, href)
                    if self._is_relevant_url(full_url):
                        links.append(full_url)
        
        return list(set(links))
    
    def _is_relevant_url(self, url: str) -> bool:
        """Check if URL is relevant for gut health and nutrition"""
        relevant_patterns = [
            r'/health/',
            r'/food/',
            r'/digestive',
            r'/gut',
            r'/microbiome',
            r'/probiotic',
            r'/fiber',
            r'/nutrition',
            r'/wellness',
            r'/diseases-and-conditions'
        ]
        
        return any(re.search(pattern, url, re.IGNORECASE) for pattern in relevant_patterns)
    
    async def _fetch_article(self, 
                           session: aiohttp.ClientSession,
                           url: str,
                           topics: List[str]) -> Optional[Dict]:
        """Fetch and parse an Academy article"""
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
                    'source': 'Academy of Nutrition and Dietetics',
                    'author': author,
                    'publication_date': date,
                    'categories': categories,
                    'content_type': 'professional_guidance',
                    'organization': 'Academy of Nutrition and Dietetics',
                    'crawled_at': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error fetching Academy article {url}: {e}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article title"""
        selectors = [
            'h1.page-title',
            'h1.article-title',
            'h1.entry-title',
            'h1',
            '.main-title',
            '.content-title'
        ]
        
        for selector in selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                return title_elem.get_text().strip()
        
        return None
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Extract main article content"""
        content_parts = []
        
        # Academy content selectors
        content_selectors = [
            '.article-content',
            '.page-content',
            '.main-content',
            '.content-body',
            '.entry-content'
        ]
        
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                # Remove unwanted elements
                for unwanted in content_elem.select('script, style, .social-share, .advertisement'):
                    unwanted.decompose()
                
                # Get text from paragraphs and lists
                text_elements = content_elem.select('p, li, h2, h3, h4, blockquote')
                for elem in text_elements:
                    text = elem.get_text().strip()
                    if text and len(text) > 20:
                        content_parts.append(text)
        
        # Fallback: get all paragraphs
        if not content_parts:
            paragraphs = soup.select('p')
            content_parts = [p.get_text().strip() for p in paragraphs if len(p.get_text().strip()) > 20]
        
        return '\n\n'.join(content_parts)
    
    def _extract_author(self, soup: BeautifulSoup) -> str:
        """Extract article author"""
        author_selectors = [
            '.author-name',
            '.byline .author',
            '.article-author',
            '.content-author',
            '[data-author]'
        ]
        
        for selector in author_selectors:
            author_elem = soup.select_one(selector)
            if author_elem:
                return author_elem.get_text().strip()
        
        return "Academy of Nutrition and Dietetics"
    
    def _extract_date(self, soup: BeautifulSoup) -> str:
        """Extract publication or update date"""
        date_selectors = [
            '.publish-date',
            '.article-date',
            '.updated-date',
            'time[datetime]',
            '[data-date]'
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
        categories = ['nutrition-professional', 'dietetics']
        
        # Extract from URL path
        if '/health/' in url:
            categories.append('health')
        if '/food/' in url:
            categories.append('food')
        if '/digestive' in url:
            categories.append('digestive-health')
        if '/wellness' in url:
            categories.append('wellness')
        
        # Extract from category tags
        category_selectors = [
            '.category a',
            '.tag a',
            '.topic-tag',
            '.content-category'
        ]
        
        for selector in category_selectors:
            elements = soup.select(selector)
            for elem in elements:
                text = elem.get_text().strip().lower()
                if text and text not in categories:
                    categories.append(text)
        
        # Add professional nutrition categories
        professional_keywords = [
            'registered dietitian', 'nutrition professional',
            'evidence-based nutrition', 'clinical nutrition',
            'nutrition counseling', 'dietary guidance'
        ]
        
        categories.extend(professional_keywords)
        
        return list(set(categories))
    
    def _is_content_relevant(self, content: str, topics: List[str]) -> bool:
        """Check if content is relevant to gut health and nutrition topics"""
        content_lower = content.lower()
        
        # Professional nutrition keywords
        nutrition_keywords = [
            'nutrition', 'diet', 'food', 'digestive', 'gut',
            'fiber', 'probiotic', 'microbiome', 'dietitian',
            'nutrients', 'healthy eating', 'meal planning',
            'dietary guidelines', 'food safety', 'wellness'
        ]
        
        # Check for topic relevance
        topic_match = any(topic.lower() in content_lower for topic in topics)
        keyword_match = any(keyword in content_lower for keyword in nutrition_keywords)
        
        return topic_match or keyword_match
