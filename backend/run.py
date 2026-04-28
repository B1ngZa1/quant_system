#!/usr/bin/env python3
"""开发服务器启动脚本"""
import uvicorn

from app.core.config import settings
from app.core.logging import log

if __name__ == "__main__":
    log.info(f"启动开发服务器: http://{settings.HOST}:{settings.PORT}")
    log.info(f"API文档: http://{settings.HOST}:{settings.PORT}/docs")

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        reload_dirs=["app"] if settings.DEBUG else None,
        workers=1,
        access_log=False,
    )
