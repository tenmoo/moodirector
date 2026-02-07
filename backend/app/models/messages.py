"""Message models for agent communication."""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class TaskType(str, Enum):
    """Types of tasks agents can perform."""
    DECOMPOSE = "decompose"
    FETCH_ASSETS = "fetch_assets"
    PLACE_OBJECTS = "place_objects"
    APPLY_MATERIALS = "apply_materials"
    SETUP_LIGHTING = "setup_lighting"
    SETUP_CAMERA = "setup_camera"
    VALIDATE = "validate"
    REVISE = "revise"


class TaskMessage(BaseModel):
    """A task message sent between agents."""
    task_id: str
    task_type: TaskType
    from_agent: str
    to_agent: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    priority: int = 1
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AgentResponse(BaseModel):
    """Response from an agent after completing a task."""
    agent_name: str
    task_id: str
    success: bool
    result: Dict[str, Any] = Field(default_factory=dict)
    message: str = ""
    artifacts: List[Dict[str, Any]] = Field(default_factory=list)
    next_agent: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ValidationResult(BaseModel):
    """Result from the Critic agent's validation."""
    passed: bool
    score: float = 0.0  # 0-100
    issues: List[Dict[str, Any]] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    requires_revision: bool = False
    revision_targets: List[str] = Field(default_factory=list)  # Agent names needing revision


class SceneRequest(BaseModel):
    """Request to create a 3D scene."""
    prompt: str = Field(..., description="Natural language description of the desired scene")
    style: Optional[str] = Field(default=None, description="Art style preference")
    constraints: Optional[Dict[str, Any]] = Field(default=None, description="Technical constraints")
    

class SceneResponse(BaseModel):
    """Response containing the generated scene data."""
    request_id: str
    status: str
    scene_data: Optional[Dict[str, Any]] = None
    validation_report: Optional[Dict[str, Any]] = None
    message: str = ""
    processing_time_ms: float = 0.0
