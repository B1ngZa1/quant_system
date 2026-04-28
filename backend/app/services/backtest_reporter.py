"""
回测报告生成器

生成专业的回测分析报告，支持多种格式:
- JSON: 结构化数据
- HTML: 可视化报告
- PDF: 正式文档 (可选)
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Union
from dataclasses import dataclass



@dataclass
class ReportSection:
    """报告章节"""
    title: str
    content: Dict[str, Any]
    order: int


class BacktestReportGenerator:
    """回测报告生成器"""
    
    def __init__(self, backtest_results: Dict[str, Any]):
        self.results = backtest_results
        self.sections: List[ReportSection] = []
    
    def generate_full_report(self) -> Dict[str, Any]:
        """生成完整报告"""
        self.sections = []
        
        # 1. 执行摘要
        self._add_summary_section()
        
        # 2. 绩效指标
        self._add_performance_section()
        
        # 3. 风险分析
        self._add_risk_section()
        
        # 4. 交易分析
        self._add_trading_section()
        
        # 5. 图表数据
        self._add_charts_section()
        
        # 6. 优化建议
        self._add_recommendations_section()
        
        # 7. 回测设置
        self._add_settings_section()
        
        # 排序
        self.sections.sort(key=lambda x: x.order)
        
        return {
            "report_type": "backtest_analysis",
            "generated_at": datetime.now().isoformat(),
            "version": "2.0",
            "sections": [
                {
                    "title": section.title,
                    "content": section.content
                }
                for section in self.sections
            ],
            "summary": self._generate_executive_summary()
        }
    
    def _add_summary_section(self):
        """执行摘要"""
        metrics = self.results.get("metrics", {})
        summary = self._generate_executive_summary()
        
        content = {
            "overall_score": summary["score"],
            "score_rating": summary["rating"],
            "key_highlights": [
                f"总收益率: {metrics.get('total_return', 0):.2f}%",
                f"夏普比率: {metrics.get('sharpe_ratio', 0):.2f}",
                f"最大回撤: {metrics.get('max_drawdown', 0):.2f}%",
                f"交易次数: {metrics.get('total_trades', 0)}次"
            ],
            "verdict": summary["verdict"],
            "risk_level": summary["risk_level"]
        }
        
        self.sections.append(ReportSection(
            title="执行摘要",
            content=content,
            order=1
        ))
    
    def _generate_executive_summary(self) -> Dict[str, Any]:
        """生成执行摘要"""
        metrics = self.results.get("metrics", {})
        self.results.get("analysis", {})
        
        # 计算综合评分
        score = 0
        details = []
        
        # 收益评分 (30分)
        total_return = metrics.get("total_return", 0)
        if total_return > 50:
            score += 30
            details.append("收益优秀")
        elif total_return > 20:
            score += 20
            details.append("收益良好")
        elif total_return > 0:
            score += 10
            details.append("收益为正")
        else:
            details.append("收益为负")
        
        # 夏普评分 (25分)
        sharpe = metrics.get("sharpe_ratio", 0)
        if sharpe > 2:
            score += 25
            details.append("风险调整收益优秀")
        elif sharpe > 1:
            score += 15
            details.append("风险调整收益良好")
        elif sharpe > 0.5:
            score += 5
        
        # 回撤评分 (20分)
        drawdown = metrics.get("max_drawdown", 0)
        if drawdown < 10:
            score += 20
            details.append("风险控制优秀")
        elif drawdown < 20:
            score += 15
            details.append("风险控制良好")
        elif drawdown < 30:
            score += 5
        
        # 胜率评分 (10分)
        win_rate = metrics.get("win_rate", 0)
        if win_rate > 60:
            score += 10
            details.append("胜率较高")
        elif win_rate > 50:
            score += 5
        
        # 盈亏比评分 (15分)
        profit_factor = metrics.get("profit_factor", 0)
        if profit_factor > 2:
            score += 15
            details.append("盈亏比优秀")
        elif profit_factor > 1.5:
            score += 10
            details.append("盈亏比良好")
        elif profit_factor > 1:
            score += 5
        
        # 评级
        if score >= 80:
            rating = "A+"
            verdict = "策略表现优秀，建议实盘测试"
            risk_level = "低"
        elif score >= 65:
            rating = "A"
            verdict = "策略表现良好，可考虑优化后实盘"
            risk_level = "中低"
        elif score >= 50:
            rating = "B"
            verdict = "策略表现一般，需要优化"
            risk_level = "中等"
        elif score >= 35:
            rating = "C"
            verdict = "策略表现较差，建议重新设计"
            risk_level = "较高"
        else:
            rating = "D"
            verdict = "策略表现不佳，不建议使用"
            risk_level = "高"
        
        return {
            "score": score,
            "rating": rating,
            "verdict": verdict,
            "risk_level": risk_level,
            "details": details
        }
    
    def _add_performance_section(self):
        """绩效指标"""
        metrics = self.results.get("metrics", {})
        
        content = {
            "returns": {
                "total_return": {
                    "value": metrics.get("total_return"),
                    "display": f"{metrics.get('total_return', 0):.2f}%",
                    "grade": self._grade_return(metrics.get("total_return", 0))
                },
                "annual_return": {
                    "value": metrics.get("annual_return"),
                    "display": f"{metrics.get('annual_return', 0):.2f}%",
                    "grade": self._grade_return(metrics.get("annual_return", 0))
                },
                "calmar_ratio": {
                    "value": metrics.get("calmar_ratio"),
                    "display": f"{metrics.get('calmar_ratio', 0):.2f}",
                    "benchmark": "> 2.0"
                }
            },
            "risk_adjusted": {
                "sharpe_ratio": {
                    "value": metrics.get("sharpe_ratio"),
                    "display": f"{metrics.get('sharpe_ratio', 0):.2f}",
                    "grade": self._grade_sharpe(metrics.get("sharpe_ratio", 0))
                },
                "sortino_ratio": {
                    "value": metrics.get("sortino_ratio"),
                    "display": f"{metrics.get('sortino_ratio', 0):.2f}",
                    "grade": self._grade_sharpe(metrics.get("sortino_ratio", 0))
                },
                "volatility": {
                    "value": metrics.get("volatility"),
                    "display": f"{metrics.get('volatility', 0):.2f}%",
                    "note": "年化波动率"
                }
            }
        }
        
        self.sections.append(ReportSection(
            title="绩效指标",
            content=content,
            order=2
        ))
    
    def _add_risk_section(self):
        """风险分析"""
        metrics = self.results.get("metrics", {})
        analysis = self.results.get("analysis", {})
        risk_analysis = analysis.get("risk_analysis", {})
        
        content = {
            "drawdown": {
                "max_drawdown": {
                    "value": metrics.get("max_drawdown"),
                    "display": f"{metrics.get('max_drawdown', 0):.2f}%",
                    "severity": self._drawdown_severity(metrics.get("max_drawdown", 0))
                },
                "max_drawdown_days": metrics.get("max_drawdown_days", 0),
                "recovery": "待分析"  # 可以进一步计算恢复时间
            },
            "risk_score": {
                "score": risk_analysis.get("risk_score", 0),
                "level": risk_analysis.get("risk_level", "未知"),
                "assessment": self._risk_assessment(risk_analysis.get("risk_score", 0))
            },
            "var_analysis": {
                "note": "VaR分析需要更多历史数据",
                "daily_var_95": "待计算",
                "monthly_var_95": "待计算"
            }
        }
        
        self.sections.append(ReportSection(
            title="风险分析",
            content=content,
            order=3
        ))
    
    def _add_trading_section(self):
        """交易分析"""
        metrics = self.results.get("metrics", {})
        trades = self.results.get("trades", [])
        analysis = self.results.get("analysis", {})
        trade_analysis = analysis.get("trade_analysis", {})
        
        # 计算交易统计
        trade_stats = self._analyze_trades(trades)
        
        content = {
            "overview": {
                "total_trades": metrics.get("total_trades", 0),
                "winning_trades": metrics.get("winning_trades", 0),
                "losing_trades": metrics.get("losing_trades", 0),
                "win_rate": {
                    "value": metrics.get("win_rate"),
                    "display": f"{metrics.get('win_rate', 0):.2f}%"
                }
            },
            "profit_metrics": {
                "profit_factor": {
                    "value": metrics.get("profit_factor"),
                    "display": f"{metrics.get('profit_factor', 0):.2f}",
                    "assessment": "盈利" if metrics.get("profit_factor", 0) > 1 else "亏损"
                },
                "avg_profit": metrics.get("avg_profit"),
                "avg_loss": metrics.get("avg_loss"),
                "payoff_ratio": trade_analysis.get("payoff_ratio"),
                "expectancy": trade_analysis.get("expectancy")
            },
            "trade_distribution": trade_stats.get("distribution", {}),
            "consecutive": trade_stats.get("consecutive", {})
        }
        
        self.sections.append(ReportSection(
            title="交易分析",
            content=content,
            order=4
        ))
    
    def _analyze_trades(self, trades: List[Dict]) -> Dict[str, Any]:
        """分析交易记录"""
        if not trades:
            return {"distribution": {}, "consecutive": {}}
        
        # 收益分布
        pnls = [t.get("pnl", 0) for t in trades]
        profits = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p < 0]
        
        # 连续盈亏
        win_streaks = []
        loss_streaks = []
        current_streak = 0
        current_type = None
        
        for pnl in pnls:
            if pnl > 0:
                if current_type == "win":
                    current_streak += 1
                else:
                    if current_type == "loss":
                        loss_streaks.append(current_streak)
                    current_streak = 1
                    current_type = "win"
            else:
                if current_type == "loss":
                    current_streak += 1
                else:
                    if current_type == "win":
                        win_streaks.append(current_streak)
                    current_streak = 1
                    current_type = "loss"
        
        return {
            "distribution": {
                "profit_count": len(profits),
                "loss_count": len(losses),
                "avg_profit": round(sum(profits) / len(profits), 2) if profits else 0,
                "avg_loss": round(sum(losses) / len(losses), 2) if losses else 0,
                "largest_profit": round(max(profits), 2) if profits else 0,
                "largest_loss": round(min(losses), 2) if losses else 0
            },
            "consecutive": {
                "max_win_streak": max(win_streaks) if win_streaks else 0,
                "max_loss_streak": max(loss_streaks) if loss_streaks else 0,
                "avg_win_streak": round(sum(win_streaks) / len(win_streaks), 1) if win_streaks else 0,
                "avg_loss_streak": round(sum(loss_streaks) / len(loss_streaks), 1) if loss_streaks else 0
            }
        }
    
    def _add_charts_section(self):
        """图表数据"""
        equity_curve = self.results.get("equity_curve", [])
        monthly_returns = self.results.get("monthly_returns", [])
        
        # 处理权益曲线数据
        equity_data = []
        if equity_curve:
            for point in equity_curve:
                equity_data.append({
                    "timestamp": point.get("timestamp"),
                    "equity": point.get("total_equity"),
                    "drawdown": point.get("drawdown", 0) * 100
                })
        
        content = {
            "equity_curve": {
                "data": equity_data,
                "description": "权益曲线展示资金随时间的变化"
            },
            "monthly_returns": {
                "data": monthly_returns,
                "description": "月度收益率分布"
            },
            "heatmap": {
                "data": [],
                "description": "收益率热力图 (需要更多数据)"
            },
            "distribution": {
                "data": [],
                "description": "收益分布直方图"
            }
        }
        
        self.sections.append(ReportSection(
            title="图表数据",
            content=content,
            order=5
        ))
    
    def _add_recommendations_section(self):
        """优化建议"""
        analysis = self.results.get("analysis", {})
        recommendations = analysis.get("recommendations", [])
        
        # 分类建议
        categorized = {
            "high": [],
            "medium": [],
            "info": []
        }
        
        for rec in recommendations:
            severity = rec.get("severity", "info")
            categorized[severity].append({
                "type": rec.get("type"),
                "message": rec.get("message")
            })
        
        content = {
            "summary": f"共 {len(recommendations)} 条建议",
            "critical": categorized["high"],
            "suggestions": categorized["medium"],
            "notes": categorized["info"],
            "next_steps": self._generate_next_steps(recommendations)
        }
        
        self.sections.append(ReportSection(
            title="优化建议",
            content=content,
            order=6
        ))
    
    def _generate_next_steps(self, recommendations: List[Dict]) -> List[str]:
        """生成后续步骤建议"""
        steps = []
        
        has_risk_issues = any(r.get("type") == "risk" for r in recommendations)
        has_performance_issues = any(r.get("type") == "performance" for r in recommendations)
        
        if has_risk_issues:
            steps.append("优先解决风险控制问题，如降低仓位、收紧止损")
        
        if has_performance_issues:
            steps.append("优化策略入场/出场逻辑，提高信号质量")
        
        steps.append("进行样本外测试验证策略稳健性")
        steps.append("对比基准指数分析超额收益来源")
        steps.append("考虑加入多因子框架提升策略效果")
        
        return steps
    
    def _add_settings_section(self):
        """回测设置"""
        summary = self.results.get("summary", {})
        
        content = {
            "initial_capital": summary.get("initial_capital"),
            "final_capital": summary.get("final_capital"),
            "date_range": {
                "start": summary.get("start_date"),
                "end": summary.get("end_date"),
                "duration_days": summary.get("duration_days")
            },
            "execution": {
                "commission_rate": "0.03%",
                "slippage_model": "Dynamic",
                "risk_controls": "Enabled"
            }
        }
        
        self.sections.append(ReportSection(
            title="回测设置",
            content=content,
            order=7
        ))
    
    # ============== 辅助方法 ==============
    
    def _grade_return(self, ret: float) -> str:
        """收益评级"""
        if ret > 30:
            return "A"
        elif ret > 15:
            return "B"
        elif ret > 0:
            return "C"
        return "D"
    
    def _grade_sharpe(self, sharpe: float) -> str:
        """夏普比率评级"""
        if sharpe > 2:
            return "A"
        elif sharpe > 1.5:
            return "B"
        elif sharpe > 1:
            return "C"
        elif sharpe > 0.5:
            return "D"
        return "F"
    
    def _drawdown_severity(self, dd: float) -> str:
        """回撤严重程度"""
        if dd < 10:
            return "低"
        elif dd < 20:
            return "中等"
        elif dd < 30:
            return "较高"
        return "高"
    
    def _risk_assessment(self, score: int) -> str:
        """风险评估"""
        if score >= 70:
            return "策略风险可控，表现稳健"
        elif score >= 50:
            return "存在一定风险，建议优化"
        elif score >= 30:
            return "风险较高，需要改进"
        return "风险很高，不建议使用"


class HTMLReportRenderer:
    """HTML报告渲染器"""
    
    @staticmethod
    def render(report_data: Dict[str, Any]) -> str:
        """渲染HTML报告"""
        
        summary = report_data.get("summary", {})
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>回测分析报告</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        .score-card {{
            display: inline-block;
            background: rgba(255,255,255,0.2);
            padding: 15px 30px;
            border-radius: 10px;
            margin-top: 15px;
        }}
        .score-value {{
            font-size: 48px;
            font-weight: bold;
        }}
        .rating {{
            font-size: 24px;
            margin-left: 15px;
        }}
        .section {{
            background: white;
            padding: 25px;
            margin-bottom: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .section-title {{
            font-size: 20px;
            font-weight: bold;
            color: #333;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }}
        .metric-card {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }}
        .metric-label {{
            font-size: 12px;
            color: #666;
            margin-bottom: 5px;
        }}
        .metric-value {{
            font-size: 24px;
            font-weight: bold;
            color: #333;
        }}
        .positive {{ color: #28a745; }}
        .negative {{ color: #dc3545; }}
        .grade-a {{ color: #28a745; }}
        .grade-b {{ color: #6c757d; }}
        .grade-c {{ color: #ffc107; }}
        .grade-d {{ color: #dc3545; }}
        .recommendation {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
        }}
        .recommendation.critical {{
            background: #f8d7da;
            border-left-color: #dc3545;
        }}
        .chart-container {{
            height: 300px;
            background: #f8f9fa;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>回测分析报告</h1>
        <p>生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        <div class="score-card">
            <span class="score-value">{summary.get('score', 0)}</span>
            <span class="rating">评级: {summary.get('rating', 'N/A')}</span>
            <p>{summary.get('verdict', '')}</p>
            <p>风险等级: {summary.get('risk_level', '未知')}</p>
        </div>
    </div>
"""
        
        # 添加各个章节
        for section in report_data.get("sections", []):
            html += HTMLReportRenderer._render_section(section)
        
        html += """
</body>
</html>
"""
        return html
    
    @staticmethod
    def _render_section(section: Dict[str, Any]) -> str:
        """渲染单个章节"""
        title = section.get("title", "")
        content = section.get("content", {})
        
        html = '<div class="section">\n'
        html += f'<div class="section-title">{title}</div>\n'
        
        # 根据章节类型渲染不同内容
        if title == "执行摘要":
            html += HTMLReportRenderer._render_summary(content)
        elif title == "绩效指标":
            html += HTMLReportRenderer._render_performance(content)
        elif title == "风险分析":
            html += HTMLReportRenderer._render_risk(content)
        elif title == "交易分析":
            html += HTMLReportRenderer._render_trading(content)
        elif title == "图表数据":
            html += HTMLReportRenderer._render_charts(content)
        elif title == "优化建议":
            html += HTMLReportRenderer._render_recommendations(content)
        else:
            html += f'<pre>{json.dumps(content, indent=2, ensure_ascii=False)}</pre>'
        
        html += '</div>\n'
        return html
    
    @staticmethod
    def _render_summary(content: Dict) -> str:
        html = '<div class="metrics-grid">'
        for highlight in content.get("key_highlights", []):
            html += f'<div class="metric-card"><div class="metric-value">{highlight}</div></div>'
        html += '</div>'
        return html
    
    @staticmethod
    def _render_performance(content: Dict) -> str:
        html = '<div class="metrics-grid">'
        
        returns = content.get("returns", {})
        for key, value in returns.items():
            if isinstance(value, dict):
                grade_class = f"grade-{value.get('grade', 'c').lower()}"
                html += f'''
                <div class="metric-card">
                    <div class="metric-label">{key}</div>
                    <div class="metric-value {grade_class}">{value.get('display', 'N/A')}</div>
                </div>
                '''
        
        risk_adj = content.get("risk_adjusted", {})
        for key, value in risk_adj.items():
            if isinstance(value, dict):
                grade_class = f"grade-{value.get('grade', 'c').lower()}"
                html += f'''
                <div class="metric-card">
                    <div class="metric-label">{key}</div>
                    <div class="metric-value {grade_class}">{value.get('display', 'N/A')}</div>
                </div>
                '''
        
        html += '</div>'
        return html
    
    @staticmethod
    def _render_risk(content: Dict) -> str:
        html = '<div class="metrics-grid">'
        
        drawdown = content.get("drawdown", {})
        max_dd = drawdown.get("max_drawdown", {})
        html += f'''
        <div class="metric-card">
            <div class="metric-label">最大回撤</div>
            <div class="metric-value negative">{max_dd.get('display', 'N/A')}</div>
            <small>严重程度: {max_dd.get('severity', '未知')}</small>
        </div>
        '''
        
        risk_score = content.get("risk_score", {})
        html += f'''
        <div class="metric-card">
            <div class="metric-label">风险评分</div>
            <div class="metric-value">{risk_score.get('score', 0)}/100</div>
            <small>{risk_score.get('level', '未知')}</small>
        </div>
        '''
        
        html += '</div>'
        return html
    
    @staticmethod
    def _render_trading(content: Dict) -> str:
        overview = content.get("overview", {})
        profit = content.get("profit_metrics", {})
        
        html = f"""
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-label">总交易次数</div>
                <div class="metric-value">{overview.get('total_trades', 0)}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">胜率</div>
                <div class="metric-value">{overview.get('win_rate', {}).get('display', 'N/A')}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">盈亏比</div>
                <div class="metric-value">{profit.get('profit_factor', {}).get('display', 'N/A')}</div>
            </div>
        </div>
        """
        return html
    
    @staticmethod
    def _render_charts(content: Dict) -> str:
        return '<div class="chart-container">图表数据请使用前端可视化组件渲染</div>'
    
    @staticmethod
    def _render_recommendations(content: Dict) -> str:
        html = ''
        
        critical = content.get("critical", [])
        if critical:
            html += '<h4>重要问题</h4>'
            for rec in critical:
                html += f'<div class="recommendation critical">{rec.get("message", "")}</div>'
        
        suggestions = content.get("suggestions", [])
        if suggestions:
            html += '<h4>改进建议</h4>'
            for rec in suggestions:
                html += f'<div class="recommendation">{rec.get("message", "")}</div>'
        
        next_steps = content.get("next_steps", [])
        if next_steps:
            html += '<h4>后续步骤</h4><ol>'
            for step in next_steps:
                html += f'<li>{step}</li>'
            html += '</ol>'
        
        return html


# 便捷函数
def generate_backtest_report(
    backtest_results: Dict[str, Any],
    format: str = "json"
) -> Union[Dict[str, Any], str]:
    """
    生成回测报告
    
    Args:
        backtest_results: 回测结果字典
        format: 报告格式 (json, html)
    
    Returns:
        格式化后的报告
    """
    generator = BacktestReportGenerator(backtest_results)
    report = generator.generate_full_report()
    
    if format == "json":
        return report
    elif format == "html":
        return HTMLReportRenderer.render(report)
    else:
        raise ValueError(f"不支持的报告格式: {format}")
