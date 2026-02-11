# Moo Director - Product Requirements Document

## 1. Executive Summary

Moo Director is a multi-agent AI assistant for 3D workflow automation that enables users to create 3D scenes from natural language descriptions. Using a team of 6 specialized AI agents (Orchestrator, Librarian, Architect, Material Scientist, Cinematographer, and Critic), the system decomposes complex requests and collaboratively builds scenes with proper asset placement, PBR materials, lighting, and camera setup.

**Current Status**: ✅ **MVP Completed**

## 2. Problem Statement

3D artists and designers face significant challenges when creating scenes:
- Manual asset sourcing is time-consuming and tedious
- Spatial arrangement requires constant adjustments to avoid clipping
- Material assignment and texturing is repetitive
- Lighting setup requires technical expertise
- Quality validation is often missed until render time
- Coordinating all these tasks requires significant expertise and time

## 3. Product Vision

Create a multi-agent, agentic workflow automation system that helps guide users through 3D scene creation by:
- Understanding natural language scene descriptions
- Automatically sourcing appropriate 3D assets
- Placing objects with correct spatial relationships
- Applying physically-based materials
- Setting up mood-appropriate lighting and camera
- Validating quality and iterating until requirements are met

## 4. Target Users

### Primary Users
- **3D Artists** looking to accelerate scene creation workflows
- **Designers** who need quick 3D mockups without deep technical knowledge
- **Game Developers** wanting rapid environment prototyping
- **Visualization Studios** seeking to automate repetitive scene setup tasks

### User Personas
- **Time-Pressed Artist**: Needs to create multiple scene variations quickly
- **Non-Technical Designer**: Wants 3D output without learning complex software
- **Technical Director**: Looking to automate team's repetitive workflows

## 5. Core Features

### 5.1 Multi-Agent System ✅ **IMPLEMENTED**

The system consists of 6 specialized AI agents that collaborate:

#### 1. The Orchestrator (The Manager)
- **Primary Responsibility**: Decomposition & Coordination
- **Specific Actions**:
  - Translates natural language into structured project briefs
  - Decides the order of operations
  - Routes data between agents
  - Synthesizes final reports for the user
  - Handles revision requests from the Critic
- **System Prompt**: "You are the Lead Art Director. Your role is to break down a 3D scene request into JSON tasks for a Librarian, Architect, Material Scientist, and Cinematographer. Do not perform the tasks yourself. Only coordinate. If the Critic Agent finds a 'clipping' error, send a correction command back to the Architect immediately."

#### 2. The Scene Architect (The Layout Artist)
- **Primary Responsibility**: Spatial Logic & Object Hierarchy
- **Specific Actions**:
  - Assigns X, Y, Z coordinates to every object (Z-Up system)
  - Ensures spatial relationships (desk facing window)
  - Manages Parent-Child relationships
  - Prevents mesh clipping with collision detection
- **Math Tool**: Coordinate_System(Z=Up) for all calculations
- **System Prompt**: "You are a 3D Layout Engineer. You receive model dimensions from the Librarian. Your task is to output x, y, z coordinates. Place the bed against the primary wall and the desk within 2 meters of a window. Ensure no two meshes occupy the same space (No Clipping)."

#### 3. The Asset Librarian (The Fetcher)
- **Primary Responsibility**: Sourcing & Compatibility
- **Specific Actions**:
  - Searches for assets matching requested style
  - Returns file paths and bounding box dimensions
  - Checks polygon counts (max 500K per asset)
  - Suggests substitutions when exact match unavailable
- **Constraint**: Never download 'Heavy' assets that crash the render engine
- **System Prompt**: "You are an expert 3D Asset Librarian. Your goal is to find models that match the user's aesthetic. For every object requested, return the file path and bounding box dimensions. If a model is not found, suggest the closest visual match and flag it for the Material Scientist."

#### 4. The Material Scientist (The Look-Dev Artist)
- **Primary Responsibility**: Surface Physics & Texturing
- **Specific Actions**:
  - Applies PBR (Physically Based Rendering) materials
  - Sets roughness, metallic, and subsurface scattering
  - Ensures realistic appearance (fabric looks like fabric, not plastic)
  - Adjusts materials based on scene mood
- **Constraint**: Do not use 'Flat' colors; everything must have a texture map
- **System Prompt**: "You are a Look-Dev Specialist. You apply PBR shaders. For 'White Bed,' use a Cloth shader with high roughness. For 'Wooden Desk,' use an Oak texture with a clear coat of 0.1. Ensure all textures are mapped to UV coordinates."

