#!/usr/bin/env python3
"""
Simplified IBKR Flex Web Service Client
Handles XML parsing directly without ibflex library issues
"""

import os
import sys
import json
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import requests


class SimpleIBKRExporter:
    """Simple Interactive Brokers Flex Web Service client"""
    
    def __init__(self, token: str, query_id: str):
        self.token = token
        self.query_id = query_id
        self.base_url = "https://ndcdyn.interactivebrokers.com/AccountManagement/FlexWebService"
        
    def download_flex_report(self) -> Optional[ET.Element]:
        """Download Flex report and return XML root"""
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
            print("📡 Requesting report from IBKR...")
            response = requests.get(send_url, params=params, headers=headers)
            response.raise_for_status()
            
            # Parse response
            root = ET.fromstring(response.text)
            
            if root.tag == "FlexStatementResponse":
                # Success - get reference code and URL
                reference_code = root.find("ReferenceCode").text
                base_url = root.find("Url").text
                
                print(f"✅ Got reference code: {reference_code}")
                
                # Step 2: Get statement
                statement_url = f"{base_url}?t={self.token}&q={reference_code}&v=3"
                
                # Wait a bit for report generation
                print("⏳ Waiting for report generation...")
                time.sleep(3)
                
                statement_response = requests.get(statement_url, headers=headers)
                statement_response.raise_for_status()
                
                # Parse and return XML
                return ET.fromstring(statement_response.text)
                
            else:
                # Error response
                error_code = root.find("ErrorCode")
                error_message = root.find("ErrorMessage")
                if error_code is not None and error_message is not None:
                    print(f"❌ Error from IBKR: {error_code.text} - {error_message.text}")
                else:
                    print(f"❌ Unknown error response: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error downloading report: {e}")
            return None
    
    def extract_account_info(self, root: ET.Element) -> Dict[str, Any]:
        """Extract account information from XML"""
        account_info = {}
        
        for statement in root.findall(".//FlexStatement"):
            account_id = statement.get("accountId")
            
            # Find AccountInformation element
            acc_info = statement.find("AccountInformation")
            if acc_info is not None:
                account_info[account_id] = {
                    'accountId': account_id,
                    'alias': acc_info.get('acctAlias', ''),
                    'currency': acc_info.get('currency', 'USD'),
                    'type': acc_info.get('accountType', ''),
                    'dateOpened': acc_info.get('dateOpened', ''),
                    'lastTradedDate': acc_info.get('lastTradedDate', ''),
                }
        
        return account_info
    
    def _safe_float(self, value: str, default: float = 0.0) -> float:
        """Safely convert string to float"""
        if not value or value == '':
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default
    
    def extract_trades(self, root: ET.Element) -> List[Dict[str, Any]]:
        """Extract trades from XML"""
        trades = []
        
        for statement in root.findall(".//FlexStatement"):
            account_id = statement.get("accountId")
            
            # Find all Trade elements
            for trade in statement.findall(".//Trade"):
                trade_dict = {
                    'accountId': account_id,
                    'tradeID': trade.get('tradeID', ''),
                    'reportDate': trade.get('reportDate', ''),
                    'tradeDate': trade.get('tradeDate', ''),
                    'tradeTime': trade.get('tradeTime', ''),
                    'settleDateTarget': trade.get('settleDateTarget', ''),
                    'transactionType': trade.get('transactionType', ''),
                    'exchange': trade.get('exchange', ''),
                    'quantity': self._safe_float(trade.get('quantity', '0')),
                    'tradePrice': self._safe_float(trade.get('tradePrice', '0')),
                    'tradeMoney': self._safe_float(trade.get('tradeMoney', '0')),
                    'proceeds': self._safe_float(trade.get('proceeds', '0')),
                    'taxes': self._safe_float(trade.get('taxes', '0')),
                    'ibCommission': self._safe_float(trade.get('ibCommission', '0')),
                    'ibCommissionCurrency': trade.get('ibCommissionCurrency', 'USD'),
                    'netCash': self._safe_float(trade.get('netCash', '0')),
                    'closePrice': self._safe_float(trade.get('closePrice', '0')),
                    'openCloseIndicator': trade.get('openCloseIndicator', ''),
                    'notes': trade.get('notes', ''),
                    'cost': self._safe_float(trade.get('cost', '0')),
                    'fifoPnlRealized': self._safe_float(trade.get('fifoPnlRealized', '0')),
                    'mtmPnl': self._safe_float(trade.get('mtmPnl', '0')),
                    'origTradePrice': self._safe_float(trade.get('origTradePrice', '0')),
                    'origTradeDate': trade.get('origTradeDate', ''),
                    'origTradeID': trade.get('origTradeID', ''),
                    'origOrderID': trade.get('origOrderID', ''),
                    'openDateTime': trade.get('openDateTime', ''),
                    'assetCategory': trade.get('assetCategory', ''),
                    'symbol': trade.get('symbol', ''),
                    'description': trade.get('description', ''),
                    'conid': trade.get('conid', ''),
                    'securityID': trade.get('securityID', ''),
                    'securityIDType': trade.get('securityIDType', ''),
                    'cusip': trade.get('cusip', ''),
                    'isin': trade.get('isin', ''),
                    'listingExchange': trade.get('listingExchange', ''),
                    'underlyingConid': trade.get('underlyingConid', ''),
                    'underlyingSymbol': trade.get('underlyingSymbol', ''),
                    'underlyingSecurityID': trade.get('underlyingSecurityID', ''),
                    'underlyingListingExchange': trade.get('underlyingListingExchange', ''),
                    'issuer': trade.get('issuer', ''),
                    'multiplier': self._safe_float(trade.get('multiplier', '1'), 1),
                    'strike': self._safe_float(trade.get('strike', '0')),
                    'expiry': trade.get('expiry', ''),
                    'putCall': trade.get('putCall', ''),
                    'principalAdjustFactor': self._safe_float(trade.get('principalAdjustFactor', '1'), 1),
                    # Additional calculated fields
                    'pnl': self._safe_float(trade.get('fifoPnlRealized', '0')),
                    'commission': abs(self._safe_float(trade.get('ibCommission', '0'))),
                    'currency': trade.get('currency', trade.get('ibCommissionCurrency', 'USD')),
                }
                trades.append(trade_dict)
        
        return trades
    
    def extract_positions(self, root: ET.Element) -> List[Dict[str, Any]]:
        """Extract open positions from XML"""
        positions = []
        
        for statement in root.findall(".//FlexStatement"):
            account_id = statement.get("accountId")
            
            # Find all OpenPosition elements
            for position in statement.findall(".//OpenPosition"):
                position_dict = {
                    'accountId': account_id,
                    'symbol': position.get('symbol', ''),
                    'description': position.get('description', ''),
                    'conid': position.get('conid', ''),
                    'reportDate': position.get('reportDate', ''),
                    'position': self._safe_float(position.get('position', '0')),
                    'markPrice': self._safe_float(position.get('markPrice', '0')),
                    'positionValue': self._safe_float(position.get('positionValue', '0')),
                    'openPrice': self._safe_float(position.get('openPrice', '0')),
                    'costBasisPrice': self._safe_float(position.get('costBasisPrice', '0')),
                    'costBasisMoney': self._safe_float(position.get('costBasisMoney', '0')),
                    'fifoPnlUnrealized': self._safe_float(position.get('fifoPnlUnrealized', '0')),
                    'assetCategory': position.get('assetCategory', ''),
                    'currency': position.get('currency', 'USD'),
                }
                positions.append(position_dict)
        
        return positions
    
    def extract_cash_report(self, root: ET.Element) -> Dict[str, Any]:
        """Extract cash report from XML"""
        cash_report = {}
        
        for statement in root.findall(".//FlexStatement"):
            account_id = statement.get("accountId")
            cash_report[account_id] = {}
            
            # Find all CashReport elements
            for cash_entry in statement.findall(".//CashReport"):
                currency = cash_entry.get('currency', 'USD')
                cash_report[account_id][currency] = {
                    'startingCash': self._safe_float(cash_entry.get('startingCash', '0')),
                    'endingCash': self._safe_float(cash_entry.get('endingCash', '0')),
                    'endingSettledCash': self._safe_float(cash_entry.get('endingSettledCash', '0')),
                }
        
        return cash_report


