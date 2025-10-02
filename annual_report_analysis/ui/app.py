"""Main Streamlit application for Annual Report Analysis."""

import streamlit as st
import pandas as pd

# Sample static data
SAMPLE_COMPANIES = {
    "AAPL": "Apple Inc.",
    "MSFT": "Microsoft Corporation",
    "GOOGL": "Alphabet Inc.",
    "AMZN": "Amazon.com, Inc.",
    "META": "Meta Platforms Inc.",
    "NVDA": "NVIDIA Corporation",
    "TSM": "Taiwan Semiconductor Manufacturing",
    "ASML": "ASML Holding N.V."
}

# Financial metrics data
FINANCIAL_DATA = {
    "AAPL": {
        "revenue": {"value": "₹365.8B", "change": "8.2%"},
        "net_income": {"value": "₹96.7B", "change": "5.5%"},
        "eps": {"value": "₹6.15", "change": "7.8%"},
        "operating_margin": {"value": "30.5%", "change": "-1.2%"},
        "r_and_d": {"value": "₹27.4B", "change": "15.3%"},
        "cash_flow": {"value": "₹110.5B", "change": "3.8%"},
        "market_cap": {"value": "₹2.85T", "change": "12.4%"},
        "pe_ratio": {"value": "29.5", "change": "-2.1%"}
    }
}

# ESG Metrics
ESG_DATA = {
    "AAPL": {
        "environmental": {
            "carbon_footprint": {"value": "22.5M", "unit": "metric tons CO2e", "change": "-15%"},
            "renewable_energy": {"value": "95", "unit": "%", "change": "+5%"},
            "water_usage": {"value": "1.2B", "unit": "gallons", "change": "-8%"}
        },
        "social": {
            "workforce_diversity": {"value": "45", "unit": "%", "change": "+3%"},
            "supplier_compliance": {"value": "98", "unit": "%", "change": "+2%"},
            "community_investment": {"value": "₹350M", "unit": "", "change": "+25%"}
        },
        "governance": {
            "board_independence": {"value": "85", "unit": "%", "change": "0%"},
            "ethics_compliance": {"value": "99.5", "unit": "%", "change": "+0.5%"},
            "shareholder_rights": {"value": "95", "unit": "%", "change": "+5%"}
        }
    }
}

