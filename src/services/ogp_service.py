import httpx
from bs4 import BeautifulSoup
from typing import Optional, Dict
from src.core.logger import setup_logger

logger = setup_logger(__name__)

class OGPService:
    """Service to fetch Open Graph Protocol metadata from URLs."""
    
    @staticmethod
    async def fetch_ogp(url: str) -> Optional[Dict[str, str]]:
        """
        Fetch OGP metadata from a given URL.
        
        Args:
            url: The URL to fetch metadata from
            
        Returns:
            Dictionary containing title, description, and image URL, or None if fetch fails
        """
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                response = await client.get(url, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'lxml')
                
                # Extract OGP metadata
                ogp_data = {}
                
                # Try OGP tags first
                og_title = soup.find('meta', property='og:title')
                og_description = soup.find('meta', property='og:description')
                og_image = soup.find('meta', property='og:image')
                
                # Fallback to standard meta tags
                title_tag = soup.find('title')
                meta_description = soup.find('meta', attrs={'name': 'description'})
                
                ogp_data['title'] = (
                    og_title.get('content') if og_title 
                    else title_tag.string if title_tag 
                    else url
                )
                
                ogp_data['description'] = (
                    og_description.get('content') if og_description 
                    else meta_description.get('content') if meta_description 
                    else ''
                )
                
                ogp_data['image'] = og_image.get('content') if og_image else ''
                
                logger.info(f"✅ OGP fetched for {url[:50]}...")
                return ogp_data
                
        except Exception as e:
            logger.error(f"❌ OGP fetch error for {url}: {e}")
            return None
