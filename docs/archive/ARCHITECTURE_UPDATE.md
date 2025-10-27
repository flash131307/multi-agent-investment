# Architecture Update: ChromaDB Integration

## Summary

Updated the system architecture to use **ChromaDB** for local vector search instead of MongoDB Atlas Vector Search, enabling **completely free development** while maintaining full functionality.

## Changes Overview

### Before (Original Plan)
- **MongoDB Atlas M10+** ($57/month) - Required for vector search
- OpenAI embeddings stored in MongoDB
- Vector search via MongoDB Atlas Search

### After (Updated Plan)
- **MongoDB Atlas M0** (FREE) - Conversation & entity storage
- **ChromaDB** (FREE, local) - Vector search for RAG
- OpenAI embeddings stored in ChromaDB
- **Total cost: $0/month** (excluding OpenAI API usage)

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        User Query                           │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │   FastAPI Backend     │
                │   (WebSocket Stream)  │
                └───────────┬───────────┘
                            │
                ┌───────────┴──────────┐
                │                      │
                ▼                      ▼
    ┌──────────────────┐   ┌──────────────────┐
    │  LangGraph       │   │  Session Mgmt    │
    │  Multi-Agent     │   │  (MongoDB Free)  │
    │  System          │   └──────────────────┘
    └────────┬─────────┘
             │
    ┌────────┴────────┬──────────────┬──────────────┐
    │                 │              │              │
    ▼                 ▼              ▼              ▼
┌────────┐    ┌────────────┐  ┌──────────┐  ┌────────────┐
│ Router │    │Market Data │  │Sentiment │  │   Report   │
│ Agent  │    │   Agent    │  │  Agent   │  │  Generator │
└────┬───┘    └─────┬──────┘  └────┬─────┘  └─────┬──────┘
     │              │              │              │
     │              ▼              ▼              │
     │      ┌────────────┐  ┌────────────┐       │
     │      │   Yahoo    │  │  ChromaDB  │       │
     │      │  Finance   │  │  (Vector   │       │
     │      │    API     │  │  Search)   │       │
     │      └────────────┘  └────────────┘       │
     │                            ▲               │
     │              ┌─────────────┘               │
     │              │ Embeddings                  │
     │              │ (OpenAI)                    │
     │              │                             │
     └──────────────┴─────────────────────────────┘
                    │
                    ▼
            ┌───────────────┐
            │  OpenAI API   │
            │  (GPT-4o-mini)│
            └───────────────┘
```

## Database Separation of Concerns

### MongoDB (Free M0)
**Purpose**: Structured data storage
- **Conversations Collection**: Session history, user messages (24h TTL)
- **Entities Collection**: Stock entities, relationships, metadata
- **No embeddings**: Removed embedding fields to reduce storage

**Why MongoDB**:
- ✅ Free tier available
- ✅ Excellent for structured data
- ✅ TTL indexes for automatic cleanup
- ✅ Relationship management

### ChromaDB (Local)
**Purpose**: Vector similarity search
- **Document embeddings**: SEC filings, news articles, financial docs
- **Metadata filtering**: By ticker, date, source, doc_type
- **Cosine similarity**: Fast nearest-neighbor search

**Why ChromaDB**:
- ✅ Completely free, runs locally
- ✅ No external service dependencies
- ✅ Simple API, easy setup
- ✅ Persistent storage to disk
- ✅ Built-in metadata filtering
- ✅ No index configuration needed

## Data Flow

### RAG Pipeline with ChromaDB

```
1. Ingest Document (EDGAR/News)
   ↓
2. Chunk Text (512 tokens, 50 overlap)
   ↓
3. Generate Embeddings (OpenAI text-embedding-3-small)
   ↓
4. Store in ChromaDB
   - documents: ["chunk1", "chunk2", ...]
   - embeddings: [[0.1, 0.2, ...], ...]
   - metadatas: [
       {"ticker": "AAPL", "source": "10-K", "date": "2024-01-15"},
       ...
     ]
   ↓
5. Query (User asks about AAPL)
   ↓
6. Embed Query (OpenAI)
   ↓
7. ChromaDB Similarity Search
   - Find top 5 most similar chunks
   - Filter by ticker="AAPL" (optional)
   ↓
8. Return to LLM as Context
```

### Conversation Flow

```
User Query → MongoDB (Load History)
             ↓
          LangGraph Router
             ↓
       Agent Execution
       (Market Data / Sentiment)
             ↓
       MongoDB (Save Message)
             ↓
          Return to User
