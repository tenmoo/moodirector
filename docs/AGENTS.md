# Moo Director - Agent System Documentation

This document provides detailed information about each agent in the multi-agent system.

## Agent Overview

The Moo Director uses 6 specialized AI agents that collaborate to create 3D scenes:

| Agent | Role | Responsibility |
|-------|------|----------------|
| Orchestrator | Lead Art Director | Decomposition & Coordination |
| Librarian | Asset Fetcher | Sourcing & Compatibility |
| Architect | Layout Artist | Spatial Logic & Placement |
| Material Scientist | Look-Dev Artist | Surface Physics & Texturing |
| Cinematographer | Lighting Director | Atmosphere & Camera |
| Critic | Quality Controller | Validation & Error Detection |

---

## 1. Orchestrator (The Manager)

**File:** `backend/app/agents/orchestrator.py`

### Primary Responsibility
Decomposition & Coordination - Acts as the interface between the user and the agent system.

### Specific Actions
- Interprets natural language prompts
- Creates a Master Plan with structured tasks
- Determines execution order
- Routes data between agents
- Handles revision requests from the Critic

### System Prompt
```
You are the Lead Art Director. Your role is to break down a 3D scene request 
into structured tasks for a team of specialized agents:
- Librarian: Fetches 3D assets from the library
- Architect: Places objects in 3D space with correct coordinates
- Material Scientist: Applies PBR materials and textures
- Cinematographer: Sets up lighting and camera

You do NOT perform the tasks yourself. You ONLY coordinate and delegate.
```

### Output Format
```json
{
  "interpreted_mood": "cozy, warm, intimate",
  "required_objects": ["bed", "desk", "lamp"],
  "spatial_requirements": {
    "primary_focal_point": "bed",
    "relationships": [
      {"object": "desk", "relative_to": "window", "position": "near"}
    ]
  },
  "material_requirements": {
    "bed": {"style": "fabric", "finish": "soft"}
  },
  "lighting_requirements": {
    "time_of_day": "morning",
    "mood": "warm"
  },
  "execution_order": ["librarian", "architect", "material_scientist", "cinematographer"]
}
```

---

## 2. Librarian (The Fetcher)

**File:** `backend/app/agents/librarian.py`

### Primary Responsibility
Sourcing & Compatibility - The only agent with "database access" permissions.

### Specific Actions
- Searches the asset library for requested objects
- Returns file paths and bounding box dimensions
- Checks polygon counts (max 500,000 per asset)
- Suggests substitutions if exact match not found
- Converts file formats if needed

### Constraint
**Never download 'Heavy' assets that could crash the render engine.**

### System Prompt
```
You are an expert 3D Asset Librarian. Your goal is to find models that match 
the user's aesthetic. For every object requested, return the file path and 
bounding box dimensions. If a model is not found, suggest the closest visual 
match and flag it for the Material Scientist.
```

### Asset Library Categories
- Furniture: beds, desks, chairs, tables, sofas
- Lighting: lamps, fixtures
- Storage: bookshelves, cabinets
- Decor: plants, rugs, curtains, books
- Architecture: windows, doors

### Output Format
```json
{
  "assets": [
    {
      "name": "white_bed",
      "asset_path": "/library/furniture/beds/white_modern_bed.blend",
      "bounding_box": {"width": 2.0, "depth": 1.8, "height": 0.9},
      "polygon_count": 25000,
      "substitution": null
    }
  ],
  "warnings": []
}
```

---

## 3. Architect (The Layout Artist)

**File:** `backend/app/agents/architect.py`

### Primary Responsibility
Spatial Logic & Object Hierarchy - Handles all 3D positioning.

### Coordinate System
**Z-Up Convention:**
- X: Left/Right
- Y: Forward/Backward
- Z: Up/Down (height)

### Specific Actions
- Assigns X, Y, Z coordinates to every object
- Ensures spatial relationships (desk facing window)
- Manages Parent-Child relationships
- **CRITICAL:** Ensures no two meshes occupy the same space (No Clipping!)

