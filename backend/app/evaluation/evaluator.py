"""
LangSmith evaluation utilities for Moo Director.

Provides functions to create evaluation datasets, run evaluations,
and retrieve evaluation results using LangSmith.
"""
from typing import Dict, Any, List, Optional, Callable
import logging
import asyncio
from datetime import datetime

from langsmith import Client
from langsmith.evaluation import evaluate

from ..config import get_settings
from ..workflow.graph import run_workflow
from .custom_evaluators import (
    scene_completeness_evaluator,
    prompt_alignment_evaluator,
    validation_pass_evaluator,
    object_count_evaluator,
)

logger = logging.getLogger(__name__)

# Default evaluation examples for 3D scene generation
DEFAULT_EVALUATION_EXAMPLES = [
    {
        "inputs": {"prompt": "Create a cozy bedroom with a white bed, wooden desk, and warm morning light"},
        "expected_objects": ["bed", "desk"],
        "min_objects": 2,
        "max_objects": 10,
    },
    {
        "inputs": {"prompt": "Create a modern office with a glass desk, ergonomic chair, and ambient lighting"},
        "expected_objects": ["desk", "chair"],
        "min_objects": 2,
        "max_objects": 10,
    },
    {
        "inputs": {"prompt": "Create a minimalist living room with a white sofa, coffee table, and natural light"},
        "expected_objects": ["sofa", "table"],
        "min_objects": 2,
        "max_objects": 8,
    },
    {
        "inputs": {"prompt": "Create a rustic kitchen with wooden cabinets, marble countertop, and pendant lights"},
        "expected_objects": ["cabinet", "countertop", "light"],
        "min_objects": 3,
        "max_objects": 15,
    },
    {
        "inputs": {"prompt": "Create a zen garden with bamboo plants, stone path, and water feature"},
        "expected_objects": ["plant", "path", "water"],
        "min_objects": 3,
        "max_objects": 12,
    },
]


def _get_langsmith_client() -> Optional[Client]:
    """
    Get a LangSmith client if configured.
    
    Returns:
        LangSmith Client or None if not configured.
    """
    settings = get_settings()
    if not settings.langchain_api_key or settings.langchain_api_key == "your_langsmith_api_key_here":
        logger.warning("LangSmith API key not configured")
        return None
    
    return Client(
        api_key=settings.langchain_api_key,
        api_url=settings.langchain_endpoint,
    )


def create_evaluation_dataset(
    dataset_name: str = "3d-scene-prompts",
    description: str = "Evaluation dataset for 3D scene generation prompts",
    examples: Optional[List[Dict[str, Any]]] = None,
) -> Optional[str]:
    """
    Create an evaluation dataset in LangSmith.
    
    Args:
        dataset_name: Name for the dataset
        description: Description of the dataset
        examples: List of example dicts with 'inputs' and optional expected values.
                 If None, uses DEFAULT_EVALUATION_EXAMPLES.
    
    Returns:
        Dataset ID if created successfully, None otherwise.
    """
    client = _get_langsmith_client()
    if not client:
        return None
    
    try:
        # Check if dataset already exists
        existing_datasets = list(client.list_datasets(dataset_name=dataset_name))
        if existing_datasets:
            logger.info(f"Dataset '{dataset_name}' already exists")
            return str(existing_datasets[0].id)
        
        # Create new dataset
        dataset = client.create_dataset(
            dataset_name=dataset_name,
            description=description,
        )
        
        # Add examples
        examples = examples or DEFAULT_EVALUATION_EXAMPLES
        for example in examples:
            client.create_example(
                inputs=example.get("inputs", {}),
                outputs=example.get("outputs", {}),
                metadata={
                    "expected_objects": example.get("expected_objects", []),
                    "min_objects": example.get("min_objects", 1),
                    "max_objects": example.get("max_objects", 20),
                },
                dataset_id=dataset.id,
            )
        
        logger.info(f"Created dataset '{dataset_name}' with {len(examples)} examples")
        return str(dataset.id)
        
    except Exception as e:
        logger.error(f"Failed to create evaluation dataset: {e}")
        return None


def list_datasets() -> List[Dict[str, Any]]:
    """
    List all evaluation datasets.
    
    Returns:
        List of dataset information dicts.
    """
    client = _get_langsmith_client()
    if not client:
        return []
    
    try:
        datasets = []
        for ds in client.list_datasets():
            datasets.append({
                "id": str(ds.id),
                "name": ds.name,
                "description": ds.description,
                "created_at": ds.created_at.isoformat() if ds.created_at else None,
                "example_count": ds.example_count,
            })
        return datasets
    except Exception as e:
        logger.error(f"Failed to list datasets: {e}")
        return []


