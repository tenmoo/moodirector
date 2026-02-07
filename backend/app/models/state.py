"""State models for the multi-agent Moo Director system."""
from typing import TypedDict, List, Optional, Dict, Any, Annotated
from pydantic import BaseModel, Field
from enum import Enum
import operator


class AgentType(str, Enum):
    """Types of agents in the system."""
    ORCHESTRATOR = "orchestrator"
    ARCHITECT = "architect"
    LIBRARIAN = "librarian"
    MATERIAL_SCIENTIST = "material_scientist"
    CINEMATOGRAPHER = "cinematographer"
    CRITIC = "critic"


class WorkflowStatus(str, Enum):
    """Status of the workflow."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    VALIDATION = "validation"
    REVISION = "revision"
    COMPLETED = "completed"
    FAILED = "failed"


class Coordinate3D(BaseModel):
    """3D coordinate with Z-up convention."""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    
    def to_dict(self) -> Dict[str, float]:
        return {"x": self.x, "y": self.y, "z": self.z}


class BoundingBox(BaseModel):
    """Bounding box dimensions for 3D objects."""
    width: float = 1.0   # X dimension
    depth: float = 1.0   # Y dimension
    height: float = 1.0  # Z dimension


class Material(BaseModel):
    """PBR Material definition."""
    name: str
    shader_type: str = "principled_bsdf"  # cloth, wood, metal, glass, etc.
    base_color: List[float] = Field(default=[1.0, 1.0, 1.0, 1.0])  # RGBA
    roughness: float = 0.5
    metallic: float = 0.0
    subsurface: float = 0.0
    subsurface_color: List[float] = Field(default=[1.0, 1.0, 1.0])
    clear_coat: float = 0.0
    texture_map: Optional[str] = None
    normal_map: Optional[str] = None
    roughness_map: Optional[str] = None


class SceneObject(BaseModel):
    """A 3D object in the scene."""
    id: str
    name: str
    asset_path: Optional[str] = None
    position: Coordinate3D = Field(default_factory=Coordinate3D)
    rotation: Coordinate3D = Field(default_factory=Coordinate3D)
    scale: Coordinate3D = Field(default_factory=lambda: Coordinate3D(x=1, y=1, z=1))
    bounding_box: BoundingBox = Field(default_factory=BoundingBox)
    material: Optional[Material] = None
    parent_id: Optional[str] = None
    polygon_count: int = 0
    status: str = "pending"  # pending, placed, textured, validated


class LightSource(BaseModel):
    """A light source in the scene."""
    id: str
    name: str
    light_type: str = "sun"  # sun, area, point, spot
    position: Coordinate3D = Field(default_factory=Coordinate3D)
    rotation: Coordinate3D = Field(default_factory=Coordinate3D)
    color_temperature: int = 5500  # Kelvin
    intensity: float = 1.0
    angle: float = 45.0  # degrees
    size: float = 1.0  # for area lights


class LightingSetup(BaseModel):
    """Complete lighting setup for the scene."""
    lights: List[LightSource] = Field(default_factory=list)
    hdri_map: Optional[str] = None
    ambient_intensity: float = 0.1
    exposure: float = 1.0


class CameraSetup(BaseModel):
    """Camera configuration for the scene."""
    position: Coordinate3D = Field(default_factory=Coordinate3D)
    target: Coordinate3D = Field(default_factory=Coordinate3D)
    focal_length: float = 35.0  # mm
    aperture: float = 2.8  # f-stop
    sensor_size: float = 36.0  # mm (full frame)
    depth_of_field: bool = True
    focus_distance: float = 5.0


class ValidationIssue(BaseModel):
    """A validation issue found by the Critic."""
    severity: str = "warning"  # error, warning, info
    category: str = ""  # clipping, floating, overexposure, prompt_alignment
    description: str = ""
    affected_object_id: Optional[str] = None
    suggested_fix: Optional[str] = None


class MasterPlan(BaseModel):
    """The master plan created by the Orchestrator."""
    original_prompt: str = ""
    interpreted_mood: str = ""
    required_objects: List[str] = Field(default_factory=list)
    spatial_requirements: Dict[str, Any] = Field(default_factory=dict)
    material_requirements: Dict[str, Any] = Field(default_factory=dict)
    lighting_requirements: Dict[str, Any] = Field(default_factory=dict)
    execution_order: List[str] = Field(default_factory=list)


def merge_lists(left: List[Any], right: List[Any]) -> List[Any]:
    """Merge two lists, appending right to left."""
    return left + right


def merge_dicts(left: Dict[str, Any], right: Dict[str, Any]) -> Dict[str, Any]:
    """Merge two dicts, right values override left."""
    return {**left, **right}


def replace_list(left: List[Any], right: List[Any]) -> List[Any]:
    """Replace the list entirely if right is non-empty, otherwise keep left."""
    return right if right else left


def replace_validation_issues(left: List[Any], right: List[Any]) -> List[Any]:
    """Replace validation issues entirely (don't accumulate across iterations)."""
    return right if right else left


class AgentState(TypedDict):
    """
    The shared state for the multi-agent LangGraph workflow.
    Uses Annotated types with reducers for proper state updates.
    """
    # User input
    user_prompt: str
    
    # Master plan from Orchestrator
    master_plan: Optional[MasterPlan]
    
    # Scene objects (REPLACED each iteration, not accumulated)
    scene_objects: Annotated[List[SceneObject], replace_list]
    
    # Lighting and camera from Cinematographer
    lighting_setup: Optional[LightingSetup]
    camera_setup: Optional[CameraSetup]
    
    # Validation from Critic (REPLACED each iteration, not accumulated)
    validation_issues: Annotated[List[ValidationIssue], replace_validation_issues]
    validation_passed: bool
    
    # Workflow tracking
    current_agent: str
    workflow_status: WorkflowStatus
    iteration_count: int
    max_iterations: int
    
    # Message history for context (accumulated)
    messages: Annotated[List[Dict[str, Any]], operator.add]
    
    # Error tracking (accumulated)
    errors: Annotated[List[str], operator.add]
    
    # Final output
    final_report: Optional[str]