### Placement Zones
```
Room Layout (6m x 6m)
┌─────────────────────────────────────────┐
│              primary_wall               │
│        (beds, sofas against wall)       │
├──────────────┬───────────┬──────────────┤
│ corner_left  │  center   │ corner_right │
│ (bookshelf,  │  (rugs,   │  (lamps)     │
│  plants)     │  tables)  │              │
├──────────────┼───────────┼──────────────┤
│              │           │ window_area  │
│              │           │ (desks)      │
├──────────────┴───────────┴──────────────┤
│            opposite_wall                │
│              (chairs)                   │
└─────────────────────────────────────────┘
```

### Placement Algorithm
- **Grid search** within zone bounds first (40cm steps)
- **Spiral expansion** to room bounds if no space found
- **Corner fallback** positions as last resort
- **Minimum spacing**: 50cm between objects
- **Smart clipping resolution**: Moves objects away directionally

### System Prompt
```
You are a 3D Layout Engineer. You receive model dimensions from the Librarian. 
Your task is to output x, y, z coordinates. Place the bed against the primary 
wall and the desk within 2 meters of a window. Ensure no two meshes occupy 
the same space (No Clipping).

Math Tool: Use Coordinate_System(Z=Up) for all calculations.
```

### Output Format
```json
{
  "placements": [
    {
      "object_id": "uuid",
      "name": "bed",
      "position": {"x": 0.0, "y": 1.95, "z": 0.0},
      "rotation": {"x": 0.0, "y": 0.0, "z": 0.0},
      "parent_id": null,
      "reasoning": "Placed against primary wall"
    }
  ]
}
```

---

## 4. Material Scientist (The Look-Dev Artist)

**File:** `backend/app/agents/material_scientist.py`

### Primary Responsibility
Surface Physics & Texturing - Focuses on the "skin" of 3D models.

### Specific Actions
- Applies PBR (Physically Based Rendering) materials
- Sets roughness, metallic, and subsurface scattering
- Ensures realistic material appearance
- Adjusts materials based on scene mood

### Constraint
**Every material includes a texture map.** The system automatically assigns appropriate textures based on material type. Even fallback materials include generic textures.

### Shader Types
| Type | Use Case | Roughness | Metallic |
|------|----------|-----------|----------|
| cloth | Fabric, bedding | 0.8-0.95 | 0.0 |
| wood | Furniture | 0.3-0.5 | 0.0 |
| metal | Fixtures, hardware | 0.1-0.3 | 0.8-1.0 |
| glass | Windows, displays | 0.0-0.1 | 0.0 |
| plastic | Modern furniture | 0.4-0.6 | 0.0 |

### System Prompt
```
You are a Look-Dev Specialist. You apply PBR shaders. For 'White Bed,' use a 
Cloth shader with high roughness. For 'Wooden Desk,' use an Oak texture with 
a clear coat of 0.1. Ensure all textures are mapped to UV coordinates.
```

### Material Presets
```python
# Cloth (fabric)
Material(
    shader_type="cloth",
    roughness=0.85,
    subsurface=0.15,
    texture_map="/textures/fabric/linen_diffuse.png"
)

# Wood
Material(
    shader_type="wood",
    roughness=0.4,
    clear_coat=0.1,
    texture_map="/textures/wood/oak_diffuse.png"
)
```

---

## 5. Cinematographer (The Lighting Director)

**File:** `backend/app/agents/cinematographer.py`

### Primary Responsibility
Atmosphere & Camera - Controls the virtual "set."

### Specific Actions
- Creates mood-appropriate lighting
- Uses HDRI maps or physical lights
- Sets camera focal length and aperture
- Configures depth of field

### Lighting Presets
| Mood | Key Light | Color Temp | Exposure |
|------|-----------|------------|----------|
| warm_morning | Area @ 30° | 3200K | 0.9 |
| cool_evening | Sun @ 15° | 6500K | 0.8 |
| dramatic | Spot @ 45° | 4000K | 1.2 |
| soft_diffuse | Large Area | 5500K | 1.0 |
| cozy | Area + Point | 3200K | 0.9 |

### Camera Guidelines
| Scene Type | Focal Length | Aperture | DOF |
|------------|--------------|----------|-----|
| Interior wide | 24-35mm | f/5.6-8 | Off |
| Intimate/cozy | 50mm | f/1.8-2.8 | On |
| Detail shot | 85mm | f/1.4-2 | On |
| Architectural | 24mm | f/8-11 | Off |

