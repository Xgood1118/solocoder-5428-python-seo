from typing import Dict, List, Optional
from collections import defaultdict

from ..crawler import PageData, Crawler
from ..utils import extract_domain, normalize_url
from .models import (
    SiteAuditResult,
    PageAuditResult,
    RuleResult,
    Rule,
    Severity,
    Category,
    SEVERITY_SCORES,
    CATEGORY_NAMES,
)
from .rule_loader import RuleLoader
from .checks import get_all_checks, get_check_by_name


class Auditor:
    def __init__(self, rules_dir: str = None):
        self.rule_loader = RuleLoader(rules_dir=rules_dir)
        self.rule_loader.load_rules()
        self._check_functions = get_all_checks()

    def reload_rules(self) -> bool:
        changed = self.rule_loader.reload_if_changed()
        if changed:
            self._check_functions = get_all_checks()
        return changed

    @property
    def total_rules_count(self) -> int:
        return self.rule_loader.rules_count

    def audit_page(self, page: PageData, context: dict = None) -> PageAuditResult:
        self.reload_rules()
        page_result = PageAuditResult(url=page.final_url or page.url)
        rules = self.rule_loader.get_all_rules()
        rules_by_id = {r.id: r for r in rules if r.enabled}
        called_checks = set()
        results_by_id = {}
        for rule in rules:
            if not rule.enabled:
                continue
            check_name = rule.check_function
            if not check_name:
                continue
            if check_name in called_checks:
                continue
            check_func = self._check_functions.get(check_name)
            if not check_func:
                continue
            called_checks.add(check_name)
            try:
                result = check_func(page, context or {})
                if isinstance(result, list):
                    for r in result:
                        results_by_id[r.rule_id] = r
                else:
                    results_by_id[result.rule_id] = result
            except Exception as e:
                pass
        for rule in rules:
            if not rule.enabled:
                continue
            if rule.id in results_by_id:
                r = results_by_id[rule.id]
                self._apply_rule_metadata(r, rules_by_id)
                page_result.results.append(r)
            else:
                check_func = self._check_functions.get(rule.check_function)
                if check_func:
                    error_result = RuleResult(
                        rule_id=rule.id,
                        rule_name=rule.name,
                        category=rule.category,
                        severity=rule.severity,
                        weight=rule.weight,
                        passed=False,
                        message="规则执行失败：检查函数未返回对应结果",
                        fix_advice=rule.fix_advice,
                        executed=False,
                        error=f"check function '{rule.check_function}' did not return result for rule '{rule.id}'",
                    )
                    page_result.results.append(error_result)
        self._compute_page_score(page_result)
        return page_result

    def _apply_rule_metadata(self, result: RuleResult, rules_by_id: Dict[str, Rule]):
        if result.rule_id and result.rule_id in rules_by_id:
            rule = rules_by_id[result.rule_id]
            result.rule_name = rule.name
            result.category = rule.category
            result.severity = rule.severity
            result.weight = rule.weight
            if not result.fix_advice:
                result.fix_advice = rule.fix_advice

    def _compute_page_score(self, page_result: PageAuditResult):
        total_weight = 0
        earned_weight = 0
        critical = 0
        important = 0
        info = 0
        executed = 0
        passed = 0
        failed = 0
        skipped = 0
        for result in page_result.results:
            if not result.executed:
                skipped += 1
                continue
            executed += 1
            weight_value = self._weight_to_value(result.weight)
            total_weight += weight_value
            if result.passed:
                passed += 1
                earned_weight += weight_value
            else:
                failed += 1
                if result.severity == Severity.CRITICAL:
                    critical += 1
                elif result.severity == Severity.IMPORTANT:
                    important += 1
                else:
                    info += 1
        page_result.total_rules = executed
        page_result.passed_rules = passed
        page_result.failed_rules = failed
        page_result.skipped_rules = skipped
        page_result.critical_issues = critical
        page_result.important_issues = important
        page_result.info_issues = info
        if total_weight > 0:
            page_result.score = round((earned_weight / total_weight) * 100, 1)
        else:
            page_result.score = 0.0

    def _weight_to_value(self, weight) -> int:
        from .models import Weight
        if weight == Weight.HIGH:
            return 3
        elif weight == Weight.MEDIUM:
            return 2
        else:
            return 1

    def audit_site(self, pages: Dict[str, PageData]) -> SiteAuditResult:
        self.reload_rules()
        site_url = ""
        if pages:
            first_url = list(pages.keys())[0]
            domain = extract_domain(first_url)
            site_url = f"https://{domain}"
        site_result = SiteAuditResult(site_url=site_url, total_pages=len(pages))
        context = self._build_site_context(pages)
        page_results = []
        for url, page in pages.items():
            page_ctx = dict(context)
            if url in context.get("page_specific", {}):
                page_ctx.update(context["page_specific"][url])
            page_result = self.audit_page(page, page_ctx)
            page_results.append(page_result)
        site_result.page_results = page_results
        self._compute_site_score(site_result)
        self._compute_category_scores(site_result)
        site_result.orphan_pages = context.get("orphan_pages", [])
        site_result.summary = self._build_summary(site_result, context)
        return site_result

    def _build_site_context(self, pages: Dict[str, PageData]) -> dict:
        context = {}
        titles = defaultdict(list)
        descriptions = defaultdict(list)
        keywords = defaultdict(list)
        all_urls = set()
        linked_urls = set()
        error_5xx_count = 0
        has_robots = False
        has_sitemap = False
        sitemap_count = 0
        for url, page in pages.items():
            all_urls.add(url)
            if page.is_5xx:
                error_5xx_count += 1
            if page.title:
                titles[page.title].append(url)
            if page.description:
                descriptions[page.description].append(url)
            if page.keywords:
                keywords[page.keywords].append(url)
            for link in page.internal_links:
                norm_link = normalize_url(link)
                if norm_link.startswith(("http://", "https://")):
                    linked_urls.add(norm_link)
        orphan_pages = list(all_urls - linked_urls)
        context["orphan_pages"] = orphan_pages
        context["orphan_count"] = len(orphan_pages)
        context["5xx_count"] = error_5xx_count
        page_specific = {}
        for url, page in pages.items():
            ps = {}
            if page.title and len(titles.get(page.title, [])) > 1:
                ps["title_duplicate"] = True
                ps["title_duplicate_urls"] = [u for u in titles[page.title] if u != url]
            if page.description and len(descriptions.get(page.description, [])) > 1:
                ps["description_duplicate"] = True
                ps["description_duplicate_urls"] = [u for u in descriptions[page.description] if u != url]
            if page.keywords and len(keywords.get(page.keywords, [])) > 1:
                ps["keywords_duplicate"] = True
            page_specific[url] = ps
        context["page_specific"] = page_specific
        context["title_duplicates"] = {t: urls for t, urls in titles.items() if len(urls) > 1}
        context["description_duplicates"] = {d: urls for d, urls in descriptions.items() if len(urls) > 1}
        first_url = list(pages.keys())[0] if pages else ""
        domain = extract_domain(first_url)
        robots_url = f"https://{domain}/robots.txt"
        if robots_url in pages or f"http://{domain}/robots.txt" in pages:
            has_robots = True
        context["has_robots_txt"] = has_robots
        context["has_sitemap"] = has_sitemap
        context["sitemap_count"] = sitemap_count
        return context

    def _compute_site_score(self, site_result: SiteAuditResult):
        if not site_result.page_results:
            site_result.overall_score = 0.0
            return
        total_score = sum(p.score for p in site_result.page_results)
        site_result.overall_score = round(total_score / len(site_result.page_results), 1)

    def _compute_category_scores(self, site_result: SiteAuditResult):
        category_totals = defaultdict(float)
        category_counts = defaultdict(int)
        for page in site_result.page_results:
            cat_scores = defaultdict(float)
            cat_weights = defaultdict(int)
            for result in page.results:
                if not result.executed:
                    continue
                wv = self._weight_to_value(result.weight)
                cat_weights[result.category] += wv
                if result.passed:
                    cat_scores[result.category] += wv
            for cat in cat_weights:
                if cat_weights[cat] > 0:
                    score = (cat_scores[cat] / cat_weights[cat]) * 100
                    category_totals[cat] += score
                    category_counts[cat] += 1
        for cat in category_counts:
            site_result.category_scores[cat] = round(category_totals[cat] / category_counts[cat], 1)

    def _build_summary(self, site_result: SiteAuditResult, context: dict) -> dict:
        total_critical = sum(p.critical_issues for p in site_result.page_results)
        total_important = sum(p.important_issues for p in site_result.page_results)
        total_info = sum(p.info_issues for p in site_result.page_results)
        total_failed = sum(p.failed_rules for p in site_result.page_results)
        total_passed = sum(p.passed_rules for p in site_result.page_results)
        total_skipped = sum(p.skipped_rules for p in site_result.page_results)
        avg_score = site_result.overall_score
        return {
            "total_pages": site_result.total_pages,
            "overall_score": avg_score,
            "critical_issues": total_critical,
            "important_issues": total_important,
            "info_issues": total_info,
            "total_failed": total_failed,
            "total_passed": total_passed,
            "total_skipped": total_skipped,
            "orphan_pages": len(site_result.orphan_pages),
            "title_duplicates": len(context.get("title_duplicates", {})),
            "description_duplicates": len(context.get("description_duplicates", {})),
        }

    def get_failed_rules_count(self, site_result: SiteAuditResult) -> int:
        return sum(p.failed_rules for p in site_result.page_results)

    def get_unexecuted_rules(self, site_result: SiteAuditResult) -> List[dict]:
        unexecuted = []
        for page in site_result.page_results:
            for result in page.results:
                if not result.executed:
                    unexecuted.append({
                        "url": page.url,
                        "rule_id": result.rule_id,
                        "rule_name": result.rule_name,
                        "error": result.error,
                    })
        return unexecuted
