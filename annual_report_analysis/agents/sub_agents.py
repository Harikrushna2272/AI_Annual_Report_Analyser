"""
Sub-agents for specialized analysis within each section
Each section agent can orchestrate multiple sub-agents for specific tasks
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import json
from datetime import datetime

from ..tools.transformer_tools import (
    analyze_sentiment_finbert,
    detect_risk_fingpt,
    detect_financial_shenanigans,
)
from ..tools.enhanced_tools import (
    WebSearchTool,
    FinanceDataTool,
    WebCrawlerTool,
    NewsTool,
)
from ..tools.knowledge_graph import KnowledgeGraph, extract_and_add_to_graph
from ..agents.memory import ShortTermMemory, LongTermMemory
from ..graph.state_graph import StateGraph, GraphMessage, MessageType


@dataclass
class SubAgentResult:
    """Result from a sub-agent execution"""

    agent_name: str
    task_id: str
    output: Any
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0
    errors: List[str] = field(default_factory=list)


class BaseSubAgent(ABC):
    """Base class for all sub-agents"""

    def __init__(
        self,
        name: str,
        section: str,
        state_graph: StateGraph,
        knowledge_graph: KnowledgeGraph,
    ):
        self.name = name
        self.section = section
        self.state_graph = state_graph
        self.knowledge_graph = knowledge_graph
        self.short_term_memory = ShortTermMemory(capacity=10)

    @abstractmethod
    def process(self, content: str, context: Dict[str, Any]) -> SubAgentResult:
        """Process content and return results"""
        pass

    def send_message(self, recipient: str, content: Any, msg_type: MessageType = MessageType.INFO):
        """Send message through state graph"""
        message = GraphMessage(
            id=f"{self.name}_{datetime.now().timestamp()}",
            type=msg_type,
            sender=self.name,
            recipient=recipient,
            content=content,
        )
        self.state_graph.send_message(message)

    def receive_messages(self) -> List[GraphMessage]:
        """Receive messages from state graph"""
        return self.state_graph.receive_messages(self.name)


class SentimentAnalysisAgent(BaseSubAgent):
    """Sub-agent for sentiment and shenanigans analysis"""

    def process(self, content: str, context: Dict[str, Any]) -> SubAgentResult:
        """Analyze sentiment and detect financial shenanigans"""
        start_time = datetime.now()
        errors = []

        # Run sentiment analysis
        sentiment = analyze_sentiment_finbert(content)
        if not sentiment:
            sentiment = {"positive": 0.0, "neutral": 1.0, "negative": 0.0, "label": "neutral"}
            errors.append("FinBERT model unavailable, using defaults")

        # Detect shenanigans
        shenanigans = detect_financial_shenanigans(content)
        if not shenanigans:
            shenanigans = {}
            errors.append("Shenanigans detection unavailable")

        # Identify high-risk patterns
        high_risk_patterns = [
            pattern for pattern, score in shenanigans.items()
            if score > 0.7
        ]

        # Calculate overall sentiment score
        sentiment_score = (
            sentiment.get("positive", 0) * 1.0 +
            sentiment.get("neutral", 0) * 0.5 +
            sentiment.get("negative", 0) * 0.0
        )

        # Adjust for shenanigans
        if high_risk_patterns:
            sentiment_score *= 0.7  # Reduce confidence if shenanigans detected

        result = {
            "sentiment": sentiment,
            "sentiment_score": sentiment_score,
            "shenanigans_patterns": shenanigans,
            "high_risk_patterns": high_risk_patterns,
            "overall_assessment": self._generate_assessment(sentiment, shenanigans),
        }

        # Update state graph
        self.state_graph.add_section_finding(
            self.section,
            "sentiment_analysis",
            result
        )

        execution_time = (datetime.now() - start_time).total_seconds()

        return SubAgentResult(
            agent_name=self.name,
            task_id=context.get("task_id", "sentiment_analysis"),
            output=result,
            confidence=0.9 if not errors else 0.6,
            metadata={"chunk_id": context.get("chunk_id")},
            execution_time=execution_time,
            errors=errors
        )

    def _generate_assessment(self, sentiment: Dict, shenanigans: Dict) -> str:
        """Generate textual assessment based on analysis"""
        label = sentiment.get("label", "neutral")
        high_risk = any(score > 0.7 for score in shenanigans.values())

        if high_risk:
            return f"CAUTION: {label} sentiment with potential financial manipulation indicators detected"
        elif label == "positive":
            return f"Positive sentiment indicating healthy outlook"
        elif label == "negative":
            return f"Negative sentiment suggesting concerns or challenges"
        else:
            return f"Neutral sentiment with balanced tone"


class RiskAssessmentAgent(BaseSubAgent):
    """Sub-agent for comprehensive risk assessment"""

    def process(self, content: str, context: Dict[str, Any]) -> SubAgentResult:
        """Assess various types of risks"""
        start_time = datetime.now()
        errors = []

        # Detect risks using model
        model_risks = detect_risk_fingpt(content)
        if not model_risks:
            model_risks = {}
            errors.append("Risk detection model unavailable")

        # Pattern-based risk detection
        pattern_risks = self._detect_pattern_risks(content)

        # Query knowledge graph for related risks
        kg_risks = self._query_kg_risks(context.get("chunk_id", ""))

        # Combine and prioritize risks
        all_risks = self._combine_risks(model_risks, pattern_risks, kg_risks)

        # Categorize risks
        categorized_risks = self._categorize_risks(all_risks)

        result = {
            "risk_categories": categorized_risks,
            "high_priority_risks": [r for r in all_risks if r.get("priority") == "high"],
            "total_risks_identified": len(all_risks),
            "risk_summary": self._generate_risk_summary(categorized_risks),
        }

        # Update state graph
        for risk in all_risks:
            self.state_graph.add_risk(self.section, risk)

        execution_time = (datetime.now() - start_time).total_seconds()

        return SubAgentResult(
            agent_name=self.name,
            task_id=context.get("task_id", "risk_assessment"),
            output=result,
            confidence=0.85 if not errors else 0.7,
            metadata={"chunk_id": context.get("chunk_id")},
            execution_time=execution_time,
            errors=errors
        )

    def _detect_pattern_risks(self, content: str) -> List[Dict[str, Any]]:
        """Detect risks using pattern matching"""
        risks = []

        risk_patterns = {
            "compliance": ["violation", "non-compliance", "breach", "regulatory action"],
            "financial": ["loss", "impairment", "write-off", "default", "liquidity crisis"],
            "operational": ["disruption", "failure", "outage", "incident", "breakdown"],
            "strategic": ["competition", "market share loss", "obsolescence", "disruption"],
            "reputational": ["scandal", "controversy", "investigation", "lawsuit"],
            "cyber": ["breach", "hack", "ransomware", "data theft", "cyber attack"],
        }

        for risk_type, keywords in risk_patterns.items():
            for keyword in keywords:
                if keyword.lower() in content.lower():
                    risks.append({
                        "type": risk_type,
                        "keyword": keyword,
                        "priority": "medium",
                        "source": "pattern_detection",
                    })

        return risks

    def _query_kg_risks(self, chunk_id: str) -> List[Dict[str, Any]]:
        """Query knowledge graph for risk entities"""
        risks = []
        risk_entities = self.knowledge_graph.query_entities_by_type("RISK")

        for entity in risk_entities:
            if chunk_id in entity.references:
                risks.append({
                    "type": "kg_identified",
                    "description": entity.name,
                    "priority": "medium",
                    "source": "knowledge_graph",
                    "entity_id": entity.id,
                })

        return risks

    def _combine_risks(self, model_risks: Dict, pattern_risks: List, kg_risks: List) -> List[Dict]:
        """Combine risks from different sources"""
        combined = []

        # Add model risks
        for risk_type, score in model_risks.items():
            if score > 0.3:
                combined.append({
                    "type": risk_type,
                    "score": score,
                    "priority": "high" if score > 0.7 else "medium" if score > 0.5 else "low",
                    "source": "model",
                })

        # Add pattern and KG risks
        combined.extend(pattern_risks)
        combined.extend(kg_risks)

        # Deduplicate
        seen = set()
        unique_risks = []
        for risk in combined:
            risk_key = f"{risk.get('type')}_{risk.get('source')}"
            if risk_key not in seen:
                seen.add(risk_key)
                unique_risks.append(risk)

        return unique_risks

    def _categorize_risks(self, risks: List[Dict]) -> Dict[str, List[Dict]]:
        """Categorize risks by type"""
        categories = {}
        for risk in risks:
            risk_type = risk.get("type", "other")
            if risk_type not in categories:
                categories[risk_type] = []
            categories[risk_type].append(risk)
        return categories

    def _generate_risk_summary(self, categorized_risks: Dict) -> str:
        """Generate textual risk summary"""
        total_risks = sum(len(risks) for risks in categorized_risks.values())
        high_priority = sum(
            1 for risks in categorized_risks.values()
            for r in risks if r.get("priority") == "high"
        )

        summary = f"Identified {total_risks} total risks across {len(categorized_risks)} categories. "
        if high_priority > 0:
            summary += f"{high_priority} high-priority risks require immediate attention."

        return summary


class MetricsExtractorAgent(BaseSubAgent):
    """Sub-agent for extracting KPIs and metrics"""

    def process(self, content: str, context: Dict[str, Any]) -> SubAgentResult:
        """Extract financial and operational metrics"""
        start_time = datetime.now()
        errors = []

        # Extract metrics from text
        metrics = self._extract_metrics(content)

        # Extract from knowledge graph
        kg_metrics = self._extract_kg_metrics(context.get("chunk_id", ""))

        # Combine and validate
        all_metrics = self._combine_metrics(metrics, kg_metrics)

        # Categorize metrics
        categorized = self._categorize_metrics(all_metrics)

        result = {
            "metrics": categorized,
            "key_metrics": self._identify_key_metrics(all_metrics),
            "total_metrics": len(all_metrics),
            "metric_summary": self._generate_metric_summary(categorized),
        }

        # Update state graph
        for metric in all_metrics:
            self.state_graph.add_metric(self.section, metric)

        execution_time = (datetime.now() - start_time).total_seconds()

        return SubAgentResult(
            agent_name=self.name,
            task_id=context.get("task_id", "metrics_extraction"),
            output=result,
            confidence=0.9,
            metadata={"chunk_id": context.get("chunk_id")},
            execution_time=execution_time,
            errors=errors
        )

    def _extract_metrics(self, content: str) -> List[Dict[str, Any]]:
        """Extract metrics using patterns"""
        import re

        metrics = []

        # Financial metrics patterns
        patterns = [
            (r"\$?([\d,]+\.?\d*)\s*(million|billion|M|B)?\s*(?:in\s+)?(revenue|sales)", "revenue"),
            (r"\$?([\d,]+\.?\d*)\s*(million|billion|M|B)?\s*(?:in\s+)?(profit|earnings)", "profit"),
            (r"([\d.]+)%\s*(growth|increase|decrease)", "growth_rate"),
            (r"([\d.]+)%\s*(margin)", "margin"),
            (r"([\d.]+)[x\s]*(P/E|PE)", "pe_ratio"),
        ]

        for pattern, metric_type in patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                metrics.append({
                    "type": metric_type,
                    "value": match.group(1),
                    "unit": match.group(2) if len(match.groups()) > 1 else None,
                    "context": content[max(0, match.start()-30):match.end()+30],
                })

        return metrics

    def _extract_kg_metrics(self, chunk_id: str) -> List[Dict[str, Any]]:
        """Extract metrics from knowledge graph"""
        metrics = []
        metric_entities = self.knowledge_graph.query_entities_by_type("METRIC")
        metric_entities.extend(self.knowledge_graph.query_entities_by_type("KPI"))
        metric_entities.extend(self.knowledge_graph.query_entities_by_type("FINANCIAL_METRIC"))

        for entity in metric_entities:
            if chunk_id in entity.references:
                metrics.append({
                    "type": entity.type.lower(),
                    "value": entity.properties.get("value"),
                    "name": entity.name,
                    "entity_id": entity.id,
                })

        return metrics

    def _combine_metrics(self, text_metrics: List, kg_metrics: List) -> List[Dict]:
        """Combine metrics from different sources"""
        combined = text_metrics + kg_metrics

        # Deduplicate based on value and type
        seen = set()
        unique = []
        for metric in combined:
            key = f"{metric.get('type')}_{metric.get('value')}"
            if key not in seen:
                seen.add(key)
                unique.append(metric)

        return unique

    def _categorize_metrics(self, metrics: List[Dict]) -> Dict[str, List[Dict]]:
        """Categorize metrics by type"""
        categories = {
            "financial": [],
            "operational": [],
            "growth": [],
            "efficiency": [],
            "other": [],
        }

        for metric in metrics:
            metric_type = metric.get("type", "").lower()
            if any(x in metric_type for x in ["revenue", "profit", "earnings", "cash"]):
                categories["financial"].append(metric)
            elif any(x in metric_type for x in ["growth", "increase", "decrease"]):
                categories["growth"].append(metric)
            elif any(x in metric_type for x in ["margin", "ratio", "efficiency"]):
                categories["efficiency"].append(metric)
            elif any(x in metric_type for x in ["production", "output", "volume"]):
                categories["operational"].append(metric)
            else:
                categories["other"].append(metric)

        return categories

    def _identify_key_metrics(self, metrics: List[Dict]) -> List[Dict]:
        """Identify the most important metrics"""
        # Prioritize certain metric types
        priority_types = ["revenue", "profit", "growth_rate", "margin"]
        key_metrics = [m for m in metrics if any(pt in m.get("type", "") for pt in priority_types)]
        return key_metrics[:10]  # Top 10 key metrics

    def _generate_metric_summary(self, categorized: Dict) -> str:
        """Generate summary of extracted metrics"""
        total = sum(len(metrics) for metrics in categorized.values())
        summary = f"Extracted {total} metrics: "
        summaries = []
        for category, metrics in categorized.items():
            if metrics:
                summaries.append(f"{len(metrics)} {category}")
        summary += ", ".join(summaries)
        return summary


class ExternalIntelligenceAgent(BaseSubAgent):
    """Sub-agent for gathering external intelligence"""

    def __init__(self, name: str, section: str, state_graph: StateGraph, knowledge_graph: KnowledgeGraph):
        super().__init__(name, section, state_graph, knowledge_graph)
        self.web_search = WebSearchTool()
        self.finance_data = FinanceDataTool()
        self.news_tool = NewsTool()
        self.web_crawler = WebCrawlerTool()

    def process(self, content: str, context: Dict[str, Any]) -> SubAgentResult:
        """Gather external intelligence related to content"""
        start_time = datetime.now()
        errors = []

        # Extract entities for search
        entities = self._extract_search_entities(content)

        # Search for external information
        external_data = {}

        if context.get("enable_web_search", False):
            try:
                external_data["web_results"] = self._search_web(entities)
            except Exception as e:
                errors.append(f"Web search failed: {str(e)}")

        if context.get("enable_finance_data", False):
            try:
                external_data["finance_data"] = self._get_finance_data(entities)
            except Exception as e:
                errors.append(f"Finance data failed: {str(e)}")

        if context.get("enable_news", False):
            try:
                external_data["news"] = self._get_news(entities)
            except Exception as e:
                errors.append(f"News fetch failed: {str(e)}")

        result = {
            "entities_searched": entities,
            "external_data": external_data,
            "insights": self._generate_insights(external_data),
        }

        execution_time = (datetime.now() - start_time).total_seconds()

        return SubAgentResult(
            agent_name=self.name,
            task_id=context.get("task_id", "external_intelligence"),
            output=result,
            confidence=0.7 if external_data else 0.3,
            metadata={"chunk_id": context.get("chunk_id")},
            execution_time=execution_time,
            errors=errors
        )

    def _extract_search_entities(self, content: str) -> List[str]:
        """Extract entities to search for"""
        # Simple extraction - in production, use NER
        entities = []

        # Look for company names (capitalized words)
        import re
        company_pattern = r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b"
        matches = re.findall(company_pattern, content)
        entities.extend(matches[:5])  # Top 5 potential company names

        return list(set(entities))

    def _search_web(self, entities: List[str]) -> Dict:
        """Search web for entities"""
        results = {}
        for entity in entities[:3]:  # Limit to 3 searches
            try:
                results[entity] = self.web_search.search(entity, max_results=5)
            except:
                results[entity] = []
        return results

    def _get_finance_data(self, entities: List[str]) -> Dict:
        """Get financial data for entities"""
        data = {}
        for entity in entities[:2]:  # Limit to 2 lookups
            try:
                # Assume entity is a stock symbol
                data[entity] = self.finance_data.get_financial_ratios(entity)
            except:
                data[entity] = {}
        return data

    def _get_news(self, entities: List[str]) -> Dict:
        """Get news for entities"""
        news = {}
        for entity in entities[:2]:  # Limit to 2 lookups
            try:
                news[entity] = self.news_tool.get_company_news(entity, days=7)
            except:
                news[entity] = []
        return news

    def _generate_insights(self, external_data: Dict) -> List[str]:
        """Generate insights from external data"""
        insights = []

        if "web_results" in external_data:
            total_results = sum(len(r) for r in external_data["web_results"].values())
            if total_results > 0:
                insights.append(f"Found {total_results} web references for mentioned entities")

        if "finance_data" in external_data:
            for entity, data in external_data["finance_data"].items():
                if "pe_ratio" in data and data["pe_ratio"]:
                    insights.append(f"{entity} P/E ratio: {data['pe_ratio']}")

        if "news" in external_data:
            total_news = sum(len(n) for n in external_data["news"].values())
            if total_news > 0:
                insights.append(f"Found {total_news} recent news articles")

        return insights


class GovernanceESGAgent(BaseSubAgent):
    """Sub-agent for governance and ESG analysis"""

    def process(self, content: str, context: Dict[str, Any]) -> SubAgentResult:
        """Analyze governance and ESG aspects"""
        start_time = datetime.now()

        # Extract governance elements
        governance = self._extract_governance(content)

        # Extract ESG elements
        esg = self._extract_esg(content)

        # Extract SDG references
        sdg = self._extract_sdg(content)

        result = {
            "governance": governance,
            "esg": esg,
            "sdg": sdg,
            "compliance_score": self._calculate_compliance_score(governance, esg),
            "sustainability_score": self._calculate_sustainability_score(esg, sdg),
        }

        # Update state graph
        self.state_graph.add_section_finding(self.section, "governance_esg", result)

        execution_time = (datetime.now() - start_time).total_seconds()

        return SubAgentResult(
            agent_name=self.name,
            task_id=context.get("task_id", "governance_esg"),
            output=result,
            confidence=0.85,
            metadata={"chunk_id": context.get("chunk_id")},
            execution_time=execution_time,
        )

    def _extract_governance(self, content: str) -> Dict[str, Any]:
        """Extract governance-related information"""
        governance = {
            "board_members": [],
            "committees": [],
            "policies": [],
            "independence_indicators": [],
        }

        # Pattern matching for governance elements
        import re

        # Board members
        board_pattern = r"(?:board member|director|chairman|chairwoman|chairperson)[\s:]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)"
        matches = re.finditer(board_pattern, content, re.IGNORECASE)
        governance["board_members"] = [m.group(1) for m in matches]

        # Committees
        committee_pattern = r"(audit|compensation|nominating|governance|risk|ethics)\s+committee"
        matches = re.finditer(committee_pattern, content, re.IGNORECASE)
        governance["committees"] = [m.group(0) for m in matches]

        # Independence
        if "independent director" in content.lower():
            governance["independence_indicators"].append("Independent directors mentioned")

        return governance

    def _extract_esg(self, content: str) -> Dict[str, Any]:
        """Extract ESG-related information"""
        esg = {
            "environmental": [],
            "social": [],
            "governance": [],
        }

        # Environmental keywords
        env_keywords = ["carbon", "emissions", "renewable", "sustainability", "climate", "energy"]
        for keyword in env_keywords:
            if keyword in content.lower():
                esg["environmental"].append(keyword)

        # Social keywords
        social_keywords = ["diversity", "inclusion", "community", "safety", "human rights"]
        for keyword in social_keywords:
            if keyword in content.lower():
                esg["social"].append(keyword)

        # Governance keywords
        gov_keywords = ["ethics", "transparency", "accountability", "compliance", "integrity"]
        for keyword in gov_keywords:
            if keyword in content.lower():
                esg["governance"].append(keyword)

        return esg

    def _extract_sdg(self, content: str) -> List[str]:
        """Extract SDG references"""
        import re

        sdg_goals = []
        sdg_pattern = r"SDG[\s-]?(\d{1,2})|Sustainable Development Goal[\s-]?(\d{1,2})"
        matches = re.finditer(sdg_pattern, content, re.IGNORECASE)

        for match in matches:
            goal_num = match.group(1) or match.group(2)
            if goal_num and 1 <= int(goal_num) <= 17:
                sdg_goals.append(f"SDG {goal_num}")

        return list(set(sdg_goals))

    def _calculate_compliance_score(self, governance: Dict, esg: Dict) -> float:
        """Calculate compliance score based on governance and ESG"""
        score = 0.5  # Base score

        if governance["board_members"]:
            score += 0.1
        if governance["committees"]:
            score += 0.1 * min(len(governance["committees"]), 3)
        if governance["independence_indicators"]:
            score += 0.1
        if esg["governance"]:
            score += 0.1

        return min(score, 1.0)

    def _calculate_sustainability_score(self, esg: Dict, sdg: List[str]) -> float:
        """Calculate sustainability score"""
        score = 0.3  # Base score

        if esg["environmental"]:
            score += 0.2
        if esg["social"]:
            score += 0.2
        if sdg:
            score += 0.1 * min(len(sdg), 3)

        return min(score, 1.0)


class MemoryCoordinatorAgent(BaseSubAgent):
    """Sub-agent for coordinating memory and cross-section insights"""

    def __init__(self, name: str, section: str, state_graph: StateGraph, knowledge_graph: KnowledgeGraph):
        super().__init__(name, section, state_graph, knowledge_graph)
        self.long_term_memory = LongTermMemory()

    def process(self, content: str, context: Dict[str, Any]) -> SubAgentResult:
        """Coordinate memory and cross-section insights"""
        start_time = datetime.now()

        # Retrieve relevant memories
        memories = self._retrieve_memories(context)

        # Find cross-section references
        cross_refs = self._find_cross_references(content, context)

        # Generate collaborative insights
        insights = self._generate_collaborative_insights(memories, cross_refs)

        # Update memories
        self._update_memories(content, context, insights)

        result = {
            "relevant_memories": memories,
            "cross_references": cross_refs,
            "collaborative_insights": insights,
            "memory_summary": self._generate_memory_summary(memories, cross_refs),
        }

        # Update state graph
        for insight in insights:
            self.state_graph.add_collaborative_insight(insight)

        for source, targets in cross_refs.items():
            for target in targets:
                self.state_graph.add_cross_reference(source, target)

        execution_time = (datetime.now() - start_time).total_seconds()

        return SubAgentResult(
            agent_name=self.name,
            task_id=context.get("task_id", "memory_coordination"),
            output=result,
            confidence=0.9,
            metadata={"chunk_id": context.get("chunk_id")},
            execution_time=execution_time,
        )

    def _retrieve_memories(self, context: Dict[str, Any]) -> List[Dict]:
        """Retrieve relevant memories from long-term memory"""
        memories = []

        # Get memories for current section
        section_memories = self.long_term_memory.query_all(
            agent_name=self.section,
            section=context.get("section_name")
        )

        # Get last 10 relevant memories
        for memory in section_memories[-10:]:
            memories.append({
                "key": memory.get("key"),
                "summary": memory.get("value", {}).get("summary", "")[:200],
                "sentiment": memory.get("value", {}).get("sentiment"),
            })

        return memories

    def _find_cross_references(self, content: str, context: Dict[str, Any]) -> Dict[str, List[str]]:
        """Find references to other sections"""
        cross_refs = {}

        section_keywords = {
            "letter_to_shareholders": ["letter", "shareholders", "CEO message"],
            "mdna": ["MD&A", "management discussion", "analysis"],
            "financial_statements": ["financial statements", "balance sheet", "income statement"],
            "audit_report": ["audit", "auditor", "opinion"],
            "corporate_governance": ["governance", "board", "directors"],
            "esg": ["ESG", "sustainability", "environmental"],
            "sdg_17": ["SDG", "sustainable development", "partnership"],
        }

        current_section = context.get("section", "")

        for section, keywords in section_keywords.items():
            if section != current_section:
                for keyword in keywords:
                    if keyword.lower() in content.lower():
                        if current_section not in cross_refs:
                            cross_refs[current_section] = []
                        if section not in cross_refs[current_section]:
                            cross_refs[current_section].append(section)

        return cross_refs

    def _generate_collaborative_insights(self, memories: List[Dict], cross_refs: Dict) -> List[Dict]:
        """Generate insights from memories and cross-references"""
        insights = []

        # Insight from memory patterns
        if len(memories) > 5:
            sentiments = [m.get("sentiment", {}).get("label") for m in memories if m.get("sentiment")]
            if sentiments:
                most_common = max(set(sentiments),
