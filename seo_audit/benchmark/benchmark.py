from typing import Dict, Optional
from dataclasses import dataclass, field
from enum import Enum


class Industry(str, Enum):
    E_COMMERCE = "e_commerce"
    NEWS = "news"
    BLOG = "blog"
    CORPORATE = "corporate"
    SAAS = "saas"
    EDUCATION = "education"
    HEALTHCARE = "healthcare"
    FINANCE = "finance"
    GENERAL = "general"


INDUSTRY_NAMES = {
    Industry.E_COMMERCE: "电商",
    Industry.NEWS: "新闻资讯",
    Industry.BLOG: "博客",
    Industry.CORPORATE: "企业官网",
    Industry.SAAS: "SaaS 服务",
    Industry.EDUCATION: "教育",
    Industry.HEALTHCARE: "医疗健康",
    Industry.FINANCE: "金融",
    Industry.GENERAL: "通用",
}


@dataclass
class BenchmarkData:
    industry: Industry
    avg_score: float
    avg_page_count: int
    avg_critical_issues: float
    avg_important_issues: float
    avg_info_issues: float
    category_avg_scores: Dict[str, float] = field(default_factory=dict)
    percentile_25: float = 0.0
    percentile_50: float = 0.0
    percentile_75: float = 0.0
    percentile_90: float = 0.0
    sample_size: int = 0


