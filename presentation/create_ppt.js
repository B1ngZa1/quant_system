const PptxGenJS = require("pptxgenjs");

const pptx = new PptxGenJS();

// 简约配色方案 - 深蓝灰为主
const COLORS = {
  primary: "2C3E50",    // 深蓝灰
  secondary: "34495E",  // 中蓝灰
  accent: "3498DB",     // 蓝色点缀
  text: "2C3E50",       // 深色文字
  lightText: "7F8C8D",  // 浅灰文字
  white: "FFFFFF",
  bgLight: "F8F9FA",    // 浅灰背景
  border: "BDC3C7"      // 边框灰
};

// 设置默认字体
pptx.defineSlideMaster({
  title: "MASTER_SLIDE",
  background: { color: COLORS.white }
});

// ========== 第1页：封面 ==========
const slide1 = pptx.addSlide();
slide1.background = { color: COLORS.primary };
slide1.addText("Quant System v4.1.0", {
  x: 0.5, y: 2.5, w: 9, h: 1,
  fontSize: 44, bold: true, color: COLORS.white,
  fontFace: "Microsoft YaHei", align: "center"
});
slide1.addText("全栈量化交易平台", {
  x: 0.5, y: 3.5, w: 9, h: 0.6,
  fontSize: 24, color: "BDC3C7",
  fontFace: "Microsoft YaHei", align: "center"
});
slide1.addText("Vue 3 + FastAPI | A股/港股/美股", {
  x: 0.5, y: 4.2, w: 9, h: 0.5,
  fontSize: 16, color: "95A5A6",
  fontFace: "Microsoft YaHei", align: "center"
});

// ========== 第2页：目录 ==========
const slide2 = pptx.addSlide();
slide2.addText("目录", {
  x: 0.5, y: 0.5, w: 9, h: 0.8,
  fontSize: 32, bold: true, color: COLORS.primary,
  fontFace: "Microsoft YaHei"
});
const tocItems = [
  "01  项目概述",
  "02  系统架构",
  "03  核心功能模块",
  "04  统计与量化方法",
  "05  项目演示"
];
tocItems.forEach((item, i) => {
  slide2.addText(item, {
    x: 1, y: 1.6 + i * 0.9, w: 8, h: 0.6,
    fontSize: 18, color: COLORS.text,
    fontFace: "Microsoft YaHei"
  });
  slide2.addShape(pptx.ShapeType.line, {
    x: 1, y: 2.1 + i * 0.9, w: 8, h: 0,
    line: { color: COLORS.border, width: 0.5 }
  });
});

// ========== 第3页：项目概述 ==========
const slide3 = pptx.addSlide();
slide3.addText("01  项目概述", {
  x: 0.5, y: 0.5, w: 9, h: 0.8,
  fontSize: 28, bold: true, color: COLORS.primary,
  fontFace: "Microsoft YaHei"
});
slide3.addText("Quant System 是一个面向多市场的全栈量化交易平台，支持A股、港股、美股的数据获取、策略开发与交易执行。", {
  x: 0.5, y: 1.5, w: 9, h: 1,
  fontSize: 14, color: COLORS.text,
  fontFace: "Microsoft YaHei"
});
// 技术栈
slide3.addText("技术栈", {
  x: 0.5, y: 2.6, w: 4, h: 0.5,
  fontSize: 16, bold: true, color: COLORS.secondary,
  fontFace: "Microsoft YaHei"
});
const techStack = [
  "前端：Vue 3 + TypeScript + Element Plus",
  "后端：FastAPI + SQLAlchemy + Alembic",
  "数据：AKShare + Tushare + 本地数据库",
  "部署：Docker + Redis"
];
techStack.forEach((item, i) => {
  slide3.addText("• " + item, {
    x: 0.7, y: 3.1 + i * 0.45, w: 8.5, h: 0.4,
    fontSize: 13, color: COLORS.text,
    fontFace: "Microsoft YaHei"
  });
});
// 市场覆盖
slide3.addText("市场覆盖", {
  x: 5.5, y: 2.6, w: 4, h: 0.5,
  fontSize: 16, bold: true, color: COLORS.secondary,
  fontFace: "Microsoft YaHei"
});
const markets = [
  "A股：沪深主板、科创板、创业板",
  "港股：恒生指数成分股",
  "美股：纳斯达克、道琼斯"
];
markets.forEach((item, i) => {
  slide3.addText("• " + item, {
    x: 5.7, y: 3.1 + i * 0.45, w: 4, h: 0.4,
    fontSize: 13, color: COLORS.text,
    fontFace: "Microsoft YaHei"
  });
});

