#!/usr/bin/env python3
"""
Generate trading calendar visualization
Creates GitHub-style contribution calendar for trading performance
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


def get_year_data(year: int) -> Dict[str, Dict]:
    """Get all trading data for a year"""
    base_dir = os.getenv('EXPORT_OUTPUT_DIR', 'exports')
    daily_dir = Path(f'{base_dir}/daily')
    
    year_data = {}
    
    # Load all daily files for the year
    for file in daily_dir.glob(f'{year}-*.json'):
        if '_positions' not in str(file) and '_cash' not in str(file):
            data = load_json_file(file)
            if data:
                date = data.get('date', '')
                summary = data.get('summary', {})
                year_data[date] = {
                    'pnl': summary.get('netPnL', 0),
                    'trades': summary.get('totalTrades', 0)
                }
    
    return year_data


def generate_svg_calendar(year_data: Dict, year: int) -> str:
    """Generate SVG calendar similar to GitHub contributions"""
    # Configuration
    cell_size = 12
    cell_gap = 3
    months_height = 20
    
    # Calculate dimensions
    width = 53 * (cell_size + cell_gap) + 50  # 53 weeks + margin
    height = 7 * (cell_size + cell_gap) + months_height + 20  # 7 days + header
    
    # Start SVG
    svg = [f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">']
    
    # Add styles
    svg.append('''<style>
        .month { font-size: 10px; fill: #767676; }
        .day { font-size: 9px; fill: #767676; }
        .cell { stroke: #e1e4e8; stroke-width: 1; }
        .cell-profit { fill: #40c463; }
        .cell-loss { fill: #f85149; }
        .cell-breakeven { fill: #ffd33d; }
        .cell-empty { fill: #ebedf0; }
    </style>''')
    
    # Add month labels
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    month_x = 50
    
    for i, month in enumerate(months):
        x = month_x + (i * 4.5 * (cell_size + cell_gap))
        svg.append(f'<text x="{x}" y="12" class="month">{month}</text>')
    
    # Add day labels
    days = ['Mon', 'Wed', 'Fri']
    day_positions = [1, 3, 5]
    
    for i, (day, pos) in enumerate(zip(days, day_positions)):
        y = months_height + pos * (cell_size + cell_gap) + 9
        svg.append(f'<text x="5" y="{y}" class="day">{day}</text>')
    
    # Generate calendar cells
    start_date = datetime(year, 1, 1)
    start_weekday = start_date.weekday()
    
    for week in range(53):
        x = 50 + week * (cell_size + cell_gap)
        
        for day in range(7):
            # Calculate date
            days_from_start = week * 7 + day - start_weekday
            current_date = start_date + timedelta(days=days_from_start)
            
            if current_date.year != year:
                continue
            
            y = months_height + day * (cell_size + cell_gap)
            date_str = current_date.strftime('%Y-%m-%d')
            
            # Determine color based on P&L
            if date_str in year_data:
                pnl = year_data[date_str]['pnl']
                trades = year_data[date_str]['trades']
                
                if trades == 0:
                    color_class = 'cell-empty'
                elif pnl > 0:
                    color_class = 'cell-profit'
                elif pnl < 0:
                    color_class = 'cell-loss'
                else:
                    color_class = 'cell-breakeven'
                
                title = f"{date_str}: ${pnl:.2f} ({trades} trades)"
            else:
                color_class = 'cell-empty'
                title = f"{date_str}: No data"
            
            svg.append(f'<rect x="{x}" y="{y}" width="{cell_size}" height="{cell_size}" '
                      f'class="cell {color_class}" rx="2" ry="2">'
                      f'<title>{title}</title></rect>')
    
    svg.append('</svg>')
    
    return '\n'.join(svg)


def generate_markdown_calendar(year: int) -> str:
    """Generate calendar and statistics in Markdown format"""
    year_data = get_year_data(year)
    
    if not year_data:
        return f"No trading data found for {year}"
    
    # Generate SVG calendar
    svg_calendar = generate_svg_calendar(year_data, year)
    
    # Save SVG file
    base_dir = os.getenv('EXPORT_OUTPUT_DIR', 'exports')
    os.makedirs('.github/assets', exist_ok=True)
    svg_file = f'.github/assets/calendar-{year}.svg'
    
    with open(svg_file, 'w', encoding='utf-8') as f:
        f.write(svg_calendar)
    
    # Calculate statistics
    total_trades = sum(d['trades'] for d in year_data.values())
    total_pnl = sum(d['pnl'] for d in year_data.values())
    trading_days = len([d for d in year_data.values() if d['trades'] > 0])
    profit_days = len([d for d in year_data.values() if d['pnl'] > 0 and d['trades'] > 0])
    loss_days = len([d for d in year_data.values() if d['pnl'] < 0 and d['trades'] > 0])
    
    # Find best and worst days
    trading_data = [(date, data) for date, data in year_data.items() if data['trades'] > 0]
    if trading_data:
        best_day = max(trading_data, key=lambda x: x[1]['pnl'])
        worst_day = min(trading_data, key=lambda x: x[1]['pnl'])
        avg_daily = total_pnl / trading_days if trading_days > 0 else 0
    else:
        best_day = worst_day = (None, {'pnl': 0})
        avg_daily = 0
    
    # Generate markdown
    markdown = f"""## 📅 {year} Trading Calendar

