# Agent-to-Agent Communication Architecture

This document explains how the 6 AI agents in the Moo Director system communicate and collaborate with each other.

## Overview

The agents in this system **don't communicate directly** with each other. Instead, they use a **shared state pattern** (also known as the "Blackboard Pattern") managed by LangGraph. Each agent:

1. **Reads** from the shared state
2. **Processes** its specific task
3. **Writes** updates back to the state
4. **Specifies** which agent should run next

## The Shared State Model

```
┌────────────────────────────────────────────────────────────────────────────┐
│                           SHARED STATE (AgentState)                        │
│                                                                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐       │
│  │ user_prompt │  │ master_plan │  │scene_objects│  │lighting_setup│       │
│  └─────────────┘  └─────────────┘  └─────────────┘  └──────────────┘       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐       │
│  │camera_setup │  │  validation │  │current_agent│  │   messages   │       │
│  └─────────────┘  └─────────────┘  └─────────────┘  └──────────────┘       │
└───────▲─────────────────▲─────────────────▲─────────────────▲──────────────┘
        │ READ            │ READ            │ READ            │ READ
        │ WRITE           │ WRITE           │ WRITE           │ WRITE
        │                 │                 │                 │
   ┌────┴────┐       ┌────┴────┐       ┌────┴────┐       ┌────┴────┐
   │Orchestr.│       │Librarian│       │Architect│       │  Critic │
   └─────────┘       └─────────┘       └─────────┘       └─────────┘
```

## AgentState Structure

The shared state is defined as a `TypedDict` in `backend/app/models/state.py`:

```python
class AgentState(TypedDict):
    # User input
    user_prompt: str
    
    # Master plan from Orchestrator
    master_plan: Optional[MasterPlan]
    
    # Scene objects (accumulated from Librarian and Architect)
    scene_objects: Annotated[List[SceneObject], operator.add]
    
    # Lighting and camera from Cinematographer
    lighting_setup: Optional[LightingSetup]
    camera_setup: Optional[CameraSetup]
    
    # Validation from Critic
    validation_issues: Annotated[List[ValidationIssue], operator.add]
    validation_passed: bool
    
    # Workflow tracking
    current_agent: str
    workflow_status: WorkflowStatus
    iteration_count: int
    max_iterations: int
    
    # Message history for context
    messages: Annotated[List[Dict[str, Any]], operator.add]
    
    # Error tracking
    errors: Annotated[List[str], operator.add]
    
    # Final output
    final_report: Optional[str]
```

### Reducer Functions

Note the `Annotated[List, operator.add]` syntax. This tells LangGraph how to merge updates:

| Field | Reducer | Behavior |
|-------|---------|----------|
| `scene_objects` | `operator.add` | New objects are **appended** to existing list |
| `validation_issues` | `operator.add` | New issues are **appended** |
| `messages` | `operator.add` | Messages accumulate |
| `errors` | `operator.add` | Errors accumulate |
| `master_plan` | None (replace) | New value **replaces** old |
| `lighting_setup` | None (replace) | New value **replaces** old |

---

## How Communication Works Step-by-Step

### Step 1: Initial State is Created

When a workflow starts, an initial state is created:

```python
initial_state: AgentState = {
    "user_prompt": "Create a cozy bedroom with a white bed...",
    "master_plan": None,
    "scene_objects": [],          # Empty - Librarian will fill
    "lighting_setup": None,       # Empty - Cinematographer will fill
    "camera_setup": None,
    "validation_issues": [],
    "validation_passed": False,
    "current_agent": "orchestrator",
    "workflow_status": WorkflowStatus.PENDING,
    "iteration_count": 0,
    "max_iterations": 3,
    "messages": [],
    "errors": [],
    "final_report": None
}
```

### Step 2: Each Agent Reads State, Processes, Returns Updates

Each agent's `process()` method:
1. Reads what it needs from the state
2. Does its work
3. Returns a dict with updates

```python
# Example: Orchestrator agent
async def process(self, state: AgentState) -> Dict[str, Any]:
    # READ from state
    user_prompt = state.get("user_prompt")
    
    # PROCESS - create master plan using LLM
    master_plan = self._create_master_plan(user_prompt)
    
    # RETURN updates (these will be merged into state)
    return {
        "master_plan": master_plan,
        "current_agent": "librarian",  # Who runs next
        "workflow_status": WorkflowStatus.IN_PROGRESS,
        "messages": [{
            "agent": "Orchestrator",
            "action": "created_master_plan",
            "content": f"Interpreted as '{master_plan.interpreted_mood}'"
        }]
    }
```

### Step 3: LangGraph Merges Updates Into State

After each agent runs, LangGraph merges the returned dict into the state:

