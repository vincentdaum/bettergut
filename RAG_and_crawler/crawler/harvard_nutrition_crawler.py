"""
Harvard Nutrition Source Crawler - Fetches evidence-based nutrition information
from Harvard T.H. Chan School of Public Health
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

class HarvardNutritionCrawler:
    """Crawler for Harvard Nutrition Source content"""
    
    def __init__(self):
        self.base_url = "https://www.hsph.harvard.edu"
        self.nutrition_sections = [
            "/nutritionsource/",
            "/nutritionsource/food-features/",
            "/nutritionsource/healthy-eating-plate/",
            "/nutritionsource/carbohydrates/fiber/",
            "/nutritionsource/what-should-you-eat/probiotics/",
            "/nutritionsource/disease-prevention/digestive-disease-prevention/"
        ]
        
        self.session_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }
    
    async def crawl_harvard_nutrition(self, 
                                    topics: List[str], 
                                    max_articles: int = 100) -> List[Dict]:
        """
        Crawl Harvard Nutrition Source for evidence-based nutrition articles
        
        Args:
            topics: List of topics to search for
            max_articles: Maximum number of articles to collect
            
        Returns:
            List of article dictionaries
        """
        logger.info(f"Starting Harvard Nutrition Source crawl for topics: {topics}")
        
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
            
            # Get sitemap articles
            sitemap_articles = await self._crawl_sitemap(
                session, topics, max_articles - len(articles)
            )
            articles.extend(sitemap_articles)
        
        logger.info(f"Harvard Nutrition Source crawl completed. Collected {len(articles)} articles")
        return articles[:max_articles]
    
    async def _crawl_section(self, 
                           session: aiohttp.ClientSession,
                           section_path: str,
                           topics: List[str],
                           max_articles: int) -> List[Dict]:
        """Crawl a specific Harvard Nutrition section"""
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
            logger.error(f"Error crawling Harvard section {section_path}: {e}")
        
        return articles
    
    async def _crawl_sitemap(self, 
                           session: aiohttp.ClientSession,
                           topics: List[str],
                           max_articles: int) -> List[Dict]:
        """Crawl Harvard nutrition sitemap for articles"""
        articles = []
        
        try:
            sitemap_url = f"{self.base_url}/sitemap.xml"
            async with session.get(sitemap_url) as response:
                if response.status != 200:
                    return articles
                
                xml_content = await response.text()
                soup = BeautifulSoup(xml_content, 'xml')
                
                # Extract URLs from sitemap
                urls = [loc.text for loc in soup.find_all('loc')]
                nutrition_urls = [url for url in urls if '/nutritionsource/' in url]
                
                # Process relevant URLs
                for url in nutrition_urls[:max_articles * 2]:  # Get more than needed to filter
                    if len(articles) >= max_articles:
                        break
                        
                    if self._is_relevant_url(url):
                        article = await self._fetch_article(session, url, topics)
                        if article:
                            articles.append(article)
                            
                        await asyncio.sleep(0.5)
                        
        except Exception as e:
            logger.error(f"Error crawling Harvard sitemap: {e}")
        
        return articles
    
    def _extract_article_links(self, soup: BeautifulSoup) -> List[str]:
        """Extract article links from a section page"""
        links = []
        
        # Harvard Nutrition Source selectors
        selectors = [
            'a[href*="/nutritionsource/"]',
            '.entry-title a',
            '.post-title a',
            '.article-link',
            '.content-list a',
            '.menu-item a'
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
            r'/nutritionsource/',
            r'/fiber',
            r'/probiotic',
            r'/microbiome',
            r'/digestive',
            r'/gut',
            r'/food-features',
            r'/carbohydrates',
            r'/healthy-eating',
            r'/disease-prevention'
        ]
        
        return any(re.search(pattern, url, re.IGNORECASE) for pattern in relevant_patterns)
    
    async def _fetch_article(self, 
                           session: aiohttp.ClientSession,
                           url: str,
                           topics: List[str]) -> Optional[Dict]:
        """Fetch and parse a Harvard Nutrition article"""
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
                    'source': 'Harvard Nutrition Source',
                    'author': author,
                    'publication_date': date,
                    'categories': categories,
                    'content_type': 'academic_article',
                    'institution': 'Harvard T.H. Chan School of Public Health',
                    'crawled_at': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error fetching Harvard article {url}: {e}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article title"""
        selectors = [
            'h1.entry-title',
            'h1.page-title',
            'h1.post-title',
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
        
        # Harvard Nutrition Source content selectors
        content_selectors = [
            '.entry-content',
            '.post-content',
            '.article-content',
            '.main-content',
            '.content-area'
        ]
        
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                # Remove unwanted elements
                for unwanted in content_elem.select('script, style, .share-buttons, .related-posts'):
                    unwanted.decompose()
                
                # Get text from paragraphs and lists
                text_elements = content_elem.select('p, li, h2, h3, h4')
                for elem in text_elements:
                    text = elem.get_text().strip()
                    if text and len(text) > 20:  # Filter out very short snippets
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
            '.post-author',
            '.entry-author',
            '[data-author]'
        ]
        
        for selector in author_selectors:
            author_elem = soup.select_one(selector)
            if author_elem:
                return author_elem.get_text().strip()
        
        return "Harvard T.H. Chan School of Public Health"
    
    def _extract_date(self, soup: BeautifulSoup) -> str:
        """Extract publication or update date"""
        date_selectors = [
            '.entry-date',
            '.post-date',
            '.publish-date',
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
        categories = ['nutrition', 'harvard-nutrition-source']
        
        # Extract from URL path
        if '/food-features/' in url:
            categories.append('food-features')
        if '/healthy-eating-plate/' in url:
            categories.append('healthy-eating-plate')
        if '/fiber/' in url:
            categories.append('fiber')
        if '/probiotics/' in url:
            categories.append('probiotics')
        
        # Extract from category tags
        category_selectors = [
            '.category a',
            '.tag a',
            '.post-categories a',
            '.entry-categories a'
        ]
        
        for selector in category_selectors:
            links = soup.select(selector)
            for link in links:
                text = link.get_text().strip().lower()
                if text and text not in categories:
                    categories.append(text)
        
        # Add evidence-based nutrition categories
        evidence_keywords = [
            'evidence-based nutrition', 'scientific nutrition',
            'dietary guidelines', 'nutrition research',
            'public health nutrition', 'preventive nutrition'
        ]
        
        categories.extend(evidence_keywords)
        
        return list(set(categories))
    
    def _is_content_relevant(self, content: str, topics: List[str]) -> bool:
        """Check if content is relevant to gut health and nutrition topics"""
        content_lower = content.lower()
        
        # Harvard Nutrition specific keywords
        nutrition_keywords = [
            'nutrition', 'diet', 'food', 'fiber', 'probiotic',
            'digestive', 'gut', 'microbiome', 'healthy eating',
            'nutrients', 'vitamins', 'minerals', 'antioxidants',
            'whole grains', 'vegetables', 'fruits', 'protein'
        ]
        
        # Check for topic relevance
        topic_match = any(topic.lower() in content_lower for topic in topics)
        keyword_match = any(keyword in content_lower for keyword in nutrition_keywords)
        
        return topic_match or keyword_match
