import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    PORT: int = int(os.getenv("PORT", "8000"))
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "86400"))
    MAX_PAGES_PER_AUDIT: int = int(os.getenv("MAX_PAGES_PER_AUDIT", "1000"))
    RATE_LIMIT_PER_DOMAIN: int = int(os.getenv("RATE_LIMIT_PER_DOMAIN", "5"))
    MAX_BATCH_URLS: int = int(os.getenv("MAX_BATCH_URLS", "50"))
    USER_AGENT: str = os.getenv("USER_AGENT", "SEO-AuditBot/1.0")


settings = Settings()
