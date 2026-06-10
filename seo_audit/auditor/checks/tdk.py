from .base import BaseCheck
from ..models import RuleResult, Severity, Weight, Category


def _r(rule_id, passed, message, details=None):
    return RuleResult(
        rule_id=rule_id, rule_name="",
        category=Category.TDK,
        severity=Severity.INFO, weight=Weight.LOW,
        passed=passed, message=message, fix_advice="",
        details=details or {},
    )


class TDKChecks(BaseCheck):
    category = Category.TDK

    @staticmethod
    def check_title_exists(page, context=None):
        results = []
        has_dup = context.get("title_duplicate", False) if context else False
        if not page.title:
            results.append(_r("title_missing", False, "页面缺少 title 标签"))
            results.append(_r("title_duplicate", True, "无 title 标签，不涉及重复问题"))
        else:
            results.append(_r("title_missing", True, "页面有 title 标签"))
            if has_dup:
                results.append(_r("title_duplicate", False, "有其他页面使用了相同的 title"))
            else:
                results.append(_r("title_duplicate", True, "Title 唯一，无重复"))
        return results

    @staticmethod
    def check_title_length(page, context=None):
        if not page.title:
            return _r("title_length", False, "无 title 标签，无法检查长度")
        length = len(page.title)
        if length < 30:
            return _r("title_length", False, f"Title 只有 {length} 字符，偏短",
                     {"length": length, "min": 30, "max": 60})
        elif length > 60:
            return _r("title_length", False, f"Title 有 {length} 字符，超长可能被截断",
                     {"length": length, "min": 30, "max": 60})
        return _r("title_length", True, f"Title 长度 {length} 字符，符合要求",
                 {"length": length, "min": 30, "max": 60})

    @staticmethod
    def check_description_exists(page, context=None):
        results = []
        has_dup = context.get("description_duplicate", False) if context else False
        if not page.description:
            results.append(_r("description_missing", False, "页面缺少 meta description"))
            results.append(_r("description_duplicate", True, "无 description，不涉及重复问题"))
        else:
            results.append(_r("description_missing", True, "页面有 meta description"))
            if has_dup:
                results.append(_r("description_duplicate", False, "有其他页面使用了相同的 description"))
            else:
                results.append(_r("description_duplicate", True, "Description 唯一，无重复"))
        return results

    @staticmethod
    def check_description_length(page, context=None):
        if not page.description:
            return _r("description_length", False, "无 description，无法检查长度")
        length = len(page.description)
        if length < 70:
            return _r("description_length", False, f"Description 只有 {length} 字符，偏短",
                     {"length": length, "min": 70, "max": 160})
        elif length > 160:
            return _r("description_length", False, f"Description 有 {length} 字符，超长可能被截断",
                     {"length": length, "min": 70, "max": 160})
        return _r("description_length", True, f"Description 长度 {length} 字符，符合要求",
                 {"length": length, "min": 70, "max": 160})

    @staticmethod
    def check_keywords_exists(page, context=None):
        results = []
        has_dup = context.get("keywords_duplicate", False) if context else False
        if not page.keywords:
            results.append(_r("keywords_missing", False, "页面缺少 meta keywords"))
            results.append(_r("keywords_duplicate", True, "无 keywords，不涉及重复问题"))
        else:
            results.append(_r("keywords_missing", True, "页面有 meta keywords"))
            if has_dup:
                results.append(_r("keywords_duplicate", False, "有其他页面使用了相同的 keywords"))
            else:
                results.append(_r("keywords_duplicate", True, "Keywords 唯一，无重复"))
        return results

    @staticmethod
    def check_title_brand(page, context=None):
        if not page.title:
            return _r("title_brand", True, "无 title 标签")
        has_separator = any(s in page.title for s in [" - ", " | ", " _ "])
        return _r(
            "title_brand", has_separator,
            "Title 包含品牌分隔符" if has_separator else "Title 未包含品牌/站点名分隔符",
        )

    @staticmethod
    def check_title_keyword_first(page, context=None):
        if not page.title or not page.keywords:
            return _r("title_keyword_first", True, "条件不足")
        first_kw = page.keywords.split(",")[0].strip().lower()
        title_lower = page.title.lower()
        idx = title_lower.find(first_kw)
        first_half = idx >= 0 and idx < len(page.title) / 2
        return _r(
            "title_keyword_first", first_half,
            "主关键词出现在 title 前半部分" if first_half else "主关键词未出现在 title 前半部分",
        )
