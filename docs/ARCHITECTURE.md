# Moo Director - Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER INTERFACE                                  │
│                         (Browser - localhost:3000)                          │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 │ HTTPS/HTTP
                                 │
┌────────────────────────────────▼────────────────────────────────────────────┐
│                            FRONTEND (React + TypeScript)                     │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                        React Application                            │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │    │
│  │  │   Header     │  │ PromptInput  │  │ SceneDisplay │            │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘            │    │
│  │                             │                   │                   │    │
│  │         ┌───────────────────┴───────────────────┘                   │    │
│  │         │                                                            │    │
│  │  ┌──────▼───────┐                                                   │    │
│  │  │    Zustand   │  ┌──────────────┐                                │    │
│  │  │    Store     │──│  API Client  │                                │    │
│  │  │  (useStore)  │  │   (Axios)    │                                │    │
│  │  └──────────────┘  └──────┬───────┘                                │    │
│  └───────────────────────────┼────────────────────────────────────────┘    │
└──────────────────────────────┼──────────────────────────────────────────────┘
                               │
                               │ REST API (JSON)
                               │
┌──────────────────────────────▼──────────────────────────────────────────────┐
│                            BACKEND (FastAPI + LangGraph)                     │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                       FastAPI Application                           │    │
│  │  ┌──────────────────────────────────────────────────────────┐     │    │
│  │  │                    API Endpoints                          │     │    │
│  │  │  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐ │     │    │
│  │  │  │ /scene/create │  │   /agents    │  │    /health     │ │     │    │
│  │  │  └──────────────┘  └──────────────┘  └────────────────┘ │     │    │
│  │  └────────────┬──────────────────────────────────────────────┘     │    │
│  │               │                                                     │    │
│  │  ┌────────────▼─────────────────────────────────────────────────┐ │    │
│  │  │               LangGraph Workflow Engine                       │ │    │
│  │  │  ┌─────────────────────────────────────────────────────────┐│ │    │
│  │  │  │                    State Graph                          ││ │    │
│  │  │  │                                                         ││ │    │
│  │  │  │  ┌───────────┐    ┌───────────┐    ┌───────────┐      ││ │    │
│  │  │  │  │Orchestrator│───▶│ Librarian │───▶│ Architect │      ││ │    │
│  │  │  │  └───────────┘    └───────────┘    └─────┬─────┘      ││ │    │
│  │  │  │        ▲                                  │            ││ │    │
│  │  │  │        │                                  ▼            ││ │    │
│  │  │  │  ┌─────┴─────┐    ┌───────────┐    ┌───────────┐      ││ │    │
│  │  │  │  │  Critic   │◀───│Cinemato-  │◀───│ Material  │      ││ │    │
│  │  │  │  │           │    │  grapher  │    │ Scientist │      ││ │    │
│  │  │  │  └───────────┘    └───────────┘    └───────────┘      ││ │    │
│  │  │  └─────────────────────────────────────────────────────────┘│ │    │
│  │  └──────────────────────────────────────────────────────────────┘ │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────┬──────────────────────────────────────────────┘
                               │
                               │ HTTPS API
                               │
┌──────────────────────────────▼──────────────────────────────────────────────┐
│                          GROQ API (LLM Provider)                             │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                    Meta LLaMA Models (Groq-hosted)                  │    │
│  │                                                                      │    │
│  │  • LLaMA 3.3 70B (280 t/s) - Primary model                         │    │
│  │  • LLaMA 3.1 8B (560 t/s) - Fast fallback                          │    │
│  │  • Ultra-Fast Inference (Groq infrastructure)                       │    │
│  │  • 131K Token Context Window                                        │    │
│  └────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘

                               │ Traces (optional)
                               │
┌──────────────────────────────▼──────────────────────────────────────────────┐
│                          LANGSMITH (Observability)                           │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                   LangSmith Cloud (Optional)                        │    │
│  │                                                                      │    │
│  │  • Automatic LangChain/LangGraph tracing                           │    │
│  │  • Workflow visualization                                           │    │
│  │  • Token usage & latency metrics                                    │    │
│  │  • Evaluation datasets & custom evaluators                          │    │
│  └────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Multi-Agent Workflow

