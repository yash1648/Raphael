"""Web search and content fetching capability."""

import re
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup


class WebSearchTool:
    """Web research tool — search, fetch, and extract content."""

    def __init__(self):
        self._http = httpx.Client(timeout=30, follow_redirects=True)
        self._search_urls = {
            "google": "https://www.google.com/search?q={query}",
            "duckduckgo": "https://html.duckduckgo.com/html/?q={query}",
        }

    def search_web(self, query: str, num_results: int = 5) -> list[dict]:
        """Search the web for a query and return results."""
        try:
            url = self._search_urls["duckduckgo"].format(query=query.replace(" ", "+"))
            resp = self._http.get(url, headers=self._headers())
            resp.raise_for_status()
            return self._parse_ddg_results(resp.text, num_results)
        except Exception as e:
            return [{"title": "Search failed", "url": "", "snippet": f"Error: {e}"}]

    def fetch_page(self, url: str) -> dict:
        """Fetch and extract readable content from a URL."""
        try:
            resp = self._http.get(url, headers=self._headers())
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            # Remove non-content elements
            for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                tag.decompose()

            title = soup.title.string.strip() if soup.title else ""
            text = soup.get_text(separator="\n", strip=True)
            # Clean up whitespace
            lines = [line for line in text.split("\n") if line.strip()]
            content = "\n".join(lines[:200])  # First 200 lines

            return {
                "url": url,
                "title": title,
                "content": content[:10000],  # Truncate to 10k chars
                "success": True,
            }
        except Exception as e:
            return {"url": url, "title": "", "content": "", "success": False, "error": str(e)}

    def _headers(self) -> dict:
        return {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
        }

    def _parse_ddg_results(self, html: str, num_results: int) -> list[dict]:
        """Parse DuckDuckGo HTML search results."""
        soup = BeautifulSoup(html, "html.parser")
        results = []

        for result in soup.select(".result")[:num_results]:
            title_el = result.select_one(".result__title a")
            snippet_el = result.select_one(".result__snippet")

            if title_el:
                title = title_el.get_text(strip=True)
                url = title_el.get("href", "")
                # DDG wraps URLs
                if url and "uddg=" in str(url):
                    from urllib.parse import parse_qs, urlparse
                    parsed = urlparse(str(url))
                    qs = parse_qs(parsed.query)
                    url = qs.get("uddg", [""])[0]

                snippet = snippet_el.get_text(strip=True) if snippet_el else ""

                results.append({
                    "title": title,
                    "url": url,
                    "snippet": snippet,
                })

        return results

    def close(self):
        self._http.close()
