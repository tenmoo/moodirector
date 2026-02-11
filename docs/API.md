# API Documentation

Complete API reference for Moo Director backend.

## Base URL

- **Development**: `http://localhost:8000`
- **Production**: `https://your-app.fly.dev`

## API Version

All endpoints are prefixed with `/api/v1`.

---

## Endpoints

### Health & Info

#### GET /

Get API information.

**Response:**
```json
{
  "name": "Moo Director",
  "version": "1.0.0",
  "description": "Multi-agent AI system for 3D workflow automation",
  "docs": "/docs",
  "health": "/api/v1/health"
}
```

#### GET /api/v1/health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "moo-director"
}
```

---

### Scene Creation

#### POST /api/v1/scene/create

Create a new 3D scene from a natural language prompt. This endpoint runs the full multi-agent workflow synchronously.

**Request Body:**
```json
{
  "prompt": "Create a cozy bedroom with a white bed, wooden desk, and warm morning light",
  "max_iterations": 3
}
```

**Fields:**
- `prompt` (string, required): Natural language description of the desired scene
- `max_iterations` (integer, optional): Maximum revision cycles (1-5, default: 3)

**Response:** `200 OK`
```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "scene_data": {
    "objects": [
      {
        "id": "obj-uuid-1",
        "name": "bed",
        "asset_path": "/library/furniture/beds/white_modern_bed.blend",
        "position": {"x": 0.0, "y": 1.95, "z": 0.0},
        "rotation": {"x": 0.0, "y": 0.0, "z": 0.0},
        "scale": {"x": 1.0, "y": 1.0, "z": 1.0},
        "material": {
          "name": "white_bedding",
          "shader_type": "cloth",
          "base_color": [0.98, 0.98, 0.98, 1.0],
          "roughness": 0.9,
          "metallic": 0.0,
          "subsurface": 0.2,
          "texture_map": "/textures/fabric/cotton_white.png"
        },
        "status": "textured"
      }
    ],
    "lighting": {
      "lights": [
        {
          "id": "key_light_001",
          "name": "key_light",
          "light_type": "area",
          "position": {"x": 3.0, "y": -2.0, "z": 4.0},
          "rotation": {"x": 30.0, "y": 0.0, "z": 45.0},
          "color_temperature": 3200,
          "intensity": 2.5
        }
      ],
      "hdri_map": "/hdri/cozy_interior.hdr",
      "exposure": 0.9
    },
    "camera": {
      "position": {"x": 0.0, "y": -4.0, "z": 1.6},
      "target": {"x": 0.0, "y": 0.0, "z": 0.5},
      "focal_length": 50.0,
      "aperture": 1.8,
      "depth_of_field": true
    }
  },
  "validation_report": {
    "passed": true,
    "issues": [],
    "final_report": "# 3D Scene Validation Report\n\n## Summary\n..."
  },
  "message": "Scene created with 3 objects",
  "processing_time_ms": 4523.5
}
```

**Errors:**
- `500`: Error processing scene creation

---

#### POST /api/v1/scene/create-async

Create a scene asynchronously. Returns a job ID to poll for status.

**Request Body:**
```json
{
  "prompt": "Create a modern office with glass desk and ambient lighting",
  "max_iterations": 3,
  "async_mode": true
}
```

**Response:** `200 OK`
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "progress": "Job queued"
}
```

---

#### GET /api/v1/scene/status/{job_id}

Get the status of an async scene creation job.

**Path Parameters:**
- `job_id` (string, required): The job ID returned from create-async

**Response (pending):**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "progress": "Material Scientist applying textures...",
  "result": null,
  "error": null
}
```

**Response (completed):**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "progress": "Done",
  "result": {
    "objects": [...],
    "lighting": {...},
    "camera": {...},
    "validation_passed": true,
    "final_report": "..."
  },
  "error": null
}
```

**Errors:**
- `404`: Job not found

---

### Agents

#### GET /api/v1/agents

Get information about all agents in the system.

**Response:** `200 OK`
```json
{
  "agents": [
    {
      "name": "Orchestrator",
      "role": "Lead Art Director",
      "description": "Decomposes requests and coordinates all other agents"
    },
    {
      "name": "Librarian",
      "role": "Asset Fetcher",
      "description": "Searches and retrieves 3D assets from the library"
    },
    {
      "name": "Architect",
      "role": "Layout Artist",
      "description": "Places objects in 3D space with correct coordinates"
    },
    {
      "name": "Material Scientist",
      "role": "Look-Dev Artist",
      "description": "Applies PBR materials and textures to objects"
    },
    {
      "name": "Cinematographer",
      "role": "Lighting Director",
      "description": "Sets up scene lighting and camera configuration"
    },
    {
      "name": "Critic",
      "role": "Quality Controller",
      "description": "Validates the scene and identifies issues"
    }
  ],
  "workflow": "Orchestrator → Librarian → Architect → Material Scientist → Cinematographer → Critic → (Revision loop if needed)"
}
```

