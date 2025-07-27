# 🚀 IBKR Auto-Exporter

[![GitHub Action](https://img.shields.io/badge/GitHub-Action-blue?logo=github)](https://github.com/marketplace/actions/ibkr-auto-exporter)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/github/v/release/jefrnc/ibkr-auto-exporter)](https://github.com/jefrnc/ibkr-auto-exporter/releases)

> Automatically export your trading data from Interactive Brokers with daily snapshots, weekly summaries, and monthly analytics using the Flex Web Service API.

[Español](./docs/README_ES.md) | [Installation](#-quick-start) | [Examples](./examples) | [FAQ](./docs/FAQ.md)

<!-- STATS_START -->
### 📊 Live Trading Statistics

*Statistics will appear here after first export*
<!-- STATS_END -->

<!-- CALENDAR_START -->
<!-- CALENDAR_END -->

## ✨ Features

- 📅 **Daily Automatic Export** - Never miss a trade
- 📊 **Weekly Summaries** - Pattern analysis and performance metrics
- 📈 **Monthly Reports** - Deep analytics with recommendations
- 🔄 **Auto-Versioning** - Git history of all your trades
- 🔒 **Secure** - Uses token-based authentication (no passwords)
- 🛡️ **Privacy First** - Automatic account number obfuscation
- ⚡ **5-Minute Setup** - Start tracking immediately
- 🌍 **Multi-Currency Support** - Handles all IBKR currencies

## 🎯 Who is this for?

- Traders using Interactive Brokers
- Anyone wanting automated performance tracking
- Traders needing reliable trade data backup
- Quants requiring structured trade data for analysis

## 📚 Quick Start

### Prerequisites
- An Interactive Brokers account
- Access to IBKR Client Portal
- A GitHub account
- 5 minutes of your time

### Step 1: Configure IBKR Flex Web Service

#### 1.1 Enable Flex Web Service

1. Log in to [IBKR Client Portal](https://www.interactivebrokers.com/sso/Login)
2. Navigate to **Performance & Reports** → **Flex Queries**
3. Click on **Flex Web Service Configuration** (right side)
4. Check the box next to **Flex Web Service Status** to enable
5. Click **Save**
6. **IMPORTANT**: Copy and save your **Current Token** (you'll need this)

![Flex Web Service Configuration](./docs/images/flex-web-service-config.png)

#### 1.2 Configure Your Flex Query

⚠️ **IMPORTANT**: The default Flex Query may only include Account Information. You need to add more sections for complete data export.

##### Edit Your Flex Query:
1. In **Flex Queries**, find your query (or create a new one)
2. Click **Edit** (pencil icon)
3. Configure these settings:
   - **Query Name**: "GitHub Export" (or any name)
   - **Period**: Last 365 Days (or your preference)
   - **Format**: XML v3
   - **Sections to Include** (REQUIRED):
     - ✅ Account Information
     - ✅ Trades → **Executions** (not Orders)
     - ✅ Open Positions
     - ✅ Cash Report
     - ✅ Change in Position Value (optional)
     - ✅ Financial Instrument Information (optional)
4. Click **Save**
5. Click the **Info** icon (ℹ️) and copy the **Query ID**

##### Why These Sections?
- **Trades (Executions)**: Your actual filled trades with P&L
- **Open Positions**: Current holdings and unrealized P&L
- **Cash Report**: Account balances by currency
- **Account Information**: Basic account details

#### 1.3 Token Settings
- **Token Duration**: Can be set from 6 hours to 1 year
- **IP Restrictions**: Optional (leave blank for GitHub Actions)
- **Regenerating Token**: Invalidates the previous token

### Step 2: GitHub Setup

#### Option A: GitHub Actions (Recommended)

1. **Create a new private repository** on GitHub

2. **Add your credentials as secrets**:
   ```
   Settings → Secrets and variables → Actions → New repository secret
   ```
   - `IBKR_TOKEN`: Your Flex Web Service token
   - `IBKR_QUERY_ID`: Your Query ID

3. **Create `.github/workflows/export.yml`**:
   ```yaml
   name: Export IBKR Trading Data

   on:
     schedule:
       - cron: '0 3 * * *'  # Daily at 10 PM EST
     workflow_dispatch:       # Manual trigger

   jobs:
     export:
       runs-on: ubuntu-latest
       permissions:
         contents: write
       
       steps:
       - uses: actions/checkout@v3
       
       - uses: jefrnc/ibkr-auto-exporter@v1
         with:
           ibkr-token: ${{ secrets.IBKR_TOKEN }}
           ibkr-query-id: ${{ secrets.IBKR_QUERY_ID }}
   ```

That's it! 🎉 Your trades will be exported automatically every day.

#### Option B: Quick Setup Script

```bash
curl -sSL https://raw.githubusercontent.com/jefrnc/ibkr-auto-exporter/main/quick-setup.sh | bash
```

## 🗂️ Data Structure

```
exports/
├── daily/
│   ├── 2024-03-01.json     # Individual trades for each day
│   ├── 2024-03-02.json
│   └── ...
├── weekly/
│   ├── 2024-W09.json       # Weekly analytics
│   └── ...
└── monthly/
    ├── 2024-03.json        # Full monthly analysis
    └── 2024-03.txt         # Human-readable report
```

## ⚙️ Configuration

### Basic Configuration

```yaml
- uses: jefrnc/ibkr-auto-exporter@v1
  with:
    ibkr-token: ${{ secrets.IBKR_TOKEN }}
    ibkr-query-id: ${{ secrets.IBKR_QUERY_ID }}
```

### Advanced Configuration

```yaml
- uses: jefrnc/ibkr-auto-exporter@v1
  with:
    # Required
    ibkr-token: ${{ secrets.IBKR_TOKEN }}
    ibkr-query-id: ${{ secrets.IBKR_QUERY_ID }}
    
    # Optional
    export-path: 'trading-data'      # Custom export directory
    obfuscate-account: 'true'        # Privacy mode (default: true)
    generate-weekly: 'true'          # Force weekly summary
    generate-monthly: 'true'         # Force monthly summary
    commit-exports: 'true'           # Auto-commit (default: true)
    base-currency: 'USD'             # Base currency for P&L (default: USD)
    cost-basis-min: '0'              # Min cost basis filter (optional)
    cost-basis-max: '50'             # Max cost basis filter (optional)
```

### Input Parameters

| Parameter | Description | Required | Default |
|-----------|-------------|----------|---------|
| `ibkr-token` | Your Flex Web Service token | ✅ | - |
| `ibkr-query-id` | Your Flex Query ID | ✅ | - |
| `export-path` | Directory for exports | ❌ | `exports` |
| `obfuscate-account` | Hide account numbers | ❌ | `true` |
| `generate-weekly` | Generate weekly summary | ❌ | `auto` |
| `generate-monthly` | Generate monthly summary | ❌ | `auto` |
| `commit-exports` | Auto-commit changes | ❌ | `true` |
| `base-currency` | Base currency for calculations | ❌ | `USD` |

## 📊 Exported Data

### Daily Export Format
```json
{
  "exportDate": "2024-03-15 22:00:00",
  "account": "U*****23",
  "date": "2024-03-15",
  "trades": [
    {
      "date": "2024-03-15",
      "symbol": "AAPL",
      "description": "APPLE INC",
      "conid": "265598",
      "securityID": "US0378331005",
      "listingExchange": "NASDAQ",
      "multiplier": "1",
      "strike": "",
      "expiry": "",
      "putCall": "",
      "tradeID": "123456789",
      "reportDate": "2024-03-15",
      "tradeDate": "2024-03-15",
      "tradeTime": "093045",
      "settleDateTarget": "2024-03-17",
      "transactionType": "ExchTrade",
      "exchange": "ISLAND",
      "quantity": "100",
      "tradePrice": "150.25",
      "tradeMoney": "15025",
      "proceeds": "-15025",
      "taxes": "0",
      "ibCommission": "-1",
      "ibCommissionCurrency": "USD",
      "closePrice": "150.50",
      "openCloseIndicator": "O",
      "notes": "",
      "cost": "15026",
      "fifoPnlRealized": "0",
      "mtmPnl": "25",
      "origTradePrice": "150.25",
      "origTradeDate": "2024-03-15",
      "origTradeID": "123456789",
      "origOrderID": "987654321",
      "openDateTime": "2024-03-15;093045",
      "assetCategory": "STK",
      "subCategory": "COMMON",
      "pnl": 125.50,
      "commission": 1.00
    }
  ],
  "summary": {
    "totalTrades": 15,
    "totalPnL": 450.75,
    "winRate": 0.73,
    "symbols": ["AAPL", "MSFT", "GOOGL"]
  }
}
```

### Weekly Summary Includes
- Consolidated daily performance
- Trading patterns analysis
- Best/worst trading days
- Peak trading hours
- Symbol performance breakdown
- Asset category distribution

### Monthly Report Features
- Comprehensive P&L analysis
- Risk metrics (Sharpe ratio, max drawdown)
- Performance by symbol and asset class
- Trading consistency metrics
- Currency exposure analysis
- Automated recommendations

## 🔧 Local Usage

### Installation
```bash
git clone https://github.com/jefrnc/ibkr-auto-exporter.git
cd ibkr-auto-exporter
pip install -r requirements.txt
```

### Configuration
```bash
export IBKR_TOKEN="your-token-here"
export IBKR_QUERY_ID="your-query-id"
```

### Usage
```bash
# Daily export
python src/daily_exporter.py

# Export specific date range
python src/advanced_exporter.py range 2024-03-01 2024-03-15

# Generate weekly summary
python src/weekly_summary.py

# Generate monthly report
python src/monthly_summary.py
```

## 📖 Examples

### Multiple Accounts
```yaml
# Create separate workflows for each account
name: Export Account 1
# ... workflow configuration with ACCOUNT1 secrets

---
name: Export Account 2  
# ... workflow configuration with ACCOUNT2 secrets
```

### Custom Schedule
```yaml
on:
  schedule:
    # Every 4 hours during market days
    - cron: '0 */4 * * 1-5'
    # Once on weekends
    - cron: '0 22 * * 0,6'
```

## 🛡️ Security Best Practices

1. **Always use GitHub Secrets** - Never hardcode credentials
2. **Use private repositories** - Keep your trading data secure
3. **Rotate tokens periodically** - IBKR allows token regeneration
4. **Monitor access logs** - Check IBKR audit trail regularly
5. **Set token expiration** - Use shortest practical duration

## 🆚 Comparison with Manual Export

| Feature | Manual Export | IBKR Auto-Exporter |
|---------|---------------|-------------------|
| Daily exports | ❌ Must login daily | ✅ Fully automated |
| Historical data | ❌ One-time download | ✅ Git versioned history |
| Analytics | ❌ DIY in Excel | ✅ Automated reports |
| Multi-currency | ❌ Manual conversion | ✅ Automatic handling |
| Time investment | 📅 5-10 min/day | ⚡ 0 min/day |

## ❓ Troubleshooting

### Common Issues

1. **"Invalid token" error**
   - Token may have expired - regenerate in IBKR Client Portal
   - Ensure you copied the entire token

2. **"Query not found" error**
   - Verify Query ID is correct
   - Ensure Flex Query is active and not deleted

3. **No data returned**
   - Check if you have trades in the specified period
   - Verify Flex Query includes "Trades" section

4. **Authentication failed**
   - Token might be IP-restricted
   - Try regenerating token without IP restrictions

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md).

## 📝 License

Distributed under the MIT License. See [LICENSE](LICENSE) for more information.

## 🙏 Acknowledgments

- Interactive Brokers for their Flex Web Service API
- The `ibflex` library maintainers
- GitHub Actions for reliable automation

## 📞 Support

- 📧 [Open an Issue](https://github.com/jefrnc/ibkr-auto-exporter/issues)
- 📚 [Read the FAQ](./docs/FAQ.md)
- 💬 [Discussions](https://github.com/jefrnc/ibkr-auto-exporter/discussions)

---

⭐ If this project helps you, please star it!

Made with ❤️ by traders, for traders.