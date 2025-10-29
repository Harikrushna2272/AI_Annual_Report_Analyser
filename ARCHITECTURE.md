# AI Annual Report Analyser - Architecture Overview

## System Architecture (LangGraph-Style with Knowledge Graph)

### Overview
This system analyzes annual reports using a multi-agent architecture with task decomposition, knowledge graph enrichment, and collaborative memory. The workflow follows a LangGraph-style orchestration pattern where chunks are processed through decomposed tasks, distributed to specialized sub-agents, and synthesized into a comprehensive report.

## Core Flow

### 1. Document Ingestion & Parsing
- **Input**: Annual report PDF
- **Process**: Docling + SmolDocling VLM for advanced layout recognition
- **Output**: Structured Markdown/JSON in `annual_report_analysis/output/`

### 2. Chunking & Preprocessing
- **Process**: Split document into ~3000 character chunks
- **Metadata**: Attach chunk_id, section_hint, source information
- **Storage**: StateGraph manages chunk queue and processing status

### 3. Knowledge Graph Enrichment (Per Chunk)
- **Entity Extraction**: Companies, persons, metrics, risks, opportunities, SDG goals
- **Relationship Mapping**: HAS_METRIC, FACES_RISK, LED_BY, TARGETS, etc.
- **Graph Operations**: Deduplication, centrality analysis, community detection
- **Storage**: NetworkX graph with GEXF export capability

### 4. Task Decomposition
- **Input**: Chunk content
- **Decomposition Types**:
  - FINANCIAL_ANALYSIS
  - RISK_ASSESSMENT
  - PERFORMANCE_METRICS
  - GOVERNANCE_REVIEW
  - SUSTAINABILITY_ANALYSIS
  - MARKET_ANALYSIS
  - STRATEGY_REVIEW
  - COMPLIANCE_CHECK
- **Output**: Prioritized tasks with dependencies and target agents

### 5. Section Routing & Agent Assignment
- **Section Types**: Letter to Shareholders, MD&A, Financial Statements, Audit Report, Corporate Governance, ESG/SDG, Other
- **Routing**: Based on section_hint + heuristic guessing
- **Assignment**: Each section has a SectionAgent orchestrating multiple sub-agents

### 6. Sub-Agent Processing (Parallel Execution)
Each SectionAgent orchestrates specialized sub-agents:

#### 6.1 SentimentAnalysisAgent
- FinBERT sentiment analysis
- Financial shenanigans detection
- Confidence scoring with adjustment for manipulation patterns

#### 6.2 RiskAssessmentAgent
- Model-based risk detection (zero-shot classification)
- Pattern-based risk identification
- Knowledge graph risk entity queries
- Risk categorization and prioritization

#### 6.3 MetricsExtractorAgent
- Regex-based metric extraction
- Knowledge graph metric entities
- Categorization (financial, operational, growth, efficiency)
- Key metric identification

#### 6.4 ExternalIntelligenceAgent (Optional)
- Web search integration
- Financial data APIs (yfinance)
- News gathering
- Market sentiment analysis

#### 6.5 GovernanceESGAgent
- Board structure analysis
- ESG element extraction
- SDG goal identification
- Compliance and sustainability scoring

#### 6.6 MemoryCoordinatorAgent
- Long-term memory retrieval
- Cross-section reference identification
- Collaborative insight generation
- Memory updates and persistence

### 7. State Graph Management
- **Blackboard Pattern**: Shared state accessible by all agents
- **Components**:
  - Chunk processing status
  - Task queue and completion tracking
  - Section summaries, findings, metrics, risks, opportunities
  - Cross-section insights and references
  - Knowledge graph entity/relationship tracking
  - Message passing between agents

### 8. Collaborative Memory & Cross-Section Insights
- **Long-Term Memory**: JSONL files per section for persistence
- **Collaborative Memory**: Agent subscriptions and cross-references
- **Pattern**: Related sections share insights (e.g., MD&A ↔ Financial Statements)

### 9. Final Report Generation (FinalGeneratorAgent)
- **Executive Summary**: Company overview, key findings, sentiment, financial highlights
- **Section Analyses**: Comprehensive per-section summaries with findings
- **Key Metrics**: Top 20 deduplicated metrics across all sections
- **Risk Assessment**: Categorized by priority with detailed descriptions
- **Opportunities**: Identified growth and improvement opportunities
- **Financial Health**: Overall assessment based on metrics and trends
- **Governance & ESG**: Board structure, sustainability initiatives, SDG alignment
- **Knowledge Graph Insights**: Key entities, centrality analysis, relationships
- **Cross-Section Insights**: Collaborative findings from related sections
- **Recommendations**: Actionable items based on analysis
- **Appendices**: Detailed data, KG statistics, processing metadata

### 10. Output Formats
- **CLI**: `analysis_summary.json` with structured results
- **UI**: Streamlit dashboard with interactive visualizations
- **Knowledge Graph**: GEXF format for graph analysis tools
- **Checkpoints**: Periodic state saves for recovery

## Component Architecture

### Core Modules