![Trading Calendar]({svg_file})

### Legend
🟩 Profit Day | 🟨 Break Even | 🟥 Loss Day | ⬜ No Trades

### 📊 {year} Statistics

| Metric | Value |
|--------|-------|
| **Total Trading Days** | {trading_days} |
| **Total Trades** | {total_trades} |
| **Total P&L** | ${total_pnl:.2f} |
| **Win Rate** | {(profit_days/trading_days*100 if trading_days > 0 else 0):.1f}% |
| **Profit Days** | {profit_days} ({(profit_days/trading_days*100 if trading_days > 0 else 0):.1f}%) |
| **Loss Days** | {loss_days} ({(loss_days/trading_days*100 if trading_days > 0 else 0):.1f}%) |
| **Best Day** | ${best_day[1]['pnl']:.2f} ({best_day[0] if best_day[0] else 'N/A'}) |
| **Worst Day** | ${worst_day[1]['pnl']:.2f} ({worst_day[0] if worst_day[0] else 'N/A'}) |
| **Daily Average** | ${avg_daily:.2f} |
"""
    
    # Add monthly breakdown
    monthly_stats = {}
    for date_str, data in year_data.items():
        if data['trades'] > 0:
            month = date_str[:7]  # YYYY-MM
            if month not in monthly_stats:
                monthly_stats[month] = {'trades': 0, 'pnl': 0, 'days': 0}
            monthly_stats[month]['trades'] += data['trades']
            monthly_stats[month]['pnl'] += data['pnl']
            monthly_stats[month]['days'] += 1
    
    if monthly_stats:
        markdown += "\n### 📈 Monthly Breakdown\n\n"
        markdown += "| Month | Trades | P&L | Win Rate |\n"
        markdown += "|-------|--------|-----|----------|\n"
        
        for month in sorted(monthly_stats.keys()):
            stats = monthly_stats[month]
            month_name = datetime.strptime(month + '-01', '%Y-%m-%d').strftime('%B')
            
            # Calculate win rate for the month
            month_profit_days = len([date for date, data in year_data.items() 
                                   if date.startswith(month) and data['pnl'] > 0 and data['trades'] > 0])
            win_rate = (month_profit_days / stats['days'] * 100) if stats['days'] > 0 else 0
            
            pnl_display = f"**+${stats['pnl']:.2f}**" if stats['pnl'] > 0 else f"**-${abs(stats['pnl']):.2f}**"
            markdown += f"| {month_name} | {stats['trades']} | {pnl_display} | {win_rate:.1f}% |\n"
    
    return markdown


def update_readme_with_calendar(calendar_content: str):
    """Update README with calendar content"""
    readme_path = "README.md"
    
    try:
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find markers
        start_marker = "<!-- CALENDAR_START -->"
        end_marker = "<!-- CALENDAR_END -->"
        
        start_idx = content.find(start_marker)
        end_idx = content.find(end_marker)
        
        if start_idx != -1 and end_idx != -1:
            # Replace content between markers
            new_content = (
                content[:start_idx + len(start_marker)] +
                "\n" + calendar_content + "\n" +
                content[end_idx:]
            )
            
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print("✅ README updated with calendar")
        else:
            print("⚠️ Could not find calendar markers in README")
            
    except FileNotFoundError:
        print("⚠️ README.md not found")
    except Exception as e:
        print(f"❌ Error updating README: {e}")


if __name__ == "__main__":
    year = datetime.now().year
    calendar_content = generate_markdown_calendar(year)
    print(calendar_content)
    update_readme_with_calendar(calendar_content)