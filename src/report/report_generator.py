"""
报告生成器

生成分析报告、可视化图表和推荐列表
"""

from typing import Dict, List, Optional
import pandas as pd
from datetime import datetime
import json
from pathlib import Path
from loguru import logger


class ReportGenerator:
    """
    报告生成器类
    
    生成各种格式的分析报告和图表
    """
    
    def __init__(self, config: Dict):
        """
        初始化报告生成器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.output_path = Path(config.get('output_path', 'data/reports/'))
        self.output_path.mkdir(parents=True, exist_ok=True)
        self.format = config.get('format', ['html', 'json'])
        self.top_n = config.get('top_n', 10)
        self.include_charts = config.get('include_charts', True)
        
        logger.info(f"初始化报告生成器，输出路径: {self.output_path}")
    
    def generate_report(self, 
                       strategy_name: str,
                       recommendations: List[Dict],
                       portfolio_stats: Optional[Dict] = None,
                       backtest_results: Optional[Dict] = None) -> Dict[str, str]:
        """
        生成完整报告
        
        Args:
            strategy_name: 策略名称
            recommendations: 推荐列表
            portfolio_stats: 组合统计（可选）
            backtest_results: 回测结果（可选）
            
        Returns:
            Dict: 生成的报告文件路径 {'html': path, 'json': path, ...}
        """
        logger.info(f"开始生成报告: {strategy_name}")
        
        # 生成时间戳
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_name = f"{strategy_name}_{timestamp}"
        
        report_paths = {}
        
        # 生成JSON报告
        if 'json' in self.format:
            json_path = self._generate_json_report(
                report_name, 
                strategy_name,
                recommendations, 
                portfolio_stats,
                backtest_results
            )
            report_paths['json'] = str(json_path)
            logger.info(f"JSON报告已生成: {json_path}")
        
        # 生成HTML报告
        if 'html' in self.format:
            html_path = self._generate_html_report(
                report_name,
                strategy_name,
                recommendations,
                portfolio_stats,
                backtest_results
            )
            report_paths['html'] = str(html_path)
            logger.info(f"HTML报告已生成: {html_path}")
        
        logger.info(f"报告生成完成，共 {len(report_paths)} 个文件")
        
        return report_paths
    
    def _generate_json_report(self,
                             report_name: str,
                             strategy_name: str,
                             recommendations: List[Dict],
                             portfolio_stats: Optional[Dict],
                             backtest_results: Optional[Dict]) -> Path:
        """
        生成JSON格式报告
        
        Args:
            report_name: 报告名称
            strategy_name: 策略名称
            recommendations: 推荐列表
            portfolio_stats: 组合统计
            backtest_results: 回测结果
            
        Returns:
            Path: JSON文件路径
        """
        report_data = {
            'report_name': report_name,
            'strategy_name': strategy_name,
            'generated_at': datetime.now().isoformat(),
            'recommendations': recommendations,
            'portfolio_stats': portfolio_stats or {},
            'backtest_results': backtest_results or {},
            'summary': {
                'total_recommendations': len(recommendations),
                'top_n': self.top_n,
            }
        }
        
        json_path = self.output_path / f'{report_name}.json'
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2, default=str)
        
        return json_path
    
    def _generate_html_report(self,
                             report_name: str,
                             strategy_name: str,
                             recommendations: List[Dict],
                             portfolio_stats: Optional[Dict],
                             backtest_results: Optional[Dict]) -> Path:
        """
        生成HTML格式报告
        
        Args:
            report_name: 报告名称
            strategy_name: 策略名称
            recommendations: 推荐列表
            portfolio_stats: 组合统计
            backtest_results: 回测结果
            
        Returns:
            Path: HTML文件路径
        """
        html_content = self._create_html_template(
            strategy_name,
            recommendations,
            portfolio_stats,
            backtest_results
        )
        
        html_path = self.output_path / f'{report_name}.html'
        
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return html_path
    
    def _create_html_template(self,
                             strategy_name: str,
                             recommendations: List[Dict],
                             portfolio_stats: Optional[Dict],
                             backtest_results: Optional[Dict]) -> str:
        """
        创建HTML模板
        
        Args:
            strategy_name: 策略名称
            recommendations: 推荐列表
            portfolio_stats: 组合统计
            backtest_results: 回测结果
            
        Returns:
            str: HTML内容
        """
        # 生成推荐表格
        recommendations_html = self._create_recommendations_table(recommendations)
        
        # 生成统计信息
        stats_html = self._create_stats_section(portfolio_stats) if portfolio_stats else ""
        
        # 生成回测结果
        backtest_html = self._create_backtest_section(backtest_results) if backtest_results else ""
        
        # 组装完整HTML
        html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>证券交易推荐报告 - {strategy_name}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: #f5f7fa;
            color: #333;
            line-height: 1.6;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 28px;
            margin-bottom: 10px;
        }}
        
        .header p {{
            font-size: 14px;
            opacity: 0.9;
        }}
        
        .content {{
            padding: 30px;
        }}
        
        .section {{
            margin-bottom: 40px;
        }}
        
        .section-title {{
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #667eea;
            color: #667eea;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .stat-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 6px;
            border-left: 4px solid #667eea;
        }}
        
        .stat-label {{
            font-size: 12px;
            color: #666;
            margin-bottom: 5px;
        }}
        
        .stat-value {{
            font-size: 24px;
            font-weight: 600;
            color: #333;
        }}
        
        .recommendations-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        
        .recommendations-table th {{
            background: #667eea;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            font-size: 14px;
        }}
        
        .recommendations-table td {{
            padding: 12px;
            border-bottom: 1px solid #e9ecef;
            font-size: 14px;
        }}
        
        .recommendations-table tr:hover {{
            background: #f8f9fa;
        }}
        
        .rank-badge {{
            display: inline-block;
            width: 30px;
            height: 30px;
            line-height: 30px;
            text-align: center;
            border-radius: 50%;
            background: #667eea;
            color: white;
            font-weight: 600;
        }}
        
        .rank-badge.top-1 {{
            background: #ffd700;
            color: #333;
        }}
        
        .rank-badge.top-2 {{
            background: #c0c0c0;
            color: #333;
        }}
        
        .rank-badge.top-3 {{
            background: #cd7f32;
            color: white;
        }}
        
        .positive {{
            color: #28a745;
        }}
        
        .negative {{
            color: #dc3545;
        }}
        
        .reasons-list {{
            list-style: none;
            padding-left: 0;
            font-size: 13px;
            color: #666;
        }}
        
        .reasons-list li {{
            padding: 3px 0;
        }}
        
        .reasons-list li:before {{
            content: "• ";
            color: #667eea;
            font-weight: bold;
            margin-right: 5px;
        }}
        
        .footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #666;
            font-size: 12px;
            border-top: 1px solid #e9ecef;
        }}
        
        .badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
        }}
        
        .badge-success {{
            background: #d4edda;
            color: #155724;
        }}
        
        .badge-info {{
            background: #d1ecf1;
            color: #0c5460;
        }}
        
        @media print {{
            body {{
                background: white;
            }}
            .container {{
                box-shadow: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 证券交易推荐报告</h1>
            <p>策略: {strategy_name} | 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="content">
            {stats_html}
            
            <div class="section">
                <h2 class="section-title">🎯 推荐列表</h2>
                {recommendations_html}
            </div>
            
            {backtest_html}
        </div>
        
        <div class="footer">
            <p>本报告由证券交易推荐系统自动生成 | Trading Tips System v1.0</p>
            <p>⚠️ 投资有风险，入市需谨慎。本报告仅供参考，不构成投资建议。</p>
        </div>
    </div>
</body>
</html>
"""
        
        return html
    
    def _create_recommendations_table(self, recommendations: List[Dict]) -> str:
        """
        创建推荐列表表格
        
        Args:
            recommendations: 推荐列表
            
        Returns:
            str: HTML表格
        """
        if not recommendations:
            return "<p>暂无推荐</p>"
        
        rows = []
        for rec in recommendations:
            rank = rec.get('rank', 0)
            rank_class = ""
            if rank == 1:
                rank_class = "top-1"
            elif rank == 2:
                rank_class = "top-2"
            elif rank == 3:
                rank_class = "top-3"
            
            # 格式化推荐理由
            reasons = rec.get('reasons', [])
            reasons_html = "<ul class='reasons-list'>"
            for reason in reasons:
                reasons_html += f"<li>{reason}</li>"
            reasons_html += "</ul>"
            
            # 波动率和动量颜色
            volatility = rec.get('volatility', 0)
            momentum = rec.get('momentum', 0)
            momentum_class = "positive" if momentum > 0 else "negative"
            
            row = f"""
            <tr>
                <td><span class="rank-badge {rank_class}">{rank}</span></td>
                <td><strong>{rec.get('name', 'N/A')}</strong><br><small>{rec.get('code', 'N/A')}</small></td>
                <td>{rec.get('current_price', 'N/A')}</td>
                <td><span class="badge badge-success">{rec.get('score', 0):.2f}</span></td>
                <td>{volatility:.2f}%</td>
                <td class="{momentum_class}">{momentum:.2f}%</td>
                <td>{rec.get('suggested_position', 'N/A')}</td>
                <td>{reasons_html}</td>
            </tr>
            """
            rows.append(row)
        
        table = f"""
        <table class="recommendations-table">
            <thead>
                <tr>
                    <th>排名</th>
                    <th>名称/代码</th>
                    <th>当前价格</th>
                    <th>综合得分</th>
                    <th>波动率</th>
                    <th>动量</th>
                    <th>建议仓位</th>
                    <th>推荐理由</th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows)}
            </tbody>
        </table>
        """
        
        return table
    
    def _create_stats_section(self, portfolio_stats: Dict) -> str:
        """
        创建统计信息部分
        
        Args:
            portfolio_stats: 组合统计
            
        Returns:
            str: HTML内容
        """
        stats = [
            {
                'label': '组合数量',
                'value': portfolio_stats.get('portfolio_count', 0)
            },
            {
                'label': '平均波动率',
                'value': f"{portfolio_stats.get('avg_volatility', 0):.2f}%"
            },
            {
                'label': '平均动量',
                'value': f"{portfolio_stats.get('avg_momentum', 0):.2f}%"
            },
            {
                'label': '预期年化收益',
                'value': portfolio_stats.get('expected_annual_return', 'N/A')
            },
        ]
        
        if 'avg_sharpe_ratio' in portfolio_stats:
            sharpe = portfolio_stats.get('avg_sharpe_ratio', 0)
            if not pd.isna(sharpe):
                stats.append({
                    'label': '平均夏普比率',
                    'value': f"{sharpe:.2f}"
                })
        
        if 'avg_max_drawdown' in portfolio_stats:
            stats.append({
                'label': '平均最大回撤',
                'value': f"{portfolio_stats.get('avg_max_drawdown', 0):.2f}%"
            })
        
        stats_cards = ""
        for stat in stats:
            stats_cards += f"""
            <div class="stat-card">
                <div class="stat-label">{stat['label']}</div>
                <div class="stat-value">{stat['value']}</div>
            </div>
            """
        
        return f"""
        <div class="section">
            <h2 class="section-title">📈 组合统计</h2>
            <div class="stats-grid">
                {stats_cards}
            </div>
        </div>
        """
    
    def _create_backtest_section(self, backtest_results: Dict) -> str:
        """
        创建回测结果部分
        
        Args:
            backtest_results: 回测结果
            
        Returns:
            str: HTML内容
        """
        # TODO: 实现回测结果展示
        return """
        <div class="section">
            <h2 class="section-title">📊 回测结果</h2>
            <p>回测功能开发中...</p>
        </div>
        """
    
    def generate_simple_report(self,
                              strategy_name: str,
                              recommendations: List[Dict]) -> str:
        """
        生成简单的文本报告
        
        Args:
            strategy_name: 策略名称
            recommendations: 推荐列表
            
        Returns:
            str: 文本报告内容
        """
        lines = []
        lines.append("=" * 70)
        lines.append(f"证券交易推荐报告 - {strategy_name}")
        lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 70)
        lines.append("")
        
        if not recommendations:
            lines.append("暂无推荐")
        else:
            lines.append(f"共推荐 {len(recommendations)} 只标的:")
            lines.append("")
            
            for rec in recommendations:
                lines.append(f"【排名 {rec.get('rank', 0)}】 {rec.get('name', 'N/A')} ({rec.get('code', 'N/A')})")
                lines.append(f"  当前价格: {rec.get('current_price', 'N/A')}")
                lines.append(f"  综合得分: {rec.get('score', 0):.2f}")
                lines.append(f"  波动率: {rec.get('volatility', 0):.2f}%")
                lines.append(f"  动量: {rec.get('momentum', 0):.2f}%")
                lines.append(f"  建议仓位: {rec.get('suggested_position', 'N/A')}")
                lines.append(f"  推荐理由:")
                for reason in rec.get('reasons', []):
                    lines.append(f"    - {reason}")
                lines.append("")
        
        lines.append("=" * 70)
        lines.append("⚠️  投资有风险，入市需谨慎")
        lines.append("=" * 70)
        
        return "\n".join(lines)

