"""动态策略加载器"""
import types
from typing import Type

from app.core.config import settings
from app.core.logging import log
from app.services.backtest.engine import StrategyInterface


def load_dynamic_strategy(code: str, class_name: str = "CustomStrategy") -> Type[StrategyInterface]:
    """
    动态执行 Python 代码并返回策略类
    
    Args:
        code: Python 策略源码
        class_name: 期望加载的策略类名
    """
    if not settings.ALLOW_CUSTOM_STRATEGY_CODE_EXEC:
        raise ValueError("安全策略限制：系统未开启自定义代码执行 (ALLOW_CUSTOM_STRATEGY_CODE_EXEC=False)")
        
    module_name = f"dynamic_strategy_{hash(code)}"
    
    # 创建一个新的模块
    module = types.ModuleType(module_name)
    module.__file__ = f"<dynamic_{module_name}>"
    
    # 将所需的基础依赖注入到模块中
    from app.services.backtest import engine
    from app.services.backtest import domain
    module.__dict__["StrategyInterface"] = engine.StrategyInterface
    module.__dict__["MarketData"] = domain.MarketData
    module.__dict__["OrderSide"] = domain.OrderSide
    module.__dict__["OrderType"] = domain.OrderType
    
    try:
        # 执行代码
        exec(code, module.__dict__)
        
        # 提取策略类
        strategy_class = getattr(module, class_name)
        if not issubclass(strategy_class, StrategyInterface):
            raise TypeError(f"{class_name} 必须继承自 StrategyInterface")
            
        return strategy_class
    except Exception as e:
        log.error(f"动态策略加载失败: {e}")
        raise RuntimeError(f"动态策略编译执行错误: {e}")