async def _run_scene_generation(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run scene generation for evaluation.
    
    Args:
        inputs: Dict containing 'prompt' key
        
    Returns:
        Scene generation output
    """
    prompt = inputs.get("prompt", "")
    if not prompt:
        return {"error": "No prompt provided"}
    
    try:
        result = await run_workflow(
            user_prompt=prompt,
            max_iterations=2,  # Limit iterations for evaluation
            store_in_memory=False,  # Don't pollute memory with eval runs
        )
        return result
    except Exception as e:
        logger.error(f"Scene generation failed during evaluation: {e}")
        return {"error": str(e)}


def run_scene_evaluation(
    dataset_name: str = "3d-scene-prompts",
    experiment_prefix: str = "moo-director-eval",
    evaluators: Optional[List[Callable]] = None,
    max_concurrency: int = 2,
) -> Optional[Dict[str, Any]]:
    """
    Run evaluation on a dataset.
    
    Args:
        dataset_name: Name of the dataset to evaluate against
        experiment_prefix: Prefix for the experiment name
        evaluators: List of evaluator functions. If None, uses default evaluators.
        max_concurrency: Maximum number of concurrent evaluations
        
    Returns:
        Evaluation results summary or None if failed.
    """
    client = _get_langsmith_client()
    if not client:
        logger.error("LangSmith client not available - check API key configuration")
        return None
    
    # Use default evaluators if none provided
    if evaluators is None:
        evaluators = [
            scene_completeness_evaluator,
            prompt_alignment_evaluator,
            validation_pass_evaluator,
            object_count_evaluator,
        ]
    
    try:
        # Check if dataset exists
        existing_datasets = list(client.list_datasets(dataset_name=dataset_name))
        if not existing_datasets:
            logger.error(f"Dataset '{dataset_name}' not found. Create it first using /evaluation/datasets/create")
            return None
        
        # Create experiment name with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        experiment_name = f"{experiment_prefix}_{timestamp}"
        
        logger.info(f"Starting evaluation: {experiment_name} on dataset: {dataset_name}")
        
        # Define the target function that wraps our async workflow
        def target_func(inputs: Dict[str, Any]) -> Dict[str, Any]:
            try:
                return asyncio.run(_run_scene_generation(inputs))
            except Exception as e:
                logger.error(f"Target function failed: {e}")
                return {"error": str(e)}
        
        # Run evaluation using langsmith
        results = evaluate(
            target_func,
            data=dataset_name,
            evaluators=evaluators,
            experiment_prefix=experiment_name,
            max_concurrency=max_concurrency,
        )
        
        # Summarize results - handle both generator and list cases
        summary = {
            "experiment_name": experiment_name,
            "dataset_name": dataset_name,
            "evaluator_count": len(evaluators),
            "results": [],
        }
        
        # Process results - results might be a generator or ExperimentResults object
        try:
            # Try to iterate over results
            result_list = list(results) if hasattr(results, '__iter__') else []
            for result in result_list:
                # Handle different result formats
                if hasattr(result, 'dict'):
                    result = result.dict()
                elif hasattr(result, '__dict__'):
                    result = vars(result)
                
                if isinstance(result, dict):
                    result_dict = {
                        "input": result.get("input", result.get("inputs", {})),
                        "output": result.get("output", result.get("outputs", {})),
                        "scores": {},
                    }
                    
                    # Extract evaluation scores
                    eval_results = result.get("evaluation_results", result.get("feedback", []))
                    if eval_results:
                        for eval_result in eval_results:
                            if hasattr(eval_result, 'dict'):
                                eval_result = eval_result.dict()
                            elif hasattr(eval_result, '__dict__'):
                                eval_result = vars(eval_result)
                            
                            if isinstance(eval_result, dict):
                                key = eval_result.get("key", "unknown")
                                score = eval_result.get("score", 0)
                                result_dict["scores"][key] = score
                    
                    summary["results"].append(result_dict)
        except Exception as iter_error:
            logger.warning(f"Could not iterate results: {iter_error}")
            # Still return summary with experiment name so user can check dashboard
        
        logger.info(f"Evaluation completed: {experiment_name}")
        return summary
        
    except Exception as e:
        logger.error(f"Failed to run evaluation: {e}", exc_info=True)
        return None


def get_evaluation_results(
    experiment_name: Optional[str] = None,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """
    Get evaluation results from LangSmith.
    
    Args:
        experiment_name: Filter by experiment name (optional)
        limit: Maximum number of results to return
        
    Returns:
        List of evaluation result summaries.
    """
    client = _get_langsmith_client()
    if not client:
        return []
    
    try:
        # List recent test runs/experiments
        projects = list(client.list_projects(limit=limit))
        
        results = []
        for project in projects:
            if experiment_name and experiment_name not in project.name:
                continue
                
            results.append({
                "id": str(project.id),
                "name": project.name,
                "created_at": project.created_at.isoformat() if project.created_at else None,
                "run_count": project.run_count,
            })
        
        return results
        
    except Exception as e:
        logger.error(f"Failed to get evaluation results: {e}")
        return []


async def quick_evaluate_prompt(prompt: str) -> Dict[str, Any]:
    """
    Quick evaluation of a single prompt without using datasets.
    
    Useful for ad-hoc testing and debugging.
    
    Args:
        prompt: The scene description prompt to evaluate
        
    Returns:
        Dict with generation result and evaluation scores.
    """
    # Run generation
    result = await _run_scene_generation({"prompt": prompt})
    
    # Create a mock example for evaluators
    example = {
        "inputs": {"prompt": prompt},
        "expected_objects": [],
        "min_objects": 1,
        "max_objects": 20,
    }
    
    # Run evaluators
    evaluations = {}
    for evaluator in [
        scene_completeness_evaluator,
        prompt_alignment_evaluator,
        validation_pass_evaluator,
        object_count_evaluator,
    ]:
        eval_result = evaluator(result, example)
        evaluations[eval_result["key"]] = {
            "score": eval_result["score"],
            "reasoning": eval_result["reasoning"],
        }
    
    return {
        "prompt": prompt,
        "result": result,
        "evaluations": evaluations,
        "overall_score": sum(e["score"] for e in evaluations.values()) / len(evaluations),
    }
