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

    @staticmethod
    def check_https_mixed_content_none(page, context=None):
        parsed = urlparse(page.final_url or page.url)
        if parsed.scheme != "https":
            return _r("https_mixed_content_none", True, "非 HTTPS 页面，不涉及混合内容")
        if not page.html:
            return _r("https_mixed_content_none", True, "无 HTML")
        patterns = [
            r'<img[^>]+src\s*=\s*["\']http://[^"\']+["\']',
            r'<script[^>]+src\s*=\s*["\']http://[^"\']+["\']',
            r'<link[^>]+href\s*=\s*["\']http://[^"\']+["\']',
            r'<iframe[^>]+src\s*=\s*["\']http://[^"\']+["\']',
            r'<video[^>]+src\s*=\s*["\']http://[^"\']+["\']',
            r'<audio[^>]+src\s*=\s*["\']http://[^"\']+["\']',
            r'<source[^>]+src\s*=\s*["\']http://[^"\']+["\']',
        ]
        found = []
        for pat in patterns:
            matches = re.findall(pat, page.html, re.I)
            found.extend(matches)
        unique = list(set(found))
        return _r(
            "https_mixed_content_none", len(unique) == 0,
            "无 HTTPS 混合内容" if len(unique) == 0 else f"发现 {len(unique)} 处 HTTP 资源引用",
            {"mixed_resources": unique[:20]},
        )

    @staticmethod
    def check_tls_modern_version(page, context=None):
        version = context.get("tls_version", None) if context else None
        if version is None:
            return _r("tls_modern_version", True, "缺少 TLS 版本信息，跳过检查")
        try:
            v = float(version)
            ok = v >= 1.2
            return _r(
                "tls_modern_version", ok,
                f"TLS 版本 {version} ≥ 1.2，符合要求" if ok else f"TLS 版本 {version} 过低，建议升级",
                {"tls_version": version},
            )
        except (TypeError, ValueError):
            ok = str(version) not in ("1.0", "1.1", "TLSv1", "TLSv1.1")
            return _r(
                "tls_modern_version", ok,
                f"TLS 版本为 {version}" if ok else f"TLS 版本 {version} 过旧，建议升级",
                {"tls_version": version},
            )

    @staticmethod
    def check_ssl_not_expiring_soon(page, context=None):
        days = context.get("ssl_days_remaining", None) if context else None
        if days is None:
            return _r("ssl_not_expiring_soon", True, "缺少 SSL 证书有效期信息，跳过检查")
        try:
            d = int(days)
            ok = d > 30
            return _r(
                "ssl_not_expiring_soon", ok,
                f"SSL 证书剩余 {d} 天，充足" if ok else f"SSL 证书仅剩 {d} 天，需尽快续费",
                {"days_remaining": d},
            )
        except (TypeError, ValueError):
            return _r(
                "ssl_not_expiring_soon", True,
                f"SSL 证书有效期信息：{days}",
                {"days_remaining": days},
            )

    @staticmethod
    def check_www_non_www_canonical(page, context=None):
        has = context.get("www_non_www_canonical", None) if context else None
        if has is True:
            return _r("www_non_www_canonical", True, "www 与非 www 已通过 301 统一")
        elif has is False:
            return _r("www_non_www_canonical", False, "www 与非 www 版本均可访问，未规范化")
        parsed = urlparse(page.final_url or page.url)
        host = parsed.netloc.lower()
        www_count = 1 if host.startswith("www.") else 0
        return _r(
            "www_non_www_canonical", True,
            f"当前访问版本为 {'www' if www_count else '非 www'}，请确认两版本已统一 301",
            {"current_host": host},
        )

    @staticmethod
    def check_trailing_slash_canonical(page, context=None):
        has = context.get("trailing_slash_canonical", None) if context else None
        if has is True:
            return _r("trailing_slash_canonical", True, "带/与不带/ 版本已通过 301 统一")
        elif has is False:
            return _r("trailing_slash_canonical", False, "带/和不带/ 两个版本均可访问，建议统一")
        parsed = urlparse(page.final_url or page.url)
        path = parsed.path
        if path in ("", "/"):
            return _r("trailing_slash_canonical", True, "根路径不涉及结尾斜杠规范化")
        has_slash = path.endswith("/")
        return _r(
            "trailing_slash_canonical", True,
            f"当前路径结尾{'带' if has_slash else '不带'}斜杠，请确认两版本已统一",
            {"current_path": path, "has_trailing_slash": has_slash},
        )

    @staticmethod
    def check_case_sensitive_url(page, context=None):
        has = context.get("case_sensitive_url", None) if context else None
        if has is True:
            return _r("case_sensitive_url", True, "URL 大小写已规范化")
        elif has is False:
            return _r("case_sensitive_url", False, "URL 大小写不敏感未统一，建议统一小写")
        parsed = urlparse(page.final_url or page.url)
        path = parsed.path
        has_upper = any(c.isupper() for c in path)
        return _r(
            "case_sensitive_url", not has_upper,
            "URL 路径均为小写" if not has_upper else "URL 路径包含大写字母，建议统一小写",
            {"current_path": path},
        )

    @staticmethod
    def check_amp_version_present(page, context=None):
        if not page.html:
            return _r("amp_version_present", True, "无 HTML")
        has_amphtml = bool(re.search(r'<link[^>]+rel\s*=\s*["\'][^"\']*amphtml[^"\']*["\']', page.html, re.I))
        has_amp_boilerplate = bool(re.search(r'<html[^>]+⚡', page.html, re.I)) or \
                              bool(re.search(r'<html[^>]+amp\b', page.html, re.I))
        found = has_amphtml or has_amp_boilerplate
        return _r(
            "amp_version_present", found,
            "已配置 AMP 加速移动页面" if found else "未配置 AMP 版本（新闻/资讯类站点建议考虑）",
            {"has_amphtml_link": has_amphtml, "is_amp_page": has_amp_boilerplate},
        )

    @staticmethod
    def check_pwa_manifest_present(page, context=None):
        if not page.html:
            return _r("pwa_manifest_present", True, "无 HTML")
        found = bool(re.search(r'<link[^>]+rel\s*=\s*["\'][^"\']*manifest[^"\']*["\']', page.html, re.I))
        return _r(
            "pwa_manifest_present", found,
            "已配置 PWA manifest.json" if found else "未配置 PWA 应用清单",
            {"has_manifest": found},
        )

    @staticmethod
    def check_rel_alternate_mobile(page, context=None):
        if not page.html:
            return _r("rel_alternate_mobile", True, "无 HTML")
        found = bool(re.search(
            r'<link[^>]+rel\s*=\s*["\'][^"\']*alternate[^"\']*["\'][^>]+media\s*=\s*["\'][^"\']*mobile',
            page.html, re.I,
        )) or bool(re.search(
            r'<link[^>]+media\s*=\s*["\'][^"\']*mobile[^"\']*["\'][^>]+rel\s*=\s*["\'][^"\']*alternate',
            page.html, re.I,
        ))
        return _r(
            "rel_alternate_mobile", found,
            "已配置移动版 rel=alternate" if found else "未配置移动版专用 rel=alternate（独立 m 站需配置）",
            {"has_mobile_alternate": found},
        )

    @staticmethod
    def check_pagination_canonical_correct(page, context=None):
        url = page.final_url or page.url
        parsed = urlparse(url)
        path_lower = parsed.path.lower()
        query_lower = parsed.query.lower()
        is_pagination = (
            re.search(r'/page/\d+', path_lower) is not None
            or re.search(r'(^|&)page=\d+', query_lower) is not None
            or re.search(r'(^|&)paged?=\d+', query_lower) is not None
            or re.search(r'/p/\d+', path_lower) is not None
        )
        if not is_pagination:
            return _r("pagination_canonical_correct", True, "非分页页，不适用本项检查")
        if not page.canonical:
            return _r("pagination_canonical_correct", False, "分页页缺少 canonical 标签")
        canonical_url = page.canonical.rstrip("/")
        current_url = (page.final_url or page.url).rstrip("/")
        if canonical_url == current_url:
            return _r(
                "pagination_canonical_correct", True,
                "分页页 canonical 指向自身，正确",
                {"canonical": page.canonical, "current": current_url},
            )
        parsed_canonical = urlparse(canonical_url)
        parsed_current = urlparse(current_url)
        if parsed_canonical.netloc != parsed_current.netloc:
            return _r(
                "pagination_canonical_correct", False,
                "分页页 canonical 指向其他域名，可能错误",
                {"canonical": page.canonical},
            )
        return _r(
            "pagination_canonical_correct", True,
            f"分页页 canonical 指向：{page.canonical}（如为 all-in-one 视图则正确）",
            {"canonical": page.canonical, "current": current_url},
        )

    @staticmethod
    def check_pagination_noindex_first_only(page, context=None):
        if not page.html:
            return _r("pagination_noindex_first_only", True, "无 HTML")
        url = page.final_url or page.url
        parsed = urlparse(url)
        path_lower = parsed.path.lower()
        query_lower = parsed.query.lower()
        page_num = None
        m = re.search(r'/page/(\d+)', path_lower)
        if m:
            page_num = int(m.group(1))
        else:
            m = re.search(r'(?:^|&)page=(\d+)', query_lower)
            if m:
                page_num = int(m.group(1))
        is_first_page = (page_num is None) or (page_num <= 1)
        has_noindex = bool(re.search(
            r'<meta[^>]+name\s*=\s*["\']robots["\'][^>]+content\s*=\s*["\'][^"\']*noindex',
            page.html, re.I,
        )) or bool(re.search(
            r'<meta[^>]+content\s*=\s*["\'][^"\']*noindex[^"\']*["\'][^>]+name\s*=\s*["\']robots',
            page.html, re.I,
        ))
        x_robots = page.headers.get("X-Robots-Tag", "") if page.headers else ""
        if "noindex" in x_robots.lower():
            has_noindex = True
        if is_first_page and has_noindex:
            return _r(
                "pagination_noindex_first_only", False,
                "列表第一页被设置了 noindex，可能损失流量",
                {"is_first_page": True, "has_noindex": True},
            )
        return _r(
            "pagination_noindex_first_only", True,
            "分页第一页未被误 noindex" if is_first_page else "非列表第一页，不适用本项",
            {"is_first_page": is_first_page, "has_noindex": has_noindex},
        )

    @staticmethod
    def check_hreflang_self_referential(page, context=None):
        if not page.hreflang:
            return _r("hreflang_self_referential", True, "无 hreflang 标签，跳过自引用检查")
        current_url = (page.final_url or page.url).rstrip("/")
        found_self = False
        for h in page.hreflang:
            href = (h.get("href", "") or "").rstrip("/")
            if href == current_url:
                found_self = True
                break
        return _r(
            "hreflang_self_referential", found_self,
            "hreflang 包含自引用（x→x），正确" if found_self else "hreflang 缺少当前页的自引用，可能被整体忽略",
            {"hreflang_count": len(page.hreflang)},
        )

    @staticmethod
    def check_hreflang_return_tags(page, context=None):
        if not page.hreflang:
            return _r("hreflang_return_tags", True, "无 hreflang 标签，跳过返回标签检查")
        return_tags_ok = context.get("hreflang_return_tags_ok", None) if context else None
        if return_tags_ok is False:
            return _r(
                "hreflang_return_tags", False,
                "检测到 hreflang 存在单向引用，缺少对应返回标签",
                {"hreflang_count": len(page.hreflang)},
            )
        langs = [h.get("hreflang", "") for h in page.hreflang if h.get("hreflang", "")]
        unique_langs = list(set([l for l in langs if l]))
        return _r(
            "hreflang_return_tags", True,
            f"当前页声明 {len(unique_langs)} 种语言/区域，请确保目标页存在对应返回标签",
            {"declared_languages": unique_langs[:20]},
        )

    @staticmethod
    def check_hreflang_x_default(page, context=None):
        if not page.hreflang:
            return _r("hreflang_x_default", True, "无 hreflang 标签，不适用 x-default 检查")
        has_x_default = any(
            (h.get("hreflang", "") or "").lower() == "x-default"
            for h in page.hreflang
        )
        return _r(
            "hreflang_x_default", has_x_default,
            "已配置 hreflang x-default 回退版本" if has_x_default else "建议配置 hreflang x-default 作为默认回退",
            {"has_x_default": has_x_default, "hreflang_count": len(page.hreflang)},
        )

    @staticmethod
    def check_soft_404_custom_page(page, context=None):
        if not page.is_404:
            return _r("soft_404_custom_page", True, "非 404 页，跳过本项检查")
        status_ok = page.status_code == 404
        text_len = len(page.text_content.strip()) if page.text_content else 0
        has_content = text_len > 100
        has_nav_links = len(page.internal_links) > 0
        ok = status_ok and (has_content or has_nav_links)
        details = {
            "status_code": page.status_code,
            "content_length": text_len,
            "has_internal_links": has_nav_links,
        }
        if not status_ok:
            return _r(
                "soft_404_custom_page", False,
                f"404 页返回状态码 {page.status_code}，应为 404",
                details,
            )
        if not has_content and not has_nav_links:
            return _r(
                "soft_404_custom_page", False,
                "404 页内容过于空泛，建议添加搜索框和导航引导用户",
                details,
            )
        return _r(
            "soft_404_custom_page", ok,
            "404 页为真 404 且具备引导内容",
            details,
        )

    @staticmethod
    def check_http2_https_support(page, context=None):
        supported = context.get("http2_supported", None) if context else None
        if supported is True:
            return _r("http2_https_support", True, "HTTPS 已启用 HTTP/2")
        elif supported is False:
            return _r("http2_https_support", False, "HTTPS 未启用 HTTP/2，建议开启")
        parsed = urlparse(page.final_url or page.url)
        if parsed.scheme != "https":
            return _r("http2_https_support", True, "非 HTTPS 页面，跳过 HTTP/2 检查")
        return _r(
            "http2_https_support", True,
            "当前页面可能走 HTTP/2，请服务器确认已启用",
        )

    @staticmethod
    def check_ipv6_dns_record(page, context=None):
        has_ipv6 = context.get("has_ipv6_aaaa", None) if context else None
        if has_ipv6 is True:
            return _r("ipv6_dns_record", True, "已配置 IPv6 AAAA 记录")
        elif has_ipv6 is False:
            return _r("ipv6_dns_record", False, "未检测到 IPv6 AAAA 记录，建议配置")
        parsed = urlparse(page.final_url or page.url)
        return _r(
            "ipv6_dns_record", True,
            f"域名 {parsed.netloc}，建议确认已配置 IPv6 AAAA 记录",
            {"domain": parsed.netloc},
        )

    @staticmethod
    def check_ga_tracking_present(page, context=None):
        if not page.html:
            return _r("ga_tracking_present", True, "无 HTML")
        patterns = [
            r'googletagmanager\.com/gtag/js',
            r'google-analytics\.com/(analytics|ga|gtag)\.js',
            r'gtag\s*\(',
            r'ga\s*\(\s*["\']create["\']',
            r'_gaq\.push',
            r'GoogleAnalyticsObject',
        ]
        found = False
        matched_pat = None
        for pat in patterns:
            if re.search(pat, page.html, re.I):
                found = True
                matched_pat = pat
                break
        return _r(
            "ga_tracking_present", found,
            "已检测到 Google Analytics / GA4 代码" if found else "未检测到 GA 统计代码，建议安装",
            {"matched_pattern": matched_pat},
        )

    @staticmethod
    def check_gsc_verification(page, context=None):
        if not page.html:
            return _r("gsc_verification", True, "无 HTML")
        found = bool(re.search(
            r'<meta[^>]+name\s*=\s*["\']google-site-verification["\']',
            page.html, re.I,
        )) or bool(re.search(
            r'<meta[^>]+content\s*=\s*["\'][^"\']*["\'][^>]+name\s*=\s*["\']google-site-verification',
            page.html, re.I,
        ))
        return _r(
            "gsc_verification", found,
            "检测到 Google Search Console HTML 验证标记" if found else "未检测到 GSC HTML 验证标记（也可使用 DNS 验证）",
            {"has_gsc_meta": found},
        )

    @staticmethod
    def check_gtm_installed(page, context=None):
        if not page.html:
            return _r("gtm_installed", True, "无 HTML")
        found = bool(re.search(r'googletagmanager\.com/gtm\.js', page.html, re.I)) or \
                bool(re.search(r'<!--\s*Google\s*Tag\s*Manager', page.html, re.I)) or \
                bool(re.search(r'dataLayer\s*=', page.html, re.I))
        return _r(
            "gtm_installed", found,
            "已部署 Google Tag Manager 容器" if found else "未检测到 GTM 部署",
            {"has_gtm": found},
        )

    @staticmethod
    def check_privacy_policy_link(page, context=None):
        if not page.html:
            return _r("privacy_policy_link", True, "无 HTML")
        links = re.findall(r'<a[^>]+href\s*=\s*["\']([^"\']+)["\'][^>]*>(.*?)</a>', page.html, re.I | re.S)
        found = False
        matched_link = None
        keywords = [
            "隐私", "privacy", "privacy-policy", "privacy_policy",
            "隐私政策", "隐私声明", "privacypolicy",
        ]
        for href, text in links:
            combined = f"{href.lower()} {text.lower().strip()}"
            for kw in keywords:
                if kw.lower() in combined:
                    found = True
                    matched_link = href
                    break
            if found:
                break
        return _r(
            "privacy_policy_link", found,
            "检测到隐私政策链接" if found else "未检测到隐私政策链接，建议页脚放置",
            {"matched_link": matched_link},
        )

    @staticmethod
    def check_cookie_consent_banner(page, context=None):
        if not page.html:
            return _r("cookie_consent_banner", True, "无 HTML")
        patterns = [
            r'cookie\s*(consent|notice|banner|policy|bar)',
            r'cookieconsent',
            r'cookie-law',
            r'gdpr',
            r'ccpa',
            r'同意.*cookie',
            r'cookie.*同意',
            r'接受.*cookie',
            r'cookie.*接受',
        ]
        found = False
        for pat in patterns:
            if re.search(pat, page.html, re.I):
                found = True
                break
        return _r(
            "cookie_consent_banner", found,
            "检测到 Cookie 同意/提示相关组件" if found else "未检测到 Cookie 同意弹窗（面向欧盟/加州用户需注意合规）",
            {"has_consent": found},
        )

    @staticmethod
    def check_sitemap_in_robots_duplicate(page, context=None):
        sitemap_in_robots = context.get("sitemap_in_robots", None) if context else None
        sitemap_in_gsc = context.get("sitemap_in_gsc", None) if context else None
        if sitemap_in_robots is True and sitemap_in_gsc is True:
            return _r(
                "sitemap_in_robots_duplicate", True,
                "sitemap 已在 robots.txt 和 GSC 两处提交",
            )
        if sitemap_in_robots is False or sitemap_in_gsc is False:
            details = {
                "sitemap_in_robots": sitemap_in_robots,
                "sitemap_in_gsc": sitemap_in_gsc,
            }
            if sitemap_in_robots is False and sitemap_in_gsc is False:
                return _r(
                    "sitemap_in_robots_duplicate", False,
                    "robots.txt 中未声明 sitemap，且未在 GSC 中手动提交",
                    details,
                )
            return _r(
                "sitemap_in_robots_duplicate", False,
                "建议在 robots.txt 与 GSC 两处同时提交 sitemap 以获得更好效果",
                details,
            )
        return _r(
            "sitemap_in_robots_duplicate", True,
            "请确认 sitemap 已在 robots.txt 和 GSC 两处同时提交",
        )

    @staticmethod
    def check_404_200_status_conflict(page, context=None):
        if not page.is_404:
            return _r("404_200_status_conflict", True, "非 404 页，跳过本项检查")
        conflict = page.status_code == 200
        if conflict:
            return _r(
                "404_200_status_conflict", False,
                f"页面标记为 404 但返回状态码 200（软 404），请立即修复",
                {"status_code": page.status_code},
            )
        return _r(
            "404_200_status_conflict", True,
            f"404 页正确返回状态码 {page.status_code}",
            {"status_code": page.status_code},
        )

    @staticmethod
    def check_cdn_enabled(page, context=None):
        cdn_detected = context.get("cdn_detected", None) if context else None
        if cdn_detected is True:
            return _r("cdn_enabled", True, "检测到网站已接入 CDN 加速")
        elif cdn_detected is False:
            return _r("cdn_enabled", False, "未检测到 CDN，建议接入 CDN 加速静态资源")
        if not page.headers:
            return _r("cdn_enabled", True, "无响应头，跳过 CDN 检测")
        cdn_indicators = [
            ("server", ["cloudflare", "cloudfront", "akamai", "fastly", "gcore", "cdn"]),
            ("x-cache", [""]),
            ("via", ["cloudflare", "cloudfront", "akamai", "fastly", "gcore", "cdn"]),
            ("x-cdn", [""]),
            ("cf-cache-status", [""]),
            ("x-amz-cf-id", [""]),
            ("x-sucuri-id", [""]),
            ("x-edge-location", [""]),
        ]
        found = False
        matched_header = None
        for hdr, keywords in cdn_indicators:
            val = ""
            for k in page.headers:
                if k.lower() == hdr.lower():
                    val = str(page.headers[k]).lower()
                    break
            if not val:
                continue
            if not keywords:
                found = True
                matched_header = hdr
                break
            for kw in keywords:
                if kw in val:
                    found = True
                    matched_header = hdr
                    break
            if found:
                break
        return _r(
            "cdn_enabled", found,
            "响应头显示已接入 CDN" if found else "未从响应头检测到 CDN 标识，建议接入 CDN",
            {"matched_header": matched_header},
        )

    @staticmethod
    def check_dns_prefetch_configured(page, context=None):
        if not page.html:
            return _r("dns_prefetch_configured", True, "无 HTML")
        matches = re.findall(
            r'<link[^>]+rel\s*=\s*["\'][^"\']*dns-prefetch[^"\']*["\'][^>]*/?>',
            page.html, re.I,
        )
        count = len(matches)
        return _r(
            "dns_prefetch_configured", count > 0,
            f"已配置 {count} 个 dns-prefetch" if count > 0 else "未配置 dns-prefetch，建议对常用第三方域名预解析",
            {"dns_prefetch_count": count},
        )

    @staticmethod
    def check_preconnect_3rd_party(page, context=None):
        if not page.html:
            return _r("preconnect_3rd_party", True, "无 HTML")
        matches = re.findall(
            r'<link[^>]+rel\s*=\s*["\'][^"\']*preconnect[^"\']*["\'][^>]*/?>',
            page.html, re.I,
        )
        count = len(matches)
        return _r(
            "preconnect_3rd_party", count > 0,
            f"已配置 {count} 个 preconnect" if count > 0 else "未配置 preconnect，建议对 GTM/字体等关键第三方域名建立预连接",
            {"preconnect_count": count},
        )

    @staticmethod
    def check_cors_headers_correct(page, context=None):
        if not page.headers:
            return _r("cors_headers_correct", True, "无响应头，跳过 CORS 检查")
        acao = ""
        for k in page.headers:
            if k.lower() == "access-control-allow-origin":
                acao = page.headers[k]
                break
        if not acao:
            return _r("cors_headers_correct", True, "未设置 CORS Access-Control-Allow-Origin，无风险")
        is_wildcard = acao.strip() == "*"
        return _r(
            "cors_headers_correct", not is_wildcard,
            f"CORS Access-Control-Allow-Origin 已限制为 {acao}" if not is_wildcard
            else "CORS Access-Control-Allow-Origin 设为 *，如非必要请收窄范围",
            {"access_control_allow_origin": acao},
        )

    @staticmethod
    def check_security_headers_present(page, context=None):
        if not page.headers:
            return _r("security_headers_present", True, "无响应头，跳过安全头检查")
        headers_lower = {k.lower(): v for k, v in page.headers.items()}
        expected = {
            "content-security-policy": False,
            "referrer-policy": False,
            "permissions-policy": False,
            "x-content-type-options": False,
        }
        for hdr in expected:
            expected[hdr] = hdr in headers_lower
        present = [h for h, ok in expected.items() if ok]
        missing = [h for h, ok in expected.items() if not ok]
        all_present = len(missing) == 0
        return _r(
            "security_headers_present", all_present,
            f"已配置完整安全响应头（{', '.join(present)}）" if all_present
            else f"建议补充安全响应头：{', '.join(missing)}",
            {"present": present, "missing": missing},
        )
