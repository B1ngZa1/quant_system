from dataclasses import dataclass
from typing import Optional

@dataclass
class Stock:
    symbol: str
    name: str
    exchange: str
    industry: Optional[str] = None
    list_date: Optional[str] = None
    is_active: bool = True

    def disable(self) -> None:
        """业务逻辑：退市或停牌"""
        self.is_active = False
