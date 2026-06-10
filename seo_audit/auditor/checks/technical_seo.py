import re
from urllib.parse import urlparse

from .base import BaseCheck
from ..models import RuleResult, Severity, Weight, Category


def _r(rule_id, passed, message, details=None):
    return RuleResult(
        rule_id=rule_id, rule_name="",
        category=Category.TECHNICAL_SEO,
        severity=Severity.INFO, weight=Weight.LOW,
        passed=passed, message=message, fix_advice="",
        details=details or {},
    )


class TechnicalSEOChecks(BaseCheck):
    category = Category.TECHNICAL_SEO

    @staticmethod
    def check_https(page, context=None):
        parsed = urlparse(page.final_url or page.url)
        is_https = parsed.scheme == "https"
        return _r("https_enabled", is_https,
                 "网站已启用 HTTPS" if is_https else "网站未使用 HTTPS 加密")

    @staticmethod
    def check_hsts(page, context=None):
        hsts = page.headers.get("Strict-Transport-Security", "") if page.headers else ""
        return _r("hsts_enabled", bool(hsts),
                 "网站已配置 HSTS 安全头" if hsts else "网站未配置 HSTS 响应头",
                 {"hsts_value": hsts} if hsts else {})

    @staticmethod
    def check_http_to_https_redirect(page, context=None):
        has = context.get("http_to_https_redirect", None) if context else None
        if has is True:
            return _r("http_https_redirect", True, "HTTP 请求会 301 跳转到 HTTPS")
        elif has is False:
            return _r("http_https_redirect", False, "HTTP 请求未跳转到 HTTPS")
        parsed = urlparse(page.final_url or page.url)
        if parsed.scheme == "https":
            return _r("http_https_redirect", True, "当前页面通过 HTTPS 访问")
        return _r("http_https_redirect", False, "页面未使用 HTTPS")

    @staticmethod
    def check_canonical(page, context=None):
        results = []
        chain = context.get("canonical_chain", []) if context else []
        has_loop = context.get("canonical_loop", False) if context else False
        if not page.canonical:
            results.append(_r("canonical_tag", False, "页面缺少 canonical 标签"))
            results.append(_r("canonical_loop", True, "无 canonical 标签，不涉及循环问题"))
        else:
            if has_loop:
                results.append(_r("canonical_tag", False, "Canonical 指向形成循环", {"chain": chain}))
                results.append(_r("canonical_loop", False, "Canonical 指向形成循环", {"chain": chain}))
            else:
                if page.canonical != page.final_url:
                    cd = urlparse(page.canonical).netloc if page.canonical else ""
                    pd = urlparse(page.final_url).netloc if page.final_url else ""
                    if cd and pd and cd != pd:
                        results.append(_r("canonical_tag", False, f"Canonical 指向其他域名：{page.canonical}",
                                         {"canonical": page.canonical}))
                    else:
                        results.append(_r("canonical_tag", True, f"Canonical 指向：{page.canonical}",
                                         {"canonical": page.canonical}))
                else:
                    results.append(_r("canonical_tag", True, f"Canonical 指向：{page.canonical}",
                                     {"canonical": page.canonical}))
                results.append(_r("canonical_loop", True, "未检测到 canonical 循环"))
        return results

    @staticmethod
    def check_hreflang(page, context=None):
        if page.hreflang:
            return _r("hreflang_tags", True, f"页面有 {len(page.hreflang)} 个 hreflang 标签",
                     {"hreflang_count": len(page.hreflang)})
        return _r("hreflang_tags", True, "页面没有 hreflang 标签（单语言站点适用）")

    @staticmethod
    def check_breadcrumb(page, context=None):
        return _r("breadcrumb", page.has_breadcrumb,
                 "页面有面包屑导航" if page.has_breadcrumb else "页面缺少面包屑导航")

    @staticmethod
    def check_url_static(page, context=None):
        url = page.final_url or page.url
        parsed = urlparse(url)
        if parsed.query:
            n = len([p for p in parsed.query.split("&") if p])
            if n > 3:
                return _r("url_static", False, f"URL 包含 {n} 个参数，建议静态化",
                         {"param_count": n})
            return _r("url_static", True, f"URL 包含 {n} 个参数，较少可接受",
                     {"param_count": n})
        return _r("url_static", True, "URL 为静态化形式")

    @staticmethod
    def check_x_frame_options(page, context=None):
        xfo = page.headers.get("X-Frame-Options", "") if page.headers else ""
        return _r("x_frame_options", bool(xfo),
                 "网站配置了 X-Frame-Options 安全头" if xfo else "网站未配置 X-Frame-Options 头")

    @staticmethod
    def check_gzip_compression(page, context=None):
        ce = page.headers.get("Content-Encoding", "") if page.headers else ""
        ok = "gzip" in ce.lower() or "br" in ce.lower()
        return _r("gzip_compression", ok,
                 "网站启用了内容压缩" if ok else "网站未启用 Gzip/Brotli 压缩")

    @staticmethod
    def check_caching_headers(page, context=None):
        cc = page.headers.get("Cache-Control", "") if page.headers else ""
        etag = page.headers.get("ETag", "") if page.headers else ""
        lm = page.headers.get("Last-Modified", "") if page.headers else ""
        has_cache = bool(cc or etag or lm)
        return _r(
            "caching_headers", has_cache,
            "网站配置了缓存头" if has_cache else "网站缺少缓存相关响应头",
        )

    @staticmethod
    def check_meta_viewport(page, context=None):
        return _r(
            "meta_viewport", bool(page.viewport),
            "有 viewport meta 标签" if page.viewport else "缺少 viewport meta 标签",
        )

    @staticmethod
    def check_doctype(page, context=None):
        if not page.html:
            return _r("doctype", True, "无 HTML")
        has_doctype = bool(re.search(r"<!DOCTYPE\s+html", page.html, re.I))
        return _r("doctype", has_doctype,
                 "有正确的 HTML5 DOCTYPE 声明" if has_doctype else "缺少 DOCTYPE 声明")

    @staticmethod
    def check_lang_attr(page, context=None):
        if not page.html:
            return _r("lang_attr", True, "无 HTML")
        has_lang = bool(re.search(r'<html[^>]*\blang\s*=', page.html, re.I))
        return _r("lang_attr", has_lang,
                 "html 标签有 lang 属性" if has_lang else "html 标签缺少 lang 属性")
