# Getting Started with Moo Director

This guide will help you get Moo Director up and running on your local machine.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.11+**: [Download here](https://www.python.org/downloads/)
- **Node.js 18+**: [Download here](https://nodejs.org/)
- **Git**: [Download here](https://git-scm.com/)

You'll also need:
- A Groq API key (free): [Get one here](https://console.groq.com/)
- (Optional) A LangSmith API key for observability: [Get one here](https://smith.langchain.com/)

## Step 1: Clone the Repository

```bash
git clone <your-repo-url>
cd moo-director
```

## Step 2: Backend Setup

### 2.1 Navigate to Backend Directory

```bash
cd backend
```

### 2.2 Create Virtual Environment

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**On Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

### 2.3 Install Dependencies

```bash
pip install -r requirements.txt
```

### 2.4 Configure Environment

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` and add your Groq API key:
```env
GROQ_API_KEY=your_actual_groq_api_key
SECRET_KEY=your_secret_key_for_jwt
```

3. (Optional) Enable LangSmith tracing for observability:
```env
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_api_key
LANGCHAIN_PROJECT=moo-director
```

### 2.5 Start Backend Server

```bash
python main.py
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Starting Moo Director API
```

✅ Backend is now running! Visit http://localhost:8000/docs to see the API documentation.

## Step 3: Frontend Setup

Open a **new terminal window** (keep the backend running).

### 3.1 Navigate to Frontend Directory

```bash
cd frontend
```

### 3.2 Install Dependencies

```bash
npm install
```

This may take a few minutes on first run.

### 3.3 Start Frontend Development Server

```bash
npm run dev
```

You should see:
```
  VITE v5.0.8  ready in 500 ms

  ➜  Local:   http://localhost:3000/
```

✅ Frontend is now running! Visit http://localhost:3000

## Step 4: Create Your First Scene

1. Open http://localhost:3000 in your browser
2. Enter a scene description in the prompt box:
   ```
   Create a cozy bedroom with a white bed, wooden desk, and warm morning light
   ```
3. Click "Create Scene"
4. Watch as the agents collaborate to build your scene!

## Understanding the Agent Workflow

When you submit a prompt, 6 specialized agents work together:

```
Your Prompt
    ↓
┌─────────────────────────────────────────────────────┐
│ 1. ORCHESTRATOR - Interprets your request           │
│    "Cozy bedroom" → warm textures, soft lighting    │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ 2. LIBRARIAN - Fetches 3D assets                    │
│    Finds: white_bed.blend, oak_desk.blend           │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ 3. ARCHITECT - Places objects in 3D space           │
│    Bed: (0, 1.95, 0), Desk: (1.2, -1.5, 0)         │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ 4. MATERIAL SCIENTIST - Applies textures            │
│    Bed: cloth shader, white fabric texture          │
│    Desk: wood shader, oak grain texture             │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ 5. CINEMATOGRAPHER - Sets up lighting & camera      │
│    Key light: 3200K (warm), Camera: 50mm f/1.8      │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ 6. CRITIC - Validates everything                    │
│    ✓ No clipping, ✓ Materials applied, ✓ Lighting  │
└─────────────────────────────────────────────────────┘
    ↓
Your Scene is Ready!
```

## Example Prompts to Try

**Cozy Interior:**
```
Create a cozy bedroom with a white bed, wooden desk, and warm morning light
```

**Modern Office:**
```
Design a modern home office with a glass desk, leather chair, and cool ambient lighting
```

**Living Room:**
```
Set up a living room with a large sofa, bookshelf, floor lamp, and soft evening light
```

**Dramatic Scene:**
```
Create a dramatic study with a wooden desk, tall bookshelf, and single spotlight
```

## Troubleshooting

### Backend Issues

**Error: "No module named 'fastapi'"**
- Make sure your virtual environment is activated
- Run `pip install -r requirements.txt` again

**Error: "Groq API key not found"**
- Check that you've created a `.env` file in the backend directory
- Verify your `GROQ_API_KEY` is set correctly
- Make sure there are no quotes around the key

**Port 8000 already in use:**
```bash
# Find and kill the process using port 8000
lsof -ti:8000 | xargs kill -9
```

### Frontend Issues

**Error: "Cannot find module"**
- Delete `node_modules` and `package-lock.json`
- Run `npm install` again

**Port 3000 already in use:**
- Vite will automatically suggest an alternative port
- Or kill the process: `lsof -ti:3000 | xargs kill -9`

**API connection error:**
- Make sure the backend is running on port 8000
- Check that the Vite proxy is configured correctly
- Try accessing http://localhost:8000/api/v1/health in your browser

### Both Running But Scene Creation Fails

**CORS Error:**
- Check browser console for CORS errors
- Restart the backend server

**Groq API Error:**
- Verify your API key is valid
- Check your Groq usage limits at https://console.groq.com

### Memory/Embedding Warnings

**"sentence_transformers not installed" warning:**
- This is optional - the system works without it
- For better semantic search, install: `pip install sentence-transformers`
- Without it, ChromaDB uses default embeddings (still functional)

**ChromaDB telemetry errors:**
- These are automatically suppressed and don't affect functionality
- The system disables telemetry by default

## Next Steps

- 📖 Read the [API Documentation](API.md)
- 🏗️ Learn the [Architecture](ARCHITECTURE.md)
- 🚀 Learn about [Deployment](DEPLOYMENT.md)
- 🤖 Explore the [Agent System](AGENTS.md)
- 📁 Review the [Project Structure](PROJECT_STRUCTURE.md)
- 📊 Read the [LangSmith Guide](LANGSMITH.md) for observability and evaluation

## Development Tips

### Backend Hot Reload

For automatic reload on code changes:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Hot Reload

The Vite dev server automatically reloads when you edit files.

### Viewing Logs

Backend logs appear in the terminal where you ran `python main.py`. You'll see:
- Agent execution logs
- LLM invocations
- Validation results

### LangSmith Observability (Optional)

If you've configured LangSmith, you can view detailed traces at https://smith.langchain.com:
- Full LangGraph workflow visualization
- Each agent's LLM calls with inputs/outputs
- Token usage and latency per call
- Create evaluation datasets from production traces
- Run automated quality evaluations

### Testing API Endpoints

Use the Swagger UI at http://localhost:8000/docs to test API endpoints directly.

---

Happy creating! 🎨
