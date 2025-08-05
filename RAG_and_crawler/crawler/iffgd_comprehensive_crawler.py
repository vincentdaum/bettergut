"""
International Foundation for Gastrointestinal Disorders (IFFGD) Comprehensive Crawler
Fetches evidence-based information on functional gastrointestinal disorders
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

class IFFGDComprehensiveCrawler:
    """Comprehensive crawler for International Foundation for Gastrointestinal Disorders"""
    
    def __init__(self):
        self.base_url = "https://www.iffgd.org"
        self.nutrition_sections = [
            "/diet-nutrition",
            "/diet-nutrition/nutrition-basics",
            "/diet-nutrition/special-diets",
            "/diet-nutrition/food-intolerances",
            "/diet-nutrition/supplements",
            "/diet-nutrition/meal-planning",
            "/lower-gi-disorders/irritable-bowel-syndrome/diet-treatments",
            "/lower-gi-disorders/functional-dyspepsia/dietary-management",
            "/upper-gi-disorders/gastroparesis/nutrition",
            "/resources/nutrition-resources",
            "/professionals/nutrition-guidelines"
        ]
        
        self.session_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }
    
    async def crawl_iffgd_comprehensive(self, 
                                      topics: List[str], 
                                      max_articles: int = 100) -> List[Dict]:
        """
        Comprehensive crawl of IFFGD for functional GI disorder nutrition information
        
        Args:
            topics: List of topics to search for
            max_articles: Maximum number of articles to collect
            
        Returns:
            List of article dictionaries
        """
        logger.info(f"Starting comprehensive IFFGD crawl for topics: {topics}")
        
        articles = []
        
        async with aiohttp.ClientSession(
            headers=self.session_headers,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as session:
            
            # Crawl nutrition sections
            for section in self.nutrition_sections:
                if len(articles) >= max_articles:
                    break
                    
                section_articles = await self._crawl_section(
                    session, section, topics, max_articles - len(articles)
                )
                articles.extend(section_articles)
                
                await asyncio.sleep(1)
            
            # Crawl disorder-specific content
            disorder_articles = await self._crawl_disorder_content(
                session, topics, max_articles - len(articles)
            )
            articles.extend(disorder_articles)
            
            # Search for specific topics
            for topic in topics:
                if len(articles) >= max_articles:
                    break
                    
                search_articles = await self._search_topic(
                    session, topic, max_articles - len(articles)
                )
                articles.extend(search_articles)
                
                await asyncio.sleep(1)
        
        logger.info(f"Comprehensive IFFGD crawl completed. Collected {len(articles)} articles")
        return articles[:max_articles]
    
    async def _crawl_disorder_content(self,
                                    session: aiohttp.ClientSession,
                                    topics: List[str],
                                    max_articles: int) -> List[Dict]:
        """Crawl disorder-specific nutritional content"""
        articles = []
        
        disorder_sections = [
            "/lower-gi-disorders/irritable-bowel-syndrome",
            "/lower-gi-disorders/functional-constipation",
            "/lower-gi-disorders/functional-diarrhea",
            "/upper-gi-disorders/functional-dyspepsia",
            "/upper-gi-disorders/gastroparesis",
            "/upper-gi-disorders/functional-heartburn",
            "/pediatric-gi-disorders",
            "/women-gi-health"
        ]
        
        for section in disorder_sections:
            if len(articles) >= max_articles:
                break
                
            section_articles = await self._crawl_section(
                session, section, topics, max_articles - len(articles)
            )
            articles.extend(section_articles)
            
            await asyncio.sleep(1)
        
        return articles
    
    async def _crawl_section(self, 
                           session: aiohttp.ClientSession,
                           section_path: str,
                           topics: List[str],
                           max_articles: int) -> List[Dict]:
        """Crawl a specific IFFGD section"""
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
            logger.error(f"Error crawling IFFGD section {section_path}: {e}")
        
        return articles
    
    async def _search_topic(self, 
                          session: aiohttp.ClientSession,
                          topic: str,
                          max_articles: int) -> List[Dict]:
        """Search IFFGD website for a specific topic"""
        articles = []
        
        try:
            # IFFGD search URL
            search_url = f"{self.base_url}/search"
            params = {
                'q': topic,
                'type': 'all'
            }
            
            async with session.get(search_url, params=params) as response:
                if response.status != 200:
                    return articles
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Extract search result links
                result_selectors = [
                    '.search-results a[href]',
                    '.result-item a',
                    '.resource-link',
                    '.article-listing a'
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
            logger.error(f"Error searching IFFGD for topic {topic}: {e}")
        
        return articles
    
    def _extract_article_links(self, soup: BeautifulSoup) -> List[str]:
        """Extract article links from a section page"""
        links = []
        
        # IFFGD selectors
        selectors = [
            'a[href*="/diet-nutrition/"]',
            'a[href*="/disorders/"]',
            'a[href*="/resources/"]',
            'a[href*="/professionals/"]',
            '.content-listing a',
            '.resource-link',
            '.article-link',
            '.factsheet-link',
            '.nutrition-resource a'
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
        """Check if URL is relevant for functional GI disorder nutrition"""
        relevant_patterns = [
            r'/diet-nutrition/',
            r'/disorders/',
            r'/resources/',
            r'/nutrition',
            r'/diet',
            r'/ibs',
            r'/gastroparesis',
            r'/dyspepsia',
            r'/constipation',
            r'/diarrhea',
            r'/fodmap',
            r'/supplements',
            r'/meal-planning'
        ]
        
        return any(re.search(pattern, url, re.IGNORECASE) for pattern in relevant_patterns)
    
    async def _fetch_article(self, 
                           session: aiohttp.ClientSession,
                           url: str,
                           topics: List[str]) -> Optional[Dict]:
        """Fetch and parse an IFFGD article"""
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
                content_type = self._determine_content_type(soup, url)
                
                return {
                    'title': title,
                    'content': content,
                    'url': url,
                    'source': 'International Foundation for Gastrointestinal Disorders (IFFGD)',
                    'author': author,
                    'publication_date': date,
                    'categories': categories,
                    'content_type': content_type,
                    'organization': 'IFFGD',
                    'focus_area': 'functional_gastrointestinal_disorders',
                    'target_audience': 'patients_and_providers',
                    'evidence_level': 'patient_education_guidelines',
                    'crawled_at': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error fetching IFFGD article {url}: {e}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article title"""
        selectors = [
            'h1.page-title',
            'h1.article-title',
            'h1.resource-title',
            'h1.factsheet-title',
            'h1',
            '.main-title',
            '.content-title',
            '.entry-title'
        ]
        
        for selector in selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                return title_elem.get_text().strip()
        
        return None
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Extract main article content"""
        content_parts = []
        
        # IFFGD content selectors
        content_selectors = [
            '.main-content',
            '.article-content',
            '.resource-content',
            '.factsheet-content',
            '.entry-content',
            '.page-content',
            '.content-body'
        ]
        
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                # Remove unwanted elements
                for unwanted in content_elem.select('script, style, .sidebar, .related-content, .navigation'):
                    unwanted.decompose()
                
                # Get text from structured elements
                text_elements = content_elem.select('p, li, h2, h3, h4, h5, blockquote, .highlight-box, .tip-box')
                for elem in text_elements:
                    text = elem.get_text().strip()
                    if text and len(text) > 25:
                        content_parts.append(text)
        
        # Fallback: get all paragraphs
        if not content_parts:
            paragraphs = soup.select('p')
            content_parts = [p.get_text().strip() for p in paragraphs if len(p.get_text().strip()) > 25]
        
        return '\n\n'.join(content_parts)
    
    def _extract_author(self, soup: BeautifulSoup) -> str:
        """Extract article author"""
        author_selectors = [
            '.author-name',
            '.byline .author',
            '.medical-reviewer',
            '.expert-author',
            '.contributor',
            '[data-author]'
        ]
        
        for selector in author_selectors:
            author_elem = soup.select_one(selector)
            if author_elem:
                return author_elem.get_text().strip()
        
        return "IFFGD Medical Advisory Board"
    
    def _extract_date(self, soup: BeautifulSoup) -> str:
        """Extract publication or review date"""
        date_selectors = [
            '.publication-date',
            '.last-updated',
            '.review-date',
            '.medical-review-date',
            'time[datetime]',
            '[data-date]',
            '.date-updated'
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
        categories = ['iffgd', 'functional-gastrointestinal-disorders']
        
        # Extract from URL path
        if '/diet-nutrition/' in url:
            categories.append('diet-and-nutrition')
        if '/irritable-bowel-syndrome/' in url:
            categories.append('ibs')
        if '/gastroparesis/' in url:
            categories.append('gastroparesis')
        if '/dyspepsia/' in url:
            categories.append('functional-dyspepsia')
        if '/constipation/' in url:
            categories.append('functional-constipation')
        if '/diarrhea/' in url:
            categories.append('functional-diarrhea')
        if '/fodmap' in url:
            categories.append('low-fodmap-diet')
        if '/supplements' in url:
            categories.append('nutritional-supplements')
        
        # Extract from category tags
        category_selectors = [
            '.category a',
            '.tag a',
            '.disorder-type',
            '.condition-tag'
        ]
        
        for selector in category_selectors:
            elements = soup.select(selector)
            for elem in elements:
                text = elem.get_text().strip().lower()
                if text and text not in categories:
                    categories.append(text)
        
        # Add functional GI disorder categories
        fgid_keywords = [
            'functional gastrointestinal disorders', 'ibs management',
            'low-fodmap diet', 'gastroparesis nutrition',
            'functional dyspepsia diet', 'gi symptom management',
            'digestive health optimization', 'gut-brain axis'
        ]
        
        categories.extend(fgid_keywords)
        
        return list(set(categories))
    
    def _determine_content_type(self, soup: BeautifulSoup, url: str) -> str:
        """Determine the type of content"""
        if '/resources/' in url:
            return 'educational_resource'
        elif '/professionals/' in url:
            return 'professional_guideline'
        elif '/diet-nutrition/' in url:
            return 'nutrition_guide'
        elif '/disorders/' in url:
            return 'disorder_information'
        else:
            return 'patient_education'
    
    def _is_content_relevant(self, content: str, topics: List[str]) -> bool:
        """Check if content is relevant to functional GI disorder topics"""
        content_lower = content.lower()
        
        # Functional GI disorder keywords
        fgid_keywords = [
            'functional gastrointestinal', 'irritable bowel syndrome', 'ibs',
            'gastroparesis', 'functional dyspepsia', 'functional constipation',
            'functional diarrhea', 'fodmap', 'nutrition', 'diet',
            'digestive', 'gut', 'intestine', 'bowel', 'stomach',
            'meal planning', 'food intolerance', 'supplements'
        ]
        
        # Check for topic relevance
        topic_match = any(topic.lower() in content_lower for topic in topics)
        keyword_match = any(keyword in content_lower for keyword in fgid_keywords)
        
        return topic_match or keyword_match
