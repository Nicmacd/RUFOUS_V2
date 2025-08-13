"""
Natural Language Query Handler using Groq API
Converts user questions to database operations and provides insights
"""

import logging
import json
import re
import os
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, date, timedelta
import requests
import pandas as pd

from .database import RufousDatabase

logger = logging.getLogger(__name__)


class ChatHandler:
    """Handles natural language queries about financial data"""
    
    def __init__(self, database: RufousDatabase, model_name: str = "llama-3.3-70b-versatile"):
        """Initialize with database and Groq model"""
        self.db = database
        self.model_name = model_name
        self.groq_url = "https://api.groq.com/openai/v1/chat/completions"
        self.api_key = os.getenv('GROQ_API_KEY')
        self._check_groq_connection()
    
    def _check_groq_connection(self):
        """Verify Groq API key and connection"""
        if not self.api_key:
            raise ConnectionError("GROQ_API_KEY environment variable not set")
        
        try:
            # Test connection with a simple request
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            test_payload = {
                "model": self.model_name,
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 10,
                "temperature": 0.1
            }
            
            response = requests.post(self.groq_url, json=test_payload, headers=headers, timeout=10)
            response.raise_for_status()
            
            logger.info(f"Chat handler initialized with Groq {self.model_name}")
            
        except Exception as e:
            logger.error(f"Groq connection failed: {e}")
            raise ConnectionError(f"Please check your GROQ_API_KEY: {e}")
    
    def _call_groq_api(self, messages: List[Dict], max_tokens: int = 500, temperature: float = 0.1) -> str:
        """Make API call to Groq"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model_name,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": 0.9
        }
        
        try:
            response = requests.post(self.groq_url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            return result["choices"][0]["message"]["content"]
            
        except Exception as e:
            logger.error(f"Groq API call failed: {e}")
            raise
    
    def process_query(self, user_query: str) -> Dict[str, Any]:
        """Process natural language query and return results"""
        try:
            # Classify query type and extract parameters
            query_analysis = self._analyze_query(user_query)
            
            if query_analysis['type'] == 'error':
                return {
                    'status': 'error',
                    'message': query_analysis.get('message', 'Query analysis failed'),
                    'query': user_query
                }
            
            # Execute appropriate database operation
            data_result = self._execute_data_query(query_analysis)
            
            # Generate natural language response
            response = self._generate_response(user_query, query_analysis, data_result)
            
            # Save successful query to history
            self.db.save_query(
                query_text=user_query,
                query_type=query_analysis['type'],
                results_summary=response.get('summary', ''),
                favorited=False
            )
            
            return {
                'status': 'success',
                'query': user_query,
                'query_type': query_analysis['type'],
                'data': data_result,
                'response': response,
                'visualization_suggestion': query_analysis.get('visualization')
            }
            
        except Exception as e:
            logger.error(f"Query processing failed: {e}")
            return {
                'status': 'error',
                'message': f"I couldn't process that query: {str(e)}",
                'query': user_query
            }
    
    def _analyze_query(self, user_query: str) -> Dict[str, Any]:
        """Analyze user query to determine intent and parameters"""
        
        analysis_prompt = f"""
You are a financial data analyst. Analyze this user query about their personal finances and return a JSON response with the query intent and parameters.

User Query: "{user_query}"

Available query types:
1. "search" - Search for specific transactions
2. "spending_analysis" - Analyze spending patterns
3. "category_breakdown" - Group spending by categories  
4. "trends" - Time-based analysis (monthly, weekly trends)
5. "comparison" - Compare periods or categories
6. "summary" - Overall financial summary
7. "budget" - Budget-related analysis

For each query, extract:
- type: one of the above types
- parameters: relevant filters (dates, amounts, categories, search terms, location)
- time_period: if mentioned (last month, this year, etc.)
- visualization: suggested chart type (bar, line, pie, etc.)

Location examples: "Kingston", "Toronto", "CA", "Ontario", "New York"

Return ONLY valid JSON in this format:
{{
  "type": "spending_analysis",
  "parameters": {{
    "category": "food",
    "time_period": "last_30_days",
    "search_term": null,
    "location": null
  }},
  "time_range": {{
    "start_date": "2024-01-01",
    "end_date": "2024-01-31"
  }},
  "visualization": "bar_chart"
}}

