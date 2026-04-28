"""Pytest 启动前设置环境变量，避免加载占位 SECRET_KEY 触发校验失败。"""

import os

os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("SECRET_KEY", "pytest-secret-key-minimum-32-characters-long")
