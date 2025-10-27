"""
Conversation memory management using MongoDB.
Stores session history with automatic TTL expiration.
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging
import uuid

from backend.services.database import mongodb

logger = logging.getLogger(__name__)


class ConversationMemory:
    """Manages conversation history in MongoDB."""

    COLLECTION_NAME = "conversations"

    def __init__(self):
        self.db = None

    async def _get_collection(self):
        """Get conversations collection."""
        if self.db is None:
            self.db = await mongodb.get_database()
        return self.db[self.COLLECTION_NAME]

    async def create_session(self, user_id: Optional[str] = None) -> str:
        """
        Create a new conversation session with auto-generated ID.

        Args:
            user_id: Optional user identifier

        Returns:
            session_id: Unique session identifier
        """
        session_id = str(uuid.uuid4())
        await self._create_session_with_id(session_id, user_id)
        return session_id

    async def _create_session_with_id(
        self,
        session_id: str,
        user_id: Optional[str] = None
    ):
        """
        Create a session with a specific session_id.

        Args:
            session_id: Specific session identifier to use
            user_id: Optional user identifier
        """
        collection = await self._get_collection()

        session_doc = {
            "session_id": session_id,
            "user_id": user_id,
            "messages": [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(hours=24)  # TTL
        }

        await collection.insert_one(session_doc)
        logger.info(f"Created session with specific ID: {session_id}")

    async def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        _retry: bool = False
    ):
        """
        Save a message to the conversation history.

        Args:
            session_id: Session identifier
            role: "user" or "assistant"
            content: Message content
            _retry: Internal flag to prevent infinite recursion
        """
        collection = await self._get_collection()

        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow()
        }

        result = await collection.update_one(
            {"session_id": session_id},
            {
                "$push": {"messages": message},
                "$set": {
                    "updated_at": datetime.utcnow(),
                    "expires_at": datetime.utcnow() + timedelta(hours=24)
                }
            }
        )

        if result.matched_count == 0:
            if _retry:
                logger.error(f"Session {session_id} still not found after retry, giving up")
                return

            logger.warning(f"Session not found: {session_id}, creating new session with ID")
            # Create session with the specific session_id instead of generating new one
            await self._create_session_with_id(session_id)
            # Retry saving the message (only once)
            await self.save_message(session_id, role, content, _retry=True)
        else:
            logger.info(f"Saved {role} message to session {session_id}")

    async def get_conversation(
        self,
        session_id: str,
        limit: int = 50
    ) -> List[Dict]:
        """
        Get conversation history for a session.

        Args:
            session_id: Session identifier
            limit: Maximum number of messages to return

        Returns:
            List of messages (most recent first)
        """
        collection = await self._get_collection()

        session = await collection.find_one(
            {"session_id": session_id},
            {"messages": {"$slice": -limit}}  # Get last N messages
        )

        if session is None:
            logger.warning(f"Session not found: {session_id}")
            return []

        return session.get("messages", [])

    async def get_session_info(self, session_id: str) -> Optional[Dict]:
        """
        Get session metadata.

        Args:
            session_id: Session identifier

        Returns:
            Session document without messages
        """
        collection = await self._get_collection()

        session = await collection.find_one(
            {"session_id": session_id},
            {"messages": 0}  # Exclude messages
        )

        return session

    async def clear_conversation(self, session_id: str):
        """
        Clear all messages from a conversation.

        Args:
            session_id: Session identifier
        """
        collection = await self._get_collection()

        await collection.update_one(
            {"session_id": session_id},
            {
                "$set": {
                    "messages": [],
                    "updated_at": datetime.utcnow()
                }
            }
        )
        logger.info(f"Cleared conversation: {session_id}")

    async def delete_session(self, session_id: str):
        """
        Delete a conversation session.

        Args:
            session_id: Session identifier
        """
        collection = await self._get_collection()

        result = await collection.delete_one({"session_id": session_id})
        if result.deleted_count > 0:
            logger.info(f"Deleted session: {session_id}")
        else:
            logger.warning(f"Session not found for deletion: {session_id}")

    async def delete_expired_sessions(self) -> int:
        """
        Delete all expired sessions (cleanup job).

        Returns:
            Number of deleted sessions
        """
        collection = await self._get_collection()

        result = await collection.delete_many({
            "expires_at": {"$lt": datetime.utcnow()}
        })

        deleted_count = result.deleted_count
        if deleted_count > 0:
            logger.info(f"Deleted {deleted_count} expired sessions")
        return deleted_count

    async def create_indexes(self):
        """Create indexes for the conversations collection."""
        collection = await self._get_collection()

        # Unique index on session_id
        await collection.create_index("session_id", unique=True)

        # Index on user_id for querying user's sessions
        await collection.create_index("user_id")

        # TTL index to auto-delete expired sessions
        await collection.create_index(
            "expires_at",
            expireAfterSeconds=0  # Delete immediately when expires_at passes
        )

        logger.info("✅ Created indexes for conversations collection")


# Singleton instance
conversation_memory = ConversationMemory()
