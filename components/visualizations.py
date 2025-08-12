"""
Visualization module using Plotly for interactive financial charts
Generates charts based on query results and data analysis
"""

import logging
from typing import Dict, Any, List, Optional
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, date

logger = logging.getLogger(__name__)


class FinancialVisualizer:
    """Creates interactive financial visualizations using Plotly"""
    
    def __init__(self):
        """Initialize visualizer with default styling"""
        self.color_palette = [
            '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
            '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
        ]
        
        self.layout_defaults = {
            'template': 'plotly_white',
            'font': {'size': 12},
            'margin': {'t': 40, 'l': 40, 'r': 40, 'b': 40}
        }
    
    def create_spending_by_category_chart(self, category_data: List[Dict[str, Any]], 
                                        chart_type: str = 'pie') -> go.Figure:
        """Create category breakdown visualization"""
        if not category_data:
            return self._create_empty_chart("No category data available")
        
        df = pd.DataFrame(category_data)
        
        if chart_type == 'pie':
            fig = px.pie(
                df, 
                values='total_spent', 
                names='category',
                title='Spending by Category',
                color_discrete_sequence=self.color_palette
            )
            fig.update_traces(
                textposition='inside',
                textinfo='percent+label',
                hovertemplate='<b>%{label}</b><br>Amount: $%{value:,.2f}<br>Percentage: %{percent}<extra></extra>'
            )
        
        elif chart_type == 'bar':
            fig = px.bar(
                df.sort_values('total_spent', ascending=True),
                x='total_spent',
                y='category',
                orientation='h',
                title='Spending by Category',
                labels={'total_spent': 'Amount Spent ($)', 'category': 'Category'},
                color='total_spent',
                color_continuous_scale='Reds'
            )
            fig.update_traces(
                hovertemplate='<b>%{y}</b><br>Amount: $%{x:,.2f}<extra></extra>'
            )
        
        else:  # treemap
            fig = px.treemap(
                df,
                values='total_spent',
                path=['category'],
                title='Spending by Category (Treemap)',
                color='total_spent',
                color_continuous_scale='Reds'
            )
        
        fig.update_layout(**self.layout_defaults)
        return fig
    
    def create_monthly_trends_chart(self, monthly_data: List[Dict[str, Any]]) -> go.Figure:
        """Create monthly spending trends chart"""
        if not monthly_data:
            return self._create_empty_chart("No monthly data available")
        
        df = pd.DataFrame(monthly_data)
        df['month'] = pd.to_datetime(df['month'])
        df = df.sort_values('month')
        
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Monthly Spending & Income', 'Net Cash Flow'),
            shared_xaxes=True,
            vertical_spacing=0.1
        )
        
        # Spending and Income
        fig.add_trace(
            go.Scatter(
                x=df['month'],
                y=df['total_spent'],
                mode='lines+markers',
                name='Spending',
                line=dict(color='red', width=2),
                marker=dict(size=6),
                hovertemplate='<b>%{fullData.name}</b><br>Date: %{x}<br>Amount: $%{y:,.2f}<extra></extra>'
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=df['month'],
                y=df['total_income'],
                mode='lines+markers',
                name='Income',
                line=dict(color='green', width=2),
                marker=dict(size=6),
                hovertemplate='<b>%{fullData.name}</b><br>Date: %{x}<br>Amount: $%{y:,.2f}<extra></extra>'
            ),
            row=1, col=1
        )
        
        # Net flow
        colors = ['green' if x >= 0 else 'red' for x in df['net_flow']]
        fig.add_trace(
            go.Bar(
                x=df['month'],
                y=df['net_flow'],
                name='Net Flow',
                marker_color=colors,
                hovertemplate='<b>Net Flow</b><br>Date: %{x}<br>Amount: $%{y:,.2f}<extra></extra>'
            ),
            row=2, col=1
        )
        
        fig.update_layout(
            title='Financial Trends Over Time',
            **self.layout_defaults
        )
        
        fig.update_xaxes(title_text="Month", row=2, col=1)
        fig.update_yaxes(title_text="Amount ($)", row=1, col=1)
        fig.update_yaxes(title_text="Net Flow ($)", row=2, col=1)
        
        return fig
    
    def create_transaction_timeline(self, transactions: List[Dict[str, Any]], 
                                  limit: int = 50) -> go.Figure:
        """Create transaction timeline chart"""
        if not transactions:
            return self._create_empty_chart("No transactions available")
        
        df = pd.DataFrame(transactions[:limit])  # Limit for performance
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        # Separate income and expenses
        expenses = df[df['amount'] < 0].copy()
        income = df[df['amount'] > 0].copy()
        
        fig = go.Figure()
        
        if not expenses.empty:
            fig.add_trace(
                go.Scatter(
                    x=expenses['date'],
                    y=expenses['amount'],
                    mode='markers',
                    name='Expenses',
                    marker=dict(
                        color='red',
                        size=8,
                        opacity=0.7
                    ),
                    text=expenses['description'],
                    hovertemplate='<b>%{text}</b><br>Date: %{x}<br>Amount: $%{y:,.2f}<extra></extra>'
                )
            )
        
        if not income.empty:
            fig.add_trace(
                go.Scatter(
                    x=income['date'],
                    y=income['amount'],
                    mode='markers',
                    name='Income',
                    marker=dict(
                        color='green',
                        size=8,
                        opacity=0.7
                    ),
                    text=income['description'],
                    hovertemplate='<b>%{text}</b><br>Date: %{x}<br>Amount: $%{y:,.2f}<extra></extra>'
                )
            )
        
        # Add zero line
        fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
        
        fig.update_layout(
            title=f'Transaction Timeline (Last {limit} transactions)',
            xaxis_title='Date',
            yaxis_title='Amount ($)',
            **self.layout_defaults
        )
        
        return fig
    
    def create_balance_over_time(self, transactions: List[Dict[str, Any]]) -> go.Figure:
        """Create account balance over time chart"""
        if not transactions:
            return self._create_empty_chart("No balance data available")
        
        # Filter transactions with balance data
        df = pd.DataFrame(transactions)
        df = df[df['balance'].notna()].copy()
        
        if df.empty:
            return self._create_empty_chart("No balance information in transactions")
        
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        fig = go.Figure()
        
        fig.add_trace(
            go.Scatter(
                x=df['date'],
                y=df['balance'],
                mode='lines+markers',
                name='Account Balance',
                line=dict(color='blue', width=2),
                marker=dict(size=4),
                fill='tonexty',
                fillcolor='rgba(0,123,255,0.1)',
                hovertemplate='<b>Balance</b><br>Date: %{x}<br>Balance: $%{y:,.2f}<extra></extra>'
            )
        )
        
        # Add trend line
        if len(df) > 1:
            z = np.polyfit(range(len(df)), df['balance'], 1)
            p = np.poly1d(z)
            trend_color = 'green' if z[0] >= 0 else 'red'
            
            fig.add_trace(
                go.Scatter(
                    x=df['date'],
                    y=p(range(len(df))),
                    mode='lines',
                    name='Trend',
                    line=dict(color=trend_color, width=1, dash='dash'),
                    hovertemplate='<b>Trend Line</b><extra></extra>'
                )
            )
        
        fig.update_layout(
            title='Account Balance Over Time',
            xaxis_title='Date',
            yaxis_title='Balance ($)',
            **self.layout_defaults
        )
        
        return fig
    
    def create_spending_comparison(self, comparison_data: Dict[str, Any]) -> go.Figure:
        """Create period comparison chart"""
        if not comparison_data:
            return self._create_empty_chart("No comparison data available")
        
        # Expected format: {'period1': {...}, 'period2': {...}}
        periods = list(comparison_data.keys())
        
        if len(periods) < 2:
            return self._create_empty_chart("Need at least 2 periods for comparison")
        
        categories = []
        period1_values = []
        period2_values = []
        
        # Extract category data from both periods
        for category_data in comparison_data[periods[0]].get('categories', []):
            category = category_data['category']
            categories.append(category)
            period1_values.append(category_data['total_spent'])
            
            # Find matching category in period 2
            period2_value = 0
            for cat2 in comparison_data[periods[1]].get('categories', []):
                if cat2['category'] == category:
                    period2_value = cat2['total_spent']
                    break
            period2_values.append(period2_value)
        
        fig = go.Figure()
        
        fig.add_trace(
            go.Bar(
                name=periods[0],
                x=categories,
                y=period1_values,
                marker_color='lightblue',
                hovertemplate='<b>%{fullData.name}</b><br>Category: %{x}<br>Amount: $%{y:,.2f}<extra></extra>'
            )
        )
        
        fig.add_trace(
            go.Bar(
                name=periods[1],
                x=categories,
                y=period2_values,
                marker_color='darkblue',
                hovertemplate='<b>%{fullData.name}</b><br>Category: %{x}<br>Amount: $%{y:,.2f}<extra></extra>'
            )
        )
        
        fig.update_layout(
            title=f'Spending Comparison: {periods[0]} vs {periods[1]}',
            xaxis_title='Category',
            yaxis_title='Amount Spent ($)',
            barmode='group',
            **self.layout_defaults
        )
        
        return fig
    
    def create_top_merchants_chart(self, transactions: List[Dict[str, Any]], 
                                 limit: int = 10) -> go.Figure:
        """Create top merchants spending chart"""
        if not transactions:
            return self._create_empty_chart("No transaction data available")
        
        df = pd.DataFrame(transactions)
        
        # Group by merchant and sum spending (negative amounts only)
        expenses = df[df['amount'] < 0].copy()
        if expenses.empty:
            return self._create_empty_chart("No expense transactions found")
        
        # Use merchant if available, otherwise use description
        expenses['merchant_name'] = expenses['merchant'].fillna(expenses['description'])
        
        merchant_spending = expenses.groupby('merchant_name')['amount'].agg(['sum', 'count']).reset_index()
        merchant_spending['total_spent'] = abs(merchant_spending['sum'])
        merchant_spending = merchant_spending.sort_values('total_spent', ascending=False).head(limit)
        
        fig = px.bar(
            merchant_spending,
            x='total_spent',
            y='merchant_name',
            orientation='h',
            title=f'Top {limit} Merchants by Spending',
            labels={'total_spent': 'Amount Spent ($)', 'merchant_name': 'Merchant'},
            color='total_spent',
            color_continuous_scale='Reds'
        )
        
        fig.update_traces(
            hovertemplate='<b>%{y}</b><br>Amount: $%{x:,.2f}<br>Transactions: %{customdata[0]}<extra></extra>',
            customdata=merchant_spending[['count']]
        )
        
        fig.update_layout(**self.layout_defaults)
        return fig
    
    def create_dashboard_summary(self, stats: Dict[str, Any]) -> go.Figure:
        """Create dashboard summary with key metrics"""
        if not stats:
            return self._create_empty_chart("No statistics available")
        
        # Create subplots for different metrics
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Account Overview', 'Transaction Volume', 'Income vs Expenses', 'Date Range'),
            specs=[[{"type": "indicator"}, {"type": "indicator"}],
                   [{"type": "bar"}, {"type": "table"}]]
        )
        
        # Account balance indicator
        net_change = stats.get('net_worth_change', 0)
        fig.add_trace(
            go.Indicator(
                mode="gauge+number+delta",
                value=net_change,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Net Worth Change ($)"},
                delta={'reference': 0},
                gauge={
                    'axis': {'range': [None, max(abs(net_change) * 2, 1000)]},
                    'bar': {'color': "green" if net_change >= 0 else "red"},
                    'steps': [{'range': [0, max(abs(net_change), 1000)], 'color': "lightgray"}],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 0
                    }
                }
            ),
            row=1, col=1
        )
        
        # Transaction count indicator
        fig.add_trace(
            go.Indicator(
                mode="number",
                value=stats.get('total_transactions', 0),
                title={'text': "Total Transactions"},
                number={'font': {'size': 40}}
            ),
            row=1, col=2
        )
        
        # Income vs Expenses bar
        income = stats.get('total_income', 0)
        expenses = stats.get('total_spent', 0)
        
        fig.add_trace(
            go.Bar(
                x=['Income', 'Expenses'],
                y=[income, expenses],
                marker_color=['green', 'red'],
                name="Financial Overview"
            ),
            row=2, col=1
        )
        
        # Summary table
        fig.add_trace(
            go.Table(
                header=dict(values=['Metric', 'Value']),
                cells=dict(values=[
                    ['Total Statements', 'Date Range', 'Avg Daily Spending'],
                    [
                        stats.get('total_statements', 0),
                        f"{stats.get('date_range', {}).get('earliest', 'N/A')} to {stats.get('date_range', {}).get('latest', 'N/A')}",
                        f"${expenses/365:.2f}" if expenses > 0 else "$0.00"
                    ]
                ])
            ),
            row=2, col=2
        )
        
        fig.update_layout(
            title='Financial Dashboard Summary',
            showlegend=False,
            **self.layout_defaults
        )
        
        return fig
    
    def _create_empty_chart(self, message: str) -> go.Figure:
        """Create empty chart with message"""
        fig = go.Figure()
        fig.add_annotation(
            text=message,
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16)
        )
        fig.update_layout(
            showlegend=False,
            **self.layout_defaults
        )
        return fig
    
    def suggest_visualization(self, query_type: str, data: Dict[str, Any]) -> str:
        """Suggest appropriate visualization based on query type and data"""
        suggestions = {
            'category_breakdown': 'pie',
            'trends': 'line',
            'comparison': 'bar_grouped',
            'spending_analysis': 'bar',
            'search': 'timeline',
            'summary': 'dashboard'
        }
        
        return suggestions.get(query_type, 'bar')