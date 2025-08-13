"""
Rufous v2 - Personal Financial Analysis Tool
Streamlit app with local PDF processing and natural language queries
"""

import streamlit as st
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import our components
from components.database import RufousDatabase
from components.clean_pdf_processor import CleanPDFProcessor  
from components.chat_handler import ChatHandler
from components.visualizations import FinancialVisualizer

# Page config
st.set_page_config(
    page_title="Rufous v2 - Financial Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #2E86C1;
        text-align: center;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #dee2e6;
    }
    .chat-message {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0.5rem;
        border-left: 4px solid #2E86C1;
        background-color: #f8f9fa;
    }
    .upload-section {
        background-color: #e8f4f8;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    if 'database' not in st.session_state:
        st.session_state.database = RufousDatabase()
    
    if 'pdf_processor' not in st.session_state:
        try:
            st.session_state.pdf_processor = CleanPDFProcessor()
        except Exception as e:
            st.error(f"Failed to initialize PDF processor: {e}")
            st.session_state.pdf_processor = None
    
    if 'chat_handler' not in st.session_state:
        try:
            st.session_state.chat_handler = ChatHandler(st.session_state.database)
        except ConnectionError as e:
            st.error(f"Failed to initialize chat handler: {e}")
            st.info("💡 **Setup Instructions:** Set your GROQ_API_KEY environment variable to enable chat features.")
            st.session_state.chat_handler = None
    
    if 'visualizer' not in st.session_state:
        st.session_state.visualizer = FinancialVisualizer()
    
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    if 'processed_files' not in st.session_state:
        st.session_state.processed_files = []

def render_sidebar():
    """Render sidebar with controls and stats"""
    with st.sidebar:
        st.markdown("### 🏦 Rufous v2")
        st.markdown("Personal Financial Analysis")
        
        # Database stats
        try:
            stats = st.session_state.database.get_database_stats()
            
            st.markdown("### 📊 Quick Stats")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Transactions", stats['total_transactions'])
                st.metric("Statements", stats['total_statements'])
            with col2:
                st.metric("Total Spent", f"${stats['total_spent']:,.2f}")
                st.metric("Net Change", f"${stats['net_worth_change']:,.2f}")
        
        except Exception as e:
            st.warning("Could not load database stats")
            logger.error(f"Stats loading error: {e}")
        
        st.markdown("---")
        
        # Quick actions
        st.markdown("### ⚡ Quick Actions")
        if st.button("📈 Dashboard View", use_container_width=True):
            st.session_state.current_view = 'dashboard'
        
        if st.button("💬 Chat Analysis", use_container_width=True):
            st.session_state.current_view = 'chat'
        
        if st.button("📄 Process PDFs", use_container_width=True):
            st.session_state.current_view = 'upload'
        
        # Favorite queries
        try:
            favorites = st.session_state.database.get_favorite_queries(limit=5)
            if favorites:
                st.markdown("### ⭐ Favorite Queries")
                for fav in favorites:
                    if st.button(f"🔍 {fav['query_text'][:30]}...", key=f"fav_{fav['id']}"):
                        st.session_state.quick_query = fav['query_text']
                        st.session_state.current_view = 'chat'
        except:
            pass

def render_pdf_upload():
    """Render PDF upload and processing section"""
    st.markdown('<div class="upload-section">', unsafe_allow_html=True)
    st.markdown("### 📄 Upload Bank Statements")
    
    if st.session_state.pdf_processor is None:
        st.error("PDF processor not available. Please check that pdfplumber is installed.")
        st.markdown("""
        **Setup Instructions:**
        1. Install dependencies: `pip install pdfplumber`
        2. For OCR fallback: `brew install poppler` (macOS) or `sudo apt-get install poppler-utils` (Linux)
        """)
        st.markdown('</div>', unsafe_allow_html=True)
        return
    
    # File uploader
    uploaded_files = st.file_uploader(
        "Choose PDF statements",
        type=['pdf'],
        accept_multiple_files=True,
        help="Upload one or more bank statement PDFs"
    )
    
    if uploaded_files:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Account type selection
            default_account_type = st.selectbox(
                "Default account type",
                ["debit", "credit"],
                help="Select the default account type for uploaded statements"
            )
        
        with col2:
            process_button = st.button(
                "🚀 Process Statements",
                type="primary",
                disabled=len(uploaded_files) == 0
            )
        
        if process_button and uploaded_files:
            process_uploaded_files(uploaded_files, default_account_type)
    
    # Show processing history
    if st.session_state.processed_files:
        st.markdown("### 📋 Processing History")
        for result in st.session_state.processed_files[-5:]:  # Show last 5
            status_icon = "✅" if result['status'] == 'success' else "❌"
            st.markdown(f"{status_icon} **{result['filename']}** - {result.get('total_transactions', 0)} transactions")
    
    # Manual import section for when AI fails
    with st.expander("💻 Manual Import (if AI extraction fails)", expanded=False):
        st.markdown("""
        **If PDF extraction fails, you can:**
        1. Upload your PDF to ChatGPT or Claude
        2. Ask it to extract transactions as JSON
        3. Paste the JSON below
        """)
        
        col1, col2 = st.columns([3, 1])
        with col1:
            json_input = st.text_area(
                "Paste transaction JSON here:",
                height=150,
                placeholder='[{"date": "2024-11-13", "description": "MERCHANT NAME", "amount": -11.43}, ...]'
            )
            statement_name = st.text_input("Statement filename:", value="manual_import.json")
        
        with col2:
            account_type_manual = st.selectbox("Account type:", ["credit", "debit"], key="manual_account")
            
        if st.button("📥 Import JSON Transactions") and json_input.strip():
            try:
                from components.manual_import import ManualTransactionImporter
                importer = ManualTransactionImporter()
                result = importer.import_from_json(json_input, statement_name, account_type_manual)
                
                if result['status'] == 'success':
                    transactions = result['transactions']
                    
                    # Add to database
                    statement_id = st.session_state.database.add_statement(
                        filename=statement_name,
                        statement_date=transactions[0]['date'] if transactions else None,
                        account_type=account_type_manual,
                        transaction_count=len(transactions),
                        total_amount=sum(t['amount'] for t in transactions)
                    )
                    
                    added_count = st.session_state.database.add_transactions(transactions)
                    st.success(f"✅ Successfully imported {added_count} transactions!")
                else:
                    st.error(f"❌ Import failed: {result['message']}")
                    
            except Exception as e:
                st.error(f"❌ Import error: {str(e)}")
    
    st.markdown('</div>', unsafe_allow_html=True)

def process_uploaded_files(uploaded_files: List, default_account_type: str):
    """Process uploaded PDF files"""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    results = []
    
    for i, uploaded_file in enumerate(uploaded_files):
        status_text.text(f"Processing {uploaded_file.name}...")
        progress_bar.progress((i + 1) / len(uploaded_files))
        
        try:
            # Save uploaded file temporarily
            temp_path = Path(f"/tmp/{uploaded_file.name}")
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Check if already processed
            if st.session_state.database.is_statement_processed(uploaded_file.name):
                st.warning(f"Statement {uploaded_file.name} already processed. Skipping.")
                continue
            
            # Process PDF
            result = st.session_state.pdf_processor.process_pdf_statement(
                temp_path, 
                default_account_type
            )
            
            if result['status'] == 'success':
                # Store in database
                transactions = result['transactions']
                if transactions:
                    # Add statement record
                    statement_date = transactions[0]['date'] if transactions else None
                    total_amount = sum(t['amount'] for t in transactions)
                    
                    statement_id = st.session_state.database.add_statement(
                        filename=uploaded_file.name,
                        statement_date=statement_date,
                        account_type=default_account_type,
                        transaction_count=len(transactions),
                        total_amount=total_amount
                    )
                    
                    # Add transactions
                    added_count = st.session_state.database.add_transactions(transactions)
                    
                    # Auto-categorize new transactions
                    categorized_count = st.session_state.database.auto_categorize_transactions()
                    
                    result['transactions_stored'] = added_count
                    if categorized_count > 0:
                        st.success(f"✅ {uploaded_file.name}: {added_count} transactions stored, {categorized_count} auto-categorized")
                    else:
                        st.success(f"✅ {uploaded_file.name}: {added_count} transactions stored")
                else:
                    st.warning(f"⚠️ {uploaded_file.name}: No transactions extracted")
            else:
                st.error(f"❌ {uploaded_file.name}: {result.get('message', 'Processing failed')}")
            
            results.append({
                'filename': uploaded_file.name,
                'status': result['status'],
                'total_transactions': len(result.get('transactions', [])),
                'message': result.get('message', '')
            })
            
            # Clean up temp file
            temp_path.unlink(missing_ok=True)
            
        except Exception as e:
            st.error(f"❌ Error processing {uploaded_file.name}: {str(e)}")
            results.append({
                'filename': uploaded_file.name,
                'status': 'error',
                'total_transactions': 0,
                'message': str(e)
            })
    
    # Update session state
    st.session_state.processed_files.extend(results)
    
    status_text.text("Processing complete!")
    progress_bar.progress(1.0)
    
    # Show summary
    successful = sum(1 for r in results if r['status'] == 'success')
    total_transactions = sum(r['total_transactions'] for r in results)
    
    st.success(f"Processing Summary: {successful}/{len(results)} files processed successfully. {total_transactions} total transactions added.")

def render_chat_interface():
    """Render chat interface for natural language queries"""
    st.markdown("### 💬 Financial Chat Assistant")
    
    if st.session_state.chat_handler is None:
        st.error("Chat handler not available. Please check your GROQ_API_KEY environment variable.")
        st.info("💡 Get a free API key at: https://console.groq.com/")
        return
    
    # Check for pre-filled queries (from sidebar or suggestions)
    user_query = None
    
    # Quick query from sidebar
    if hasattr(st.session_state, 'quick_query'):
        user_query = st.session_state.quick_query
        del st.session_state.quick_query
    
    # Query suggestions
    with st.expander("💡 Query Suggestions", expanded=False):
        suggestions = st.session_state.chat_handler.get_query_suggestions()
        cols = st.columns(2)
        for i, suggestion in enumerate(suggestions[:6]):
            with cols[i % 2]:
                if st.button(suggestion, key=f"suggest_{i}"):
                    user_query = suggestion
    
    # Chat input (only get input if no pre-filled query)
    if not user_query:
        user_query = st.chat_input("Ask about your finances...")
    
    if user_query:
        # Add user message to chat history
        st.session_state.chat_history.append({
            'role': 'user',
            'content': user_query,
            'timestamp': datetime.now()
        })
        
        # Process query
        with st.spinner("Analyzing your question..."):
            try:
                result = st.session_state.chat_handler.process_query(user_query)
                
                # Add assistant response
                st.session_state.chat_history.append({
                    'role': 'assistant',
                    'content': result,
                    'timestamp': datetime.now()
                })
                
            except Exception as e:
                st.error(f"Query processing failed: {str(e)}")
    
    # Display chat history
    for message in st.session_state.chat_history[-10:]:  # Show last 10 messages
        with st.container():
            if message['role'] == 'user':
                st.markdown(f"**You:** {message['content']}")
            else:
                result = message['content']
                if isinstance(result, dict) and result.get('status') == 'success':
                    response = result.get('response', {})
                    
                    # Show response
                    st.markdown(f"**Assistant:** {response.get('detailed_response', 'Here are your results:')}")
                    
                    # Show data if available
                    data = result.get('data', {})
                    if data:
                        render_query_results(result)
                elif isinstance(result, dict) and result.get('status') == 'error':
                    st.error(f"**Assistant:** {result.get('message', 'Something went wrong')}")
                else:
                    # Handle unexpected result format
                    if isinstance(result, str):
                        st.markdown(f"**Assistant:** {result}")
                    else:
                        st.error("**Assistant:** I encountered an unexpected error processing your query.")
            
            st.markdown("---")

def render_query_results(query_result: Dict[str, Any]):
    """Render query results with data and visualizations"""
    data = query_result.get('data', {})
    query_type = query_result.get('query_type', '')
    
    # Show key insights
    response = query_result.get('response', {})
    insights = response.get('key_insights', [])
    if insights:
        st.markdown("**Key Insights:**")
        for insight in insights:
            st.markdown(f"• {insight}")
    
    # Create appropriate visualization
    try:
        fig = None
        
        if query_type == 'category_breakdown':
            categories = data.get('categories', [])
            if categories:
                fig = st.session_state.visualizer.create_spending_by_category_chart(categories)
        
        elif query_type == 'trends':
            monthly_data = data.get('monthly_data', [])
            if monthly_data:
                fig = st.session_state.visualizer.create_monthly_trends_chart(monthly_data)
        
        elif query_type == 'search' or query_type == 'spending_analysis':
            transactions = data.get('transactions', [])
            if transactions:
                fig = st.session_state.visualizer.create_transaction_timeline(transactions)
        
        elif query_type == 'summary':
            stats = data.get('overall_stats', {})
            if stats:
                fig = st.session_state.visualizer.create_dashboard_summary(stats)
        
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        
        # Show data table if relevant
        if 'transactions' in data and len(data['transactions']) > 0:
            with st.expander("📋 Transaction Details", expanded=False):
                df = pd.DataFrame(data['transactions'])
                if not df.empty:
                    # Format for display - include location if available
                    available_cols = ['date', 'description', 'amount', 'category']
                    if 'location' in df.columns:
                        available_cols.insert(2, 'location')
                    
                    display_df = df[available_cols].copy()
                    display_df['amount'] = display_df['amount'].apply(lambda x: f"${x:,.2f}")
                    st.dataframe(display_df, use_container_width=True)
        
    except Exception as e:
        st.error(f"Visualization error: {str(e)}")
        logger.error(f"Visualization error: {e}")

def render_dashboard():
    """Render main dashboard with overview"""
    st.markdown("### 📊 Financial Dashboard")
    
    try:
        # Get database stats
        stats = st.session_state.database.get_database_stats()
        
        # Overview metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Transactions", stats['total_transactions'])
        with col2:
            st.metric("Total Spent", f"${stats['total_spent']:,.2f}")
        with col3:
            st.metric("Total Income", f"${stats['total_income']:,.2f}")
        with col4:
            st.metric("Net Change", f"${stats['net_worth_change']:,.2f}")
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Category breakdown
            category_data = st.session_state.database.get_spending_by_category()
            if not category_data.empty:
                fig = st.session_state.visualizer.create_spending_by_category_chart(
                    category_data.to_dict('records')
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Monthly trends
            trends_data = st.session_state.database.get_monthly_trends(6)
            if not trends_data.empty:
                fig = st.session_state.visualizer.create_monthly_trends_chart(
                    trends_data.to_dict('records')
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Recent transactions
        st.markdown("### 🕐 Recent Transactions")
        recent_df = st.session_state.database.get_transactions_df(limit=10)
        if not recent_df.empty:
            # Include location if available
            available_cols = ['date', 'description', 'amount', 'category']
            if 'location' in recent_df.columns:
                available_cols.insert(2, 'location')
            
            display_df = recent_df[available_cols].copy()
            display_df['amount'] = display_df['amount'].apply(lambda x: f"${x:,.2f}")
            st.dataframe(display_df, use_container_width=True)
        else:
            st.info("No transactions found. Upload some statements to get started!")
    
    except Exception as e:
        st.error(f"Dashboard error: {str(e)}")
        logger.error(f"Dashboard error: {e}")

def main():
    """Main application"""
    # Initialize session state
    initialize_session_state()
    
    # Header
    st.markdown('<h1 class="main-header">📊 Rufous v2</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #666;">Personal Financial Analysis with Natural Language Queries</p>', unsafe_allow_html=True)
    
    # Sidebar
    render_sidebar()
    
    # Main content based on current view
    current_view = getattr(st.session_state, 'current_view', 'dashboard')
    
    if current_view == 'upload':
        render_pdf_upload()
    elif current_view == 'chat':
        render_chat_interface()
    else:  # dashboard
        render_dashboard()
    
    # Footer
    st.markdown("---")
    st.markdown(
        '<p style="text-align: center; color: #666; font-size: 0.8rem;">Rufous v2 - Local Financial Analysis • Data stays on your device</p>',
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()