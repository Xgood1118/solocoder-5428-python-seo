from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .service import AuditService
from .schemas import (
    AuditRequest,
    BatchAuditRequest,
    CompareRequest,
    BenchmarkRequest,
    CanonicalLoopRequest,
)
from .utils import is_valid_url

app = FastAPI(
    title="SEO 自动化审计服务",
    description="基于 FastAPI 的自动化 SEO 审计服务，支持七大维度、200+ 条规则检测",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

audit_service = AuditService()


@app.get("/")
async def root():
    return {
        "name": "SEO Audit Service",
        "version": "1.0.0",
        "description": "自动化 SEO 审计服务 API",
        "endpoints": {
            "POST /audit/page": "单页面 SEO 审计",
            "POST /audit/site": "整站 SEO 审计",
            "POST /audit/batch": "批量 URL 审计（最多50个）",
            "GET /history/{domain}": "获取历史审计记录",
            "POST /compare/history": "与历史报告对比",
            "POST /compare/benchmark": "与行业基准对比",
            "GET /industries": "获取支持的行业列表",
            "POST /canonical/loop": "检测 canonical 循环",
            "GET /rules": "获取规则信息",
            "POST /rules/reload": "热加载规则",
            "GET /cache/stats": "获取缓存统计",
            "POST /cache/clear": "清空缓存",
            "GET /report/markdown/{domain}": "获取 Markdown 格式报告",
        },
    }


@app.post("/audit/page")
async def audit_page(request: AuditRequest):
    if not is_valid_url(request.url):
        raise HTTPException(status_code=400, detail="无效的 URL")
    try:
        result = await audit_service.audit_single_page(request.url)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"审计失败: {str(e)}")


@app.post("/audit/site")
async def audit_site(request: AuditRequest):
    if not is_valid_url(request.url):
        raise HTTPException(status_code=400, detail="无效的 URL")
    try:
        result = await audit_service.audit_site(request.url, request.max_pages)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"审计失败: {str(e)}")


@app.post("/audit/batch")
async def audit_batch(request: BatchAuditRequest):
    if not request.urls:
        raise HTTPException(status_code=400, detail="URL 列表不能为空")
    if len(request.urls) > settings.MAX_BATCH_URLS:
        raise HTTPException(
            status_code=400,
            detail=f"批量审计最多支持 {settings.MAX_BATCH_URLS} 个 URL",
        )
    try:
        result = await audit_service.audit_batch(request.urls)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量审计失败: {str(e)}")


@app.get("/history/{domain}")
async def get_history(domain: str):
    try:
        history = audit_service.get_history(domain)
        return {"domain": domain, "history": history, "count": len(history)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/compare/history")
async def compare_history(request: CompareRequest):
    if not is_valid_url(request.url):
        raise HTTPException(status_code=400, detail="无效的 URL")
    try:
        result = audit_service.compare_with_history(request.url, request.history_index)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/compare/benchmark")
async def compare_benchmark(request: BenchmarkRequest):
    if not is_valid_url(request.url):
        raise HTTPException(status_code=400, detail="无效的 URL")
    try:
        result = audit_service.compare_with_benchmark(request.url, request.industry)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/industries")
async def get_industries():
    return audit_service.get_all_industries()


@app.post("/canonical/loop")
async def detect_canonical_loop(request: CanonicalLoopRequest):
    if not is_valid_url(request.url):
        raise HTTPException(status_code=400, detail="无效的 URL")
    try:
        result = await audit_service.detect_canonical_loop(request.url)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/rules")
async def get_rules_info():
    return audit_service.get_rules_info()


@app.post("/rules/reload")
async def reload_rules():
    result = audit_service.reload_rules()
    return result


@app.get("/cache/stats")
async def cache_stats():
    return audit_service.get_cache_stats()


@app.post("/cache/clear")
async def clear_cache():
    return audit_service.clear_cache()


@app.get("/report/markdown/{domain}")
async def get_markdown_report(domain: str):
    result = audit_service.get_markdown_report(domain)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@app.get("/health")
async def health():
    return {"status": "healthy", "rules_loaded": audit_service.auditor.total_rules_count}
