from .base import BaseCheck
from ..models import RuleResult, Severity, Weight, Category


def _r(rule_id, passed, message, details=None):
    return RuleResult(
        rule_id=rule_id, rule_name="",
        category=Category.STRUCTURED_DATA,
        severity=Severity.INFO, weight=Weight.LOW,
        passed=passed, message=message, fix_advice="",
        details=details or {},
    )


class StructuredDataChecks(BaseCheck):
    category = Category.STRUCTURED_DATA

    @staticmethod
    def check_json_ld(page, context=None):
        if not page.json_ld:
            return _r("json_ld_present", False, "页面没有 JSON-LD 结构化数据")
        types = []
        for item in page.json_ld:
            if isinstance(item, dict) and item.get("@type"):
                types.append(item["@type"])
        return _r("json_ld_present", True, f"页面有 {len(page.json_ld)} 个结构化数据块",
                 {"schema_types": types, "count": len(page.json_ld)})

    @staticmethod
    def check_schema_valid(page, context=None):
        if not page.json_ld:
            return _r("schema_valid", True, "无结构化数据，不适用")
        valid = 0
        invalid = 0
        for item in page.json_ld:
            if isinstance(item, dict) and "@type" in item:
                valid += 1
            else:
                invalid += 1
        if invalid > 0:
            return _r("schema_valid", False, f"有 {invalid} 个结构化数据块结构不完整",
                     {"valid": valid, "invalid": invalid})
        return _r("schema_valid", True, f"所有 {valid} 个结构化数据块结构完整",
                 {"valid": valid, "invalid": 0})

    @staticmethod
    def check_og_tags(page, context=None):
        required = ["og:title", "og:description", "og:image", "og:url"]
        missing = [t for t in required if t not in page.og_tags]
        if missing:
            return _r("og_tags", False, f"缺少 {len(missing)} 个必要 OG 标签：{', '.join(missing)}",
                     {"missing": missing, "present": list(page.og_tags.keys())})
        return _r("og_tags", True, "必要的 Open Graph 标签齐全",
                 {"present": list(page.og_tags.keys())})

    @staticmethod
    def check_twitter_card(page, context=None):
        if not page.twitter_tags:
            return _r("twitter_card", False, "页面没有 Twitter Card 标签")
        has_type = "twitter:card" in page.twitter_tags
        if not has_type:
            return _r("twitter_card", False, "缺少 twitter:card 类型定义")
        return _r("twitter_card", True, "Twitter Card 标签已配置",
                 {"present": list(page.twitter_tags.keys())})

    @staticmethod
    def check_breadcrumb_schema(page, context=None):
        has_schema = False
        for item in page.json_ld:
            if isinstance(item, dict) and item.get("@type") == "BreadcrumbList":
                has_schema = True
                break
        if page.has_breadcrumb and not has_schema:
            return _r("breadcrumb_schema", False, "有面包屑导航但缺少 Schema 标记")
        if has_schema:
            return _r("breadcrumb_schema", True, "面包屑导航已添加 Schema 标记")
        return _r("breadcrumb_schema", True, "无面包屑导航，不适用")

    @staticmethod
    def check_article_schema(page, context=None):
        has_article = False
        for item in page.json_ld:
            if isinstance(item, dict):
                t = item.get("@type", "")
                if isinstance(t, str) and "article" in t.lower():
                    has_article = True
                    break
        if page.word_count > 500 and not has_article:
            return _r("article_schema", False, "长内容页面建议添加 Article Schema")
        return _r("article_schema", True, "检测通过")

    @staticmethod
    def check_org_schema(page, context=None):
        has_org = False
        for item in page.json_ld:
            if isinstance(item, dict):
                t = item.get("@type", "")
                if isinstance(t, str) and ("organization" in t.lower() or "website" in t.lower()):
                    has_org = True
                    break
        return _r(
            "org_schema", has_org,
            "有站点级结构化数据" if has_org else "建议添加 Organization 或 Website 结构化数据",
        )

    @staticmethod
    def check_faq_schema(page, context=None):
        has_faq = False
        for item in page.json_ld:
            if isinstance(item, dict) and item.get("@type") == "FAQPage":
                has_faq = True
                break
        return _r(
            "faq_schema", has_faq,
            "有 FAQ 结构化数据" if has_faq else "如适用可添加 FAQ 结构化数据以获得富结果展示",
        )

    @staticmethod
    def check_rich_results_eligibility(page, context=None):
        types = []
        for item in page.json_ld:
            if isinstance(item, dict) and item.get("@type"):
                types.append(item["@type"])
        eligible = len(types) > 0
        return _r(
            "rich_results_eligibility", eligible,
            f"有 {len(types)} 种 Schema 类型可能支持富结果" if eligible else "无结构化数据，无法获得富结果展示",
            {"schema_types": types},
        )
