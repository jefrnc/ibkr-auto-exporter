#!/bin/bash
# Quick setup script for IBKR Auto-Exporter

set -e

echo "🚀 IBKR Auto-Exporter Quick Setup"
echo "================================="
echo ""

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) is not installed."
    echo "Please install it from: https://cli.github.com/"
    exit 1
fi

# Check if user is authenticated
if ! gh auth status &> /dev/null; then
    echo "❌ You're not authenticated with GitHub CLI."
    echo "Please run: gh auth login"
    exit 1
fi

# Get repository name
echo "📝 Enter a name for your repository (e.g., my-ibkr-exports):"
read -r REPO_NAME

if [ -z "$REPO_NAME" ]; then
    REPO_NAME="ibkr-trading-exports"
fi

# Get IBKR credentials
echo ""
echo "🔑 Enter your IBKR Flex Web Service Token:"
read -r IBKR_TOKEN

if [ -z "$IBKR_TOKEN" ]; then
    echo "❌ Token is required!"
    exit 1
fi

echo ""
echo "🆔 Enter your IBKR Flex Query ID:"
read -r IBKR_QUERY_ID

if [ -z "$IBKR_QUERY_ID" ]; then
    echo "❌ Query ID is required!"
    exit 1
fi

# Create repository
echo ""
echo "📂 Creating private repository: $REPO_NAME"
gh repo create "$REPO_NAME" --private --clone

cd "$REPO_NAME"

# Create workflow directory
mkdir -p .github/workflows

# Create workflow file
cat > .github/workflows/export.yml << 'EOF'
name: Export IBKR Trading Data

on:
  schedule:
    # Run daily at 10 PM EST (3 AM UTC)
    - cron: '0 3 * * *'
  workflow_dispatch:  # Allow manual trigger

jobs:
  export:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    
    steps:
    - name: Checkout repository
      uses: actions/checkout@v3
    
    - name: Export IBKR data
      uses: jefrnc/ibkr-auto-exporter@v1
      with:
        ibkr-token: ${{ secrets.IBKR_TOKEN }}
        ibkr-query-id: ${{ secrets.IBKR_QUERY_ID }}
EOF

# Create README
cat > README.md << EOF
# 📊 My IBKR Trading Exports

This repository automatically exports trading data from Interactive Brokers using [IBKR Auto-Exporter](https://github.com/jefrnc/ibkr-auto-exporter).

<!-- STATS_START -->
### 📊 Live Trading Statistics

*Statistics will appear here after first export*
<!-- STATS_END -->

<!-- CALENDAR_START -->
<!-- CALENDAR_END -->

## 🔧 Configuration

- **Export Schedule**: Daily at 10 PM EST
- **Data Location**: \`exports/\` directory
- **Account**: Obfuscated for privacy

## 📈 Features

- ✅ Automated daily exports
- ✅ Weekly performance summaries
- ✅ Monthly analytics reports
- ✅ Trading calendar visualization
- ✅ Live statistics in README

## 🛡️ Security

- Token-based authentication (no passwords)
- Account numbers automatically obfuscated
- Private repository

---

Powered by [IBKR Auto-Exporter](https://github.com/jefrnc/ibkr-auto-exporter)
EOF

# Create .gitignore
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Debug files
debug_export.json
EOF

# Commit initial files
git add .
git commit -m "🚀 Initial setup with IBKR Auto-Exporter"

# Set secrets
echo ""
echo "🔐 Setting up GitHub secrets..."
gh secret set IBKR_TOKEN -b "$IBKR_TOKEN"
gh secret set IBKR_QUERY_ID -b "$IBKR_QUERY_ID"

# Push to GitHub
git push origin main

echo ""
echo "✅ Setup complete!"
echo ""
echo "📊 Your repository is ready at: https://github.com/$(gh api user -q .login)/$REPO_NAME"
echo ""
echo "🎯 Next steps:"
echo "1. The workflow will run automatically at 10 PM EST daily"
echo "2. You can also trigger it manually from Actions tab"
echo "3. Check the exports/ directory for your data"
echo ""
echo "⚠️  IMPORTANT: Make sure your Flex Query includes:"
echo "   - Trades (Executions)"
echo "   - Open Positions"
echo "   - Cash Report"
echo ""
echo "Happy trading! 📈"