#### 5. The Cinematographer (The Lighting Director)
- **Primary Responsibility**: Atmosphere & Camera
- **Specific Actions**:
  - Creates mood-appropriate lighting (HDRI maps, Sun Lamps, Area Lights)
  - Sets camera lens (focal length, aperture)
  - Configures depth of field
  - Controls exposure settings
- **System Prompt**: "You are a Lighting Director. Your goal is 'Warm Morning.' Set a Sun Lamp at a 20-degree angle with a color temperature of 3500K. Add a soft Area Light near the window to simulate bounce light. Set the Camera to 35mm at f/2.8 for a shallow depth of field."

#### 6. The Critic Agent (The Quality Controller)
- **Primary Responsibility**: Validation & Error Detection
- **Specific Actions**:
  - Collision Detection: Checks for floating or clipping objects
  - Prompt Alignment: Verifies scene matches request
  - Technical Check: Identifies overexposure, render artifacts
  - Material Check: Ensures no flat colors
- **System Prompt**: "You are a ruthless 3D Quality Controller. You check the work of the other agents. You analyze the Architect's coordinates for clipping and the Cinematographer's render for overexposure. If the Bed's white value exceeds 95% brightness, reject it and request a lighting adjustment. Look for 'floating' objects."

### 5.2 Workflow Architecture ✅ **IMPLEMENTED**

```
User Prompt
    ↓
┌─────────────────────────────────────┐
│ 1. ORCHESTRATOR (The Brain)         │
│    Interprets request, creates plan │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 2. LIBRARIAN (Asset Fetcher)        │
│    Finds and returns 3D assets      │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 3. ARCHITECT (Layout Artist)        │
│    Places objects in 3D space       │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 4. MATERIAL SCIENTIST (Look-Dev)    │
│    Applies PBR materials            │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 5. CINEMATOGRAPHER (Lighting)       │
│    Sets up lights and camera        │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 6. CRITIC (Quality Control)         │
│    Validates and scores scene       │
├─────────────────────────────────────┤
│ PASS → Final Report                 │
│ FAIL → Back to Orchestrator (loop)  │
└─────────────────────────────────────┘
```

### 5.3 LangGraph Integration ✅ **IMPLEMENTED**
- StateGraph for workflow orchestration
- Conditional routing between agents
- Iterative refinement with revision loop
- Checkpointing support for resumable workflows
- Max iteration limits to prevent infinite loops

### 5.4 Vector Memory (RAG) ✅ **IMPLEMENTED**
- ChromaDB for vector storage
- Sentence-transformers for embeddings (all-MiniLM-L6-v2)
- Automatic scene storage after completion
- Semantic search for similar past scenes
- Orchestrator uses memory context for better planning
- Persistent storage across restarts

### 5.5 Modern Web Interface ✅ **IMPLEMENTED**
- Responsive dark theme design
- Real-time scene creation feedback
- Object cards with position and material info
- Lighting and camera configuration display
- Validation report with issues and recommendations
- Markdown-rendered final reports
- Agent team panel showing workflow

## 6. User Experience & Interface

### 6.1 Interface Components ✅ **IMPLEMENTED**
- **Header**: Application title and branding
- **Prompt Input**: Text area for scene description
- **Scene Display**: Results with objects, lighting, camera info
- **Validation Report**: Issues, recommendations, final report
- **Agent Panel**: Shows all agents and workflow

### 6.2 User Flow ✅ **IMPLEMENTED**
1. User enters natural language scene description
2. Clicks "Create Scene" button
3. System shows loading state with agent progress
4. Results display with scene objects, lighting, camera
5. Validation report shows any issues
6. Final report provides comprehensive summary

### 6.3 Design Principles
- **Simplicity**: Clean, focused interface
- **Feedback**: Real-time progress indication
- **Transparency**: Show agent workflow and decisions
- **Actionable**: Clear display of validation issues

## 7. Technical Requirements

### 7.1 AI/ML Components ✅ **IMPLEMENTED**
- **LLM**: Groq LLaMA 3.3 70B (default), LLaMA 3.1 8B (fallback)
- **Framework**: LangGraph for multi-agent orchestration
- **Agent Base**: LangChain with ChatGroq integration
- **Prompt Templates**: ChatPromptTemplate with system prompts
- **State Management**: TypedDict with Annotated reducers
- **Workflow**: StateGraph with conditional edges
- **Error Handling**: Comprehensive logging and graceful fallbacks

### 7.2 Data Sources & Integrations

