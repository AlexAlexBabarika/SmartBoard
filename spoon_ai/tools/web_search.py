"""
Web Search Tool for SpoonOS

This module provides web search functionality using SerpAPI
and content extraction from resulting URLs.
"""
import os
import json
import aiohttp
import asyncio
import ssl
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field

# Create a custom SSL context to handle certificate verification
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

class SearchResult(BaseModel):
    """Model for search results."""
    title: str
    url: str
    snippet: str
    content: str = ""

class WebSearchTool:
    """
    A tool that performs web searches and retrieves page contents.
    
    Requires SERPAPI_KEY to be set in environment variables.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the WebSearchTool with an optional API key."""
        self.api_key = api_key or os.getenv("SERPAPI_KEY")
        if not self.api_key:
            raise ValueError("SERPAPI_KEY not provided and not found in environment variables")
        
        # SerpAPI endpoint
        self.base_url = "https://serpapi.com/search"
        self.params = {
            'api_key': self.api_key,
            'engine': 'google',
            'num': 5,  # Default number of results
            'hl': 'en',  # Language
            'gl': 'us'   # Country
        }
    
    async def _fetch_url_content(self, session: aiohttp.ClientSession, url: str) -> str:
        """Fetch and extract text content from a URL."""
        try:
            # Use the custom SSL context for the request
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            async with session.get(url, timeout=10, ssl=ssl_context) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Remove script and style elements
                    for script in soup(["script", "style", "nav", "footer", "header"]):
                        script.decompose()
                    
                    # Get text and clean up
                    text = soup.get_text(separator=' ', strip=True)
                    # Remove extra whitespace and newlines
                    return ' '.join(text.split())
        except Exception as e:
            print(f"Error fetching {url}: {str(e)}")
        return ""
    
    async def search(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        """
        Perform a web search and retrieve page contents using SerpAPI.
        
        Args:
            query: The search query string
            num_results: Number of results to return (default: 5)
            
        Returns:
            List of dictionaries containing search results with content
        """
        # Prepare the search parameters
        params = self.params.copy()
        params['q'] = query
        params['num'] = min(num_results, 10)  # Limit to 10 results max
        
        # Create a session with custom SSL context
        conn = aiohttp.TCPConnector(ssl=ssl_context)
        async with aiohttp.ClientSession(connector=conn) as session:
            # Perform the search
            async with session.get(
                self.base_url,
                params=params,
                ssl=ssl_context
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Search API error: {response.status} - {error_text}")
                
                search_results = await response.json()
            
            # Extract organic results from SerpAPI response
            results = []
            for item in search_results.get('organic_results', [])[:num_results]:
                if 'link' in item:
                    try:
                        content = await self._fetch_url_content(session, item['link'])
                        results.append({
                            'title': item.get('title', 'No title'),
                            'url': item['link'],
                            'snippet': item.get('snippet', ''),
                            'content': content
                        })
                    except Exception as e:
                        print(f"Error fetching {item['link']}: {str(e)}")
                        # Add result without content if we can't fetch it
                        results.append({
                            'title': item.get('title', 'No title'),
                            'url': item['link'],
                            'snippet': item.get('snippet', ''),
                            'content': ''
                        })
            
            return results

# Example usage
async def example_usage():
    """Example of how to use the WebSearchTool."""
    tool = WebSearchTool()
    results = await tool.search("latest AI developments 2025", num_results=3)
    for result in results:
        print(f"Title: {result['title']}")
        print(f"URL: {result['url']}")
        print(f"Snippet: {result['snippet']}")
        print(f"Content length: {len(result['content'])} characters\n")

if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())
