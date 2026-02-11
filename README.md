# Moo Director

A multi-agent AI system for 3D workflow automation, built with LangGraph, FastAPI, and React.

## Overview

Moo Director uses a team of specialized AI agents to automatically create 3D scenes from natural language descriptions. The system decomposes complex requests into tasks and orchestrates multiple agents to handle different aspects of scene creation.

## Agent Architecture

The system consists of 6 specialized agents:

| Agent | Role | Responsibility |
|-------|------|----------------|
| **Orchestrator** | Lead Art Director | Decomposes requests, coordinates agents, manages workflow |
| **Librarian** | Asset Fetcher | Searches and retrieves 3D assets from the library |
| **Architect** | Layout Artist | Places objects in 3D space with correct coordinates |
| **Material Scientist** | Look-Dev Artist | Applies PBR materials and textures |
| **Cinematographer** | Lighting Director | Sets up scene lighting and camera |
| **Critic** | Quality Controller | Validates scene and triggers revisions if needed |

## Workflow

```
User Prompt → Orchestrator → Librarian → Architect → Material Scientist → Cinematographer → Critic
                   ↑                                                                           |
                   └─────────────────────── Revision Loop (if needed) ─────────────────────────┘
```

## Tech Stack

### Backend
- **Framework**: FastAPI
- **AI Orchestration**: LangGraph
- **LLM**: Groq (LLaMA 3.3 70B)
- **Language**: Python 3.11+

### Frontend
- **Framework**: React 18
- **Language**: TypeScript
- **Build Tool**: Vite
- **State Management**: Zustand

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- Groq API Key (get one at https://console.groq.com)

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your GROQ_API_KEY

# Run the server
python main.py
```

The API will be available at http://localhost:8000

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

The frontend will be available at http://localhost:3000

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/scene/create` | POST | Create a 3D scene from a prompt |
| `/api/v1/scene/create-async` | POST | Create scene asynchronously |
| `/api/v1/scene/status/{job_id}` | GET | Check async job status |
| `/api/v1/agents` | GET | List all agents |
| `/api/v1/health` | GET | Health check |

### Example Request

```bash
curl -X POST "http://localhost:8000/api/v1/scene/create" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create a cozy bedroom with a white bed, wooden desk, and warm morning light",
    "max_iterations": 3
  }'
```

## Project Structure

```
moo-director/
├── backend/
│   ├── app/
│   │   ├── agents/           # AI agent implementations
│   │   │   ├── orchestrator.py
│   │   │   ├── librarian.py
│   │   │   ├── architect.py
│   │   │   ├── material_scientist.py
│   │   │   ├── cinematographer.py
│   │   │   └── critic.py
│   │   ├── api/              # FastAPI routes
│   │   ├── models/           # Pydantic models & state
│   │   ├── workflow/         # LangGraph workflow
│   │   └── config.py
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── api/              # API client
│   │   ├── store/            # Zustand store
│   │   ├── types/            # TypeScript types
│   │   └── styles/           # CSS styles
│   ├── package.json
│   └── vite.config.ts
└── docs/
```

## Features

- **Multi-Agent Collaboration**: Specialized agents work together to create scenes
- **Iterative Refinement**: Critic agent validates and triggers revisions
- **PBR Materials**: Physically-based rendering materials for realistic output
- **Z-Up Coordinate System**: Industry-standard 3D coordinate system
- **Collision Detection**: Prevents objects from intersecting
- **Prompt Alignment**: Validates that the scene matches the user's request
- **Async Processing**: Support for long-running scene generation

## AI Assistance Disclosure

Portions of this project were developed with the assistance of AI-based tools. 
All generated code was reviewed, modified, and validated by the author.

## License

This project is licensed under the Apache License 2.0.

See the [LICENSE](/LICENSE) file for details.