# SDG 17 Parameters Data
SDG_DATA = {
    "AAPL": {
        "sdg1_no_poverty": {
            "score": 85,
            "initiatives": ["Job Creation Programs", "Supplier Development", "Economic Empowerment"],
            "impact": "High",
            "investment": "₹250M"
        },
        "sdg2_zero_hunger": {
            "score": 70,
            "initiatives": ["Food Security Programs", "Agricultural Tech Support"],
            "impact": "Medium",
            "investment": "₹120M"
        },
        "sdg3_good_health": {
            "score": 90,
            "initiatives": ["Health Monitoring Devices", "Healthcare Research"],
            "impact": "High",
            "investment": "₹380M"
        },
        "sdg4_quality_education": {
            "score": 88,
            "initiatives": ["Coding Education", "STEM Programs", "Digital Learning"],
            "impact": "High",
            "investment": "₹290M"
        },
        "sdg5_gender_equality": {
            "score": 85,
            "initiatives": ["Women in Tech", "Equal Pay Initiative"],
            "impact": "High",
            "investment": "₹200M"
        },
        "sdg6_clean_water": {
            "score": 75,
            "initiatives": ["Water Conservation", "Clean Water Tech"],
            "impact": "Medium",
            "investment": "₹150M"
        },
        "sdg7_clean_energy": {
            "score": 95,
            "initiatives": ["Renewable Energy", "Carbon Neutral Operations"],
            "impact": "High",
            "investment": "₹450M"
        },
        "sdg8_economic_growth": {
            "score": 92,
            "initiatives": ["Job Creation", "Economic Development"],
            "impact": "High",
            "investment": "₹500M"
        },
        "sdg9_innovation": {
            "score": 95,
            "initiatives": ["R&D Investment", "Infrastructure Development"],
            "impact": "High",
            "investment": "₹800M"
        },
        "sdg10_reduced_inequalities": {
            "score": 83,
            "initiatives": ["Diversity Programs", "Accessibility Features"],
            "impact": "High",
            "investment": "₹280M"
        },
        "sdg11_sustainable_cities": {
            "score": 78,
            "initiatives": ["Smart City Solutions", "Urban Development"],
            "impact": "Medium",
            "investment": "₹220M"
        },
        "sdg12_responsible_consumption": {
            "score": 88,
            "initiatives": ["Recycling Programs", "Sustainable Packaging"],
            "impact": "High",
            "investment": "₹320M"
        },
        "sdg13_climate_action": {
            "score": 90,
            "initiatives": ["Carbon Reduction", "Environmental Protection"],
            "impact": "High",
            "investment": "₹400M"
        },
        "sdg14_life_below_water": {
            "score": 72,
            "initiatives": ["Ocean Protection", "Plastic Reduction"],
            "impact": "Medium",
            "investment": "₹100M"
        },
        "sdg15_life_on_land": {
            "score": 75,
            "initiatives": ["Biodiversity Protection", "Forest Conservation"],
            "impact": "Medium",
            "investment": "₹130M"
        },
        "sdg16_peace_justice": {
            "score": 85,
            "initiatives": ["Ethics Programs", "Human Rights"],
            "impact": "High",
            "investment": "₹180M"
        },
        "sdg17_partnerships": {
            "score": 89,
            "initiatives": ["Global Partnerships", "Technology Transfer"],
            "impact": "High",
            "investment": "₹350M"
        }
    }
}

# Risk Assessment Data
RISK_DATA = {
    "AAPL": {
        "strategic_risks": [
            {"name": "AI Competition", "severity": "High", "trend": "↑", "impact": "8.5"},
            {"name": "Market Saturation", "severity": "Medium", "trend": "→", "impact": "6.2"},
            {"name": "Emerging Markets", "severity": "Medium", "trend": "↓", "impact": "5.8"}
        ],
        "operational_risks": [
            {"name": "Supply Chain", "severity": "High", "trend": "→", "impact": "8.0"},
            {"name": "Talent Retention", "severity": "Medium", "trend": "↑", "impact": "7.2"},
            {"name": "Product Innovation", "severity": "Medium", "trend": "→", "impact": "6.8"}
        ],
        "financial_risks": [
            {"name": "Currency Exchange", "severity": "Medium", "trend": "↑", "impact": "5.5"},
            {"name": "Tax Regulations", "severity": "Medium", "trend": "→", "impact": "5.0"},
            {"name": "Credit Risk", "severity": "Low", "trend": "→", "impact": "3.2"}
        ]
    }
}

def set_page_config():
    """Configure the Streamlit page."""
    st.set_page_config(
        page_title="Annual Report Analyzer",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )

def sidebar():
    """Render the sidebar."""
    with st.sidebar:
        st.title("Annual Report Analyzer")
        
        # Company selection
        selected_company = st.selectbox(
            "Select Company",
            options=list(SAMPLE_COMPANIES.keys()),
            format_func=lambda x: f"{x} - {SAMPLE_COMPANIES[x]}"
        )
        
        # Year selection
        selected_year = st.selectbox(
            "Select Year",
            options=["2025", "2024", "2023"],
        )
        
        # Analysis options
        st.subheader("Analysis Options")
        show_financial = st.checkbox("Financial Analysis", value=True)
        show_risks = st.checkbox("Risk Analysis", value=True)
        show_sentiment = st.checkbox("Sentiment Analysis", value=True)
        show_news = st.checkbox("News Analysis", value=True)
        
        return {
            "company": selected_company,
            "year": selected_year,
            "options": {
                "financial": show_financial,
                "risks": show_risks,
                "sentiment": show_sentiment,
                "news": show_news
            }
        }

