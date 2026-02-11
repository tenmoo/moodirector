# Changelog

All notable changes to the Moo Director project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-01-31

### Added

#### Multi-Agent System
- **Orchestrator Agent**: Lead Art Director that decomposes requests and coordinates all other agents
- **Librarian Agent**: Asset fetcher with simulated 3D asset library
- **Architect Agent**: Spatial layout with Z-Up coordinate system and collision detection
- **Material Scientist Agent**: PBR material application with mood-based adjustments
- **Cinematographer Agent**: Lighting and camera setup with presets
- **Critic Agent**: Quality validation with iterative refinement loop

#### Backend (FastAPI + LangGraph)
- LangGraph workflow with StateGraph for multi-agent orchestration
- Conditional routing between agents
- Revision loop when Critic finds issues
- Async scene creation with job tracking
- RESTful API endpoints:
  - `POST /api/v1/scene/create` - Synchronous scene creation
  - `POST /api/v1/scene/create-async` - Asynchronous scene creation
  - `GET /api/v1/scene/status/{job_id}` - Job status polling
  - `GET /api/v1/agents` - Agent information
  - `GET /api/v1/health` - Health check

#### Frontend (React + TypeScript)
- Modern dark theme UI (colors from PRD)
- Scene prompt input with max iterations selector
- Scene display with object cards, lighting/camera info
- Validation report with issues and recommendations
- Final report rendered as Markdown
- Agent panel showing workflow
- Zustand state management
- Axios API client with TypeScript types

#### State Management
- `AgentState` TypedDict with annotated reducers
- `SceneObject` model with position, rotation, material
- `Material` model with PBR properties
- `LightingSetup` and `CameraSetup` models
- `ValidationIssue` model with severity levels

#### Documentation
- `ARCHITECTURE.md` - System architecture diagrams
- `API.md` - Complete API reference
- `GETTING_STARTED.md` - Setup guide
- `PROJECT_STRUCTURE.md` - File structure overview
- `AGENTS.md` - Detailed agent documentation
- `DEPLOYMENT.md` - Production deployment guide
- `QUICK_REFERENCE.md` - Quick commands
- `CHANGELOG.md` - This file

### Technical Details

#### LLM Integration
- Groq API with LLaMA 3.3 70B (default)
- LLaMA 3.1 8B (fallback)
- LangChain + langchain-groq integration
- System prompts for each agent role

#### Asset Library
- Simulated asset library with categories:
  - Furniture (beds, desks, chairs)
  - Lighting (lamps)
  - Storage (bookshelves)
  - Decor (plants, rugs, curtains, books)
- Bounding box and polygon count data

#### Material Presets
- Cloth (fabric, bedding)
- Wood (furniture)
- Metal (fixtures)
- Glass (windows)
- Plastic (modern furniture)

#### Lighting Presets
- Warm morning
- Cool evening
- Dramatic
- Soft diffuse
- Cozy
- Neutral

#### Validation Checks
- Collision detection (clipping)
- Floating object detection
- Material validation (no flat colors)
- Lighting validation
- Prompt alignment

---

## [1.1.0] - 2026-02-06

### Added

#### LangSmith Integration (Observability & Evaluation)
- **Automatic Tracing**: All LangChain/LangGraph operations automatically traced when configured
- **Custom Metadata**: Agent names and model info attached to traces for filtering
- **Evaluation Module**: New `backend/app/evaluation/` module with:
  - Dataset creation helpers for scene validation
  - Custom evaluators for scene quality assessment
  - Quick evaluation for ad-hoc testing

#### Custom Evaluators
- `scene_completeness_evaluator` - Checks if all requested objects are present
- `prompt_alignment_evaluator` - Checks if output matches prompt keywords
- `validation_pass_evaluator` - Checks if scene passed internal validation
- `object_count_evaluator` - Checks if object count is reasonable

#### New API Endpoints
- `POST /api/v1/evaluation/datasets/create` - Create evaluation datasets in LangSmith
- `GET /api/v1/evaluation/datasets` - List all evaluation datasets
- `POST /api/v1/evaluation/run` - Run batch evaluations against datasets
- `GET /api/v1/evaluation/results` - Get evaluation results
- `POST /api/v1/evaluation/quick` - Quick single-prompt evaluation (no LangSmith required)

#### Configuration
- New environment variables:
  - `LANGCHAIN_TRACING_V2` - Enable/disable tracing
  - `LANGCHAIN_API_KEY` - LangSmith API key
  - `LANGCHAIN_PROJECT` - Project name in LangSmith
  - `LANGCHAIN_ENDPOINT` - LangSmith API endpoint

### Changed
- Updated `BaseAgent.invoke_llm()` with `@traceable` decorator for better trace organization
- Added agent metadata and tags to LLM invocations

### Documentation
- Added `LANGSMITH.md` - Complete guide for observability and evaluation
- Updated `GETTING_STARTED.md` with LangSmith setup instructions
- Updated `API.md` with evaluation endpoint documentation
- Updated `ARCHITECTURE.md` with LangSmith in architecture diagrams

---

## [Unreleased]

### Planned Features
- Real 3D asset library integration
- User authentication
- Scene persistence (database)
- Export to Blender/USD format
- Real-time 3D preview
- Collaborative editing
- Custom agent prompts via UI
