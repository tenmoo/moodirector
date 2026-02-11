# Moo Director - Study Guide

A structured learning path to understand how the multi-agent 3D scene generation system works.

## Learning Path Overview

```
Week 1: Foundations
├── Day 1: Project Overview & Setup
├── Day 2: FastAPI Backend Basics
└── Day 3: Understanding the API

Week 2: Multi-Agent System
├── Day 4: LangGraph & State Management
├── Day 5: Agent Architecture (Part 1)
├── Day 6: Agent Architecture (Part 2)
└── Day 7: The Workflow Graph

Week 3: Deep Dives
├── Day 8: Orchestrator & Planning
├── Day 9: Librarian & Asset Management
├── Day 10: Architect & Spatial Logic
├── Day 11: Material Scientist & PBR
├── Day 12: Cinematographer & Lighting
└── Day 13: Critic & Validation

Week 4: Advanced Topics
├── Day 14: Vector Memory (RAG)
├── Day 15: LangSmith Observability & Evaluation
├── Day 16: Frontend Integration
└── Day 17: Extending the System
```

---

## Week 1: Foundations

### Day 1: Project Overview & Setup

**Goal:** Understand what the project does and get it running.

**Read:**
1. [README.md](../README.md) - Project overview
2. [GETTING_STARTED.md](GETTING_STARTED.md) - Setup instructions
3. [prd.md](prd.md) - Product requirements (understand the "why")

**Do:**
1. Clone and set up the project
2. Start both backend and frontend
3. Create your first scene with a simple prompt
4. Explore the Swagger UI at http://localhost:8000/docs

**Key Concepts:**
- Multi-agent AI systems
- Natural language to structured output
- 3D scene composition

---

### Day 2: FastAPI Backend Basics

**Goal:** Understand the backend structure and FastAPI patterns.

**Read:**
```
backend/
├── main.py              ← Start here (entry point)
├── app/
│   ├── config.py        ← Configuration & settings
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py    ← API endpoints
│   └── models/
│       ├── state.py     ← Data models
│       └── messages.py  ← Request/Response schemas
```

**Study Code:**
1. `main.py` - How FastAPI app is configured
2. `app/config.py` - Environment variables and settings
3. `app/api/routes.py` - Focus on `/scene/create` endpoint

**Key Concepts:**
- FastAPI application structure
- Pydantic models for validation
- Async/await patterns
- Lifespan events (startup/shutdown)

**Exercise:**
Add a simple `/api/v1/ping` endpoint that returns `{"message": "pong"}`.

---

### Day 3: Understanding the API

**Goal:** Master the API contracts and data flow.

**Read:**
1. [API.md](API.md) - Full API reference
2. `app/models/messages.py` - Request/Response schemas
3. `app/models/state.py` - Core data structures

**Study the Data Models:**

```python
# Key models to understand:
SceneObject      # A 3D object in the scene
Material         # PBR material properties
LightingSetup    # Lights and exposure
CameraSetup      # Camera position and settings
ValidationIssue  # Quality check results
MasterPlan       # Orchestrator's plan
AgentState       # Shared workflow state
```

**Exercise:**
Use curl or Postman to:
1. Create a scene via POST `/api/v1/scene/create`
2. Check health via GET `/api/v1/health`
3. Get agent info via GET `/api/v1/agents`

---

## Week 2: Multi-Agent System

### Day 4: LangGraph & State Management

**Goal:** Understand how LangGraph orchestrates the agents.

