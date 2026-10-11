"""AI智能API - DeepSeek与事件分析链路。"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.deps import get_current_user
from app.schemas.base import DataResponse
from app.services.ai_analysis_service import ai_analysis_service

router = APIRouter()


class StrategySuggestionRequest(BaseModel):
    """策略建议请求"""
    strategy_type: str = Field(..., description="策略类型")
    description: Optional[str] = Field(None, description="策略描述或需求")
    symbols: list = Field(default_factory=list, description="关注的股票代码")
    risk_preference: str = Field("medium", description="风险偏好: low/medium/high")


class CodeOptimizationRequest(BaseModel):
    """代码优化请求"""
    code: str = Field(..., description="需要优化的策略代码")
    optimization_goal: Optional[str] = Field(None, description="优化目标")


class MarketAnalysisRequest(BaseModel):
    """市场分析请求"""
    symbols: list = Field(default_factory=list, description="要分析的股票代码")
    analysis_type: str = Field("technical", description="分析类型: technical/fundamental/sentiment")


class EventAnalysisRequest(BaseModel):
    """事件分析请求。"""

    event_text: str = Field(..., min_length=20, description="新闻或事件文本")
    symbol: Optional[str] = Field(None, description="关联股票代码")


class BacktestInterpretRequest(BaseModel):
    """回测解读请求。"""

    strategy_name: str = Field(..., description="策略名称")
    total_return: float = Field(..., description="总收益率(%)")
    annual_return: float = Field(..., description="年化收益率(%)")
    max_drawdown: float = Field(..., description="最大回撤(%)")
    sharpe_ratio: float = Field(..., description="夏普比率")
    win_rate: float = Field(..., description="胜率(%)")


class NL2StrategyRequest(BaseModel):
    """自然语言生成策略代码请求。"""

    prompt: str = Field(
        ...,
        min_length=5,
        max_length=2000,
        description="用自然语言描述你想要的交易策略，例如：用20日和60日均线金叉死叉做多空切换，止损3%",
    )
    symbols: list[str] = Field(default_factory=list, description="可选，指定策略关注的股票代码")
    risk_level: str = Field("medium", description="风险偏好: low/medium/high")


class NL2StrategyResponse(BaseModel):
    """自然语言生成策略代码响应。"""

    code: str = Field(..., description="生成的策略Python代码")
    explanation: str = Field("", description="策略逻辑的文字说明")
    provider: str = Field("deepseek", description="生成来源: deepseek / fallback")


@router.post("/strategy/suggest", response_model=DataResponse[dict])
async def suggest_strategy(
    request: StrategySuggestionRequest, current_user=Depends(get_current_user)
) -> Any:
    """AI策略建议。"""
    symbols = request.symbols or ["000001", "600519", "300750"]
    prompt = (
        f"策略类型: {request.strategy_type}\n"
        f"风险偏好: {request.risk_preference}\n"
        f"关注标的: {', '.join(symbols)}\n"
        f"用户需求: {request.description or '稳健增厚收益'}\n"
        "请输出: 核心逻辑、入场条件、风控规则、参数建议。"
    )
    deepseek_text = await ai_analysis_service.ask_deepseek(
        "你是资深量化研究员，请给出结构化、可执行的策略建议。", prompt
    )
    if deepseek_text:
        return DataResponse(
            data={
                "provider": "deepseek",
                "suggestion": deepseek_text,
                "strategy_outline": None,
                "code_template": None,
            }
        )

    return DataResponse(
        data={
            "provider": "rule-based",
            "suggestion": "基于中等风险偏好，建议采用趋势+风控约束的行业轮动策略。",
            "strategy_outline": {
                "name": "动量轮动+回撤保护",
                "description": "以20/60日动量筛选强势资产，结合波动率控制仓位",
                "entry_rules": [
                    "近20日动量进入前30%且放量时开仓",
                    "价格跌破20日均线或动量掉出前50%时减仓/平仓",
                ],
                "risk_management": [
                    "单票风险预算不超过净值2%",
                    "组合最大回撤阈值-8%，触发后整体降仓到40%",
                ],
                "suggested_symbols": symbols,
            },
            "code_template": """
