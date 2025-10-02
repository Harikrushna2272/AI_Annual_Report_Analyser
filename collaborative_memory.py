from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class SharedInsight:
    agent_name: str
    section_name: str
    timestamp: datetime
    insight_type: str
    content: Any
    confidence: float
    related_sections: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)

class CollaborativeMemory:
    def __init__(self):
        self.shared_insights: List[SharedInsight] = []
        self.agent_subscriptions: Dict[str, List[str]] = {}
        self.cross_references: Dict[str, List[str]] = {}
        
    def share_insight(self, insight: SharedInsight) -> None:
        """Share a new insight with other agents"""
        self.shared_insights.append(insight)
        # Notify subscribed agents
        self._notify_subscribers(insight)
    
    def subscribe_to_agent(self, subscriber: str, publisher: str) -> None:
        """Subscribe an agent to another agent's insights"""
        if subscriber not in self.agent_subscriptions:
            self.agent_subscriptions[subscriber] = []
        if publisher not in self.agent_subscriptions[subscriber]:
            self.agent_subscriptions[subscriber].append(publisher)
    
    def get_agent_insights(self, agent_name: str, since: Optional[datetime] = None) -> List[SharedInsight]:
        """Get insights shared by a specific agent"""
        insights = [i for i in self.shared_insights if i.agent_name == agent_name]
        if since:
            insights = [i for i in insights if i.timestamp > since]
        return insights
    
    def get_section_insights(self, section_name: str) -> List[SharedInsight]:
        """Get all insights related to a specific section"""
        return [i for i in self.shared_insights if i.section_name == section_name or section_name in i.related_sections]
    
    def add_cross_reference(self, section1: str, section2: str) -> None:
        """Add a cross-reference between two sections"""
        if section1 not in self.cross_references:
            self.cross_references[section1] = []
        if section2 not in self.cross_references[section2]:
            self.cross_references[section2] = []
        
        if section2 not in self.cross_references[section1]:
            self.cross_references[section1].append(section2)
        if section1 not in self.cross_references[section2]:
            self.cross_references[section2].append(section1)
    
    def get_related_sections(self, section_name: str) -> List[str]:
        """Get all sections related to a given section"""
        return self.cross_references.get(section_name, [])
    
    def _notify_subscribers(self, insight: SharedInsight) -> None:
        """Notify all subscribed agents of new insights"""
        for subscriber, publishers in self.agent_subscriptions.items():
            if insight.agent_name in publishers:
                # In a real implementation, this would trigger a notification
                # to the subscribed agent
                pass

    def get_collaborative_insights(self, section_name: str) -> Dict[str, List[Any]]:
        """Get insights from all related sections for collaborative analysis"""
        related_sections = self.get_related_sections(section_name)
        all_insights = {}
        
        # Get direct insights
        all_insights[section_name] = self.get_section_insights(section_name)
        
        # Get related insights
        for related_section in related_sections:
            all_insights[related_section] = self.get_section_insights(related_section)
            
        return all_insights
