"""
Entity graph management using MongoDB.
Stores entities (stocks, sectors, portfolios) and their relationships.
"""
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging

from backend.services.database import mongodb

logger = logging.getLogger(__name__)


class EntityGraph:
    """Manages entity relationships in MongoDB."""

    COLLECTION_NAME = "entities"

    def __init__(self):
        self.db = None

    async def _get_collection(self):
        """Get entities collection."""
        if self.db is None:
            self.db = await mongodb.get_database()
        return self.db[self.COLLECTION_NAME]

    async def create_entity(
        self,
        entity_id: str,
        entity_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict:
        """
        Create a new entity.

        Args:
            entity_id: Unique identifier (e.g., "AAPL", "TECH_SECTOR")
            entity_type: Type of entity ("stock", "sector", "portfolio")
            metadata: Additional metadata (price, market_cap, etc.)

        Returns:
            Created entity document
        """
        collection = await self._get_collection()

        entity_doc = {
            "entity_id": entity_id,
            "entity_type": entity_type,
            "relationships": [],
            "metadata": metadata or {},
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        # Upsert (insert if not exists, replace if exists)
        await collection.replace_one(
            {"entity_id": entity_id},
            entity_doc,
            upsert=True
        )

        logger.info(f"Created entity: {entity_id} ({entity_type})")
        return entity_doc

    async def get_entity(self, entity_id: str) -> Optional[Dict]:
        """
        Get entity by ID.

        Args:
            entity_id: Entity identifier

        Returns:
            Entity document or None
        """
        collection = await self._get_collection()
        entity = await collection.find_one({"entity_id": entity_id})

        if entity:
            entity.pop("_id", None)  # Remove MongoDB internal ID
        return entity

    async def update_metadata(
        self,
        entity_id: str,
        metadata: Dict[str, Any]
    ):
        """
        Update entity metadata.

        Args:
            entity_id: Entity identifier
            metadata: Metadata to update/add
        """
        collection = await self._get_collection()

        result = await collection.update_one(
            {"entity_id": entity_id},
            {
                "$set": {
                    f"metadata.{key}": value for key, value in metadata.items()
                } | {"updated_at": datetime.utcnow()}
            }
        )

        if result.matched_count > 0:
            logger.info(f"Updated metadata for entity: {entity_id}")
        else:
            logger.warning(f"Entity not found: {entity_id}")

    async def add_relationship(
        self,
        entity_id: str,
        related_to: str,
        relation_type: str
    ):
        """
        Add a relationship between entities.

        Args:
            entity_id: Source entity
            related_to: Target entity
            relation_type: Type of relationship
                          ("belongs_to", "tracked_by", "similar_to", etc.)
        """
        collection = await self._get_collection()

        relationship = {
            "related_to": related_to,
            "relation_type": relation_type
        }

        # Add relationship if it doesn't already exist
        await collection.update_one(
            {"entity_id": entity_id},
            {
                "$addToSet": {"relationships": relationship},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )

        logger.info(f"Added relationship: {entity_id} --{relation_type}--> {related_to}")

    async def remove_relationship(
        self,
        entity_id: str,
        related_to: str,
        relation_type: Optional[str] = None
    ):
        """
        Remove a relationship.

        Args:
            entity_id: Source entity
            related_to: Target entity
            relation_type: Optional relation type filter
        """
        collection = await self._get_collection()

        if relation_type:
            query = {
                "related_to": related_to,
                "relation_type": relation_type
            }
        else:
            query = {"related_to": related_to}

        await collection.update_one(
            {"entity_id": entity_id},
            {
                "$pull": {"relationships": query},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )

        logger.info(f"Removed relationship: {entity_id} --> {related_to}")

    async def get_related_entities(
        self,
        entity_id: str,
        relation_type: Optional[str] = None
    ) -> List[Dict]:
        """
        Get entities related to this entity.

        Args:
            entity_id: Entity identifier
            relation_type: Optional filter by relation type

        Returns:
            List of related entity documents
        """
        collection = await self._get_collection()

        # Get source entity
        entity = await collection.find_one({"entity_id": entity_id})
        if not entity:
            return []

        # Filter relationships
        relationships = entity.get("relationships", [])
        if relation_type:
            relationships = [
                r for r in relationships
                if r.get("relation_type") == relation_type
            ]

        # Get related entities
        related_ids = [r["related_to"] for r in relationships]
        if not related_ids:
            return []

        cursor = collection.find({"entity_id": {"$in": related_ids}})
        related_entities = await cursor.to_list(length=100)

        # Remove MongoDB IDs
        for entity in related_entities:
            entity.pop("_id", None)

        return related_entities

    async def search_entities(
        self,
        entity_type: Optional[str] = None,
        metadata_filter: Optional[Dict[str, Any]] = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        Search entities by type and metadata.

        Args:
            entity_type: Filter by entity type
            metadata_filter: Filter by metadata fields
            limit: Max results

        Returns:
            List of matching entities
        """
        collection = await self._get_collection()

        query = {}
        if entity_type:
            query["entity_type"] = entity_type

        if metadata_filter:
            for key, value in metadata_filter.items():
                query[f"metadata.{key}"] = value

        cursor = collection.find(query).limit(limit)
        entities = await cursor.to_list(length=limit)

        # Remove MongoDB IDs
        for entity in entities:
            entity.pop("_id", None)

        return entities

    async def delete_entity(self, entity_id: str):
        """
        Delete an entity.

        Args:
            entity_id: Entity identifier
        """
        collection = await self._get_collection()

        result = await collection.delete_one({"entity_id": entity_id})
        if result.deleted_count > 0:
            logger.info(f"Deleted entity: {entity_id}")
        else:
            logger.warning(f"Entity not found for deletion: {entity_id}")

    async def create_indexes(self):
        """Create indexes for the entities collection."""
        collection = await self._get_collection()

        # Unique index on entity_id
        await collection.create_index("entity_id", unique=True)

        # Index on entity_type for filtering
        await collection.create_index("entity_type")

        # Compound index for common queries
        await collection.create_index([
            ("entity_type", 1),
            ("updated_at", -1)
        ])

        logger.info("✅ Created indexes for entities collection")


# Singleton instance
entity_graph = EntityGraph()