// ========== 第4页：系统架构 ==========
const slide4 = pptx.addSlide();
slide4.addText("02  系统架构", {
  x: 0.5, y: 0.5, w: 9, h: 0.8,
  fontSize: 28, bold: true, color: COLORS.primary,
  fontFace: "Microsoft YaHei"
});
// 架构图（简化版）
const layers = [
  { y: 1.8, label: "前端层", desc: "Vue3 + Element Plus | 行情/策略/交易界面", color: "E8F4FD" },
  { y: 2.8, label: "API网关层", desc: "FastAPI | JWT认证/限流/路由", color: "D5E8D4" },
  { y: 3.8, label: "业务逻辑层", desc: "行情引擎/策略管理/回测系统/交易撮合", color: "FFF2CC" },
  { y: 4.8, label: "数据层", desc: "MySQL + Redis | AKShare/Tushare数据源", color: "F8CECC" }
];
layers.forEach(layer => {
  slide4.addShape(pptx.ShapeType.rect, {
    x: 0.5, y: layer.y, w: 9, h: 0.8,
    fill: { color: layer.color },
    line: { color: COLORS.border, width: 1 }
  });
  slide4.addText(layer.label, {
    x: 0.7, y: layer.y + 0.15, w: 1.5, h: 0.5,
    fontSize: 14, bold: true, color: COLORS.text,
    fontFace: "Microsoft YaHei"
  });
  slide4.addText(layer.desc, {
    x: 2.3, y: layer.y + 0.2, w: 7, h: 0.4,
    fontSize: 12, color: COLORS.lightText,
    fontFace: "Microsoft YaHei"
  });
});

// ========== 第5页：核心功能 - 行情数据引擎 ==========
const slide5 = pptx.addSlide();
slide5.addText("03  核心功能模块", {
  x: 0.5, y: 0.5, w: 9, h: 0.8,
  fontSize: 28, bold: true, color: COLORS.primary,
  fontFace: "Microsoft YaHei"
});
slide5.addText("行情数据引擎", {
  x: 0.5, y: 1.4, w: 9, h: 0.6,
  fontSize: 20, bold: true, color: COLORS.secondary,
  fontFace: "Microsoft YaHei"
});
slide5.addText("多级数据源优先级策略，确保行情数据的实时性与可靠性", {
  x: 0.5, y: 1.9, w: 9, h: 0.4,
  fontSize: 13, color: COLORS.lightText,
  fontFace: "Microsoft YaHei"
});
// 数据源优先级
const dataSources = [
  { level: "1", name: "本地数据库（新鲜）", desc: "优先使用当日同步的本地数据" },
  { level: "2", name: "AKShare", desc: "实时抓取东方财富等数据源" },
  { level: "3", name: "本地数据库（兜底）", desc: "使用缓存的历史数据" },
  { level: "4", name: "CSV文件", desc: "离线数据文件作为最终备选" }
];
dataSources.forEach((ds, i) => {
  slide5.addShape(pptx.ShapeType.rect, {
    x: 0.5 + i * 2.3, y: 2.6, w: 2.1, h: 2.5,
    fill: { color: i === 0 ? "E8F4FD" : (i === 1 ? "D5E8D4" : (i === 2 ? "FFF2CC" : "F8CECC")) },
    line: { color: COLORS.border, width: 1 }
  });
  slide5.addText(ds.level, {
    x: 0.5 + i * 2.3, y: 2.75, w: 2.1, h: 0.5,
    fontSize: 28, bold: true, color: COLORS.accent, align: "center",
    fontFace: "Microsoft YaHei"
  });
  slide5.addText(ds.name, {
    x: 0.6 + i * 2.3, y: 3.4, w: 1.9, h: 0.6,
    fontSize: 11, bold: true, color: COLORS.text, align: "center",
    fontFace: "Microsoft YaHei"
  });
  slide5.addText(ds.desc, {
    x: 0.6 + i * 2.3, y: 4.0, w: 1.9, h: 0.8,
    fontSize: 10, color: COLORS.lightText, align: "center",
    fontFace: "Microsoft YaHei"
  });
});

