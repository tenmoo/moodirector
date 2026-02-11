# Moo Director - Project Structure

Complete overview of the project structure and files.

## Directory Tree

```
moo-director/
├── backend/                        # FastAPI + LangGraph backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py              # Application configuration
│   │   ├── agents/                # Multi-agent implementations
│   │   │   ├── __init__.py
│   │   │   ├── base.py            # BaseAgent class
│   │   │   ├── orchestrator.py    # Lead Art Director agent
│   │   │   ├── librarian.py       # Asset fetching agent
│   │   │   ├── architect.py       # Spatial layout agent
│   │   │   ├── material_scientist.py  # PBR materials agent
│   │   │   ├── cinematographer.py # Lighting/camera agent
│   │   │   └── critic.py          # Quality validation agent
│   │   ├── api/                   # FastAPI routes
│   │   │   ├── __init__.py
│   │   │   └── routes.py          # API endpoints
│   │   ├── models/                # Pydantic data models
│   │   │   ├── __init__.py
│   │   │   ├── state.py           # LangGraph state models
│   │   │   └── messages.py        # Request/response models
│   │   ├── evaluation/            # LangSmith evaluation module
│   │   │   ├── __init__.py
│   │   │   ├── evaluator.py       # Dataset & evaluation functions
│   │   │   └── custom_evaluators.py  # Custom quality evaluators
│   │   └── workflow/              # LangGraph workflow
│   │       ├── __init__.py
│   │       └── graph.py           # Workflow graph definition
│   ├── main.py                    # FastAPI application entry
│   ├── requirements.txt           # Python dependencies
│   ├── .env.example              # Environment template
│   └── Dockerfile                # Docker configuration
│
├── frontend/                      # React + TypeScript frontend
│   ├── src/
│   │   ├── api/
│   │   │   └── client.ts         # Axios API client
│   │   ├── components/
│   │   │   ├── Header.tsx        # App header
│   │   │   ├── PromptInput.tsx   # Scene prompt input
│   │   │   ├── SceneDisplay.tsx  # Scene results display
│   │   │   └── AgentPanel.tsx    # Agent information panel
│   │   ├── store/
│   │   │   └── useStore.ts       # Zustand state management
│   │   ├── styles/
│   │   │   └── index.css         # Global styles (dark theme)
│   │   ├── types/
│   │   │   └── index.ts          # TypeScript type definitions
│   │   ├── App.tsx               # Main app component
│   │   └── main.tsx              # Application entry point
│   ├── index.html                # HTML template
│   ├── package.json              # Node.js dependencies
│   ├── tsconfig.json             # TypeScript configuration
│   ├── tsconfig.node.json        # TypeScript Node config
│   └── vite.config.ts            # Vite build configuration
│
├── docs/                          # Documentation
│   ├── prd.md                    # Product requirements
│   ├── ARCHITECTURE.md           # Architecture diagrams
│   ├── API.md                    # API documentation
│   ├── GETTING_STARTED.md        # Setup guide
│   ├── PROJECT_STRUCTURE.md      # This file
│   ├── AGENTS.md                 # Agent documentation
│   ├── LANGSMITH.md              # Observability & evaluation guide
│   ├── DEPLOYMENT.md             # Deployment guide
│   └── QUICK_REFERENCE.md        # Quick commands
│
└── README.md                      # Main project documentation
```

## File Descriptions

### Backend Files

#### `app/config.py`
Application configuration using Pydantic Settings:
- Environment variable loading
- Groq API key management
- JWT configuration
- Server settings

#### `app/agents/base.py`
Abstract base class for all agents:
- LLM initialization with Groq
- Prompt template setup
- Common utility methods
- State context formatting

#### `app/agents/orchestrator.py`
Lead Art Director agent:
- Request decomposition
- Master plan creation
- Agent coordination
- Revision handling

