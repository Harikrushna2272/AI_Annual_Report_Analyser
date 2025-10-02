# Annual Report Analysis

A sophisticated AI-powered tool for analyzing annual reports using a multi-agent system with collaboration and memory, featuring an interactive Streamlit-based UI for comprehensive analysis visualization.

## Features

### Core Analysis Engine
- **Multi-Agent Analysis**: Specialized agents for different sections of annual reports
- **Collaborative Memory**: Shared insights between agents for better analysis
- **Task Decomposition**: Smart breaking down of complex analysis tasks
- **Enhanced Tools**: Web search, financial data, news aggregation, and web crawling capabilities
- **Sentiment Analysis**: Used Fine-Tunned FinBERT with financial shenanigans detection
- **Document Processing**: PDF parsing with advanced layout recognition

### Interactive UI Features
- **📊 Financial Analysis Dashboard**: Comprehensive financial metrics and performance indicators
- **🎯 Risk Assessment**: Strategic, operational, and ESG risk evaluation
- **📰 News & Sentiment Analysis**: Real-time news tracking with sentiment scoring
- **🌍 UN SDG Analysis**: Complete tracking of sustainability goals and initiatives
- **📈 Advanced Visualizations**: Interactive charts and multi-company comparisons

## Installation

### Basic Installation
```bash
pip install -e .
```

### Development Installation
```bash
pip install -e ".[dev]"
```

### Post-Installation
```bash
python scripts/postinstall.py
```

## Quick Start

### Command Line Analysis
1. Place your annual report in the output directory:
```bash
cp your_report.pdf annual_report_analysis/output/
```

2. Run the analysis:
```bash
python -m annual_report_analysis.utils.cli
```

3. Check the results:
```bash
cat annual_report_analysis/output/analysis_summary.json
```

### Interactive UI
1. Start the Streamlit application:
```bash
python run_ui.py
```

2. Open your web browser and navigate to http://localhost:8501

3. Use the sidebar to:
   - Select a company to analyze
   - Choose the analysis year
   - Toggle different analysis sections
   - Customize the view

## Project Structure

```
annual_report_analysis/
├── core/               # Core functionality and data models
│   ├── state.py       # Data models and state management
│   ├── config.py      # Configuration handling
│   └── workflow.py    # Main workflow orchestration
├── agents/            # Agent implementations
│   ├── agents.py      # Base and specialized agents
│   ├── memory.py      # Agent memory systems
│   └── prompts.py     # Agent prompts and guidance
├── tools/             # Analysis and processing tools
│   ├── tools.py       # Basic analysis tools
│   └── enhanced_tools.py  # Advanced tools (web, finance)
├── ui/                # Streamlit user interface
│   ├── app.py        # Main Streamlit application
│   └── mock_data.py  # Sample data for UI development
└── utils/             # Utility functions
    ├── cli.py         # Command line interface
    └── runner.py      # Execution runners
```

## Development

### Setup
```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Install pre-commit hook
cp scripts/pre-commit.py .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

### Common Tasks
```bash
# Format code
make format

# Run linting
make lint

# Run tests
make test

# Clean build artifacts
make clean
```

## Configuration

The system can be configured through:

1. Environment variables:
- `ANNUAL_FORCE_AGNO=1`: Force Agno runtime
- `ANNUAL_FORCE_FALLBACK=1`: Force deterministic path

2. CLI options:
```bash
annual-report-analysis 
  --input ./annual_report_analysis/output 
  --max-chars 3000 
  --force-agno
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- FinBERT-Shenanigans model for financial sentiment analysis
- SMOLDOCLING VLM for document parsing
- Agno framework for agent orchestration
- Streamlit for the interactive web interface
- Financial data providers and news sources
- UN SDG framework for sustainability metrics
