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
            return _r("page_load_time", True, "未测量加载时间")
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
            return _r("lighthouse_lcp", True, "未运行 Lighthouse 检测")
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
            return _r("lighthouse_fid", True, "未运行 Lighthouse 检测")
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
            return _r("lighthouse_cls", True, "未运行 Lighthouse 检测")
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
            return _r("lighthouse_performance_score", True, "未运行 Lighthouse 检测")
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
            return _r("lighthouse_seo_score", True, "未运行 Lighthouse 检测")
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
        lcp_ok = lh.get("lcp", 0) <= 2500 if lh.get("lcp") is not None else True
        fid_ok = lh.get("fid", 0) <= 100 if lh.get("fid") is not None else True
        cls_ok = lh.get("cls", 0) <= 0.1 if lh.get("cls") is not None else True
        all_ok = lcp_ok and fid_ok and cls_ok
        has_data = any(v is not None for v in [lh.get("lcp"), lh.get("fid"), lh.get("cls")])
        if not has_data:
            return _r("core_web_vitals", True, "无 Core Web Vitals 数据")
        return _r(
            "core_web_vitals", all_ok,
            "Core Web Vitals 全部达标" if all_ok else "部分 Core Web Vitals 不达标",
            {"lcp_ok": lcp_ok, "fid_ok": fid_ok, "cls_ok": cls_ok},
        )