def header_section(company: str, year: str):
    """Render the header section."""
    st.title(f"{SAMPLE_COMPANIES[company]} - Annual Report Analysis {year}")
    st.markdown("---")

def financial_metrics_section():
    """Render financial metrics section with static data."""
    st.header("📈 Financial Performance Analysis")
    
    # Key Financial Metrics
    st.subheader("Key Financial Metrics")
    metrics_cols = st.columns(4)
    with metrics_cols[0]:
        st.metric(
            "Revenue",
            FINANCIAL_DATA["AAPL"]["revenue"]["value"],
            FINANCIAL_DATA["AAPL"]["revenue"]["change"]
        )
    with metrics_cols[1]:
        st.metric(
            "Net Income",
            FINANCIAL_DATA["AAPL"]["net_income"]["value"],
            FINANCIAL_DATA["AAPL"]["net_income"]["change"]
        )
    with metrics_cols[2]:
        st.metric(
            "EPS",
            FINANCIAL_DATA["AAPL"]["eps"]["value"],
            FINANCIAL_DATA["AAPL"]["eps"]["change"]
        )
    with metrics_cols[3]:
        st.metric(
            "Operating Margin",
            FINANCIAL_DATA["AAPL"]["operating_margin"]["value"],
            FINANCIAL_DATA["AAPL"]["operating_margin"]["change"]
        )
    
    st.markdown("---")
    
    # Segment Performance
    st.subheader("Segment Performance")
    col1, col2 = st.columns([2, 1])
    
    with col1:
        segment_data = pd.DataFrame({
            'Segment': ['iPhone', 'Services', 'Mac', 'Wearables', 'iPad'],
            'Revenue (₹B)': [205.4, 95.4, 40.2, 38.5, 20.3],
            'YoY Growth': ['6.5%', '15.8%', '-3.2%', '12.4%', '-5.1%'],
            'Margin': ['42%', '70%', '35%', '38%', '32%']
        })
        st.dataframe(segment_data, hide_index=True)
    
    with col2:
        st.markdown("### Segment Highlights")
        st.markdown("""
        - **Services**: Highest margin at 70%, strong growth
        - **iPhone**: Core revenue driver with healthy margins
        - **Wearables**: Growing segment with good margins
        - **Mac & iPad**: Cyclical performance
        """)
    
    st.markdown("---")
    
    # Financial Health Indicators
    st.subheader("Financial Health Indicators")
    health_cols = st.columns(3)
    
    with health_cols[0]:
        st.markdown("### Liquidity")
        st.markdown("""
        - Current Ratio: 1.8x
        - Quick Ratio: 1.5x
        - Cash Ratio: 0.9x
        """)
    
    with health_cols[1]:
        st.markdown("### Solvency")
        st.markdown("""
        - Debt/Equity: 1.2x
        - Interest Coverage: 25x
        - Debt/EBITDA: 1.1x
        """)
    
    with health_cols[2]:
        st.markdown("### Efficiency")
        st.markdown("""
        - Asset Turnover: 1.1x
        - Inventory Turnover: 40x
        - Receivables Days: 35
        """)

