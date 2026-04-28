"""日志配置模块"""

import sys

from loguru import logger

from app.core.config import settings


def setup_logging():
    """配置日志系统"""
    # 移除默认处理器
    logger.remove()

    # 控制台日志
    logger.add(
        sys.stdout,
        level=settings.LOG_LEVEL,
        format=settings.LOG_FORMAT,
        colorize=True,
        enqueue=True,
    )

    # 文件日志
    logger.add(
        "logs/app.log",
        level=settings.LOG_LEVEL,
        format=settings.LOG_FORMAT,
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        enqueue=True,
        encoding="utf-8",
    )

    # 错误日志单独记录
    logger.add(
        "logs/error.log",
        level="ERROR",
        format=settings.LOG_FORMAT,
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        enqueue=True,
        encoding="utf-8",
    )

    return logger


# 全局日志实例
log = setup_logging()