```

## File Structure Changes

### New Files
```
backend/services/chroma_client.py    # ChromaDB initialization
backend/rag/vector_store.py          # Vector search wrapper
backend/scripts/test_chroma.py       # ChromaDB testing
docs/MONGODB_SETUP.md                # MongoDB setup guide
data/chroma/                         # ChromaDB persistence (gitignored)
```

### Modified Files
```
requirements.txt                     # Added chromadb>=0.4.22
.env.template                        # Added CHROMA_* settings
backend/config/settings.py           # Added ChromaDB config
CLAUDE.md                            # Updated architecture
PLAN.md                              # Updated Phase 2 & 3
README.md                            # Updated tech stack
.gitignore                           # Added data/chroma/
```

## Configuration

### Environment Variables (.env)
```bash
# MongoDB (Free M0 tier)
MONGODB_URI=mongodb+srv://...
MONGODB_DB_NAME=investment_research

# ChromaDB (local)
CHROMA_PERSIST_DIR=./data/chroma
CHROMA_COLLECTION_NAME=investment_docs

# OpenAI (LLM + Embeddings)
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

## Performance Comparison

| Feature | MongoDB M10+ Vector Search | ChromaDB (Local) |
|---------|---------------------------|------------------|
| **Cost** | $57/month | FREE |
| **Setup** | Complex (index config) | Simple (auto-config) |
| **Latency** | Network call (~50-100ms) | Local (~5-10ms) |
| **Scalability** | Cloud-hosted, unlimited | Limited by disk space |
| **Metadata Filter** | Yes | Yes |
| **Hybrid Search** | Yes | Yes |
| **Best For** | Production, large scale | Development, testing |

## Migration Path (Future)

When ready for production deployment, you can:

1. **Keep ChromaDB** (Recommended for small-medium scale)
   - Deploy with Docker
   - Mount persistent volume
   - Works great for most use cases

2. **Migrate to MongoDB Atlas Vector Search**
   - Upgrade to M10+ cluster
   - Run migration script
   - Update vector_store.py to use MongoDB
   - Benefit: Unified database

3. **Migrate to Pinecone/Weaviate**
   - Dedicated vector DBs
   - Better for massive scale
   - Higher cost

## Testing Strategy

### Phase 2 (Database Setup)
```bash
# Test MongoDB connection
python -m backend.scripts.init_db

# Test ChromaDB operations
python -m backend.scripts.test_chroma

# Run unit tests
pytest tests/test_memory.py tests/test_chroma.py -v
```

### Phase 3 (RAG Pipeline)
```bash
# Ingest sample document
python -m backend.scripts.seed_edgar --ticker AAPL

# Test vector search
python -m backend.scripts.test_rag

# Run integration tests
pytest tests/test_rag.py -v
```

## Cost Analysis

### Development (Current Setup)
- MongoDB Atlas M0: **$0/month**
- ChromaDB: **$0/month**
- OpenAI API: **Pay-as-you-go**
  - GPT-4o-mini: ~$0.15 per 1M input tokens
  - text-embedding-3-small: ~$0.02 per 1M tokens
  - Estimated monthly (moderate testing): **$5-10**

**Total: ~$5-10/month** (OpenAI only)

### Production (if deployed)
- MongoDB Atlas M0: **$0/month** (or upgrade to M2 for $9/month)
- ChromaDB in Docker: **$0/month** (or VPS hosting ~$5-10/month)
- OpenAI API: **Variable** (scales with usage)

**Total: ~$15-30/month** (small scale production)

## Benefits of This Approach

1. **Zero Infrastructure Cost** for development
2. **Faster Local Development** (no network latency)
3. **Easy Testing** (no cloud dependencies)
4. **Flexible Migration** (can switch to cloud vector DB later)
5. **Full Functionality** (no feature compromise)

## Next Steps

1. ✅ Architecture updated
2. ✅ Dependencies configured
3. 🔜 Set up MongoDB Atlas (Free M0)
4. 🔜 Implement Phase 2 (MongoDB + ChromaDB)
5. 🔜 Test RAG pipeline with ChromaDB
6. 🔜 Build LangGraph agents
7. 🔜 Complete FastAPI backend

---

**Status**: Architecture update complete, ready for Phase 2 implementation!
