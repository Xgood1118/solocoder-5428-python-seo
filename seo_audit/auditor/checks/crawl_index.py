from .base import BaseCheck
from ..models import RuleResult, Severity, Weight, Category


def _r(rule_id, passed, message, details=None):
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
        return _r(
            "robots_txt_exists", has_robots,
            "网站已配置 robots.txt 文件" if has_robots else "网站未找到 robots.txt 文件",
        )

    @staticmethod
    def check_sitemap_exists(page, context=None):
        has_sitemap = context.get("has_sitemap", False) if context else False
        count = context.get("sitemap_count", 0) if context else 0
        return _r(
            "sitemap_exists", has_sitemap,
            f"网站有 {count} 个 sitemap 文件" if has_sitemap else "网站未配置 sitemap.xml",
            {"sitemap_count": count},
        )

    @staticmethod
    def check_404_status(page, context=None):
        if page.is_404:
            return _r("404_status", True, "页面返回正确的 404 状态码")
        tested = context.get("tested_404", False) if context else False
        ok = context.get("test_404_status") == 404 if context else False
        if tested:
            if ok:
                return _r("404_status", True, "随机路径返回 404 状态码")
            else:
                s = context.get("test_404_status", 0)
                return _r("404_status", False, f"不存在的页面返回 {s} 而非 404")
        return _r("404_status", True, "当前页面状态码正常")

    @staticmethod
    def check_5xx_errors(page, context=None):
        if page.is_5xx:
            return _r("5xx_errors", False, f"页面返回 {page.status_code} 服务器错误")
        count = context.get("5xx_count", 0) if context else 0
        if count > 0:
            return _r("5xx_errors", False, f"发现 {count} 个 5xx 错误页面", {"error_count": count})
        return _r("5xx_errors", True, "未发现 5xx 服务器错误")

    @staticmethod
    def check_redirect_chain(page, context=None):
        n = len(page.redirect_chain)
        return _r(
            "redirect_chain", n <= 3,
            f"重定向链 {n} 跳，{'超过建议的 3 跳' if n > 3 else '符合要求'}",
            {"redirect_count": n},
        )

    @staticmethod
    def check_orphan_pages(page, context=None):
        count = context.get("orphan_count", 0) if context else 0
        return _r(
            "orphan_pages", count == 0,
            f"发现 {count} 个孤立页面" if count > 0 else "未发现孤立页面",
            {"orphan_count": count},
        )

    @staticmethod
    def check_meta_robots_index(page, context=None):
        has_noindex = "noindex" in page.meta_robots.lower()
        return _r(
            "meta_robots_index", not has_noindex,
            "页面设置了 noindex，搜索引擎不会收录此页面" if has_noindex else "页面允许搜索引擎索引",
        )

    @staticmethod
    def check_robots_blocked(page, context=None):
        blocked = context.get("is_blocked_by_robots", False) if context else False
        return _r(
            "robots_blocked", not blocked,
            "页面被 robots.txt 屏蔽抓取" if blocked else "页面未被 robots.txt 屏蔽",
        )

    @staticmethod
    def check_http_status_ok(page, context=None):
        ok = 200 <= page.status_code < 300
        return _r(
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
        return _r(
            "page_indexable", indexable,
            "页面可被收录" if indexable else f"页面不可被收录：{', '.join(reasons)}",
            {"reasons": reasons},
        )

    @staticmethod
    def check_xml_sitemap_valid(page, context=None):
        valid = context.get("sitemap_valid", None)
        if valid is None:
            return _r("xml_sitemap_valid", True, "未检测 sitemap 有效性")
        return _r(
            "xml_sitemap_valid", valid,
            "sitemap.xml 格式正确" if valid else "sitemap.xml 格式错误",
        )

    @staticmethod
    def check_sitemap_in_robots(page, context=None):
        has = context.get("sitemap_in_robots", False)
        return _r(
            "sitemap_in_robots", has,
            "robots.txt 中已声明 sitemap 位置" if has else "robots.txt 中未声明 sitemap 位置",
        )

    @staticmethod
    def check_robots_sitemap_declared(page, context=None):
        declared = context.get("robots_sitemap_declared", False) if context else False
        return _r(
            "robots_sitemap_declared", declared,
            "robots.txt 中已声明 Sitemap 位置" if declared else "robots.txt 中未声明 Sitemap 位置",
        )

    @staticmethod
    def check_robots_crawl_delay(page, context=None):
        delay = context.get("crawl_delay", None) if context else None
        if delay is None:
            return _r("robots_crawl_delay", True, "未设置 Crawl-delay")
        reasonable = delay <= 10
        return _r(
            "robots_crawl_delay", reasonable,
            f"Crawl-delay 设置为 {delay} 秒，{'配置合理' if reasonable else '过大，可能影响抓取效率'}",
            {"crawl_delay": delay},
        )

    @staticmethod
    def check_robots_no_wildcard_block(page, context=None):
        has_wildcard_block = context.get("robots_wildcard_block", False) if context else False
        return _r(
            "robots_no_wildcard_block", not has_wildcard_block,
            "robots.txt 存在过度屏蔽全站的通配符规则" if has_wildcard_block else "robots.txt 无过度屏蔽的通配符规则",
        )

    @staticmethod
    def check_sitemap_format_valid(page, context=None):
        valid = context.get("sitemap_format_valid", None) if context else None
        if valid is None:
            return _r("sitemap_format_valid", True, "未检测 sitemap 格式")
        return _r(
            "sitemap_format_valid", valid,
            "sitemap XML 格式有效" if valid else "sitemap XML 格式存在错误",
        )

    @staticmethod
    def check_sitemap_url_count(page, context=None):
        count = context.get("sitemap_url_count", 0) if context else 0
        within_limit = count <= 50000
        return _r(
            "sitemap_url_count", within_limit,
            f"sitemap URL 数量为 {count}，{'未超过 5 万限制' if within_limit else '超过 5 万，需拆分'}",
            {"url_count": count},
        )

    @staticmethod
    def check_sitemap_gzip_support(page, context=None):
        has_gzip = context.get("sitemap_gzip", False) if context else False
        return _r(
            "sitemap_gzip_support", has_gzip,
            "已提供 sitemap.xml.gz 压缩版本" if has_gzip else "未提供 sitemap.xml.gz 压缩版本",
        )

    @staticmethod
    def check_sitemap_lastmod_present(page, context=None):
        ratio = context.get("sitemap_lastmod_ratio", 1.0) if context else 1.0
        all_have = ratio >= 0.99
        return _r(
            "sitemap_lastmod_present", all_have,
            f"sitemap 中 {int(ratio * 100)}% 的 URL 包含 lastmod 字段",
            {"lastmod_ratio": ratio},
        )

    @staticmethod
    def check_sitemap_index_exists(page, context=None):
        has_index = context.get("sitemap_index_exists", False) if context else False
        sitemap_count = context.get("sitemap_count", 0) if context else 0
        needs_index = sitemap_count > 1
        ok = (not needs_index) or has_index
        return _r(
            "sitemap_index_exists", ok,
            "已正确配置 sitemap index" if ok else "多 sitemap 场景建议配置 sitemap index",
            {"sitemap_count": sitemap_count, "has_index": has_index},
        )

    @staticmethod
    def check_http_403_forbidden(page, context=None):
        if page.status_code == 403:
            return _r("http_403_forbidden", False, "当前页面返回 403 Forbidden")
        count = context.get("http_403_count", 0) if context else 0
        return _r(
            "http_403_forbidden", count == 0,
            f"发现 {count} 个 403 Forbidden 页面" if count > 0 else "未发现异常 403 封禁页面",
            {"forbidden_count": count},
        )

    @staticmethod
    def check_http_410_gone(page, context=None):
        if page.status_code == 410:
            return _r("http_410_gone", True, "已删除页面正确返回 410 Gone 状态码")
        count_410 = context.get("http_410_count", 0) if context else 0
        count_404 = context.get("http_404_count", 0) if context else 0
        return _r(
            "http_410_gone", True,
            f"共 {count_410} 个 410 Gone，{count_404} 个 404 页面",
            {"gone_count": count_410, "notfound_count": count_404},
        )

    @staticmethod
    def check_soft_404_detected(page, context=None):
        count = context.get("soft_404_count", 0) if context else 0
        return _r(
            "soft_404_detected", count == 0,
            f"发现 {count} 个软 404 页面（200 OK 但内容为错误页）" if count > 0 else "未发现软 404 问题",
            {"soft_404_count": count},
        )

    @staticmethod
    def check_redirect_chain_too_long(page, context=None):
        n = len(page.redirect_chain)
        too_long = n > 3
        return _r(
            "redirect_chain_too_long", not too_long,
            f"重定向链共 {n} 跳，{'超过 3 跳建议缩短' if too_long else '未超过 3 跳'}",
            {"redirect_count": n},
        )

    @staticmethod
    def check_redirect_loop_detected(page, context=None):
        has_loop = context.get("redirect_loop", False) if context else False
        if not has_loop and page.redirect_chain:
            urls_in_chain = [r[0] for r in page.redirect_chain]
            has_loop = len(urls_in_chain) != len(set(urls_in_chain))
        return _r(
            "redirect_loop_detected", not has_loop,
            "检测到重定向循环" if has_loop else "未检测到重定向循环",
        )

    @staticmethod
    def check_redirect_302_misused(page, context=None):
        count = context.get("redirect_302_count", 0) if context else 0
        total = context.get("redirect_total_count", 0) if context else 0
        misused = False
        if total > 0:
            misused = (count / total) > 0.5
        return _r(
            "redirect_302_misused", not misused,
            f"302 临时跳转 {count} 次，占全部重定向的 {int(count / total * 100) if total else 0}%，{'疑似滥用' if misused else '使用情况正常'}",
            {"redirect_302_count": count, "redirect_total": total},
        )

    @staticmethod
    def check_redirect_mixed_usage(page, context=None):
        codes = [r[1] for r in page.redirect_chain] if page.redirect_chain else []
        has_301 = any(301 <= c < 302 for c in codes)
        has_302 = any(302 <= c < 303 or 307 <= c < 308 for c in codes)
        mixed = has_301 and has_302
        return _r(
            "redirect_mixed_usage", not mixed,
            "重定向链中同时混用了 301 和 302" if mixed else "重定向链中状态码使用一致",
        )

    @staticmethod
    def check_dns_resolvable(page, context=None):
        resolvable = context.get("dns_resolvable", True) if context else True
        return _r(
            "dns_resolvable", resolvable,
            "域名 DNS 可正常解析" if resolvable else "域名 DNS 解析失败",
        )

    @staticmethod
    def check_ssl_certificate_valid(page, context=None):
        valid = context.get("ssl_valid", True) if context else True
        days_left = context.get("ssl_days_left", None) if context else None
        msg = "SSL 证书有效"
        details = {}
        if days_left is not None:
            details["days_left"] = days_left
            if days_left < 30:
                valid = False
                msg = f"SSL 证书将在 {days_left} 天后过期，请及时更新"
            else:
                msg = f"SSL 证书有效，剩余 {days_left} 天"
        if not valid and days_left is None:
            msg = "SSL 证书无效或已过期"
        return _r("ssl_certificate_valid", valid, msg, details)

    @staticmethod
    def check_internal_dead_links(page, context=None):
        count = context.get("internal_dead_links", 0) if context else 0
        return _r(
            "internal_dead_links", count == 0,
            f"发现 {count} 个站内死链（指向 4xx/5xx）" if count > 0 else "未发现站内死链",
            {"dead_links_count": count},
        )

    @staticmethod
    def check_slow_response_pages(page, context=None):
        response_time = getattr(page, "response_time", None)
        if response_time is not None:
            slow = response_time > 3.0
            return _r(
                "slow_response_pages", not slow,
                f"页面响应时间 {response_time:.2f}s，{'超过 3s 建议优化' if slow else '正常'}",
                {"response_time": response_time},
            )
        count = context.get("slow_pages_count", 0) if context else 0
        return _r(
            "slow_response_pages", count == 0,
            f"发现 {count} 个响应时间超 3s 的页面" if count > 0 else "未发现响应超时页面",
            {"slow_pages_count": count},
        )

    @staticmethod
    def check_pagination_rel_next_prev(page, context=None):
        has_next = context.get("has_rel_next", False) if context else False
        has_prev = context.get("has_rel_prev", False) if context else False
        is_pagination = context.get("is_pagination", None) if context else None
        if is_pagination is False:
            return _r("pagination_rel_next_prev", True, "非分页页面，无需 rel=next/prev")
        ok = has_next or has_prev
        return _r(
            "pagination_rel_next_prev", ok,
            "分页页已配置 rel=next/prev 标签" if ok else "分页页缺少 rel=next/prev 标签",
            {"has_rel_next": has_next, "has_rel_prev": has_prev},
        )

    @staticmethod
    def check_meta_noindex_check(page, context=None):
        is_important = context.get("is_important_page", None) if context else None
        has_noindex = "noindex" in page.meta_robots.lower()
        if is_important is False:
            return _r("meta_noindex_check", True, "非重要页面，无需额外检查 noindex")
        return _r(
            "meta_noindex_check", not has_noindex,
            "重要页面被设置为 noindex，无法收录" if has_noindex else "重要页面未设置 noindex",
        )

    @staticmethod
    def check_nofollow_internal_abuse(page, context=None):
        total = context.get("internal_links_total", 0) if context else 0
        nofollow = context.get("internal_links_nofollow", 0) if context else 0
        abuse = False
        if total > 10:
            abuse = (nofollow / total) > 0.5
        ratio = (nofollow / total * 100) if total else 0
        return _r(
            "nofollow_internal_abuse", not abuse,
            f"内部链接共 {total} 条，其中 nofollow {nofollow} 条，占比 {int(ratio)}%，{'疑似滥用' if abuse else '比例正常'}",
            {"internal_total": total, "internal_nofollow": nofollow, "ratio": ratio},
        )

    @staticmethod
    def check_x_robots_tag_used(page, context=None):
        has_header = context.get("has_x_robots_tag", False) if context else False
        content = context.get("x_robots_content", "") if context else ""
        problematic = "noindex" in content.lower() or "none" in content.lower()
        if not has_header:
            return _r("x_robots_tag_used", True, "未使用 X-Robots-Tag 响应头")
        return _r(
            "x_robots_tag_used", not problematic,
            f"X-Robots-Tag: {content}，{'包含限制收录指令' if problematic else '配置正常'}",
            {"x_robots_content": content},
        )

    @staticmethod
    def check_connect_timeout_none(page, context=None):
        count = context.get("connect_timeout_count", 0) if context else 0
        return _r(
            "connect_timeout_none", count == 0,
            f"发现 {count} 个连接超时无法访问的页面" if count > 0 else "未发现连接超时页面",
            {"timeout_count": count},
        )

    @staticmethod
    def check_ssl_stapling_enabled(page, context=None):
        enabled = context.get("ssl_stapling_enabled", None) if context else None
        if enabled is None:
            return _r("ssl_stapling_enabled", True, "未检测 OCSP Stapling 状态")
        return _r(
            "ssl_stapling_enabled", enabled,
            "已启用 OCSP Stapling" if enabled else "未启用 OCSP Stapling，建议开启",
        )

    @staticmethod
    def check_http2_supported(page, context=None):
        supported = context.get("http2_supported", None) if context else None
        if supported is None:
            return _r("http2_supported", True, "未检测 HTTP/2 支持状态")
        return _r(
            "http2_supported", supported,
            "服务器已支持 HTTP/2 协议" if supported else "服务器未支持 HTTP/2 协议，建议升级",
        )

    @staticmethod
    def check_ipv6_reachable(page, context=None):
        reachable = context.get("ipv6_reachable", None) if context else None
        if reachable is None:
            return _r("ipv6_reachable", True, "未检测 IPv6 可访问性")
        return _r(
            "ipv6_reachable", reachable,
            "网站支持 IPv6 访问" if reachable else "网站未支持 IPv6 访问，建议配置",
        )

    @staticmethod
    def check_canonical_status_ok(page, context=None):
        canonical = getattr(page, "canonical", None)
        if not canonical:
            return _r("canonical_status_ok", True, "页面未设置 canonical，跳过检查")
        status = context.get("canonical_status", None) if context else None
        if status is None:
            return _r("canonical_status_ok", True, "未检测 canonical 目标页状态")
        ok = 200 <= status < 300
        return _r(
            "canonical_status_ok", ok,
            f"canonical 目标页返回 {status} 状态码，{'正常' if ok else '异常'}",
            {"canonical_url": canonical, "canonical_status": status},
        )

    @staticmethod
    def check_redirect_to_404(page, context=None):
        count = context.get("redirect_to_404_count", 0) if context else 0
        return _r(
            "redirect_to_404", count == 0,
            f"发现 {count} 个重定向最终指向 404 页面" if count > 0 else "未发现重定向指向 404 的情况",
            {"redirect_404_count": count},
        )

    @staticmethod
    def check_maintenance_503_none(page, context=None):
        if page.status_code == 503:
            return _r("maintenance_503_none", False, "当前页面返回 503 Service Unavailable")
        count = context.get("http_503_count", 0) if context else 0
        return _r(
            "maintenance_503_none", count == 0,
            f"发现 {count} 个 503 维护模式残留页面" if count > 0 else "未发现 503 维护模式残留",
            {"maintenance_503_count": count},
        )
