"""
Specialist Crawler - Focused crawling of specialist gut health and microbiome sites
"""
import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional
import time
import re

logger = logging.getLogger(__name__)

class SpecialistCrawler:
    """Crawler for specialist gut health and microbiome websites"""
    
    def __init__(self):
        self.specialist_sites = {
            'gut_microbiota_health': {
                'name': 'Gut Microbiota for Health',
                'base_url': 'https://www.gutmicrobiotaforhealth.com',
                'article_patterns': ['/en/category/', '/en/tag/', '/en/'],
                'content_selectors': ['.entry-content', '.post-content', 'article'],
                'pagination_selector': '.pagination a'
            },
            'isapp': {
                'name': 'International Scientific Association for Probiotics',
                'base_url': 'https://isappscience.org',
                'article_patterns': ['/category/', '/tag/', '/'],
                'content_selectors': ['.entry-content', '.content', 'main'],
                'pagination_selector': '.page-numbers a'
            },
            'microbiome_institute': {
                'name': 'Microbiome Institute',
                'base_url': 'https://microbiomeinstitute.org',
                'article_patterns': ['/blog/', '/research/', '/news/'],
                'content_selectors': ['.post-content', '.entry-content', 'article'],
                'pagination_selector': '.pagination a'
            },
            'american_gut': {
                'name': 'American Gut Project',
                'base_url': 'https://americangut.org',
                'article_patterns': ['/results/', '/blog/', '/news/'],
                'content_selectors': ['.content', '.post', 'main'],
                'pagination_selector': '.pagination a'
            }
        }
    
    async def crawl_specialist_sites(self, 
                                   topics: List[str], 
                                   max_articles: int = 100) -> List[Dict]:
        """
        Crawl specialist gut health and microbiome sites
        
        Args:
            topics: List of health topics to search for
            max_articles: Maximum articles per site
            
        Returns:
            List of articles from specialist sites
        """
        all_articles = []
        
        async with aiohttp.ClientSession() as session:
            for site_id, config in self.specialist_sites.items():
                try:
                    logger.info(f"Crawling {config['name']}...")
                    
                    articles = await self._crawl_specialist_site(
                        session, site_id, config, topics, max_articles
                    )
                    
                    all_articles.extend(articles)
                    logger.info(f"Collected {len(articles)} articles from {config['name']}")
                    
                    # Rate limiting between sites
                    await asyncio.sleep(3)
                    
                except Exception as e:
                    logger.error(f"Error crawling {config['name']}: {e}")
        
        return all_articles
    
    async def _crawl_specialist_site(self, 
                                   session: aiohttp.ClientSession,
                                   site_id: str,
                                   config: Dict,
                                   topics: List[str],
                                   max_articles: int) -> List[Dict]:
        """Crawl a single specialist site"""
        articles = []
        
        try:
            # Discover article URLs
            urls = await self._discover_article_urls(session, config, topics, max_articles)
            
            if not urls:
                logger.warning(f"No URLs found for {config['name']}")
                return []
            
            # Process URLs in batches
            batch_size = 3  # Conservative for specialist sites
            for i in range(0, len(urls), batch_size):
                batch_urls = urls[i:i + batch_size]
                
                batch_articles = await asyncio.gather(
                    *[self._scrape_specialist_article(session, url, config, site_id) 
                      for url in batch_urls],
                    return_exceptions=True
                )
                
                # Filter out exceptions and None results
                for article in batch_articles:
                    if isinstance(article, dict):
                        articles.append(article)
                
                # Conservative rate limiting
                await asyncio.sleep(2)
        
        except Exception as e:
            logger.error(f"Error in specialist site crawl for {site_id}: {e}")
        
        return articles
    
    async def _discover_article_urls(self, 
                                   session: aiohttp.ClientSession,
                                   config: Dict,
                                   topics: List[str],
                                   max_articles: int) -> List[str]:
        """Discover article URLs through category and tag pages"""
        urls = set()
        
        try:
            base_url = config['base_url']
            
            # Method 1: Try to find sitemap
            sitemap_urls = await self._try_sitemap(session, base_url)
            if sitemap_urls:
                urls.update(sitemap_urls[:max_articles // 2])
            
            # Method 2: Crawl category and tag pages
            category_urls = await self._crawl_categories(session, config, topics)
            urls.update(category_urls[:max_articles // 2])
            
            # Method 3: Try RSS feeds
            rss_urls = await self._try_rss_feeds(session, base_url, topics)
            urls.update(rss_urls[:max_articles // 4])
            
        except Exception as e:
            logger.error(f"Error discovering URLs for {config['name']}: {e}")
        
        return list(urls)[:max_articles]
    
    async def _try_sitemap(self, 
                         session: aiohttp.ClientSession, 
                         base_url: str) -> List[str]:
        """Try to fetch URLs from sitemap"""
        sitemap_urls = [
            f"{base_url}/sitemap.xml",
            f"{base_url}/sitemap_index.xml",
            f"{base_url}/wp-sitemap.xml"
        ]
        
        for sitemap_url in sitemap_urls:
            try:
                async with session.get(sitemap_url) as response:
                    if response.status == 200:
                        content = await response.text()
                        return self._parse_sitemap_urls(content)
            except:
                continue
        
        return []
    
    def _parse_sitemap_urls(self, sitemap_content: str) -> List[str]:
        """Parse URLs from sitemap XML"""
        urls = []
        
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(sitemap_content)
            
            # Handle regular sitemap
            for url_elem in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}url'):
                loc_elem = url_elem.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
                if loc_elem is not None:
                    url = loc_elem.text
                    # Filter for relevant content
                    if any(keyword in url.lower() for keyword in 
                          ['blog', 'article', 'post', 'research', 'news', 'microbiome', 'gut', 'probiotic']):
                        urls.append(url)
            
            # Handle sitemap index
            for sitemap_elem in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}sitemap'):
                loc_elem = sitemap_elem.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
                if loc_elem is not None:
                    # Could recursively fetch sub-sitemaps here
                    pass
                    
        except Exception as e:
            logger.error(f"Error parsing sitemap: {e}")
        
        return urls
    
    async def _crawl_categories(self, 
                              session: aiohttp.ClientSession,
                              config: Dict,
                              topics: List[str]) -> List[str]:
        """Crawl category and tag pages for article URLs"""
        urls = set()
        base_url = config['base_url']
        
        # Common category/tag paths to try
        category_paths = [
            '/category/gut-health/', '/category/microbiome/', '/category/probiotics/',
            '/category/nutrition/', '/category/research/', '/tag/microbiota/',
            '/tag/digestive-health/', '/blog/', '/research/', '/news/'
        ]
        
        for path in category_paths:
            try:
                category_url = base_url + path
                async with session.get(category_url) as response:
                    if response.status == 200:
                        content = await response.text()
                        page_urls = self._extract_article_links(content, base_url)
                        urls.update(page_urls)
                
                # Rate limiting
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.warning(f"Error crawling category {path}: {e}")
        
        return list(urls)
    
    def _extract_article_links(self, html_content: str, base_url: str) -> List[str]:
        """Extract article links from HTML content"""
        urls = []
        
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Look for article links
            link_selectors = [
                'a[href*="/post/"]', 'a[href*="/article/"]', 'a[href*="/blog/"]',
                'a[href*="/research/"]', 'a[href*="/news/"]', '.post-title a',
                '.entry-title a', 'h2 a', 'h3 a'
            ]
            
            for selector in link_selectors:
                links = soup.select(selector)
                for link in links:
                    href = link.get('href')
                    if href:
                        # Convert relative URLs to absolute
                        if href.startswith('/'):
                            href = base_url + href
                        elif not href.startswith('http'):
                            continue
                        
                        # Filter for relevant URLs
                        if self._is_relevant_url(href):
                            urls.append(href)
                            
        except Exception as e:
            logger.error(f"Error extracting links: {e}")
        
        return urls
    
    def _is_relevant_url(self, url: str) -> bool:
        """Check if URL is relevant for gut health content"""
        url_lower = url.lower()
        
        relevant_keywords = [
            'microbiome', 'gut', 'probiotic', 'prebiotic', 'digestive',
            'nutrition', 'fiber', 'bacteria', 'microbiota', 'intestinal',
            'health', 'research', 'study', 'article', 'blog', 'post'
        ]
        
        # Exclude unwanted URLs
        excluded_keywords = [
            'login', 'register', 'admin', 'wp-', 'feed', 'rss',
            'contact', 'about', 'privacy', 'terms'
        ]
        
        has_relevant = any(keyword in url_lower for keyword in relevant_keywords)
        has_excluded = any(keyword in url_lower for keyword in excluded_keywords)
        
        return has_relevant and not has_excluded
    
    async def _try_rss_feeds(self, 
                           session: aiohttp.ClientSession,
                           base_url: str,
                           topics: List[str]) -> List[str]:
        """Try to find content through RSS feeds"""
        rss_urls = [
            f"{base_url}/feed/",
            f"{base_url}/rss/",
            f"{base_url}/feed.xml",
            f"{base_url}/rss.xml"
        ]
        
        urls = []
        
        for rss_url in rss_urls:
            try:
                async with session.get(rss_url) as response:
                    if response.status == 200:
                        content = await response.text()
                        feed_urls = self._parse_rss_feed(content)
                        urls.extend(feed_urls)
                        break  # Use first working RSS feed
            except:
                continue
        
        return urls
    
    def _parse_rss_feed(self, rss_content: str) -> List[str]:
        """Parse URLs from RSS feed"""
        urls = []
        
        try:
            import feedparser
            feed = feedparser.parse(rss_content)
            
            for entry in feed.entries[:50]:  # Limit to recent entries
                if hasattr(entry, 'link'):
                    urls.append(entry.link)
                    
        except Exception as e:
            logger.error(f"Error parsing RSS feed: {e}")
        
        return urls
    
    async def _scrape_specialist_article(self, 
                                       session: aiohttp.ClientSession,
                                       url: str,
                                       config: Dict,
                                       site_id: str) -> Optional[Dict]:
        """Scrape content from a specialist site article"""
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    return None
                
                html_content = await response.text()
                
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Extract title
                title = self._extract_title(soup)
                if not title:
                    return None
                
                # Extract content
                content = self._extract_content(soup, config['content_selectors'])
                if not content or len(content) < 200:  # Higher minimum for specialist content
                    return None
                
                # Extract metadata
                publication_date = self._extract_date(soup)
                author = self._extract_author(soup)
                tags = self._extract_tags(soup)
                
                article = {
                    'source': f'specialist_{site_id}',
                    'site_name': config['name'],
                    'title': title,
                    'content': content,
                    'url': url,
                    'author': author,
                    'publication_date': publication_date,
                    'tags': tags,
                    'categories': ['specialist', 'microbiome', 'gut_health'],
                    'language': 'en',
                    'content_type': 'specialist_article',
                    'crawl_timestamp': time.time()
                }
                
                return article
                
        except Exception as e:
            logger.warning(f"Error scraping specialist article {url}: {e}")
            return None
    
    def _extract_title(self, soup) -> Optional[str]:
        """Extract article title"""
        title_selectors = [
            'h1.entry-title', 'h1.post-title', 'h1', 
            '.entry-title', '.post-title', 'title'
        ]
        
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element and element.get_text(strip=True):
                return element.get_text(strip=True)
        
        return None
    
    def _extract_content(self, soup, content_selectors: List[str]) -> Optional[str]:
        """Extract main article content"""
        content_parts = []
        
        for selector in content_selectors:
            elements = soup.select(selector)
            for element in elements:
                # Remove unwanted elements
                for unwanted in element.select(
                    'nav, footer, aside, .sidebar, .menu, .comments, '
                    '.social-share, .related-posts, .advertisement'
                ):
                    unwanted.decompose()
                
                text = element.get_text(strip=True)
                if text and len(text) > 100:
                    content_parts.append(text)
        
        if content_parts:
            full_content = '\n\n'.join(content_parts)
            # Clean up content
            full_content = re.sub(r'\n\s*\n', '\n\n', full_content)
            return full_content.strip()
        
        return None
    
    def _extract_date(self, soup) -> Optional[str]:
        """Extract publication date"""
        date_selectors = [
            'time[datetime]', '.published', '.post-date', 
            '.entry-date', 'meta[property="article:published_time"]'
        ]
        
        for selector in date_selectors:
            element = soup.select_one(selector)
            if element:
                date_value = (element.get('datetime') or 
                            element.get('content') or 
                            element.get_text(strip=True))
                if date_value:
                    return date_value
        
        return None
    
    def _extract_author(self, soup) -> Optional[str]:
        """Extract author information"""
        author_selectors = [
            '.author', '.byline', '.post-author', 
            'meta[name="author"]', '.entry-author'
        ]
        
        for selector in author_selectors:
            element = soup.select_one(selector)
            if element:
                author = element.get('content') or element.get_text(strip=True)
                if author:
                    return author
        
        return None
    
    def _extract_tags(self, soup) -> List[str]:
        """Extract article tags"""
        tags = []
        
        tag_selectors = [
            '.tags a', '.post-tags a', '.entry-tags a',
            'meta[property="article:tag"]'
        ]
        
        for selector in tag_selectors:
            elements = soup.select(selector)
            for element in elements:
                tag_text = element.get('content') or element.get_text(strip=True)
                if tag_text:
                    tags.append(tag_text)
        
        return tags[:10]  # Limit number of tags
