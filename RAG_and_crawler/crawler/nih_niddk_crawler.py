"""
NIH NIDDK Crawler - Fetches digestive health information from the
National Institute of Diabetes and Digestive and Kidney Diseases
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

class NIHNIDDKCrawler:
    """Crawler for NIH NIDDK digestive health content"""
    
    def __init__(self):
        self.base_url = "https://www.niddk.nih.gov"
        self.digestive_sections = [
            "/health-information/digestive-diseases",
            "/health-information/digestive-diseases/irritable-bowel-syndrome",
            "/health-information/digestive-diseases/inflammatory-bowel-disease",
            "/health-information/digestive-diseases/celiac-disease",
            "/health-information/digestive-diseases/gastroesophageal-reflux-gerd", 
            "/health-information/digestive-diseases/constipation",
            "/health-information/digestive-diseases/diarrhea",
            "/health-information/weight-management"
        ]
        
        self.session_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }
    
    async def crawl_nih_niddk(self, 
                             topics: List[str], 
                             max_articles: int = 100) -> List[Dict]:
        """
        Crawl NIH NIDDK for authoritative digestive health information
        
        Args:
            topics: List of topics to search for
            max_articles: Maximum number of articles to collect
            
        Returns:
            List of article dictionaries
        """
        logger.info(f"Starting NIH NIDDK crawl for topics: {topics}")
        
        articles = []
        
        async with aiohttp.ClientSession(
            headers=self.session_headers,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as session:
            
            # Crawl digestive health sections
            for section in self.digestive_sections:
                if len(articles) >= max_articles:
                    break
                    
                section_articles = await self._crawl_section(
                    session, section, topics, max_articles - len(articles)
                )
                articles.extend(section_articles)
                
                await asyncio.sleep(1)
            
            # Get sitemap content
            sitemap_articles = await self._crawl_sitemap(
                session, topics, max_articles - len(articles)
            )
            articles.extend(sitemap_articles)
        
        logger.info(f"NIH NIDDK crawl completed. Collected {len(articles)} articles")
        return articles[:max_articles]
    
    async def _crawl_section(self, 
                           session: aiohttp.ClientSession,
                           section_path: str,
                           topics: List[str],
                           max_articles: int) -> List[Dict]:
        """Crawl a specific NIH NIDDK section"""
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
            logger.error(f"Error crawling NIH NIDDK section {section_path}: {e}")
        
        return articles
    
    async def _crawl_sitemap(self, 
                           session: aiohttp.ClientSession,
                           topics: List[str],
                           max_articles: int) -> List[Dict]:
        """Crawl NIH NIDDK sitemap for health information"""
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
                health_urls = [url for url in urls if '/health-information/' in url]
                
                # Process relevant URLs
                for url in health_urls[:max_articles * 2]:
                    if len(articles) >= max_articles:
                        break
                        
                    if self._is_relevant_url(url):
                        article = await self._fetch_article(session, url, topics)
                        if article:
                            articles.append(article)
                            
                        await asyncio.sleep(0.5)
                        
        except Exception as e:
            logger.error(f"Error crawling NIH NIDDK sitemap: {e}")
        
        return articles
    
    def _extract_article_links(self, soup: BeautifulSoup) -> List[str]:
        """Extract article links from a section page"""
        links = []
        
        # NIH NIDDK selectors
        selectors = [
            'a[href*="/health-information/"]',
            '.content-list a',
            '.topic-list a',
            '.health-topic a',
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
        """Check if URL is relevant for digestive health"""
        relevant_patterns = [
            r'/health-information/digestive-diseases',
            r'/health-information/weight-management',
            r'/digestive',
            r'/gut',
            r'/nutrition',
            r'/diet',
            r'/fiber',
            r'/probiotic',
            r'/microbiome',
            r'/irritable-bowel',
            r'/inflammatory-bowel',
            r'/celiac',
            r'/gastro'
        ]
        
        return any(re.search(pattern, url, re.IGNORECASE) for pattern in relevant_patterns)
    
    async def _fetch_article(self, 
                           session: aiohttp.ClientSession,
                           url: str,
                           topics: List[str]) -> Optional[Dict]:
        """Fetch and parse an NIH NIDDK article"""
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
                date = self._extract_date(soup)
                categories = self._extract_categories(soup, url)
                
                return {
                    'title': title,
                    'content': content,
                    'url': url,
                    'source': 'NIH NIDDK',
                    'author': 'National Institute of Diabetes and Digestive and Kidney Diseases',
                    'publication_date': date,
                    'categories': categories,
                    'content_type': 'government_health_info',
                    'institution': 'National Institutes of Health',
                    'authority_level': 'federal_government',
                    'crawled_at': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error fetching NIH NIDDK article {url}: {e}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article title"""
        selectors = [
            'h1.page-title',
            'h1.article-title',
            'h1.main-title',
            'h1',
            '.content-title',
            '.health-title'
        ]
        
        for selector in selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                return title_elem.get_text().strip()
        
        return None
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Extract main article content"""
        content_parts = []
        
        # NIH NIDDK content selectors
        content_selectors = [
            '.main-content',
            '.article-content',
            '.health-content',
            '.page-content',
            '.content-body'
        ]
        
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                # Remove unwanted elements
                for unwanted in content_elem.select('script, style, .sidebar, .navigation'):
                    unwanted.decompose()
                
                # Get text from structured elements
                text_elements = content_elem.select('p, li, h2, h3, h4, h5, blockquote, .highlight-box')
                for elem in text_elements:
                    text = elem.get_text().strip()
                    if text and len(text) > 25:  # Filter meaningful content
                        content_parts.append(text)
        
        # Fallback: get all paragraphs
        if not content_parts:
            paragraphs = soup.select('p')
            content_parts = [p.get_text().strip() for p in paragraphs if len(p.get_text().strip()) > 25]
        
        return '\n\n'.join(content_parts)
    
    def _extract_date(self, soup: BeautifulSoup) -> str:
        """Extract publication or last reviewed date"""
        date_selectors = [
            '.last-reviewed',
            '.publication-date',
            '.updated-date',
            '.review-date',
            'time[datetime]',
            '[data-date]'
        ]
        
        for selector in date_selectors:
            date_elem = soup.select_one(selector)
            if date_elem:
                date_text = date_elem.get('datetime') or date_elem.get_text()
                if date_text:
                    # NIH often uses "Last Reviewed: Month Year" format
                    cleaned_date = re.sub(r'Last Reviewed:?\s*', '', date_text, flags=re.IGNORECASE)
                    return cleaned_date.strip()
        
        return datetime.now().strftime('%Y-%m-%d')
    
    def _extract_categories(self, soup: BeautifulSoup, url: str) -> List[str]:
        """Extract article categories"""
        categories = ['nih-niddk', 'digestive-health', 'government-health']
        
        # Extract from URL path
        if '/digestive-diseases/' in url:
            categories.append('digestive-diseases')
        if '/weight-management/' in url:
            categories.append('weight-management')
        if '/irritable-bowel' in url:
            categories.append('irritable-bowel-syndrome')
        if '/inflammatory-bowel' in url:
            categories.append('inflammatory-bowel-disease')
        if '/celiac' in url:
            categories.append('celiac-disease')
        if '/gastroesophageal-reflux' in url:
            categories.append('gerd')
        
        # Extract from breadcrumbs
        breadcrumb_selectors = [
            '.breadcrumb a',
            '.navigation-path a',
            '.page-path a'
        ]
        
        for selector in breadcrumb_selectors:
            links = soup.select(selector)
            for link in links:
                text = link.get_text().strip().lower()
                if text and text not in categories:
                    categories.append(text)
        
        # Add authoritative health categories
        authority_keywords = [
            'evidence-based medicine', 'clinical guidelines',
            'patient education', 'health information',
            'medical research', 'digestive disorders'
        ]
        
        categories.extend(authority_keywords)
        
        return list(set(categories))
    
    def _is_content_relevant(self, content: str, topics: List[str]) -> bool:
        """Check if content is relevant to digestive health topics"""
        content_lower = content.lower()
        
        # NIH digestive health keywords
        digestive_keywords = [
            'digestive', 'gut', 'intestine', 'stomach', 'bowel',
            'colon', 'nutrition', 'diet', 'fiber', 'probiotic',
            'microbiome', 'gastro', 'digestion', 'absorption',
            'irritable bowel', 'inflammatory bowel', 'celiac',
            'gerd', 'reflux', 'constipation', 'diarrhea'
        ]
        
        # Check for topic relevance
        topic_match = any(topic.lower() in content_lower for topic in topics)
        keyword_match = any(keyword in content_lower for keyword in digestive_keywords)
        
        return topic_match or keyword_match
