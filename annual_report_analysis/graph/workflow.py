"""
LangGraph-style workflow for Annual Report Analysis
Orchestrates document processing with task decomposition, sub-agents, and knowledge graph
"""

from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
import asyncio
from pathlib import Path
import json

from ..core.state import SectionName
from ..core.config import AppConfig
from ..graph.state_graph import StateGraph, NodeStatus, NodeResult
from ..tools.document_processing import parse_pdf_to_structured_format
from ..tools.knowledge_graph import KnowledgeGraph, extract_and_add_to_graph
from ..tools.tools import load_parsed_document_chunks, guess_section
from ..agents.task_decomposition import TaskDecomposer, TaskType
from ..agents.sub_agents import (
    SentimentAnalysisAgent,
    RiskAssessmentAgent,
    MetricsExtractorAgent,
    ExternalIntelligenceAgent,
    GovernanceESGAgent,
    MemoryCoordinatorAgent,
)
from ..agents.memory import LongTermMemory
from ..agents.collaborative_memory import CollaborativeMemory


class SectionAgent:
    """Section agent that orchestrates multiple sub-agents"""

    def __init__(
        self,
        section_name: SectionName,
        state_graph: StateGraph,
        knowledge_graph: KnowledgeGraph,
        long_term_memory: LongTermMemory,
        collaborative_memory: CollaborativeMemory,
    ):
        self.section_name = section_name
        self.state_graph = state_graph
        self.knowledge_graph = knowledge_graph
        self.long_term_memory = long_term_memory
        self.collaborative_memory = collaborative_memory

        # Initialize sub-agents
        self.sub_agents = {
            "sentiment": SentimentAnalysisAgent(
                f"{section_name.value}_sentiment",
                section_name.value,
                state_graph,
                knowledge_graph,
            ),
            "risk": RiskAssessmentAgent(
                f"{section_name.value}_risk",
                section_name.value,
                state_graph,
                knowledge_graph,
            ),
            "metrics": MetricsExtractorAgent(
                f"{section_name.value}_metrics",
                section_name.value,
                state_graph,
                knowledge_graph,
            ),
            "external": ExternalIntelligenceAgent(
                f"{section_name.value}_external",
                section_name.value,
                state_graph,
                knowledge_graph,
            ),
            "governance_esg": GovernanceESGAgent(
                f"{section_name.value}_governance_esg",
                section_name.value,
                state_graph,
                knowledge_graph,
            ),
            "memory": MemoryCoordinatorAgent(
                f"{section_name.value}_memory",
                section_name.value,
                state_graph,
                knowledge_graph,
            ),
        }

    async def process_tasks(
        self, tasks: List[Dict[str, Any]], chunk: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process multiple tasks using sub-agents"""
        results = {}
        context = {
            "chunk_id": chunk.get("chunk_id"),
            "section": self.section_name.value,
            "section_name": self.section_name,
        }

        # Map task types to sub-agents
        task_agent_mapping = {
            TaskType.FINANCIAL_ANALYSIS: ["metrics", "sentiment"],
            TaskType.RISK_ASSESSMENT: ["risk", "sentiment"],
            TaskType.PERFORMANCE_METRICS: ["metrics"],
            TaskType.GOVERNANCE_REVIEW: ["governance_esg"],
            TaskType.SUSTAINABILITY_ANALYSIS: ["governance_esg"],
            TaskType.MARKET_ANALYSIS: ["external", "metrics"],
            TaskType.STRATEGY_REVIEW: ["sentiment", "memory"],
            TaskType.COMPLIANCE_CHECK: ["governance_esg", "risk"],
        }

        # Process each task with appropriate sub-agents
        for task in tasks:
            task_type = task.get("task_type")
            task_id = task.get("id")
            context["task_id"] = task_id

            # Get relevant sub-agents for this task
            agent_names = task_agent_mapping.get(task_type, ["sentiment"])

            # Run sub-agents in parallel
            sub_results = await asyncio.gather(
                *[
                    self._run_sub_agent(agent_name, chunk["content"], context)
                    for agent_name in agent_names
                    if agent_name in self.sub_agents
                ]
            )

            # Combine results
            task_result = {
                "task_id": task_id,
                "task_type": task_type.value
                if hasattr(task_type, "value")
                else str(task_type),
                "sub_agent_results": sub_results,
                "timestamp": datetime.now().isoformat(),
            }

            results[task_id] = task_result

            # Mark task as completed in state graph
            self.state_graph.complete_task(task_id, task_result)

        # Always run memory coordinator to maintain cross-section awareness
        memory_result = await self._run_sub_agent("memory", chunk["content"], context)
        results["memory_coordination"] = memory_result

        return results

    async def _run_sub_agent(
        self, agent_name: str, content: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run a single sub-agent"""
        try:
            agent = self.sub_agents[agent_name]
            result = agent.process(content, context)
            return {
                "agent": agent_name,
                "success": True,
                "result": result.output if hasattr(result, "output") else result,
                "confidence": result.confidence
                if hasattr(result, "confidence")
                else 1.0,
                "errors": result.errors if hasattr(result, "errors") else [],
            }
        except Exception as e:
            return {
                "agent": agent_name,
                "success": False,
                "error": str(e),
                "result": {},
            }


class FinalGeneratorAgent:
    """Final agent that generates the complete analysis report"""

    def __init__(self, state_graph: StateGraph, knowledge_graph: KnowledgeGraph):
        self.state_graph = state_graph
        self.knowledge_graph = knowledge_graph

    def generate_report(self) -> Dict[str, Any]:
        """Generate the final comprehensive report"""
        report = {
            "executive_summary": self._generate_executive_summary(),
            "section_analyses": self._compile_section_analyses(),
            "key_metrics": self._compile_key_metrics(),
            "risk_assessment": self._compile_risk_assessment(),
            "opportunities": self._compile_opportunities(),
            "financial_health": self._assess_financial_health(),
            "governance_esg_summary": self._compile_governance_esg(),
            "knowledge_graph_insights": self._generate_kg_insights(),
            "cross_section_insights": self._compile_cross_section_insights(),
            "recommendations": self._generate_recommendations(),
            "appendices": self._generate_appendices(),
        }

        # Update state graph with final report
        self.state_graph.global_report = json.dumps(report, indent=2)
        self.state_graph.executive_summary = report["executive_summary"]
        self.state_graph.recommendations = report["recommendations"]

        return report

    def _generate_executive_summary(self) -> str:
        """Generate executive summary"""
        summary_parts = []

        # Company overview from knowledge graph
        company_entities = self.knowledge_graph.query_entities_by_type("COMPANY")
        if company_entities:
            summary_parts.append(
                f"Analysis of {company_entities[0].name} Annual Report"
            )

        # Key findings
        total_risks = sum(
            len(risks) for risks in self.state_graph.section_risks.values()
        )
        total_opportunities = sum(
            len(opps) for opps in self.state_graph.section_opportunities.values()
        )

        summary_parts.append(f"\nKey Findings:")
        summary_parts.append(f"- Identified {total_risks} risks across all sections")
        summary_parts.append(f"- Found {total_opportunities} opportunities for growth")

        # Sentiment overview
        sentiments = []
        for findings in self.state_graph.section_findings.values():
            if "sentiment_analysis" in findings:
                for analysis in findings["sentiment_analysis"]:
                    if isinstance(analysis, dict) and "sentiment" in analysis:
                        sentiments.append(analysis["sentiment"].get("label", "neutral"))

        if sentiments:
            most_common_sentiment = max(set(sentiments), key=sentiments.count)
            summary_parts.append(f"- Overall sentiment: {most_common_sentiment}")

        # Financial highlights
        financial_metrics = self.state_graph.section_metrics.get(
            "financial_statements", []
        )
        if financial_metrics:
            summary_parts.append(f"\nFinancial Highlights:")
            for metric in financial_metrics[:5]:  # Top 5 metrics
                if "type" in metric and "value" in metric:
                    summary_parts.append(f"- {metric['type']}: {metric['value']}")

        return "\n".join(summary_parts)

    def _compile_section_analyses(self) -> Dict[str, str]:
        """Compile analyses from all sections"""
        analyses = {}
        for section, summary in self.state_graph.section_summaries.items():
            analyses[section] = {
                "summary": summary,
                "findings": self.state_graph.section_findings.get(section, {}),
                "metrics": self.state_graph.section_metrics.get(section, []),
                "risks": self.state_graph.section_risks.get(section, []),
                "opportunities": self.state_graph.section_opportunities.get(
                    section, []
                ),
            }
        return analyses

    def _compile_key_metrics(self) -> List[Dict[str, Any]]:
        """Compile all key metrics"""
        all_metrics = []
        for section_metrics in self.state_graph.section_metrics.values():
            all_metrics.extend(section_metrics)

        # Prioritize and deduplicate
        seen = set()
        unique_metrics = []
        for metric in all_metrics:
            metric_key = f"{metric.get('type')}_{metric.get('value')}"
            if metric_key not in seen:
                seen.add(metric_key)
                unique_metrics.append(metric)

        return unique_metrics[:20]  # Top 20 metrics

    def _compile_risk_assessment(self) -> Dict[str, Any]:
        """Compile comprehensive risk assessment"""
        all_risks = []
        for section, risks in self.state_graph.section_risks.items():
            for risk in risks:
                risk["section"] = section
                all_risks.append(risk)

        # Categorize by priority
        high_priority = [r for r in all_risks if r.get("priority") == "high"]
        medium_priority = [r for r in all_risks if r.get("priority") == "medium"]
        low_priority = [r for r in all_risks if r.get("priority") == "low"]

        return {
            "total_risks": len(all_risks),
            "high_priority": high_priority,
            "medium_priority": medium_priority,
            "low_priority": low_priority,
            "risk_summary": f"Identified {len(all_risks)} total risks: {len(high_priority)} high, {len(medium_priority)} medium, {len(low_priority)} low priority",
        }

    def _compile_opportunities(self) -> List[Dict[str, Any]]:
        """Compile all opportunities"""
        all_opportunities = []
        for section, opportunities in self.state_graph.section_opportunities.values():
            for opp in opportunities:
                opp["section"] = section
                all_opportunities.append(opp)
        return all_opportunities

    def _assess_financial_health(self) -> Dict[str, Any]:
        """Assess overall financial health"""
        assessment = {
            "status": "Unknown",
            "indicators": [],
            "concerns": [],
            "strengths": [],
        }

        # Analyze financial metrics
        financial_metrics = self.state_graph.section_metrics.get(
            "financial_statements", []
        )

        for metric in financial_metrics:
            metric_type = metric.get("type", "").lower()
            value = metric.get("value", "")

            if "growth" in metric_type and "increase" in str(value):
                assessment["strengths"].append(f"Positive growth in {metric_type}")
            elif "loss" in metric_type or "decrease" in str(value):
                assessment["concerns"].append(f"Negative trend in {metric_type}")

        # Determine overall status
        if len(assessment["strengths"]) > len(assessment["concerns"]):
            assessment["status"] = "Healthy"
        elif len(assessment["concerns"]) > len(assessment["strengths"]):
            assessment["status"] = "Concerning"
        else:
            assessment["status"] = "Stable"

        return assessment

    def _compile_governance_esg(self) -> Dict[str, Any]:
        """Compile governance and ESG summary"""
        governance_esg = {
            "governance": {},
            "esg": {},
            "sdg": [],
        }

        # Extract from findings
        for section, findings in self.state_graph.section_findings.items():
            if "governance_esg" in findings:
                for analysis in findings["governance_esg"]:
                    if isinstance(analysis, dict):
                        if "governance" in analysis:
                            governance_esg["governance"].update(analysis["governance"])
                        if "esg" in analysis:
                            governance_esg["esg"].update(analysis["esg"])
                        if "sdg" in analysis:
                            governance_esg["sdg"].extend(analysis["sdg"])

        # Deduplicate SDG goals
        governance_esg["sdg"] = list(set(governance_esg["sdg"]))

        return governance_esg

    def _generate_kg_insights(self) -> Dict[str, Any]:
        """Generate insights from knowledge graph"""
        kg_stats = self.knowledge_graph.get_summary_stats()

        # Find most central entities
        centrality = self.knowledge_graph.compute_centrality("degree")
        top_entities = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:5]

        insights = {
            "statistics": kg_stats,
            "key_entities": [
                {
                    "id": entity_id,
                    "centrality": score,
                    "entity": self.knowledge_graph.entities.get(entity_id, {}),
                }
                for entity_id, score in top_entities
            ],
            "total_entities": kg_stats.get("total_entities", 0),
            "total_relationships": kg_stats.get("total_relationships", 0),
        }

        return insights

    def _compile_cross_section_insights(self) -> List[Dict[str, Any]]:
        """Compile cross-section collaborative insights"""
        return self.state_graph.collaborative_insights

    def _generate_recommendations(self) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []

        # Based on risks
        high_risks = [
            r
            for risks in self.state_graph.section_risks.values()
            for r in risks
            if r.get("priority") == "high"
        ]

        if high_risks:
            recommendations.append(
                f"Address {len(high_risks)} high-priority risks immediately"
            )

        # Based on financial health
        financial_assessment = self._assess_financial_health()
        if financial_assessment["status"] == "Concerning":
            recommendations.append("Review financial strategy and cost structure")

        # Based on governance
        governance_data = self._compile_governance_esg()
        if not governance_data.get("governance"):
            recommendations.append("Enhance governance disclosure and transparency")

        # Based on ESG
        if governance_data.get("sdg"):
            recommendations.append(
                f"Continue focus on {len(governance_data['sdg'])} SDG goals"
            )
        else:
            recommendations.append(
                "Consider adopting SDG framework for sustainability reporting"
            )

        return recommendations

    def _generate_appendices(self) -> Dict[str, Any]:
        """Generate appendices with detailed data"""
        return {
            "detailed_metrics": {
                section: metrics
                for section, metrics in self.state_graph.section_metrics.items()
            },
            "knowledge_graph_entities": self.state_graph.kg_entities,
            "knowledge_graph_relationships": self.state_graph.kg_relationships,
            "processing_metadata": self.state_graph.get_summary(),
        }