def main():
    """Main function for testing"""
    # Get credentials from environment
    token = os.getenv('IBKR_TOKEN')
    query_id = os.getenv('IBKR_QUERY_ID')
    
    if not token or not query_id:
        print("Error: IBKR_TOKEN and IBKR_QUERY_ID environment variables must be set")
        sys.exit(1)
    
    # Create exporter
    exporter = SimpleIBKRExporter(token, query_id)
    
    # Download report
    print("📊 Downloading IBKR Flex report...")
    xml_root = exporter.download_flex_report()
    
    if xml_root:
        # Extract data
        account_info = exporter.extract_account_info(xml_root)
        trades = exporter.extract_trades(xml_root)
        positions = exporter.extract_positions(xml_root)
        cash_report = exporter.extract_cash_report(xml_root)
        
        print(f"\n✅ Report downloaded successfully!")
        print(f"📋 Account info: {json.dumps(account_info, indent=2)}")
        print(f"📈 Found {len(trades)} trades")
        print(f"💼 Found {len(positions)} open positions")
        print(f"💰 Cash report: {json.dumps(cash_report, indent=2)}")
        
        # Save to file for debugging
        with open('debug_export.json', 'w') as f:
            json.dump({
                'account_info': account_info,
                'trades': trades,
                'positions': positions,
                'cash_report': cash_report,
                'export_date': datetime.now().isoformat()
            }, f, indent=2)
        
        print(f"\n💾 Export saved to debug_export.json")
        
        # Show sample trade if available
        if trades:
            print(f"\n📊 Sample trade:")
            print(json.dumps(trades[0], indent=2))
    else:
        print("❌ Failed to download report")
        sys.exit(1)


if __name__ == "__main__":
    main()