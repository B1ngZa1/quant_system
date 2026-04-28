"""在本项目 local_datasets 下创建指向「项目根/daily_data/前复权」的目录联接（junction，可选）。

默认数据目录为仓库根目录下的 ``daily_data``（例如 ``quant_system/daily_data/前复权``）。
若数据已直接放在该路径，通常无需再运行本脚本；仅当希望用 junction 复用其它路径时再执行。
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _find_forward_adj_dir() -> Path:
    quant_root = Path(__file__).resolve().parents[2]
    root = quant_root / "daily_data"
    if not root.is_dir():
        raise SystemExit(f"未找到目录: {root}（请将 A 股 daily_data 放在项目根目录下）")
    for p in root.iterdir():
        if p.is_dir() and "复权" in p.name and p.name.startswith("前"):
            return p
    raise SystemExit(f"在 {root} 下未找到「前复权」类子目录")


def main() -> None:
    backend = Path(__file__).resolve().parents[1]
    link = backend / "data" / "local_datasets" / "a_share_daily_adj"
    target = _find_forward_adj_dir()
    link.parent.mkdir(parents=True, exist_ok=True)
    if link.exists():
        print(f"已存在，跳过: {link}")
        print("如需改指向，请先删除该 junction 目录后再运行本脚本。")
        return
    subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(link), str(target)],
        check=True,
    )
    print(f"已创建 junction:\n  {link}\n-> {target}")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        print(f"mklink 失败: {e}", file=sys.stderr)
        sys.exit(1)
