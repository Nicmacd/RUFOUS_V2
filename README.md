# Rufous v2 🦜

**Personal Financial Analysis with Natural Language Queries**

A privacy-first financial analysis tool that processes your bank statements locally using Ollama AI models. Ask questions about your spending in plain English and get instant insights with interactive charts.

![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat&logo=streamlit&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama-Local_AI-green)
![SQLite](https://img.shields.io/badge/SQLite-07405E?style=flat&logo=sqlite&logoColor=white)

## ✨ What's New in v2

- **🚀 10x Faster**: Direct database queries instead of slow MCP JSON processing
- **💬 Natural Language**: Ask questions like "How much did I spend on coffee last month?"
- **📊 Interactive Charts**: Instant visualizations with Plotly
- **🔒 100% Local**: Your data never leaves your computer
- **🎯 Smart Analysis**: Automatic categorization and merchant detection

## 🎯 Features

### 💬 Natural Language Queries
```
"Show me my spending trends over the last 6 months"
"How much did I spend at Starbucks this year?"  
"What are my top 5 expense categories?"
"Compare this month's spending to last month"
```

### 📊 Interactive Visualizations
- **Category breakdowns** with pie/bar charts
- **Monthly trends** with income vs expenses
- **Transaction timelines** and balance tracking
- **Merchant analysis** and spending patterns

### 📄 Smart PDF Processing
- **Automatic extraction** from any bank statement format
- **Duplicate detection** prevents double-counting
- **Multi-page support** for complete statements
- **Batch processing** for multiple files

### 🏦 Financial Insights
- Account balance tracking over time
- Spending pattern recognition
- Budget analysis and category trends  
- Merchant and recurring transaction detection

## 🚀 Quick Start

### Prerequisites

1. **Python 3.8+**
2. **Ollama** - Install from [ollama.ai](https://ollama.ai)
3. **Poppler** (for PDF processing):
   ```bash
   # macOS
   brew install poppler
   
   # Ubuntu/Debian  
   sudo apt-get install poppler-utils
   ```

### Installation

1. **Clone and setup**:
   ```bash
   git clone <repository-url>
   cd Rufous_v2
   pip install -r requirements.txt
   ```

2. **Start Ollama and pull models**:
   ```bash
   # Start Ollama service
   ollama serve
   
   # In another terminal, pull required models
   ollama pull moondream          # For PDF processing
   ollama pull llama3.2           # For chat queries
   ```

3. **Launch the app**:
   ```bash
   streamlit run app.py
   ```

4. **Open your browser** to `http://localhost:8501`

## 📖 How to Use

### 1. 📄 Upload Bank Statements
- Click **"Process PDFs"** in the sidebar
- Upload one or more PDF bank statements  
- Select account type (debit/credit)
- Click **"Process Statements"**

### 2. 💬 Ask Questions
- Click **"Chat Analysis"** in the sidebar
- Type natural language questions like:
  - "What did I spend the most money on last month?"
  - "Show me all my Amazon purchases"
  - "How is my spending trending?"

### 3. 📊 Explore Dashboard
- View **"Dashboard View"** for overview
- See spending breakdowns, trends, and key metrics
- Interactive charts you can zoom, pan, and explore

## 🏗️ Architecture

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

## 📁 Project Structure

```
Rufous_v2/
├── app.py                      # Main Streamlit application
├── components/
│   ├── database.py            # SQLite database operations
│   ├── pdf_processor.py       # Ollama PDF extraction
│   ├── chat_handler.py        # Natural language processing
│   └── visualizations.py      # Plotly chart generation
├── data/
│   └── transactions.db        # SQLite database (auto-created)
├── requirements.txt
└── README.md
```

## 🔧 Configuration

The app works out of the box with sensible defaults:

- **Database**: Stored in `./data/transactions.db`
- **Models**: `moondream` for PDFs, `llama3.2` for chat
- **Ollama**: Expected at `http://localhost:11434`

## 🆚 vs Original Rufous

| Feature | Original (MCP) | v2 (Streamlit) |
|---------|----------------|----------------|
| **Speed** | Slow JSON processing | 10x faster direct queries |
| **Interface** | Claude Desktop only | Dedicated web app |
| **Queries** | Limited MCP tools | Natural language |
| **Visualization** | None | Interactive charts |
| **User Experience** | Command-based | Conversational |

## 🔒 Privacy & Security

- **100% Local Processing**: AI models run on your machine
- **No Cloud APIs**: No data sent to external services  
- **Local Database**: All data stored in SQLite on your device
- **No Telemetry**: Zero tracking or analytics
- **Open Source**: Full transparency of code and data handling

## 💡 Example Queries

### Spending Analysis
- "How much did I spend on restaurants last quarter?"
- "What's my biggest expense category this year?"
- "Show me all transactions over $500"

### Trends & Patterns  
- "What are my monthly spending trends?"
- "Compare my spending this year vs last year"
- "Am I spending more or less than usual?"

### Specific Searches
- "Find all my Netflix payments"
- "Show me gas station purchases in December"
- "What did I buy at Target last month?"

### Financial Health
- "What's my account balance trend?"
- "How much do I spend on average per day?"
- "What percentage of income goes to each category?"

## 🛠️ Development

### Adding Custom Visualizations
Extend `components/visualizations.py`:

```python
def create_custom_chart(self, data):
    fig = px.custom_chart(data)
    return fig
```

### Adding Query Types
Extend `components/chat_handler.py`:

```python
def _analyze_query(self, user_query):
    # Add new query type logic
    if "custom pattern" in user_query.lower():
        return {"type": "custom_analysis", ...}
```

## 🐛 Troubleshooting

### PDF Processing Issues
```bash
# Install poppler if PDFs fail to process
brew install poppler  # macOS
sudo apt install poppler-utils  # Linux
```

### Ollama Connection Failed
```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama if needed
ollama serve
```

### Model Not Found
```bash
# Pull required models
ollama pull moondream
ollama pull llama3.2
```

## 🔮 Roadmap

### Near Term
- [ ] Transaction categorization rules
- [ ] Budget tracking and alerts
- [ ] Data export (CSV, Excel)
- [ ] Mobile-responsive design

### Future Features  
- [ ] Receipt OCR integration
- [ ] Investment portfolio tracking
- [ ] Multi-currency support
- [ ] Custom dashboard widgets
- [ ] API for external tools

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Ollama** for local AI inference
- **Streamlit** for rapid web app development
- **Plotly** for interactive visualizations
- **Original Rufous** for the foundational concept

---

**Built with ❤️ for privacy-conscious financial analysis**