from .base import BaseCheck
from ..models import RuleResult, Severity, Weight, Category


def _make_result(rule_id, passed, message, details=None):
    return RuleResult(
        rule_id=rule_id, rule_name="",
        category=Category.CRAWL_INDEX,
        severity=Severity.INFO, weight=Weight.LOW,
        passed=passed, message=message, fix_advice="",
        details=details or {},
    )


class CrawlIndexChecks(BaseCheck):
    category = Category.CRAWL_INDEX

    @staticmethod
    def check_robots_txt_exists(page, context=None):
        has_robots = context.get("has_robots_txt", False) if context else False
        return _make_result(
            "robots_txt_exists", has_robots,
            "网站已配置 robots.txt 文件" if has_robots else "网站未找到 robots.txt 文件",
        )

    @staticmethod
    def check_sitemap_exists(page, context=None):
        has_sitemap = context.get("has_sitemap", False) if context else False
        count = context.get("sitemap_count", 0) if context else 0
        return _make_result(
            "sitemap_exists", has_sitemap,
            f"网站有 {count} 个 sitemap 文件" if has_sitemap else "网站未配置 sitemap.xml",
            {"sitemap_count": count},
        )

    @staticmethod
    def check_404_status(page, context=None):
        if page.is_404:
            return _make_result("404_status", True, "页面返回正确的 404 状态码")
        tested = context.get("tested_404", False) if context else False
        ok = context.get("test_404_status") == 404 if context else False
        if tested:
            if ok:
                return _make_result("404_status", True, "随机路径返回 404 状态码")
            else:
                s = context.get("test_404_status", 0)
                return _make_result("404_status", False, f"不存在的页面返回 {s} 而非 404")
        return _make_result("404_status", True, "当前页面状态码正常")

    @staticmethod
    def check_5xx_errors(page, context=None):
        if page.is_5xx:
            return _make_result("5xx_errors", False, f"页面返回 {page.status_code} 服务器错误")
        count = context.get("5xx_count", 0) if context else 0
        if count > 0:
            return _make_result("5xx_errors", False, f"发现 {count} 个 5xx 错误页面", {"error_count": count})
        return _make_result("5xx_errors", True, "未发现 5xx 服务器错误")

    @staticmethod
    def check_redirect_chain(page, context=None):
        n = len(page.redirect_chain)
        return _make_result(
            "redirect_chain", n <= 3,
            f"重定向链 {n} 跳，{'超过建议的 3 跳' if n > 3 else '符合要求'}",
            {"redirect_count": n},
        )

    @staticmethod
    def check_orphan_pages(page, context=None):
        count = context.get("orphan_count", 0) if context else 0
        return _make_result(
            "orphan_pages", count == 0,
            f"发现 {count} 个孤立页面" if count > 0 else "未发现孤立页面",
            {"orphan_count": count},
        )

    @staticmethod
    def check_meta_robots_index(page, context=None):
        has_noindex = "noindex" in page.meta_robots.lower()
        return _make_result(
            "meta_robots_index", not has_noindex,
            "页面设置了 noindex，搜索引擎不会收录此页面" if has_noindex else "页面允许搜索引擎索引",
        )

    @staticmethod
    def check_robots_blocked(page, context=None):
        blocked = context.get("is_blocked_by_robots", False) if context else False
        return _make_result(
            "robots_blocked", not blocked,
            "页面被 robots.txt 屏蔽抓取" if blocked else "页面未被 robots.txt 屏蔽",
        )

    @staticmethod
    def check_http_status_ok(page, context=None):
        ok = 200 <= page.status_code < 300
        return _make_result(
            "http_status_ok", ok,
            f"页面返回 {page.status_code} 状态码",
            {"status_code": page.status_code},
        )

    @staticmethod
    def check_indexable(page, context=None):
        indexable = True
        reasons = []
        if "noindex" in page.meta_robots.lower():
            indexable = False
            reasons.append("meta noindex")
        if page.status_code >= 400:
            indexable = False
            reasons.append(f"HTTP {page.status_code}")
        blocked = context.get("is_blocked_by_robots", False) if context else False
        if blocked:
            indexable = False
            reasons.append("robots.txt 屏蔽")
        return _make_result(
            "page_indexable", indexable,
            "页面可被收录" if indexable else f"页面不可被收录：{', '.join(reasons)}",
            {"reasons": reasons},
        )

    @staticmethod
    def check_xml_sitemap_valid(page, context=None):
        valid = context.get("sitemap_valid", None)
        if valid is None:
            return _make_result("xml_sitemap_valid", True, "未检测 sitemap 有效性")
        return _make_result(
            "xml_sitemap_valid", valid,
            "sitemap.xml 格式正确" if valid else "sitemap.xml 格式错误",
        )

    @staticmethod
    def check_sitemap_in_robots(page, context=None):
        has = context.get("sitemap_in_robots", False)
        return _make_result(
            "sitemap_in_robots", has,
            "robots.txt 中已声明 sitemap 位置" if has else "robots.txt 中未声明 sitemap 位置",
        )
