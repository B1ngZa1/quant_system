"""One-command database initialization.

Steps:
1) alembic upgrade head
2) seed sample data
"""
import subprocess
import sys
import os
from alembic import command
from alembic.config import Config


def run(command: list[str], env: dict[str, str]) -> None:
    completed = subprocess.run(command, check=False, env=env)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def main() -> None:
    from dotenv import load_dotenv
    load_dotenv()
    env = os.environ.copy()
    os.makedirs("data", exist_ok=True)
    os.environ.update(env)

    print("[1/2] 执行数据库迁移...")
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")

    print("[2/2] 导入样例数据...")
    run([sys.executable, "scripts/seed_data.py"], env=env)

    print("初始化完成：数据库结构与样例数据已就绪。")


if __name__ == "__main__":
    main()
