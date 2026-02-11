# Moo Director - Quick Reference

Quick commands and common operations.

## Development Commands

### Start Development Servers

**Backend:**
```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
python main.py
```

**Frontend:**
```bash
cd frontend
npm run dev
```

**Both (in separate terminals):**
```bash
# Terminal 1
cd backend && source venv/bin/activate && python main.py

# Terminal 2
cd frontend && npm run dev
```

### URLs

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| Health Check | http://localhost:8000/api/v1/health |
| LangSmith Dashboard | https://smith.langchain.com |

---

## API Quick Reference

### Create Scene

```bash
curl -X POST http://localhost:8000/api/v1/scene/create \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Create a cozy bedroom with a white bed"}'
```

### List Agents

```bash
curl http://localhost:8000/api/v1/agents
```

### Health Check

```bash
curl http://localhost:8000/api/v1/health
```

### Quick Evaluation (LangSmith)

```bash
curl -X POST http://localhost:8000/api/v1/evaluation/quick \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Create a cozy bedroom with a white bed"}'
```

### Create Evaluation Dataset

```bash
curl -X POST http://localhost:8000/api/v1/evaluation/datasets/create \
  -H "Content-Type: application/json" \
  -d '{"dataset_name": "my-test-prompts"}'
```

### Run Batch Evaluation

```bash
curl -X POST http://localhost:8000/api/v1/evaluation/run \
  -H "Content-Type: application/json" \
  -d '{"dataset_name": "3d-scene-prompts"}'
```

---

## Python Quick Reference

### Setup Virtual Environment

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Run with Hot Reload

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Install New Package

```bash
pip install package_name
pip freeze > requirements.txt
```

---

## Node.js Quick Reference

### Install Dependencies

```bash
cd frontend
npm install
```

### Build for Production

```bash
npm run build
```

### Preview Production Build

```bash
npm run preview
```

### Update Dependencies

```bash
npm update
```

---

## Git Commands

### Basic Workflow

```bash
git add .
git commit -m "Description of changes"
git push origin main
```

### Create Feature Branch

```bash
git checkout -b feature/new-feature
```

### Merge to Main

```bash
git checkout main
git merge feature/new-feature
git push origin main
```

---

## Deployment Commands

### Fly.io (Backend)

```bash
cd backend

# Deploy
fly deploy

# View logs
fly logs

# Check status
fly status

# Set secrets
fly secrets set GROQ_API_KEY=your_key
fly secrets set LANGCHAIN_API_KEY=your_langsmith_key  # Optional
```

### Vercel (Frontend)

```bash
cd frontend

# Deploy to preview
vercel

# Deploy to production
vercel --prod
```

---

## Troubleshooting Commands

### Kill Process on Port

```bash
# macOS/Linux
lsof -ti:8000 | xargs kill -9  # Backend port
lsof -ti:3000 | xargs kill -9  # Frontend port

# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Reset Node Modules

```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Reset Python Virtual Environment

```bash
cd backend
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Check Python Path

```bash
which python
python --version
```

### Check Node Version

```bash
node --version
npm --version
```

---

## File Locations

| File | Purpose |
|------|---------|
| `backend/main.py` | FastAPI entry point |
| `backend/app/agents/*.py` | Agent implementations |
| `backend/app/workflow/graph.py` | LangGraph workflow |
| `backend/app/api/routes.py` | API endpoints |
| `backend/app/evaluation/*.py` | LangSmith evaluators |
| `frontend/src/App.tsx` | React app entry |
| `frontend/src/api/client.ts` | API client |
| `frontend/src/store/useStore.ts` | Zustand store |

---

## Environment Variables

### Backend (.env)

```env
# Required
GROQ_API_KEY=your_groq_api_key
SECRET_KEY=your_secret_key

# Optional: Server
HOST=0.0.0.0
PORT=8000
DEBUG=true
DEFAULT_MODEL=llama-3.3-70b-versatile

# Optional: LangSmith (Observability)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_api_key
LANGCHAIN_PROJECT=moo-director
```

### Copy Template

```bash
cd backend
cp .env.example .env
```

---

## Agent Workflow

```
User Prompt
    ↓
Orchestrator (decompose)
    ↓
Librarian (fetch assets)
    ↓
Architect (place objects)
    ↓
Material Scientist (apply textures)
    ↓
Cinematographer (setup lights/camera)
    ↓
Critic (validate)
    ↓
Pass? → Final Report
  ↓
Fail? → Back to Orchestrator
```

---

## Example Prompts

**Cozy Bedroom:**
```
Create a cozy bedroom with a white bed, wooden desk, and warm morning light
```

**Modern Office:**
```
Design a modern home office with a glass desk, leather chair, and cool ambient lighting
```

**Dramatic Study:**
```
Create a dramatic study with a wooden desk, tall bookshelf, and single spotlight
```

**Living Room:**
```
Set up a living room with a large sofa, bookshelf, floor lamp, and soft evening light
```

---

## Logs and Debugging

### View Backend Logs

Logs appear in the terminal running `python main.py`

### View Frontend Console

Open browser DevTools (F12) → Console tab

### Check Network Requests

Open browser DevTools (F12) → Network tab

### View LangSmith Traces

If `LANGCHAIN_API_KEY` is configured:
1. Visit https://smith.langchain.com
2. Select project "moo-director"
3. View traces with full LLM inputs/outputs

---

## Documentation Links

| Document | Description |
|----------|-------------|
| [README](../README.md) | Project overview |
| [Getting Started](GETTING_STARTED.md) | Setup guide |
| [Architecture](ARCHITECTURE.md) | System design |
| [API](API.md) | API reference |
| [Agents](AGENTS.md) | Agent documentation |
| [Agent Communication](AGENT_COMMUNICATION.md) | How agents communicate via shared state |
| [Memory (RAG)](MEMORY.md) | Vector memory for scene retrieval |
| [LangSmith](LANGSMITH.md) | Observability & evaluation |
| [Deployment](DEPLOYMENT.md) | Production deployment |
| [Project Structure](PROJECT_STRUCTURE.md) | File structure |
