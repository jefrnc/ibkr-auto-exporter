#!/usr/bin/env python3
"""
Monthly summary generator for IBKR trades
Creates comprehensive monthly analytics
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import numpy as np


def load_weekly_summaries(year: int, month: int) -> List[Dict]:
    """Load all weekly summaries for the month"""
    base_dir = os.getenv('EXPORT_OUTPUT_DIR', 'exports')
    weekly_dir = Path(f'{base_dir}/weekly')
    
    summaries = []
    for file in weekly_dir.glob(f'{year}-W*.json'):
        with open(file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Check if week overlaps with our month
            week_start = datetime.strptime(data['weekStart'], '%Y-%m-%d')
            week_end = datetime.strptime(data['weekEnd'], '%Y-%m-%d')
            
            if (week_start.month == month or week_end.month == month) and \
               (week_start.year == year or week_end.year == year):
                summaries.append(data)
    
    return sorted(summaries, key=lambda x: x['weekNumber'])


def load_all_daily_files(year: int, month: int) -> List[Dict]:
    """Load all daily files for the month"""
    base_dir = os.getenv('EXPORT_OUTPUT_DIR', 'exports')
    daily_dir = Path(f'{base_dir}/daily')
    
    daily_data = []
    # Generate all days of the month
    for day in range(1, 32):
        try:
            date = datetime(year, month, day)
            date_str = date.strftime('%Y-%m-%d')
            
            daily_file = daily_dir / f'{date_str}.json'
            if daily_file.exists():
                with open(daily_file, 'r', encoding='utf-8') as f:
                    daily_data.append(json.load(f))
        except ValueError:
            # Invalid day for this month
            break
    
    return daily_data


def analyze_monthly_performance(trades: List[Dict], daily_summaries: List[Dict]) -> Dict[str, Any]:
    """Deep analysis of monthly performance"""
    analysis = {
        'tradingDays': len([d for d in daily_summaries if d.get('summary', {}).get('totalTrades', 0) > 0]),
        'totalDays': len(daily_summaries),
        'consistency': 0,
        'bestStreak': 0,
        'currentStreak': 0,
        'worstDrawdown': 0,
        'avgDailyPnL': 0,
        'stdDailyPnL': 0,
        'sharpeRatio': 0,
        'profitFactor': 0,
        'expectancy': 0,
        'maxConsecutiveLosses': 0
    }
    
    # Calculate daily P&Ls
    daily_pnls = []
    cumulative_pnl = 0
    max_cumulative = 0
    current_streak = 0
    best_streak = 0
    consecutive_losses = 0
    max_consecutive_losses = 0
    
    for day in sorted(daily_summaries, key=lambda x: x['date']):
        if day.get('summary', {}).get('totalTrades', 0) > 0:
            daily_pnl = day['summary']['netPnL']
            daily_pnls.append(daily_pnl)
            cumulative_pnl += daily_pnl
            
            # Track streaks
            if daily_pnl > 0:
                current_streak += 1
                best_streak = max(best_streak, current_streak)
                consecutive_losses = 0
            else:
                current_streak = 0
                consecutive_losses += 1
                max_consecutive_losses = max(max_consecutive_losses, consecutive_losses)
            
            # Track drawdown
            max_cumulative = max(max_cumulative, cumulative_pnl)
            drawdown = max_cumulative - cumulative_pnl
            analysis['worstDrawdown'] = max(analysis['worstDrawdown'], drawdown)
    
    analysis['bestStreak'] = best_streak
    analysis['maxConsecutiveLosses'] = max_consecutive_losses
    
    if daily_pnls:
        analysis['avgDailyPnL'] = np.mean(daily_pnls)
        analysis['stdDailyPnL'] = np.std(daily_pnls)
        
        # Calculate Sharpe Ratio (assuming 0 risk-free rate)
        if analysis['stdDailyPnL'] > 0:
            analysis['sharpeRatio'] = (analysis['avgDailyPnL'] * np.sqrt(252)) / (analysis['stdDailyPnL'] * np.sqrt(252))
        
        # Calculate consistency
        positive_days = sum(1 for pnl in daily_pnls if pnl > 0)
        analysis['consistency'] = positive_days / len(daily_pnls) if daily_pnls else 0
    
    # Calculate profit factor and expectancy
    total_wins = sum(pnl for pnl in daily_pnls if pnl > 0)
    total_losses = abs(sum(pnl for pnl in daily_pnls if pnl < 0))
    
    if total_losses > 0:
        analysis['profitFactor'] = total_wins / total_losses
    
    if trades:
        winners = [t for t in trades if t.get('pnl', 0) > 0]
        losers = [t for t in trades if t.get('pnl', 0) < 0]
        
        if winners or losers:
            avg_win = np.mean([t['pnl'] for t in winners]) if winners else 0
            avg_loss = np.mean([t['pnl'] for t in losers]) if losers else 0
            win_rate = len(winners) / (len(winners) + len(losers))
            
            analysis['expectancy'] = (win_rate * avg_win) - ((1 - win_rate) * abs(avg_loss))
    
    return analysis


def generate_monthly_summary(year=None, month=None):
    """Generate monthly summary"""
    # If not specified, use current month
    if year is None or month is None:
        now = datetime.now()
        year = now.year
        month = now.month
    
    month_name = datetime(year, month, 1).strftime('%B')
    print(f"📈 Generating monthly summary for {month_name} {year}")
    
    # Load data
    daily_data = load_all_daily_files(year, month)
    weekly_data = load_weekly_summaries(year, month)
    
    if not daily_data:
        print("ℹ️ No data found for this month")
        return
    
    # Aggregate all trades
    all_trades = []
    total_pnl = 0
    total_commission = 0
    total_trades = 0
    
    for day in daily_data:
        trades = day.get('trades', [])
        all_trades.extend(trades)
        summary = day.get('summary', {})
        total_pnl += summary.get('totalPnL', 0)
        total_commission += summary.get('totalCommission', 0)
        total_trades += summary.get('totalTrades', 0)
    
    # Analyze performance
    analysis = analyze_monthly_performance(all_trades, daily_data)
    
    # Get account info
    account = daily_data[0].get('account', 'Unknown') if daily_data else 'Unknown'
    
    # Build summary
    summary = {
        'exportDate': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'account': account,
        'year': year,
        'month': month,
        'monthName': month_name,
        'statistics': {
            'totalTrades': total_trades,
            'totalPnL': round(total_pnl, 2),
            'totalCommission': round(total_commission, 2),
            'netPnL': round(total_pnl - total_commission, 2),
            'tradingDays': analysis['tradingDays'],
            'avgDailyPnL': round(analysis['avgDailyPnL'], 2),
            'consistency': round(analysis['consistency'], 4),
            'sharpeRatio': round(analysis['sharpeRatio'], 2),
            'profitFactor': round(analysis['profitFactor'], 2),
            'worstDrawdown': round(analysis['worstDrawdown'], 2),
            'bestStreak': analysis['bestStreak'],
            'maxConsecutiveLosses': analysis['maxConsecutiveLosses']
        },
        'analysis': analysis,
        'weeklyData': weekly_data,
        'metadata': {
            'generatedAt': datetime.now().isoformat(),
            'version': '1.0'
        }
    }
    
    # Save summary
    base_dir = os.getenv('EXPORT_OUTPUT_DIR', 'exports')
    output_file = f"{base_dir}/monthly/{year}-{month:02d}.json"
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Monthly summary generated: {output_file}")
    print(f"   - Total trades: {total_trades}")
    print(f"   - Net P&L: ${summary['statistics']['netPnL']:.2f}")
    print(f"   - Trading days: {analysis['tradingDays']}")
    print(f"   - Consistency: {analysis['consistency']*100:.1f}%")
    
    # Generate human-readable report
    generate_text_report(summary, f"{base_dir}/monthly/{year}-{month:02d}.txt")


def generate_text_report(summary: Dict, filename: str):
    """Generate a human-readable monthly report"""
    with open(filename, 'w', encoding='utf-8') as f:
        stats = summary['statistics']
        
        f.write(f"MONTHLY TRADING REPORT - {summary['monthName']} {summary['year']}\n")
        f.write("=" * 60 + "\n\n")
        
        f.write(f"Account: {summary['account']}\n")
        f.write(f"Generated: {summary['exportDate']}\n\n")
        
        f.write("PERFORMANCE SUMMARY\n")
        f.write("-" * 30 + "\n")
        f.write(f"Total Trades:        {stats['totalTrades']:>10}\n")
        f.write(f"Trading Days:        {stats['tradingDays']:>10}\n")
        f.write(f"Gross P&L:          ${stats['totalPnL']:>10.2f}\n")
        f.write(f"Commissions:        ${stats['totalCommission']:>10.2f}\n")
        f.write(f"Net P&L:            ${stats['netPnL']:>10.2f}\n\n")
        
        f.write("RISK METRICS\n")
        f.write("-" * 30 + "\n")
        f.write(f"Avg Daily P&L:      ${stats['avgDailyPnL']:>10.2f}\n")
        f.write(f"Consistency:         {stats['consistency']*100:>10.1f}%\n")
        f.write(f"Sharpe Ratio:        {stats['sharpeRatio']:>10.2f}\n")
        f.write(f"Profit Factor:       {stats['profitFactor']:>10.2f}\n")
        f.write(f"Worst Drawdown:     ${stats['worstDrawdown']:>10.2f}\n")
        f.write(f"Best Win Streak:     {stats['bestStreak']:>10}\n")
        f.write(f"Max Losing Streak:   {stats['maxConsecutiveLosses']:>10}\n")
    
    print(f"✅ Text report generated: {filename}")


if __name__ == "__main__":
    generate_monthly_summary()