```python
# Before: state["scene_objects"] = [obj1, obj2]
# Agent returns: {"scene_objects": [obj3]}
# After: state["scene_objects"] = [obj1, obj2, obj3]  # Appended due to reducer
```

### Step 4: Routing Determines Next Agent

The `current_agent` field controls which agent runs next:

```python
def route_standard(state: AgentState) -> str:
    next_agent = state.get("current_agent")
    
    if state.get("workflow_status") == WorkflowStatus.FAILED:
        return END
    
    return next_agent  # "librarian", "architect", etc.
```

---

## Data Flow Between Agents

### What Each Agent Writes

| Agent | Writes to State |
|-------|-----------------|
| **Orchestrator** | `master_plan`, `current_agent`, `workflow_status`, `messages` |
| **Librarian** | `scene_objects` (with asset_path, bounding_box), `current_agent`, `messages` |
| **Architect** | `scene_objects` (with position, rotation), `current_agent`, `messages` |
| **Material Scientist** | `scene_objects` (with material), `current_agent`, `messages` |
| **Cinematographer** | `lighting_setup`, `camera_setup`, `current_agent`, `messages` |
| **Critic** | `validation_issues`, `validation_passed`, `workflow_status`, `final_report` |

### What Each Agent Reads

| Agent | Reads from State |
|-------|------------------|
| **Orchestrator** | `user_prompt`, `validation_issues` (on revision) |
| **Librarian** | `master_plan.required_objects` |
| **Architect** | `scene_objects` (bounding boxes), `master_plan.spatial_requirements` |
| **Material Scientist** | `scene_objects`, `master_plan.material_requirements`, `master_plan.interpreted_mood` |
| **Cinematographer** | `scene_objects`, `master_plan.lighting_requirements`, `master_plan.interpreted_mood` |
| **Critic** | `scene_objects`, `lighting_setup`, `camera_setup`, `master_plan` |

---

## Detailed Communication Examples

### Example 1: Orchestrator → Librarian

**Orchestrator writes:**
```python
{
    "master_plan": MasterPlan(
        original_prompt="Create a cozy bedroom...",
        interpreted_mood="cozy, warm, intimate",
        required_objects=["bed", "desk", "lamp"],
        material_requirements={"bed": {"style": "fabric", "finish": "soft"}},
        lighting_requirements={"time_of_day": "morning", "mood": "warm"},
        execution_order=["librarian", "architect", "material_scientist", "cinematographer"]
    ),
    "current_agent": "librarian"
}
```

**Librarian reads:**
```python
master_plan = state.get("master_plan")
required_objects = master_plan.required_objects  # ["bed", "desk", "lamp"]
```

### Example 2: Librarian → Architect

**Librarian writes:**
```python
{
    "scene_objects": [
        SceneObject(
            id="uuid-123",
            name="bed",
            asset_path="/library/furniture/beds/white_bed.blend",
            bounding_box=BoundingBox(width=2.0, depth=1.8, height=0.9),
            polygon_count=25000,
            status="fetched"
        ),
        SceneObject(
            id="uuid-456",
            name="desk",
            asset_path="/library/furniture/desks/oak_desk.blend",
            bounding_box=BoundingBox(width=1.4, depth=0.7, height=0.75),
            polygon_count=12000,
            status="fetched"
        )
    ],
    "current_agent": "architect"
}
```

**Architect reads:**
```python
scene_objects = state.get("scene_objects")
for obj in scene_objects:
    # Use bounding_box to calculate non-clipping positions
    width = obj.bounding_box.width
    depth = obj.bounding_box.depth
    # ... calculate position ...
```

### Example 3: Architect → Material Scientist

**Architect writes (updates existing objects):**
```python
{
    "scene_objects": [
        # Same objects but with positions added
        SceneObject(
            id="uuid-123",
            name="bed",
            position=Coordinate3D(x=0.0, y=1.95, z=0.0),
            rotation=Coordinate3D(x=0, y=0, z=0),
            status="placed"
            # ... other fields ...
        )
    ],
    "current_agent": "material_scientist"
}
```

**Material Scientist reads:**
```python
scene_objects = state.get("scene_objects")
master_plan = state.get("master_plan")
mood = master_plan.interpreted_mood  # "cozy, warm"

for obj in scene_objects:
    # Apply materials based on object type and mood
    material = self._select_material(obj, mood)
```

### Example 4: Critic → Orchestrator (Revision Loop)

**Critic finds issues and writes:**
```python
{
    "validation_issues": [
        ValidationIssue(
            severity="error",
            category="clipping",
            description="'desk' intersects with 'bed'",
            affected_object_id="uuid-456",
            suggested_fix="Move desk 0.5m to the left"
        )
    ],
    "validation_passed": False,
    "workflow_status": WorkflowStatus.REVISION,
    "current_agent": "orchestrator"  # Route back for revision
}
```