// ========== 第6页：核心功能 - 策略管理 ==========
const slide6 = pptx.addSlide();
slide6.addText("策略管理", {
  x: 0.5, y: 0.5, w: 9, h: 0.8,
  fontSize: 20, bold: true, color: COLORS.secondary,
  fontFace: "Microsoft YaHei"
});
const strategyFeatures = [
  { title: "策略CRUD", desc: "创建、编辑、删除策略，支持版本管理" },
  { title: "参数配置", desc: "可视化配置策略参数，实时生效" },
  { title: "状态切换", desc: "启用/停用策略，支持批量操作" },
  { title: "策略分类", desc: "按市场、类型、风险等级分类管理" }
];
strategyFeatures.forEach((feat, i) => {
  const row = Math.floor(i / 2);
  const col = i % 2;
  slide6.addShape(pptx.ShapeType.rect, {
    x: 0.5 + col * 4.6, y: 1.5 + row * 2.2, w: 4.4, h: 1.9,
    fill: { color: COLORS.bgLight },
    line: { color: COLORS.border, width: 1 }
  });
  slide6.addText(feat.title, {
    x: 0.7 + col * 4.6, y: 1.7 + row * 2.2, w: 4, h: 0.5,
    fontSize: 16, bold: true, color: COLORS.primary,
    fontFace: "Microsoft YaHei"
  });
  slide6.addText(feat.desc, {
    x: 0.7 + col * 4.6, y: 2.2 + row * 2.2, w: 4, h: 1,
    fontSize: 12, color: COLORS.text,
    fontFace: "Microsoft YaHei"
  });
});

// ========== 第7页：核心功能 - 回测系统 ==========
const slide7 = pptx.addSlide();
slide7.addText("回测系统", {
  x: 0.5, y: 0.5, w: 9, h: 0.8,
  fontSize: 20, bold: true, color: COLORS.secondary,
  fontFace: "Microsoft YaHei"
});
slide7.addText("模拟回测流程，验证策略有效性", {
  x: 0.5, y: 1.2, w: 9, h: 0.4,
  fontSize: 13, color: COLORS.lightText,
  fontFace: "Microsoft YaHei"
});
// 回测流程
const backtestSteps = [
  { step: "1", name: "数据准备", detail: "加载历史行情数据\n支持日线/分钟线" },
  { step: "2", name: "策略执行", detail: "按时间序列模拟交易\n生成买卖信号" },
  { step: "3", name: "撮合计算", detail: "模拟成交价格\n计算手续费/滑点" },
  { step: "4", name: "结果分析", detail: "收益率/最大回撤\n夏普比率等指标" }
];
backtestSteps.forEach((s, i) => {
  slide7.addShape(pptx.ShapeType.ellipse, {
    x: 0.8 + i * 2.3, y: 2, w: 1.2, h: 1.2,
    fill: { color: COLORS.accent }
  });
  slide7.addText(s.step, {
    x: 0.8 + i * 2.3, y: 2.35, w: 1.2, h: 0.5,
    fontSize: 28, bold: true, color: COLORS.white, align: "center",
    fontFace: "Microsoft YaHei"
  });
  slide7.addText(s.name, {
    x: 0.5 + i * 2.3, y: 3.4, w: 1.8, h: 0.4,
    fontSize: 14, bold: true, color: COLORS.text, align: "center",
    fontFace: "Microsoft YaHei"
  });
  slide7.addText(s.detail, {
    x: 0.4 + i * 2.3, y: 3.9, w: 2, h: 1,
    fontSize: 10, color: COLORS.lightText, align: "center",
    fontFace: "Microsoft YaHei"
  });
  if (i < 3) {
    slide7.addShape(pptx.ShapeType.rightArrow, {
      x: 2.1 + i * 2.3, y: 2.4, w: 0.6, h: 0.4,
      fill: { color: COLORS.border }
    });
  }
});

