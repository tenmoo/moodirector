"""
The Orchestrator Agent - The Manager/Lead Art Director.
Primary Responsibility: Decomposition & Coordination.
"""
from typing import Dict, Any, List, Optional
import json
import logging

from .base import BaseAgent
from ..models.state import AgentState, MasterPlan, WorkflowStatus
from ..memory.scene_memory import get_scene_memory

logger = logging.getLogger(__name__)

ORCHESTRATOR_SYSTEM_PROMPT = """You are the Lead Art Director. Your role is to break down a 3D scene request into structured tasks for a team of specialized agents:

- Librarian: Fetches 3D assets from the library
- Architect: Places objects in 3D space with correct coordinates
- Material Scientist: Applies PBR materials and textures
- Cinematographer: Sets up lighting and camera

Your responsibilities:
1. Interpret the user's natural language request and extract the mood, style, and requirements
2. Create a Master Plan that lists all required objects, spatial relationships, materials, and lighting
3. Determine the order of operations (Librarian → Architect → Material Scientist → Cinematographer)
4. Route data between agents as needed
5. If the Critic finds errors, send correction commands to the appropriate agent

You do NOT perform the tasks yourself. You ONLY coordinate and delegate.

When creating a plan, output valid JSON with this structure:
{{
    "interpreted_mood": "description of the mood/atmosphere",
    "required_objects": ["list", "of", "objects"],
    "spatial_requirements": {{
        "primary_focal_point": "object name",
        "relationships": [{{"object": "name", "relative_to": "other", "position": "description"}}]
    }},
    "material_requirements": {{
        "object_name": {{"style": "description", "finish": "matte/glossy/etc"}}
    }},
    "lighting_requirements": {{
        "time_of_day": "morning/afternoon/evening/night",
        "mood": "warm/cool/neutral",
        "key_light_direction": "description"
    }},
    "execution_order": ["librarian", "architect", "material_scientist", "cinematographer"]
}}"""


