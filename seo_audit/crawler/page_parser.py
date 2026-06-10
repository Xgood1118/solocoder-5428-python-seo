from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import List, Dict
import json
import re
from .page_data import PageData


class PageParser:
    def __init__(self, base_domain: str = ""):
        self.base_domain = base_domain

    def parse(self, url: str, html: str, status_code: int, headers: dict) -> PageData:
        page = PageData(
            url=url,
            final_url=url,
            status_code=status_code,
            headers=dict(headers) if headers else {},
        )
        page.is_404 = status_code == 404
        page.is_5xx = 500 <= status_code < 600
        page.content_type = headers.get("Content-Type", "") if headers else ""
        if not html or status_code >= 400:
            return page
        try:
            soup = BeautifulSoup(html, "html.parser")
            self._extract_meta(soup, page)
            self._extract_headings(soup, page)
            self._extract_text(soup, page)
            self._extract_links(soup, page, url)
            self._extract_images(soup, page, url)
            self._extract_canonical(soup, page)
            self._extract_hreflang(soup, page)
            self._extract_og_tags(soup, page)
            self._extract_twitter_tags(soup, page)
            self._extract_json_ld(soup, page)
            self._extract_breadcrumb(soup, page)
            page.has_structured_data = len(page.json_ld) > 0
        except Exception:
            pass
        return page

    def _extract_meta(self, soup: BeautifulSoup, page: PageData):
        title_tag = soup.find("title")
        if title_tag and title_tag.string:
            page.title = title_tag.string.strip()
        desc_tag = soup.find("meta", attrs={"name": "description"})
        if desc_tag and desc_tag.get("content"):
            page.description = desc_tag["content"].strip()
        kw_tag = soup.find("meta", attrs={"name": "keywords"})
        if kw_tag and kw_tag.get("content"):
            page.keywords = kw_tag["content"].strip()
        robots_tag = soup.find("meta", attrs={"name": "robots"})
        if robots_tag and robots_tag.get("content"):
            page.meta_robots = robots_tag["content"].strip()
        viewport_tag = soup.find("meta", attrs={"name": "viewport"})
        if viewport_tag and viewport_tag.get("content"):
            page.viewport = viewport_tag["content"].strip()

    def _extract_headings(self, soup: BeautifulSoup, page: PageData):
        for h1 in soup.find_all("h1"):
            text = h1.get_text(strip=True)
            if text:
                page.h1_tags.append(text)
        for h2 in soup.find_all("h2"):
            text = h2.get_text(strip=True)
            if text:
                page.h2_tags.append(text)

    def _extract_text(self, soup: BeautifulSoup, page: PageData):
        for tag in soup(["script", "style", "noscript", "nav", "footer", "header"]):
            tag.decompose()
        main_content = soup.find("main") or soup.find("article") or soup.body
        if main_content:
            text = main_content.get_text(separator=" ", strip=True)
        else:
            text = soup.get_text(separator=" ", strip=True)
        page.text_content = text
        page.word_count = len(re.findall(r'\b\w+\b', text))

    def _extract_links(self, soup: BeautifulSoup, page: PageData, base_url: str):
        base_domain = self.base_domain or urlparse(base_url).netloc.lower()
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"].strip()
            if href.startswith(("javascript:", "mailto:", "tel:", "#")):
                continue
            full_url = urljoin(base_url, href)
            parsed = urlparse(full_url)
            if not parsed.scheme or not parsed.netloc:
                continue
            if parsed.netloc.lower() == base_domain:
                if full_url not in page.internal_links:
                    page.internal_links.append(full_url)
            else:
                if full_url not in page.external_links:
                    page.external_links.append(full_url)

    def _extract_images(self, soup: BeautifulSoup, page: PageData, base_url: str):
        for img in soup.find_all("img"):
            src = img.get("src", "")
            alt = img.get("alt", "")
            full_src = urljoin(base_url, src) if src else ""
            page.images.append({
                "src": full_src,
                "alt": alt,
                "has_alt": bool(alt and alt.strip())
            })

    def _extract_canonical(self, soup: BeautifulSoup, page: PageData):
        canonical_tag = soup.find("link", attrs={"rel": "canonical"})
        if canonical_tag and canonical_tag.get("href"):
            page.canonical = canonical_tag["href"].strip()

    def _extract_hreflang(self, soup: BeautifulSoup, page: PageData):
        for tag in soup.find_all("link", attrs={"rel": "alternate"}):
            if tag.get("hreflang") and tag.get("href"):
                page.hreflang.append({
                    "lang": tag["hreflang"],
                    "href": tag["href"]
                })

    def _extract_og_tags(self, soup: BeautifulSoup, page: PageData):
        for tag in soup.find_all("meta", attrs={"property": re.compile(r"^og:", re.I)}):
            prop = tag.get("property", "")
            content = tag.get("content", "")
            if prop:
                page.og_tags[prop.lower()] = content

    def _extract_twitter_tags(self, soup: BeautifulSoup, page: PageData):
        for tag in soup.find_all("meta", attrs={"name": re.compile(r"^twitter:", re.I)}):
            name = tag.get("name", "")
            content = tag.get("content", "")
            if name:
                page.twitter_tags[name.lower()] = content

    def _extract_json_ld(self, soup: BeautifulSoup, page: PageData):
        for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
            if script.string:
                try:
                    data = json.loads(script.string.strip())
                    if isinstance(data, list):
                        page.json_ld.extend(data)
                    else:
                        page.json_ld.append(data)
                except (json.JSONDecodeError, ValueError):
                    pass

    def _extract_breadcrumb(self, soup: BeautifulSoup, page: PageData):
        if soup.find(attrs={"class": re.compile(r"breadcrumb", re.I)}):
            page.has_breadcrumb = True
        elif soup.find(attrs={"id": re.compile(r"breadcrumb", re.I)}):
            page.has_breadcrumb = True
        elif soup.find("nav", attrs={"aria-label": re.compile(r"breadcrumb", re.I)}):
            page.has_breadcrumb = True
        else:
            for item in page.json_ld:
                if isinstance(item, dict) and item.get("@type") == "BreadcrumbList":
                    page.has_breadcrumb = True
                    break
