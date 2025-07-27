#!/usr/bin/env python3
"""
IBKR Flex Web Service Client
Handles authentication and data retrieval from Interactive Brokers
"""

import os
import sys
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import xml.etree.ElementTree as ET

try:
    from ibflex import client, parser
    from ibflex.Types import FlexQueryResponse, FlexStatement
except ImportError:
    print("Error: ibflex library not found. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "ibflex"])
    from ibflex import client, parser
    from ibflex.Types import FlexQueryResponse, FlexStatement

import requests


class IBKRExporter:
    """Interactive Brokers Flex Web Service client"""
    
    def __init__(self, token: str, query_id: str):
        self.token = token
        self.query_id = query_id
        self.base_url = "https://ndcdyn.interactivebrokers.com/AccountManagement/FlexWebService"
        
    def download_flex_report(self) -> FlexStatement:
        """Download Flex report using ibflex client"""
        try:
            # Use ibflex client for downloading
            response = client.download(token=self.token, query_id=self.query_id)
            
            # Check if response is bytes (XML string)
            if isinstance(response, bytes):
                # Parse the XML response
                response = parser.parse(response)
            elif isinstance(response, str):
                # Parse the XML response
                response = parser.parse(response)
            
            return response
        except Exception as e:
            print(f"Error downloading Flex report: {e}")
            print(f"Error type: {type(e)}")
            import traceback
            traceback.print_exc()
            # Fallback to manual implementation
            return self._manual_download()
    
    def _manual_download(self) -> Optional[str]:
        """Manual implementation of Flex Web Service download"""
        # Step 1: Send request
        send_url = f"{self.base_url}/SendRequest"
        params = {
            "t": self.token,
            "q": self.query_id,
            "v": "3"
        }
        
        headers = {
            "User-Agent": "Python/3.9"
        }
        
        try:
            response = requests.get(send_url, params=params, headers=headers)
            response.raise_for_status()
            
            # Parse response
            root = ET.fromstring(response.text)
            
            if root.tag == "FlexStatementResponse":
                # Success - get reference code and URL
                reference_code = root.find("ReferenceCode").text
                base_url = root.find("Url").text
                
                # Step 2: Get statement
                statement_url = f"{base_url}?t={self.token}&q={reference_code}&v=3"
                
                # Wait a bit for report generation
                time.sleep(2)
                
                statement_response = requests.get(statement_url, headers=headers)
                statement_response.raise_for_status()
                
                # Parse with ibflex parser
                return parser.parse(statement_response.text)
                
            else:
                # Error response
                error_code = root.find("ErrorCode").text
                error_message = root.find("ErrorMessage").text
                print(f"Error from IBKR: {error_code} - {error_message}")
                return None
                
        except Exception as e:
            print(f"Error in manual download: {e}")
            return None
    
    def extract_trades(self, statement: FlexStatement) -> List[Dict[str, Any]]:
        """Extract trades from Flex statement"""
        trades = []
        
        # Get all accounts in the statement
        for account_id, account in statement.accounts.items():
            # Process trades
            if hasattr(account, 'Trades') and account.Trades:
                for trade in account.Trades:
                    trade_dict = {
                        'accountId': account_id,
                        'tradeID': trade.tradeID,
                        'reportDate': str(trade.reportDate),
                        'tradeDate': str(trade.tradeDate),
                        'tradeTime': str(trade.tradeTime) if hasattr(trade, 'tradeTime') else '',
                        'settleDateTarget': str(trade.settleDateTarget) if hasattr(trade, 'settleDateTarget') else '',
                        'transactionType': trade.transactionType,
                        'exchange': trade.exchange if hasattr(trade, 'exchange') else '',
                        'quantity': float(trade.quantity),
                        'tradePrice': float(trade.tradePrice),
                        'tradeMoney': float(trade.tradeMoney) if hasattr(trade, 'tradeMoney') else 0,
                        'proceeds': float(trade.proceeds) if hasattr(trade, 'proceeds') else 0,
                        'taxes': float(trade.taxes) if hasattr(trade, 'taxes') else 0,
                        'ibCommission': float(trade.ibCommission),
                        'ibCommissionCurrency': trade.ibCommissionCurrency,
                        'netCash': float(trade.netCash) if hasattr(trade, 'netCash') else 0,
                        'closePrice': float(trade.closePrice) if hasattr(trade, 'closePrice') else 0,
                        'openCloseIndicator': trade.openCloseIndicator.value if hasattr(trade, 'openCloseIndicator') else '',
                        'notes': str(trade.notes) if hasattr(trade, 'notes') else '',
                        'cost': float(trade.cost) if hasattr(trade, 'cost') else 0,
                        'fifoPnlRealized': float(trade.fifoPnlRealized) if hasattr(trade, 'fifoPnlRealized') else 0,
                        'mtmPnl': float(trade.mtmPnl) if hasattr(trade, 'mtmPnl') else 0,
                        'origTradePrice': float(trade.origTradePrice) if hasattr(trade, 'origTradePrice') else 0,
                        'origTradeDate': str(trade.origTradeDate) if hasattr(trade, 'origTradeDate') else '',
                        'origTradeID': str(trade.origTradeID) if hasattr(trade, 'origTradeID') else '',
                        'origOrderID': str(trade.origOrderID) if hasattr(trade, 'origOrderID') else '',
                        'openDateTime': str(trade.openDateTime) if hasattr(trade, 'openDateTime') else '',
                        'assetCategory': trade.assetCategory.value if hasattr(trade, 'assetCategory') else '',
                        'symbol': trade.symbol,
                        'description': trade.description if hasattr(trade, 'description') else '',
                        'conid': str(trade.conid),
                        'securityID': trade.securityID if hasattr(trade, 'securityID') else '',
                        'securityIDType': trade.securityIDType if hasattr(trade, 'securityIDType') else '',
                        'cusip': trade.cusip if hasattr(trade, 'cusip') else '',
                        'isin': trade.isin if hasattr(trade, 'isin') else '',
                        'listingExchange': trade.listingExchange if hasattr(trade, 'listingExchange') else '',
                        'underlyingConid': str(trade.underlyingConid) if hasattr(trade, 'underlyingConid') else '',
                        'underlyingSymbol': trade.underlyingSymbol if hasattr(trade, 'underlyingSymbol') else '',
                        'underlyingSecurityID': trade.underlyingSecurityID if hasattr(trade, 'underlyingSecurityID') else '',
                        'underlyingListingExchange': trade.underlyingListingExchange if hasattr(trade, 'underlyingListingExchange') else '',
                        'issuer': trade.issuer if hasattr(trade, 'issuer') else '',
                        'multiplier': float(trade.multiplier) if hasattr(trade, 'multiplier') else 1,
                        'strike': float(trade.strike) if hasattr(trade, 'strike') and trade.strike else 0,
                        'expiry': str(trade.expiry) if hasattr(trade, 'expiry') else '',
                        'putCall': trade.putCall if hasattr(trade, 'putCall') else '',
                        'principalAdjustFactor': float(trade.principalAdjustFactor) if hasattr(trade, 'principalAdjustFactor') else 1,
                        # Additional calculated fields
                        'pnl': float(trade.fifoPnlRealized) if hasattr(trade, 'fifoPnlRealized') else 0,
                        'commission': abs(float(trade.ibCommission)) if hasattr(trade, 'ibCommission') else 0,
                        'currency': trade.currency if hasattr(trade, 'currency') else trade.ibCommissionCurrency,
                    }
                    trades.append(trade_dict)
        
        return trades
    
    def extract_positions(self, statement: FlexStatement) -> List[Dict[str, Any]]:
        """Extract open positions from Flex statement"""
        positions = []
        
        for account_id, account in statement.accounts.items():
            # Process open positions
            if hasattr(account, 'OpenPositions') and account.OpenPositions:
                for position in account.OpenPositions:
                    position_dict = {
                        'accountId': account_id,
                        'symbol': position.symbol,
                        'description': position.description if hasattr(position, 'description') else '',
                        'conid': str(position.conid),
                        'reportDate': str(position.reportDate),
                        'position': float(position.position),
                        'markPrice': float(position.markPrice) if hasattr(position, 'markPrice') else 0,
                        'positionValue': float(position.positionValue) if hasattr(position, 'positionValue') else 0,
                        'openPrice': float(position.openPrice) if hasattr(position, 'openPrice') else 0,
                        'costBasisPrice': float(position.costBasisPrice) if hasattr(position, 'costBasisPrice') else 0,
                        'costBasisMoney': float(position.costBasisMoney) if hasattr(position, 'costBasisMoney') else 0,
                        'fifoPnlUnrealized': float(position.fifoPnlUnrealized) if hasattr(position, 'fifoPnlUnrealized') else 0,
                        'assetCategory': position.assetCategory.value if hasattr(position, 'assetCategory') else '',
                        'currency': position.currency if hasattr(position, 'currency') else '',
                    }
                    positions.append(position_dict)
        
        return positions
    
    def extract_cash_report(self, statement: FlexStatement) -> Dict[str, Any]:
        """Extract cash report from Flex statement"""
        cash_report = {}
        
        for account_id, account in statement.accounts.items():
            cash_report[account_id] = {}
            
            # Process cash report
            if hasattr(account, 'CashReport') and account.CashReport:
                for cash_entry in account.CashReport:
                    currency = cash_entry.currency
                    cash_report[account_id][currency] = {
                        'startingCash': float(cash_entry.startingCash) if hasattr(cash_entry, 'startingCash') else 0,
                        'endingCash': float(cash_entry.endingCash) if hasattr(cash_entry, 'endingCash') else 0,
                        'endingSettledCash': float(cash_entry.endingSettledCash) if hasattr(cash_entry, 'endingSettledCash') else 0,
                    }
        
        return cash_report
    
    def get_account_information(self, statement: FlexStatement) -> Dict[str, Any]:
        """Extract account information"""
        account_info = {}
        
        for account_id, account in statement.accounts.items():
            account_info[account_id] = {
                'accountId': account_id,
                'currency': account.currency if hasattr(account, 'currency') else 'USD',
                # Add more fields as needed
            }
        
        return account_info


def main():
    """Main function for testing"""
    # Get credentials from environment
    token = os.getenv('IBKR_TOKEN')
    query_id = os.getenv('IBKR_QUERY_ID')
    
    if not token or not query_id:
        print("Error: IBKR_TOKEN and IBKR_QUERY_ID environment variables must be set")
        sys.exit(1)
    
    # Create exporter
    exporter = IBKRExporter(token, query_id)
    
    # Download report
    print("Downloading Flex report...")
    statement = exporter.download_flex_report()
    
    if statement:
        # Extract data
        trades = exporter.extract_trades(statement)
        positions = exporter.extract_positions(statement)
        cash_report = exporter.extract_cash_report(statement)
        account_info = exporter.get_account_information(statement)
        
        print(f"Found {len(trades)} trades")
        print(f"Found {len(positions)} open positions")
        print(f"Cash report: {json.dumps(cash_report, indent=2)}")
        
        # Save to file for debugging
        with open('debug_export.json', 'w') as f:
            json.dump({
                'trades': trades,
                'positions': positions,
                'cash_report': cash_report,
                'account_info': account_info
            }, f, indent=2)
        
        print("Export saved to debug_export.json")
    else:
        print("Failed to download report")
        sys.exit(1)


if __name__ == "__main__":
    main()