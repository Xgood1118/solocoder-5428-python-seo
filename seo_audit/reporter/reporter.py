from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

from ..auditor import (
    SiteAuditResult,
    PageAuditResult,
    RuleResult,
    Severity,
    Category,
    CATEGORY_NAMES,
)


class ReportFormat(str, Enum):
    JSON = "json"
    HTML = "html"
    MARKDOWN = "markdown"


SEVERITY_ORDER = {
    Severity.CRITICAL: 0,
    Severity.IMPORTANT: 1,
    Severity.INFO: 2,
}


@dataclass
class IssueItem:
    rule_id: str
    rule_name: str
    category: Category
    severity: Severity
    message: str
    fix_advice: str
    affected_pages: List[str] = field(default_factory=list)
    details: dict = field(default_factory=dict)


@dataclass
class CompareResult:
    site_url: str
    old_score: float
    new_score: float
    score_change: float
    fixed_issues: List[IssueItem] = field(default_factory=list)
    new_issues: List[IssueItem] = field(default_factory=list)
    remaining_issues: List[IssueItem] = field(default_factory=list)


class ReportGenerator:
    def generate_site_report(self, audit_result: SiteAuditResult) -> dict:
        sorted_pages = sorted(
            audit_result.page_results,
            key=lambda p: p.critical_issues * 1000 + p.important_issues * 100 + p.info_issues,
            reverse=True,
        )
        issues_by_severity = self._group_issues_by_severity(audit_result)
        issues_by_category = self._group_issues_by_category(audit_result)
        unexecuted_rules = self._collect_unexecuted_rules(audit_result)
        report = {
            "site_url": audit_result.site_url,
            "audit_time": "",
            "summary": {
                "total_pages": audit_result.total_pages,
                "overall_score": audit_result.overall_score,
                "critical_issues": audit_result.summary.get("critical_issues", 0),
                "important_issues": audit_result.summary.get("important_issues", 0),
                "info_issues": audit_result.summary.get("info_issues", 0),
                "orphan_pages": len(audit_result.orphan_pages),
                "title_duplicates": audit_result.summary.get("title_duplicates", 0),
                "description_duplicates": audit_result.summary.get("description_duplicates", 0),
            },
            "category_scores": {
                cat.value: {
                    "name": CATEGORY_NAMES.get(cat, cat.value),
                    "score": score,
                }
                for cat, score in audit_result.category_scores.items()
            },
            "issues_by_severity": {
                sev.value: {
                    "name": self._severity_name(sev),
                    "count": len(issues),
                    "issues": issues,
                }
                for sev, issues in issues_by_severity.items()
            },
            "issues_by_category": {
                cat.value: {
                    "name": CATEGORY_NAMES.get(cat, cat.value),
                    "count": len(issues),
                    "issues": issues,
                }
                for cat, issues in issues_by_category.items()
            },
            "top_problem_pages": [
                {
                    "url": p.url,
                    "score": p.score,
                    "critical_issues": p.critical_issues,
                    "important_issues": p.important_issues,
                    "info_issues": p.info_issues,
                }
                for p in sorted_pages[:10]
            ],
            "orphan_pages": audit_result.orphan_pages,
            "unexecuted_rules": unexecuted_rules,
            "page_results": [
                self._page_result_to_dict(p)
                for p in sorted_pages
            ],
        }
        return report

    def _page_result_to_dict(self, page: PageAuditResult) -> dict:
        sorted_results = sorted(
            page.results,
            key=lambda r: (SEVERITY_ORDER.get(r.severity, 99), not r.passed),
        )
        return {
            "url": page.url,
            "score": page.score,
            "total_rules": page.total_rules,
            "passed_rules": page.passed_rules,
            "failed_rules": page.failed_rules,
            "skipped_rules": page.skipped_rules,
            "critical_issues": page.critical_issues,
            "important_issues": page.important_issues,
            "info_issues": page.info_issues,
            "issues": [
                self._rule_result_to_dict(r)
                for r in sorted_results
                if not r.passed and r.executed
            ],
            "passed_checks": [
                self._rule_result_to_dict(r)
                for r in sorted_results
                if r.passed and r.executed
            ],
            "unexecuted_rules": [
                self._rule_result_to_dict(r)
                for r in sorted_results
                if not r.executed
            ],
        }

    def _rule_result_to_dict(self, result: RuleResult) -> dict:
        return {
            "rule_id": result.rule_id,
            "rule_name": result.rule_name,
            "category": result.category.value if hasattr(result.category, "value") else str(result.category),
            "severity": result.severity.value if hasattr(result.severity, "value") else str(result.severity),
            "weight": result.weight.value if hasattr(result.weight, "value") else str(result.weight),
            "passed": result.passed,
            "message": result.message,
            "fix_advice": result.fix_advice,
            "details": result.details,
            "executed": result.executed,
            "error": result.error,
        }

    def _group_issues_by_severity(self, audit_result: SiteAuditResult) -> Dict[Severity, List[IssueItem]]:
        rule_issues: Dict[str, IssueItem] = {}
        for page in audit_result.page_results:
            for result in page.results:
                if result.passed or not result.executed:
                    continue
                key = result.rule_id
                if key not in rule_issues:
                    rule_issues[key] = IssueItem(
                        rule_id=result.rule_id,
                        rule_name=result.rule_name,
                        category=result.category,
                        severity=result.severity,
                        message=result.message,
                        fix_advice=result.fix_advice,
                        details=result.details,
                    )
                rule_issues[key].affected_pages.append(page.url)
        grouped: Dict[Severity, List[IssueItem]] = {
            Severity.CRITICAL: [],
            Severity.IMPORTANT: [],
            Severity.INFO: [],
        }
        for issue in rule_issues.values():
            if issue.severity in grouped:
                grouped[issue.severity].append(issue)
        for sev in grouped:
            grouped[sev].sort(key=lambda i: len(i.affected_pages), reverse=True)
        return grouped

    def _group_issues_by_category(self, audit_result: SiteAuditResult) -> Dict[Category, List[IssueItem]]:
        rule_issues: Dict[str, IssueItem] = {}
        for page in audit_result.page_results:
            for result in page.results:
                if result.passed or not result.executed:
                    continue
                key = result.rule_id
                if key not in rule_issues:
                    rule_issues[key] = IssueItem(
                        rule_id=result.rule_id,
                        rule_name=result.rule_name,
                        category=result.category,
                        severity=result.severity,
                        message=result.message,
                        fix_advice=result.fix_advice,
                        details=result.details,
                    )
                rule_issues[key].affected_pages.append(page.url)
        grouped: Dict[Category, List[IssueItem]] = {}
        for issue in rule_issues.values():
            if issue.category not in grouped:
                grouped[issue.category] = []
            grouped[issue.category].append(issue)
        for cat in grouped:
            grouped[cat].sort(key=lambda i: SEVERITY_ORDER.get(i.severity, 99))
        return grouped

    def _collect_unexecuted_rules(self, audit_result: SiteAuditResult) -> List[dict]:
        unexecuted = []
        for page in audit_result.page_results:
            for result in page.results:
                if not result.executed:
                    unexecuted.append({
                        "url": page.url,
                        "rule_id": result.rule_id,
                        "rule_name": result.rule_name,
                        "category": result.category.value if hasattr(result.category, "value") else str(result.category),
                        "error": result.error,
                    })
        return unexecuted

    def _severity_name(self, severity: Severity) -> str:
        names = {
            Severity.CRITICAL: "致命",
            Severity.IMPORTANT: "重要",
            Severity.INFO: "一般",
        }
        return names.get(severity, str(severity))

    def compare_reports(self, old_report: SiteAuditResult, new_report: SiteAuditResult) -> CompareResult:
        old_issues = self._extract_issues_dict(old_report)
        new_issues = self._extract_issues_dict(new_report)
        fixed = []
        new = []
        remaining = []
        for rule_id, issue in old_issues.items():
            if rule_id not in new_issues:
                fixed.append(issue)
            else:
                remaining.append(issue)
        for rule_id, issue in new_issues.items():
            if rule_id not in old_issues:
                new.append(issue)
        fixed.sort(key=lambda i: SEVERITY_ORDER.get(i.severity, 99))
        new.sort(key=lambda i: SEVERITY_ORDER.get(i.severity, 99))
        remaining.sort(key=lambda i: SEVERITY_ORDER.get(i.severity, 99))
        return CompareResult(
            site_url=new_report.site_url,
            old_score=old_report.overall_score,
            new_score=new_report.overall_score,
            score_change=round(new_report.overall_score - old_report.overall_score, 1),
            fixed_issues=fixed,
            new_issues=new,
            remaining_issues=remaining,
        )

    def _extract_issues_dict(self, audit_result: SiteAuditResult) -> Dict[str, IssueItem]:
        issues: Dict[str, IssueItem] = {}
        for page in audit_result.page_results:
            for result in page.results:
                if result.passed or not result.executed:
                    continue
                key = result.rule_id
                if key not in issues:
                    issues[key] = IssueItem(
                        rule_id=result.rule_id,
                        rule_name=result.rule_name,
                        category=result.category,
                        severity=result.severity,
                        message=result.message,
                        fix_advice=result.fix_advice,
                        details=result.details,
                    )
                issues[key].affected_pages.append(page.url)
        return issues

    def generate_batch_report(self, results: List[SiteAuditResult]) -> dict:
        total_sites = len(results)
        avg_score = sum(r.overall_score for r in results) / total_sites if total_sites > 0 else 0
        total_critical = sum(r.summary.get("critical_issues", 0) for r in results)
        total_important = sum(r.summary.get("important_issues", 0) for r in results)
        total_info = sum(r.summary.get("info_issues", 0) for r in results)
        sorted_sites = sorted(results, key=lambda r: r.overall_score)
        return {
            "total_sites": total_sites,
            "average_score": round(avg_score, 1),
            "total_critical_issues": total_critical,
            "total_important_issues": total_important,
            "total_info_issues": total_info,
            "sites_ranked_by_score": [
                {
                    "site_url": r.site_url,
                    "score": r.overall_score,
                    "critical_issues": r.summary.get("critical_issues", 0),
                    "important_issues": r.summary.get("important_issues", 0),
                    "info_issues": r.summary.get("info_issues", 0),
                }
                for r in sorted_sites
            ],
            "site_reports": [
                self.generate_site_report(r)
                for r in results
            ],
        }

    def generate_markdown_report(self, audit_result: SiteAuditResult) -> str:
        report = self.generate_site_report(audit_result)
        lines = []
        lines.append(f"# SEO 审计报告 - {report['site_url']}")
        lines.append("")
        lines.append("## 概览")
        lines.append("")
        lines.append(f"- **总分**: {report['summary']['overall_score']}/100")
        lines.append(f"- **页面数**: {report['summary']['total_pages']}")
        lines.append(f"- **致命问题**: {report['summary']['critical_issues']} 个")
        lines.append(f"- **重要问题**: {report['summary']['important_issues']} 个")
        lines.append(f"- **一般问题**: {report['summary']['info_issues']} 个")
        lines.append("")
        lines.append("## 分类得分")
        lines.append("")
        for cat_key, cat_data in report["category_scores"].items():
            lines.append(f"- **{cat_data['name']}**: {cat_data['score']} 分")
        lines.append("")
        for sev_key, sev_data in report["issues_by_severity"].items():
            if sev_data["count"] == 0:
                continue
            lines.append(f"## {sev_data['name']}问题 ({sev_data['count']})")
            lines.append("")
            for issue in sev_data["issues"][:10]:
                lines.append(f"### {issue['rule_name']}")
                lines.append(f"- 分类: {report['issues_by_category'].get(issue['category'], {}).get('name', issue['category'])}")
                lines.append(f"- 影响页面: {len(issue['affected_pages'])} 个")
                lines.append(f"- 问题描述: {issue['message']}")
                lines.append(f"- 修复建议: {issue['fix_advice']}")
                lines.append("")
        unexecuted = report.get("unexecuted_rules", [])
        if unexecuted:
            lines.append(f"## ⚠️ 未成功执行的规则 ({len(unexecuted)})")
            lines.append("")
            lines.append("以下规则因执行异常未完成审计，仅供参考：")
            lines.append("")
            for item in unexecuted[:10]:
                lines.append(f"- **{item['rule_name']}** ({item['rule_id']}) - 页面: {item['url']}")
                if item.get("error"):
                    lines.append(f"  错误: {item['error']}")
            lines.append("")
        return "\n".join(lines)