---

## Data Models

### SceneObject

```typescript
interface SceneObject {
  id: string;
  name: string;
  asset_path: string | null;
  position: Coordinate3D | null;
  rotation: Coordinate3D | null;
  scale: Coordinate3D | null;
  bounding_box?: BoundingBox;
  material: Material | null;
  polygon_count?: number;
  status: "pending" | "fetched" | "placed" | "textured" | "validated";
}
```

### Coordinate3D

```typescript
interface Coordinate3D {
  x: number;  // Left/Right
  y: number;  // Forward/Backward
  z: number;  // Up/Down (height)
}
```

### Material (PBR)

```typescript
interface Material {
  name: string;
  shader_type: "cloth" | "wood" | "metal" | "glass" | "plastic" | "principled_bsdf";
  base_color: [number, number, number, number];  // RGBA
  roughness: number;      // 0.0 - 1.0
  metallic: number;       // 0.0 - 1.0
  subsurface: number;     // 0.0 - 1.0
  subsurface_color?: [number, number, number];
  clear_coat: number;     // 0.0 - 1.0
  texture_map: string | null;
  normal_map: string | null;
  roughness_map: string | null;
}
```

### LightSource

```typescript
interface LightSource {
  id: string;
  name: string;
  light_type: "sun" | "area" | "point" | "spot";
  position: Coordinate3D;
  rotation: Coordinate3D;
  color_temperature: number;  // Kelvin (e.g., 3500 = warm, 6500 = cool)
  intensity: number;
  angle: number;
  size: number;
}
```

### ValidationIssue

```typescript
interface ValidationIssue {
  severity: "error" | "warning" | "info";
  category: "clipping" | "floating" | "material" | "lighting" | "overexposure" | "prompt_alignment";
  description: string;
  affected_object_id: string | null;
  suggested_fix: string | null;
}
```

---

## Error Responses

All error responses follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common HTTP Status Codes

| Code | Meaning |
|------|---------|
| `200 OK` | Request succeeded |
| `201 Created` | Resource created |
| `400 Bad Request` | Invalid request data |
| `404 Not Found` | Resource not found |
| `422 Unprocessable Entity` | Validation error |
| `500 Internal Server Error` | Server error |

---

## Testing the API

### Using cURL

**Create a scene:**
```bash
curl -X POST http://localhost:8000/api/v1/scene/create \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create a cozy bedroom with a white bed and warm lighting",
    "max_iterations": 3
  }'
```

**List agents:**
```bash
curl http://localhost:8000/api/v1/agents
```

**Health check:**
```bash
curl http://localhost:8000/api/v1/health
```

### Using Python

```python
import requests

# Create a scene
response = requests.post(
    "http://localhost:8000/api/v1/scene/create",
    json={
        "prompt": "Create a modern office with a glass desk",
        "max_iterations": 3
    }
)
result = response.json()
print(f"Status: {result['status']}")
print(f"Objects: {len(result['scene_data']['objects'])}")
print(f"Processing time: {result['processing_time_ms']}ms")

# List agents
response = requests.get("http://localhost:8000/api/v1/agents")
agents = response.json()
for agent in agents["agents"]:
    print(f"- {agent['name']}: {agent['description']}")
```

### Using Swagger UI

Visit `http://localhost:8000/docs` for interactive API documentation where you can test all endpoints.

1. Click on an endpoint
2. Click "Try it out"
3. Fill in the parameters
4. Click "Execute"

---

## CORS

The API supports CORS for development origins.

**Default (development):**
- `http://localhost:3000`

**Production:**
Configure via the CORS middleware in `main.py`.

---

## Rate Limiting

Currently, there are no rate limits enforced. In production, consider implementing rate limiting to prevent abuse.

---

## Versioning

Current version: `1.0.0`

The API version is included in the URL path: `/api/v1/`

---

---

## Memory Endpoints

The memory system stores past scenes and enables semantic search for similar scenes.

### POST /api/v1/memory/search

Search for similar scenes using semantic similarity.

**Request Body:**
```json
{
  "query": "cozy bedroom with warm lighting",
  "n_results": 5,
  "min_score": 0.3
}
```