// ========== 第8页：核心功能 - 交易系统 ==========
const slide8 = pptx.addSlide();
slide8.addText("交易系统", {
  x: 0.5, y: 0.5, w: 9, h: 0.8,
  fontSize: 20, bold: true, color: COLORS.secondary,
  fontFace: "Microsoft YaHei"
});
// 模拟盘
slide8.addShape(pptx.ShapeType.rect, {
  x: 0.5, y: 1.5, w: 4.4, h: 3.5,
  fill: { color: "E8F4FD" },
  line: { color: COLORS.border, width: 1 }
});
slide8.addText("模拟盘", {
  x: 0.7, y: 1.7, w: 4, h: 0.5,
  fontSize: 18, bold: true, color: COLORS.primary,
  fontFace: "Microsoft YaHei"
});
slide8.addText("• 组合管理\n• 下单/撤单\n• 模拟撮合\n• 持仓更新\n• 盈亏计算", {
  x: 0.7, y: 2.3, w: 4, h: 2,
  fontSize: 13, color: COLORS.text,
  fontFace: "Microsoft YaHei"
});
// 实盘（骨架）
slide8.addShape(pptx.ShapeType.rect, {
  x: 5.1, y: 1.5, w: 4.4, h: 3.5,
  fill: { color: "FFF2CC" },
  line: { color: COLORS.border, width: 1 }
});
slide8.addText("实盘（骨架）", {
  x: 5.3, y: 1.7, w: 4, h: 0.5,
  fontSize: 18, bold: true, color: COLORS.primary,
  fontFace: "Microsoft YaHei"
});
slide8.addText("• 券商网关接口\n• 风控审计\n• 成交回报对账\n• 资金划拨\n• 待完善...", {
  x: 5.3, y: 2.3, w: 4, h: 2,
  fontSize: 13, color: COLORS.lightText,
  fontFace: "Microsoft YaHei"
});

// ========== 第9页：统计与量化方法 ==========
const slide9 = pptx.addSlide();
slide9.addText("04  统计与量化方法", {
  x: 0.5, y: 0.5, w: 9, h: 0.8,
  fontSize: 28, bold: true, color: COLORS.primary,
  fontFace: "Microsoft YaHei"
});
slide9.addText("基于MCM竞赛经验与统计学习方法构建的策略体系", {
  x: 0.5, y: 1.3, w: 9, h: 0.4,
  fontSize: 13, color: COLORS.lightText,
  fontFace: "Microsoft YaHei"
});
// 方法分类
const methods = [
  { name: "回归与预测", items: ["线性回归", "鲁棒回归 (RANSAC)", "ARIMA时间序列"] },
  { name: "技术指标", items: ["移动平均线 (MA)", "相对强弱指标 (RSI)", "波动率 (Volatility)"] },
  { name: "网格策略", items: ["等差/等比网格", "自适应网格 (APGM)", "动态边界调整"] },
  { name: "风险管理", items: ["止损止盈", "仓位管理", "极端行情保护"] }
];
methods.forEach((m, i) => {
  const col = i % 2;
  const row = Math.floor(i / 2);
  slide9.addShape(pptx.ShapeType.rect, {
    x: 0.5 + col * 4.6, y: 1.9 + row * 2.3, w: 4.4, h: 2.1,
    fill: { color: COLORS.bgLight },
    line: { color: COLORS.border, width: 1 }
  });
  slide9.addText(m.name, {
    x: 0.7 + col * 4.6, y: 2.05 + row * 2.3, w: 4, h: 0.4,
    fontSize: 15, bold: true, color: COLORS.secondary,
    fontFace: "Microsoft YaHei"
  });
  m.items.forEach((item, j) => {
    slide9.addText("• " + item, {
      x: 0.8 + col * 4.6, y: 2.5 + row * 2.3 + j * 0.4, w: 4, h: 0.35,
      fontSize: 12, color: COLORS.text,
      fontFace: "Microsoft YaHei"
    });
  });
});

