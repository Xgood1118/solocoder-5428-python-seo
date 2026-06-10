import time
from typing import Dict, List, Optional
from collections import defaultdict
from dataclasses import dataclass, field

from .crawler import Crawler, PageData
from .auditor import Auditor, SiteAuditResult
from .reporter import ReportGenerator
from .benchmark import Benchmark, Industry
from .config import settings
from .utils import extract_domain, normalize_url


@dataclass
class AuditRecord:
    url: str
    result: SiteAuditResult
    timestamp: float
    report_data: dict = field(default_factory=dict)


class AuditService:
    def __init__(self):
        self.crawler = Crawler()
        self.auditor = Auditor()
        self.reporter = ReportGenerator()
        self.benchmark = Benchmark()
        self._report_cache: Dict[str, AuditRecord] = {}
        self._history: Dict[str, List[AuditRecord]] = defaultdict(list)

    async def audit_single_page(self, url: str) -> dict:
        url = normalize_url(url)
        cached = self._get_cached_report(url)
        if cached:
            return cached
        page_data = await self.crawler.fetch_single(url)
        if not page_data:
            return {"error": "无法获取页面内容", "url": url}
        pages = {url: page_data}
        audit_result = self.auditor.audit_site(pages)
        report = self.reporter.generate_site_report(audit_result)
        self._cache_report(url, audit_result, report)
        return report

    async def audit_site(self, start_url: str, max_pages: int = None) -> dict:
        start_url = normalize_url(start_url)
        domain = extract_domain(start_url)
        cached = self._get_cached_report(domain)
        if cached:
            return cached
        if max_pages is None:
            max_pages = settings.MAX_PAGES_PER_AUDIT
        pages = await self.crawler.audit_site(start_url)
        if not pages:
            return {"error": "未能抓取到任何页面", "url": start_url}
        audit_result = self.auditor.audit_site(pages)
        report = self.reporter.generate_site_report(audit_result)
        self._cache_report(domain, audit_result, report)
        self._add_to_history(domain, audit_result, report)
        return report

    async def audit_batch(self, urls: List[str]) -> dict:
        if len(urls) > settings.MAX_BATCH_URLS:
            return {"error": f"批量审计最多支持 {settings.MAX_BATCH_URLS} 个 URL"}
        results = []
        for url in urls:
            try:
                url = normalize_url(url)
                page_data = await self.crawler.fetch_single(url)
                if page_data:
                    pages = {url: page_data}
                    audit_result = self.auditor.audit_site(pages)
                    results.append(audit_result)
            except Exception:
                pass
        batch_report = self.reporter.generate_batch_report(results)
        return batch_report

    def compare_with_history(self, site_url: str, history_index: int = -1) -> dict:
        domain = extract_domain(site_url)
        history = self._history.get(domain, [])
        if len(history) < 2:
            return {"error": "历史报告不足，无法对比", "history_count": len(history)}
        if history_index >= 0:
            old_idx = history_index
        else:
            old_idx = len(history) - 2
        new_idx = len(history) - 1
        if old_idx < 0 or old_idx >= len(history):
            return {"error": "历史记录索引无效"}
        old_record = history[old_idx]
        new_record = history[new_idx]
        compare_result = self.reporter.compare_reports(old_record.result, new_record.result)
        return {
            "site_url": site_url,
            "old_timestamp": old_record.timestamp,
            "new_timestamp": new_record.timestamp,
            "old_score": compare_result.old_score,
            "new_score": compare_result.new_score,
            "score_change": compare_result.score_change,
            "fixed_issues": [
                self._issue_to_dict(i) for i in compare_result.fixed_issues
            ],
            "new_issues": [
                self._issue_to_dict(i) for i in compare_result.new_issues
            ],
            "remaining_issues": [
                self._issue_to_dict(i) for i in compare_result.remaining_issues
            ],
            "fixed_count": len(compare_result.fixed_issues),
            "new_count": len(compare_result.new_issues),
            "remaining_count": len(compare_result.remaining_issues),
        }

    def get_history(self, site_url: str) -> list:
        domain = extract_domain(site_url)
        history = self._history.get(domain, [])
        return [
            {
                "timestamp": r.timestamp,
                "score": r.result.overall_score,
                "page_count": r.result.total_pages,
                "critical_issues": r.result.summary.get("critical_issues", 0),
                "important_issues": r.result.summary.get("important_issues", 0),
                "info_issues": r.result.summary.get("info_issues", 0),
            }
            for r in history
        ]

    def compare_with_benchmark(self, site_url: str, industry: str = "general") -> dict:
        domain = extract_domain(site_url)
        cached = self._get_cached_report(domain)
        if not cached:
            return {"error": "请先执行审计后再对比行业基准"}
        score = cached.get("summary", {}).get("overall_score", 0)
        category_scores = cached.get("category_scores", {})
        cat_scores_flat = {k: v["score"] for k, v in category_scores.items()}
        try:
            industry_enum = Industry(industry)
        except ValueError:
            industry_enum = Industry.GENERAL
        overall = self.benchmark.compare_with_benchmark(score, industry_enum)
        categories = self.benchmark.compare_categories(cat_scores_flat, industry_enum)
        return {
            "industry": industry_enum.value,
            "industry_name": self.benchmark.get_all_industries().get(industry_enum, ""),
            "overall": overall,
            "categories": categories,
        }

    def get_all_industries(self) -> dict:
        return {
            k.value: v for k, v in self.benchmark.get_all_industries().items()
        }

    def reload_rules(self) -> dict:
        changed = self.auditor.reload_rules()
        return {
            "rules_reloaded": changed,
            "total_rules": self.auditor.total_rules_count,
        }

    def get_rules_info(self) -> dict:
        rules = self.auditor.rule_loader.get_all_rules()
        by_category = defaultdict(int)
        by_severity = defaultdict(int)
        for rule in rules:
            if rule.enabled:
                by_category[rule.category.value] += 1
                by_severity[rule.severity.value] += 1
        return {
            "total_rules": len(rules),
            "enabled_rules": self.auditor.total_rules_count,
            "by_category": dict(by_category),
            "by_severity": dict(by_severity),
        }

    def clear_cache(self) -> dict:
        self.crawler.clear_cache()
        self._report_cache.clear()
        return {"cleared": True, "message": "缓存已清空"}

    def get_cache_stats(self) -> dict:
        return {
            "page_cache_size": self.crawler.cache_size,
            "report_cache_size": len(self._report_cache),
            "history_entries": sum(len(v) for v in self._history.values()),
        }

    def _get_cached_report(self, key: str) -> Optional[dict]:
        if key in self._report_cache:
            record = self._report_cache[key]
            if time.time() - record.timestamp < settings.CACHE_TTL:
                return record.report_data
            else:
                del self._report_cache[key]
        return None

    def _cache_report(self, key: str, result: SiteAuditResult, report: dict):
        record = AuditRecord(
            url=key,
            result=result,
            timestamp=time.time(),
            report_data=report,
        )
        self._report_cache[key] = record

    def _add_to_history(self, domain: str, result: SiteAuditResult, report: dict):
        record = AuditRecord(
            url=domain,
            result=result,
            timestamp=time.time(),
            report_data=report,
        )
        self._history[domain].append(record)
        if len(self._history[domain]) > 20:
            self._history[domain] = self._history[domain][-20:]

    def _issue_to_dict(self, issue) -> dict:
        return {
            "rule_id": issue.rule_id,
            "rule_name": issue.rule_name,
            "category": issue.category.value if hasattr(issue.category, "value") else str(issue.category),
            "severity": issue.severity.value if hasattr(issue.severity, "value") else str(issue.severity),
            "message": issue.message,
            "fix_advice": issue.fix_advice,
            "affected_pages": issue.affected_pages,
            "details": issue.details,
        }

    async def detect_canonical_loop(self, start_url: str) -> dict:
        visited = []
        current_url = normalize_url(start_url)
        max_hops = 10
        for i in range(max_hops):
            if current_url in visited:
                loop_start = visited.index(current_url)
                loop = visited[loop_start:] + [current_url]
                return {
                    "has_loop": True,
                    "loop": loop,
                    "loop_length": len(loop) - 1,
                    "message": f"检测到 canonical 循环，共 {len(loop) - 1} 跳",
                }
            visited.append(current_url)
            page = await self.crawler.fetch_single(current_url)
            if not page or not page.canonical:
                break
            current_url = normalize_url(page.canonical)
        return {
            "has_loop": False,
            "chain": visited,
            "chain_length": len(visited) - 1,
            "message": "未检测到 canonical 循环",
        }

    def get_markdown_report(self, site_url: str) -> dict:
        domain = extract_domain(site_url)
        cached = self._report_cache.get(domain)
        if not cached:
            return {"error": "请先执行审计再生成报告"}
        markdown = self.reporter.generate_markdown_report(cached.result)
        return {
            "site_url": site_url,
            "markdown": markdown,
        }
