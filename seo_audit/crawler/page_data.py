from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class PageData:
    url: str
    status_code: int
    headers: Dict[str, str] = field(default_factory=dict)
    html: str = ""
    title: str = ""
    description: str = ""
    keywords: str = ""
    h1_tags: List[str] = field(default_factory=list)
    h2_tags: List[str] = field(default_factory=list)
    text_content: str = ""
    word_count: int = 0
    internal_links: List[str] = field(default_factory=list)
    external_links: List[str] = field(default_factory=list)
    images: List[Dict] = field(default_factory=list)
    canonical: Optional[str] = None
    hreflang: List[Dict] = field(default_factory=list)
    meta_robots: str = ""
    viewport: str = ""
    og_tags: Dict[str, str] = field(default_factory=dict)
    twitter_tags: Dict[str, str] = field(default_factory=dict)
    json_ld: List[dict] = field(default_factory=list)
    has_breadcrumb: bool = False
    has_structured_data: bool = False
    redirect_chain: List[str] = field(default_factory=list)
    load_time: float = 0.0
    is_404: bool = False
    is_5xx: bool = False
    content_type: str = ""
    final_url: str = ""
    lighthouse_data: Optional[dict] = None
