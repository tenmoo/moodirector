# Vector Memory (RAG) for Scene Retrieval

This document explains the vector memory system that enables the Moo Director to remember past scenes and use them as context for new creations.

## Overview

The system uses **ChromaDB** as a vector database for storing and retrieving past scenes. When you create a scene, it's automatically stored in memory. When creating new scenes, the Orchestrator retrieves similar past scenes to inform its decisions.

### Embedding Options
- **With sentence-transformers** (recommended): Semantic search using `all-MiniLM-L6-v2`
- **Without sentence-transformers** (default fallback): Uses ChromaDB's built-in embeddings

> **Note:** The system works without `sentence-transformers` installed. Install it for better semantic search quality: `pip install sentence-transformers`

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           VECTOR MEMORY FLOW                                 │
│                                                                              │
│  New Scene Request                                                           │
│        │                                                                     │
│        ▼                                                                     │
│  ┌─────────────┐     search      ┌─────────────────────┐                   │
│  │ Orchestrator │◄───────────────│   ChromaDB          │                   │
│  │             │                  │   Vector Store      │                   │
│  │ "Similar to │                  │                     │                   │
│  │  these past │                  │ ┌─────────────────┐│                   │
│  │  scenes..." │                  │ │ Scene Embeddings ││                   │
│  └──────┬──────┘                  │ │ (all-MiniLM-L6) ││                   │
│         │                         │ └─────────────────┘│                   │
│         ▼                         └─────────────────────┘                   │
│    Create Plan                              ▲                                │
│         │                                   │                                │
│         ▼                                   │ store                          │
│    ... workflow ...                         │                                │
│         │                                   │                                │
│         ▼                                   │                                │
│  ┌─────────────┐                           │                                │
│  │  Completed  │───────────────────────────┘                                │
│  │    Scene    │                                                             │
│  └─────────────┘                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## How It Works

### 1. Scene Storage

When a scene is successfully completed, it's automatically stored in vector memory:

```python
# Automatically happens after workflow completion
memory.store_scene(
    scene_id="uuid-123",
    user_prompt="Create a cozy bedroom...",
    master_plan=master_plan,
    scene_objects=[...],
    lighting_setup=lighting,
    camera_setup=camera,
    validation_passed=True
)
```

**What's Stored:**
- User prompt (original request)
- Interpreted mood
- Object names and count
- Lighting mood and color temperature
- Camera settings
- Validation status

### 2. Semantic Search

When creating a new scene, the Orchestrator searches for similar past scenes:

```python
similar_scenes = memory.search_similar_scenes(
    query="modern home office with natural light",
    n_results=3,
    min_score=0.3
)
```

The search uses **semantic similarity**, not keyword matching:
- "cozy bedroom" matches "warm sleeping area"
- "modern office" matches "contemporary workspace"
- "dramatic lighting" matches "high contrast illumination"

### 3. Context Injection

Similar scenes are formatted as context for the Orchestrator:

```
REFERENCE: Here are similar scenes you've created before that may help:

1. "Create a comfortable bedroom with soft lighting..."
   Mood: cozy, intimate
   Objects: bed, nightstand, lamp, rug
   Lighting: warm
   Similarity: 78%

2. "Design a relaxing reading nook..."
   Mood: calm, warm
   Objects: chair, bookshelf, lamp
   Lighting: warm, soft
   Similarity: 65%

You can use these as inspiration, but create a unique plan for the current request.
```

## API Endpoints

### Search Memory

```bash
POST /api/v1/memory/search
```

**Request:**
```json
{
  "query": "cozy bedroom with warm lighting",
  "n_results": 5,
  "min_score": 0.3
}
```

**Response:**
```json
{
  "query": "cozy bedroom with warm lighting",
  "results": [
    {
      "id": "scene-uuid-1",
      "similarity": 0.85,
      "user_prompt": "Create a comfortable bedroom...",
      "interpreted_mood": "cozy, warm",
      "object_count": 5,
      "object_names": ["bed", "desk", "lamp", "rug", "curtain"],
      "lighting_mood": "warm",
      "validation_passed": true,
      "timestamp": "2026-01-31T10:30:00"
    }
  ],
  "total_in_memory": 15
}
```

### Get Recent Scenes

```bash
GET /api/v1/memory/recent?limit=10
```

