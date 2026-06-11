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
            return _r("mobile_lighthouse_score", False, "未运行移动端 Lighthouse，SEO 评分数据缺失",
                     {"notice": "请运行 Lighthouse CLI 获取移动端评分"})
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

    @staticmethod
    def check_viewport_width_device(page, context=None):
        if not page.viewport:
            return _r("viewport_width_device", False, "页面缺少 viewport meta 标签")
        vl = page.viewport.lower()
        ok = "width=device-width" in vl
        return _r(
            "viewport_width_device", ok,
            "Viewport 已设置 width=device-width" if ok else "Viewport 未设置 width=device-width",
            {"viewport": page.viewport},
        )

    @staticmethod
    def check_viewport_no_user_scalable_no(page, context=None):
        if not page.viewport:
            return _r("viewport_no_user_scalable_no", True, "页面缺少 viewport meta 标签")
        vl = page.viewport.lower()
        has_no_scalable = "user-scalable=no" in vl or "user-scalable = no" in vl
        return _r(
            "viewport_no_user_scalable_no", not has_no_scalable,
            "未禁用用户缩放" if not has_no_scalable else "设置了 user-scalable=no 禁止用户缩放",
            {"viewport": page.viewport},
        )

    @staticmethod
    def check_viewport_maximum_scale(page, context=None):
        if not page.viewport:
            return _r("viewport_maximum_scale", True, "页面缺少 viewport meta 标签")
        vl = page.viewport.lower()
        has_max_scale = "maximum-scale" in vl
        return _r(
            "viewport_maximum_scale", not has_max_scale,
            "未设置 maximum-scale 限制缩放" if not has_max_scale else "设置了 maximum-scale 限制用户放大",
            {"viewport": page.viewport},
        )

    @staticmethod
    def check_small_screen_360_ok(page, context=None):
        html = page.html or ""
        has_360_mq = bool(re.search(r"@media[^{]*\(\s*max-width\s*:\s*360px\s*\)", html, re.I))
        has_375_mq = bool(re.search(r"@media[^{]*\(\s*max-width\s*:\s*3[67]\dpx\s*\)", html, re.I))
        has_small_mq = has_360_mq or has_375_mq
        has_xs_class = bool(re.search(r"col-xs-", html, re.I))
        ok = has_small_mq or has_xs_class
        return _r(
            "small_screen_360_ok", ok,
            "检测到 360px 小屏适配规则" if ok else "未检测到针对 360px 小屏的适配规则",
            {"has_360_media_query": has_360_mq, "has_xs_class": has_xs_class},
        )

    @staticmethod
    def check_font_size_mobile_14px(page, context=None):
        html = page.html or ""
        small_fonts = 0
        for m in re.finditer(r"font-size\s*:\s*(\d+(?:\.\d+)?)\s*px", html, re.I):
            if float(m.group(1)) < 14:
                small_fonts += 1
        return _r(
            "font_size_mobile_14px", small_fonts == 0,
            "未检测到小于 14px 的字体" if small_fonts == 0 else f"检测到 {small_fonts} 处字体小于 14px（移动端建议 ≥14px）",
            {"small_font_count": small_fonts},
        )

    @staticmethod
    def check_line_height_mobile_ok(page, context=None):
        html = page.html or ""
        has_line_height = bool(re.search(r"line-height\s*:\s*(?:1\.[5-9]|[2-9])", html, re.I))
        has_unitless = bool(re.search(r"line-height\s*:\s*1\.[5-9]", html, re.I))
        ok = has_line_height or has_unitless
        return _r(
            "line_height_mobile_ok", ok,
            "检测到合理的行高设置（≥1.5）" if ok else "未检测到移动端行高设置，建议设置为 1.5-1.6",
            {"has_line_height_rule": has_line_height},
        )

    @staticmethod
    def check_tap_target_size_48(page, context=None):
        html = page.html or ""
        has_min_size = bool(re.search(r"min-(?:width|height)\s*:\s*4[0-9]px", html, re.I))
        has_padding = bool(re.search(r"padding\s*:\s*(?:1[0-9]|[2-9]\d)px", html, re.I))
        buttons = len(re.findall(r"<button", html, re.I))
        ok = has_min_size or has_padding or buttons == 0
        return _r(
            "tap_target_size_48", ok,
            "检测到触摸元素尺寸设置" if ok else "未检测到触摸元素 48x48px 尺寸设置",
            {"has_min_size": has_min_size, "has_padding": has_padding, "button_count": buttons},
        )

    @staticmethod
    def check_tap_target_spacing_8(page, context=None):
        html = page.html or ""
        has_gap = bool(re.search(r"(?:gap|grid-gap)\s*:\s*[89]\d*px", html, re.I))
        has_margin = bool(re.search(r"margin\s*:\s*[89]\d*px", html, re.I))
        has_spacing_class = bool(re.search(r"(?:space|gap|spacing)-(?:2|3|4|5|6|7|8)", html, re.I))
        ok = has_gap or has_margin or has_spacing_class
        return _r(
            "tap_target_spacing_8", ok,
            "检测到触摸元素间距设置（≥8px）" if ok else "未检测到触摸元素之间 ≥8px 的间距设置",
            {"has_gap": has_gap, "has_margin": has_margin, "has_spacing_class": has_spacing_class},
        )

    @staticmethod
    def check_no_flash_or_applets(page, context=None):
        html = page.html or ""
        has_flash = bool(re.search(r"<(?:object|embed|applet)", html, re.I))
        has_swf = ".swf" in html.lower()
        has_java_applet = "applet" in html.lower() and "<applet" in html.lower()
        ok = not (has_flash or has_swf or has_java_applet)
        return _r(
            "no_flash_or_applets", ok,
            "未检测到 Flash 或 Java 插件内容" if ok else "检测到 Flash/Java 插件内容，移动端不支持",
            {"has_flash": has_flash, "has_swf": has_swf, "has_java_applet": has_java_applet},
        )

    @staticmethod
    def check_popup_not_obstructing(page, context=None):
        html = page.html or ""
        has_fullscreen_popup = bool(re.search(r"(?:position\s*:\s*fixed|z-index\s*:\s*\d{3,})", html, re.I))
        has_large_modal = bool(re.search(r"(?:width|height)\s*:\s*100(?:vh|vw|%)", html, re.I))
        problem = has_fullscreen_popup and has_large_modal
        return _r(
            "popup_not_obstructing", not problem,
            "未检测到全屏遮挡式弹窗" if not problem else "可能存在全屏遮挡主内容的弹窗，影响移动端体验",
            {"has_fullscreen_popup": has_fullscreen_popup, "has_large_modal": has_large_modal},
        )

    @staticmethod
    def check_popup_close_easy(page, context=None):
        html = page.html or ""
        has_close_btn = bool(re.search(r"(?:close|cancel|dismiss|关闭)", html, re.I))
        has_close_icon = bool(re.search(r"(?:×|&times;|X|icon-close)", html, re.I))
        ok = has_close_btn or has_close_icon
        return _r(
            "popup_close_easy", ok,
            "检测到弹窗关闭按钮/标识" if ok else "未检测到明显的弹窗关闭按钮标识",
            {"has_close_btn": has_close_btn, "has_close_icon": has_close_icon},
        )

    @staticmethod
    def check_img_responsive_width(page, context=None):
        html = page.html or ""
        has_max_width = bool(re.search(r"img\s*\{[^}]*max-width\s*:\s*100", html, re.I))
        has_img_class = bool(re.search(r'class=["\'][^"\']*(?:img-fluid|img-responsive|w-full|max-w-full)', html, re.I))
        has_inline_style = bool(re.search(r'<img[^>]*style=["\'][^"\']*max-width\s*:\s*100', html, re.I))
        ok = has_max_width or has_img_class or has_inline_style
        return _r(
            "img_responsive_width", ok,
            "检测到响应式图片设置（max-width: 100%）" if ok else "未检测到图片 max-width:100% 响应式设置",
            {"has_global_max_width": has_max_width, "has_responsive_class": has_img_class, "has_inline_style": has_inline_style},
        )

    @staticmethod
    def check_no_horizontal_scroll(page, context=None):
        html = page.html or ""
        has_overflow_x_hidden = bool(re.search(r"overflow-x\s*:\s*hidden", html, re.I))
        has_body_overflow = bool(re.search(r"(?:body|html)\s*\{[^}]*overflow-x\s*:\s*hidden", html, re.I))
        has_wide_fixed = bool(re.search(r"width\s*:\s*(?:1[0-9]{3}|[2-9]\d{3})px", html, re.I))
        has_no_wrap = bool(re.search(r"white-space\s*:\s*nowrap", html, re.I))
        risk = has_wide_fixed and not (has_overflow_x_hidden or has_body_overflow)
        ok = not risk or has_overflow_x_hidden or has_body_overflow
        return _r(
            "no_horizontal_scroll", ok,
            "静态检测无横向滚动风险" if ok else "检测到可能导致横向滚动的宽元素，建议检查",
            {"has_overflow_x_hidden": has_overflow_x_hidden, "has_wide_fixed": has_wide_fixed, "has_no_wrap": has_no_wrap},
        )

    @staticmethod
    def check_fixed_elements_width_ok(page, context=None):
        html = page.html or ""
        fixed_count = len(re.findall(r"position\s*:\s*fixed", html, re.I))
        has_width_limit = bool(re.search(r"position\s*:\s*fixed[^}]*width\s*:\s*(?:100%|auto|max-width)", html, re.I | re.S))
        has_left_right = bool(re.search(r"position\s*:\s*fixed[^}]*left\s*:|position\s*:\s*fixed[^}]*right\s*:", html, re.I | re.S))
        ok = fixed_count == 0 or has_width_limit or has_left_right
        return _r(
            "fixed_elements_width_ok", ok,
            "Fixed 定位元素宽度有合理限制" if ok else "Fixed 元素可能缺少宽度限制导致横向溢出",
            {"fixed_count": fixed_count, "has_width_limit": has_width_limit, "has_left_right": has_left_right},
        )

    @staticmethod
    def check_buttons_mobile_size(page, context=None):
        html = page.html or ""
        button_count = len(re.findall(r"<button", html, re.I))
        has_min_height = bool(re.search(r"button\s*\{[^}]*min-height\s*:\s*(?:4[0-9]|[5-9]\d)px", html, re.I | re.S))
        has_padding = bool(re.search(r"button\s*\{[^}]*padding\s*:", html, re.I | re.S))
        has_btn_class = bool(re.search(r'class=["\'][^"\']*(?:btn-lg|btn-block|text-base|py-|px-)', html, re.I))
        ok = button_count == 0 or has_min_height or has_padding or has_btn_class
        return _r(
            "buttons_mobile_size", ok,
            "按钮有合理的移动端尺寸设置" if ok else "未检测到按钮的移动端尺寸优化",
            {"button_count": button_count, "has_min_height": has_min_height, "has_padding": has_padding, "has_btn_class": has_btn_class},
        )

    @staticmethod
    def check_form_input_autocorrect(page, context=None):
        html = page.html or ""
        inputs = re.findall(r"<input[^>]*>", html, re.I)
        text_inputs = [i for i in inputs if re.search(r'type=["\'](?:text|search|email|tel|url)', i, re.I)]
        has_autocorrect_off = any('autocorrect="off"' in i.lower() or "autocorrect='off'" in i.lower() for i in text_inputs)
        has_autocomplete = any('autocomplete' in i.lower() for i in text_inputs)
        total_text = len(text_inputs)
        ok = total_text == 0 or has_autocomplete or total_text < 3
        return _r(
            "form_input_autocorrect", ok,
            "表单输入框属性设置合理" if ok else "建议为输入框合理设置 autocomplete/autocorrect 等属性",
            {"text_input_count": total_text, "has_autocorrect_off": has_autocorrect_off, "has_autocomplete": has_autocomplete},
        )

    @staticmethod
    def check_mobile_navigation_accessible(page, context=None):
        html = page.html or ""
        has_hamburger = bool(re.search(r"(?:hamburger|burger|menu[-_]?toggle|navbar[-_]?toggler)", html, re.I))
        has_nav_class = bool(re.search(r'class=["\'][^"\']*(?:navbar|nav-menu|mobile-menu)', html, re.I))
        has_button_nav = bool(re.search(r"<button[^>]*(?:menu|nav|toggle)", html, re.I))
        ok = has_hamburger or has_nav_class or has_button_nav
        return _r(
            "mobile_navigation_accessible", ok,
            "检测到移动端导航组件（汉堡菜单等）" if ok else "未检测到移动端导航组件，建议添加汉堡菜单",
            {"has_hamburger": has_hamburger, "has_nav_class": has_nav_class},
        )

    @staticmethod
    def check_touch_active_feedback(page, context=None):
        html = page.html or ""
        has_active = bool(re.search(r":(?:active|focus|hover)[^,{]*\{[^}]*", html, re.I))
        has_button_active = bool(re.search(r"(?:button|a)\s*:\s*active", html, re.I))
        has_pressed = bool(re.search(r"(?:aria-pressed|data-pressed|pressed)", html, re.I))
        ok = has_active or has_button_active or has_pressed
        return _r(
            "touch_active_feedback", ok,
            "检测到 :active 等触摸状态视觉反馈" if ok else "未检测到触摸状态（:active）的视觉反馈样式",
            {"has_active": has_active, "has_button_active": has_button_active, "has_pressed": has_pressed},
        )

    @staticmethod
    def check_inputmode_attribute_set(page, context=None):
        html = page.html or ""
        inputs = re.findall(r"<input[^>]*>", html, re.I)
        has_inputmode = any('inputmode' in i.lower() for i in inputs)
        numeric_inputs = [i for i in inputs if re.search(r'type=["\'](?:number|tel|email|url|date)', i, re.I) or 'inputmode' in i.lower()]
        total_with_hint = len([i for i in inputs if 'inputmode' in i.lower() or 'type=' in i.lower() and re.search(r'type=["\'](?:number|tel|email|url|date|search)', i, re.I)])
        ok = len(inputs) == 0 or has_inputmode or total_with_hint >= len(numeric_inputs)
        return _r(
            "inputmode_attribute_set", ok,
            "关键输入框已设置 inputmode 或对应 type" if ok else "建议为数字/电话/邮箱等输入框设置 inputmode 属性",
            {"input_count": len(inputs), "has_inputmode": has_inputmode, "typed_input_count": total_with_hint},
        )

    @staticmethod
    def check_orientation_landscape_ok(page, context=None):
        html = page.html or ""
        has_orientation_mq = bool(re.search(r"orientation\s*:\s*(?:landscape|portrait)", html, re.I))
        has_landscape = bool(re.search(r"landscape", html, re.I))
        has_flex_wrap = "flex-wrap" in html.lower()
        has_grid_auto = "grid-auto" in html.lower()
        ok = has_orientation_mq or has_landscape or has_flex_wrap or has_grid_auto
        return _r(
            "orientation_landscape_ok", ok,
            "检测到横屏适配或灵活布局（flex-wrap/grid）" if ok else "未检测到横屏模式适配，建议进行横屏优化",
            {"has_orientation_mq": has_orientation_mq, "has_flex_wrap": has_flex_wrap, "has_grid_auto": has_grid_auto},
        )

    @staticmethod
    def check_tel_links_used(page, context=None):
        html = page.html or ""
        phone_patterns = [
            r"1[3-9]\d{9}",
            r"\d{3,4}[-\s]?\d{7,8}",
            r"\(\d{3,4}\)\s*\d{7,8}",
        ]
        phone_matches = []
        for pat in phone_patterns:
            phone_matches.extend(re.findall(pat, html))
        has_tel_link = bool(re.search(r'href=["\']tel:', html, re.I))
        tel_link_count = len(re.findall(r'href=["\']tel:', html, re.I))
        phone_count = len(phone_matches)
        ok = phone_count == 0 or (tel_link_count > 0 and tel_link_count >= phone_count * 0.5)
        return _r(
            "tel_links_used", ok,
            f"检测到 {tel_link_count} 个 tel: 链接，{phone_count} 个电话号码" if ok else f"检测到 {phone_count} 个电话号码，但仅有 {tel_link_count} 个 tel: 拨号链接",
            {"phone_count": phone_count, "tel_link_count": tel_link_count},
        )

    @staticmethod
    def check_mailto_links_used(page, context=None):
        html = page.html or ""
        email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
        emails = re.findall(email_pattern, html)
        has_mailto = bool(re.search(r'href=["\']mailto:', html, re.I))
        mailto_count = len(re.findall(r'href=["\']mailto:', html, re.I))
        email_count = len(emails)
        ok = email_count == 0 or (mailto_count > 0 and mailto_count >= email_count * 0.5)
        return _r(
            "mailto_links_used", ok,
            f"检测到 {mailto_count} 个 mailto: 链接，{email_count} 个邮箱地址" if ok else f"检测到 {email_count} 个邮箱地址，但仅有 {mailto_count} 个 mailto: 链接",
            {"email_count": email_count, "mailto_count": mailto_count},
        )

    @staticmethod
    def check_responsive_breakpoints(page, context=None):
        html = page.html or ""
        mq_values = re.findall(r"\(\s*(?:min|max)-width\s*:\s*(\d+)px\s*\)", html, re.I)
        breakpoints = set(int(v) for v in mq_values)
        has_360 = any(320 <= b <= 380 for b in breakpoints)
        has_768 = any(700 <= b <= 800 for b in breakpoints)
        has_1024 = any(960 <= b <= 1100 for b in breakpoints)
        covered = sum([has_360, has_768, has_1024])
        ok = covered >= 2 or len(breakpoints) >= 3
        return _r(
            "responsive_breakpoints", ok,
            f"断点覆盖良好，检测到 {len(breakpoints)} 个断点，覆盖 {covered}/3 个主流断点" if ok else f"断点覆盖不足，检测到 {len(breakpoints)} 个断点，建议覆盖 360/768/1024",
            {"breakpoints": sorted(list(breakpoints)), "has_360": has_360, "has_768": has_768, "has_1024": has_1024},
        )

    @staticmethod
    def check_flex_or_grid_used(page, context=None):
        html = page.html or ""
        has_flex = bool(re.search(r"display\s*:\s*flex", html, re.I))
        has_grid = bool(re.search(r"display\s*:\s*grid", html, re.I))
        has_flex_class = bool(re.search(r'class=["\'][^"\']*(?:flex|d-flex)', html, re.I))
        has_grid_class = bool(re.search(r'class=["\'][^"\']*(?:grid|d-grid)', html, re.I))
        has_float = bool(re.search(r"float\s*:\s*(?:left|right)", html, re.I))
        ok = has_flex or has_grid or has_flex_class or has_grid_class
        return _r(
            "flex_or_grid_used", ok,
            "使用了 Flex/Grid 现代布局" if ok else ("未检测到 Flex/Grid 布局，仍在使用 float 布局" if has_float else "未检测到 Flex/Grid 现代布局"),
            {"has_flex": has_flex, "has_grid": has_grid, "has_float": has_float},
        )

    @staticmethod
    def check_mobile_first_css(page, context=None):
        html = page.html or ""
        min_width_mq = re.findall(r"@media[^{]*\(\s*min-width\s*:\s*(\d+)px\s*\)", html, re.I)
        max_width_mq = re.findall(r"@media[^{]*\(\s*max-width\s*:\s*(\d+)px\s*\)", html, re.I)
        min_count = len(min_width_mq)
        max_count = len(max_width_mq)
        mobile_first = min_count > 0 and (max_count == 0 or min_count >= max_count)
        ok = min_count + max_count == 0 or mobile_first
        return _r(
            "mobile_first_css", ok,
            f"采用 Mobile First 写法（min-width: {min_count} 条 vs max-width: {max_count} 条）" if ok else f"可能未采用 Mobile First，建议以小屏为默认样式（min-width {min_count} 条 < max-width {max_count} 条）",
            {"min_width_mq_count": min_count, "max_width_mq_count": max_count},
        )