**Response:** `200 OK`
```json
{
  "query": "cozy bedroom with warm lighting",
  "results": [
    {
      "id": "scene-uuid",
      "similarity": 0.85,
      "user_prompt": "Create a comfortable bedroom...",
      "interpreted_mood": "cozy, warm",
      "object_count": 5,
      "object_names": ["bed", "desk", "lamp"],
      "lighting_mood": "warm",
      "validation_passed": true,
      "timestamp": "2026-01-31T10:30:00"
    }
  ],
  "total_in_memory": 15
}
```

### GET /api/v1/memory/recent

Get the most recently created scenes.

**Query Parameters:**
- `limit` (int, optional): Number of scenes (1-50, default: 10)

### GET /api/v1/memory/scene/{scene_id}

Retrieve a specific scene by ID.

### DELETE /api/v1/memory/scene/{scene_id}

Delete a specific scene from memory.

### GET /api/v1/memory/stats

Get memory statistics.

**Response:**
```json
{
  "total_scenes": 15,
  "collection_name": "scene_memory",
  "embedding_model": "all-MiniLM-L6-v2"
}
```

### DELETE /api/v1/memory/clear

Clear all scenes from memory. **Warning: Cannot be undone!**

---

## Evaluation Endpoints (LangSmith)

The evaluation system integrates with LangSmith for observability and quality assessment. These endpoints require `LANGCHAIN_API_KEY` to be configured.

### POST /api/v1/evaluation/datasets/create

Create a new evaluation dataset in LangSmith.

**Request Body:**
```json
{
  "dataset_name": "3d-scene-prompts",
  "description": "Evaluation dataset for 3D scene generation prompts"
}
```

**Response:** `200 OK`
```json
{
  "message": "Dataset '3d-scene-prompts' created successfully",
  "dataset_id": "uuid-here"
}
```

### GET /api/v1/evaluation/datasets

List all evaluation datasets.

**Response:** `200 OK`
```json
{
  "datasets": [
    {
      "id": "uuid",
      "name": "3d-scene-prompts",
      "description": "Evaluation dataset for 3D scene generation",
      "created_at": "2026-02-06T10:30:00Z",
      "example_count": 5
    }
  ],
  "count": 1
}
```

### POST /api/v1/evaluation/run

Run evaluation against a dataset. This executes scene generation for all examples and evaluates results.

**Request Body:**
```json
{
  "dataset_name": "3d-scene-prompts",
  "experiment_prefix": "moo-director-eval",
  "max_concurrency": 2
}
```

**Response:** `200 OK`
```json
{
  "message": "Evaluation completed",
  "experiment_name": "moo-director-eval_20260206_103000",
  "dataset_name": "3d-scene-prompts",
  "result_count": 5
}
```

**Evaluators Used:**
- `scene_completeness` - Are all requested objects present?
- `prompt_alignment` - Does the output match the prompt?
- `validation_pass` - Did the scene pass internal validation?
- `object_count` - Is the object count reasonable?

### GET /api/v1/evaluation/results

Get evaluation results from LangSmith.

**Query Parameters:**
- `experiment_name` (string, optional): Filter by experiment name
- `limit` (int, optional): Max results (1-100, default: 10)

**Response:** `200 OK`
```json
{
  "results": [
    {
      "id": "uuid",
      "name": "moo-director-eval_20260206_103000",
      "created_at": "2026-02-06T10:30:00Z",
      "run_count": 5
    }
  ],
  "count": 1
}
```

### POST /api/v1/evaluation/quick

Quickly evaluate a single prompt without using datasets. Does not require LangSmith.

**Request Body:**
```json
{
  "prompt": "Create a cozy bedroom with a white bed and warm lighting"
}
```

**Response:** `200 OK`
```json
{
  "prompt": "Create a cozy bedroom with a white bed and warm lighting",
  "overall_score": 0.85,
  "evaluations": {
    "scene_completeness": {
      "score": 1.0,
      "reasoning": "Generated 3 objects: bed, lamp, nightstand"
    },
    "prompt_alignment": {
      "score": 0.8,
      "reasoning": "Found 4/5 key terms from prompt in output"
    },
    "validation_pass": {
      "score": 1.0,
      "reasoning": "Validation passed. Issues: 0 errors, 0 warnings"
    },
    "object_count": {
      "score": 1.0,
      "reasoning": "Object count (3) is within expected range [1, 20]"
    }
  },
  "scene_objects_count": 3,
  "validation_passed": true
}
```

---

## Support

For issues or questions about the API:
- Check the interactive documentation at `/docs`
- Review the source code in `backend/app/api/routes.py`
- See [MEMORY.md](MEMORY.md) for vector memory details
- See [LANGSMITH.md](LANGSMITH.md) for observability and evaluation details
