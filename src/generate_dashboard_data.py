#!/usr/bin/env python3
"""
Generate dashboard data JSON for IBKR trading performance
Creates aggregated data for web visualization
"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any


def load_json_file(filepath: str) -> Dict:
    """Load JSON file safely"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}


def generate_dashboard_data():
    """Generate dashboard data from daily exports"""
    base_dir = os.getenv('EXPORT_OUTPUT_DIR', 'exports')
    daily_dir = Path(f'{base_dir}/daily')
    
    print("📊 Generating dashboard data...")
    
    # Initialize data structure
    year_data = {}
    total_trades = 0
    total_pnl = 0
    trading_days = 0
    profit_days = 0
    loss_days = 0
    best_day = {"date": "", "pnl": -float('inf')}
    worst_day = {"date": "", "pnl": float('inf')}
    
    # Load all daily files
    daily_files = sorted(daily_dir.glob('20*.json'))
    
    for file in daily_files:
        # Skip position and cash files
        if '_positions' in str(file) or '_cash' in str(file):
            continue
            
        data = load_json_file(file)
        if not data or 'summary' not in data:
            continue
            
        date = data.get('date', file.stem)
        summary = data['summary']
        
        # Extract metrics
        day_trades = summary.get('totalTrades', 0)
        day_pnl = summary.get('netPnL', 0)
        
        if day_trades > 0:
            trading_days += 1
            total_trades += day_trades
            total_pnl += day_pnl
            
            # Calculate win rate for the day
            trades = data.get('trades', [])
            if trades:
                winners = sum(1 for t in trades if t.get('pnl', 0) > 0)
                win_rate = winners / len(trades) if trades else 0
            else:
                win_rate = 0
            
            # Store day data
            year_data[date] = {
                "trades": day_trades,
                "pnl": round(day_pnl, 2),
                "winRate": win_rate
            }
            
            # Track best/worst days
            if day_pnl > best_day["pnl"]:
                best_day = {"date": date, "pnl": day_pnl}
            if day_pnl < worst_day["pnl"]:
                worst_day = {"date": date, "pnl": day_pnl}
                
            # Count profit/loss days
            if day_pnl > 0:
                profit_days += 1
            elif day_pnl < 0:
                loss_days += 1
    
    # Calculate statistics
    win_rate = (profit_days / trading_days * 100) if trading_days > 0 else 0
    daily_avg = total_pnl / trading_days if trading_days > 0 else 0
    
    # Build dashboard data
    dashboard_data = {
        "yearData": year_data,
        "yearStats": {
            "trading_days": trading_days,
            "total_trades": total_trades,
            "total_pnl": round(total_pnl, 2),
            "win_rate": round(win_rate, 2),
            "profit_days": profit_days,
            "profit_days_pct": round(profit_days / trading_days * 100, 2) if trading_days > 0 else 0,
            "loss_days": loss_days,
            "loss_days_pct": round(loss_days / trading_days * 100, 2) if trading_days > 0 else 0,
            "best_day": best_day["date"],
            "best_day_pnl": round(best_day["pnl"], 2) if best_day["date"] else 0,
            "worst_day": worst_day["date"],
            "worst_day_pnl": round(worst_day["pnl"], 2) if worst_day["date"] else 0,
            "daily_avg": round(daily_avg, 2)
        },
        "metadata": {
            "lastUpdate": datetime.now().isoformat(),
            "exportedTrades": total_trades,
            "source": "IBKR Flex Web Service"
        }
    }
    
    # Check for cost basis filter from environment
    cost_min = os.getenv('COST_BASIS_MIN', '')
    cost_max = os.getenv('COST_BASIS_MAX', '')
    
    if cost_min or cost_max:
        dashboard_data["metadata"]["costBasisFilter"] = {}
        if cost_min:
            dashboard_data["metadata"]["costBasisFilter"]["min"] = float(cost_min)
        if cost_max:
            dashboard_data["metadata"]["costBasisFilter"]["max"] = float(cost_max)
    
    # Save dashboard data
    output_file = "docs/dashboard-data.json"
    os.makedirs("docs", exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(dashboard_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Dashboard data generated: {output_file}")
    print(f"   - Trading days: {trading_days}")
    print(f"   - Total trades: {total_trades}")
    print(f"   - Total P&L: ${total_pnl:.2f}")
    print(f"   - Win rate: {win_rate:.1f}%")
    
    return dashboard_data


if __name__ == "__main__":
    generate_dashboard_data()