class Benchmark:
    def __init__(self):
        self._benchmarks: Dict[Industry, BenchmarkData] = {}
        self._init_default_benchmarks()

    def _init_default_benchmarks(self):
        defaults = {
            Industry.E_COMMERCE: {
                "avg_score": 62.0,
                "avg_page_count": 250,
                "avg_critical_issues": 3.2,
                "avg_important_issues": 12.5,
                "avg_info_issues": 25.0,
                "percentile_25": 45.0,
                "percentile_50": 60.0,
                "percentile_75": 75.0,
                "percentile_90": 85.0,
                "sample_size": 580,
                "category_avg_scores": {
                    "crawl_index": 70.0,
                    "tdk": 65.0,
                    "content_quality": 55.0,
                    "technical_seo": 60.0,
                    "performance": 50.0,
                    "mobile": 62.0,
                    "structured_data": 45.0,
                },
            },
            Industry.NEWS: {
                "avg_score": 58.0,
                "avg_page_count": 5000,
                "avg_critical_issues": 5.0,
                "avg_important_issues": 18.0,
                "avg_info_issues": 35.0,
                "percentile_25": 40.0,
                "percentile_50": 55.0,
                "percentile_75": 72.0,
                "percentile_90": 82.0,
                "sample_size": 320,
                "category_avg_scores": {
                    "crawl_index": 65.0,
                    "tdk": 70.0,
                    "content_quality": 50.0,
                    "technical_seo": 55.0,
                    "performance": 45.0,
                    "mobile": 58.0,
                    "structured_data": 55.0,
                },
            },
            Industry.BLOG: {
                "avg_score": 68.0,
                "avg_page_count": 80,
                "avg_critical_issues": 2.0,
                "avg_important_issues": 8.0,
                "avg_info_issues": 18.0,
                "percentile_25": 52.0,
                "percentile_50": 68.0,
                "percentile_75": 80.0,
                "percentile_90": 88.0,
                "sample_size": 890,
                "category_avg_scores": {
                    "crawl_index": 78.0,
                    "tdk": 72.0,
                    "content_quality": 65.0,
                    "technical_seo": 68.0,
                    "performance": 55.0,
                    "mobile": 65.0,
                    "structured_data": 55.0,
                },
            },
            Industry.CORPORATE: {
                "avg_score": 65.0,
                "avg_page_count": 120,
                "avg_critical_issues": 2.5,
                "avg_important_issues": 10.0,
                "avg_info_issues": 20.0,
                "percentile_25": 48.0,
                "percentile_50": 65.0,
                "percentile_75": 78.0,
                "percentile_90": 86.0,
                "sample_size": 650,
                "category_avg_scores": {
                    "crawl_index": 72.0,
                    "tdk": 68.0,
                    "content_quality": 60.0,
                    "technical_seo": 65.0,
                    "performance": 55.0,
                    "mobile": 62.0,
                    "structured_data": 50.0,
                },
            },
            Industry.SAAS: {
                "avg_score": 72.0,
                "avg_page_count": 60,
                "avg_critical_issues": 1.5,
                "avg_important_issues": 7.0,
                "avg_info_issues": 15.0,
                "percentile_25": 58.0,
                "percentile_50": 72.0,
                "percentile_75": 82.0,
                "percentile_90": 90.0,
                "sample_size": 420,
                "category_avg_scores": {
                    "crawl_index": 80.0,
                    "tdk": 75.0,
                    "content_quality": 68.0,
                    "technical_seo": 72.0,
                    "performance": 65.0,
                    "mobile": 70.0,
                    "structured_data": 62.0,
                },
            },
            Industry.EDUCATION: {
                "avg_score": 60.0,
                "avg_page_count": 300,
                "avg_critical_issues": 3.0,
                "avg_important_issues": 14.0,
                "avg_info_issues": 28.0,
                "percentile_25": 42.0,
                "percentile_50": 60.0,
                "percentile_75": 76.0,
                "percentile_90": 84.0,
                "sample_size": 280,
                "category_avg_scores": {
                    "crawl_index": 68.0,
                    "tdk": 62.0,
                    "content_quality": 58.0,
                    "technical_seo": 58.0,
                    "performance": 50.0,
                    "mobile": 60.0,
                    "structured_data": 48.0,
                },
            },
            Industry.HEALTHCARE: {
                "avg_score": 63.0,
                "avg_page_count": 180,
                "avg_critical_issues": 2.8,
                "avg_important_issues": 11.0,
                "avg_info_issues": 22.0,
                "percentile_25": 46.0,
                "percentile_50": 62.0,
                "percentile_75": 77.0,
                "percentile_90": 85.0,
                "sample_size": 230,
                "category_avg_scores": {
                    "crawl_index": 70.0,
                    "tdk": 66.0,
                    "content_quality": 60.0,
                    "technical_seo": 62.0,
                    "performance": 52.0,
                    "mobile": 62.0,
                    "structured_data": 52.0,
                },
            },
            Industry.FINANCE: {
                "avg_score": 66.0,
                "avg_page_count": 200,
                "avg_critical_issues": 2.2,
                "avg_important_issues": 9.5,
                "avg_info_issues": 19.0,
                "percentile_25": 50.0,
                "percentile_50": 66.0,
                "percentile_75": 79.0,
                "percentile_90": 87.0,
                "sample_size": 310,
                "category_avg_scores": {
                    "crawl_index": 75.0,
                    "tdk": 70.0,
                    "content_quality": 62.0,
                    "technical_seo": 65.0,
                    "performance": 55.0,
                    "mobile": 64.0,
                    "structured_data": 52.0,
                },
            },
            Industry.GENERAL: {
                "avg_score": 63.0,
                "avg_page_count": 150,
                "avg_critical_issues": 2.8,
                "avg_important_issues": 11.0,
                "avg_info_issues": 22.0,
                "percentile_25": 45.0,
                "percentile_50": 62.0,
                "percentile_75": 76.0,
                "percentile_90": 85.0,
                "sample_size": 1000,
                "category_avg_scores": {
                    "crawl_index": 70.0,
                    "tdk": 66.0,
                    "content_quality": 58.0,
                    "technical_seo": 62.0,
                    "performance": 52.0,
                    "mobile": 62.0,
                    "structured_data": 50.0,
                },
            },
        }
        for industry, data in defaults.items():
            self._benchmarks[industry] = BenchmarkData(
                industry=industry,
                avg_score=data["avg_score"],
                avg_page_count=data["avg_page_count"],
                avg_critical_issues=data["avg_critical_issues"],
                avg_important_issues=data["avg_important_issues"],
                avg_info_issues=data["avg_info_issues"],
                percentile_25=data["percentile_25"],
                percentile_50=data["percentile_50"],
                percentile_75=data["percentile_75"],
                percentile_90=data["percentile_90"],
                sample_size=data["sample_size"],
                category_avg_scores=data["category_avg_scores"],
            )

    def get_benchmark(self, industry: Industry = Industry.GENERAL) -> Optional[BenchmarkData]:
        return self._benchmarks.get(industry)

    def get_all_industries(self) -> Dict[Industry, str]:
        return {ind: INDUSTRY_NAMES.get(ind, ind.value) for ind in Industry}

    def compare_with_benchmark(self, score: float, industry: Industry = Industry.GENERAL) -> dict:
        benchmark = self.get_benchmark(industry)
        if not benchmark:
            return {"better_than_avg": False, "percentile": "unknown", "benchmark": None}
        difference = round(score - benchmark.avg_score, 1)
        percentile_rank = self._calculate_percentile(score, benchmark)
        return {
            "your_score": score,
            "industry_avg": benchmark.avg_score,
            "difference": difference,
            "better_than_avg": score >= benchmark.avg_score,
            "percentile_rank": percentile_rank,
            "percentile_25": benchmark.percentile_25,
            "percentile_50": benchmark.percentile_50,
            "percentile_75": benchmark.percentile_75,
            "percentile_90": benchmark.percentile_90,
            "sample_size": benchmark.sample_size,
        }

    def _calculate_percentile(self, score: float, benchmark: BenchmarkData) -> str:
        if score >= benchmark.percentile_90:
            return "Top 10%"
        elif score >= benchmark.percentile_75:
            return "Top 25%"
        elif score >= benchmark.percentile_50:
            return "前 50%"
        elif score >= benchmark.percentile_25:
            return "后 50%"
        else:
            return "Bottom 25%"

    def compare_categories(self, category_scores: dict, industry: Industry = Industry.GENERAL) -> dict:
        benchmark = self.get_benchmark(industry)
        if not benchmark:
            return {}
        result = {}
        for cat_key, your_score in category_scores.items():
            avg_score = benchmark.category_avg_scores.get(cat_key, 0)
            result[cat_key] = {
                "your_score": your_score,
                "industry_avg": avg_score,
                "difference": round(your_score - avg_score, 1),
                "better_than_avg": your_score >= avg_score,
            }
        return result
