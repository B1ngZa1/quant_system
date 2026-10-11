# 照片转 3D 可选管线状态

该管线是演示/地理资产工具，不是量化交易核心依赖，也不会被加入 FastAPI、前端或交易数据目录。

## 已装备

- Open3D `0.20.0`：安装在项目外部隔离环境 `C:\University\Code_total\quant_photo3d_env`。
- Python：3.12.6。
- 许可证：MIT。
- Smoke test：创建球体、计算顶点法线成功，输出 `vertices=762`。
- `gis-drone-reality-mapping` Codex Skill：从 `bestagentkits/agency-skills` 的 `skills/gis/gis-drone-reality-mapping` 安装至 `C:\Users\14012\.codex\skills\gis-drone-reality-mapping`，记录的上游 `main` 提交为 `a837f9f81a4dc42b58a9ba87ab65e5110112a9c8`。已核对仓库 MIT 许可证与 Skill 内容；它仅提供现实建模工作流说明，不携带可执行脚本、行情源或交易能力。

验证命令：

```powershell
C:\University\Code_total\quant_photo3d_env\Scripts\python.exe -c "import open3d as o3d; m=o3d.geometry.TriangleMesh.create_sphere(); m.compute_vertex_normals(); print(o3d.__version__, len(m.vertices))"
```

## 尚未装备

- COLMAP：未安装。建议有真实照片数据后再使用 Windows 预编译包，先做稀疏重建 smoke test。
- Nerfstudio：未安装。Windows/WSL2 和 CUDA 依赖较重；本机 RTX 4060 8GB 仅适合小型 `nerfacto` 试验，不应在没有照片数据时部署。

## 安全边界

- 原始照片、点云、网格和模型缓存放在项目外部临时目录，避免进入 `backend/`、`frontend/`、`daily_data/` 或交易数据库。
- 不从单张 K 线截图推断“3D 市场结构”；市场研究只使用结构化行情和可追溯数据。
- 使用 COLMAP/Nerfstudio 前需固定版本、记录第三方依赖许可证并核验 GPU/磁盘空间。
- 新安装 Skill 只能用于照片/视频到点云、网格、正射影像等可选演示资产；不得用于推断行情、执行订单或访问账户。