#### `/graph` - LangGraph-Style Orchestration
- `state_graph.py`: StateGraph blackboard for shared state
- `workflow.py`: Main orchestration engine

#### `/agents` - Multi-Agent System
- `sub_agents.py`: Specialized analysis sub-agents
- `task_decomposition.py`: Task decomposer with priority/dependency management
- `memory.py`: Short-term and long-term memory
- `collaborative_memory.py`: Cross-section insight sharing

#### `/tools` - Analysis Tools
- `document_processing.py`: Docling PDF parsing
- `knowledge_graph.py`: Entity/relationship extraction and graph operations
- `transformer_tools.py`: FinBERT, shenanigans detection, risk classification
- `enhanced_tools.py`: Web search, finance data, news, crawling

#### `/core` - Legacy/Fallback System
- Original deterministic workflow for backward compatibility
- Can be activated with `--force-fallback` flag

#### `/ui` - User Interface
- `app.py`: Streamlit dashboard for visualization

## Data Flow

```
PDF Document
    ↓
[Docling Parser] → Structured MD/JSON
    ↓
[Chunking] → Document Chunks
    ↓
[Knowledge Graph] ← Extract Entities/Relations
    ↓
[Task Decomposer] → Prioritized Tasks
    ↓
[Section Router] → Section Assignment
    ↓
[Section Agent] → Orchestrate Sub-Agents
    ↓
[Sub-Agents] ← Parallel Processing → [State Graph]
    ↓                                       ↑
[Memory Systems] ← Updates ←───────────────┘
    ↓
[Final Generator] → Comprehensive Report
    ↓
[Output] → JSON/UI/KG Export
```

## Key Design Patterns

1. **Blackboard Pattern**: StateGraph as shared workspace
2. **Task Decomposition**: Breaking complex analysis into manageable tasks
3. **Agent Orchestration**: Section agents managing specialized sub-agents
4. **Knowledge Graph**: Entity-relationship model for document understanding
5. **Collaborative Memory**: Cross-section insight sharing
6. **Pipeline Pattern**: Sequential processing with parallel sub-tasks

## Configuration Options

### Environment Variables
- `ANNUAL_FORCE_AGNO=1`: Use Agno runtime (if available)
- `ANNUAL_FORCE_FALLBACK=1`: Use deterministic fallback
- `ENABLE_WEB_SEARCH=1`: Enable external web search
- `ENABLE_FINANCE_DATA=1`: Enable financial data APIs
- `ENABLE_NEWS=1`: Enable news gathering

### CLI Arguments
- `--pdf <path>`: Direct PDF input
- `--input <path>`: Input directory or file
- `--max-chars <int>`: Chunk size (default: 3000)
- `--output-dir <path>`: Output directory
- `--force-agno`: Force Agno runtime
- `--force-fallback`: Force deterministic runtime
- `--enable-web-search`: Enable web search
- `--enable-finance-data`: Enable finance APIs
- `--enable-news`: Enable news gathering
- `--verbose`: Verbose output
- `--debug`: Debug mode

## Extensibility

### Adding New Section Types
1. Add to `SectionName` enum in `core/state.py`
2. Create specialized agent class extending `BaseSectionAgent`
3. Add routing logic in `guess_section()`
4. Register in workflow's section_agents map

### Adding New Sub-Agents
1. Create class extending `BaseSubAgent` in `agents/sub_agents.py`
2. Implement `process()` method
3. Add to SectionAgent's sub_agents dictionary
4. Map to task types in `task_agent_mapping`

### Adding New Task Types
1. Add to `TaskType` enum in `agents/task_decomposition.py`
2. Define patterns in `task_patterns`
3. Add agent mapping in `task_agent_mapping`
4. Implement priority and dependency logic

### Adding New Entity/Relationship Types
1. Add to entity_types/relationship_types in `KnowledgeGraph`
2. Implement extraction patterns
3. Add to extraction methods

## Performance Considerations

- **Chunking**: Configurable size for memory efficiency
- **Parallel Processing**: Sub-agents run concurrently via asyncio
- **Caching**: Knowledge graph and tool results are cached
- **Checkpointing**: Periodic state saves for recovery
- **Lazy Loading**: Models loaded on first use

## Security Considerations

- **API Keys**: Stored as environment variables
- **File System**: Bounded to project directories
- **External Calls**: Rate-limited and error-handled
- **PDF Processing**: Sandboxed document parsing

## Testing

- Component tests in `test_new_workflow.py`
- Test StateGraph, KnowledgeGraph, TaskDecomposer
- Test SectionAgent with sub-agents
- Test FinalGeneratorAgent report generation
- Integration test for full workflow

## Future Enhancements

1. **Distributed Processing**: Multi-node agent execution
2. **Real-time Collaboration**: WebSocket-based agent communication
3. **ML Model Fine-tuning**: Domain-specific model training
4. **Graph Database**: Neo4j integration for scalability
5. **API Service**: RESTful API for remote analysis
6. **Batch Processing**: Multiple document analysis
7. **Incremental Updates**: Delta processing for document revisions
8. **Custom Ontologies**: Industry-specific knowledge graphs