def initialize(context):
    set_benchmark('000001.SH')
    set_commission(0.0003)
    set_slippage(0.001)

def handle_data(context, data):
    for symbol in context.symbols:
        hist = data.history(symbol, 'close', 30, '1d')
        ma5 = hist[-5:].mean()
        ma20 = hist.mean()
        position = context.portfolio.positions.get(symbol)
        if ma5 > ma20 and not position:
            order_target_percent(symbol, 0.2)
        elif ma5 < ma20 and position:
            order_target_percent(symbol, 0)
"""
        }
    )


_NL2STRATEGY_SYSTEM_PROMPT = """\
你是一位资深量化策略工程师。用户会用自然语言描述一个交易策略，你需要把它转化为可运行的 Python 策略代码。

## 框架约束

你生成的代码必须严格遵循以下框架规范：

1. 代码中必须定义 `initialize(context)` 和 `handle_data(context, data)` 两个函数。
2. `initialize(context)` 用于初始化配置：
   - `set_benchmark('000001.SH')` 设置基准
   - `set_commission(0.0003)` 设置佣金
   - `set_slippage(0.001)` 设置滑点
   - 在 `context` 上挂载自定义参数，如 `context.symbols = [...]`
3. `handle_data(context, data)` 每个交易日调用一次：
   - `data.history(symbol, field, count, frequency)` 获取历史数据
     - `field`: 'open', 'high', 'low', 'close', 'volume'
     - `frequency`: '1d' (日线), '1m' (分钟线)
   - `context.portfolio.positions.get(symbol)` 查询持仓
   - `context.portfolio.positions[symbol].amount` 查询持仓数量
   - `context.portfolio.total_value` 查询组合总市值
   - `context.portfolio.available_cash` 查询可用现金
   - `order(symbol, amount)` 下单（正数买入，负数卖出）
   - `order_target_percent(symbol, percent)` 按目标仓位比例下单
   - `order_target_value(symbol, value)` 按目标金额下单

## 输出格式要求

1. 只输出 Python 代码，不要包含任何 markdown 标记（不要用 ```python``` 包裹）。
2. 代码应包含简洁的中文注释说明关键逻辑。
3. 代码应可直接运行，无语法错误。
4. 风控措施（止损/止盈/仓位上限）必须内嵌在代码中。
5. 如果用户未指定股票代码，使用 `context.symbols` 作为占位并在 `initialize` 中给出示例列表。
"""


@router.post("/strategy/generate", response_model=DataResponse[dict])
async def generate_strategy_code(
    request: NL2StrategyRequest, current_user=Depends(get_current_user)
) -> Any:
    """自然语言转策略代码：输入策略描述，输出可运行的 Python 策略代码。"""
    _ = current_user
    symbols_hint = ""
    if request.symbols:
        symbols_hint = f"\n用户指定的股票代码: {', '.join(request.symbols)}"

    user_prompt = (
        f"请根据以下描述生成策略代码：\n\n"
        f"{request.prompt}\n"
        f"风险偏好: {request.risk_level}{symbols_hint}"
    )

    generated_code = await ai_analysis_service.ask_deepseek(
        _NL2STRATEGY_SYSTEM_PROMPT, user_prompt
    )

    if generated_code:
        # 去除可能的 markdown 代码块包裹
        code = generated_code.strip()
        if code.startswith("```"):
            # 移除首行 ```python 或 ```
            first_newline = code.index("\n")
            code = code[first_newline + 1 :]
        if code.endswith("```"):
            code = code[: code.rfind("```")].rstrip()
        return DataResponse(
            data=NL2StrategyResponse(
                code=code,
                explanation="策略代码已根据自然语言描述生成，请在回测环境中验证后再实盘使用。",
                provider="deepseek",
            ).model_dump()
        )

    # DeepSeek 不可用时的降级响应
    fallback_code = """\
