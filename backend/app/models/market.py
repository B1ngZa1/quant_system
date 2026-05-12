"""市场数据模型"""
from datetime import datetime, date
from typing import Optional
from decimal import Decimal
from sqlalchemy import String, DateTime, Date, Numeric, Integer, Text, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MarketSentiment(Base):
    """市场情绪表"""
    __tablename__ = "market_sentiment"
    
    # 日期
    trade_date: Mapped[date] = mapped_column(Date, unique=True, index=True, nullable=False)
    
    # 整体情绪指标
    overall_sentiment: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)  # -100 到 100
    sentiment_label: Mapped[str] = mapped_column(String(20), nullable=False)  # 极度恐慌/恐慌/中性/贪婪/极度贪婪
    
    # 细分指标
    volatility_index: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)  # 波动率指数
    market_momentum: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)  # 市场动能
    stock_price_strength: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)  # 股价强度
    stock_price_breadth: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)  # 股价广度
    put_call_ratio: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)  #  put/call 比率
    safe_haven_demand: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)  # 避险需求
    junk_bond_demand: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)  # 垃圾债需求
    
    # 涨跌统计
    advancers: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 上涨家数
    decliners: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 下跌家数
    unchanged: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 平盘家数
    
    # 数据来源和分析
    data_sources: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    analysis_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    def __repr__(self) -> str:
        return f"<MarketSentiment(date={self.trade_date}, sentiment={self.overall_sentiment})>"
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "trade_date": self.trade_date.isoformat() if self.trade_date else None,
            "overall_sentiment": float(self.overall_sentiment),
            "sentiment_label": self.sentiment_label,
            "volatility_index": float(self.volatility_index) if self.volatility_index else None,
            "market_momentum": float(self.market_momentum) if self.market_momentum else None,
            "advancers": self.advancers,
            "decliners": self.decliners,
            "analysis_summary": self.analysis_summary,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class News(Base):
    """新闻资讯表"""
    __tablename__ = "news"
    
    # 新闻标题和内容
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # 来源信息
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    source_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    author: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # 发布时间
    publish_time: Mapped[datetime] = mapped_column(DateTime, index=True, nullable=False)
    
    # 相关标的
    related_symbols: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    
    # 分类标签
    category: Mapped[str] = mapped_column(String(50), default="general", nullable=False)  # 宏观/行业/个股/公告
    tags: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    
    # 情绪分析
    sentiment: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # positive/negative/neutral
    sentiment_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4), nullable=True)  # -1 到 1
    
    # 重要性
    importance: Mapped[int] = mapped_column(Integer, default=1, nullable=False)  # 1-5
    is_urgent: Mapped[bool] = mapped_column(default=False, nullable=False)
    
    # 阅读统计
    view_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # 图片链接
    images: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    
    __table_args__ = (
        Index("ix_news_publish_category", "publish_time", "category"),
        Index("ix_news_sentiment", "sentiment"),
    )
    
    def __repr__(self) -> str:
        return f"<News(title={self.title[:30]}..., source={self.source})>"
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "summary": self.summary,
            "source": self.source,
            "source_url": self.source_url,
            "author": self.author,
            "publish_time": self.publish_time.isoformat() if self.publish_time else None,
            "related_symbols": self.related_symbols,
            "category": self.category,
            "tags": self.tags,
            "sentiment": self.sentiment,
            "sentiment_score": float(self.sentiment_score) if self.sentiment_score else None,
            "importance": self.importance,
            "is_urgent": self.is_urgent,
            "view_count": self.view_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class FundFlow(Base):
    """资金流向表"""
    __tablename__ = "fund_flow"
    
    # 标的和时间
    symbol: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    trade_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    
    # 主力流向
    main_inflow: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4), nullable=True)  # 主力流入
    main_outflow: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4), nullable=True)  # 主力流出
    main_net_flow: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4), nullable=True)  # 主力净流入
    
    # 散户流向
    retail_inflow: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4), nullable=True)
    retail_outflow: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4), nullable=True)
    retail_net_flow: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4), nullable=True)
    
    # 大单统计
    large_buy_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4), nullable=True)
    large_sell_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4), nullable=True)
    
    # 中单统计
    medium_buy_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4), nullable=True)
    medium_sell_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4), nullable=True)
    
    # 小单统计
    small_buy_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4), nullable=True)
    small_sell_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4), nullable=True)
    
    __table_args__ = (
        Index("ix_fund_flow_symbol_date", "symbol", "trade_date", unique=True),
    )
    
    def __repr__(self) -> str:
        return f"<FundFlow(symbol={self.symbol}, date={self.trade_date}, net_flow={self.main_net_flow})>"


class NewsSymbol(Base):
    """新闻-标的关联表（用于高效按标的查询关联新闻）"""
    __tablename__ = "news_symbols"

    # 新闻 ID
    news_id: Mapped[int] = mapped_column(Integer, nullable=False)
    # 标的代码
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)

    __table_args__ = (
        Index("ix_news_symbols_news_id_symbol", "news_id", "symbol", unique=True),
        Index("ix_news_symbols_symbol", "symbol"),
    )

    def __repr__(self) -> str:
        return f"<NewsSymbol(news_id={self.news_id}, symbol={self.symbol})>"
