"""
Manual transaction import from JSON (for when AI extraction fails)
"""

import json
import logging
from typing import List, Dict, Any
from datetime import datetime, date

logger = logging.getLogger(__name__)


class ManualTransactionImporter:
    """Import transactions from manually provided JSON"""
    
    def import_from_json(self, json_data: str, statement_filename: str, account_type: str = "credit") -> Dict[str, Any]:
        """Import transactions from JSON string"""
        try:
            # Parse JSON
            if isinstance(json_data, str):
                transactions = json.loads(json_data)
            else:
                transactions = json_data
            
            # Validate and clean transactions
            cleaned_transactions = []
            for txn in transactions:
                cleaned_txn = self._clean_transaction(txn, statement_filename, account_type)
                if cleaned_txn:
                    cleaned_transactions.append(cleaned_txn)
            
            return {
                'status': 'success',
                'statement_filename': statement_filename,
                'account_type': account_type,
                'transactions': cleaned_transactions,
                'extraction_method': 'manual',
                'total_transactions': len(cleaned_transactions)
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON: {e}")
            return {
                'status': 'error',
                'message': f'Invalid JSON: {e}',
                'transactions': []
            }
        except Exception as e:
            logger.error(f"Import failed: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'transactions': []
            }
    
    def _clean_transaction(self, txn: Dict[str, Any], statement_file: str, account_type: str) -> Dict[str, Any]:
        """Clean and validate a transaction"""
        try:
            # Required fields
            if 'date' not in txn or 'description' not in txn or 'amount' not in txn:
                return None
            
            # Parse date
            date_str = str(txn['date'])
            if len(date_str) == 10 and date_str.count('-') == 2:
                # Already in YYYY-MM-DD format
                parsed_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            else:
                # Try other formats
                for fmt in ['%m/%d/%Y', '%m/%d/%y', '%Y-%m-%d']:
                    try:
                        parsed_date = datetime.strptime(date_str, fmt).date()
                        break
                    except ValueError:
                        continue
                else:
                    logger.warning(f"Could not parse date: {date_str}")
                    return None
            
            # Clean amount
            amount = float(txn['amount'])
            
            # Build clean transaction
            clean_txn = {
                'date': parsed_date,
                'description': str(txn['description']).strip(),
                'amount': amount,
                'balance': txn.get('balance'),
                'merchant': txn.get('merchant', '').strip() or None,
                'account_type': account_type,
                'statement_file': statement_file,
                'is_transfer': 'transfer' in txn.get('description', '').lower(),
                'is_recurring': False  # Could be enhanced later
            }
            
            return clean_txn
            
        except Exception as e:
            logger.warning(f"Failed to clean transaction: {e} - {txn}")
            return None