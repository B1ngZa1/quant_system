-- =============================================================================
-- 初始化 PostgreSQL 扩展与配置
-- 效仿 jzhu-trading 项目的底层设计
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS timescaledb;
SET timezone = 'Asia/Shanghai';

-- 注意：业务表结构目前由 backend/alembic 自动维护。
-- 此处主要用于确保 TimescaleDB 插件被正确加载，以及可能需要补充的触发器或原生 SQL 函数。
