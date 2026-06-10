from .base import BaseCheck
from ..models import RuleResult, Severity, Weight, Category


def _r(rule_id, passed, message, details=None):
    return RuleResult(
        rule_id=rule_id, rule_name="",
        category=Category.CONTENT_QUALITY,
        severity=Severity.INFO, weight=Weight.LOW,
        passed=passed, message=message, fix_advice="",
        details=details or {},
    )


class ContentQualityChecks(BaseCheck):
    category = Category.CONTENT_QUALITY

    @staticmethod
    def check_word_count(page, context=None):
        if page.word_count < 300:
            return _r("low_word_count", False, f"页面正文只有 {page.word_count} 字",
                     {"word_count": page.word_count, "min_required": 300})
        return _r("low_word_count", True, f"页面正文 {page.word_count} 字，内容充足",
                 {"word_count": page.word_count})

    @staticmethod
    def check_h1_exists(page, context=None):
        results = []
        if not page.h1_tags:
            results.append(_r("h1_missing", False, "页面缺少 H1 标签"))
            results.append(_r("multiple_h1", True, "无 H1 标签，不涉及多个 H1 问题"))
        elif len(page.h1_tags) > 1:
            results.append(_r("h1_missing", True, "页面有 H1 标签"))
            results.append(_r("multiple_h1", False, f"页面有 {len(page.h1_tags)} 个 H1 标签",
                             {"h1_count": len(page.h1_tags)}))
        else:
            results.append(_r("h1_missing", True, "页面有 H1 标签"))
            results.append(_r("multiple_h1", True, "页面有唯一的 H1 标签"))
        return results

    @staticmethod
    def check_keyword_density(page, context=None):
        if page.word_count < 50 or not page.text_content:
            return _r("keyword_density", True, "内容较少，关键词密度不适用")
        keywords = page.keywords.split(",") if page.keywords else []
        keywords = [k.strip().lower() for k in keywords if k.strip()]
        if not keywords:
            return _r("keyword_density", True, "未设置关键词，无法计算密度")
        text_lower = page.text_content.lower()
        total = sum(text_lower.count(kw) for kw in keywords[:3])
        density = (total / page.word_count) * 100 if page.word_count > 0 else 0
        if density < 2:
            return _r("keyword_density", False, f"主要关键词密度约 {density:.1f}%，偏低",
                     {"density": round(density, 2), "min": 2, "max": 8})
        elif density > 8:
            return _r("keyword_density", False, f"主要关键词密度约 {density:.1f}%，可能有堆砌嫌疑",
                     {"density": round(density, 2), "min": 2, "max": 8})
        return _r("keyword_density", True, f"主要关键词密度约 {density:.1f}%，在合理范围",
                 {"density": round(density, 2), "min": 2, "max": 8})

    @staticmethod
    def check_image_alt(page, context=None):
        total = len(page.images)
        if total == 0:
            return _r("image_alt", True, "页面没有图片",
                     {"total": 0, "missing": 0, "missing_rate": 0})
        missing = sum(1 for img in page.images if not img["has_alt"])
        rate = (missing / total) * 100
        if rate > 30:
            return _r("image_alt", False, f"图片 Alt 缺失率 {rate:.0f}%（{missing}/{total}）",
                     {"total": total, "missing": missing, "missing_rate": round(rate, 1)})
        return _r("image_alt", True, f"图片 Alt 缺失率 {rate:.0f}%（{missing}/{total}）",
                 {"total": total, "missing": missing, "missing_rate": round(rate, 1)})

    @staticmethod
    def check_internal_links(page, context=None):
        n = len(page.internal_links)
        if n == 0:
            return _r("internal_links", False, "页面没有内部链接", {"count": 0})
        return _r("internal_links", True, f"页面有 {n} 个内部链接", {"count": n})

    @staticmethod
    def check_external_links(page, context=None):
        n = len(page.external_links)
        if n == 0:
            return _r("external_links", True, "页面没有外部链接", {"count": 0})
        return _r("external_links", True, f"页面有 {n} 个外部链接", {"count": n})

    @staticmethod
    def check_h2_structure(page, context=None):
        if not page.h2_tags:
            return _r("h2_structure", False, "页面缺少 H2 副标题", {"h2_count": 0})
        return _r("h2_structure", True, f"页面有 {len(page.h2_tags)} 个 H2 副标题",
                 {"h2_count": len(page.h2_tags)})

    @staticmethod
    def check_content_unique(page, context=None):
        dup = context.get("content_duplicate", False)
        return _r(
            "content_unique", not dup,
            "内容为原创" if not dup else "检测到与其他页面内容重复",
        )

    @staticmethod
    def check_paragraph_structure(page, context=None):
        from bs4 import BeautifulSoup
        if not page.html:
            return _r("paragraph_structure", True, "无 HTML 内容")
        soup = BeautifulSoup(page.html, "html.parser")
        p_count = len(soup.find_all("p"))
        has_list = bool(soup.find_all(["ul", "ol"]))
        ok = p_count >= 3
        return _r(
            "paragraph_structure", ok,
            f"页面有 {p_count} 个段落，结构{'合理' if ok else '偏少'}",
            {"paragraph_count": p_count, "has_list": has_list},
        )

    @staticmethod
    def check_bold_keywords(page, context=None):
        if not page.keywords or not page.html:
            return _r("bold_keywords", True, "条件不足")
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(page.html, "html.parser")
        bold_texts = [b.get_text().lower() for b in soup.find_all(["b", "strong"])]
        first_kw = page.keywords.split(",")[0].strip().lower()
        has_kw_bold = any(first_kw in t for t in bold_texts)
        return _r(
            "bold_keywords", has_kw_bold,
            "有关键词加粗强调" if has_kw_bold else "关键词未使用加粗强调",
        )