```
                              User Prompt
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ORCHESTRATOR (Lead Art Director)                     │
│  • Interprets user request                                                   │
│  • Creates Master Plan                                                       │
│  • Determines execution order                                                │
│  • Handles revision routing                                                  │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          LIBRARIAN (Asset Fetcher)                           │
│  • Searches asset library                                                    │
│  • Returns file paths & bounding boxes                                       │
│  • Checks polygon counts                                                     │
│  • Handles asset substitutions                                               │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ARCHITECT (Layout Artist)                          │
│  • Assigns X, Y, Z coordinates (Z-Up)                                        │
│  • Manages object hierarchy                                                  │
│  • Collision detection                                                       │
│  • Spatial relationships                                                     │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       MATERIAL SCIENTIST (Look-Dev Artist)                   │
│  • Applies PBR materials                                                     │
│  • Sets roughness, metallic, subsurface                                      │
│  • Assigns texture maps                                                      │
│  • Mood-based adjustments                                                    │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      CINEMATOGRAPHER (Lighting Director)                     │
│  • Sets up lighting (Sun, Area, HDRI)                                        │
│  • Configures camera (focal length, aperture)                                │
│  • Depth of field settings                                                   │
│  • Exposure control                                                          │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CRITIC (Quality Controller)                          │
│  • Collision detection                                                       │
│  • Floating object check                                                     │
│  • Material validation                                                       │
│  • Lighting validation                                                       │
│  • Prompt alignment check                                                    │
├─────────────────────────────────┴───────────────────────────────────────────┤
│                         │                              │                     │
│                    PASSED                          FAILED                    │
│                         │                              │                     │
│                         ▼                              ▼                     │
│                   Final Report              Route to Orchestrator            │
│                   + Scene Data              for Revision (loop)              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Data Flow

### Scene Creation Flow

```
User (Browser)
    │
    │ 1. Enter scene description
    ▼
PromptInput.tsx
    │
    │ 2. Submit prompt
    ▼
useStore (Zustand)
    │
    │ 3. Call API
    ▼
api/client.ts (Axios)
    │
    │ 4. POST /api/v1/scene/create
    ▼
FastAPI (routes.py)
    │
    │ 5. Initialize workflow
    ▼
LangGraph (graph.py)
    │
    │ 6. Execute agent pipeline
    ▼
┌─────────────────────────┐
│ Agent Processing Loop   │
│                         │
│ Orchestrator            │
│      ↓                  │
│ Librarian               │
│      ↓                  │
│ Architect               │
│      ↓                  │
│ Material Scientist      │
│      ↓                  │
│ Cinematographer         │
│      ↓                  │
│ Critic ──────┐          │
│      │       │          │
│      ▼       ▼          │
│   PASS    REVISION      │
│      │       │          │
│      │       └──→ Orchestrator (loop)
└──────┼──────────────────┘
       │
       │ 7. Return scene data
       ▼
routes.py
    │
    │ 8. Format response
    ▼
useStore
    │
    │ 9. Update state
    ▼
SceneDisplay.tsx
    │
    │ 10. Render results
    ▼
