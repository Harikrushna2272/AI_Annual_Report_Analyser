"""
Knowledge Graph Tool for Annual Report Analysis
Handles entity extraction, relationship mapping, and graph-based queries
"""

from typing import Dict, List, Tuple, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
import json
import re
from pathlib import Path
import networkx as nx
from collections import defaultdict


@dataclass
class Entity:
    """Represents an entity in the knowledge graph"""

    id: str
    type: str  # COMPANY, PERSON, METRIC, RISK, TARGET, INITIATIVE, etc.
    name: str
    properties: Dict[str, Any] = field(default_factory=dict)
    references: List[str] = field(default_factory=list)  # chunk_ids

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return isinstance(other, Entity) and self.id == other.id


@dataclass
class Relationship:
    """Represents a relationship between entities"""

    id: str
    source_id: str
    target_id: str
    type: str  # HAS_METRIC, FACES_RISK, LED_BY, PARTNERS_WITH, etc.
    properties: Dict[str, Any] = field(default_factory=dict)
    references: List[str] = field(default_factory=list)  # chunk_ids
    confidence: float = 1.0

    def __hash__(self):
        return hash(self.id)


class KnowledgeGraph:
    """
    Main knowledge graph implementation using NetworkX
    """

    def __init__(self, storage_path: Optional[Path] = None):
        self.graph = nx.MultiDiGraph()
        self.entities: Dict[str, Entity] = {}
        self.relationships: Dict[str, Relationship] = {}
        self.entity_index: Dict[str, Set[str]] = defaultdict(set)  # type -> entity_ids
        self.chunk_index: Dict[str, Set[str]] = defaultdict(
            set
        )  # chunk_id -> entity_ids
        self.storage_path = storage_path or Path(
            "./annual_report_analysis/knowledge_store"
        )
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Predefined entity types
        self.entity_types = {
            "COMPANY",
            "SUBSIDIARY",
            "PERSON",
            "BOARD_MEMBER",
            "EXECUTIVE",
            "METRIC",
            "KPI",
            "FINANCIAL_METRIC",
            "RISK",
            "OPPORTUNITY",
            "TARGET",
            "INITIATIVE",
            "PRODUCT",
            "SERVICE",
            "MARKET",
            "REGULATION",
            "STANDARD",
            "SDG_GOAL",
            "ESG_METRIC",
        }

        # Predefined relationship types
        self.relationship_types = {
            "HAS_METRIC",
            "REPORTS",
            "FACES_RISK",
            "HAS_OPPORTUNITY",
            "LED_BY",
            "BOARD_MEMBER_OF",
            "SUBSIDIARY_OF",
            "PARTNERS_WITH",
            "OPERATES_IN",
            "COMPLIES_WITH",
            "TARGETS",
            "ACHIEVED",
            "INCREASED_BY",
            "DECREASED_BY",
            "COMPARED_TO",
            "DEPENDS_ON",
        }

    def add_entity(self, entity: Entity) -> str:
        """Add an entity to the graph"""
        self.entities[entity.id] = entity
        self.entity_index[entity.type].add(entity.id)

        # Add to NetworkX graph
        self.graph.add_node(
            entity.id, type=entity.type, name=entity.name, properties=entity.properties
        )

        # Update chunk index
        for chunk_id in entity.references:
            self.chunk_index[chunk_id].add(entity.id)

        return entity.id

    def add_relationship(self, relationship: Relationship) -> str:
        """Add a relationship to the graph"""
        self.relationships[relationship.id] = relationship

        # Add edge to NetworkX graph
        self.graph.add_edge(
            relationship.source_id,
            relationship.target_id,
            key=relationship.id,
            type=relationship.type,
            properties=relationship.properties,
            confidence=relationship.confidence,
        )

        return relationship.id

    def extract_entities_from_text(self, text: str, chunk_id: str) -> List[Entity]:
        """Extract entities from text using patterns and NER"""
        entities = []

        # Extract financial metrics
        metric_patterns = [
            (r"\$[\d,]+\.?\d*\s*(million|billion|M|B)?", "FINANCIAL_METRIC"),
            (r"\d+\.?\d*%\s*(growth|increase|decrease|margin)?", "METRIC"),
            (r"(revenue|profit|EBITDA|cash flow|debt|assets|liabilities)", "KPI"),
        ]

        for pattern, entity_type in metric_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                entity_text = match.group(0)
                entity = Entity(
                    id=f"{entity_type}_{hash(entity_text)}",
                    type=entity_type,
                    name=entity_text,
                    properties={
                        "value": entity_text,
                        "context": text[max(0, match.start() - 50) : match.end() + 50],
                    },
                    references=[chunk_id],
                )
                entities.append(entity)

        # Extract risks and opportunities
        risk_keywords = ["risk", "threat", "challenge", "uncertainty", "exposure"]
        opportunity_keywords = [
            "opportunity",
            "potential",
            "growth",
            "expansion",
            "innovation",
        ]

        sentences = text.split(".")
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(keyword in sentence_lower for keyword in risk_keywords):
                entity = Entity(
                    id=f"RISK_{hash(sentence)}",
                    type="RISK",
                    name=sentence.strip()[:100],  # First 100 chars as name
                    properties={"full_text": sentence.strip()},
                    references=[chunk_id],
                )
                entities.append(entity)

            if any(keyword in sentence_lower for keyword in opportunity_keywords):
                entity = Entity(
                    id=f"OPPORTUNITY_{hash(sentence)}",
                    type="OPPORTUNITY",
                    name=sentence.strip()[:100],
                    properties={"full_text": sentence.strip()},
                    references=[chunk_id],
                )
                entities.append(entity)

        # Extract persons (board members, executives)
        person_patterns = [
            r"(?:Mr\.|Ms\.|Dr\.|Mrs\.)\s+[A-Z][a-z]+\s+[A-Z][a-z]+",
            r"[A-Z][a-z]+\s+[A-Z][a-z]+,?\s+(?:CEO|CFO|CTO|COO|President|Director|Chairman)",
        ]

        for pattern in person_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                person_name = match.group(0).strip().strip(",")
                entity = Entity(
                    id=f"PERSON_{hash(person_name)}",
                    type="PERSON",
                    name=person_name,
                    properties={
                        "role": "Executive"
                        if any(
                            x in person_name
                            for x in ["CEO", "CFO", "CTO", "COO", "President"]
                        )
                        else "Board Member"
                    },
                    references=[chunk_id],
                )
                entities.append(entity)

        # Extract SDG goals
        sdg_pattern = r"SDG\s*\d+|Sustainable Development Goal\s*\d+"
        matches = re.finditer(sdg_pattern, text, re.IGNORECASE)
        for match in matches:
            sdg_text = match.group(0)
            entity = Entity(
                id=f"SDG_{hash(sdg_text)}",
                type="SDG_GOAL",
                name=sdg_text,
                properties={
                    "context": text[max(0, match.start() - 100) : match.end() + 100]
                },
                references=[chunk_id],
            )
            entities.append(entity)

        return entities

    def extract_relationships_from_text(
        self, text: str, entities: List[Entity], chunk_id: str
    ) -> List[Relationship]:
        """Extract relationships between entities from text"""
        relationships = []

        # Create entity lookup for quick access
        entity_positions = {}
        for entity in entities:
            # Find entity position in text
            if entity.name in text:
                pos = text.find(entity.name)
                entity_positions[entity.id] = pos

        # Detect relationships based on proximity and patterns
        relationship_patterns = [
            (r"(\w+)\s+increased\s+by\s+([\d.]+%)", "INCREASED_BY"),
            (r"(\w+)\s+decreased\s+by\s+([\d.]+%)", "DECREASED_BY"),
            (r"(\w+)\s+led\s+by\s+(\w+)", "LED_BY"),
            (r"(\w+)\s+faces?\s+(\w+\s+risk)", "FACES_RISK"),
            (r"(\w+)\s+achieved?\s+(\w+)", "ACHIEVED"),
            (r"(\w+)\s+targets?\s+(\w+)", "TARGETS"),
        ]

        for pattern, rel_type in relationship_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                # Try to match extracted entities
                for e1 in entities:
                    for e2 in entities:
                        if e1.id != e2.id:
                            if match.group(1) in e1.name and match.group(2) in e2.name:
                                rel = Relationship(
                                    id=f"REL_{hash(f'{e1.id}_{rel_type}_{e2.id}')}",
                                    source_id=e1.id,
                                    target_id=e2.id,
                                    type=rel_type,
                                    properties={"extracted_from": match.group(0)},
                                    references=[chunk_id],
                                    confidence=0.8,
                                )
                                relationships.append(rel)

        # Proximity-based relationships (entities close to each other likely related)
        for i, e1 in enumerate(entities):
            for j, e2 in enumerate(entities[i + 1 :], i + 1):
                if e1.id in entity_positions and e2.id in entity_positions:
                    distance = abs(entity_positions[e1.id] - entity_positions[e2.id])
                    if distance < 100:  # Within 100 characters
                        # Infer relationship type based on entity types
                        if e1.type == "PERSON" and e2.type == "COMPANY":
                            rel_type = (
                                "LEADS"
                                if "CEO" in e1.properties.get("role", "")
                                else "BOARD_MEMBER_OF"
                            )
                        elif e1.type == "COMPANY" and e2.type == "METRIC":
                            rel_type = "HAS_METRIC"
                        elif e1.type == "COMPANY" and e2.type == "RISK":
                            rel_type = "FACES_RISK"
                        else:
                            rel_type = "RELATED_TO"

                        rel = Relationship(
                            id=f"REL_{hash(f'{e1.id}_{rel_type}_{e2.id}')}",
                            source_id=e1.id,
                            target_id=e2.id,
                            type=rel_type,
                            properties={"proximity_distance": distance},
                            references=[chunk_id],
                            confidence=0.6,
                        )
                        relationships.append(rel)

        return relationships

    def query_entities_by_type(self, entity_type: str) -> List[Entity]:
        """Query all entities of a specific type"""
        return [self.entities[eid] for eid in self.entity_index.get(entity_type, [])]

    def query_entities_by_chunk(self, chunk_id: str) -> List[Entity]:
        """Query all entities extracted from a specific chunk"""
        return [self.entities[eid] for eid in self.chunk_index.get(chunk_id, [])]

    def query_relationships_by_entity(
        self, entity_id: str, direction: str = "both"
    ) -> List[Relationship]:
        """Query relationships connected to an entity"""
        relationships = []

        if direction in ["out", "both"]:
            # Outgoing relationships
            for target in self.graph.successors(entity_id):
                for key, data in self.graph[entity_id][target].items():
                    if key in self.relationships:
                        relationships.append(self.relationships[key])

        if direction in ["in", "both"]:
            # Incoming relationships
            for source in self.graph.predecessors(entity_id):
                for key, data in self.graph[source][entity_id].items():
                    if key in self.relationships:
                        relationships.append(self.relationships[key])

        return relationships

    def find_paths(
        self, source_entity_id: str, target_entity_id: str, max_length: int = 3
    ) -> List[List[str]]:
        """Find paths between two entities"""
        try:
            paths = list(
                nx.all_simple_paths(
                    self.graph, source_entity_id, target_entity_id, cutoff=max_length
                )
            )
            return paths
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return []

    def get_subgraph(
        self, entity_ids: List[str], include_neighbors: bool = True
    ) -> nx.DiGraph:
        """Get a subgraph containing specified entities"""
        nodes = set(entity_ids)

        if include_neighbors:
            for entity_id in entity_ids:
                nodes.update(self.graph.predecessors(entity_id))
                nodes.update(self.graph.successors(entity_id))

        return self.graph.subgraph(nodes)

    def compute_centrality(self, centrality_type: str = "degree") -> Dict[str, float]:
        """Compute centrality metrics for entities"""
        if centrality_type == "degree":
            return nx.degree_centrality(self.graph)
        elif centrality_type == "betweenness":
            return nx.betweenness_centrality(self.graph)
        elif centrality_type == "closeness":
            return nx.closeness_centrality(self.graph)
        elif centrality_type == "eigenvector":
            try:
                return nx.eigenvector_centrality(self.graph, max_iter=100)
            except:
                return {}
        else:
            return {}

    def detect_communities(self) -> List[Set[str]]:
        """Detect communities/clusters in the graph"""
        # Convert to undirected for community detection
        undirected = self.graph.to_undirected()

        # Use Louvain method for community detection
        import community.community_louvain as community_louvain

        partition = community_louvain.best_partition(undirected)

        # Group nodes by community
        communities = defaultdict(set)
        for node, comm_id in partition.items():
            communities[comm_id].add(node)

        return list(communities.values())

    def merge_duplicate_entities(self, similarity_threshold: float = 0.9) -> None:
        """Merge entities that are likely duplicates"""
        # Simple name-based deduplication
        entity_groups = defaultdict(list)

        for entity in self.entities.values():
            # Normalize name for comparison
            normalized = entity.name.lower().strip()
            entity_groups[normalized].append(entity)

        # Merge entities with same normalized name
        for normalized, group in entity_groups.items():
            if len(group) > 1:
                # Keep first entity as master
                master = group[0]

                for duplicate in group[1:]:
                    # Merge references
                    master.references.extend(duplicate.references)
                    master.references = list(set(master.references))

                    # Merge properties
                    for key, value in duplicate.properties.items():
                        if key not in master.properties:
                            master.properties[key] = value

                    # Update relationships
                    for rel in self.relationships.values():
                        if rel.source_id == duplicate.id:
                            rel.source_id = master.id
                        if rel.target_id == duplicate.id:
                            rel.target_id = master.id

                    # Remove duplicate from graph
                    if duplicate.id in self.graph:
                        self.graph.remove_node(duplicate.id)
                    if duplicate.id in self.entities:
                        del self.entities[duplicate.id]

    def save(self) -> None:
        """Save knowledge graph to disk"""
        # Save entities
        entities_path = self.storage_path / "entities.json"
        with open(entities_path, "w") as f:
            entities_data = {
                eid: {
                    "id": e.id,
                    "type": e.type,
                    "name": e.name,
                    "properties": e.properties,
                    "references": e.references,
                }
                for eid, e in self.entities.items()
            }
            json.dump(entities_data, f, indent=2)

        # Save relationships
        relationships_path = self.storage_path / "relationships.json"
        with open(relationships_path, "w") as f:
            relationships_data = {
                rid: {
                    "id": r.id,
                    "source_id": r.source_id,
                    "target_id": r.target_id,
                    "type": r.type,
                    "properties": r.properties,
                    "references": r.references,
                    "confidence": r.confidence,
                }
                for rid, r in self.relationships.items()
            }
            json.dump(relationships_data, f, indent=2)

        # Save NetworkX graph
        nx.write_gexf(self.graph, self.storage_path / "graph.gexf")

    def load(self) -> None:
        """Load knowledge graph from disk"""
        # Load entities
        entities_path = self.storage_path / "entities.json"
        if entities_path.exists():
            with open(entities_path, "r") as f:
                entities_data = json.load(f)
                for eid, data in entities_data.items():
                    entity = Entity(
                        id=data["id"],
                        type=data["type"],
                        name=data["name"],
                        properties=data["properties"],
                        references=data["references"],
                    )
                    self.add_entity(entity)

        # Load relationships
        relationships_path = self.storage_path / "relationships.json"
        if relationships_path.exists():
            with open(relationships_path, "r") as f:
                relationships_data = json.load(f)
                for rid, data in relationships_data.items():
                    relationship = Relationship(
                        id=data["id"],
                        source_id=data["source_id"],
                        target_id=data["target_id"],
                        type=data["type"],
                        properties=data["properties"],
                        references=data["references"],
                        confidence=data["confidence"],
                    )
                    self.add_relationship(relationship)

    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics about the knowledge graph"""
        return {
            "total_entities": len(self.entities),
            "total_relationships": len(self.relationships),
            "entity_types": {
                et: len(self.entity_index[et])
                for et in self.entity_types
                if self.entity_index[et]
            },
            "avg_degree": sum(dict(self.graph.degree()).values()) / len(self.graph)
            if len(self.graph) > 0
            else 0,
            "connected_components": nx.number_weakly_connected_components(self.graph),
            "density": nx.density(self.graph),
        }


# Convenience functions for integration
def create_knowledge_graph() -> KnowledgeGraph:
    """Create a new knowledge graph instance"""
    return KnowledgeGraph()


def extract_and_add_to_graph(
    kg: KnowledgeGraph, text: str, chunk_id: str
) -> Dict[str, Any]:
    """Extract entities and relationships from text and add to graph"""
    # Extract entities
    entities = kg.extract_entities_from_text(text, chunk_id)

    # Add entities to graph
    for entity in entities:
        kg.add_entity(entity)

    # Extract relationships
    relationships = kg.extract_relationships_from_text(text, entities, chunk_id)

    # Add relationships to graph
    for relationship in relationships:
        kg.add_relationship(relationship)

    # Deduplicate
    kg.merge_duplicate_entities()

    return {
        "entities_extracted": len(entities),
        "relationships_extracted": len(relationships),
        "chunk_id": chunk_id,
    }