Examples:
- "How much did I spend on food last month?" -> spending_analysis with category filter
- "Show me all transactions from Starbucks" -> search with merchant filter  
- "What are my monthly spending trends?" -> trends analysis
- "Compare my spending this month vs last month" -> comparison analysis
- "Show me all transactions in Kingston" -> search with location filter
- "How much did I spend in Toronto last month?" -> spending_analysis with location and time filters
"""
        
        try:
            messages = [
                {"role": "system", "content": "You are a financial data analyst. Analyze user queries and return structured JSON responses."},
                {"role": "user", "content": analysis_prompt}
            ]
            
            response_text = self._call_groq_api(messages, max_tokens=300, temperature=0.1)
            
            # Parse JSON response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON found in response")
            
            analysis = json.loads(json_match.group(0))
            
            # Add computed time ranges
            if 'time_range' not in analysis and 'parameters' in analysis:
                time_range = self._compute_time_range(analysis['parameters'].get('time_period'))
                if time_range:
                    analysis['time_range'] = time_range
            
            return analysis
            
        except Exception as e:
            logger.error(f"Query analysis failed: {e}")
            return {
                'type': 'error',
                'message': f"I couldn't understand that query. Please try rephrasing."
            }
    
    def _compute_time_range(self, time_period: str) -> Optional[Dict[str, str]]:
        """Convert natural language time period to date range"""
        if not time_period:
            return None
        
        today = date.today()
        
        time_mappings = {
            'last_30_days': (today - timedelta(days=30), today),
            'last_month': (today.replace(day=1) - timedelta(days=1), today.replace(day=1) - timedelta(days=1)),
            'this_month': (today.replace(day=1), today),
            'last_3_months': (today - timedelta(days=90), today),
            'this_year': (today.replace(month=1, day=1), today),
            'last_year': (
                today.replace(year=today.year-1, month=1, day=1),
                today.replace(year=today.year-1, month=12, day=31)
            )
        }
        
        if time_period.lower() in time_mappings:
            start_date, end_date = time_mappings[time_period.lower()]
            return {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            }
        
        return None
    
    def _execute_data_query(self, query_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Execute database query based on analysis"""
        query_type = query_analysis.get('type')
        parameters = query_analysis.get('parameters', {})
        time_range = query_analysis.get('time_range', {})
        
        start_date = None
        end_date = None
        if time_range:
            start_date = datetime.fromisoformat(time_range['start_date']).date() if time_range.get('start_date') else None
            end_date = datetime.fromisoformat(time_range['end_date']).date() if time_range.get('end_date') else None
        
        try:
            if query_type == 'search':
                search_term = parameters.get('search_term', '')
                location_filter = parameters.get('location')
                
                if location_filter:
                    # Search with location filter
                    df = self.db.search_transactions_with_location(search_term, location_filter)
                else:
                    df = self.db.search_transactions(search_term)
                    
                return {
                    'transactions': df.to_dict('records') if not df.empty else [],
                    'count': len(df),
                    'total_amount': df['amount'].sum() if not df.empty else 0
                }
            
            elif query_type == 'spending_analysis':
                category = parameters.get('category')
                df = self.db.get_transactions_df(start_date, end_date, category)
                
                if df.empty:
                    return {'data': [], 'summary': 'No transactions found for this period'}
                
                expenses = df[df['amount'] < 0]
                return {
                    'transactions': df.to_dict('records'),
                    'total_spent': abs(expenses['amount'].sum()),
                    'transaction_count': len(expenses),
                    'average_expense': abs(expenses['amount'].mean()) if not expenses.empty else 0,
                    'date_range': f"{start_date} to {end_date}" if start_date and end_date else "All time"
                }
            
            elif query_type == 'category_breakdown':
                df = self.db.get_spending_by_category(start_date, end_date)
                return {
                    'categories': df.to_dict('records') if not df.empty else [],
                    'total_categories': len(df),
                    'top_category': df.iloc[0]['category'] if not df.empty else None
                }
            
            elif query_type == 'trends':
                months = 12  # Default to 12 months
                if 'months' in parameters:
                    months = parameters['months']
                
                df = self.db.get_monthly_trends(months)
                return {
                    'monthly_data': df.to_dict('records') if not df.empty else [],
                    'trend_period': f"Last {months} months"
                }
            
            elif query_type == 'summary':
                stats = self.db.get_database_stats()
                recent_df = self.db.get_transactions_df(
                    start_date=date.today() - timedelta(days=30)
                )
                
                return {
                    'overall_stats': stats,
                    'recent_activity': {
                        'last_30_days_transactions': len(recent_df),
                        'last_30_days_spending': abs(recent_df[recent_df['amount'] < 0]['amount'].sum()) if not recent_df.empty else 0
                    }
                }
            
            else:
                # Default: return recent transactions
                df = self.db.get_transactions_df(limit=20)
                return {
                    'recent_transactions': df.to_dict('records') if not df.empty else [],
                    'message': 'Showing recent transactions'
                }
        
        except Exception as e:
            logger.error(f"Data query execution failed: {e}")
            return {
                'error': str(e),
                'data': []
            }
    
    def _generate_response(self, user_query: str, query_analysis: Dict[str, Any], 
                          data_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate natural language response from data results"""
        
        response_prompt = f"""
You are a helpful financial assistant. The user asked: "{user_query}"

Query Analysis: {json.dumps(query_analysis, indent=2)}

Data Results: {json.dumps(data_result, indent=2, default=str)}

Generate a helpful, conversational response that:
1. Directly answers the user's question
2. Highlights key insights from the data
3. Is concise but informative
4. Uses natural language (avoid technical jargon)

Return ONLY a JSON response with this format:
{{
  "summary": "Brief one-sentence summary",
  "detailed_response": "Full conversational response",
  "key_insights": ["insight 1", "insight 2", "insight 3"],
  "suggested_followup": "Optional follow-up question suggestion"
}}
"""
        
        try:
            messages = [
                {"role": "system", "content": "You are a helpful financial assistant. Generate conversational responses about financial data."},
                {"role": "user", "content": response_prompt}
            ]
            
            response_text = self._call_groq_api(messages, max_tokens=400, temperature=0.3)
            
            # Parse JSON response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            else:
                # Fallback to simple text response
                return {
                    'summary': 'Query completed',
                    'detailed_response': response_text,
                    'key_insights': [],
                    'suggested_followup': None
                }
        
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            # Fallback response
            return {
                'summary': 'Data retrieved successfully',
                'detailed_response': f"I found {len(data_result.get('data', []))} results for your query.",
                'key_insights': [],
                'suggested_followup': None
            }
    
    def get_query_suggestions(self) -> List[str]:
        """Get common query suggestions for users"""
        return [
            "How much did I spend last month?",
            "Show me all transactions over $100",
            "What are my top spending categories?",
            "Compare my spending this month vs last month",
            "Show me all transactions from Amazon",
            "What's my monthly spending trend?",
            "How much did I spend on food this year?",
            "Show me all transactions in Kingston",
            "What was my biggest expense last week?",
            "How much did I spend in Toronto last month?"
        ]