#### `app/agents/librarian.py`
Asset fetching agent:
- Asset library searching
- Bounding box retrieval
- Polygon count validation
- Asset substitution handling

#### `app/agents/architect.py`
Spatial layout agent:
- Z-Up coordinate system
- Object placement algorithms
- Collision detection
- Parent-child relationships

#### `app/agents/material_scientist.py`
PBR materials agent:
- Material preset library
- Shader type selection
- Mood-based adjustments
- Texture map assignment

#### `app/agents/cinematographer.py`
Lighting and camera agent:
- Lighting preset library
- Time-of-day adjustments
- Camera composition
- Depth of field settings

#### `app/agents/critic.py`
Quality validation agent:
- Collision checking
- Floating object detection
- Material validation
- Lighting validation
- Prompt alignment checking

#### `app/models/state.py`
LangGraph state definitions:
- `AgentState` TypedDict
- `SceneObject` model
- `Material` model
- `LightingSetup` model
- `CameraSetup` model
- `ValidationIssue` model

#### `app/models/messages.py`
API request/response models:
- `SceneRequest`
- `SceneResponse`
- `JobStatus`
- `TaskMessage`

#### `app/workflow/graph.py`
LangGraph workflow definition:
- StateGraph configuration
- Agent node functions
- Conditional routing
- Workflow compilation

#### `app/evaluation/evaluator.py`
LangSmith evaluation functions:
- Dataset creation in LangSmith
- Batch evaluation runs
- Result retrieval
- Quick single-prompt evaluation

#### `app/evaluation/custom_evaluators.py`
Custom quality evaluators:
- `scene_completeness_evaluator` - Object presence validation
- `prompt_alignment_evaluator` - Keyword matching
- `validation_pass_evaluator` - Internal validation check
- `object_count_evaluator` - Object count validation

#### `app/api/routes.py`
FastAPI endpoints:
- `/scene/create` - Sync scene creation
- `/scene/create-async` - Async scene creation
- `/scene/status/{job_id}` - Job status
- `/agents` - Agent information
- `/health` - Health check
- `/evaluation/datasets/create` - Create eval dataset
- `/evaluation/datasets` - List datasets
- `/evaluation/run` - Run batch evaluation
- `/evaluation/results` - Get evaluation results
- `/evaluation/quick` - Quick single-prompt eval

#### `main.py`
FastAPI application entry:
- App initialization
- CORS middleware
- Router inclusion
- Startup/shutdown events

### Frontend Files

#### `src/api/client.ts`
Axios-based API client:
- `createScene()` - Create scene
- `createSceneAsync()` - Async creation
- `getJobStatus()` - Check job status
- `listAgents()` - Get agent info
- `healthCheck()` - Health check

#### `src/components/PromptInput.tsx`
Scene prompt input component:
- Textarea for prompt
- Max iterations selector
- Submit button with loading state
- Keyboard shortcut (Cmd+Enter)

#### `src/components/SceneDisplay.tsx`
Scene results display:
- Object cards with position/material
- Lighting info panel
- Camera info panel
- Validation issues list
- Final report (Markdown rendered)

#### `src/components/AgentPanel.tsx`
Agent information sidebar:
- Agent cards with role/description
- Workflow visualization

#### `src/store/useStore.ts`
Zustand state management:
- `currentScene` - Scene response data
- `isLoading` - Loading state
- `error` - Error messages
- `agents` - Agent list
- `promptHistory` - Recent prompts

#### `src/types/index.ts`
TypeScript type definitions:
- All API response types
- Scene object interfaces
- Material/lighting interfaces
- Validation issue types

#### `src/styles/index.css`
Global CSS styles:
- CSS custom properties (variables)
- Dark theme colors
- Component styles
- Responsive layout

### Configuration Files

#### `backend/requirements.txt`
Python dependencies:
```
fastapi==0.109.0
uvicorn[standard]==0.27.0
langgraph==0.2.0
langchain==0.2.16
langchain-groq==0.1.9
pydantic==2.5.3
python-dotenv==1.0.0
httpx==0.26.0
langsmith>=0.1.0
```

