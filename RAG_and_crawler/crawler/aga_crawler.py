"""
American Gastroenterological Association Crawler - Fetches professional 
gastroenterology guidelines and patient resources from AGA
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

class AGACrawler:
    """Crawler for American Gastroenterological Association content"""
    
    def __init__(self):
        self.base_url = "https://gastro.org"
        self.patient_center_url = "https://gastro.org/patient-center"
        self.guideline_sections = [
            "/patient-center/digestive-conditions",
            "/patient-center/nutrition-and-lifestyle",
            "/guidelines-and-quality-measures/clinical-practice-guidelines",
            "/practice-guidance/gi-patient-care-pathway",
            "/research/clinical-research",
            "/education/digestive-health-topics"
        ]
        
        self.session_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }
    
    async def crawl_aga(self, 
                       topics: List[str], 
                       max_articles: int = 100) -> List[Dict]:
        """
        Crawl AGA for professional gastroenterology guidelines and patient resources
        
        Args:
            topics: List of topics to search for
            max_articles: Maximum number of articles to collect
            
        Returns:
            List of article dictionaries
        """
        logger.info(f"Starting AGA crawl for topics: {topics}")
        
        articles = []
        
        async with aiohttp.ClientSession(
            headers=self.session_headers,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as session:
            
            # Crawl guideline sections
            for section in self.guideline_sections:
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
        
        logger.info(f"AGA crawl completed. Collected {len(articles)} articles")
        return articles[:max_articles]
    
    async def _crawl_section(self, 
                           session: aiohttp.ClientSession,
                           section_path: str,
                           topics: List[str],
                           max_articles: int) -> List[Dict]:
        """Crawl a specific AGA section"""
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
            logger.error(f"Error crawling AGA section {section_path}: {e}")
        
        return articles
    
    async def _search_topic(self, 
                          session: aiohttp.ClientSession,
                          topic: str,
                          max_articles: int) -> List[Dict]:
        """Search AGA website for a specific topic"""
        articles = []
        
        try:
            # AGA search URL
            search_url = f"{self.base_url}/search"
            params = {
                'query': topic,
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
                    '.guideline-result a'
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
            logger.error(f"Error searching AGA for topic {topic}: {e}")
        
        return articles
    
    def _extract_article_links(self, soup: BeautifulSoup) -> List[str]:
        """Extract article links from a section page"""
        links = []
        
        # AGA selectors
        selectors = [
            'a[href*="/patient-center/"]',
            'a[href*="/guidelines/"]',
            'a[href*="/practice-guidance/"]',
            'a[href*="/education/"]',
            '.guideline-link',
            '.patient-resource a',
            '.content-list a'
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
        """Check if URL is relevant for gastroenterology"""
        relevant_patterns = [
            r'/patient-center/',
            r'/guidelines/',
            r'/practice-guidance/',
            r'/education/',
            r'/digestive-conditions',
            r'/nutrition-and-lifestyle',
            r'/gi-patient-care',
            r'/clinical-practice',
            r'/digestive-health'
        ]
        
        return any(re.search(pattern, url, re.IGNORECASE) for pattern in relevant_patterns)
    
    async def _fetch_article(self, 
                           session: aiohttp.ClientSession,
                           url: str,
                           topics: List[str]) -> Optional[Dict]:
        """Fetch and parse an AGA article"""
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
                content_type = self._determine_content_type(url, soup)
                
                return {
                    'title': title,
                    'content': content,
                    'url': url,
                    'source': 'American Gastroenterological Association',
                    'author': author,
                    'publication_date': date,
                    'categories': categories,
                    'content_type': content_type,
                    'organization': 'AGA',
                    'authority_level': 'professional_medical_association',
                    'crawled_at': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error fetching AGA article {url}: {e}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article title"""
        selectors = [
            'h1.page-title',
            'h1.article-title',
            'h1.guideline-title',
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
        
        # AGA content selectors
        content_selectors = [
            '.main-content',
            '.article-content',
            '.guideline-content',
            '.patient-content',
            '.page-content'
        ]
        
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                # Remove unwanted elements
                for unwanted in content_elem.select('script, style, .sidebar, .references'):
                    unwanted.decompose()
                
                # Get text from structured elements
                text_elements = content_elem.select('p, li, h2, h3, h4, h5, blockquote, .recommendation')
                for elem in text_elements:
                    text = elem.get_text().strip()
                    if text and len(text) > 30:  # Higher threshold for professional content
                        content_parts.append(text)
        
        # Fallback: get all paragraphs
        if not content_parts:
            paragraphs = soup.select('p')
            content_parts = [p.get_text().strip() for p in paragraphs if len(p.get_text().strip()) > 30]
        
        return '\n\n'.join(content_parts)
    
    def _extract_author(self, soup: BeautifulSoup) -> str:
        """Extract article author"""
        author_selectors = [
            '.author-name',
            '.byline .author',
            '.guideline-authors',
            '.committee-members',
            '[data-author]'
        ]
        
        for selector in author_selectors:
            author_elem = soup.select_one(selector)
            if author_elem:
                return author_elem.get_text().strip()
        
        return "AGA Clinical Guidelines Committee"
    
    def _extract_date(self, soup: BeautifulSoup) -> str:
        """Extract publication or guideline date"""
        date_selectors = [
            '.publication-date',
            '.guideline-date',
            '.last-updated',
            '.approval-date',
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
        categories = ['aga', 'gastroenterology']
        
        # Extract from URL path
        if '/patient-center/' in url:
            categories.append('patient-resources')
        if '/guidelines/' in url:
            categories.append('clinical-guidelines')
        if '/practice-guidance/' in url:
            categories.append('practice-guidance')
        if '/education/' in url:
            categories.append('medical-education')
        if '/digestive-conditions' in url:
            categories.append('digestive-conditions')
        if '/nutrition-and-lifestyle' in url:
            categories.append('nutrition-and-lifestyle')
        
        # Extract from category tags
        category_selectors = [
            '.category a',
            '.tag a',
            '.guideline-category',
            '.topic-category'
        ]
        
        for selector in category_selectors:
            elements = soup.select(selector)
            for elem in elements:
                text = elem.get_text().strip().lower()
                if text and text not in categories:
                    categories.append(text)
        
        # Add professional gastroenterology categories
        professional_keywords = [
            'evidence-based guidelines', 'clinical practice',
            'gastroenterology standards', 'professional guidelines',
            'digestive disease management', 'gi best practices'
        ]
        
        categories.extend(professional_keywords)
        
        return list(set(categories))
    
    def _determine_content_type(self, url: str, soup: BeautifulSoup) -> str:
        """Determine the type of content based on URL and content"""
        if '/guidelines/' in url:
            return 'clinical_guidelines'
        elif '/patient-center/' in url:
            return 'patient_education'
        elif '/practice-guidance/' in url:
            return 'practice_guidance'
        elif '/education/' in url:
            return 'medical_education'
        else:
            return 'professional_resource'
    
    def _is_content_relevant(self, content: str, topics: List[str]) -> bool:
        """Check if content is relevant to gastroenterology topics"""
        content_lower = content.lower()
        
        # Professional gastroenterology keywords
        gi_keywords = [
            'gastroenterology', 'gastrointestinal', 'digestive',
            'gut', 'bowel', 'stomach', 'intestine', 'colon',
            'endoscopy', 'colonoscopy', 'ibs', 'ibd', 'crohn',
            'ulcerative colitis', 'celiac', 'gerd', 'reflux',
            'nutrition', 'diet', 'fiber', 'probiotic', 'microbiome'
        ]
        
        # Check for topic relevance
        topic_match = any(topic.lower() in content_lower for topic in topics)
        keyword_match = any(keyword in content_lower for keyword in gi_keywords)
        
        return topic_match or keyword_match
