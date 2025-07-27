#!/usr/bin/env python3
"""
Daily exporter for IBKR trades
Downloads and processes daily trading data from Interactive Brokers
"""

import os
import json
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ibkr_simple_exporter import SimpleIBKRExporter


def obfuscate_account(account_id: str) -> str:
    """Obfuscate account ID for privacy"""
    if not account_id or len(account_id) < 4:
        return account_id
    
    # Keep first letter and last 2 characters
    return f"{account_id[0]}{'*' * (len(account_id) - 3)}{account_id[-2:]}"


def ensure_directory_structure():
    """Create directory structure for exports"""
    base_dir = os.getenv('EXPORT_OUTPUT_DIR', 'exports')
    
    dirs = [
        f'{base_dir}/daily',
        f'{base_dir}/weekly', 
        f'{base_dir}/monthly'
    ]
    
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    return base_dir


def process_trades_by_date(trades: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Group trades by date"""
    trades_by_date = {}
    
    for trade in trades:
        # Use tradeDate for grouping
        trade_date = trade.get('tradeDate', trade.get('reportDate', ''))
        
        if trade_date:
            # Convert YYYYMMDD to YYYY-MM-DD format
            if len(trade_date) == 8 and trade_date.isdigit():
                trade_date = f"{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:8]}"
            
            if trade_date not in trades_by_date:
                trades_by_date[trade_date] = []
            trades_by_date[trade_date].append(trade)
    
    return trades_by_date


def calculate_daily_summary(trades: List[Dict[str, Any]], base_currency: str = 'USD') -> Dict[str, Any]:
    """Calculate daily summary statistics"""
    if not trades:
        return {
            'totalTrades': 0,
            'totalPnL': 0,
            'totalCommission': 0,
            'netPnL': 0,
            'winRate': 0,
            'winners': 0,
            'losers': 0,
            'symbols': [],
            'assetCategories': {}
        }
    
    total_pnl = 0
    total_commission = 0
    winners = 0
    losers = 0
    symbols = set()
    asset_categories = {}
    
    for trade in trades:
        # Extract P&L (use fifoPnlRealized for closed trades)
        pnl = trade.get('pnl', 0) or trade.get('fifoPnlRealized', 0)
        commission = trade.get('commission', 0)
        
        # Convert to base currency if needed (simplified - you'd need exchange rates)
        currency = trade.get('currency', trade.get('ibCommissionCurrency', 'USD'))
        if currency != base_currency:
            # TODO: Implement currency conversion
            pass
        
        total_pnl += pnl
        total_commission += commission
        
        if pnl > 0:
            winners += 1
        elif pnl < 0:
            losers += 1
        
        # Track symbols
        symbol = trade.get('symbol', '')
        if symbol:
            symbols.add(symbol)
        
        # Track asset categories
        category = trade.get('assetCategory', 'Unknown')
        if category not in asset_categories:
            asset_categories[category] = 0
        asset_categories[category] += 1
    
    win_rate = winners / (winners + losers) if (winners + losers) > 0 else 0
    
    return {
        'totalTrades': len(trades),
        'totalPnL': round(total_pnl, 2),
        'totalCommission': round(total_commission, 2),
        'netPnL': round(total_pnl - total_commission, 2),
        'winRate': round(win_rate, 4),
        'winners': winners,
        'losers': losers,
        'symbols': sorted(list(symbols)),
        'assetCategories': asset_categories
    }


def export_daily_trades():
    """Main export function"""
    # Get configuration
    token = os.getenv('IBKR_TOKEN')
    query_id = os.getenv('IBKR_QUERY_ID')
    obfuscate = os.getenv('OBFUSCATE_ACCOUNT', 'true').lower() == 'true'
    base_currency = os.getenv('BASE_CURRENCY', 'USD')
    
    # Cost basis filter configuration
    cost_basis_min = os.getenv('COST_BASIS_MIN', '')
    cost_basis_max = os.getenv('COST_BASIS_MAX', '')
    
    # Convert to float if provided
    try:
        cost_basis_min = float(cost_basis_min) if cost_basis_min else None
    except ValueError:
        cost_basis_min = None
        
    try:
        cost_basis_max = float(cost_basis_max) if cost_basis_max else None
    except ValueError:
        cost_basis_max = None
    
    if not token or not query_id:
        print("Error: IBKR_TOKEN and IBKR_QUERY_ID must be set")
        sys.exit(1)
    
    # Ensure directories exist
    base_dir = ensure_directory_structure()
    
    # Create exporter
    exporter = SimpleIBKRExporter(token, query_id)
    
    try:
        # Download report
        print("📊 Downloading IBKR Flex report...")
        xml_root = exporter.download_flex_report()
        
        if not xml_root:
            print("❌ Failed to download report")
            sys.exit(1)
        
        # Extract data
        account_info = exporter.extract_account_info(xml_root)
        trades = exporter.extract_trades(xml_root)
        positions = exporter.extract_positions(xml_root)
        cash_report = exporter.extract_cash_report(xml_root)
        
        print(f"✅ Found {len(trades)} trades")
        
        # Apply cost basis filter if configured
        if cost_basis_min is not None or cost_basis_max is not None:
            original_count = len(trades)
            filtered_trades = []
            
            for trade in trades:
                cost = abs(trade.get('cost', 0))  # Use absolute value for cost
                
                # Check if trade meets filter criteria
                if cost_basis_min is not None and cost < cost_basis_min:
                    continue
                if cost_basis_max is not None and cost > cost_basis_max:
                    continue
                    
                filtered_trades.append(trade)
            
            trades = filtered_trades
            
            if cost_basis_min is not None and cost_basis_max is not None:
                print(f"🔍 Filtered trades with cost basis ${cost_basis_min:.2f} - ${cost_basis_max:.2f}")
            elif cost_basis_min is not None:
                print(f"🔍 Filtered trades with cost basis >= ${cost_basis_min:.2f}")
            elif cost_basis_max is not None:
                print(f"🔍 Filtered trades with cost basis <= ${cost_basis_max:.2f}")
                
            print(f"   Kept {len(trades)} of {original_count} trades")
        
        # Group trades by date
        trades_by_date = process_trades_by_date(trades)
        
        # Export each day's trades
        exported_dates = []
        
        for trade_date, day_trades in trades_by_date.items():
            # Calculate summary for the day
            summary = calculate_daily_summary(day_trades, base_currency)
            
            # Get account ID (use first trade's account)
            account_id = day_trades[0].get('accountId', 'Unknown') if day_trades else 'Unknown'
            display_account = obfuscate_account(account_id) if obfuscate else account_id
            
            # Obfuscate account in individual trades if needed
            if obfuscate:
                for trade in day_trades:
                    if 'accountId' in trade:
                        trade['accountId'] = obfuscate_account(trade['accountId'])
            
            # Prepare export data
            export_data = {
                'exportDate': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'account': display_account,
                'date': trade_date,
                'trades': day_trades,
                'summary': summary
            }
            
            # Save to file
            filename = f"{base_dir}/daily/{trade_date}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            exported_dates.append(trade_date)
            print(f"✅ Exported {trade_date}: {summary['totalTrades']} trades, "
                  f"P&L: ${summary['netPnL']:.2f}")
        
        # Also export today's positions and cash report
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Export current positions
        if positions:
            # Obfuscate account in positions if needed
            if obfuscate:
                for position in positions:
                    if 'accountId' in position:
                        position['accountId'] = obfuscate_account(position['accountId'])
            
            positions_file = f"{base_dir}/daily/{today}_positions.json"
            with open(positions_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'exportDate': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'date': today,
                    'positions': positions,
                    'count': len(positions)
                }, f, indent=2, ensure_ascii=False)
            print(f"✅ Exported {len(positions)} open positions")
        
        # Export cash report
        if any(cash_report.values()):  # Check if any account has cash data
            cash_file = f"{base_dir}/daily/{today}_cash.json"
            with open(cash_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'exportDate': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'date': today,
                    'cashReport': cash_report
                }, f, indent=2, ensure_ascii=False)
            print(f"✅ Exported cash report")
        
        # If no trades today, create empty file to show we ran
        if today not in exported_dates:
            # Get first account ID
            first_account_id = list(account_info.keys())[0] if account_info else 'Unknown'
            display_account = obfuscate_account(first_account_id) if obfuscate else first_account_id
            
            empty_data = {
                'exportDate': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'account': display_account,
                'date': today,
                'trades': [],
                'summary': calculate_daily_summary([], base_currency)
            }
            
            filename = f"{base_dir}/daily/{today}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(empty_data, f, indent=2, ensure_ascii=False)
            
            print(f"ℹ️ No trades for {today}")
        
        # Show account info
        if account_info:
            for acc_id, info in account_info.items():
                display_id = obfuscate_account(acc_id) if obfuscate else acc_id
                print(f"\n📋 Account: {display_id}")
                print(f"   Type: {info.get('type', 'Unknown')}")
                print(f"   Currency: {info.get('currency', 'USD')}")
                print(f"   Last traded: {info.get('lastTradedDate', 'Unknown')}")
        
        print("\n✅ Daily export completed successfully!")
        
        # Note about Flex Query configuration
        if not trades and not positions:
            print("\n⚠️ Note: No trades or positions found.")
            print("   Please ensure your Flex Query includes:")
            print("   - Trades (Execution)")
            print("   - Open Positions")
            print("   - Cash Report")
            print("   You can configure this in IBKR Client Portal under Flex Queries.")
        
    except Exception as e:
        print(f"❌ Error during export: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    export_daily_trades()