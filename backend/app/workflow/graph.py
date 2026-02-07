"""
LangGraph workflow for the Moo Director multi-agent system.
Implements the agent collaboration and agentic workflow.
"""
from typing import Dict, Any, Optional, Literal
import logging
import asyncio
import uuid

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from ..models.state import AgentState, WorkflowStatus, MasterPlan
from ..agents import (
    OrchestratorAgent,
    ArchitectAgent,
    LibrarianAgent,
    MaterialScientistAgent,
    CinematographerAgent,
    CriticAgent
)
from ..memory.scene_memory import get_scene_memory

logger = logging.getLogger(__name__)

# Initialize all agents
orchestrator = OrchestratorAgent()
librarian = LibrarianAgent()
architect = ArchitectAgent()
material_scientist = MaterialScientistAgent()
cinematographer = CinematographerAgent()
critic = CriticAgent()


async def orchestrator_node(state: AgentState) -> Dict[str, Any]:
    """Orchestrator node - decomposes tasks and coordinates."""
    logger.info("Executing Orchestrator node")
    return await orchestrator.process(state)


async def librarian_node(state: AgentState) -> Dict[str, Any]:
    """Librarian node - fetches assets."""
    logger.info("Executing Librarian node")
    return await librarian.process(state)


async def architect_node(state: AgentState) -> Dict[str, Any]:
    """Architect node - places objects in 3D space."""
    logger.info("Executing Architect node")
    return await architect.process(state)


async def material_scientist_node(state: AgentState) -> Dict[str, Any]:
    """Material Scientist node - applies materials."""
    logger.info("Executing Material Scientist node")
    return await material_scientist.process(state)


async def cinematographer_node(state: AgentState) -> Dict[str, Any]:
    """Cinematographer node - sets up lighting and camera."""
    logger.info("Executing Cinematographer node")
    return await cinematographer.process(state)


async def critic_node(state: AgentState) -> Dict[str, Any]:
    """Critic node - validates the scene."""
    logger.info("Executing Critic node")
    return await critic.process(state)


def route_from_orchestrator(state: AgentState) -> str:
    """Route from orchestrator to the next agent."""
    next_agent = state.get("current_agent", "librarian")
    status = state.get("workflow_status")
    
    if status == WorkflowStatus.FAILED:
        return END
    
    logger.info(f"Routing from Orchestrator to: {next_agent}")
    return next_agent


def route_from_critic(state: AgentState) -> str:
    """Route from critic - either complete or revision."""
    status = state.get("workflow_status")
    passed = state.get("validation_passed", False)
    
    if passed or status == WorkflowStatus.COMPLETED:
        logger.info("Validation passed, ending workflow")
        return END
    elif status == WorkflowStatus.REVISION:
        logger.info("Validation failed, routing to Orchestrator for revision")
        return "orchestrator"
    else:
        logger.info("Workflow ending")
        return END


def route_standard(state: AgentState) -> str:
    """Standard routing based on current_agent in state."""
    next_agent = state.get("current_agent")
    status = state.get("workflow_status")
    
    if status == WorkflowStatus.FAILED:
        return END
    
    if next_agent:
        logger.info(f"Routing to: {next_agent}")
        return next_agent
    
    return END


def create_workflow_graph() -> StateGraph:
    """
    Create the LangGraph workflow for 3D scene generation.
    
    Flow:
    1. Orchestrator decomposes the request
    2. Librarian fetches assets
    3. Architect places objects
    4. Material Scientist applies textures
    5. Cinematographer sets lighting/camera
    6. Critic validates
    7. If issues: back to Orchestrator for revision
    8. If passed: complete
    """
    
    # Create the state graph
    workflow = StateGraph(AgentState)
    
    # Add all agent nodes
    workflow.add_node("orchestrator", orchestrator_node)
    workflow.add_node("librarian", librarian_node)
    workflow.add_node("architect", architect_node)
    workflow.add_node("material_scientist", material_scientist_node)
    workflow.add_node("cinematographer", cinematographer_node)
    workflow.add_node("critic", critic_node)
    
    # Set the entry point
    workflow.set_entry_point("orchestrator")
    
    # Add conditional edges from orchestrator
    workflow.add_conditional_edges(
        "orchestrator",
        route_from_orchestrator,
        {
            "librarian": "librarian",
            "architect": "architect",
            "material_scientist": "material_scientist",
            "cinematographer": "cinematographer",
            "critic": "critic",
            END: END
        }
    )
    
    # Add edges for the main flow
    workflow.add_conditional_edges(
        "librarian",
        route_standard,
        {
            "architect": "architect",
            "orchestrator": "orchestrator",
            END: END
        }
    )
    
    workflow.add_conditional_edges(
        "architect",
        route_standard,
        {
            "material_scientist": "material_scientist",
            "orchestrator": "orchestrator",
            END: END
        }
    )
    
    workflow.add_conditional_edges(
        "material_scientist",
        route_standard,
        {
            "cinematographer": "cinematographer",
            "orchestrator": "orchestrator",
            END: END
        }
    )
    
    workflow.add_conditional_edges(
        "cinematographer",
        route_standard,
        {
            "critic": "critic",
            "orchestrator": "orchestrator",
            END: END
        }
    )
    
    # Critic can either end or loop back for revision
    workflow.add_conditional_edges(
        "critic",
        route_from_critic,
        {
            "orchestrator": "orchestrator",
            END: END
        }
    )
    
    return workflow