def risk_analysis_section():
    """Render risk analysis section with static data."""
    st.header("🎯 Comprehensive Risk Analysis")
    
    # Strategic Risks
    st.subheader("Strategic Risks")
    strategic_data = pd.DataFrame(RISK_DATA["AAPL"]["strategic_risks"])
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.dataframe(strategic_data, hide_index=True)
    
    with col2:
        st.markdown("### Key Strategic Concerns")
        st.markdown("""
        - AI competition intensifying
        - Market saturation in key segments
        - Emerging market challenges
        """)
    
    st.markdown("---")
    
    # Operational Risks
    st.subheader("Operational Risks")
    operational_data = pd.DataFrame(RISK_DATA["AAPL"]["operational_risks"])
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.dataframe(operational_data, hide_index=True)
    
    with col2:
        st.markdown("### Operational Focus Areas")
        st.markdown("""
        - Supply chain diversification
        - Talent retention strategies
        - Innovation pipeline management
        """)
    
    st.markdown("---")
    
    # ESG Risk Analysis
    st.subheader("ESG Risk Analysis")
    esg_cols = st.columns(3)
    
    with esg_cols[0]:
        st.markdown("### Environmental")
        st.metric("Carbon Footprint", 
                 ESG_DATA["AAPL"]["environmental"]["carbon_footprint"]["value"],
                 ESG_DATA["AAPL"]["environmental"]["carbon_footprint"]["change"])
        st.metric("Renewable Energy", 
                 f"{ESG_DATA['AAPL']['environmental']['renewable_energy']['value']}%",
                 ESG_DATA["AAPL"]["environmental"]["renewable_energy"]["change"])
    
    with esg_cols[1]:
        st.markdown("### Social")
        st.metric("Workforce Diversity",
                 f"{ESG_DATA['AAPL']['social']['workforce_diversity']['value']}%",
                 ESG_DATA["AAPL"]["social"]["workforce_diversity"]["change"])
        st.metric("Supplier Compliance",
                 f"{ESG_DATA['AAPL']['social']['supplier_compliance']['value']}%",
                 ESG_DATA["AAPL"]["social"]["supplier_compliance"]["change"])
    
    with esg_cols[2]:
        st.markdown("### Governance")
        st.metric("Board Independence",
                 f"{ESG_DATA['AAPL']['governance']['board_independence']['value']}%",
                 ESG_DATA["AAPL"]["governance"]["board_independence"]["change"])
        st.metric("Ethics Compliance",
                 f"{ESG_DATA['AAPL']['governance']['ethics_compliance']['value']}%",
                 ESG_DATA["AAPL"]["governance"]["ethics_compliance"]["change"])

def sentiment_analysis_section():
    """Render sentiment analysis section with static data."""
    st.header("😊 Sentiment Analysis")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Key Sentiment Indicators")
        sentiment_data = pd.DataFrame({
            'Category': ['Positive', 'Neutral', 'Negative'],
            'Percentage': [75, 15, 10]
        })
        st.bar_chart(sentiment_data.set_index('Category'))
    
    with col2:
        st.subheader("Key Topics")
        topics = [
            {"topic": "Innovation", "sentiment": "positive", "score": 0.9},
            {"topic": "Market Share", "sentiment": "positive", "score": 0.8},
            {"topic": "Competition", "sentiment": "neutral", "score": 0.5},
            {"topic": "Regulations", "sentiment": "negative", "score": 0.3}
        ]
        for topic in topics:
            st.markdown(
                f"**{topic['topic']}**: _{topic['sentiment']}_ "
                f"({topic['score']:.2f})"
            )

