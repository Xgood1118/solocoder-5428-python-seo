import re

from .base import BaseCheck
from ..models import RuleResult, Severity, Weight, Category


def _r(rule_id, passed, message, details=None):
    return RuleResult(
        rule_id=rule_id, rule_name="",
        category=Category.MOBILE,
        severity=Severity.INFO, weight=Weight.LOW,
        passed=passed, message=message, fix_advice="",
        details=details or {},
    )


class MobileChecks(BaseCheck):
    category = Category.MOBILE

    @staticmethod
    def check_viewport(page, context=None):
        if page.viewport:
            vl = page.viewport.lower()
            ok = "width=device-width" in vl
            return _r("viewport_meta", ok,
                     "页面设置了正确的 viewport meta 标签" if ok else "Viewport 未设置 width=device-width",
                     {"viewport": page.viewport})
        return _r("viewport_meta", False, "页面缺少 viewport meta 标签")

    @staticmethod
    def check_responsive_css(page, context=None):
        html = page.html or ""
        mq = len(re.findall(r"@media\s*(?:only\s+)?screen", html, re.I))
        mq += len(re.findall(r"@media\s*\(", html))
        has_rc = bool(re.search(r"col-(?:xs|sm|md|lg|xl)-", html, re.I))
        has_fw = "flex-wrap" in html.lower()
        has_grid = "grid-template-columns" in html.lower() or "display:grid" in html.lower()
        ok = mq > 0 or has_rc or has_fw or has_grid
        return _r(
            "responsive_css", ok,
            "页面使用了响应式设计" if ok else "未检测到响应式设计特征",
            {"media_queries": mq, "responsive_classes": has_rc},
        )

    @staticmethod
    def check_font_size(page, context=None):
        html = page.html or ""
        very_small = 0
        for m in re.finditer(r"font-size\s*:\s*(\d+(?:\.\d+)?)\s*px", html, re.I):
            if float(m.group(1)) < 12:
                very_small += 1
        if very_small > 0:
            return _r("font_size", False, f"检测到 {very_small} 处字体小于 12px",
                     {"small_font_count": very_small})
        return _r("font_size", True, "未检测到过小的字体（基于内联样式检测）",
                 {"small_font_count": 0})

    @staticmethod
    def check_tap_targets(page, context=None):
        html = page.html or ""
        buttons = len(re.findall(r"<button", html, re.I))
        links = len(re.findall(r"<a\s", html, re.I))
        inputs = len(re.findall(r"<input", html, re.I))
        taps = buttons + links + inputs
        has_size = "min-width:" in html.lower() or "height:" in html.lower()
        if taps > 50 and not has_size:
            return _r("tap_targets", False, f"页面有 {taps} 个可点击元素，建议检查间距",
                     {"tap_targets": taps})
        return _r("tap_targets", True, "静态检测无明显问题，建议结合实际页面检查")

    @staticmethod
    def check_mobile_lighthouse_score(page, context=None):
        lh = page.lighthouse_data or {}
        score = lh.get("mobile_seo_score")
        if score is None:
            return _r("mobile_lighthouse_score", True, "未运行移动端 Lighthouse 检测")
        if score < 80:
            return _r("mobile_lighthouse_score", False, f"移动端评分 {score} 分",
                     {"score": score})
        return _r("mobile_lighthouse_score", True, f"移动端评分 {score} 分，表现良好",
                 {"score": score})

    @staticmethod
    def check_popup_avoid(page, context=None):
        html = page.html or ""
        has_popup = bool(re.search(r"(?:popup|modal|overlay)[-_]?class", html, re.I))
        has_interstitial = "interstitial" in html.lower()
        intrusive = has_popup and has_interstitial
        return _r(
            "popup_avoid", not intrusive,
            "未检测到侵入式弹窗" if not intrusive else "可能存在影响移动端体验的弹窗",
        )

    @staticmethod
    def check_touch_icon(page, context=None):
        html = page.html or ""
        has_touch = bool(re.search(r'apple-touch-icon', html, re.I))
        return _r(
            "touch_icon", has_touch,
            "有 Apple Touch Icon" if has_touch else "缺少 Apple Touch Icon",
        )

    @staticmethod
    def check_theme_color(page, context=None):
        html = page.html or ""
        has_theme = bool(re.search(r'meta\s+name=["\']theme-color', html, re.I))
        return _r(
            "theme_color", has_theme,
            "设置了 theme-color" if has_theme else "缺少移动端 theme-color 配置",
        )