**Current** ✅:
- Groq API for LLM inference
- Simulated 3D asset library with categories:
  - Furniture (beds, desks, chairs, tables, sofas)
  - Lighting (lamps, fixtures)
  - Storage (bookshelves, cabinets)
  - Decor (plants, rugs, curtains, books)
  - Architecture (windows, doors)

**Future Enhancements**:
- Real 3D asset library integration (Sketchfab, TurboSquid)
- Blender/USD export
- MCP server integration for external tools
- Real-time 3D preview

### 7.3 Technology Stack ✅ **IMPLEMENTED**

#### Backend
- **Framework**: FastAPI 0.109.0
- **Language**: Python 3.11+
- **LLM Provider**: Groq (Free tier available)
- **LLM Models**: Meta LLaMA 3.3 70B / 3.1 8B
- **AI Framework**: LangGraph 0.2.0 + LangChain 0.2.16 + langchain-groq 0.1.9
- **State Management**: TypedDict with operator-based reducers
- **Validation**: Pydantic 2.5.3
- **Server**: Uvicorn with async support
- **HTTP Client**: httpx 0.26.0 for async requests
- **Deployment**: Fly.io with Docker containerization
- **Logging**: Structured logging with agent action tracking

#### Frontend
- **Framework**: React 18
- **Language**: TypeScript
- **Build Tool**: Vite 5.0
- **State Management**: Zustand 4.4
- **HTTP Client**: Axios 1.6
- **Styling**: Custom CSS with CSS Variables (Dark theme)
- **Theme Colors**: 
  - Background: #0a0a0a (deep black)
  - Surface: #1a1a1a (dark charcoal)
  - Primary: #6366f1 (indigo)
- **Deployment**: Vercel with edge network
- **Markdown Rendering**: react-markdown with remark-gfm

#### Database
- **Current**: In-memory storage (demo/development)
- **Recommended Production**: PostgreSQL or MongoDB
- **Future**: Vector database for embeddings

#### Deployment ✅ **CONFIGURED**
- **Frontend**: Vercel
  - Automatic deployments from Git
  - Edge network for global performance
  - API proxy to backend
- **Backend**: Fly.io
  - Docker containerization
  - Secrets management
  - Auto-scaling capabilities

#### Monitoring & Logging ✅ **IMPLEMENTED**
- FastAPI automatic request logging
- Agent action logging with details
- Health check endpoints
- Console logging for debugging
- Ready for: Sentry, DataDog, or similar

### 7.4 Performance Requirements ✅ **MET**

**Target Performance**:
- Scene Creation: < 30 seconds typical
- API Response: < 1 second for simple requests
- Page Load: < 1 second
- LLM Response: 1-5 seconds (via Groq infrastructure)

**Model Performance** (Groq-hosted):
- LLaMA 3.3 70B: 280 tokens/sec (default)
- LLaMA 3.1 8B: 560 tokens/sec (fallback)

## 8. Privacy & Security

### 8.1 Security Measures ✅ **IMPLEMENTED**
- ✅ Environment variable secrets (never committed)
- ✅ HTTPS enforced in production
- ✅ Input validation with Pydantic
- ✅ CORS protection with configurable origins

### 8.2 Privacy
- ✅ Minimal data collection
- ✅ No persistent storage of prompts (current implementation)
- ✅ No third-party tracking
- 🔄 Privacy policy (to be added)

## 9. Success Metrics

### 9.1 Technical Metrics ✅
- **Uptime**: Target 99.5%
- **Response Time**: < 30 seconds for scene creation
- **Validation Pass Rate**: > 80% on first attempt
- **Error Rate**: < 5%

### 9.2 User Metrics 🔄 (To be implemented)
- Scenes created per user
- Revision iterations per scene
- Prompt complexity analysis
- User satisfaction ratings

## 10. Phases & Roadmap

### Phase 1: MVP ✅ **COMPLETED** (January 2026)
- [x] Multi-agent system with 6 specialized agents
- [x] LangGraph workflow orchestration
- [x] Orchestrator for request decomposition
- [x] Librarian with simulated asset library
- [x] Architect with Z-Up coordinate system and collision detection
- [x] Material Scientist with PBR presets
- [x] Cinematographer with lighting presets
- [x] Critic with validation checks and revision loop
- [x] FastAPI backend with RESTful endpoints
- [x] React frontend with TypeScript
- [x] Dark theme UI
- [x] Scene display with object/lighting/camera info
- [x] Validation report rendering
- [x] Comprehensive documentation

### Phase 2: Enhancement 🔄 (Q1 2026)
- [ ] Real 3D asset library integration
- [ ] User authentication
- [ ] Scene persistence (database)
- [ ] Export to Blender/USD format
- [ ] Real-time 3D preview
- [ ] Custom agent prompts via UI
- [ ] MCP server integration

