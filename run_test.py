import sys
sys.path.insert(0, '.')

output = []

def log(msg):
    output.append(msg)
    print(msg)

log("=== 测试导入 ===")
try:
    from seo_audit.config import settings
    log("✓ config 导入成功")
    log(f"  PORT={settings.PORT}, CACHE_TTL={settings.CACHE_TTL}")
except Exception as e:
    log(f"✗ config 导入失败: {e}")

try:
    from seo_audit.crawler import Crawler, PageData
    log("✓ crawler 导入成功")
except Exception as e:
    log(f"✗ crawler 导入失败: {e}")

try:
    from seo_audit.auditor import Auditor, Category, Severity
    log("✓ auditor 导入成功")
    auditor = Auditor()
    log(f"  规则总数: {auditor.total_rules_count}")
    log(f"  分类: {[c.value for c in Category]}")
except Exception as e:
    import traceback
    log(f"✗ auditor 导入失败: {e}")
    log(traceback.format_exc())

try:
    from seo_audit.reporter import ReportGenerator
    log("✓ reporter 导入成功")
except Exception as e:
    log(f"✗ reporter 导入失败: {e}")

try:
    from seo_audit.benchmark import Benchmark, Industry
    log("✓ benchmark 导入成功")
    bm = Benchmark()
    log(f"  行业数: {len(bm.get_all_industries())}")
except Exception as e:
    log(f"✗ benchmark 导入失败: {e}")

try:
    from seo_audit.service import AuditService
    log("✓ service 导入成功")
    svc = AuditService()
    stats = svc.get_cache_stats()
    log(f"  缓存统计: {stats}")
    rules_info = svc.get_rules_info()
    log(f"  规则信息: {rules_info}")
except Exception as e:
    import traceback
    log(f"✗ service 导入失败: {e}")
    log(traceback.format_exc())

try:
    from seo_audit.api import app
    log("✓ FastAPI app 创建成功")
    log(f"  路由数: {len(app.routes)}")
except Exception as e:
    import traceback
    log(f"✗ FastAPI app 创建失败: {e}")
    log(traceback.format_exc())

log("\n=== 测试模拟页面审计 ===")
try:
    from seo_audit.crawler.page_data import PageData
    from seo_audit.crawler.page_parser import PageParser
    from seo_audit.auditor import Auditor
    from seo_audit.reporter import ReportGenerator

    page = PageData(
        url="https://example.com",
        final_url="https://example.com",
        status_code=200,
        html="""
        <html>
        <head>
            <title>测试页面 - Example</title>
            <meta name="description" content="这是一个测试页面，用于验证SEO审计功能是否正常工作。">
            <meta name="keywords" content="测试,SEO,审计">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <link rel="canonical" href="https://example.com">
        </head>
        <body>
            <h1>欢迎来到 Example</h1>
            <p>这是一个测试页面，包含一些正文内容用于测试SEO审计功能。我们需要至少300字的内容来测试低质页面检测。那我就多写一点内容吧。这个页面是用来测试我们的SEO审计系统的。系统会检查各种SEO因素，包括标题、描述、关键词、H1标签、内容质量、图片alt属性、内部链接、外部链接等等。系统还会检查技术SEO因素，比如HTTPS、HSTS、canonical标签、hreflang标签、面包屑导航、URL静态化等。性能方面会检查页面加载时间、LCP、FID、CLS等Core Web Vitals指标。移动友好性方面会检查viewport、响应式设计、字体大小、点击元素间距等。结构化数据方面会检查JSON-LD、Open Graph、Twitter Card等标签。</p>
            <p>继续添加内容以确保字数足够。SEO（Search Engine Optimization）搜索引擎优化是提升网站在搜索引擎中排名的技术。好的SEO可以帮助网站获得更多的免费流量。我们的自动化审计工具可以帮助SEO团队快速发现网站的问题，提高工作效率。工具支持七大维度的审计：抓取与索引、TDK优化、内容质量、技术SEO、性能优化、移动友好、结构化数据。每个维度下面又有很多具体的检查规则。每条规则都有对应的严重级别和修复建议。</p>
            <img src="/test.jpg" alt="测试图片">
            <a href="/about">关于我们</a>
            <a href="https://other.com">外部链接</a>
        </body>
        </html>
        """,
        headers={"Content-Type": "text/html"},
    )

    parser = PageParser(base_domain="example.com")
    parsed = parser.parse(page.url, page.html, page.status_code, page.headers)
    log("✓ 页面解析成功")
    log(f"  Title: {parsed.title}")
    log(f"  字数: {parsed.word_count}")
    log(f"  H1: {parsed.h1_tags}")
    log(f"  内链: {len(parsed.internal_links)}, 外链: {len(parsed.external_links)}")
    log(f"  图片: {len(parsed.images)}")

    auditor = Auditor()
    result = auditor.audit_page(parsed)
    log("\n✓ 单页审计完成")
    log(f"  得分: {result.score}/100")
    log(f"  总规则: {result.total_rules}")
    log(f"  通过: {result.passed_rules}, 失败: {result.failed_rules}, 跳过: {result.skipped_rules}")
    log(f"  致命: {result.critical_issues}, 重要: {result.important_issues}, 一般: {result.info_issues}")

    log("\n  失败的规则:")
    for r in result.results:
        if not r.passed and r.executed:
            log(f"    - [{r.severity.value}] {r.rule_name}: {r.message}")

    log("\n  未执行的规则:")
    unexecuted_count = 0
    for r in result.results:
        if not r.executed:
            unexecuted_count += 1
            log(f"    - {r.rule_name}: {r.error}")
    if unexecuted_count == 0:
        log("    (无)")

    site_result = auditor.audit_site({parsed.url: parsed})
    reporter = ReportGenerator()
    md = reporter.generate_markdown_report(site_result)
    log(f"\n✓ Markdown 报告生成成功，长度: {len(md)} 字符")

except Exception as e:
    import traceback
    log(f"✗ 模拟页面审计失败: {e}")
    log(traceback.format_exc())

log("\n=== 所有测试完成 ===")

with open("test_result.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(output))
