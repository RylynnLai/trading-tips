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
                       backtest_results: Optional[Dict] = None,
                       data_info: Optional[Dict] = None) -> Dict[str, str]:
        """
        生成完整报告
        
        Args:
            strategy_name: 策略名称
            recommendations: 推荐列表
            portfolio_stats: 组合统计（可选）
            backtest_results: 回测结果（可选）
            data_info: 数据信息（时间范围等）
            
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
                backtest_results,
                data_info
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
                backtest_results,
                data_info
            )
            report_paths['html'] = str(html_path)
            logger.info(f"HTML报告已生成: {html_path}")
        
        # 生成Markdown报告（默认总是生成）
        markdown_path = self._generate_markdown_report(
            report_name,
            strategy_name,
            recommendations,
            portfolio_stats,
            backtest_results,
            data_info
        )
        report_paths['markdown'] = str(markdown_path)
        logger.info(f"Markdown报告已生成: {markdown_path}")
        
        logger.info(f"报告生成完成，共 {len(report_paths)} 个文件")
        
        return report_paths
    
    def _generate_json_report(self,
                             report_name: str,
                             strategy_name: str,
                             recommendations: List[Dict],
                             portfolio_stats: Optional[Dict],
                             backtest_results: Optional[Dict],
                             data_info: Optional[Dict]) -> Path:
        """
        生成JSON格式报告
        
        Args:
            report_name: 报告名称
            strategy_name: 策略名称
            recommendations: 推荐列表
            portfolio_stats: 组合统计
            backtest_results: 回测结果
            data_info: 数据信息
            
        Returns:
            Path: JSON文件路径
        """
        report_data = {
            'report_name': report_name,
            'strategy_name': strategy_name,
            'generated_at': datetime.now().isoformat(),
            'data_info': data_info or {},
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
    
    def _generate_markdown_report(self,
                                  report_name: str,
                                  strategy_name: str,
                                  recommendations: List[Dict],
                                  portfolio_stats: Optional[Dict],
                                  backtest_results: Optional[Dict],
                                  data_info: Optional[Dict]) -> Path:
        """
        生成Markdown格式报告（易读版本）
        
        Args:
            report_name: 报告名称
            strategy_name: 策略名称
            recommendations: 推荐列表
            portfolio_stats: 组合统计
            backtest_results: 回测结果
            data_info: 数据信息
            
        Returns:
            Path: Markdown文件路径
        """
        lines = []
        
        # 标题和元信息
        lines.append(f"# 📊 证券交易推荐报告")
        lines.append("")
        lines.append(f"**策略名称**: {strategy_name}")
        lines.append(f"**生成时间**: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}")
        lines.append(f"**推荐数量**: {len(recommendations)} 只")
        
        # 添加数据时间范围信息
        if data_info:
            lines.append("")
            lines.append("## 📅 数据信息")
            lines.append("")
            lines.append(f"- **分析股票数量**: {data_info.get('total_stocks', 0)} 只")
            if data_info.get('date_range'):
                lines.append(f"- **数据时间范围**: {data_info['date_range']}")
            if data_info.get('avg_data_points'):
                lines.append(f"- **平均数据点数**: {data_info['avg_data_points']} 个交易日")
        
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # 执行摘要
        if recommendations:
            lines.append("## 📋 执行摘要")
            lines.append("")
            avg_score = sum(r.get('score', 0) for r in recommendations) / len(recommendations)
            lines.append(f"- 本次共分析股票并生成 **{len(recommendations)}** 个推荐")
            lines.append(f"- 平均推荐评分: **{avg_score:.1f}** 分")
            
            # 统计策略类型
            strategy_counts = {}
            for rec in recommendations:
                strategy = rec.get('strategy', '未知')
                strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
            
            lines.append(f"- 策略分布:")
            for strategy, count in strategy_counts.items():
                lines.append(f"  - {strategy}: {count} 只")
            
            lines.append("")
            lines.append("---")
            lines.append("")
        
        # 详细推荐
        if not recommendations:
            lines.append("## ⚠️ 暂无推荐")
            lines.append("")
            lines.append("当前市场环境下，暂无符合策略标准的推荐标的。")
            lines.append("")
            lines.append("**可能原因：**")
            lines.append("1. 大部分股票处于震荡或下跌趋势，无明确方向")
            lines.append("2. 处于上涨趋势的股票位置过高，不适合买入")
            lines.append("3. 推荐评分阈值较高（默认60分），保证推荐质量")
            lines.append("")
            lines.append("**建议：**")
            lines.append("- 等待市场出现明确的趋势信号")
            lines.append("- 降低评分阈值（如调整为50分）可获得更多推荐")
            lines.append("- 使用 `--min-score 50` 参数重新运行分析")
        else:
            lines.append("## 🎯 详细推荐列表")
            lines.append("")
            
            for idx, rec in enumerate(recommendations, 1):
                # 推荐标题
                symbol = rec.get('symbol', '未知')
                strategy = rec.get('strategy', '未知策略')
                priority = rec.get('priority', '⭐')
                score = rec.get('score', 0)
                
                lines.append(f"### {idx}. {symbol} - {strategy} {priority}")
                lines.append("")
                
                # 基本信息表格
                lines.append("| 项目 | 数值 |")
                lines.append("|------|------|")
                lines.append(f"| 💯 **综合评分** | **{score}** 分 |")
                
                current_price = rec.get('current_price', 'N/A')
                lines.append(f"| 💰 当前价格 | {current_price} |")
                
                trend_type = rec.get('trend_type', '未定义')
                lines.append(f"| 📈 趋势类型 | {trend_type} |")
                
                ma_alignment = rec.get('ma_alignment', 'N/A')
                alignment_text = {
                    'bull': '多头排列 🟢',
                    'bear': '空头排列 🔴',
                    'mixed': '混乱排列 🟡'
                }.get(ma_alignment, ma_alignment)
                lines.append(f"| 📊 均线形态 | {alignment_text} |")
                
                # 交易信号
                entry_signal = rec.get('entry_signal', 'N/A')
                if entry_signal != 'N/A':
                    lines.append(f"| 🎯 入场信号 | {entry_signal} |")
                
                hold_signal = rec.get('hold_signal')
                if hold_signal:
                    lines.append(f"| 💎 持有信号 | {hold_signal} |")
                
                exit_signal = rec.get('exit_signal')
                if exit_signal:
                    lines.append(f"| 🚪 离场信号 | {exit_signal} |")
                
                # 止损和目标
                stop_loss = rec.get('stop_loss')
                if stop_loss:
                    stop_loss_pct = rec.get('stop_loss_pct', 0)
                    lines.append(f"| 🛡️ 止损位 | {stop_loss:.2f} ({stop_loss_pct:.1f}%) |")
                
                targets = rec.get('targets', [])
                if targets:
                    target_str = " / ".join([f"{t:.2f}" for t in targets[:3]])
                    lines.append(f"| 🎯 目标位 | {target_str} |")
                
                risk_reward = rec.get('risk_reward', 0)
                if risk_reward > 0:
                    lines.append(f"| ⚖️ 盈亏比 | {risk_reward:.1f}:1 |")
                
                lines.append("")
                
                # 推荐理由
                reasons = rec.get('reasons', [])
                if reasons:
                    lines.append("**📝 推荐理由：**")
                    lines.append("")
                    for reason in reasons:
                        lines.append(f"- ✅ {reason}")
                    lines.append("")
                
                # 信号分析
                signals = rec.get('signals', {})
                if signals:
                    lines.append("**🔍 技术信号：**")
                    lines.append("")
                    if signals.get('breakout'):
                        strength = signals.get('strength', 0)
                        lines.append(f"- 🚀 突破信号（强度: {strength:.0f}%）")
                    if signals.get('pullback'):
                        support = signals.get('support_level', 'N/A')
                        lines.append(f"- 📉 回调信号（支撑位: {support}）")
                    if signals.get('two_b_reversal'):
                        lines.append(f"- 🔄 2B反转信号")
                    lines.append("")
                
                # 操作建议
                lines.append("**💡 操作建议：**")
                lines.append("")
                
                if strategy == "密集成交区突破":
                    lines.append("- 🎯 **入场时机**: 价格突破MA20且带量时买入")
                    lines.append("- 🛡️ **止损设置**: 跌破止损位果断离场")
                    lines.append("- 💎 **持仓管理**: 盈利后移动止损，保护利润")
                elif strategy == "稳定趋势回调":
                    lines.append("- 🎯 **入场时机**: 回踩支撑位企稳后买入")
                    lines.append("- 🛡️ **止损设置**: 有效跌破支撑位止损")
                    lines.append("- 💎 **持仓管理**: 趋势持续可继续持有")
                elif strategy == "加速行情-持有":
                    lines.append("- ⚠️ **不建议追高**: 加速上涨中，新资金不宜买入")
                    lines.append("- 💎 **已有持仓**: 可继续持有，设好止盈止损")
                    lines.append("- 🚪 **离场信号**: 出现顶部构造或均线死叉考虑减仓")
                
                lines.append("")
                
                # 盈利预测（新增）
                profit_prediction = rec.get('profit_prediction')
                if profit_prediction:
                    lines.append("**📈 盈利预测：**")
                    lines.append("")
                    
                    # 目标价位
                    pred_targets = profit_prediction.get('targets', [])
                    if pred_targets:
                        lines.append("| 目标位 | 价格 | 预期收益 | 达成概率 | 说明 |")
                        lines.append("|--------|------|----------|----------|------|")
                        for target in pred_targets:
                            level = target.get('level', 0)
                            price = target.get('price', 0)
                            gain_pct = target.get('gain_pct', 0)
                            probability = target.get('probability', 0)
                            desc = target.get('description', '')
                            
                            # 添加emoji
                            emoji = "🥇" if level == 1 else "🥈" if level == 2 else "🥉"
                            
                            lines.append(
                                f"| {emoji} 目标{level} | {price:.2f} | +{gain_pct:.1f}% | "
                                f"{probability:.0%} | {desc} |"
                            )
                        lines.append("")
                    
                    # 持有周期预测
                    holding_period = profit_prediction.get('holding_period', {})
                    if holding_period:
                        min_days = holding_period.get('min_days', 0)
                        target_days = holding_period.get('target_days', 0)
                        max_days = holding_period.get('max_days', 0)
                        description = holding_period.get('description', '')
                        
                        lines.append(f"**⏱️ 建议持有周期：** {min_days}-{target_days}天 (最长{max_days}天)")
                        lines.append(f"- {description}")
                        lines.append("")
                    
                    # 风险收益评估
                    risk_reward_detail = profit_prediction.get('risk_reward', {})
                    if risk_reward_detail:
                        overall_ratio = risk_reward_detail.get('overall_ratio', 0)
                        evaluation = risk_reward_detail.get('evaluation', '')
                        expected_value = risk_reward_detail.get('expected_value', 0)
                        
                        lines.append(f"**⚖️ 风险收益评估：** {evaluation}")
                        lines.append(f"- 盈亏比：{overall_ratio:.2f}:1")
                        lines.append(f"- 预期收益：{expected_value:.1f}%")
                        lines.append("")
                    
                    # 成功概率
                    success_prob = profit_prediction.get('success_probability', 0)
                    if success_prob > 0:
                        prob_emoji = "🟢" if success_prob >= 0.7 else "🟡" if success_prob >= 0.5 else "🔴"
                        lines.append(f"**✅ 成功概率：** {prob_emoji} {success_prob:.0%}")
                        lines.append("")
                    
                    # 离场时机（关键！）
                    exit_signals_info = profit_prediction.get('exit_signals', {})
                    if exit_signals_info:
                        signals_dict = exit_signals_info.get('signals', {})
                        active_warnings = exit_signals_info.get('active_warnings', [])
                        
                        if active_warnings:
                            lines.append("**⚠️⚠️ 当前触发的离场信号：**")
                            lines.append("")
                            for warning in active_warnings:
                                signal_info = signals_dict.get(warning, {})
                                lines.append(f"- 🚨 **{warning}**: {signal_info.get('condition', '')}")
                                lines.append(f"  - 优先级: {signal_info.get('priority', '')}")
                                lines.append(f"  - 操作: {signal_info.get('action', '')}")
                            lines.append("")
                        
                        lines.append("**🚪 离场信号说明：**")
                        lines.append("")
                        lines.append("以下情况出现时应考虑离场：")
                        lines.append("")
                        
                        for signal_name, signal_info in signals_dict.items():
                            if signal_name not in ['止损']:  # 止损已在上面显示
                                trigger = signal_info.get('trigger', '')
                                condition = signal_info.get('condition', '')
                                priority = signal_info.get('priority', '')
                                
                                lines.append(f"- **{trigger}** {priority}")
                                lines.append(f"  - 触发条件: {condition}")
                        
                        lines.append("")
                    
                    # 综合建议
                    recommendation_text = profit_prediction.get('recommendation', '')
                    if recommendation_text:
                        lines.append("**🎯 综合建议：**")
                        lines.append("")
                        lines.append(recommendation_text)
                        lines.append("")
                
                lines.append("---")
                lines.append("")
        
        # 风险提示
        lines.append("## ⚠️ 风险提示")
        lines.append("")
        lines.append("1. **本报告仅供参考，不构成投资建议**")
        lines.append("2. **股票投资有风险，入市需谨慎**")
        lines.append("3. **请根据自身风险承受能力做出投资决策**")
        lines.append("4. **严格执行止损策略，控制风险**")
        lines.append("5. **不要将全部资金投入单一标的**")
        lines.append("")
        
        # 页脚
        lines.append("---")
        lines.append("")
        lines.append("*本报告由趋势跟随交易系统自动生成*")
        lines.append("")
        lines.append(f"*生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        
        # 写入文件
        markdown_path = self.output_path / f'{report_name}.md'
        
        with open(markdown_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        return markdown_path
    
    def _generate_html_report(self,
                             report_name: str,
                             strategy_name: str,
                             recommendations: List[Dict],
                             portfolio_stats: Optional[Dict],
                             backtest_results: Optional[Dict],
                             data_info: Optional[Dict]) -> Path:
        """
        生成HTML格式报告
        
        Args:
            report_name: 报告名称
            strategy_name: 策略名称
            recommendations: 推荐列表
            portfolio_stats: 组合统计
            backtest_results: 回测结果
            data_info: 数据信息
            
        Returns:
            Path: HTML文件路径
        """
        html_content = self._create_html_template(
            strategy_name,
            recommendations,
            portfolio_stats,
            backtest_results,
            data_info
        )
        
        html_path = self.output_path / f'{report_name}.html'
        
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return html_path
    
    def _create_html_template(self,
                             strategy_name: str,
                             recommendations: List[Dict],
                             portfolio_stats: Optional[Dict],
                             backtest_results: Optional[Dict],
                             data_info: Optional[Dict]) -> str:
        """
        创建HTML模板
        
        Args:
            strategy_name: 策略名称
            recommendations: 推荐列表
            portfolio_stats: 组合统计
            backtest_results: 回测结果
            data_info: 数据信息
            
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

