from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


class Severity(str, Enum):
    CRITICAL = "critical"
    IMPORTANT = "important"
    INFO = "info"


class Weight(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Category(str, Enum):
    CRAWL_INDEX = "crawl_index"
    TDK = "tdk"
    CONTENT_QUALITY = "content_quality"
    TECHNICAL_SEO = "technical_seo"
    PERFORMANCE = "performance"
    MOBILE = "mobile"
    STRUCTURED_DATA = "structured_data"


SEVERITY_SCORES = {
    Severity.CRITICAL: 100,
    Severity.IMPORTANT: 50,
    Severity.INFO: 10,
}

CATEGORY_NAMES = {
    Category.CRAWL_INDEX: "抓取与索引",
    Category.TDK: "TDK 优化",
    Category.CONTENT_QUALITY: "内容质量",
    Category.TECHNICAL_SEO: "技术 SEO",
    Category.PERFORMANCE: "性能优化",
    Category.MOBILE: "移动友好",
    Category.STRUCTURED_DATA: "结构化数据",
}


@dataclass
class Rule:
    id: str
    name: str
    category: Category
    severity: Severity
    weight: Weight
    description: str
    fix_advice: str
    check_function: str = ""
    enabled: bool = True


@dataclass
class RuleResult:
    rule_id: str
    rule_name: str
    category: Category
    severity: Severity
    weight: Weight
    passed: bool
    message: str
    fix_advice: str
    details: Dict[str, Any] = field(default_factory=dict)
    executed: bool = True
    error: Optional[str] = None


@dataclass
class PageAuditResult:
    url: str
    score: float = 0.0
    total_rules: int = 0
    passed_rules: int = 0
    failed_rules: int = 0
    skipped_rules: int = 0
    results: List[RuleResult] = field(default_factory=list)
    critical_issues: int = 0
    important_issues: int = 0
    info_issues: int = 0


@dataclass
class SiteAuditResult:
    site_url: str
    total_pages: int = 0
    overall_score: float = 0.0
    page_results: List[PageAuditResult] = field(default_factory=list)
    category_scores: Dict[Category, float] = field(default_factory=dict)
    summary: Dict[str, Any] = field(default_factory=dict)
    orphan_pages: List[str] = field(default_factory=list)
