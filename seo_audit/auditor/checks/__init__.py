from .crawl_index import CrawlIndexChecks
from .tdk import TDKChecks
from .content_quality import ContentQualityChecks
from .technical_seo import TechnicalSEOChecks
from .performance import PerformanceChecks
from .mobile import MobileChecks
from .structured_data import StructuredDataChecks
from ..models import Category

_ALL_CHECK_CLASSES = [
    CrawlIndexChecks,
    TDKChecks,
    ContentQualityChecks,
    TechnicalSEOChecks,
    PerformanceChecks,
    MobileChecks,
    StructuredDataChecks,
]


def get_all_checks():
    checks = {}
    for cls in _ALL_CHECK_CLASSES:
        checks.update(cls.get_checks())
    return checks


def get_check_by_name(name: str):
    all_checks = get_all_checks()
    return all_checks.get(name)


def get_checks_by_category(category: Category):
    checks = {}
    for cls in _ALL_CHECK_CLASSES:
        if cls.category == category:
            checks.update(cls.get_checks())
    return checks


__all__ = [
    "CrawlIndexChecks",
    "TDKChecks",
    "ContentQualityChecks",
    "TechnicalSEOChecks",
    "PerformanceChecks",
    "MobileChecks",
    "StructuredDataChecks",
    "get_all_checks",
    "get_check_by_name",
    "get_checks_by_category",
]
