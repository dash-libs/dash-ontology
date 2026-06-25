from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import json


@dataclass
class Entity:
    name: str
    table: str
    description: str = ""
    primary_key: str = "id"
    tags: list[str] = field(default_factory=list)


@dataclass
class Relationship:
    from_entity: str
    to_entity: str
    from_column: str
    to_column: str
    relationship_type: str  # one_to_many | many_to_many | one_to_one
    label: str = ""
    ai_semantic: str = ""   # natural language description for AI/LLM context


class OntologyBuilder:
    """
    Define entities, relationships, and lineage for Databricks tables.
    Exports an ontology that AI agents can use for semantic understanding.

    Usage::
        ont = OntologyBuilder(name="Banking Ontology")
        ont.add_entity("Customer", table="catalog.schema.dim_customer", primary_key="customer_id")
        ont.add_entity("Account",  table="catalog.schema.dim_account",  primary_key="account_id")
        ont.add_relationship("Customer", "Account", "customer_id", "customer_id",
                             "one_to_many", label="has_account",
                             ai_semantic="A customer can hold one or more bank accounts")
        ont.save(table="catalog.schema.ontology")
    """

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self._entities: dict[str, Entity] = {}
        self._relationships: list[Relationship] = []
        self._lineage: list[dict] = []

    def add_entity(self, name: str, table: str, description: str = "",
                   primary_key: str = "id", tags: list[str] = None):
        self._entities[name] = Entity(name, table, description, primary_key, tags or [])
        return self

    def add_relationship(self, from_entity: str, to_entity: str,
                         from_column: str, to_column: str,
                         relationship_type: str = "one_to_many",
                         label: str = "", ai_semantic: str = ""):
        self._relationships.append(Relationship(
            from_entity, to_entity, from_column, to_column,
            relationship_type, label, ai_semantic
        ))
        return self

    def add_lineage(self, source_table: str, target_table: str,
                    transformation: str = "", job_name: str = ""):
        self._lineage.append({
            "source": source_table,
            "target": target_table,
            "transformation": transformation,
            "job_name": job_name,
        })
        return self

    def to_dict(self) -> dict:
        return {
            "ontology_name": self.name,
            "description": self.description,
            "entities": {
                name: {
                    "table": e.table,
                    "description": e.description,
                    "primary_key": e.primary_key,
                    "tags": e.tags,
                }
                for name, e in self._entities.items()
            },
            "relationships": [
                {
                    "from": r.from_entity,
                    "to": r.to_entity,
                    "from_column": r.from_column,
                    "to_column": r.to_column,
                    "type": r.relationship_type,
                    "label": r.label,
                    "ai_semantic": r.ai_semantic,
                }
                for r in self._relationships
            ],
            "lineage": self._lineage,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    def save(self, table: str):
        """Persist the ontology as a Delta table for AI agent consumption."""
        from pyspark.sql import SparkSession, functions as F
        spark = SparkSession.getActiveSession()
        ont_dict = self.to_dict()

        # Flatten relationships for tabular storage
        rows = []
        for r in ont_dict["relationships"]:
            rows.append({
                "ontology_name": self.name,
                "record_type": "relationship",
                "from_entity": r["from"],
                "to_entity": r["to"],
                "from_column": r["from_column"],
                "to_column": r["to_column"],
                "relationship_type": r["type"],
                "label": r["label"],
                "ai_semantic": r["ai_semantic"],
            })
        for name, e in ont_dict["entities"].items():
            rows.append({
                "ontology_name": self.name,
                "record_type": "entity",
                "from_entity": name,
                "to_entity": e["table"],
                "from_column": e["primary_key"],
                "to_column": "",
                "relationship_type": "entity",
                "label": e["description"],
                "ai_semantic": json.dumps(e["tags"]),
            })

        (spark.createDataFrame(rows)
              .withColumn("updated_at", F.current_timestamp())
              .write.format("delta")
              .mode("overwrite")
              .option("overwriteSchema", "true")
              .saveAsTable(table))
        print(f"✅ Ontology '{self.name}' saved to {table}")

    def validate(self) -> list[str]:
        """Check referential integrity of defined relationships."""
        issues = []
        for r in self._relationships:
            if r.from_entity not in self._entities:
                issues.append(f"Unknown entity '{r.from_entity}' in relationship")
            if r.to_entity not in self._entities:
                issues.append(f"Unknown entity '{r.to_entity}' in relationship")
        return issues

    def summary(self):
        print(f"Ontology: {self.name}")
        print(f"  Entities:      {len(self._entities)}")
        print(f"  Relationships: {len(self._relationships)}")
        print(f"  Lineage edges: {len(self._lineage)}")
        issues = self.validate()
        if issues:
            print(f"  ⚠️  {len(issues)} validation issue(s):")
            for i in issues:
                print(f"     - {i}")
        else:
            print("  ✅ Validation passed")
