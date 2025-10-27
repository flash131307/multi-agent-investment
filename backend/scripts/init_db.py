"""
Database initialization script for MongoDB and ChromaDB.
Run this once to set up the database infrastructure.
"""
import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.services.database import mongodb
from backend.services.chroma_client import chroma_db
from backend.memory.conversation import conversation_memory
from backend.memory.entity_graph import entity_graph

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def init_mongodb():
    """Initialize MongoDB collections and indexes."""
    logger.info("=" * 60)
    logger.info("Initializing MongoDB...")
    logger.info("=" * 60)

    try:
        # Connect to MongoDB
        await mongodb.connect()

        # Create indexes for conversations
        logger.info("\nCreating indexes for conversations...")
        await conversation_memory.create_indexes()

        # Create indexes for entities
        logger.info("\nCreating indexes for entities...")
        await entity_graph.create_indexes()

        # Test health check
        is_healthy = await mongodb.health_check()
        if is_healthy:
            logger.info("\n✅ MongoDB initialized successfully!")
        else:
            logger.error("\n❌ MongoDB health check failed!")
            return False

        return True

    except Exception as e:
        logger.error(f"\n❌ MongoDB initialization failed: {e}")
        return False


def init_chromadb():
    """Initialize ChromaDB collection."""
    logger.info("\n" + "=" * 60)
    logger.info("Initializing ChromaDB...")
    logger.info("=" * 60)

    try:
        # Connect to ChromaDB
        chroma_db.connect()

        # Get collection info
        count = chroma_db.count()
        logger.info(f"\n✅ ChromaDB initialized successfully!")
        logger.info(f"📊 Current document count: {count}")

        return True

    except Exception as e:
        logger.error(f"\n❌ ChromaDB initialization failed: {e}")
        return False


async def insert_test_data():
    """Insert test data to verify database operations."""
    logger.info("\n" + "=" * 60)
    logger.info("Inserting test data...")
    logger.info("=" * 60)

    try:
        # Test conversation memory
        logger.info("\n📝 Testing conversation memory...")
        session_id = await conversation_memory.create_session(user_id="test_user")
        await conversation_memory.save_message(
            session_id=session_id,
            role="user",
            content="What is the current price of AAPL?"
        )
        await conversation_memory.save_message(
            session_id=session_id,
            role="assistant",
            content="Let me fetch the latest price for Apple Inc. (AAPL)..."
        )

        messages = await conversation_memory.get_conversation(session_id)
        logger.info(f"✅ Created test session: {session_id}")
        logger.info(f"   Messages: {len(messages)}")

        # Test entity graph
        logger.info("\n🔗 Testing entity graph...")
        await entity_graph.create_entity(
            entity_id="AAPL",
            entity_type="stock",
            metadata={
                "name": "Apple Inc.",
                "sector": "Technology",
                "market_cap": "2.8T"
            }
        )

        await entity_graph.create_entity(
            entity_id="TECH_SECTOR",
            entity_type="sector",
            metadata={
                "name": "Technology",
                "description": "Technology sector"
            }
        )

        # Add relationship
        await entity_graph.add_relationship(
            entity_id="AAPL",
            related_to="TECH_SECTOR",
            relation_type="belongs_to"
        )

        entity = await entity_graph.get_entity("AAPL")
        logger.info(f"✅ Created test entity: AAPL")
        logger.info(f"   Relationships: {len(entity['relationships'])}")

        # Test ChromaDB
        logger.info("\n📚 Testing ChromaDB...")
        test_docs = [
            "Apple Inc. is a technology company that designs consumer electronics.",
            "Tesla is an electric vehicle and clean energy company."
        ]
        test_ids = ["test_doc_1", "test_doc_2"]
        test_embeddings = [
            [0.1] * 1536,  # Dummy embedding for testing
            [0.2] * 1536
        ]
        test_metadata = [
            {"ticker": "AAPL", "source": "test", "doc_type": "description"},
            {"ticker": "TSLA", "source": "test", "doc_type": "description"}
        ]

        chroma_db.add_documents(
            ids=test_ids,
            documents=test_docs,
            embeddings=test_embeddings,
            metadatas=test_metadata
        )

        count = chroma_db.count()
        logger.info(f"✅ Added test documents to ChromaDB")
        logger.info(f"   Total documents: {count}")

        logger.info("\n" + "=" * 60)
        logger.info("✅ All test data inserted successfully!")
        logger.info("=" * 60)

        return True

    except Exception as e:
        logger.error(f"\n❌ Failed to insert test data: {e}")
        import traceback
        traceback.print_exc()
        return False


async def cleanup_test_data():
    """Clean up test data."""
    logger.info("\n🧹 Cleaning up test data...")

    try:
        # Delete test session
        sessions = await conversation_memory.db["conversations"].find(
            {"user_id": "test_user"}
        ).to_list(length=10)

        for session in sessions:
            await conversation_memory.delete_session(session["session_id"])

        # Delete test entities
        await entity_graph.delete_entity("AAPL")
        await entity_graph.delete_entity("TECH_SECTOR")

        # Delete test ChromaDB docs
        chroma_db.delete(ids=["test_doc_1", "test_doc_2"])

        logger.info("✅ Test data cleaned up")

    except Exception as e:
        logger.warning(f"⚠️  Cleanup warning: {e}")


async def main():
    """Main initialization function."""
    logger.info("\n" + "=" * 60)
    logger.info("DATABASE INITIALIZATION")
    logger.info("=" * 60)

    # Initialize MongoDB
    mongodb_success = await init_mongodb()
    if not mongodb_success:
        logger.error("\n❌ Failed to initialize MongoDB. Exiting.")
        return

    # Initialize ChromaDB
    chromadb_success = init_chromadb()
    if not chromadb_success:
        logger.error("\n❌ Failed to initialize ChromaDB. Exiting.")
        await mongodb.close()
        return

    # Insert test data
    test_success = await insert_test_data()
    if not test_success:
        logger.error("\n❌ Failed to insert test data.")
        await mongodb.close()
        return

    # Optional: Clean up test data
    # Uncomment if you want to remove test data after verification
    # await cleanup_test_data()

    # Close MongoDB connection
    await mongodb.close()

    logger.info("\n" + "=" * 60)
    logger.info("✅ DATABASE INITIALIZATION COMPLETE!")
    logger.info("=" * 60)
    logger.info("\nNext steps:")
    logger.info("1. Verify MongoDB connection at: https://cloud.mongodb.com")
    logger.info("2. Check ChromaDB data at: ./data/chroma/")
    logger.info("3. Run Phase 3 to implement RAG pipeline")
    logger.info("\n")


if __name__ == "__main__":
    asyncio.run(main())