**Read:**
1. [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
2. LangGraph docs: https://langchain-ai.github.io/langgraph/

**Study Code:**
```
backend/app/
├── workflow/
│   ├── __init__.py
│   └── graph.py         ← The LangGraph workflow definition
└── models/
    └── state.py         ← AgentState (shared state)
```

**Key Concepts:**
- StateGraph - Defines nodes and edges
- State reducers - How state updates merge
- Conditional routing - Dynamic flow control
- Checkpointing - State persistence

**Understand State Reducers:**
```python
# In state.py - these control how state merges:
scene_objects: Annotated[List[SceneObject], replace_list]      # Replaces
validation_issues: Annotated[List[ValidationIssue], replace_list]  # Replaces
messages: Annotated[List[Dict], operator.add]                  # Accumulates
```

**Exercise:**
Draw the workflow graph on paper:
- Nodes: orchestrator, librarian, architect, material_scientist, cinematographer, critic
- Edges: What connects to what?
- Conditions: When does it loop back?

---

### Day 5: Agent Architecture (Part 1)

**Goal:** Understand the BaseAgent class and LLM integration.

**Study Code:**
```
backend/app/agents/
├── __init__.py          ← Exports all agents
├── base.py              ← BaseAgent class (STUDY THIS FIRST)
├── orchestrator.py
├── librarian.py
└── ...
```

**Deep Dive: `base.py`**
```python
class BaseAgent:
    def __init__(self, name, description, system_prompt, model):
        # LLM setup with langchain-groq
        self.llm = ChatGroq(...)
        
        # Prompt template with system message
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            MessagesPlaceholder(variable_name="messages"),
            ("human", "{input}")
        ])
    
    async def invoke_llm(self, input_text, context):
        # How agents call the LLM
        
    def format_state_context(self, state):
        # How state becomes LLM context
```

**Key Concepts:**
- System prompts define agent personality
- ChatPromptTemplate structures the conversation
- Each agent inherits from BaseAgent
- `process()` method is the main entry point

---

### Day 6: Agent Architecture (Part 2)

**Goal:** Understand how each agent processes state.

**Read:**
1. [AGENTS.md](AGENTS.md) - Detailed agent documentation

**Study the Pattern:**
Every agent follows this pattern:
```python
class SomeAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Agent Name",
            description="What it does",
            system_prompt=SYSTEM_PROMPT
        )
    
    async def process(self, state: AgentState) -> Dict[str, Any]:
        # 1. Extract needed data from state
        # 2. Do agent-specific work
        # 3. Optionally call LLM
        # 4. Return state updates
        return {
            "some_field": new_value,
            "current_agent": "next_agent",
            "messages": [{"agent": self.name, "action": "...", "content": "..."}]
        }
```

**Exercise:**
Pick any agent file and identify:
1. What state fields does it read?
2. What state fields does it write?
3. When does it call the LLM?
4. What's the next agent it routes to?

---

### Day 7: The Workflow Graph

**Goal:** Master the complete workflow flow.

**Study: `workflow/graph.py`**

```python
# 1. Create the graph
workflow = StateGraph(AgentState)

# 2. Add nodes (each node is an agent)
workflow.add_node("orchestrator", orchestrator_node)
workflow.add_node("librarian", librarian_node)
# ...

# 3. Set entry point
workflow.set_entry_point("orchestrator")

# 4. Add edges (routing logic)
workflow.add_conditional_edges(
    "orchestrator",
    route_from_orchestrator,
    {"librarian": "librarian", "architect": "architect", ...}
)

# 5. Compile and run
app = workflow.compile()
result = await app.ainvoke(initial_state)
```

**Trace a Request:**
Follow a prompt through the entire system:
1. User submits "Create a cozy bedroom"
2. → `routes.py` creates initial state
3. → `run_workflow()` starts the graph
4. → Orchestrator creates master plan
5. → Librarian fetches assets
6. → Architect places objects
7. → Material Scientist applies textures
8. → Cinematographer sets lighting
9. → Critic validates
10. → If passed: return results
11. → If failed: loop back to Orchestrator

---

## Week 3: Deep Dives

### Day 8: Orchestrator & Planning

**File:** `agents/orchestrator.py`

**Responsibilities:**
- Interpret natural language prompts
- Create structured MasterPlan
- Handle revision routing
- Integrate with vector memory

**Key Methods:**
```python
async def process(state):
    # Normal flow: create master plan
    # Revision flow: route to appropriate agent

async def _get_memory_context(prompt):
    # Retrieve similar past scenes

def _parse_master_plan(response, prompt):
    # Extract JSON from LLM response

def _summarize_validation_issues(issues):
    # Condense issues for revision context
```

**Exercise:**
Modify the system prompt to add a new requirement (e.g., "always include a plant in cozy scenes").

---

### Day 9: Librarian & Asset Management

**File:** `agents/librarian.py`

**Responsibilities:**
- Search the asset library
- Return asset paths and bounding boxes
- Handle substitutions

**Study:**
```python
# The simulated asset library
ASSET_LIBRARY = {
    "bed": {
        "white_bed": {"path": "...", "polygons": 25000, "bbox": (2.0, 1.8, 0.9)},
        "default": {...}
    },
    "desk": {...},
    # ...
}

def _search_asset_library(object_name):
    # Fuzzy matching logic
```

**Exercise:**
Add a new asset category (e.g., "mirror" or "painting") to the library.

---

### Day 10: Architect & Spatial Logic

**File:** `agents/architect.py`

**Responsibilities:**
- Assign 3D coordinates (Z-up)
- Prevent object collisions
- Manage placement zones

**Key Algorithms:**
```python
def _define_zones():
    # Room divided into logical areas

def _find_valid_position(obj, zone, occupied):
    # Grid search → Spiral search → Corner fallback

def _resolve_clipping(objects, issues):
    # Move objects away from conflicts
```

**Coordinate System:**
```
    Z (up)
    │
    │    Y (forward)
    │   /
    │  /
    │ /
    └─────────── X (right)
```

**Exercise:**
Modify the zones to create a different room layout (e.g., L-shaped room).

---

### Day 11: Material Scientist & PBR

**File:** `agents/material_scientist.py`

**Responsibilities:**
- Apply PBR materials
- Adjust for scene mood
- Ensure textures are assigned

**Understand PBR:**
```python
Material(
    shader_type="cloth",     # Material type
    base_color=[R, G, B, A], # Diffuse color
    roughness=0.85,          # 0=shiny, 1=matte
    metallic=0.0,            # 0=dielectric, 1=metal
    subsurface=0.15,         # Light penetration (skin, fabric)
    texture_map="..."        # Diffuse texture path
)
```

**Exercise:**
Add a new material preset for "leather" with appropriate PBR values.

---

### Day 12: Cinematographer & Lighting

**File:** `agents/cinematographer.py`

**Responsibilities:**
- Create mood-appropriate lighting
- Set up camera

**Lighting Presets:**
```python
LIGHTING_PRESETS = {
    "warm_morning": {
        "key_light": {"type": "sun", "angle": 20, "color_temp": 3500},
        "fill_light": {"type": "area", "color_temp": 4500},
        "hdri": "/hdri/morning_interior.hdr"
    },
    # ...
}
```

**Camera Setup:**
```python
CameraSetup(
    position=Coordinate3D(x, y, z),
    target=Coordinate3D(x, y, z),  # Look-at point
    focal_length=35.0,              # mm
    aperture=2.8,                   # f-stop
    depth_of_field=True
)
```

**Exercise:**
Add a new lighting preset for "sunset" with warm orange tones.

---

### Day 13: Critic & Validation

**File:** `agents/critic.py`

**Responsibilities:**
- Validate scene quality
- Detect collisions
- Check materials and lighting
- Route revisions

**Validation Flow:**
```python
async def process(state):
    issues = []
    score = 100
    
    # Run checks, subtract penalties
    collision_issues, penalty = self._check_collisions(objects)
    issues.extend(collision_issues)
    score -= penalty
    
    # Determine pass/fail
    passed = score >= 60 and no_errors
    
    if passed:
        return {"workflow_status": COMPLETED}
    else:
        return {"workflow_status": REVISION, "current_agent": "orchestrator"}
```

**Exercise:**
Add a new validation check (e.g., "ensure at least 2 objects in scene").

---

## Week 4: Advanced Topics

### Day 14: Vector Memory (RAG)

**File:** `memory/scene_memory.py`

**Read:** [MEMORY.md](MEMORY.md)

**How It Works:**
```python
# Store a completed scene
memory.store_scene(scene_id, prompt, master_plan, objects, ...)

# Search for similar scenes
similar = memory.search_similar_scenes("cozy bedroom", n_results=3)

# Orchestrator uses this context
context = "Similar scenes: ..."
plan = await self.invoke_llm(prompt, context=context)
```

**Key Concepts:**
- ChromaDB vector database
- Semantic embeddings
- Similarity search
- RAG (Retrieval Augmented Generation)

---

### Day 15: LangSmith Observability & Evaluation

**Files:** `evaluation/` directory, `main.py`, `agents/base.py`

**Read:** [LANGSMITH.md](LANGSMITH.md)

**How Tracing Works:**

LangSmith automatically traces all LangChain/LangGraph operations when configured:

```python
# In main.py - tracing is initialized at startup
def _configure_langsmith(settings):
    if settings.langchain_api_key:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
        os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project
```

**Custom Tracing in Agents:**

```python
# In base.py - agents add metadata to traces
from langsmith import traceable

class BaseAgent:
    @traceable(run_type="llm")
    async def invoke_llm(self, input_text, context=None):
        # Config includes agent metadata for filtering
        response = await chain.ainvoke(
            {...},
            config={
                "metadata": {"agent_name": self.name, "model": self.model_name},
                "tags": ["agent", self.name.lower()]
            }
        )
```

**Evaluation System:**

```python
# Custom evaluators in evaluation/custom_evaluators.py
def scene_completeness_evaluator(run_output, example):
    # Check if all requested objects are present
    
def prompt_alignment_evaluator(run_output, example):
    # Check if output matches prompt keywords
    
def validation_pass_evaluator(run_output, example):
    # Check if scene passed internal validation
    
def object_count_evaluator(run_output, example):
    # Check if object count is reasonable
```

**Using Evaluations:**

```python
# Create dataset and run evaluations
from app.evaluation import create_evaluation_dataset, run_scene_evaluation

# Create a dataset in LangSmith
dataset_id = create_evaluation_dataset("my-test-prompts")

# Run batch evaluation
results = run_scene_evaluation(dataset_name="my-test-prompts")

# Quick single-prompt evaluation (no LangSmith required)
result = await quick_evaluate_prompt("Create a cozy bedroom")
print(f"Score: {result['overall_score']}")
```

**Key Concepts:**
- Automatic tracing of LangChain/LangGraph
- Custom metadata and tags for filtering
- Evaluation datasets
- Custom evaluators
- Free tier limits (5,000 traces/month)

**Exercise:**
1. Set up LangSmith with your API key
2. Create a scene and view the trace in the dashboard
3. Run a quick evaluation via the API
4. Create your own custom evaluator for a new quality metric

---

### Day 16: Frontend Integration

**Directory:** `frontend/`

**Key Files:**
```
frontend/src/
├── App.tsx              ← Main component
├── components/
│   ├── PromptInput.tsx  ← Scene prompt input
│   ├── SceneDisplay.tsx ← Results display
│   └── AgentStatus.tsx  ← Agent progress
├── store/
│   └── useStore.ts      ← Zustand state management
└── api/
    └── client.ts        ← API client (Axios)
```

**Data Flow:**
```
User Input → Zustand Store → API Client → Backend
                                            ↓
Display ← Zustand Store ← API Response ←───┘
```

---

### Day 17: Extending the System

**Add a New Agent:**

1. Create agent file:
```python
# agents/new_agent.py
from .base import BaseAgent

class NewAgent(BaseAgent):
    def __init__(self):
        super().__init__(...)
    
    async def process(self, state):
        ...
```

2. Register in `agents/__init__.py`

3. Add to workflow in `workflow/graph.py`:
```python
workflow.add_node("new_agent", new_agent_node)
workflow.add_conditional_edges(...)
```

4. Update routing logic

**Add a New Validation Check:**
```python
# In critic.py
def _check_something_new(self, objects):
    issues = []
    for obj in objects:
        if some_condition:
            issues.append(ValidationIssue(
                severity="warning",
                category="new_check",
                description="...",
                suggested_fix="..."
            ))
    return issues, penalty
```

---

## Quick Reference

### File Map
```
backend/
├── main.py                          # Entry point
├── app/
│   ├── config.py                    # Settings
│   ├── api/routes.py                # HTTP endpoints
│   ├── models/
│   │   ├── state.py                 # AgentState, SceneObject, etc.
│   │   └── messages.py              # Request/Response models
│   ├── agents/
│   │   ├── base.py                  # BaseAgent class
│   │   ├── orchestrator.py          # Lead Art Director
│   │   ├── librarian.py             # Asset Fetcher
│   │   ├── architect.py             # Layout Artist
│   │   ├── material_scientist.py    # Look-Dev Artist
│   │   ├── cinematographer.py       # Lighting Director
│   │   └── critic.py                # Quality Controller
│   ├── workflow/
│   │   └── graph.py                 # LangGraph workflow
│   ├── memory/
│   │   └── scene_memory.py          # Vector memory (RAG)
│   └── evaluation/
│       ├── evaluator.py             # Dataset & evaluation functions
│       └── custom_evaluators.py     # Quality evaluators
```

### Key Concepts Glossary

| Term | Definition |
|------|------------|
| **Agent** | AI worker with specific role and system prompt |
| **LangGraph** | Framework for building multi-agent workflows |
| **StateGraph** | Graph structure defining agent flow |
| **AgentState** | Shared state passed between agents |
| **System Prompt** | Instructions that define agent behavior |
| **PBR** | Physically Based Rendering (realistic materials) |
| **Bounding Box** | 3D box defining object dimensions |
| **Z-Up** | Coordinate system where Z is vertical |
| **RAG** | Retrieval Augmented Generation |
| **ChromaDB** | Vector database for similarity search |
| **LangSmith** | LangChain's observability and evaluation platform |
| **Trace** | Recorded execution path of LLM calls |
| **Evaluator** | Function that scores LLM output quality |
| **Dataset** | Collection of test examples for evaluation |

---

## Additional Resources

- **LangGraph Docs:** https://langchain-ai.github.io/langgraph/
- **LangChain Docs:** https://python.langchain.com/
- **LangSmith Docs:** https://docs.smith.langchain.com/
- **LangSmith Dashboard:** https://smith.langchain.com/
- **FastAPI Docs:** https://fastapi.tiangolo.com/
- **Groq API:** https://console.groq.com/docs
- **PBR Guide:** https://marmoset.co/posts/basic-theory-of-physically-based-rendering/

---

Happy learning! 🎓
