"""API routes for the Moo Director system."""
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel, Field
import uuid
import logging
import time

from ..workflow import run_workflow
from ..models.messages import SceneRequest, SceneResponse
from ..models.state import WorkflowStatus
from ..memory.scene_memory import get_scene_memory
from ..evaluation import (
    create_evaluation_dataset,
    run_scene_evaluation,
    get_evaluation_results,
    list_datasets,
    quick_evaluate_prompt,
)

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory storage for async job tracking
job_storage: Dict[str, Dict[str, Any]] = {}


class CreateSceneRequest(BaseModel):
    """Request to create a new 3D scene."""
    prompt: str = Field(..., description="Natural language description of the scene")
    max_iterations: int = Field(default=3, ge=1, le=5, description="Maximum revision cycles")
    async_mode: bool = Field(default=False, description="Run asynchronously")


class JobStatus(BaseModel):
    """Status of an async job."""
    job_id: str
    status: str
    progress: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@router.post("/scene/create", response_model=SceneResponse)
async def create_scene(request: CreateSceneRequest) -> SceneResponse:
    """
    Create a new 3D scene from a natural language prompt.
    
    The multi-agent system will:
    1. Orchestrator: Decompose the request into tasks
    2. Librarian: Fetch required 3D assets
    3. Architect: Place objects in 3D space
    4. Material Scientist: Apply PBR materials
    5. Cinematographer: Set up lighting and camera
    6. Critic: Validate and iterate if needed
    """
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    logger.info(f"Creating scene {request_id}: {request.prompt[:100]}...")
    
    try:
        # Run the workflow
        result = await run_workflow(
            user_prompt=request.prompt,
            max_iterations=request.max_iterations,
            thread_id=request_id
        )
        
        processing_time = (time.time() - start_time) * 1000
        
        # Extract scene data
        scene_data = {
            "objects": [
                {
                    "id": obj.id,
                    "name": obj.name,
                    "asset_path": obj.asset_path,
                    "position": obj.position.to_dict() if obj.position else None,
                    "rotation": obj.rotation.to_dict() if obj.rotation else None,
                    "scale": obj.scale.to_dict() if obj.scale else None,
                    "material": obj.material.model_dump() if obj.material else None,
                    "status": obj.status
                }
                for obj in result.get("scene_objects", [])
            ],
            "lighting": result.get("lighting_setup").model_dump() if result.get("lighting_setup") else None,
            "camera": result.get("camera_setup").model_dump() if result.get("camera_setup") else None,
        }
        
        # Extract validation report
        validation_report = {
            "passed": result.get("validation_passed", False),
            "issues": [
                issue.model_dump() for issue in result.get("validation_issues", [])
            ],
            "final_report": result.get("final_report")
        }
        
        status = "completed" if result.get("validation_passed") else "completed_with_issues"
        
        return SceneResponse(
            request_id=request_id,
            status=status,
            scene_data=scene_data,
            validation_report=validation_report,
            message=f"Scene created with {len(scene_data['objects'])} objects",
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        logger.error(f"Scene creation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scene/create-async", response_model=JobStatus)
async def create_scene_async(
    request: CreateSceneRequest,
    background_tasks: BackgroundTasks
) -> JobStatus:
    """
    Create a scene asynchronously. Returns a job ID to poll for status.
    """
    job_id = str(uuid.uuid4())
    
    # Initialize job
    job_storage[job_id] = {
        "status": "pending",
        "progress": "Initializing...",
        "result": None,
        "error": None
    }
    
    # Add background task
    background_tasks.add_task(
        _run_workflow_background,
        job_id,
        request.prompt,
        request.max_iterations
    )
    
    return JobStatus(
        job_id=job_id,
        status="pending",
        progress="Job queued"
    )


@router.get("/scene/status/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str) -> JobStatus:
    """Get the status of an async scene creation job."""
    if job_id not in job_storage:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = job_storage[job_id]
    
    return JobStatus(
        job_id=job_id,
        status=job["status"],
        progress=job.get("progress"),
        result=job.get("result"),
        error=job.get("error")
    )


@router.get("/agents")
async def list_agents():
    """List all agents in the system with their descriptions."""
    return {
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


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "moo-director"}


# =============================================================================
# Memory Endpoints
# =============================================================================

class MemorySearchRequest(BaseModel):
    """Request to search scene memory."""
    query: str = Field(..., description="Search query (natural language)")
    n_results: int = Field(default=5, ge=1, le=20, description="Number of results")
    min_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Minimum similarity score")


class MemorySearchResult(BaseModel):
    """A single search result from memory."""
    id: str
    similarity: float
    user_prompt: str
    interpreted_mood: str
    object_count: int
    object_names: List[str]
    lighting_mood: str
    validation_passed: bool
    timestamp: str


class MemorySearchResponse(BaseModel):
    """Response from memory search."""
    query: str
    results: List[MemorySearchResult]
    total_in_memory: int


class MemoryStatsResponse(BaseModel):
    """Memory statistics."""
    total_scenes: int
    collection_name: str
    embedding_model: str


@router.post("/memory/search", response_model=MemorySearchResponse)
async def search_memory(request: MemorySearchRequest) -> MemorySearchResponse:
    """
    Search for similar scenes in memory using semantic similarity.
    
    This uses vector embeddings to find scenes similar to the query,
    even if they don't share exact keywords.
    
    Examples:
    - "cozy bedroom" will find scenes with "warm bedroom", "comfortable sleeping area"
    - "modern office" will find "contemporary workspace", "minimalist desk setup"
    """
    try:
        memory = get_scene_memory()
        results = memory.search_similar_scenes(
            query=request.query,
            n_results=request.n_results,
            min_score=request.min_score
        )
        
        return MemorySearchResponse(
            query=request.query,
            results=[MemorySearchResult(**r) for r in results],
            total_in_memory=memory.get_stats()["total_scenes"]
        )
        
    except Exception as e:
        logger.error(f"Memory search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memory/recent")
async def get_recent_scenes(
    limit: int = Query(default=10, ge=1, le=50, description="Number of scenes to return")
):
    """Get the most recently created scenes from memory."""
    try:
        memory = get_scene_memory()
        scenes = memory.get_recent_scenes(limit=limit)
        
        return {
            "scenes": scenes,
            "total_in_memory": memory.get_stats()["total_scenes"]
        }
        
    except Exception as e:
        logger.error(f"Failed to get recent scenes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memory/scene/{scene_id}")
async def get_scene_from_memory(scene_id: str):
    """Retrieve a specific scene from memory by ID."""
    try:
        memory = get_scene_memory()
        scene = memory.get_scene_by_id(scene_id)
        
        if not scene:
            raise HTTPException(status_code=404, detail="Scene not found in memory")
        
        return scene
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get scene {scene_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/memory/scene/{scene_id}")
async def delete_scene_from_memory(scene_id: str):
    """Delete a specific scene from memory."""
    try:
        memory = get_scene_memory()
        success = memory.delete_scene(scene_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Scene not found or could not be deleted")
        
        return {"message": f"Scene {scene_id} deleted", "success": True}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete scene {scene_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memory/stats", response_model=MemoryStatsResponse)
async def get_memory_stats() -> MemoryStatsResponse:
    """Get statistics about the scene memory."""
    try:
        memory = get_scene_memory()
        stats = memory.get_stats()
        
        return MemoryStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Failed to get memory stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/memory/clear")
async def clear_memory():
    """
    Clear all scenes from memory.
    
    WARNING: This action cannot be undone!
    """
    try:
        memory = get_scene_memory()
        count = memory.clear_all()
        
        return {
            "message": f"Cleared {count} scenes from memory",
            "scenes_deleted": count
        }
        
    except Exception as e:
        logger.error(f"Failed to clear memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _run_workflow_background(
    job_id: str,
    prompt: str,
    max_iterations: int
):
    """Background task to run the workflow."""
    try:
        job_storage[job_id]["status"] = "running"
        job_storage[job_id]["progress"] = "Starting workflow..."
        
        result = await run_workflow(
            user_prompt=prompt,
            max_iterations=max_iterations,
            thread_id=job_id
        )
        
        # Process result
        scene_data = {
            "objects": [
                obj.model_dump() if hasattr(obj, 'model_dump') else obj
                for obj in result.get("scene_objects", [])
            ],
            "lighting": result.get("lighting_setup").model_dump() if result.get("lighting_setup") else None,
            "camera": result.get("camera_setup").model_dump() if result.get("camera_setup") else None,
            "validation_passed": result.get("validation_passed"),
            "final_report": result.get("final_report")
        }
        
        job_storage[job_id]["status"] = "completed"
        job_storage[job_id]["result"] = scene_data
        job_storage[job_id]["progress"] = "Done"
        
    except Exception as e:
        logger.error(f"Background job {job_id} failed: {e}")
        job_storage[job_id]["status"] = "failed"
        job_storage[job_id]["error"] = str(e)


# =============================================================================
# Evaluation Endpoints (LangSmith)
# =============================================================================

class CreateDatasetRequest(BaseModel):
    """Request to create an evaluation dataset."""
    dataset_name: str = Field(default="3d-scene-prompts", description="Name for the dataset")
    description: str = Field(
        default="Evaluation dataset for 3D scene generation prompts",
        description="Description of the dataset"
    )


class RunEvaluationRequest(BaseModel):
    """Request to run an evaluation."""
    dataset_name: str = Field(default="3d-scene-prompts", description="Dataset to evaluate against")
    experiment_prefix: str = Field(default="moo-director-eval", description="Prefix for experiment name")
    max_concurrency: int = Field(default=2, ge=1, le=5, description="Max concurrent evaluations")


class QuickEvaluateRequest(BaseModel):
    """Request to quickly evaluate a single prompt."""
    prompt: str = Field(..., description="Scene description prompt to evaluate")


@router.post("/evaluation/datasets/create")
async def create_dataset(request: CreateDatasetRequest):
    """
    Create a new evaluation dataset in LangSmith.
    
    This creates a dataset with default evaluation examples for 3D scene generation.
    Requires LANGCHAIN_API_KEY to be configured.
    """
    dataset_id = create_evaluation_dataset(
        dataset_name=request.dataset_name,
        description=request.description,
    )
    
    if not dataset_id:
        raise HTTPException(
            status_code=500,
            detail="Failed to create dataset. Check if LangSmith API key is configured."
        )
    
    return {
        "message": f"Dataset '{request.dataset_name}' created successfully",
        "dataset_id": dataset_id,
    }


@router.get("/evaluation/datasets")
async def list_evaluation_datasets():
    """
    List all evaluation datasets in LangSmith.
    
    Requires LANGCHAIN_API_KEY to be configured.
    """
    datasets = list_datasets()
    
    return {
        "datasets": datasets,
        "count": len(datasets),
    }


@router.post("/evaluation/run")
async def run_evaluation(
    request: RunEvaluationRequest,
    background_tasks: BackgroundTasks,
):
    """
    Run evaluation on a dataset.
    
    This runs scene generation against all examples in the dataset
    and evaluates the results using custom evaluators:
    - scene_completeness: Are all requested objects present?
    - prompt_alignment: Does the output match the prompt?
    - validation_pass: Did the scene pass internal validation?
    - object_count: Is the object count reasonable?
    
    Note: This can take several minutes depending on dataset size.
    
    Prerequisites:
    1. LANGCHAIN_API_KEY must be configured in .env
    2. Dataset must be created first via /evaluation/datasets/create
    """
    # Check if LangSmith is configured
    from ..config import get_settings
    settings = get_settings()
    if not settings.langchain_api_key or settings.langchain_api_key == "your_langsmith_api_key_here":
        raise HTTPException(
            status_code=400,
            detail="LangSmith API key not configured. Add LANGCHAIN_API_KEY to your .env file."
        )
    
    # Check if dataset exists first
    datasets = list_datasets()
    dataset_names = [d["name"] for d in datasets]
    if request.dataset_name not in dataset_names:
        raise HTTPException(
            status_code=404,
            detail=f"Dataset '{request.dataset_name}' not found. Create it first using POST /evaluation/datasets/create. Available datasets: {dataset_names}"
        )
    
    logger.info(f"Starting evaluation on dataset: {request.dataset_name}")
    
    # Run evaluation (this can take a while)
    try:
        results = run_scene_evaluation(
            dataset_name=request.dataset_name,
            experiment_prefix=request.experiment_prefix,
            max_concurrency=request.max_concurrency,
        )
    except Exception as e:
        logger.error(f"Evaluation failed with exception: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Evaluation failed: {str(e)}"
        )
    
    if not results:
        raise HTTPException(
            status_code=500,
            detail="Evaluation returned no results. Check server logs for details."
        )
    
    return {
        "message": "Evaluation completed. View detailed results in LangSmith dashboard.",
        "experiment_name": results.get("experiment_name"),
        "dataset_name": results.get("dataset_name"),
        "result_count": len(results.get("results", [])),
        "dashboard_url": f"https://smith.langchain.com/o/default/projects"
    }


@router.get("/evaluation/results")
async def get_results(
    experiment_name: Optional[str] = Query(None, description="Filter by experiment name"),
    limit: int = Query(10, ge=1, le=100, description="Max results to return"),
):
    """
    Get evaluation results from LangSmith.
    
    Returns a list of recent evaluation experiments.
    """
    results = get_evaluation_results(
        experiment_name=experiment_name,
        limit=limit,
    )
    
    return {
        "results": results,
        "count": len(results),
    }


@router.post("/evaluation/quick")
async def quick_evaluate(request: QuickEvaluateRequest):
    """
    Quickly evaluate a single prompt without using datasets.
    
    This runs the full scene generation pipeline and evaluates
    the result using all custom evaluators. Useful for ad-hoc testing.
    
    Note: This does NOT require LangSmith to be configured - evaluations
    are run locally. However, if LangSmith is configured, the generation
    will still be traced.
    """
    try:
        result = await quick_evaluate_prompt(request.prompt)
        
        return {
            "prompt": result["prompt"],
            "overall_score": result["overall_score"],
            "evaluations": result["evaluations"],
            "scene_objects_count": len(result.get("result", {}).get("scene_objects", [])),
            "validation_passed": result.get("result", {}).get("validation_passed", False),
        }
        
    except Exception as e:
        logger.error(f"Quick evaluation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