**Orchestrator reads (on revision):**
```python
validation_issues = state.get("validation_issues")
workflow_status = state.get("workflow_status")

if workflow_status == WorkflowStatus.REVISION:
    # Analyze issues and determine which agent should fix them
    for issue in validation_issues:
        if issue.category == "clipping":
            return {"current_agent": "architect"}  # Send to Architect to fix
```

---

## The Revision Loop

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Normal Flow                                     │
│                                                                              │
│  Orchestrator → Librarian → Architect → Material Scientist → Cinematographer│
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                                                      │
                                                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                                CRITIC                                        │
│                                                                              │
│  Validates: Clipping? Floating? Materials? Lighting? Prompt alignment?      │
│                                                                              │
├─────────────────────────────────┬───────────────────────────────────────────┤
│           PASS                  │                 FAIL                       │
│             │                   │                   │                        │
│             ▼                   │                   ▼                        │
│      Final Report               │           Set: workflow_status=REVISION    │
│      + Scene Data               │           Set: current_agent=orchestrator  │
│             │                   │                   │                        │
│             ▼                   │                   ▼                        │
│           END                   │            ORCHESTRATOR                    │
│                                 │                   │                        │
│                                 │   Reads validation_issues                  │
│                                 │   Determines which agent to route to       │
│                                 │                   │                        │
│                                 │                   ▼                        │
│                                 │         (Architect, Material Scientist,    │
│                                 │          or Cinematographer)               │
│                                 │                   │                        │
│                                 │                   └──────────────┐         │
│                                 │                                  │         │
│                                 │                   ... fix issue ...        │
│                                 │                                  │         │
│                                 │                                  ▼         │
│                                 │                              CRITIC        │
│                                 │                        (validate again)    │
└─────────────────────────────────┴───────────────────────────────────────────┘
```

### Revision Routing Logic

The Orchestrator determines which agent should fix issues based on category:

| Issue Category | Target Agent |
|----------------|--------------|
| `clipping`, `floating`, `placement` | Architect |
| `material`, `texture`, `color` | Material Scientist |
| `lighting`, `exposure`, `camera` | Cinematographer |
| `missing_asset` | Librarian |

---

## Key Design Principles

### 1. No Direct Agent-to-Agent Calls

Agents never call each other. All communication goes through the shared state.

```python
# ❌ WRONG - Agents don't do this
architect_result = librarian.call_architect(objects)

# ✅ CORRECT - Agent returns state updates
return {"scene_objects": objects, "current_agent": "architect"}
```

### 2. Immutable Processing Pattern

Each agent reads state and returns updates without mutating the original:

```python
async def process(self, state: AgentState) -> Dict[str, Any]:
    # Read (don't mutate state directly)
    objects = state.get("scene_objects")
    
    # Process and create new data
    updated_objects = self._place_objects(objects)
    
    # Return updates (LangGraph handles merging)
    return {"scene_objects": updated_objects}
```

### 3. Explicit Routing via State

The `current_agent` field is the "address" for routing:

```python
# Each agent explicitly says who runs next
return {
    "current_agent": "material_scientist",  # Explicit routing
    ...
}
```

### 4. Accumulator Fields for Lists

Using `Annotated[List, operator.add]` prevents data loss:

```python
# Without reducer: Architect's objects would REPLACE Librarian's
# With reducer: Architect's objects are APPENDED to Librarian's
scene_objects: Annotated[List[SceneObject], operator.add]
```

### 5. Single Source of Truth

All data lives in `AgentState`. Agents don't have internal state that persists between calls.

---

## Benefits of This Architecture

| Benefit | Description |
|---------|-------------|
| **Debuggability** | Inspect state at any point to see exactly what each agent contributed |
| **Testability** | Test agents in isolation by mocking the state |
| **Extensibility** | Add new agents by adding a node and routing edges |
| **Resumability** | Checkpoint state and resume from any point |
| **Traceability** | The `messages` field logs every agent action |
| **Decoupling** | Agents don't know about each other, only about the state schema |

---

## File References

| File | Purpose |
|------|---------|
| `backend/app/models/state.py` | `AgentState` TypedDict definition |
| `backend/app/workflow/graph.py` | LangGraph workflow and routing |
| `backend/app/agents/base.py` | Base agent class |
| `backend/app/agents/*.py` | Individual agent implementations |

---

## See Also

- [AGENTS.md](AGENTS.md) - Detailed documentation for each agent
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture diagrams
- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - File structure overview