def compile_workflow(checkpointer: Optional[MemorySaver] = None):
    """Compile the workflow graph with optional checkpointing."""
    graph = create_workflow_graph()
    
    if checkpointer:
        return graph.compile(checkpointer=checkpointer)
    
    return graph.compile()


async def run_workflow(
    user_prompt: str,
    max_iterations: int = 3,
    thread_id: Optional[str] = None,
    store_in_memory: bool = True
) -> Dict[str, Any]:
    """
    Run the complete workflow for a user prompt.
    
    Args:
        user_prompt: Natural language description of the 3D scene
        max_iterations: Maximum revision cycles allowed
        thread_id: Optional thread ID for checkpointing
        store_in_memory: Whether to store the completed scene in vector memory
        
    Returns:
        Final state with scene data and validation report
    """
    scene_id = thread_id or str(uuid.uuid4())
    logger.info(f"Starting workflow {scene_id} for prompt: {user_prompt[:100]}...")
    
    # Initialize state
    initial_state: AgentState = {
        "user_prompt": user_prompt,
        "master_plan": None,
        "scene_objects": [],
        "lighting_setup": None,
        "camera_setup": None,
        "validation_issues": [],
        "validation_passed": False,
        "current_agent": "orchestrator",
        "workflow_status": WorkflowStatus.PENDING,
        "iteration_count": 0,
        "max_iterations": max_iterations,
        "messages": [],
        "errors": [],
        "final_report": None
    }
    
    # Compile and run the workflow
    if thread_id:
        checkpointer = MemorySaver()
        app = compile_workflow(checkpointer)
        config = {"configurable": {"thread_id": thread_id}}
        
        # Use ainvoke to get the full final state (not astream which gives partial events)
        final_state = await app.ainvoke(initial_state, config)
    else:
        app = compile_workflow()
        final_state = await app.ainvoke(initial_state)
    
    logger.info(f"Workflow completed with status: {final_state.get('workflow_status')}")
    
    # Store completed scene in vector memory
    if store_in_memory and final_state.get("workflow_status") == WorkflowStatus.COMPLETED:
        await _store_scene_in_memory(scene_id, final_state)
    
    # Add scene_id to the result
    final_state["scene_id"] = scene_id
    
    return final_state


async def _store_scene_in_memory(scene_id: str, state: Dict[str, Any]) -> None:
    """
    Store a completed scene in vector memory for future retrieval.
    
    Args:
        scene_id: Unique identifier for the scene
        state: The final workflow state
    """
    try:
        memory = get_scene_memory()
        
        # Extract validation score from issues (approximate)
        validation_issues = state.get("validation_issues", [])
        error_count = sum(1 for i in validation_issues if getattr(i, 'severity', '') == 'error')
        warning_count = sum(1 for i in validation_issues if getattr(i, 'severity', '') == 'warning')
        validation_score = max(0, 100 - (error_count * 15) - (warning_count * 5))
        
        memory.store_scene(
            scene_id=scene_id,
            user_prompt=state.get("user_prompt", ""),
            master_plan=state.get("master_plan"),
            scene_objects=state.get("scene_objects", []),
            lighting_setup=state.get("lighting_setup"),
            camera_setup=state.get("camera_setup"),
            validation_passed=state.get("validation_passed", False),
            validation_score=validation_score
        )
        
        logger.info(f"Stored scene {scene_id} in vector memory")
        
    except Exception as e:
        logger.error(f"Failed to store scene in memory: {e}")


# Synchronous wrapper for non-async contexts
def run_workflow_sync(
    user_prompt: str,
    max_iterations: int = 3
) -> Dict[str, Any]:
    """Synchronous wrapper for run_workflow."""
    return asyncio.run(run_workflow(user_prompt, max_iterations))
