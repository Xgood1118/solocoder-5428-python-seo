import uvicorn
from .config import settings
from .api import app


def main():
    uvicorn.run(
        "seo_audit.api:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=True,
    )


if __name__ == "__main__":
    main()