User sees scene
```

## State Management

### LangGraph State Structure

```
AgentState (TypedDict)
├── user_prompt: str
├── master_plan: MasterPlan
│   ├── original_prompt
│   ├── interpreted_mood
│   ├── required_objects
│   ├── spatial_requirements
│   ├── material_requirements
│   ├── lighting_requirements
│   └── execution_order
├── scene_objects: List[SceneObject]      ← REPLACES each iteration (not accumulated)
│   ├── id, name, asset_path
│   ├── position (x, y, z)
│   ├── rotation (x, y, z)
│   ├── scale (x, y, z)
│   ├── bounding_box
│   ├── material
│   └── status
├── lighting_setup: LightingSetup
│   ├── lights[]
│   ├── hdri_map
│   └── exposure
├── camera_setup: CameraSetup
│   ├── position, target
│   ├── focal_length
│   ├── aperture
│   └── depth_of_field
├── validation_issues: List[ValidationIssue]  ← REPLACES each iteration (not accumulated)
├── validation_passed: bool
├── workflow_status: WorkflowStatus
├── iteration_count: int
├── messages: List[Dict]                  ← Accumulated across iterations
├── errors: List[str]                     ← Accumulated across iterations
└── final_report: str
```

**State Reducers:**
- `scene_objects` and `validation_issues` are **replaced** each iteration to prevent exponential growth
- `messages` and `errors` are **accumulated** to maintain history

## Technology Layers

```
┌─────────────────────────────────────────────────────────────────┐
│                    Presentation Layer                            │
│  • React Components (TSX)                                        │
│  • CSS Styling (Dark Theme)                                      │
│  • Markdown Rendering (react-markdown + remark-gfm)              │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                    State Management Layer                        │
│  • Zustand Store                                                 │
│  • Scene data, loading states, errors                            │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                    API Communication Layer                       │
│  • Axios HTTP Client                                             │
│  • TypeScript type safety                                        │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          │ REST API
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                    API Gateway Layer                             │
│  • FastAPI Routes                                                │
│  • Request Validation (Pydantic)                                 │
│  • CORS Handling                                                 │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                    Orchestration Layer (LangGraph)               │
│  • StateGraph definition                                         │
│  • Conditional routing                                           │
│  • Checkpointing                                                 │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                    Agent Layer                                   │
│  • Orchestrator, Librarian, Architect                           │
│  • Material Scientist, Cinematographer, Critic                   │
│  • BaseAgent class with LLM integration                          │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                    LLM Integration Layer                         │
│  • LangChain + langchain-groq                                    │
│  • ChatGroq client                                               │
│  • Prompt templates                                              │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                    External AI Services                          │
│  • Groq API                                                      │
│  • LLaMA 3.3 70B (default)                                       │
│  • LLaMA 3.1 8B (fallback)                                       │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                    Observability Layer (Optional)                │
│  • LangSmith tracing                                             │
│  • Evaluation datasets & experiments                             │
│  • Custom evaluators (completeness, alignment, validation)       │
└─────────────────────────────────────────────────────────────────┘
```

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Internet                                 │
└────────────┬────────────────────────────┬───────────────────────┘
             │                            │
    ┌────────▼────────┐          ┌───────▼────────┐
    │  Vercel CDN     │          │   Fly.io       │
    │  (Frontend)     │          │   (Backend)    │
    │                 │          │                │
    │ • React App     │          │ • FastAPI      │
    │ • Static Files  │◀────────▶│ • LangGraph    │
    │ • Edge Network  │   API    │ • Docker       │
    └─────────────────┘  Calls   └───────┬────────┘
                                          │
                          ┌───────────────┼───────────────┐
                          │               │               │
                  ┌───────▼────────┐  ┌───▼───────────┐
                  │   Groq API     │  │  LangSmith    │
                  │   (External)   │  │  (Optional)   │
                  │                │  │               │
                  │ • LLaMA 3.3 70B│  │ • Tracing     │
                  │ • LLaMA 3.1 8B │  │ • Evaluation  │
                  └────────────────┘  └───────────────┘
```

---

## Recent Improvements

### State Management
- Scene objects and validation issues now **replace** each iteration instead of accumulating
- Prevents exponential growth during revision cycles
- Messages and errors still accumulate for history tracking

### Validation System
- **Passing score lowered** to 60 (from 80) for better MVP experience
- **Collision tolerance** of 5cm allows minor overlaps
- **Graduated penalties**: severe vs minor issues have different impact
- **Smarter categorization**: architectural elements (walls, floors) exempt from floating checks

### Placement Algorithm
- **Larger room** (6m × 6m) for better object spacing
- **Grid + spiral search** algorithm for optimal placement
- **Directional clipping resolution** - moves objects away from conflicts intelligently
- **Well-separated zones** to minimize initial collisions

### Material System
- **All presets include textures** - no flat colors
- **Fallback materials** have generic textures assigned
- Glass/metal exempted from texture requirements (appropriate for material type)

### Memory System
- **sentence-transformers optional** - system falls back gracefully
- **ChromaDB telemetry disabled** - cleaner console output

### Observability (LangSmith Integration)
- **Automatic tracing** - all LangChain/LangGraph operations traced
- **Custom metadata** - agent names and model info attached to traces
- **Evaluation datasets** - create datasets from production traces
- **Custom evaluators** - scene completeness, prompt alignment, validation pass, object count
- **Quick evaluation** - ad-hoc single prompt testing without datasets
- **Free tier friendly** - optional integration, works without API key

---

This architecture provides:
- ✅ Multi-agent collaboration with LangGraph
- ✅ Clear separation of concerns
- ✅ Scalable and extensible design
- ✅ Iterative refinement with Critic feedback loop
- ✅ Type-safe state management
- ✅ Modern deployment (Edge + Containers)
- ✅ Fast AI inference via Groq
- ✅ Production observability with LangSmith (optional)
- ✅ Automated quality evaluation framework
