"""
PubMed Crawler - Fetches scientific articles from PubMed Central
using the NCBI Entrez API
"""
import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional
import xml.etree.ElementTree as ET
from urllib.parse import quote_plus
import time

logger = logging.getLogger(__name__)

class PubMedCrawler:
    """Crawler for PubMed Central scientific literature"""
    
    def __init__(self):
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
        self.email = "bettergut@example.com"  # Replace with your email
        self.api_key = None  # Optional: Add your NCBI API key for higher rate limits
        
    async def search_articles(self, 
                            topics: List[str], 
                            max_results: int = 100,
                            years_back: int = 5) -> List[Dict]:
        """
        Search for articles related to gut health and nutrition
        
        Args:
            topics: List of search terms
            max_results: Maximum number of articles to retrieve
            years_back: How many years back to search
            
        Returns:
            List of article dictionaries with metadata and abstracts
        """
        articles = []
        
        # Construct search query
        gut_health_terms = [
            "gut health", "microbiome", "digestive health", "intestinal health",
            "probiotics", "prebiotics", "fiber", "gut bacteria", "microbiota",
            "gut-brain axis", "digestive system", "gastrointestinal"
        ]
        
        # Combine user topics with gut health terms
        search_terms = list(set(topics + gut_health_terms))
        
        # Create PubMed search query
        query_parts = []
        for term in search_terms[:10]:  # Limit to avoid too long queries
            query_parts.append(f'"{term}"[Title/Abstract]')
        
        query = " OR ".join(query_parts)
        query += f" AND {2024-years_back}:{2024}[pdat]"  # Date filter
        
        try:
            # Step 1: Search for article IDs
            search_url = f"{self.base_url}esearch.fcgi"
            search_params = {
                'db': 'pubmed',
                'term': query,
                'retmax': max_results,
                'retmode': 'json',
                'email': self.email
            }
            
            if self.api_key:
                search_params['api_key'] = self.api_key
            
            logger.info(f"Searching PubMed for: {query}")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(search_url, params=search_params) as response:
                    if response.status == 200:
                        search_data = await response.json()
                        id_list = search_data.get('esearchresult', {}).get('idlist', [])
                        
                        if not id_list:
                            logger.warning("No PubMed articles found for the search query")
                            return []
                        
                        logger.info(f"Found {len(id_list)} PubMed article IDs")
                        
                        # Step 2: Fetch article details in batches
                        articles = await self._fetch_article_details(session, id_list)
                    else:
                        logger.error(f"PubMed search failed with status {response.status}")
                        
        except Exception as e:
            logger.error(f"Error searching PubMed: {e}")
        
        return articles
    
    async def _fetch_article_details(self, session: aiohttp.ClientSession, 
                                   id_list: List[str]) -> List[Dict]:
        """Fetch detailed information for articles by ID"""
        articles = []
        batch_size = 20  # Process in batches to avoid overwhelming the API
        
        for i in range(0, len(id_list), batch_size):
            batch_ids = id_list[i:i + batch_size]
            
            try:
                # Fetch article summaries
                summary_url = f"{self.base_url}esummary.fcgi"
                summary_params = {
                    'db': 'pubmed',
                    'id': ','.join(batch_ids),
                    'retmode': 'json',
                    'email': self.email
                }
                
                if self.api_key:
                    summary_params['api_key'] = self.api_key
                
                async with session.get(summary_url, params=summary_params) as response:
                    if response.status == 200:
                        summary_data = await response.json()
                        
                        # Process each article
                        for uid, article_data in summary_data.get('result', {}).items():
                            if uid == 'uids':
                                continue
                                
                            try:
                                article = self._parse_pubmed_article(article_data)
                                if article:
                                    articles.append(article)
                            except Exception as e:
                                logger.warning(f"Error parsing article {uid}: {e}")
                    
                    # Rate limiting - be respectful to NCBI servers
                    await asyncio.sleep(0.5)
                    
            except Exception as e:
                logger.error(f"Error fetching batch {i//batch_size + 1}: {e}")
        
        logger.info(f"Successfully parsed {len(articles)} PubMed articles")
        return articles
    
    def _parse_pubmed_article(self, article_data: Dict) -> Optional[Dict]:
        """Parse PubMed article data into standardized format"""
        try:
            # Extract authors
            authors = []
            author_list = article_data.get('authors', [])
            for author in author_list[:5]:  # Limit to first 5 authors
                name = author.get('name', '')
                if name:
                    authors.append(name)
            
            # Extract publication date
            pub_date = article_data.get('pubdate', '')
            
            # Extract journal info
            journal = article_data.get('fulljournalname', '') or article_data.get('source', '')
            
            # Extract DOI if available
            doi = None
            for article_id in article_data.get('articleids', []):
                if article_id.get('idtype') == 'doi':
                    doi = article_id.get('value')
                    break
            
            article = {
                'source': 'pubmed',
                'pmid': article_data.get('uid'),
                'title': article_data.get('title', ''),
                'abstract': article_data.get('abstract', ''),
                'authors': authors,
                'journal': journal,
                'publication_date': pub_date,
                'doi': doi,
                'url': f"https://pubmed.ncbi.nlm.nih.gov/{article_data.get('uid')}/",
                'categories': ['scientific_literature', 'peer_reviewed'],
                'language': 'en',
                'content_type': 'research_article',
                'crawl_timestamp': time.time()
            }
            
            return article
            
        except Exception as e:
            logger.error(f"Error parsing PubMed article: {e}")
            return None

    async def get_full_text(self, pmid: str) -> Optional[str]:
        """
        Attempt to get full text from PubMed Central (PMC)
        Note: This only works for open-access articles
        """
        try:
            # Check if article is available in PMC
            link_url = f"{self.base_url}elink.fcgi"
            link_params = {
                'dbfrom': 'pubmed',
                'db': 'pmc',
                'id': pmid,
                'retmode': 'json',
                'email': self.email
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(link_url, params=link_params) as response:
                    if response.status == 200:
                        link_data = await response.json()
                        
                        # Check if PMC link exists
                        linksets = link_data.get('linksets', [])
                        if linksets and 'linksetdbs' in linksets[0]:
                            for linksetdb in linksets[0]['linksetdbs']:
                                if linksetdb.get('dbto') == 'pmc':
                                    pmc_ids = linksetdb.get('links', [])
                                    if pmc_ids:
                                        # Try to fetch full text from PMC
                                        return await self._fetch_pmc_fulltext(session, pmc_ids[0])
            
        except Exception as e:
            logger.error(f"Error fetching full text for PMID {pmid}: {e}")
        
        return None
    
    async def _fetch_pmc_fulltext(self, session: aiohttp.ClientSession, 
                                pmc_id: str) -> Optional[str]:
        """Fetch full text from PMC"""
        try:
            fetch_url = f"{self.base_url}efetch.fcgi"
            fetch_params = {
                'db': 'pmc',
                'id': pmc_id,
                'retmode': 'xml',
                'email': self.email
            }
            
            async with session.get(fetch_url, params=fetch_params) as response:
                if response.status == 200:
                    xml_content = await response.text()
                    
                    # Parse XML and extract text content
                    root = ET.fromstring(xml_content)
                    
                    # Extract body text (simplified extraction)
                    full_text_parts = []
                    for elem in root.iter():
                        if elem.text and elem.tag in ['p', 'title', 'abstract']:
                            full_text_parts.append(elem.text.strip())
                    
                    return '\n\n'.join(full_text_parts)
                    
        except Exception as e:
            logger.error(f"Error fetching PMC full text for ID {pmc_id}: {e}")
        
        return None