**Response:**
```json
{
  "scenes": [
    {
      "id": "scene-uuid-1",
      "user_prompt": "Create a cozy bedroom...",
      "interpreted_mood": "cozy, warm",
      "object_count": 5,
      "timestamp": "2026-01-31T10:30:00"
    }
  ],
  "total_in_memory": 15
}
```

### Get Scene by ID

```bash
GET /api/v1/memory/scene/{scene_id}
```

### Delete Scene

```bash
DELETE /api/v1/memory/scene/{scene_id}
```

### Memory Statistics

```bash
GET /api/v1/memory/stats
```

**Response:**
```json
{
  "total_scenes": 15,
  "collection_name": "scene_memory",
  "embedding_model": "all-MiniLM-L6-v2"
}
```

### Clear All Memory

```bash
DELETE /api/v1/memory/clear
```

**Warning:** This cannot be undone!

## Configuration

### Persistence Directory

By default, the vector database is persisted to `./data/scene_memory/`. This can be configured:

```python
from app.memory.scene_memory import SceneMemory

# Persistent storage (default)
memory = SceneMemory(persist_directory="./data/scene_memory")

# In-memory only (lost on restart)
memory = SceneMemory(persist_directory=None)
```

### Embedding Model

The system uses `all-MiniLM-L6-v2` from sentence-transformers, which provides:
- Fast inference (~14K sentences/sec on CPU)
- Good quality for semantic similarity
- 384-dimensional embeddings
- Small model size (~80MB)

## Use Cases

### 1. Style Consistency

If you've created several "cozy" scenes before, new cozy scene requests will automatically reference your past work for consistency.

### 2. Learning from Success

Scenes that passed validation are stored with their settings. The Orchestrator can learn what object combinations, lighting setups, and moods work well together.

### 3. Iterative Refinement

Request variations like "similar to my last bedroom but with cooler lighting" and the system will find and reference your previous bedroom scene.

### 4. Portfolio Reference

Use the search API to find all scenes matching certain criteria:
- "Find all my office scenes"
- "Show scenes with dramatic lighting"
- "List bedroom designs"

## SceneRecord Structure

Each stored scene contains:

```python
class SceneRecord:
    id: str                    # Unique identifier
    timestamp: datetime        # When created
    
    # Request
    user_prompt: str           # Original prompt
    interpreted_mood: str      # Orchestrator's interpretation
    
    # Scene summary
    object_names: List[str]    # Names of all objects
    object_count: int          # Total object count
    
    # Lighting summary
    lighting_mood: str         # "warm", "cool", "neutral"
    light_count: int           # Number of lights
    color_temperature: int     # Primary light color temp
    
    # Camera summary
    focal_length: float        # e.g., 35.0
    aperture: float            # e.g., 2.8
    
    # Validation
    validation_passed: bool
    validation_score: int      # 0-100
    
    # Full data (JSON)
    full_scene_data: str       # Complete serialized scene
```

## Similarity Scoring

Similarity is computed using cosine distance in the embedding space:

| Score | Meaning |
|-------|---------|
| 0.9+ | Nearly identical requests |
| 0.7-0.9 | Very similar (same room type, mood) |
| 0.5-0.7 | Related (similar elements) |
| 0.3-0.5 | Loosely related |
| <0.3 | Different scenes |

## File Locations

| File | Purpose |
|------|---------|
| `backend/app/memory/__init__.py` | Memory module exports |
| `backend/app/memory/scene_memory.py` | SceneMemory class implementation |
| `backend/app/agents/orchestrator.py` | Memory integration in Orchestrator |
| `backend/app/workflow/graph.py` | Auto-storage after completion |
| `backend/app/api/routes.py` | Memory API endpoints |
| `./data/scene_memory/` | Persistent vector database |

## Disabling Memory

If you want to disable memory for a specific workflow:

```python
# In workflow call
result = await run_workflow(
    user_prompt="...",
    store_in_memory=False  # Don't store result
)

# In Orchestrator
orchestrator = OrchestratorAgent(use_memory=False)  # Don't retrieve context
```

## Dependencies

**Required:**
```
chromadb==0.4.22
langchain-community==0.2.16
```

**Optional (for better semantic search):**
```
sentence-transformers==2.2.2
```

> ChromaDB telemetry is automatically disabled to prevent console warnings.

## See Also

- [AGENT_COMMUNICATION.md](AGENT_COMMUNICATION.md) - How agents share state
- [API.md](API.md) - Full API reference
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