class LangGraphWorkflow:
    """Main workflow orchestrator using LangGraph-style approach"""

    def __init__(self, config: Optional[AppConfig] = None):
        self.config = config or AppConfig()
        self.state_graph = StateGraph()
        self.knowledge_graph = KnowledgeGraph()
        self.long_term_memory = LongTermMemory()
        self.collaborative_memory = CollaborativeMemory()
        self.task_decomposer = TaskDecomposer()

        # Initialize section agents
        self.section_agents = {}
        for section in SectionName:
            self.section_agents[section] = SectionAgent(
                section,
                self.state_graph,
                self.knowledge_graph,
                self.long_term_memory,
                self.collaborative_memory,
            )

        # Initialize final generator
        self.final_generator = FinalGeneratorAgent(
            self.state_graph, self.knowledge_graph
        )

    async def process_document(
        self, document_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        """Process entire document through the workflow"""

        # Step 1: Parse document if PDF, or load existing chunks
        if document_path and document_path.suffix.lower() == ".pdf":
            print(f"Parsing PDF: {document_path}")
            parse_pdf_to_structured_format(
                str(document_path), str(self.config.output_dir)
            )

        # Step 2: Load and chunk document
        print("Loading document chunks...")
        chunks = load_parsed_document_chunks(
            self.config.output_dir, self.config.max_chunk_chars
        )

        for chunk in chunks:
            self.state_graph.add_chunk(
                {
                    "chunk_id": chunk.chunk_id,
                    "content": chunk.content,
                    "section_hint": chunk.section_hint,
                    "metadata": chunk.meta,
                }
            )

        print(f"Loaded {len(chunks)} chunks")

        # Step 3: Process each chunk
        for i, chunk in enumerate(chunks):
            print(f"Processing chunk {i + 1}/{len(chunks)}")

            # Extract entities and relationships for knowledge graph
            kg_result = extract_and_add_to_graph(
                self.knowledge_graph, chunk.content, chunk.chunk_id
            )

            # Track in state graph
            if kg_result["entities_extracted"] > 0:
                entity_ids = [
                    e.id
                    for e in self.knowledge_graph.query_entities_by_chunk(
                        chunk.chunk_id
                    )
                ]
                self.state_graph.add_kg_entities(chunk.chunk_id, entity_ids)

            if kg_result["relationships_extracted"] > 0:
                # Note: Would need to add relationship query method to KG
                self.state_graph.add_kg_relationships(chunk.chunk_id, [])

            # Decompose chunk into tasks
            tasks = self.task_decomposer.decompose_content(chunk.content)

            # Add tasks to state graph
            for task in tasks:
                task_dict = {
                    "task_type": task.task_type,
                    "content": task.content,
                    "priority": task.priority,
                    "dependencies": task.dependencies,
                    "metadata": task.metadata,
                    "target_agents": task.target_agents,
                }
                self.state_graph.add_task(task_dict)

            # Route chunk to appropriate section
            section = (
                chunk.section_hint or guess_section(chunk.content) or SectionName.other
            )

            # Process tasks with section agent
            section_agent = self.section_agents[section]
            chunk_data = {
                "chunk_id": chunk.chunk_id,
                "content": chunk.content,
                "section_hint": section,
                "metadata": chunk.meta,
            }

            # Process tasks (convert async to sync for compatibility)
            loop = asyncio.get_event_loop()
            results = loop.run_until_complete(
                section_agent.process_tasks(tasks, chunk_data)
            )

            # Update chunk as processed
            self.state_graph.mark_chunk_processed(i)

            # Save checkpoint periodically
            if (i + 1) % 10 == 0:
                checkpoint_path = self.config.output_dir / f"checkpoint_{i + 1}.json"
                self.state_graph.save_checkpoint(checkpoint_path)

        # Step 4: Update knowledge graph summary
        self.state_graph.update_kg_summary(self.knowledge_graph.get_summary_stats())

        # Step 5: Generate final report
        print("Generating final report...")
        final_report = self.final_generator.generate_report()

        # Step 6: Save outputs
        output_path = self.config.output_dir / "analysis_summary.json"
        with open(output_path, "w") as f:
            json.dump(final_report, f, indent=2)

        # Save knowledge graph
        self.knowledge_graph.save()

        # Save final state
        final_checkpoint = self.config.output_dir / "final_state.json"
        self.state_graph.save_checkpoint(final_checkpoint)

        print(f"Analysis complete. Results saved to {output_path}")

        return final_report


def run_workflow(
    document_path: Optional[Path] = None, config: Optional[AppConfig] = None
) -> Dict[str, Any]:
    """Main entry point for the workflow"""
    workflow = LangGraphWorkflow(config)

    # Run async workflow in sync context
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        result = loop.run_until_complete(workflow.process_document(document_path))
        return result
    finally:
        loop.close()
