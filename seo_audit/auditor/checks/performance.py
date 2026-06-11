from .base import BaseCheck
from ..models import RuleResult, Severity, Weight, Category


def _r(rule_id, passed, message, details=None):
    return RuleResult(
        rule_id=rule_id, rule_name="",
        category=Category.PERFORMANCE,
        severity=Severity.INFO, weight=Weight.LOW,
        passed=passed, message=message, fix_advice="",
        details=details or {},
    )


class PerformanceChecks(BaseCheck):
    category = Category.PERFORMANCE

    @staticmethod
    def check_page_load_time(page, context=None):
        t = page.load_time
        if t == 0:
            return _r("page_load_time", False, "未测量加载时间，无法验证是否达标",
                     {"notice": "未获取到实际加载时间数据，请结合 Lighthouse 检测"})
        if t > 3.0:
            return _r("page_load_time", False, f"页面加载时间 {t:.2f} 秒，超过 3 秒",
                     {"load_time_seconds": round(t, 2), "threshold": 3.0})
        elif t > 1.5:
            return _r("page_load_time", True, f"页面加载时间 {t:.2f} 秒，符合基本要求",
                     {"load_time_seconds": round(t, 2), "threshold": 3.0})
        return _r("page_load_time", True, f"页面加载时间 {t:.2f} 秒，表现优秀",
                 {"load_time_seconds": round(t, 2), "threshold": 3.0})

    @staticmethod
    def check_lighthouse_lcp(page, context=None):
        lh = page.lighthouse_data or {}
        lcp = lh.get("lcp")
        if lcp is None:
            return _r("lighthouse_lcp", False, "未运行 Lighthouse，LCP 数据缺失，请运行 Lighthouse CLI 检测",
                     {"notice": "LCP 指标缺失，无法验证是否达到 < 2.5s 标准"})
        if lcp > 2500:
            return _r("lighthouse_lcp", False, f"LCP 为 {lcp}ms，超过 2.5 秒",
                     {"lcp_ms": lcp, "threshold_ms": 2500})
        return _r("lighthouse_lcp", True, f"LCP 为 {lcp}ms，符合要求",
                 {"lcp_ms": lcp, "threshold_ms": 2500})

    @staticmethod
    def check_lighthouse_fid(page, context=None):
        lh = page.lighthouse_data or {}
        fid = lh.get("fid")
        if fid is None:
            return _r("lighthouse_fid", False, "未运行 Lighthouse，FID 数据缺失，请运行 Lighthouse CLI 检测",
                     {"notice": "FID 指标缺失，无法验证是否达到 < 100ms 标准"})
        if fid > 100:
            return _r("lighthouse_fid", False, f"FID 为 {fid}ms，超过 100ms",
                     {"fid_ms": fid, "threshold_ms": 100})
        return _r("lighthouse_fid", True, f"FID 为 {fid}ms，符合要求",
                 {"fid_ms": fid, "threshold_ms": 100})

    @staticmethod
    def check_lighthouse_cls(page, context=None):
        lh = page.lighthouse_data or {}
        cls = lh.get("cls")
        if cls is None:
            return _r("lighthouse_cls", False, "未运行 Lighthouse，CLS 数据缺失，请运行 Lighthouse CLI 检测",
                     {"notice": "CLS 指标缺失，无法验证是否达到 < 0.1 标准"})
        if cls > 0.1:
            return _r("lighthouse_cls", False, f"CLS 为 {cls}，超过 0.1",
                     {"cls": cls, "threshold": 0.1})
        return _r("lighthouse_cls", True, f"CLS 为 {cls}，符合要求",
                 {"cls": cls, "threshold": 0.1})

    @staticmethod
    def check_lighthouse_performance_score(page, context=None):
        lh = page.lighthouse_data or {}
        score = lh.get("performance_score")
        if score is None:
            return _r("lighthouse_performance_score", False, "未运行 Lighthouse，性能评分缺失，请运行 Lighthouse CLI",
                     {"notice": "Lighthouse 性能评分缺失，无法评估页面整体性能水平"})
        if score < 50:
            return _r("lighthouse_performance_score", False, f"性能评分 {score} 分，较差",
                     {"score": score})
        elif score < 80:
            return _r("lighthouse_performance_score", False, f"性能评分 {score} 分，需要优化",
                     {"score": score})
        return _r("lighthouse_performance_score", True, f"性能评分 {score} 分，表现良好",
                 {"score": score})

    @staticmethod
    def check_lighthouse_seo_score(page, context=None):
        lh = page.lighthouse_data or {}
        score = lh.get("seo_score")
        if score is None:
            return _r("lighthouse_seo_score", False, "未运行 Lighthouse，SEO 评分缺失，请运行 Lighthouse CLI",
                     {"notice": "Lighthouse SEO 评分缺失"})
        if score < 80:
            return _r("lighthouse_seo_score", False, f"SEO 评分 {score} 分",
                     {"score": score})
        return _r("lighthouse_seo_score", True, f"SEO 评分 {score} 分，表现良好",
                 {"score": score})

    @staticmethod
    def check_page_size(page, context=None):
        size_kb = len(page.html.encode("utf-8")) / 1024 if page.html else 0
        if size_kb > 500:
            return _r("page_size", False, f"HTML 大小 {size_kb:.1f}KB，偏大",
                     {"size_kb": round(size_kb, 1), "threshold_kb": 500})
        return _r("page_size", True, f"HTML 大小 {size_kb:.1f}KB",
                 {"size_kb": round(size_kb, 1)})

    @staticmethod
    def check_core_web_vitals(page, context=None):
        lh = page.lighthouse_data or {}
        lcp_val = lh.get("lcp")
        fid_val = lh.get("fid")
        cls_val = lh.get("cls")
        has_data = any(v is not None for v in [lcp_val, fid_val, cls_val])
        if not has_data:
            return _r("core_web_vitals", False, "未运行 Lighthouse，Core Web Vitals 三项数据均缺失",
                     {"notice": "请运行 Lighthouse CLI 获取 LCP/FID/CLS 三项核心指标"})
        lcp_ok = lcp_val <= 2500 if lcp_val is not None else None
        fid_ok = fid_val <= 100 if fid_val is not None else None
        cls_ok = cls_val <= 0.1 if cls_val is not None else None
        all_ok = all(v is None or v for v in [lcp_ok, fid_ok, cls_ok])
        any_fail = any(v is not None and not v for v in [lcp_ok, fid_ok, cls_ok])
        msg = "Core Web Vitals 全部达标" if (all_ok and not any_fail) else "部分 Core Web Vitals 不达标"
        return _r(
            "core_web_vitals", not any_fail, msg,
            {"lcp_ok": lcp_ok, "fid_ok": fid_ok, "cls_ok": cls_ok},
        )

    @staticmethod
    def check_ttfb_fast(page, context=None):
        lh = page.lighthouse_data or {}
        ttfb = lh.get("ttfb")
        if ttfb is None:
            return _r("ttfb_fast", False, "未检测到 TTFB 数据，请运行 Lighthouse 或服务端探针检测",
                     {"notice": "TTFB 指标缺失"})
        if ttfb > 600:
            return _r("ttfb_fast", False, f"TTFB {ttfb}ms，超过 600ms",
                     {"ttfb_ms": ttfb, "threshold_ms": 600})
        return _r("ttfb_fast", True, f"TTFB {ttfb}ms，符合要求",
                 {"ttfb_ms": ttfb, "threshold_ms": 600})

    @staticmethod
    def check_ttfb_excellent(page, context=None):
        lh = page.lighthouse_data or {}
        ttfb = lh.get("ttfb")
        if ttfb is None:
            return _r("ttfb_excellent", False, "未检测到 TTFB 数据，无法评估是否优秀",
                     {"notice": "TTFB 指标缺失"})
        if ttfb < 200:
            return _r("ttfb_excellent", True, f"TTFB {ttfb}ms，表现优秀 (< 200ms)",
                     {"ttfb_ms": ttfb, "threshold_ms": 200})
        return _r("ttfb_excellent", False, f"TTFB {ttfb}ms，未达到优秀水平 200ms",
                 {"ttfb_ms": ttfb, "threshold_ms": 200})

    @staticmethod
    def check_fcp_fast(page, context=None):
        lh = page.lighthouse_data or {}
        fcp = lh.get("fcp")
        if fcp is None:
            return _r("fcp_fast", False, "未运行 Lighthouse，FCP 首次内容绘制数据缺失",
                     {"notice": "FCP 指标缺失"})
        if fcp > 1800:
            return _r("fcp_fast", False, f"FCP {fcp}ms，超过 1.8s",
                     {"fcp_ms": fcp, "threshold_ms": 1800})
        return _r("fcp_fast", True, f"FCP {fcp}ms，符合要求",
                 {"fcp_ms": fcp, "threshold_ms": 1800})

    @staticmethod
    def check_speed_index_good(page, context=None):
        lh = page.lighthouse_data or {}
        si = lh.get("speed_index")
        if si is None:
            return _r("speed_index_good", False, "未运行 Lighthouse，Speed Index 数据缺失",
                     {"notice": "Speed Index 指标缺失"})
        if si > 3400:
            return _r("speed_index_good", False, f"Speed Index {si}ms，超过 3.4s",
                     {"speed_index_ms": si, "threshold_ms": 3400})
        return _r("speed_index_good", True, f"Speed Index {si}ms，符合要求",
                 {"speed_index_ms": si, "threshold_ms": 3400})

    @staticmethod
    def check_tti_fast(page, context=None):
        lh = page.lighthouse_data or {}
        tti = lh.get("tti")
        if tti is None:
            return _r("tti_fast", False, "未运行 Lighthouse，TTI 可交互时间数据缺失",
                     {"notice": "TTI 指标缺失"})
        if tti > 3800:
            return _r("tti_fast", False, f"TTI {tti}ms，超过 3.8s",
                     {"tti_ms": tti, "threshold_ms": 3800})
        return _r("tti_fast", True, f"TTI {tti}ms，符合要求",
                 {"tti_ms": tti, "threshold_ms": 3800})

    @staticmethod
    def check_tbt_low(page, context=None):
        lh = page.lighthouse_data or {}
        tbt = lh.get("tbt")
        if tbt is None:
            return _r("tbt_low", False, "未运行 Lighthouse，TBT 总阻塞时间数据缺失",
                     {"notice": "TBT 指标缺失"})
        if tbt > 200:
            return _r("tbt_low", False, f"TBT {tbt}ms，超过 200ms",
                     {"tbt_ms": tbt, "threshold_ms": 200})
        return _r("tbt_low", True, f"TBT {tbt}ms，符合要求",
                 {"tbt_ms": tbt, "threshold_ms": 200})

    @staticmethod
    def check_image_optimized(page, context=None):
        if not page.images:
            return _r("image_optimized", True, "页面不含图片", {"image_count": 0})
        unopt_count = 0
        total = len(page.images)
        for img in page.images:
            src = img.get("src", "") if isinstance(img, dict) else getattr(img, "src", "")
            if not src:
                continue
            if not any(src.lower().endswith(ext) for ext in (".webp", ".avif", ".jpg", ".jpeg", ".png", ".gif", ".svg")):
                pass
            if isinstance(img, dict) and not img.get("width") or isinstance(img, dict) and not img.get("height"):
                unopt_count += 1
        if total == 0:
            return _r("image_optimized", True, "图片数量为 0")
        unopt_rate = unopt_count / total if total else 0
        if unopt_rate > 0.5:
            return _r("image_optimized", False, f"有 {unopt_count}/{total} 张图片未设置宽高，可能未做优化",
                     {"unoptimized": unopt_count, "total": total})
        return _r("image_optimized", True, f"图片优化情况良好，未优化图片占比 {unopt_rate:.0%}",
                 {"unoptimized": unopt_count, "total": total})

    @staticmethod
    def check_image_format_modern(page, context=None):
        if not page.images:
            return _r("image_format_modern", True, "页面不含图片")
        total = len(page.images)
        modern = 0
        for img in page.images:
            src = img.get("src", "") if isinstance(img, dict) else getattr(img, "src", "")
            if any(src.lower().endswith(ext) for ext in (".webp", ".avif")):
                modern += 1
        if modern == 0 and total > 0:
            return _r("image_format_modern", False, f"页面 {total} 张图片未使用 WebP/AVIF 等现代格式",
                     {"total_images": total, "modern_format_count": 0})
        return _r("image_format_modern", True, f"{modern}/{total} 张图片采用现代格式",
                 {"total_images": total, "modern_format_count": modern})

    @staticmethod
    def check_js_execution_fast(page, context=None):
        lh = page.lighthouse_data or {}
        js_time = lh.get("js_execution_time")
        if js_time is None:
            return _r("js_execution_fast", False, "未运行 Lighthouse，JS 执行时间数据缺失",
                     {"notice": "JS 执行时间指标缺失"})
        if js_time > 3500:
            return _r("js_execution_fast", False, f"JS 执行时间 {js_time}ms，超过 3.5s",
                     {"js_exec_ms": js_time, "threshold_ms": 3500})
        return _r("js_execution_fast", True, f"JS 执行时间 {js_time}ms，符合要求",
                 {"js_exec_ms": js_time, "threshold_ms": 3500})

    @staticmethod
    def check_unused_css_removed(page, context=None):
        lh = page.lighthouse_data or {}
        unused_css = lh.get("unused_css_bytes")
        total_css = lh.get("total_css_bytes")
        if unused_css is None or total_css is None:
            return _r("unused_css_removed", False, "未运行 Lighthouse，CSS 使用率数据缺失",
                     {"notice": "未使用 CSS 比例数据缺失"})
        if total_css == 0:
            return _r("unused_css_removed", True, "页面未加载 CSS")
        waste = unused_css / total_css
        if waste > 0.3:
            return _r("unused_css_removed", False, f"CSS 中有 {waste:.0%} 未使用，建议通过 PurgeCSS 移除",
                     {"unused_ratio": round(waste, 3), "unused_bytes": unused_css, "total_bytes": total_css})
        return _r("unused_css_removed", True, f"CSS 未使用率 {waste:.0%}，在合理范围",
                 {"unused_ratio": round(waste, 3), "unused_bytes": unused_css, "total_bytes": total_css})

    @staticmethod
    def check_unused_js_removed(page, context=None):
        lh = page.lighthouse_data or {}
        unused_js = lh.get("unused_js_bytes")
        total_js = lh.get("total_js_bytes")
        if unused_js is None or total_js is None:
            return _r("unused_js_removed", False, "未运行 Lighthouse，JS 使用率数据缺失",
                     {"notice": "未使用 JS 比例数据缺失"})
        if total_js == 0:
            return _r("unused_js_removed", True, "页面未加载 JS")
        waste = unused_js / total_js
        if waste > 0.3:
            return _r("unused_js_removed", False, f"JS 中有 {waste:.0%} 未使用，建议代码分割 + Tree Shaking",
                     {"unused_ratio": round(waste, 3), "unused_bytes": unused_js, "total_bytes": total_js})
        return _r("unused_js_removed", True, f"JS 未使用率 {waste:.0%}，在合理范围",
                 {"unused_ratio": round(waste, 3), "unused_bytes": unused_js, "total_bytes": total_js})

    @staticmethod
    def check_dom_size_reasonable(page, context=None):
        if page.dom_nodes is None:
            return _r("dom_size_reasonable", False, "未运行 Lighthouse，DOM 节点数量数据缺失",
                     {"notice": "DOM 节点数缺失"})
        dom_nodes = int(page.dom_nodes)
        if dom_nodes > 1500:
            return _r("dom_size_reasonable", False, f"DOM 节点数 {dom_nodes}，超过 1500 建议优化",
                     {"dom_nodes": dom_nodes, "threshold": 1500})
        return _r("dom_size_reasonable", True, f"DOM 节点数 {dom_nodes}，在合理范围",
                 {"dom_nodes": dom_nodes, "threshold": 1500})

    @staticmethod
    def check_dom_depth_reasonable(page, context=None):
        if page.dom_depth is None:
            return _r("dom_depth_reasonable", False, "未运行 Lighthouse，DOM 嵌套深度数据缺失",
                     {"notice": "DOM 最大深度缺失"})
        dom_depth = int(page.dom_depth)
        if dom_depth > 32:
            return _r("dom_depth_reasonable", False, f"DOM 最大深度 {dom_depth}，超过 32 层",
                     {"dom_depth": dom_depth, "threshold": 32})
        return _r("dom_depth_reasonable", True, f"DOM 最大深度 {dom_depth}，在合理范围",
                 {"dom_depth": dom_depth, "threshold": 32})

    @staticmethod
    def check_critical_request_chain_short(page, context=None):
        lh = page.lighthouse_data or {}
        chain_depth = lh.get("critical_chain_depth")
        if chain_depth is None:
            return _r("critical_request_chain_short", False, "未运行 Lighthouse，关键请求链深度数据缺失",
                     {"notice": "关键请求链深度缺失"})
        if chain_depth > 5:
            return _r("critical_request_chain_short", False, f"关键请求链深度 {chain_depth}，建议合并资源减少依赖",
                     {"chain_depth": chain_depth, "threshold": 5})
        return _r("critical_request_chain_short", True, f"关键请求链深度 {chain_depth}，合理",
                 {"chain_depth": chain_depth, "threshold": 5})

    @staticmethod
    def check_third_party_scripts_limited(page, context=None):
        if page.external_scripts_count is None:
            return _r("third_party_scripts_limited", False, "第三方脚本数量未检测",
                     {"notice": "第三方脚本统计缺失"})
        count = int(page.external_scripts_count)
        if count > 5:
            return _r("third_party_scripts_limited", False, f"第三方脚本 {count} 个，超过 5 个",
                     {"third_party_count": count, "threshold": 5})
        return _r("third_party_scripts_limited", True, f"第三方脚本 {count} 个，在合理范围",
                 {"third_party_count": count, "threshold": 5})

    @staticmethod
    def check_font_display_swap(page, context=None):
        html_lower = (page.html or "").lower()
        has_font_display = "font-display" in html_lower or "font-display:swap" in html_lower
        if not has_font_display:
            styles = page.links if hasattr(page, "links") else []
            has_stylesheet_with_font = any(
                ("fonts.googleapis" in (l.get("href", "") if isinstance(l, dict) else getattr(l, "href", "")))
                for l in styles
            )
            if has_stylesheet_with_font and not has_font_display:
                return _r("font_display_swap", False, "使用了 Google Fonts 但未设置 font-display: swap",
                         {"notice": "添加 &display=swap 参数到字体 URL，或在 CSS 中设置 font-display: swap"})
        if not has_font_display:
            return _r("font_display_swap", False, "未检测到 font-display 配置，可能存在隐形文字闪烁 FOIT",
                     {"notice": "建议为所有自定义字体设置 font-display: swap"})
        return _r("font_display_swap", True, "已配置 font-display 策略")

    @staticmethod
    def check_font_fout_minimized(page, context=None):
        html_lower = (page.html or "").lower()
        has_font_display_swap = "font-display:swap" in html_lower.replace(" ", "")
        has_preload_font = '<linkrel="preload"' in html_lower.replace(" ", "") and "font" in html_lower
        if has_font_display_swap or has_preload_font:
            return _r("font_fout_minimized", True, "已通过 font-display: swap 或字体预加载处理 FOUT")
        return _r("font_fout_minimized", False, "未检测到 FOUT/FOIT 处理措施",
                 {"notice": "建议 font-display:swap + 关键字体预加载组合使用"})

    @staticmethod
    def check_preconnect_used(page, context=None):
        links = page.links if hasattr(page, "links") else []
        preconnect_count = 0
        for l in links:
            rel = l.get("rel", "") if isinstance(l, dict) else getattr(l, "rel", "")
            if "preconnect" in rel.lower():
                preconnect_count += 1
        if preconnect_count == 0:
            return _r("preconnect_used", False, "未使用 preconnect 预连接第三方域名",
                     {"notice": "对 GA/GTM/CDN 等常用域名加 <link rel=preconnect> 可节省 100-500ms"})
        return _r("preconnect_used", True, f"已对 {preconnect_count} 个域名使用 preconnect 预连接",
                 {"preconnect_count": preconnect_count})

    @staticmethod
    def check_preload_critical(page, context=None):
        links = page.links if hasattr(page, "links") else []
        preload_count = 0
        for l in links:
            rel = l.get("rel", "") if isinstance(l, dict) else getattr(l, "rel", "")
            if "preload" in rel.lower():
                preload_count += 1
        if preload_count == 0:
            return _r("preload_critical", False, "未使用 preload 预加载关键资源",
                     {"notice": "首屏必须的字体/关键 CSS 建议用 <link rel=preload as=...> 预加载"})
        return _r("preload_critical", True, f"已对 {preload_count} 个关键资源使用 preload 预加载",
                 {"preload_count": preload_count})

    @staticmethod
    def check_prefetch_prerender_used(page, context=None):
        links = page.links if hasattr(page, "links") else []
        has_prefetch = False
        for l in links:
            rel = l.get("rel", "") if isinstance(l, dict) else getattr(l, "rel", "")
            rl = rel.lower()
            if "prefetch" in rl or "prerender" in rl or "dns-prefetch" in rl:
                has_prefetch = True
                break
        if not has_prefetch:
            return _r("prefetch_prerender_used", False, "未使用 prefetch/prerender/dns-prefetch 策略性预加载",
                     {"notice": "下一步极可能访问的页面资源可用 prefetch 提前加载"})
        return _r("prefetch_prerender_used", True, "已使用 prefetch/prerender 或 dns-prefetch 策略")

    @staticmethod
    def check_long_tasks_avoided(page, context=None):
        lh = page.lighthouse_data or {}
        long_tasks = lh.get("long_tasks_count")
        if long_tasks is None:
            return _r("long_tasks_avoided", False, "未运行 Lighthouse，长任务数量数据缺失",
                     {"notice": "长任务数指标缺失"})
        if long_tasks > 0:
            return _r("long_tasks_avoided", False, f"存在 {long_tasks} 个超过 50ms 的长任务，建议拆分",
                     {"long_tasks": long_tasks, "threshold_ms": 50})
        return _r("long_tasks_avoided", True, "没有检测到 >50ms 的长任务")

    @staticmethod
    def check_main_thread_work_low(page, context=None):
        lh = page.lighthouse_data or {}
        main_ms = lh.get("main_thread_work_ms")
        if main_ms is None:
            return _r("main_thread_work_low", False, "未运行 Lighthouse，主线程工作量数据缺失",
                     {"notice": "主线程工作量指标缺失"})
        if main_ms > 4000:
            return _r("main_thread_work_low", False, f"主线程总工作量 {main_ms}ms，超过 4s，建议优化",
                     {"main_thread_work_ms": main_ms, "threshold_ms": 4000})
        return _r("main_thread_work_low", True, f"主线程总工作量 {main_ms}ms，合理",
                 {"main_thread_work_ms": main_ms, "threshold_ms": 4000})

    @staticmethod
    def check_service_worker_registered(page, context=None):
        html = page.html or ""
        has_sw = "serviceworker.register" in html.lower() or "service-worker.js" in html.lower() or "navigator.serviceworker" in html.lower()
        if not has_sw:
            return _r("service_worker_registered", False, "未检测到 Service Worker 注册",
                     {"notice": "注册 SW 可实现离线访问和资源缓存，显著提升二次访问速度"})
        return _r("service_worker_registered", True, "已注册 Service Worker")

    @staticmethod
    def check_text_compression_enabled(page, context=None):
        headers = page.headers or {}
        ce = ""
        for k, v in headers.items():
            if k.lower() == "content-encoding":
                ce = str(v).lower()
                break
        html_size = len((page.html or "").encode("utf-8"))
        if not ce and html_size > 10240:
            return _r("text_compression_enabled", False, "响应头中未检测到 Content-Encoding，文本资源未启用压缩",
                     {"notice": "请在服务器上启用 Gzip 或 Brotli 压缩文本资源"})
        if ce in ("gzip", "br", "deflate"):
            return _r("text_compression_enabled", True, f"已启用 {ce.upper()} 压缩")
        if html_size <= 10240:
            return _r("text_compression_enabled", True, "HTML 较小 (<10KB)，压缩影响不大")
        return _r("text_compression_enabled", False, "未启用文本压缩，请开启 Gzip 或 Brotli")

    @staticmethod
    def check_cdn_static_resources(page, context=None):
        if context and context.get("cdn_for_static") is not None:
            ok = context["cdn_for_static"]
            return _r("cdn_static_resources", ok,
                      "静态资源已走 CDN" if ok else "静态资源未使用 CDN，建议接入",
                      {"cdn_used": ok})
        images = page.images or []
        scripts = page.scripts if hasattr(page, "scripts") else []
        links = page.links if hasattr(page, "links") else []
        all_hosts = set()
        for img in images:
            src = img.get("src", "") if isinstance(img, dict) else getattr(img, "src", "")
            if "://" in src:
                try:
                    from urllib.parse import urlparse
                    all_hosts.add(urlparse(src).netloc.lower())
                except Exception:
                    pass
        for sc in scripts:
            s = sc.get("src", "") if isinstance(sc, dict) else getattr(sc, "src", "")
            if "://" in s:
                try:
                    from urllib.parse import urlparse
                    all_hosts.add(urlparse(s).netloc.lower())
                except Exception:
                    pass
        for lk in links:
            href = lk.get("href", "") if isinstance(lk, dict) else getattr(lk, "href", "")
            if "://" in href:
                try:
                    from urllib.parse import urlparse
                    all_hosts.add(urlparse(href).netloc.lower())
                except Exception:
                    pass
        page_host = ""
        try:
            from urllib.parse import urlparse
            page_host = urlparse(page.final_url or page.url or "").netloc.lower()
        except Exception:
            pass
        external_hosts = [h for h in all_hosts if h and h != page_host]
        cdn_keywords = ("cdn", "cloudfront", "fastly", "jsdelivr", "unpkg", "cdnjs", "bootcdn", "staticfile", "imgcache", "alicdn")
        cdn_count = sum(1 for h in external_hosts if any(k in h for k in cdn_keywords))
        if not external_hosts:
            return _r("cdn_static_resources", True, "静态资源与主站同域，建议接入 CDN 进一步加速")
        if cdn_count == 0:
            return _r("cdn_static_resources", False, f"外部资源 {len(external_hosts)} 个域名，未检测到 CDN 域名",
                     {"external_hosts": list(external_hosts)})
        return _r("cdn_static_resources", True, f"检测到 {cdn_count} 个 CDN 域名用于静态资源分发",
                 {"cdn_host_count": cdn_count, "external_hosts": list(external_hosts)})

    @staticmethod
    def check_responsive_images_srcset(page, context=None):
        if not page.images:
            return _r("responsive_images_srcset", True, "页面不含图片")
        total = len(page.images)
        with_srcset = 0
        for img in page.images:
            srcset = img.get("srcset", "") if isinstance(img, dict) else getattr(img, "srcset", "")
            if srcset:
                with_srcset += 1
        if total > 0 and with_srcset == 0:
            return _r("responsive_images_srcset", False, f"页面 {total} 张图片均未使用 srcset 适配不同设备",
                     {"images_without_srcset": total})
        return _r("responsive_images_srcset", True, f"{with_srcset}/{total} 张图片配置了 srcset 响应式适配",
                 {"images_with_srcset": with_srcset, "total_images": total})
