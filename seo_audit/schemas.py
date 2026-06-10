from typing import List, Optional
from pydantic import BaseModel, HttpUrl


class AuditRequest(BaseModel):
    url: str
    max_pages: Optional[int] = None


class BatchAuditRequest(BaseModel):
    urls: List[str]


class CompareRequest(BaseModel):
    url: str
    history_index: Optional[int] = -1


class BenchmarkRequest(BaseModel):
    url: str
    industry: Optional[str] = "general"


class CanonicalLoopRequest(BaseModel):
    url: str