// ========== 第10页：MCM经验 - 自适应网格模型 ==========
const slide10 = pptx.addSlide();
slide10.addText("APGM 自适应周期性网格模型", {
  x: 0.5, y: 0.5, w: 9, h: 0.8,
  fontSize: 20, bold: true, color: COLORS.secondary,
  fontFace: "Microsoft YaHei"
});
slide10.addText("2022 MCM C题比特币与黄金交易策略的核心模型", {
  x: 0.5, y: 1.2, w: 9, h: 0.4,
  fontSize: 13, color: COLORS.lightText,
  fontFace: "Microsoft YaHei"
});
// 核心思想
slide10.addShape(pptx.ShapeType.rect, {
  x: 0.5, y: 1.8, w: 4.4, h: 3.2,
  fill: { color: "E8F4FD" },
  line: { color: COLORS.border, width: 1 }
});
slide10.addText("核心思想", {
  x: 0.7, y: 1.95, w: 4, h: 0.4,
  fontSize: 15, bold: true, color: COLORS.primary,
  fontFace: "Microsoft YaHei"
});
slide10.addText("传统网格策略在单边行情中失效：", {
  x: 0.7, y: 2.4, w: 4, h: 0.35,
  fontSize: 12, color: COLORS.text,
  fontFace: "Microsoft YaHei"
});
slide10.addText("• 单边上涨：涨破上限后踏空\n• 单边下跌：接飞刀被套牢", {
  x: 0.8, y: 2.8, w: 4, h: 0.8,
  fontSize: 11, color: COLORS.lightText,
  fontFace: "Microsoft YaHei"
});
slide10.addText("APGM解决方案：", {
  x: 0.7, y: 3.7, w: 4, h: 0.35,
  fontSize: 12, color: COLORS.text,
  fontFace: "Microsoft YaHei"
});
slide10.addText("• 网格随趋势动态调整\n• ARIMA预测趋势方向\n• MA平滑噪声", {
  x: 0.8, y: 4.1, w: 4, h: 0.8,
  fontSize: 11, color: COLORS.lightText,
  fontFace: "Microsoft YaHei"
});
// 效果
slide10.addShape(pptx.ShapeType.rect, {
  x: 5.1, y: 1.8, w: 4.4, h: 3.2,
  fill: { color: "D5E8D4" },
  line: { color: COLORS.border, width: 1 }
});
slide10.addText("实际效果", {
  x: 5.3, y: 1.95, w: 4, h: 0.4,
  fontSize: 15, bold: true, color: COLORS.primary,
  fontFace: "Microsoft YaHei"
});
slide10.addText("2016.9 - 2021.9 回测结果：", {
  x: 5.3, y: 2.4, w: 4, h: 0.35,
  fontSize: 12, color: COLORS.text,
  fontFace: "Microsoft YaHei"
});
slide10.addText("初始资金: $1,000", {
  x: 5.5, y: 2.85, w: 4, h: 0.35,
  fontSize: 12, color: COLORS.text,
  fontFace: "Microsoft YaHei"
});
slide10.addText("最终资产: $147,182", {
  x: 5.5, y: 3.25, w: 4, h: 0.4,
  fontSize: 16, bold: true, color: "27AE60",
  fontFace: "Microsoft YaHei"
});
slide10.addText("收益率: 14,618%", {
  x: 5.5, y: 3.75, w: 4, h: 0.4,
  fontSize: 16, bold: true, color: "27AE60",
  fontFace: "Microsoft YaHei"
});

// ========== 第11页：特征工程 ==========
const slide11 = pptx.addSlide();
slide11.addText("特征工程", {
  x: 0.5, y: 0.5, w: 9, h: 0.8,
  fontSize: 20, bold: true, color: COLORS.secondary,
  fontFace: "Microsoft YaHei"
});
const features = [
  { name: "MA30", type: "趋势指标", usage: "Price > MA: 牛市，偏向买入\nPrice < MA: 熊市，偏向卖出" },
  { name: "Volatility", type: "风险指标", usage: "波动大 → 网格放宽\n波动小 → 网格收紧" },
  { name: "Returns", type: "速度指标", usage: "ARIMA预测的主食\n涨跌幅比价格更稳定" },
  { name: "RSI", type: "情绪指标", usage: "RSI > 80: 过热，暂停买入\nRSI < 30: 超卖，关注抄底" }
];
features.forEach((f, i) => {
  const col = i % 2;
  const row = Math.floor(i / 2);
  slide11.addShape(pptx.ShapeType.rect, {
    x: 0.5 + col * 4.6, y: 1.5 + row * 2.3, w: 4.4, h: 2.1,
    fill: { color: COLORS.bgLight },
    line: { color: COLORS.border, width: 1 }
  });
  slide11.addText(f.name, {
    x: 0.7 + col * 4.6, y: 1.65 + row * 2.3, w: 1.5, h: 0.4,
    fontSize: 18, bold: true, color: COLORS.accent,
    fontFace: "Microsoft YaHei"
  });
  slide11.addText(f.type, {
    x: 2.3 + col * 4.6, y: 1.7 + row * 2.3, w: 2.5, h: 0.35,
    fontSize: 12, color: COLORS.lightText,
    fontFace: "Microsoft YaHei"
  });
  slide11.addText(f.usage, {
    x: 0.7 + col * 4.6, y: 2.15 + row * 2.3, w: 4, h: 1.3,
    fontSize: 11, color: COLORS.text,
    fontFace: "Microsoft YaHei"
  });
});

