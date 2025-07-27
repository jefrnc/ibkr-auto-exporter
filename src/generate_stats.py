#!/usr/bin/env python3
"""
Generate statistics for README
Updates README.md with current trading statistics
"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional


def load_json_file(filepath: str) -> Optional[Dict]:
    """Load JSON file safely"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None


def get_current_week_stats() -> Dict[str, Any]:
    """Get current week statistics"""
    today = datetime.now()
    week_number = today.isocalendar()[1]
    year = today.year
    
    base_dir = os.getenv('EXPORT_OUTPUT_DIR', 'exports')
    weekly_file = f"{base_dir}/weekly/{year}-W{week_number:02d}.json"
    
    data = load_json_file(weekly_file)
    if data:
        stats = data.get('statistics', {})
        return {
            'week': week_number,
            'trades': stats.get('totalTrades', 0),
            'pnl': stats.get('netPnL', 0),
            'winRate': stats.get('winRate', 0)
        }
    
    # If no weekly file, calculate from daily files
    return calculate_current_week_from_daily()


def calculate_current_week_from_daily() -> Dict[str, Any]:
    """Calculate current week stats from daily files"""
    today = datetime.now()
    week_start = today - timedelta(days=today.weekday())
    
    base_dir = os.getenv('EXPORT_OUTPUT_DIR', 'exports')
    daily_dir = Path(f'{base_dir}/daily')
    
    total_trades = 0
    total_pnl = 0
    winners = 0
    losers = 0
    
    for i in range(7):
        date = week_start + timedelta(days=i)
        if date > today:
            break
            
        daily_file = daily_dir / f"{date.strftime('%Y-%m-%d')}.json"
        if daily_file.exists():
            data = load_json_file(str(daily_file))
            if data:
                summary = data.get('summary', {})
                total_trades += summary.get('totalTrades', 0)
                total_pnl += summary.get('netPnL', 0)
                winners += summary.get('winners', 0)
                losers += summary.get('losers', 0)
    
    win_rate = winners / (winners + losers) if (winners + losers) > 0 else 0
    
    return {
        'week': today.isocalendar()[1],
        'trades': total_trades,
        'pnl': total_pnl,
        'winRate': win_rate
    }


def get_last_week_stats() -> Dict[str, Any]:
    """Get last week statistics"""
    today = datetime.now()
    last_week = today - timedelta(weeks=1)
    week_number = last_week.isocalendar()[1]
    year = last_week.year
    
    base_dir = os.getenv('EXPORT_OUTPUT_DIR', 'exports')
    weekly_file = f"{base_dir}/weekly/{year}-W{week_number:02d}.json"
    
    data = load_json_file(weekly_file)
    if data:
        stats = data.get('statistics', {})
        return {
            'week': week_number,
            'trades': stats.get('totalTrades', 0),
            'pnl': stats.get('netPnL', 0),
            'winRate': stats.get('winRate', 0)
        }
    
    return {'week': week_number, 'trades': 0, 'pnl': 0, 'winRate': 0}


def get_current_month_stats() -> Dict[str, Any]:
    """Get current month statistics"""
    today = datetime.now()
    month = today.month
    year = today.year
    
    base_dir = os.getenv('EXPORT_OUTPUT_DIR', 'exports')
    monthly_file = f"{base_dir}/monthly/{year}-{month:02d}.json"
    
    data = load_json_file(monthly_file)
    if data:
        stats = data.get('statistics', {})
        return {
            'month': today.strftime('%B'),
            'trades': stats.get('totalTrades', 0),
            'pnl': stats.get('netPnL', 0),
            'winRate': stats.get('winRate', 0)
        }
    
    # Calculate from daily files
    return calculate_month_from_daily(year, month)


def calculate_month_from_daily(year: int, month: int) -> Dict[str, Any]:
    """Calculate month stats from daily files"""
    base_dir = os.getenv('EXPORT_OUTPUT_DIR', 'exports')
    daily_dir = Path(f'{base_dir}/daily')
    
    total_trades = 0
    total_pnl = 0
    winners = 0
    losers = 0
    
    # Check all days of the month
    for day in range(1, 32):
        try:
            date = datetime(year, month, day)
            daily_file = daily_dir / f"{date.strftime('%Y-%m-%d')}.json"
            
            if daily_file.exists():
                data = load_json_file(str(daily_file))
                if data:
                    summary = data.get('summary', {})
                    total_trades += summary.get('totalTrades', 0)
                    total_pnl += summary.get('netPnL', 0)
                    winners += summary.get('winners', 0)
                    losers += summary.get('losers', 0)
        except ValueError:
            # Invalid day for this month
            break
    
    win_rate = winners / (winners + losers) if (winners + losers) > 0 else 0
    
    return {
        'month': datetime(year, month, 1).strftime('%B'),
        'trades': total_trades,
        'pnl': total_pnl,
        'winRate': win_rate
    }


