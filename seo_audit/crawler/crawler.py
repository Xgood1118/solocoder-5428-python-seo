import asyncio
import time
from collections import defaultdict
from typing import Dict, List, Optional, Set
from urllib.parse import urlparse, urljoin

import aiohttp
from bs4 import BeautifulSoup

from ..config import settings
from ..utils import extract_domain, normalize_url, is_internal_link, is_valid_url
from .rate_limiter import DomainRateLimiter
from .robots_parser import RobotsTxtParser
from .page_parser import PageParser
from .page_data import PageData


class Crawler:
    def __init__(self, max_pages: int = None, rate_limit: int = None):
        self.max_pages = max_pages or settings.MAX_PAGES_PER_AUDIT
        self.rate_limiter = DomainRateLimiter(rate_limit or settings.RATE_LIMIT_PER_DOMAIN)
        self.user_agent = settings.USER_AGENT
        self._cache: Dict[str, PageData] = {}
        self._cache_timestamps: Dict[str, float] = {}
        self._robots_parsers: Dict[str, RobotsTxtParser] = {}
        self._semaphore = asyncio.Semaphore(10)

    async def audit_site(self, start_url: str) -> Dict[str, PageData]:
        domain = extract_domain(start_url)
        base_scheme = urlparse(start_url).scheme
        base_url = f"{base_scheme}://{domain}"
        await self._load_robots(base_url, domain)
        parser = PageParser(base_domain=domain)
        visited: Set[str] = set()
        to_visit: List[str] = [normalize_url(start_url)]
        results: Dict[str, PageData] = {}
        while to_visit and len(visited) < self.max_pages:
            batch = []
            while to_visit and len(batch) < 10 and len(visited) + len(batch) < self.max_pages:
                url = to_visit.pop(0)
                url = normalize_url(url)
                if url in visited:
                    continue
                if not self._is_allowed_by_robots(url, domain):
                    visited.add(url)
                    continue
                batch.append(url)
                visited.add(url)
            if not batch:
                break
            tasks = [self._fetch_page(url, parser, domain) for url in batch]
            pages = await asyncio.gather(*tasks, return_exceptions=True)
            for i, page in enumerate(pages):
                if isinstance(page, Exception):
                    continue
                if page:
                    results[page.url] = page
                    if page.status_code < 400:
                        for link in page.internal_links:
                            norm_link = normalize_url(link)
                            if norm_link not in visited and is_internal_link(link, domain):
                                if norm_link.startswith(("http://", "https://")):
                                    to_visit.append(norm_link)
        return results

    async def fetch_single(self, url: str) -> Optional[PageData]:
        domain = extract_domain(url)
        base_scheme = urlparse(url).scheme
        base_url = f"{base_scheme}://{domain}"
        await self._load_robots(base_url, domain)
        parser = PageParser(base_domain=domain)
        return await self._fetch_page(url, parser, domain)

    async def _fetch_page(self, url: str, parser: PageParser, domain: str) -> Optional[PageData]:
        cached = self._get_from_cache(url)
        if cached:
            return cached
        url_domain = extract_domain(url)
        await self.rate_limiter.wait(url_domain)
        async with self._semaphore:
            try:
                start_time = time.monotonic()
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        url,
                        headers={"User-Agent": self.user_agent},
                        timeout=aiohttp.ClientTimeout(total=30),
                        allow_redirects=True,
                        ssl=False,
                    ) as response:
                        html = await response.text()
                        load_time = time.monotonic() - start_time
                        page = parser.parse(
                            url=str(response.url),
                            html=html,
                            status_code=response.status,
                            headers=dict(response.headers),
                        )
                        page.load_time = load_time
                        page.final_url = str(response.url)
                        if str(response.url) != url:
                            page.redirect_chain = [url, str(response.url)]
                        self._add_to_cache(url, page)
                        self._add_to_cache(str(response.url), page)
                        return page
            except Exception:
                return None

    async def _load_robots(self, base_url: str, domain: str):
        if domain in self._robots_parsers:
            return
        robots_url = urljoin(base_url, "/robots.txt")
        parser = RobotsTxtParser(user_agent=self.user_agent)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    robots_url,
                    headers={"User-Agent": self.user_agent},
                    timeout=aiohttp.ClientTimeout(total=10),
                    ssl=False,
                ) as response:
                    if response.status == 200:
                        content = await response.text()
                        parser.parse(content)
        except Exception:
            pass
        self._robots_parsers[domain] = parser

    def _is_allowed_by_robots(self, url: str, domain: str) -> bool:
        if domain not in self._robots_parsers:
            return True
        return self._robots_parsers[domain].is_allowed(url)

    def _get_from_cache(self, url: str) -> Optional[PageData]:
        if url in self._cache:
            timestamp = self._cache_timestamps.get(url, 0)
            if time.time() - timestamp < settings.CACHE_TTL:
                return self._cache[url]
            else:
                del self._cache[url]
                del self._cache_timestamps[url]
        return None

    def _add_to_cache(self, url: str, page: PageData):
        self._cache[url] = page
        self._cache_timestamps[url] = time.time()

    def clear_cache(self):
        self._cache.clear()
        self._cache_timestamps.clear()

    def get_robots_parser(self, domain: str) -> Optional[RobotsTxtParser]:
        return self._robots_parsers.get(domain)

    @property
    def cache_size(self) -> int:
        return len(self._cache)