// ========== 第12页：项目演示 ==========
const slide12 = pptx.addSlide();
slide12.background = { color: COLORS.bgLight };
slide12.addText("05  项目演示", {
  x: 0.5, y: 0.5, w: 9, h: 0.8,
  fontSize: 28, bold: true, color: COLORS.primary,
  fontFace: "Microsoft YaHei"
});
slide12.addText("演示区域", {
  x: 0.5, y: 2, w: 9, h: 1,
  fontSize: 36, bold: true, color: COLORS.border, align: "center",
  fontFace: "Microsoft YaHei"
});
slide12.addText("（此处预留项目现场演示）", {
  x: 0.5, y: 3.2, w: 9, h: 0.6,
  fontSize: 18, color: COLORS.lightText, align: "center",
  fontFace: "Microsoft YaHei"
});
slide12.addShape(pptx.ShapeType.rect, {
  x: 2, y: 4.2, w: 6, h: 0.8,
  fill: { color: COLORS.accent },
  line: { color: COLORS.accent, width: 1 }
});
slide12.addText("演示内容建议：", {
  x: 2.2, y: 4.35, w: 5.6, h: 0.5,
  fontSize: 14, color: COLORS.white, align: "center",
  fontFace: "Microsoft YaHei"
});
slide12.addText("• 行情数据实时展示  • 策略配置界面  • 回测结果分析  • 模拟交易操作", {
  x: 0.5, y: 5.2, w: 9, h: 0.5,
  fontSize: 12, color: COLORS.text, align: "center",
  fontFace: "Microsoft YaHei"
});

// ========== 第13页：总结与展望 ==========
const slide13 = pptx.addSlide();
slide13.addText("总结与展望", {
  x: 0.5, y: 0.5, w: 9, h: 0.8,
  fontSize: 28, bold: true, color: COLORS.primary,
  fontFace: "Microsoft YaHei"
});
// 已完成
slide13.addShape(pptx.ShapeType.rect, {
  x: 0.5, y: 1.5, w: 4.4, h: 3.5,
  fill: { color: "D5E8D4" },
  line: { color: COLORS.border, width: 1 }
});
slide13.addText("已完成", {
  x: 0.7, y: 1.65, w: 4, h: 0.4,
  fontSize: 16, bold: true, color: "27AE60",
  fontFace: "Microsoft YaHei"
});
slide13.addText("• 行情数据引擎（多级数据源）\n• 策略管理系统（CRUD+参数配置）\n• 回测系统（模拟撮合+指标计算）\n• 模拟交易系统（组合+下单+持仓）\n• 用户认证与API限流\n• AI辅助分析（DeepSeek接入）", {
  x: 0.7, y: 2.15, w: 4, h: 2.5,
  fontSize: 12, color: COLORS.text,
  fontFace: "Microsoft YaHei"
});
// 待完善
slide13.addShape(pptx.ShapeType.rect, {
  x: 5.1, y: 1.5, w: 4.4, h: 3.5,
  fill: { color: "FFF2CC" },
  line: { color: COLORS.border, width: 1 }
});
slide13.addText("待完善", {
  x: 5.3, y: 1.65, w: 4, h: 0.4,
  fontSize: 16, bold: true, color: "F39C12",
  fontFace: "Microsoft YaHei"
});
slide13.addText("• 实盘交易网关对接\n• 生产级风控审计系统\n• 更丰富的策略模板库\n• 机器学习策略自动生成\n• 多因子选股模型\n• 实时推送与告警系统", {
  x: 5.3, y: 2.15, w: 4, h: 2.5,
  fontSize: 12, color: COLORS.text,
  fontFace: "Microsoft YaHei"
});

// ========== 第14页：结束页 ==========
const slide14 = pptx.addSlide();
slide14.background = { color: COLORS.primary };
slide14.addText("谢谢", {
  x: 0.5, y: 2.5, w: 9, h: 1,
  fontSize: 48, bold: true, color: COLORS.white, align: "center",
  fontFace: "Microsoft YaHei"
});
slide14.addText("Quant System v4.1.0", {
  x: 0.5, y: 3.8, w: 9, h: 0.6,
  fontSize: 20, color: "BDC3C7", align: "center",
  fontFace: "Microsoft YaHei"
});
slide14.addText("Vue 3 + FastAPI 全栈量化交易平台", {
  x: 0.5, y: 4.5, w: 9, h: 0.5,
  fontSize: 14, color: "95A5A6", align: "center",
  fontFace: "Microsoft YaHei"
});

// 保存
pptx.writeFile({ fileName: "Quant_System_项目展示.pptx" })
  .then(() => console.log("PPT生成成功！"))
  .catch(err => console.error("生成失败:", err));