#### `frontend/package.json`
Node.js dependencies:
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "axios": "^1.6.0",
    "zustand": "^4.4.0",
    "react-markdown": "^9.0.0",
    "remark-gfm": "^4.0.0"
  }
}
```

#### `vite.config.ts`
Vite configuration:
- React plugin
- Dev server port (3000)
- API proxy to backend

## Key Architecture Patterns

### Multi-Agent Pattern
```
BaseAgent (Abstract)
    ├── OrchestratorAgent
    ├── LibrarianAgent
    ├── ArchitectAgent
    ├── MaterialScientistAgent
    ├── CinematographerAgent
    └── CriticAgent
```

### State Management Pattern
```
AgentState (Shared State)
    ├── user_prompt
    ├── master_plan
    ├── scene_objects (accumulator)
    ├── lighting_setup
    ├── camera_setup
    ├── validation_issues (accumulator)
    └── workflow_status
```

### Workflow Pattern
```
Entry Point
    └── Orchestrator
            └── Librarian
                    └── Architect
                            └── Material Scientist
                                    └── Cinematographer
                                            └── Critic
                                                ├── PASS → END
                                                └── FAIL → Orchestrator (loop)
```

## Environment Variables

### Backend (`.env`)
```env
# Required
GROQ_API_KEY=xxx              # Groq API key
SECRET_KEY=xxx                # JWT secret

# Optional: JWT Settings
ALGORITHM=HS256               # JWT algorithm
ACCESS_TOKEN_EXPIRE_MINUTES=30 # Token expiration

# Optional: LLM Settings
DEFAULT_MODEL=llama-3.3-70b-versatile  # LLM model
FALLBACK_MODEL=llama-3.1-8b-instant    # Fallback model

# Optional: Server Settings
HOST=0.0.0.0                  # Server host
PORT=8000                     # Server port
DEBUG=true                    # Debug mode

# Optional: LangSmith Observability
LANGCHAIN_TRACING_V2=true     # Enable tracing
LANGCHAIN_API_KEY=xxx         # LangSmith API key
LANGCHAIN_PROJECT=moo-director  # Project name
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com  # API endpoint
```

## Development Workflow

1. **Start Backend**:
   ```bash
   cd backend
   source venv/bin/activate
   python main.py
   ```

2. **Start Frontend**:
   ```bash
   cd frontend
   npm run dev
   ```

3. **Test API**:
   - Visit http://localhost:8000/docs

4. **View App**:
   - Visit http://localhost:3000

## Adding New Features

### Adding a New Agent

1. Create `app/agents/new_agent.py`:
   ```python
   from .base import BaseAgent
   
   class NewAgent(BaseAgent):
       def __init__(self):
           super().__init__(
               name="New Agent",
               description="...",
               system_prompt="..."
           )
       
       async def process(self, state: AgentState) -> Dict:
           # Implementation
           pass
   ```

2. Register in `app/agents/__init__.py`

3. Add node in `app/workflow/graph.py`:
   ```python
   workflow.add_node("new_agent", new_agent_node)
   ```

4. Add routing edges

### Adding a New API Endpoint

1. Add route in `app/api/routes.py`:
   ```python
   @router.post("/new-endpoint")
   async def new_endpoint(request: NewRequest):
       # Implementation
       pass
   ```

2. Add TypeScript types in `frontend/src/types/index.ts`

3. Add API method in `frontend/src/api/client.ts`

## Notes

- **LangGraph State**: Uses TypedDict with Annotated reducers for state accumulation
- **Async Processing**: All agents use async/await for non-blocking execution
- **Type Safety**: Full TypeScript coverage in frontend, Pydantic models in backend
- **Dark Theme**: CSS custom properties for consistent theming
