"""Base agent class for all specialized agents."""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langsmith import traceable
import logging

from ..config import get_settings
from ..models.state import AgentState

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the Moo Director system.
    Each agent has a specific role and system prompt.
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        system_prompt: str,
        model: Optional[str] = None
    ):
        self.name = name
        self.description = description
        self.system_prompt = system_prompt
        self.settings = get_settings()
        self.model_name = model or self.settings.default_model
        
        # Initialize the LLM
        self.llm = ChatGroq(
            api_key=self.settings.groq_api_key,
            model_name=self.model_name,
            temperature=0.7,
            max_tokens=4096,
        )
        
        # Create the prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            MessagesPlaceholder(variable_name="messages"),
            ("human", "{input}")
        ])
        
        logger.info(f"Initialized {self.name} agent with model {self.model_name}")
    
    @abstractmethod
    async def process(self, state: AgentState) -> Dict[str, Any]:
        """
        Process the current state and return updates.
        Must be implemented by each specialized agent.
        
        Args:
            state: The current workflow state
            
        Returns:
            Dict containing state updates
        """
        pass
    
    @traceable(run_type="llm")
    async def invoke_llm(self, input_text: str, context: Optional[str] = None) -> str:
        """
        Invoke the LLM with the given input.
        
        This method is decorated with @traceable for LangSmith observability,
        providing detailed traces of each agent's LLM invocations.
        
        Args:
            input_text: The user/task input
            context: Additional context to include
            
        Returns:
            The LLM's response text
        """
        messages = []
        
        if context:
            messages.append(HumanMessage(content=f"Context: {context}"))
        
        try:
            chain = self.prompt | self.llm
            response = await chain.ainvoke(
                {
                    "messages": messages,
                    "input": input_text
                },
                config={
                    "metadata": {
                        "agent_name": self.name,
                        "model": self.model_name,
                    },
                    "tags": ["agent", self.name.lower().replace(" ", "_")]
                }
            )
            return response.content
        except Exception as e:
            logger.error(f"{self.name} LLM invocation failed: {e}")
            raise
    
    def format_state_context(self, state: AgentState, max_objects: int = 10) -> str:
        """
        Format relevant state information as context for the LLM.
        
        Args:
            state: The current workflow state
            max_objects: Maximum number of objects to list (to avoid token overflow)
            
        Returns:
            Formatted context string
        """
        context_parts = [
            f"User Request: {state.get('user_prompt', 'No prompt provided')[:500]}"
        ]
        
        if state.get('master_plan'):
            plan = state['master_plan']
            # Only include key plan info, not the entire object
            context_parts.append(f"Mood: {plan.interpreted_mood}")
            context_parts.append(f"Required Objects: {', '.join(plan.required_objects[:10])}")
        
        if state.get('scene_objects'):
            objects = state['scene_objects']
            context_parts.append(f"Scene Objects: {len(objects)} total")
            # Only list first few objects to avoid token overflow
            for obj in objects[:max_objects]:
                context_parts.append(f"  - {obj.name}: {obj.status}")
            if len(objects) > max_objects:
                context_parts.append(f"  ... and {len(objects) - max_objects} more objects")
        
        if state.get('lighting_setup'):
            context_parts.append(f"Lighting: Configured")
        
        if state.get('validation_issues'):
            issues = state['validation_issues']
            context_parts.append(f"Validation Issues: {len(issues)} issues found")
        
        return "\n".join(context_parts)
    
    def log_action(self, action: str, details: Optional[Dict] = None):
        """Log an agent action for debugging and monitoring."""
        log_msg = f"[{self.name}] {action}"
        if details:
            log_msg += f" | Details: {details}"
        logger.info(log_msg)
