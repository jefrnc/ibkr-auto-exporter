#!/usr/bin/env python3
"""
Generate monthly data JSON files for IBKR trading performance
Creates individual monthly data for detailed monthly views
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any


def load_json_file(filepath: str) -> Dict:
    """Load JSON file safely"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return None


def generate_monthly_data():
    """Generate JSON files for each month with detailed data"""
    base_dir = os.getenv('EXPORT_OUTPUT_DIR', 'exports')
    year = datetime.now().year
    
    # Create directory for monthly data
    os.makedirs('docs/data/monthly', exist_ok=True)
    
    print("📅 Generating monthly data files...")
    
    # Process each month
    for month in range(1, 13):
        month_trades = []
        month_data = {
            'month': month,
            'year': year,
            'trades': [],
            'dailyData': {},
            'summary': {
                'totalTrades': 0,
                'totalPnL': 0,
                'winRate': 0,
                'bestDay': None,
                'bestDayPnL': -float('inf'),
                'worstDay': None,
                'worstDayPnL': float('inf'),
                'tradingDays': 0,
                'totalCommission': 0
            }
        }
        
        # Collect all trades for the month
        for day in range(1, 32):
            try:
                date_str = f"{year}-{month:02d}-{day:02d}"
                daily_file = f"{base_dir}/daily/{date_str}.json"
                
                if os.path.exists(daily_file):
                    daily_data = load_json_file(daily_file)
                    if daily_data and daily_data.get('trades'):
                        # Save daily data
                        month_data['dailyData'][date_str] = {
                            'trades': len(daily_data['trades']),
                            'pnl': daily_data['summary']['netPnL'],
                            'winRate': daily_data['summary'].get('winRate', 0),
                            'commission': daily_data['summary'].get('totalCommission', 0)
                        }
                        
                        # Add trades
                        month_trades.extend(daily_data['trades'])
                        
                        # Update summary
                        month_data['summary']['totalTrades'] += len(daily_data['trades'])
                        month_data['summary']['totalPnL'] += daily_data['summary']['netPnL']
                        month_data['summary']['totalCommission'] += daily_data['summary'].get('totalCommission', 0)
                        month_data['summary']['tradingDays'] += 1
                        
                        # Best/worst day
                        if daily_data['summary']['netPnL'] > month_data['summary']['bestDayPnL']:
                            month_data['summary']['bestDayPnL'] = daily_data['summary']['netPnL']
                            month_data['summary']['bestDay'] = date_str
                        
                        if daily_data['summary']['netPnL'] < month_data['summary']['worstDayPnL']:
                            month_data['summary']['worstDayPnL'] = daily_data['summary']['netPnL']
                            month_data['summary']['worstDay'] = date_str
            except:
                continue
        
        # Calculate win rate
        if month_trades:
            winning_trades = [t for t in month_trades if t.get('pnl', 0) > 0]
            month_data['summary']['winRate'] = len(winning_trades) / len(month_trades) * 100
            
            # Sort trades by P&L
            sorted_trades = sorted(month_trades, key=lambda x: x.get('pnl', 0), reverse=True)
            
            # Top 5 winners and losers
            month_data['topWinners'] = sorted_trades[:5] if len(sorted_trades) >= 5 else sorted_trades[:len([t for t in sorted_trades if t.get('pnl', 0) > 0])]
            month_data['topLosers'] = sorted([t for t in sorted_trades if t.get('pnl', 0) < 0], key=lambda x: x.get('pnl', 0))[:5]
        
        # Save monthly file
        month_file = f"docs/data/monthly/{year}-{month:02d}.json"
        with open(month_file, 'w', encoding='utf-8') as f:
            json.dump(month_data, f, indent=2, ensure_ascii=False)
        
        if month_data['summary']['totalTrades'] > 0:
            print(f"✅ Generated data for {year}-{month:02d}: {month_data['summary']['totalTrades']} trades")


if __name__ == "__main__":
    generate_monthly_data()