def initialize(context):
    set_benchmark('000001.SH')
    set_commission(0.0003)
    set_slippage(0.001)
    context.symbols = ['000001', '600519']
    context.ma_short = 20
    context.ma_long = 60
    context.stop_loss = 0.03

def handle_data(context, data):
    for symbol in context.symbols:
        hist = data.history(symbol, 'close', context.ma_long + 5, '1d')
        ma_short = hist[-context.ma_short:].mean()
        ma_long = hist.mean()
        position = context.portfolio.positions.get(symbol)

        if ma_short > ma_long and not position:
            # 金叉开仓
            order_target_percent(symbol, 0.5 / len(context.symbols))
        elif ma_short < ma_long and position:
            # 死叉平仓
            order_target_percent(symbol, 0)
        elif position:
            # 止损检查
            cost_price = position.avg_cost
            current_price = hist.iloc[-1]
            if (current_price - cost_price) / cost_price <= -context.stop_loss:
                order_target_percent(symbol, 0)
"""
    return DataResponse(
        data=NL2StrategyResponse(
            code=fallback_code.strip(),
            explanation="未配置 DeepSeek API Key，返回示例策略代码。请配置后重试以获得基于您描述生成的定制代码。",
            provider="fallback",
        ).model_dump()
    )


@router.post("/code/optimize", response_model=DataResponse[dict])
async def optimize_code(
    request: CodeOptimizationRequest, current_user=Depends(get_current_user)
) -> Any:
    """AI代码优化。"""
    prompt = (
        f"优化目标: {request.optimization_goal or '提高性能和可读性'}\n"
        f"代码:\n{request.code}\n"
        "请输出优化后的代码和3条改进说明。"
    )
    deepseek_text = await ai_analysis_service.ask_deepseek(
        "你是Python量化策略工程师，擅长可读性与性能优化。", prompt
    )
    if deepseek_text:
        return DataResponse(
            data={
                "provider": "deepseek",
                "optimized_code": deepseek_text,
                "suggestions": [],
                "explanation": "AI优化完成",
            }
        )

    return DataResponse(
        data={
            "provider": "rule-based",
            "optimized_code": request.code,
            "suggestions": [
                "优先使用向量化/批处理减少 Python 循环",
                "加入参数边界校验与异常回退",
                "将常量配置抽离，避免硬编码",
            ],
            "explanation": "未配置DeepSeek，返回本地优化建议",
        }
    )


@router.post("/market/analyze", response_model=DataResponse[dict])
async def analyze_market(
    request: MarketAnalysisRequest, current_user=Depends(get_current_user)
) -> Any:
    """AI市场分析。"""
    symbols_str = ", ".join(request.symbols) if request.symbols else "主要指数"
    return DataResponse(
        data={
            "analysis": f"对{symbols_str}的{request.analysis_type}分析",
            "summary": "市场仍在博弈区间，短线交易应重视风险预算。",
            "key_points": ["趋势分化明显", "量能恢复不足", "事件驱动增强波动"],
            "recommendations": ["仓位分层", "回撤止损", "优先高流动性标的"],
        }
    )


@router.post("/event/analyze", response_model=DataResponse[dict])
async def analyze_event(
    request: EventAnalysisRequest, current_user=Depends(get_current_user)
) -> Any:
    """事件分析链路：熵值 + 情绪 + CAR。"""
    entropy_score = ai_analysis_service.calc_entropy(request.event_text)
    sentiment_result = ai_analysis_service.calc_sentiment(request.event_text)
    car_result = ai_analysis_service.calc_car(sentiment_result["score"], entropy_score)
    report = ai_analysis_service.build_event_report(
        request.event_text, entropy_score, sentiment_result, car_result
    )

    deepseek_comment = await ai_analysis_service.ask_deepseek(
        "你是事件驱动策略研究员，请结合熵值、情绪、CAR给出交易建议。",
        (
            f"事件文本: {request.event_text}\n"
            f"熵值: {entropy_score}\n"
            f"情绪: {sentiment_result}\n"
            f"CAR: {car_result}\n"
            "请输出: 结论、逻辑、执行建议。"
        ),
    )
    report["symbol"] = request.symbol
    report["llm_commentary"] = deepseek_comment or "未配置DeepSeek，使用本地规则生成分析报告。"

    return DataResponse(data=report)


@router.post("/backtest/interpret", response_model=DataResponse[dict])
async def interpret_backtest(
    request: BacktestInterpretRequest, current_user=Depends(get_current_user)
) -> Any:
    """回测解读：指标总结 + 风险建议。"""
    prompt = (
        f"策略: {request.strategy_name}\n"
        f"总收益率: {request.total_return}%\n"
        f"年化收益率: {request.annual_return}%\n"
        f"最大回撤: {request.max_drawdown}%\n"
        f"夏普比率: {request.sharpe_ratio}\n"
        f"胜率: {request.win_rate}%\n"
        "请输出: 一段总体评价 + 3条改进建议。"
    )
    deepseek_text = await ai_analysis_service.ask_deepseek(
        "你是量化投研负责人，请解读回测表现并给出下一步优化方向。", prompt
    )

    if not deepseek_text:
        deepseek_text = (
            f"{request.strategy_name} 当前收益表现{request.total_return:.2f}% ，"
            f"最大回撤{request.max_drawdown:.2f}%。建议优先优化止损与仓位控制。"
        )
    return DataResponse(
        data={
            "strategy_name": request.strategy_name,
            "interpretation": deepseek_text,
            "metrics": request.model_dump(),
        }
    )


@router.get("/sentiment/analyze", response_model=DataResponse[dict])
async def analyze_sentiment(
    text: str, current_user=Depends(get_current_user)
) -> Any:
    """情绪分析。"""
    result = ai_analysis_service.calc_sentiment(text)
    label_map = {"positive": "积极", "negative": "消极", "neutral": "中性"}
    return DataResponse(
        data={
            "sentiment": result["label"],
            "score": result["score"],
            "label": label_map[result["label"]],
            "confidence": result["confidence"],
            "keywords": [],
        }
    )


@router.get("/list", response_model=DataResponse[dict])
async def list_items(current_user=Depends(get_current_user)) -> Any:
    """标准化接口：能力列表。"""
    _ = current_user
    return DataResponse(
        data={
            "items": [
                "strategy/suggest",
                "strategy/generate",
                "code/optimize",
                "market/analyze",
                "event/analyze",
                "backtest/interpret",
                "sentiment/analyze",
            ]
        }
    )


@router.get("/detail/{capability}", response_model=DataResponse[dict])
async def detail_item(capability: str, current_user=Depends(get_current_user)) -> Any:
    """标准化接口：能力详情。"""
    _ = current_user
    return DataResponse(data={"capability": capability, "enabled": True})


@router.post("/create", response_model=DataResponse[dict])
async def create_item(current_user=Depends(get_current_user)) -> Any:
    """标准化接口：创建 AI 任务。"""
    _ = current_user
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="AI 任务创建接口尚未实现",
    )


@router.post("/action/{action_name}", response_model=DataResponse[dict])
async def action_item(action_name: str, current_user=Depends(get_current_user)) -> Any:
    """标准化接口：动作入口。"""
    _ = current_user
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=f"动作 '{action_name}' 尚未实现",
    )


@router.put("/update/{capability}", response_model=DataResponse[dict])
@router.patch("/update/{capability}", response_model=DataResponse[dict])
async def update_item(capability: str, current_user=Depends(get_current_user)) -> Any:
    """标准化接口：更新能力配置。"""
    _ = current_user
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=f"更新能力 '{capability}' 的接口尚未实现",
    )


@router.delete("/remove/{capability}", response_model=DataResponse[dict])
async def remove_item(capability: str, current_user=Depends(get_current_user)) -> Any:
    """标准化接口：删除能力配置。"""
    _ = current_user
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=f"删除能力 '{capability}' 的接口尚未实现",
    )