### System Prompt
```
You are a Lighting Director. Your goal is 'Warm Morning.' Set a Sun Lamp at a 
20-degree angle with a color temperature of 3500K. Add a soft Area Light near 
the window to simulate bounce light. Set the Camera to 35mm at f/2.8 for a 
shallow depth of field.
```

---

## 6. Critic (The Quality Controller)

**File:** `backend/app/agents/critic.py`

### Primary Responsibility
Validation & Error Detection - The "adversary" that ensures quality.

### Validation Checks

#### 1. Collision Detection
- Checks if objects intersect
- Ensures no clipping between meshes

#### 2. Floating Objects
- Verifies objects rest on surfaces
- Checks Z position >= 0 for floor objects

#### 3. Material Validation
- Ensures all objects have materials
- Checks for texture maps (no flat colors)
- Validates brightness < 95% (avoid overexposure)

#### 4. Lighting Validation
- Verifies at least one light source
- Checks for adequate key light intensity
- Validates exposure settings

#### 5. Prompt Alignment
- Verifies all required objects are present
- Checks if scene matches user's request

### Validation Settings
- **Passing Score**: 60/100 (scenes scoring 60+ pass validation)
- **Collision Tolerance**: 5cm (small overlaps are allowed)
- **Max Iterations**: 3 (revision attempts before forced completion)

### Severity Levels & Penalties
| Level | Meaning | Action | Penalty |
|-------|---------|--------|---------|
| error | Must be fixed | Blocks completion | 10 pts |
| warning | Should be addressed | Does not block | 3-5 pts |
| info | Suggestion | Optional | 1 pt |

### Validation Categories
| Category | Severity | Notes |
|----------|----------|-------|
| Severe clipping (>30cm) | error | Objects significantly overlapping |
| Minor clipping (<30cm) | warning | Small overlaps, often acceptable |
| Below floor | warning | Object z < -0.1m |
| Floating object | info | Not resting on surface |
| Missing material | warning | No material assigned |
| Missing texture | info | Glass/metal exempt |
| Overexposure | warning | Brightness > 98% |
| Missing light | error | No lights in scene |
| Missing object | warning | Required object not found |

### System Prompt
```
You are a ruthless 3D Quality Controller. You check the work of the other agents. 
You analyze the Architect's coordinates for clipping and the Cinematographer's 
render for overexposure. If the Bed's white value exceeds 95% brightness, reject 
it and request a lighting adjustment. Look for 'floating' objects.
```

### Output Format
```json
{
  "passed": false,
  "score": 75,
  "issues": [
    {
      "severity": "error",
      "category": "clipping",
      "description": "Desk intersects with bed",
      "affected_object_id": "uuid",
      "suggested_fix": "Move desk 0.5m to the left"
    }
  ],
  "recommendations": ["Consider adding a rug"]
}
```

---

## Workflow Interaction

### Normal Flow
```
Orchestrator → Librarian → Architect → Material Scientist → Cinematographer → Critic
                                                                                 │
                                                                            PASSED
                                                                                 │
                                                                                 ▼
                                                                          Final Report
```

### Revision Flow
```
Orchestrator → Librarian → Architect → Material Scientist → Cinematographer → Critic
      ▲                                                                          │
      │                                                                      FAILED
      │                                                                          │
      └────────────────────────── Revision Request ──────────────────────────────┘
```

### Revision Routing
The Critic determines which agent should fix the issue:

| Issue Category | Target Agent |
|----------------|--------------|
| clipping, floating, placement | Architect |
| material, texture, color | Material Scientist |
| lighting, exposure, camera | Cinematographer |
| missing_asset | Librarian |

---

## Extending the Agent System

### Adding a New Agent

1. Create the agent file:
```python
# backend/app/agents/new_agent.py
from .base import BaseAgent

NEW_AGENT_PROMPT = """Your system prompt here..."""

class NewAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="New Agent",
            description="Description of what this agent does",
            system_prompt=NEW_AGENT_PROMPT
        )
    
    async def process(self, state: AgentState) -> Dict[str, Any]:
        # Your implementation
        return {"current_agent": "next_agent", ...}
```

2. Register in `__init__.py`
3. Add to workflow graph
4. Update routing logic

### Customizing Agent Behavior

Each agent can be customized by:
- Modifying the system prompt
- Adjusting presets (materials, lighting)
- Adding new validation rules (Critic)
- Extending the asset library (Librarian)
