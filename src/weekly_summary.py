#!/usr/bin/env python3
"""
Weekly summary generator for IBKR trades
Consolidates daily exports into weekly analytics
"""

import os
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Tuple
from collections import defaultdict


def get_week_dates(date=None) -> Tuple[str, str, int, int]:
    """Get start and end dates of the week"""
    if date is None:
        date = datetime.now()
    elif isinstance(date, str):
        date = datetime.strptime(date, '%Y-%m-%d')
    
    # Week starts on Monday
    start = date - timedelta(days=date.weekday())
    end = start + timedelta(days=6)
    
    week_number = date.isocalendar()[1]
    year = date.year
    
    return start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d'), year, week_number


def load_daily_files(week_start: str, week_end: str) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """Load all daily files for the week"""
    base_dir = os.getenv('EXPORT_OUTPUT_DIR', 'exports')
    daily_dir = Path(f'{base_dir}/daily')
    
    all_trades = []
    daily_summaries = []
    positions_data = []
    
    start_date = datetime.strptime(week_start, '%Y-%m-%d')
    end_date = datetime.strptime(week_end, '%Y-%m-%d')
    
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        
        # Load daily trades file
        daily_file = daily_dir / f'{date_str}.json'
        if daily_file.exists():
            with open(daily_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                trades = data.get('trades', [])
                all_trades.extend(trades)
                
                # Add date to summary for tracking
                summary = data.get('summary', {})
                summary['date'] = date_str
                summary['account'] = data.get('account', '')
                daily_summaries.append(summary)
        
        # Load positions file if exists
        positions_file = daily_dir / f'{date_str}_positions.json'
        if positions_file.exists():
            with open(positions_file, 'r', encoding='utf-8') as f:
                pos_data = json.load(f)
                positions_data.append({
                    'date': date_str,
                    'positions': pos_data.get('positions', [])
                })
        
        current_date += timedelta(days=1)
    
    return all_trades, daily_summaries, positions_data


def analyze_trading_patterns(trades: List[Dict]) -> Dict[str, Any]:
    """Analyze trading patterns for the week"""
    patterns = {
        'byHour': defaultdict(lambda: {'count': 0, 'pnl': 0, 'volume': 0}),
        'bySymbol': defaultdict(lambda: {'count': 0, 'pnl': 0, 'volume': 0, 'commission': 0}),
        'byAssetCategory': defaultdict(lambda: {'count': 0, 'pnl': 0, 'volume': 0}),
        'byDayOfWeek': defaultdict(lambda: {'count': 0, 'pnl': 0}),
        'largestWin': {'pnl': 0, 'trade': None},
        'largestLoss': {'pnl': 0, 'trade': None},
        'mostTraded': {'symbol': '', 'count': 0},
        'tradingDays': set(),
        'totalVolume': 0,
        'avgTradeSize': 0
    }
    
    symbol_counts = defaultdict(int)
    
    for trade in trades:
        # Extract time components
        trade_time = trade.get('tradeTime', '')
        if trade_time and len(trade_time) >= 2:
            hour = int(trade_time[:2])
            patterns['byHour'][hour]['count'] += 1
            patterns['byHour'][hour]['pnl'] += trade.get('pnl', 0)
            patterns['byHour'][hour]['volume'] += abs(trade.get('quantity', 0) * trade.get('tradePrice', 0))
        
        # By symbol
        symbol = trade.get('symbol', 'Unknown')
        patterns['bySymbol'][symbol]['count'] += 1
        patterns['bySymbol'][symbol]['pnl'] += trade.get('pnl', 0)
        patterns['bySymbol'][symbol]['volume'] += abs(trade.get('quantity', 0) * trade.get('tradePrice', 0))
        patterns['bySymbol'][symbol]['commission'] += trade.get('commission', 0)
        symbol_counts[symbol] += 1
        
        # By asset category
        category = trade.get('assetCategory', 'Unknown')
        patterns['byAssetCategory'][category]['count'] += 1
        patterns['byAssetCategory'][category]['pnl'] += trade.get('pnl', 0)
        patterns['byAssetCategory'][category]['volume'] += abs(trade.get('quantity', 0) * trade.get('tradePrice', 0))
        
        # By day of week
        trade_date = trade.get('tradeDate', '')
        if trade_date:
            # Handle both YYYYMMDD and YYYY-MM-DD formats
            if len(trade_date) == 8 and trade_date.isdigit():
                # Convert YYYYMMDD to YYYY-MM-DD
                trade_date_formatted = f"{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:8]}"
            else:
                trade_date_formatted = trade_date
            
            day_of_week = datetime.strptime(trade_date_formatted, '%Y-%m-%d').strftime('%A')
            patterns['byDayOfWeek'][day_of_week]['count'] += 1
            patterns['byDayOfWeek'][day_of_week]['pnl'] += trade.get('pnl', 0)
            patterns['tradingDays'].add(trade_date_formatted)
        
        # Track largest wins/losses
        pnl = trade.get('pnl', 0)
        if pnl > patterns['largestWin']['pnl']:
            patterns['largestWin'] = {'pnl': pnl, 'trade': trade}
        if pnl < patterns['largestLoss']['pnl']:
            patterns['largestLoss'] = {'pnl': pnl, 'trade': trade}
        
        # Total volume
        patterns['totalVolume'] += abs(trade.get('quantity', 0) * trade.get('tradePrice', 0))
    
    # Find most traded symbol
    if symbol_counts:
        most_traded = max(symbol_counts.items(), key=lambda x: x[1])
        patterns['mostTraded'] = {'symbol': most_traded[0], 'count': most_traded[1]}
    
    # Calculate average trade size
    if trades:
        patterns['avgTradeSize'] = patterns['totalVolume'] / len(trades)
    
    # Convert sets to lists for JSON serialization
    patterns['tradingDays'] = sorted(list(patterns['tradingDays']))
    
    # Convert defaultdicts to regular dicts
    patterns['byHour'] = dict(patterns['byHour'])
    patterns['bySymbol'] = dict(patterns['bySymbol'])
    patterns['byAssetCategory'] = dict(patterns['byAssetCategory'])
    patterns['byDayOfWeek'] = dict(patterns['byDayOfWeek'])
    
    return patterns


def calculate_week_statistics(trades: List[Dict], daily_summaries: List[Dict]) -> Dict[str, Any]:
    """Calculate comprehensive weekly statistics"""
    if not trades:
        return {
            'totalTrades': 0,
            'totalPnL': 0,
            'totalCommission': 0,
            'netPnL': 0,
            'winRate': 0,
            'winners': 0,
            'losers': 0,
            'avgDailyPnL': 0,
            'bestDay': None,
            'worstDay': None,
            'consistency': 0
        }
    
    # Aggregate statistics
    total_pnl = sum(trade.get('pnl', 0) for trade in trades)
    total_commission = sum(trade.get('commission', 0) for trade in trades)
    winners = sum(1 for trade in trades if trade.get('pnl', 0) > 0)
    losers = sum(1 for trade in trades if trade.get('pnl', 0) < 0)
    
    # Daily analysis
    best_day = None
    worst_day = None
    positive_days = 0
    
    for summary in daily_summaries:
        if summary.get('totalTrades', 0) > 0:
            daily_pnl = summary.get('netPnL', 0)
            
            if not best_day or daily_pnl > best_day['pnl']:
                best_day = {'date': summary['date'], 'pnl': daily_pnl}
            
            if not worst_day or daily_pnl < worst_day['pnl']:
                worst_day = {'date': summary['date'], 'pnl': daily_pnl}
            
            if daily_pnl > 0:
                positive_days += 1
    
    trading_days = len([s for s in daily_summaries if s.get('totalTrades', 0) > 0])
    
    return {
        'totalTrades': len(trades),
        'totalPnL': round(total_pnl, 2),
        'totalCommission': round(total_commission, 2),
        'netPnL': round(total_pnl - total_commission, 2),
        'winRate': round(winners / (winners + losers), 4) if (winners + losers) > 0 else 0,
        'winners': winners,
        'losers': losers,
        'avgDailyPnL': round(total_pnl / trading_days, 2) if trading_days > 0 else 0,
        'bestDay': best_day,
        'worstDay': worst_day,
        'consistency': round(positive_days / trading_days, 4) if trading_days > 0 else 0,
        'tradingDays': trading_days
    }


def generate_weekly_summary(week_date=None):
    """Generate weekly summary"""
    # Get week dates
    week_start, week_end, year, week_number = get_week_dates(week_date)
    
    print(f"📊 Generating weekly summary for week {week_number} of {year}")
    print(f"   Period: {week_start} to {week_end}")
    
    # Load daily data
    trades, daily_summaries, positions_data = load_daily_files(week_start, week_end)
    
    if not trades and not daily_summaries:
        print("ℹ️ No data found for this week")
        return
    
    # Analyze patterns
    patterns = analyze_trading_patterns(trades)
    
    # Calculate statistics
    statistics = calculate_week_statistics(trades, daily_summaries)
    
    # Get account info from first daily summary
    account = daily_summaries[0].get('account', 'Unknown') if daily_summaries else 'Unknown'
    
    # Prepare summary
    summary = {
        'exportDate': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'account': account,
        'year': year,
        'weekNumber': week_number,
        'weekStart': week_start,
        'weekEnd': week_end,
        'statistics': statistics,
        'patterns': patterns,
        'dailySummaries': daily_summaries,
        'metadata': {
            'generatedAt': datetime.now().isoformat(),
            'version': '1.0'
        }
    }
    
    # Save weekly summary
    base_dir = os.getenv('EXPORT_OUTPUT_DIR', 'exports')
    output_file = f"{base_dir}/weekly/{year}-W{week_number:02d}.json"
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Weekly summary generated: {output_file}")
    print(f"   - Total trades: {statistics['totalTrades']}")
    print(f"   - Net P&L: ${statistics['netPnL']:.2f}")
    print(f"   - Win rate: {statistics['winRate']*100:.1f}%")
    print(f"   - Trading days: {statistics['tradingDays']}")
    
    if patterns['mostTraded']['symbol']:
        print(f"   - Most traded: {patterns['mostTraded']['symbol']} ({patterns['mostTraded']['count']} trades)")


if __name__ == "__main__":
    # Allow passing a specific date
    if len(sys.argv) > 1:
        week_date = sys.argv[1]
        generate_weekly_summary(week_date)
    else:
        generate_weekly_summary()