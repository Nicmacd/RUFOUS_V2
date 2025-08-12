# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Rufous v2 is a privacy-first financial analysis tool built with Streamlit that processes bank statements locally using text-based PDF extraction. Users can upload PDF statements and query their financial data using natural language (powered by local Ollama models).

## Common Development Commands

### Setup and Installation
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install system dependencies (PDF processing)
brew install poppler  # macOS
sudo apt-get install poppler-utils  # Ubuntu/Debian

# Test setup and verify components
python test_setup.py
```

### Ollama Model Management (Chat Only)
```bash
# Start Ollama service (required for natural language queries only)
ollama serve

# Pull required model for chat
ollama pull llama3.2           # For natural language queries

# Check available models
ollama list

# Note: PDF processing now uses text-based extraction (no AI models needed)
```

### Running the Application
```bash
# Start the Streamlit app
streamlit run app.py

# The app will be available at http://localhost:8501
```

### Testing and Verification
```bash
# Run the comprehensive setup test
python test_setup.py

# Test individual components (no formal test framework used)
# Use the test_setup.py script to verify all components work
```

## Architecture Overview

### Core Components Architecture

The application follows a modular architecture with clear separation of concerns:

```
┌─────────────────┐    ┌──────────────────┐    ┌────────────────┐
│   Streamlit     │    │     Ollama       │    │    SQLite      │
│   Frontend      │◄──►│   AI Models      │    │   Database     │
│                 │    │                  │    │                │
│ • Chat UI       │    │ • Vision (PDFs)  │    │ • Transactions │
│ • File Upload   │    │ • Text (Queries) │    │ • Categories   │
│ • Visualizations│    │ • Local Only     │    │ • Query History│
└─────────────────┘    └──────────────────┘    └────────────────┘
```

### Component Structure

- **app.py**: Main Streamlit application with UI routing and session management
- **components/database.py**: SQLite database operations with optimized schemas for analytics
- **components/clean_pdf_processor.py**: Text-based PDF transaction extraction (high accuracy, fast)
- **components/pdf_processor.py**: Legacy vision model integration (deprecated)
- **components/chat_handler.py**: Natural language query processing using Ollama text models
- **components/visualizations.py**: Plotly chart generation for financial data visualization

### Key Design Patterns

1. **Session State Management**: All components are initialized in Streamlit session state for persistence across interactions
2. **Local-First Architecture**: No external API calls - all AI processing via local Ollama models
3. **Database-Centric**: SQLite with performance indexes for fast analytical queries
4. **Component Isolation**: Each component handles its own initialization and error handling

### Database Schema

The SQLite database uses an optimized schema for financial analytics:

- **transactions**: Core transaction data with indexes on date, amount, category, merchant
- **statements**: PDF processing tracking with metadata
- **categories**: Hierarchical category system with keywords for auto-classification
- **query_history**: User query tracking for favorites and analytics

### AI Model Integration

- **Text-based extraction**: High-accuracy parsing of BMO credit card statements using pdfplumber
- **llama3.2**: Handles natural language queries and converts them to database operations

PDF extraction runs locally using text parsing (no AI needed). Chat queries use local Ollama models, ensuring complete privacy.

### Error Handling Strategy

Components gracefully degrade when dependencies are unavailable:
- PDF processing requires pdfplumber (fast text extraction)
- Chat features disabled if Ollama/llama3.2 unavailable  
- Database operations continue independently
- UI shows appropriate error messages and setup instructions

## Development Notes

### Adding New Query Types

Extend `components/chat_handler.py`:
1. Add new query pattern detection in `_analyze_query()`
2. Implement corresponding database query method
3. Add visualization logic in `visualizations.py`

### Adding New Chart Types

Extend `components/visualizations.py`:
1. Create new chart method following existing patterns
2. Use Plotly for consistency
3. Handle empty data states with `_create_empty_chart()`

### Database Migrations

No formal migration system exists. Schema changes should be additive and handled in `RufousDatabase._initialize_database()` with `IF NOT EXISTS` clauses.

### Debugging Ollama Integration

- Check Ollama service: `curl http://localhost:11434/api/tags`
- Verify models available: `ollama list`
- Monitor logs in terminal running `ollama serve`
- Use `test_setup.py` for comprehensive diagnostics