def get_last_month_stats() -> Dict[str, Any]:
    """Get last month statistics"""
    today = datetime.now()
    first_day = today.replace(day=1)
    last_month = first_day - timedelta(days=1)
    
    month = last_month.month
    year = last_month.year
    
    base_dir = os.getenv('EXPORT_OUTPUT_DIR', 'exports')
    monthly_file = f"{base_dir}/monthly/{year}-{month:02d}.json"
    
    data = load_json_file(monthly_file)
    if data:
        stats = data.get('statistics', {})
        return {
            'month': last_month.strftime('%B'),
            'trades': stats.get('totalTrades', 0),
            'pnl': stats.get('netPnL', 0),
            'winRate': stats.get('winRate', 0)
        }
    
    return calculate_month_from_daily(year, month)


def calculate_yearly_projection() -> Dict[str, Any]:
    """Calculate yearly projection based on YTD performance"""
    today = datetime.now()
    year = today.year
    
    base_dir = os.getenv('EXPORT_OUTPUT_DIR', 'exports')
    
    # Calculate YTD stats
    total_trades = 0
    total_pnl = 0
    trading_days = 0
    
    # Go through all monthly files
    for month in range(1, today.month + 1):
        monthly_file = f"{base_dir}/monthly/{year}-{month:02d}.json"
        data = load_json_file(monthly_file)
        
        if data:
            stats = data.get('statistics', {})
            total_trades += stats.get('totalTrades', 0)
            total_pnl += stats.get('netPnL', 0)
            trading_days += stats.get('tradingDays', 0)
        else:
            # Calculate from daily files
            month_stats = calculate_month_from_daily(year, month)
            total_trades += month_stats['trades']
            total_pnl += month_stats['pnl']
    
    # Calculate projection
    days_passed = (today - datetime(year, 1, 1)).days + 1
    days_remaining = (datetime(year, 12, 31) - today).days
    
    if days_passed > 0:
        daily_rate = total_pnl / days_passed
        projected_pnl = total_pnl + (daily_rate * days_remaining)
        
        trade_rate = total_trades / days_passed
        projected_trades = total_trades + (trade_rate * days_remaining)
    else:
        projected_pnl = 0
        projected_trades = 0
    
    return {
        'actualTrades': total_trades,
        'actualPnL': total_pnl,
        'projectedTrades': int(projected_trades),
        'projectedPnL': projected_pnl,
        'daysRemaining': days_remaining
    }


def format_pnl(value: float) -> str:
    """Format P&L with color"""
    if value > 0:
        return f"**+${value:.2f}**"
    elif value < 0:
        return f"**-${abs(value):.2f}**"
    else:
        return "$0.00"


def generate_stats_table() -> str:
    """Generate statistics table in Markdown"""
    # Get all statistics
    current_week = get_current_week_stats()
    last_week = get_last_week_stats()
    current_month = get_current_month_stats()
    last_month = get_last_month_stats()
    yearly = calculate_yearly_projection()
    
    # Build table
    table = f"""### 📊 Live Trading Statistics

| Period | Trades | P&L | Win Rate |
|--------|--------|-----|----------|
| **Week {current_week['week']} (current)** | {current_week['trades']} | {format_pnl(current_week['pnl'])} | {current_week['winRate']*100:.1f}% |
| Week {last_week['week']} | {last_week['trades']} | {format_pnl(last_week['pnl'])} | {last_week['winRate']*100:.1f}% |
| **{current_month['month']} (current)** | {current_month['trades']} | {format_pnl(current_month['pnl'])} | {current_month['winRate']*100:.1f}% |
| {last_month['month']} | {last_month['trades']} | {format_pnl(last_month['pnl'])} | {last_month['winRate']*100:.1f}% |

#### 📈 Yearly Projection

| Metric | Actual YTD | Projected EOY |
|--------|------------|---------------|
| **Trades** | {yearly['actualTrades']} | {yearly['projectedTrades']} |
| **P&L** | {format_pnl(yearly['actualPnL'])} | {format_pnl(yearly['projectedPnL'])} |

*Based on current performance with {yearly['daysRemaining']} days remaining*

*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')} UTC*"""
    
    return table


def update_readme(stats_table: str):
    """Update README with statistics"""
    readme_path = "README.md"
    
    try:
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find markers
        start_marker = "<!-- STATS_START -->"
        end_marker = "<!-- STATS_END -->"
        
        start_idx = content.find(start_marker)
        end_idx = content.find(end_marker)
        
        if start_idx != -1 and end_idx != -1:
            # Replace content between markers
            new_content = (
                content[:start_idx + len(start_marker)] +
                "\n" + stats_table + "\n" +
                content[end_idx:]
            )
            
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print("✅ README updated with latest statistics")
        else:
            print("⚠️ Could not find stats markers in README")
            
    except FileNotFoundError:
        print("⚠️ README.md not found")
    except Exception as e:
        print(f"❌ Error updating README: {e}")


if __name__ == "__main__":
    stats_table = generate_stats_table()
    print(stats_table)
    update_readme(stats_table)