class OrchestratorAgent(BaseAgent):
    """
    The Orchestrator coordinates all other agents.
    It interprets user requests and creates the master execution plan.
    Uses vector memory to retrieve similar past scenes for context.
    """
    
    def __init__(self, use_memory: bool = True):
        super().__init__(
            name="Orchestrator",
            description="Lead Art Director - Decomposes requests and coordinates agents",
            system_prompt=ORCHESTRATOR_SYSTEM_PROMPT
        )
        self.use_memory = use_memory
    
    async def process(self, state: AgentState) -> Dict[str, Any]:
        """
        Process the user prompt and create a master plan.
        Uses vector memory to find similar past scenes for context.
        """
        self.log_action("Starting decomposition", {"prompt": state.get("user_prompt", "")[:100]})
        
        user_prompt = state.get("user_prompt", "")
        
        if not user_prompt:
            return {
                "errors": ["No user prompt provided"],
                "workflow_status": WorkflowStatus.FAILED
            }
        
        # Check if we're in revision mode
        if state.get("workflow_status") == WorkflowStatus.REVISION:
            return await self._handle_revision(state)
        
        # Create the master plan
        try:
            # Retrieve similar past scenes from memory
            memory_context = await self._get_memory_context(user_prompt)
            
            # Build the prompt with memory context
            prompt_parts = [f"Create a detailed master plan for this 3D scene request: {user_prompt}"]
            
            if memory_context:
                prompt_parts.append(f"\n\n{memory_context}")
            
            plan_response = await self.invoke_llm(
                input_text="\n".join(prompt_parts)
            )
            
            # Parse the JSON from the response
            master_plan = self._parse_master_plan(plan_response, user_prompt)
            
            self.log_action("Master plan created", {
                "objects": len(master_plan.required_objects),
                "mood": master_plan.interpreted_mood,
                "used_memory": bool(memory_context)
            })
            
            return {
                "master_plan": master_plan,
                "current_agent": "librarian",
                "workflow_status": WorkflowStatus.IN_PROGRESS,
                "messages": [{
                    "agent": self.name,
                    "action": "created_master_plan",
                    "content": f"Interpreted request as '{master_plan.interpreted_mood}' mood with {len(master_plan.required_objects)} objects" + 
                              (" (with memory context)" if memory_context else "")
                }]
            }
            
        except Exception as e:
            logger.error(f"Orchestrator failed to create plan: {e}")
            return {
                "errors": [f"Failed to create master plan: {str(e)}"],
                "workflow_status": WorkflowStatus.FAILED
            }
    
    async def _get_memory_context(self, user_prompt: str) -> Optional[str]:
        """
        Retrieve similar past scenes from vector memory.
        
        Args:
            user_prompt: The current user request
            
        Returns:
            Formatted context string or None
        """
        if not self.use_memory:
            return None
        
        try:
            memory = get_scene_memory()
            similar_scenes = memory.search_similar_scenes(
                query=user_prompt,
                n_results=3,
                min_score=0.3  # Only include reasonably similar scenes
            )
            
            if not similar_scenes:
                return None
            
            self.log_action("Retrieved similar scenes from memory", {
                "count": len(similar_scenes),
                "top_similarity": similar_scenes[0]["similarity"] if similar_scenes else 0
            })
            
            # Format the context
            context_parts = [
                "REFERENCE: Here are similar scenes you've created before that may help:"
            ]
            
            for i, scene in enumerate(similar_scenes, 1):
                context_parts.append(
                    f"\n{i}. \"{scene['user_prompt'][:100]}...\"\n"
                    f"   Mood: {scene['interpreted_mood']}\n"
                    f"   Objects: {', '.join(scene['object_names'][:5])}\n"
                    f"   Lighting: {scene['lighting_mood']}\n"
                    f"   Similarity: {scene['similarity']:.0%}"
                )
            
            context_parts.append(
                "\nYou can use these as inspiration, but create a unique plan for the current request."
            )
            
            return "\n".join(context_parts)
            
        except Exception as e:
            logger.warning(f"Failed to retrieve memory context: {e}")
            return None
    
    async def _handle_revision(self, state: AgentState) -> Dict[str, Any]:
        """Handle revision requests from the Critic."""
        validation_issues = state.get("validation_issues", [])
        
        if not validation_issues:
            return {
                "workflow_status": WorkflowStatus.COMPLETED,
                "messages": [{
                    "agent": self.name,
                    "action": "completed",
                    "content": "No issues to revise. Workflow complete."
                }]
            }
        
        # Summarize issues by category to avoid token overflow
        issue_summary = self._summarize_validation_issues(validation_issues)
        
        # Build concise revision context
        revision_context = f"User Request: {state.get('user_prompt', '')[:200]}\n"
        revision_context += f"Scene has {len(state.get('scene_objects', []))} objects.\n"
        revision_context += f"\nValidation Summary ({len(validation_issues)} total issues):\n"
        revision_context += issue_summary
        
        response = await self.invoke_llm(
            input_text="Based on these validation issues, which agent should perform the revision and what should they do?",
            context=revision_context
        )
        
        # Determine next agent based on issue categories
        next_agent = self._determine_revision_agent(validation_issues)
        
        return {
            "current_agent": next_agent,
            "workflow_status": WorkflowStatus.IN_PROGRESS,
            "messages": [{
                "agent": self.name,
                "action": "routing_revision",
                "content": f"Routing to {next_agent} for revision: {response[:200]}"
            }]
        }
    
    def _summarize_validation_issues(self, issues: List) -> str:
        """Summarize validation issues by category to reduce token usage."""
        from collections import Counter
        
        # Count issues by category and severity
        error_categories = Counter()
        warning_categories = Counter()
        
        for issue in issues:
            category = getattr(issue, 'category', 'unknown')
            severity = getattr(issue, 'severity', 'warning')
            
            if severity == 'error':
                error_categories[category] += 1
            else:
                warning_categories[category] += 1
        
        summary_parts = []
        
        if error_categories:
            summary_parts.append("ERRORS:")
            for category, count in error_categories.most_common(5):
                summary_parts.append(f"  - {category}: {count} issues")
        
        if warning_categories:
            summary_parts.append("WARNINGS:")
            for category, count in warning_categories.most_common(5):
                summary_parts.append(f"  - {category}: {count} issues")
        
        # Include a few specific examples (max 5)
        summary_parts.append("\nSample issues to address:")
        for i, issue in enumerate(issues[:5]):
            desc = getattr(issue, 'description', '')[:100]
            fix = getattr(issue, 'suggested_fix', '')
            summary_parts.append(f"  {i+1}. {desc}")
            if fix:
                summary_parts.append(f"     Fix: {fix[:80]}")
        
        return "\n".join(summary_parts)
    
    def _parse_master_plan(self, response: str, original_prompt: str) -> MasterPlan:
        """Parse the LLM response into a MasterPlan object."""
        try:
            # Try to extract JSON from the response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = response[json_start:json_end]
                plan_data = json.loads(json_str)
                
                return MasterPlan(
                    original_prompt=original_prompt,
                    interpreted_mood=plan_data.get("interpreted_mood", "neutral"),
                    required_objects=plan_data.get("required_objects", []),
                    spatial_requirements=plan_data.get("spatial_requirements", {}),
                    material_requirements=plan_data.get("material_requirements", {}),
                    lighting_requirements=plan_data.get("lighting_requirements", {}),
                    execution_order=plan_data.get("execution_order", [
                        "librarian", "architect", "material_scientist", "cinematographer"
                    ])
                )
        except json.JSONDecodeError:
            logger.warning("Could not parse JSON from orchestrator response, using defaults")
        
        # Fallback: create a basic plan
        return MasterPlan(
            original_prompt=original_prompt,
            interpreted_mood="as described",
            required_objects=self._extract_objects_from_prompt(original_prompt),
            execution_order=["librarian", "architect", "material_scientist", "cinematographer"]
        )
    
    def _extract_objects_from_prompt(self, prompt: str) -> List[str]:
        """Extract object names from a natural language prompt."""
        # Simple extraction - in production, this would use NER or the LLM
        common_3d_objects = [
            "bed", "desk", "chair", "table", "lamp", "sofa", "couch",
            "window", "door", "shelf", "bookshelf", "plant", "rug",
            "curtain", "mirror", "painting", "clock", "vase", "books"
        ]
        
        prompt_lower = prompt.lower()
        found_objects = [obj for obj in common_3d_objects if obj in prompt_lower]
        
        return found_objects if found_objects else ["primary_object"]
    
    def _determine_revision_agent(self, issues: List) -> str:
        """Determine which agent should handle revision based on issue types."""
        for issue in issues:
            category = issue.category.lower() if hasattr(issue, 'category') else ""
            
            if category in ["clipping", "floating", "placement"]:
                return "architect"
            elif category in ["material", "texture", "color"]:
                return "material_scientist"
            elif category in ["lighting", "exposure", "camera"]:
                return "cinematographer"
            elif category in ["missing_asset", "asset"]:
                return "librarian"
        
        return "architect"  # Default to architect for spatial issues