def section_summaries():
    """Render section summaries with static data."""
    st.header("📑 Section-wise Analysis")
    
    # Letter to Shareholders
    with st.expander("1. Letter to Shareholders", expanded=True):
        st.subheader("Key Highlights")
        st.markdown("* Record-breaking financial performance in FY2025")
        st.markdown("* Strategic focus on AI and sustainable technology")
        st.markdown("* Expansion into new markets and product categories")
        
        st.subheader("Management Vision")
        st.markdown("* Innovation in AI and machine learning")
        st.markdown("* Commitment to sustainability goals")
        st.markdown("* Customer-centric product development")
    
    # Financial Analysis
    with st.expander("2. Financial Analysis"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Cash & Equivalents", "$62.5B", "↑ 5.2%")
            st.metric("Total Assets", "$425.2B", "↑ 8.1%")
        
        with col2:
            st.metric("Long-term Debt", "$98.3B", "↓ 3.5%")
            st.metric("Shareholders' Equity", "$195.6B", "↑ 12.3%")
        
        st.subheader("Segment Performance")
        segment_data = pd.DataFrame({
            'Segment': ['iPhone', 'Services', 'Mac', 'Wearables', 'iPad'],
            'Revenue ($B)': [205.4, 95.4, 40.2, 38.5, 20.3],
            'Growth': ['6.5%', '15.8%', '-3.2%', '12.4%', '-5.1%']
        })
        st.dataframe(segment_data, hide_index=True)
    
    # Risk Assessment
    with st.expander("3. Risk Assessment", expanded=True):
        st.subheader("Key Risk Areas")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**High Priority Risks**")
            st.markdown("* Competition in AI sector")
            st.markdown("* Supply chain dependencies")
            st.markdown("* Regulatory compliance")
        
        with col2:
            st.markdown("**Mitigation Strategies**")
            st.markdown("* Increased R&D investment")
            st.markdown("* Supplier diversification")
            st.markdown("* Enhanced compliance protocols")

def news_analysis_section():
    """Render news analysis section."""
    st.header("📰 News & Market Sentiment Analysis")
    
    # Recent News
    st.subheader("Recent News & Events")
    news = [
        {
            "title": "Apple's Revolutionary AI Integration in iOS Platform",
            "source": "Financial Times",
            "sentiment": "positive",
            "date": "2025-10-01",
            "impact": "High",
            "summary": "Integration of advanced AI features in iOS ecosystem, potential game-changer for mobile AI"
        },
        {
            "title": "Q3 FY2025 Earnings Surpass Wall Street Expectations",
            "source": "Bloomberg",
            "sentiment": "positive",
            "date": "2025-09-28",
            "impact": "High",
            "summary": "Revenue up 8.2% YoY, Services revenue hits new record, strong iPhone 16 demand"
        },
        {
            "title": "EU Regulatory Review of App Store Practices",
            "source": "Reuters",
            "sentiment": "negative",
            "date": "2025-09-25",
            "impact": "Medium",
            "summary": "New EU digital regulations may impact App Store revenue model"
        },
        {
            "title": "Supply Chain Diversification in Southeast Asia",
            "source": "Wall Street Journal",
            "sentiment": "positive",
            "date": "2025-09-22",
            "impact": "Medium",
            "summary": "Strategic expansion of manufacturing partnerships in Vietnam and India"
        },
        {
            "title": "New AR/VR Product Line Launch Expected",
            "source": "TechCrunch",
            "sentiment": "positive",
            "date": "2025-09-20",
            "impact": "High",
            "summary": "Anticipated launch of next-gen mixed reality devices in Q4"
        }
    ]
    
    # Display news with expanded information
    for article in news:
        with st.container():
            # Header row
            cols = st.columns([3, 1, 1, 1])
            with cols[0]:
                st.write(f"**{article['title']}**")
            with cols[1]:
                st.write(f"*{article['source']}*")
            with cols[2]:
                sentiment_color = {
                    'positive': 'green',
                    'negative': 'red',
                    'neutral': 'gray'
                }[article['sentiment']]
                st.markdown(f":{sentiment_color}[{article['sentiment'].title()}]")
            with cols[3]:
                impact_color = {
                    'High': 'red',
                    'Medium': 'orange',
                    'Low': 'green'
                }[article['impact']]
                st.markdown(f"Impact: :{impact_color}[{article['impact']}]")
            
            # Summary row
            st.markdown(f"> {article['summary']}")
            st.markdown(f"*Date: {article['date']}*")
            st.markdown("---")
    
    # Sentiment Analysis Summary
    st.subheader("Sentiment Analysis Summary")
    sent_col1, sent_col2 = st.columns([1, 1])
    
    with sent_col1:
        sentiment_counts = {
            'Positive': len([x for x in news if x['sentiment'] == 'positive']),
            'Negative': len([x for x in news if x['sentiment'] == 'negative']),
            'Neutral': len([x for x in news if x['sentiment'] == 'neutral'])
        }
        st.bar_chart(sentiment_counts)
    
    with sent_col2:
        st.markdown("### Key Takeaways")
        st.markdown("""
        - Strong positive sentiment around AI initiatives
        - Mixed reactions to regulatory developments
        - High anticipation for new product launches
        - Positive response to supply chain strategy
        """)

def sdg_analysis_section():
    """Render SDG analysis section."""
    st.header("🌍 UN Sustainable Development Goals (SDG) Analysis")
    
    # Overall SDG Score
    total_score = sum(SDG_DATA["AAPL"][sdg]["score"] for sdg in SDG_DATA["AAPL"]) / len(SDG_DATA["AAPL"])
    total_investment = sum(float(SDG_DATA["AAPL"][sdg]["investment"].replace("₹", "").replace("M", "")) 
                         for sdg in SDG_DATA["AAPL"])
    
    st.subheader("Overall SDG Performance")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Average SDG Score", f"{total_score:.1f}/100", "+5.2")
    with col2:
        st.metric("Total SDG Investment", f"₹{total_investment:.0f}M", "+15.5%")
    
    st.markdown("---")
    
    # SDG Scorecard
    st.subheader("SDG Scorecard")
    
    # Create a DataFrame for all SDGs
    sdg_df = pd.DataFrame([
        {
            'SDG': sdg.replace('_', ' ').title(),
            'Score': data['score'],
            'Impact': data['impact'],
            'Investment': data['investment'],
            'Key Initiatives': ', '.join(data['initiatives'])
        }
        for sdg, data in SDG_DATA["AAPL"].items()
    ])
    
    # Display as interactive table
    st.dataframe(
        sdg_df,
        column_config={
            'SDG': 'Sustainable Development Goal',
            'Score': st.column_config.ProgressColumn(
                'Score',
                help='Score out of 100',
                format='%d/100',
                min_value=0,
                max_value=100,
            ),
            'Impact': st.column_config.SelectboxColumn(
                'Impact Level',
                help='Impact level of initiatives',
                options=['High', 'Medium', 'Low'],
            ),
            'Investment': 'Investment Amount',
            'Key Initiatives': st.column_config.TextColumn(
                'Key Initiatives',
                help='Major initiatives supporting this SDG',
                max_chars=50
            ),
        },
        hide_index=True
    )
    
    st.markdown("---")
    
    # Top Performing SDGs
    st.subheader("Top Performing SDGs")
    top_sdgs = sorted(
        [(sdg, data) for sdg, data in SDG_DATA["AAPL"].items()],
        key=lambda x: x[1]['score'],
        reverse=True
    )[:5]
    
    for sdg, data in top_sdgs:
        with st.container():
            cols = st.columns([1, 2, 1])
            with cols[0]:
                st.metric(
                    sdg.replace('_', ' ').title(),
                    f"{data['score']}/100"
                )
            with cols[1]:
                st.write("**Key Initiatives:**")
                for initiative in data['initiatives']:
                    st.markdown(f"• {initiative}")
            with cols[2]:
                st.metric("Investment", data['investment'])
            st.markdown("---")

def main():
    """Main application entry point."""
    set_page_config()
    
    # Render sidebar and get selections
    selections = sidebar()
    
    # Render main content
    header_section(selections['company'], selections['year'])
    
    if selections['options']['financial']:
        financial_metrics_section()
        st.markdown("---")
    
    if selections['options']['risks']:
        risk_analysis_section()
        st.markdown("---")
    
    if selections['options']['sentiment']:
        sentiment_analysis_section()
        st.markdown("---")
    
    # Always show section summaries and SDG analysis
    section_summaries()
    st.markdown("---")
    
    # Show SDG Analysis
    sdg_analysis_section()
    st.markdown("---")
    
    if selections['options']['news']:
        news_analysis_section()

if __name__ == "__main__":
    main()
