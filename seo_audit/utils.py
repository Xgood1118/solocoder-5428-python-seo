from urllib.parse import urlparse, urljoin, urldefrag
from typing import Optional


def extract_domain(url: str) -> str:
    parsed = urlparse(url)
    return parsed.netloc.lower()


def is_same_domain(url1: str, url2: str) -> bool:
    return extract_domain(url1) == extract_domain(url2)


def normalize_url(url: str, base_url: Optional[str] = None) -> str:
    if base_url:
        url = urljoin(base_url, url)
    url, _ = urldefrag(url)
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return url
    path = parsed.path if parsed.path else "/"
    normalized = f"{parsed.scheme}://{parsed.netloc}{path}"
    if parsed.query:
        normalized += f"?{parsed.query}"
    return normalized


def is_internal_link(url: str, base_domain: str) -> bool:
    try:
        parsed = urlparse(url)
        if not parsed.netloc:
            return True
        return parsed.netloc.lower() == base_domain.lower()
    except Exception:
        return False


def is_valid_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        return bool(parsed.scheme) and bool(parsed.netloc)
    except Exception:
        return False
