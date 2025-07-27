# Frequently Asked Questions

## General Questions

### What is IBKR Auto-Exporter?
IBKR Auto-Exporter is a GitHub Action that automatically downloads your trading data from Interactive Brokers using their Flex Web Service API. It processes the data and generates daily exports, weekly summaries, and monthly reports.

### Is it safe to use?
Yes! The tool uses IBKR's official Flex Web Service API with token-based authentication. Your login credentials are never used or stored. The token can be configured with:
- Limited validity period (6 hours to 1 year)
- IP restrictions
- Read-only access to your data

### What data does it export?
- Daily trades with P&L
- Open positions
- Cash balances
- Account information
- Performance analytics

## Setup Questions

### How do I get my IBKR Token and Query ID?

1. **Log in to IBKR Client Portal**
2. **Navigate to Performance & Reports → Flex Queries**
3. **Enable Flex Web Service** (right panel)
4. **Copy your token** (appears after enabling)
5. **Find your Query ID** by clicking the info icon next to any query

### Can I use an existing Flex Query?
Yes! IBKR provides a default "Activity" query that works perfectly. Just click the info icon to get its Query ID.

### What if my token expires?
Simply generate a new token in the IBKR Client Portal and update your GitHub secret. The old exports will remain intact.

### Can I restrict which IPs can use my token?
Yes, but for GitHub Actions, leave IP restrictions empty since GitHub uses dynamic IPs.

## Technical Questions

### What format is the data exported in?
All data is exported in JSON format with a clear structure. Human-readable text reports are also generated for monthly summaries.

### How often should I run the export?
We recommend daily exports after market close. The default schedule runs at 10 PM EST.

### Can I export historical data?
Yes, but it depends on your Flex Query configuration. By default, queries can access up to 365 days of data.

### What happens if IBKR is down?
The action will fail gracefully and retry on the next scheduled run. No data is lost.

### Can I use multiple accounts?
Yes! Create separate workflows for each account with different tokens/query IDs.

## Data Questions

### How is P&L calculated?
We use IBKR's FIFO realized P&L for closed positions and MTM P&L for open positions.

### Are commissions included?
Yes, commissions are tracked separately and included in net P&L calculations.

### How are different currencies handled?
All positions and trades maintain their original currency. Summary statistics can be converted to a base currency (default: USD).

### What about options and futures?
Fully supported! The exporter handles all asset categories that IBKR supports:
- Stocks (STK)
- Options (OPT)
- Futures (FUT)
- Forex (CASH)
- Bonds (BOND)
- Funds (FUND)
- Warrants (WAR)
- Structured Products (IOPT)

## Privacy Questions

### Is my account number visible?
By default, account numbers are obfuscated (e.g., U*****23). You can disable this with `obfuscate-account: false`.

### Where is my data stored?
Only in your GitHub repository. We don't store or transmit your data anywhere else.

### Can others see my trading data?
Only if you make your repository public. We strongly recommend using a private repository.

## Troubleshooting

### "Invalid token" error
- Token may have expired - regenerate in IBKR
- Ensure you copied the entire token
- Check for extra spaces or line breaks

### "Query not found" error
- Verify the Query ID is correct
- Ensure the Flex Query hasn't been deleted
- Try using the default "Activity" query

### No data in exports
- Check if you have trades in the period
- Verify your Flex Query includes the "Trades" section
- Ensure your account has activity

### GitHub Action fails
- Check the workflow logs for specific errors
- Verify all secrets are set correctly
- Ensure you have write permissions enabled

## Advanced Usage

### Can I customize the export format?
Yes, by forking the repository and modifying the Python scripts.

### Can I add custom analytics?
Absolutely! The modular design makes it easy to add new analysis scripts.

### Can I export to other services?
Yes, you can add steps to your workflow to upload to S3, Google Drive, etc.

### How do I contribute?
We welcome contributions! Please see our [Contributing Guidelines](../CONTRIBUTING.md).

## Contact

Still have questions? 
- 📧 [Open an Issue](https://github.com/jefrnc/ibkr-auto-exporter/issues)
- 💬 [Start a Discussion](https://github.com/jefrnc/ibkr-auto-exporter/discussions)