### Phase 3: Advanced Features (Q2 2026)
- [ ] Collaborative editing
- [ ] Version history and comparison
- [ ] Template scenes
- [ ] Batch scene generation
- [ ] Voice input
- [ ] Mobile-responsive improvements

### Phase 4: Scale & Optimize (Q3 2026)
- [ ] Performance optimization
- [ ] Advanced caching
- [ ] Multi-region deployment
- [ ] Enterprise features
- [ ] Plugin ecosystem

## 11. Open Questions & Risks

### Questions Addressed ✅
- ✅ AI Framework: LangGraph chosen for multi-agent orchestration
- ✅ LLM Provider: Groq chosen for speed and free tier
- ✅ Deployment: Fly.io + Vercel chosen
- ✅ Agent Architecture: 6 specialized agents with clear responsibilities

### Remaining Questions 🔄
- [ ] What 3D asset library to integrate?
- [ ] Which 3D file formats to support for export?
- [ ] How to handle very complex scenes (100+ objects)?
- [ ] When to add premium features?

### Risks & Mitigation ✅

**LLM API Dependencies**:
- Risk: Groq API changes or downtime
- Mitigation: ✅ Fallback model implemented, error handling

**Scene Complexity**:
- Risk: Complex scenes exceed token limits
- Mitigation: ✅ Max iteration limits, object count warnings

**Asset Availability**:
- Risk: Requested assets not in library
- Mitigation: ✅ Substitution suggestions, flagging for Material Scientist

**Validation Loops**:
- Risk: Infinite revision loops
- Mitigation: ✅ Max iterations limit (default: 3)

## 12. Constraints

### Technical Constraints ✅
- ✅ LLM API costs managed via free tier
- ✅ Groq model availability (fallback implemented)
- ✅ Browser compatibility (modern browsers)
- ✅ Scene complexity limits (managed via iteration caps)

### Business Constraints
- Bootstrap/self-funded initially
- Free tier usage for development
- MVP timeline: Completed
- Initial focus: Individual artists

## 13. Future Enhancements

### Near-term (Next 3 months)
- Real 3D asset library integration
- Scene persistence
- User authentication
- Export to common 3D formats
- Real-time 3D preview

### Medium-term (3-6 months)
- Collaborative editing
- Template library
- Custom agent training
- Voice interaction
- Mobile app

### Long-term (6-12 months)
- Enterprise features
- Plugin ecosystem
- White-label options
- API marketplace
- Multi-language support

### Potential Features
- Integration with Blender, Maya, Cinema 4D
- AR/VR scene preview
- Procedural generation options
- Style transfer between scenes
- AI-powered scene variations

---

## Document Control

**Version**: 1.0  
**Last Updated**: January 31, 2026  
**Author**: Product Team  
**Status**: ✅ **MVP Implementation Complete**  
**Next Review**: February 2026

## Implementation Status

### ✅ Completed
- Multi-agent system with LangGraph
- 6 specialized agents (Orchestrator, Librarian, Architect, Material Scientist, Cinematographer, Critic)
- **Vector Memory (RAG)** with ChromaDB for scene retrieval
- **Semantic search** for similar past scenes
- **Orchestrator memory integration** for context-aware planning
- FastAPI backend with REST API
- React + TypeScript frontend
- Dark theme UI (#0a0a0a background)
- Scene creation from natural language
- Object placement with collision detection
- PBR material application
- Lighting and camera setup
- Validation with revision loop
- Markdown-rendered final reports
- Comprehensive documentation (11 guides)

### 🔄 In Progress
- Real asset library integration
- User authentication
- Scene persistence

### 📋 Planned
- 3D preview
- Export formats
- Collaborative features
- Enterprise features

---

## Quick Links

- **Main Documentation**: [README.md](../README.md)
- **Getting Started**: [GETTING_STARTED.md](GETTING_STARTED.md)
- **Architecture**: [ARCHITECTURE.md](ARCHITECTURE.md)
- **API Reference**: [API.md](API.md)
- **Agent Documentation**: [AGENTS.md](AGENTS.md)
- **Agent Communication**: [AGENT_COMMUNICATION.md](AGENT_COMMUNICATION.md)
- **Vector Memory (RAG)**: [MEMORY.md](MEMORY.md)
- **Deployment Guide**: [DEPLOYMENT.md](DEPLOYMENT.md)
- **Project Structure**: [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)
- **Quick Reference**: [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
- **Changelog**: [CHANGELOG.md](CHANGELOG.md)
