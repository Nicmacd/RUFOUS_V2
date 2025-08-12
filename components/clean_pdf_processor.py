"""
Clean PDF processor for BMO bank statements
Focused extraction using text parsing - no vision models needed
"""

import logging
import re
import pdfplumber
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from pathlib import Path

from .location_extractor import LocationExtractor

logger = logging.getLogger(__name__)


class CleanPDFProcessor:
    """Clean, focused PDF processor for BMO credit card statements"""
    
    def __init__(self):
        """Initialize processor"""
        self.location_extractor = LocationExtractor()
    
    def process_pdf_statement(self, pdf_path: Path, account_type: str = "credit") -> Dict[str, Any]:
        """Process BMO PDF statement and extract all transactions"""
        try:
            logger.info(f"Processing PDF statement: {pdf_path}")
            
            # Extract transactions using text parsing
            transactions = self._extract_bmo_transactions(pdf_path)
            
            # Add metadata
            for txn in transactions:
                txn['account_type'] = account_type
                txn['statement_file'] = pdf_path.name
                
                # Convert date objects to strings for JSON serialization
                if isinstance(txn['date'], date):
                    txn['date'] = txn['date'].isoformat()
                if isinstance(txn.get('posting_date'), date):
                    txn['posting_date'] = txn['posting_date'].isoformat()
            
            # Remove duplicates
            unique_transactions = self._deduplicate_transactions(transactions)
            
            logger.info(f"Successfully processed {pdf_path.name}: {len(unique_transactions)} transactions")
            
            return {
                'status': 'success',
                'statement_filename': pdf_path.name,
                'account_type': account_type,
                'transactions': unique_transactions,
                'extraction_method': 'text_parsing',
                'total_transactions': len(unique_transactions)
            }
            
        except Exception as e:
            logger.error(f"PDF processing failed: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'transactions': []
            }
    
    def _extract_bmo_transactions(self, pdf_path: Path) -> List[Dict[str, Any]]:
        """Extract transactions from BMO statement using text parsing"""
        
        transactions = []
        
        with pdfplumber.open(pdf_path) as pdf:
            full_text = ""
            for page in pdf.pages:
                full_text += page.extract_text() + "\n"
        
        # Find transaction section
        lines = full_text.split('\n')
        in_transactions = False
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Start processing when we hit transactions
            if "Transactions since your last statement" in line:
                in_transactions = True
                i += 1
                continue
            
            # Stop at subtotal
            if "Subtotal for" in line:
                break
            
            if in_transactions and line:
                # BMO format: "Oct. 12 Oct. 14 USD 20.68@1.412959381 29.22"
                # Followed by: "CITIBIK*SUBSCRIPTION SAN FRANCISCOCA"
                
                # Look for date pattern
                date_match = re.match(r'^([A-Za-z]{3}\.?\s+\d{1,2})\s+([A-Za-z]{3}\.?\s+\d{1,2})\s+(.+)', line)
                if date_match:
                    trans_date_str = date_match.group(1).replace('.', '').strip()
                    posting_date_str = date_match.group(2).replace('.', '').strip()
                    rest_of_line = date_match.group(3)
                    
                    # Parse dates
                    trans_date = self._parse_bmo_date(trans_date_str, 2024)
                    posting_date = self._parse_bmo_date(posting_date_str, 2024)
                    
                    if not trans_date or not posting_date:
                        i += 1
                        continue
                    
                    # Extract amount from end of line
                    amount_match = re.search(r'(\d+(?:,\d{3})*\.\d{2})(\s+CR)?$', rest_of_line)
                    if not amount_match:
                        i += 1
                        continue
                    
                    amount_str = amount_match.group(1).replace(',', '')
                    amount = float(amount_str)
                    is_credit = amount_match.group(2) is not None
                    
                    # For credit cards: purchases are negative, payments/credits are positive
                    if not is_credit:
                        amount = -amount  # Make purchases negative
                    
                    # Get description part (remove amount and currency conversion)
                    desc_part = rest_of_line[:amount_match.start()].strip()
                    
                    # Remove currency conversion pattern like "USD 20.68@1.412959381"
                    desc_part = re.sub(r'^[A-Z]{3}\s+[\d\.]+@[\d\.]+\s*', '', desc_part)
                    
                    # Check next line for description continuation
                    if i + 1 < len(lines) and lines[i + 1].strip():
                        next_line = lines[i + 1].strip()
                        # If next line doesn't start with a date, it's description continuation
                        if not re.match(r'^[A-Za-z]{3}\.?\s+\d{1,2}', next_line):
                            desc_part += ' ' + next_line
                            i += 1  # Skip next line
                    
                    # Clean up description
                    description = re.sub(r'\s+', ' ', desc_part).strip()
                    
                    # Remove continuation text
                    description = re.sub(r'\s*\(continued on next page\)', '', description, flags=re.IGNORECASE)
                    description = description.strip()
                    
                    # Skip payment transactions and summary lines
                    skip_words = [
                        'SUBTOTAL', 'TOTAL FOR CARD', 'AUTOMATIC PYMT', 'PAYMENT RECEIVED', 
                        'PYMT RECEIVED', 'AUTO PAYMENT', 'AUTOPAY'
                    ]
                    if any(skip_word in description.upper() for skip_word in skip_words):
                        i += 1
                        continue
                    
                    if description:  # Only add if we have a description
                        # Extract location from description
                        location, cleaned_description = self.location_extractor.extract_location(description)
                        
                        # Check if this is a transfer/payment
                        is_transfer = self._is_transfer(description)
                        
                        transactions.append({
                            'date': trans_date,
                            'description': cleaned_description,
                            'location': location,
                            'amount': amount,
                            'posting_date': posting_date,
                            'merchant': self._extract_merchant(cleaned_description),
                            'is_transfer': is_transfer
                        })
            
            i += 1
        
        return transactions
    
    def _parse_bmo_date(self, date_str: str, year: int) -> Optional[date]:
        """Parse BMO date format like 'Oct 12'"""
        try:
            full_date_str = f"{date_str} {year}"
            parsed = datetime.strptime(full_date_str, '%b %d %Y')
            return parsed.date()
        except:
            return None
    
    def _extract_merchant(self, description: str) -> Optional[str]:
        """Extract merchant name from description"""
        # Simple merchant extraction - take first part before location
        parts = description.split()
        if len(parts) > 0:
            # Remove common prefixes and take first meaningful part
            merchant = parts[0]
            if merchant in ['SQ', 'TST-']:  # Square, etc.
                merchant = ' '.join(parts[:2]) if len(parts) > 1 else merchant
            return merchant
        return None
    
    def _deduplicate_transactions(self, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate transactions based on date, description, and amount"""
        seen = set()
        unique_transactions = []
        
        for txn in transactions:
            # Create a key for deduplication
            key = (str(txn['date']), txn['description'], txn['amount'])
            if key not in seen:
                seen.add(key)
                unique_transactions.append(txn)
            else:
                logger.debug(f"Duplicate transaction removed: {txn['description']} on {txn['date']}")
        
        return unique_transactions
    
    def _is_transfer(self, description: str) -> bool:
        """Check if transaction is a transfer/payment"""
        transfer_keywords = [
            'PAYMENT', 'PYMT', 'AUTOPAY', 'AUTOMATIC PAYMENT',
            'TRANSFER', 'TRSF', 'DIRECT DEBIT', 'PREAUTH', 'PRE-AUTH',
            'CREDIT CARD PAYMENT', 'ONLINE PAYMENT', 'PAYPAL TRANSFER',
            'INTERAC TRANSFER', 'E-TRANSFER', 'PAYMENT RECEIVED',
            'AUTO PAYMENT', 'FROM/DE ACCT', 'TO/A ACCT'
        ]
        
        description_upper = description.upper()
        return any(keyword in description_upper for keyword in transfer_keywords)