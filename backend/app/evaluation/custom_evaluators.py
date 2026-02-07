"""
Custom evaluators for Moo Director scene quality assessment.

These evaluators can be used with LangSmith's evaluation framework
to assess various aspects of generated 3D scenes.
"""
from typing import Dict, Any, List, Optional
import re
import logging

logger = logging.getLogger(__name__)


def scene_completeness_evaluator(
    run_output: Dict[str, Any],
    example: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Evaluate if the scene contains all requested objects.
    
    Checks if the generated scene includes all objects that were
    mentioned or implied in the original prompt.
    
    Args:
        run_output: The output from the scene generation run
        example: The example containing the input prompt and expected outputs
        
    Returns:
        Dict with 'score' (0-1) and 'reasoning'
    """
    try:
        # Extract scene objects from output
        scene_objects = run_output.get("scene_objects", [])
        if not scene_objects:
            scene_data = run_output.get("scene_data", {})
            scene_objects = scene_data.get("objects", [])
        
        # Extract object names
        generated_names = set()
        for obj in scene_objects:
            if isinstance(obj, dict):
                name = obj.get("name", "").lower()
            else:
                name = getattr(obj, "name", "").lower()
            if name:
                generated_names.add(name)
        
        # Get expected objects from the example (if provided)
        expected_objects = example.get("expected_objects", [])
        
        if not expected_objects:
            # If no expected objects defined, check if we have any objects at all
            score = 1.0 if len(generated_names) > 0 else 0.0
            return {
                "key": "scene_completeness",
                "score": score,
                "reasoning": f"Generated {len(generated_names)} objects: {', '.join(generated_names) or 'none'}"
            }
        
        # Calculate completeness score
        expected_set = set(obj.lower() for obj in expected_objects)
        found = generated_names.intersection(expected_set)
        score = len(found) / len(expected_set) if expected_set else 1.0
        
        missing = expected_set - generated_names
        reasoning = f"Found {len(found)}/{len(expected_set)} expected objects."
        if missing:
            reasoning += f" Missing: {', '.join(missing)}"
        
        return {
            "key": "scene_completeness",
            "score": score,
            "reasoning": reasoning
        }
        
    except Exception as e:
        logger.error(f"Scene completeness evaluation failed: {e}")
        return {
            "key": "scene_completeness",
            "score": 0.0,
            "reasoning": f"Evaluation error: {str(e)}"
        }


def prompt_alignment_evaluator(
    run_output: Dict[str, Any],
    example: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Evaluate how well the scene aligns with the original prompt.
    
    Uses keyword matching to assess if key terms from the prompt
    appear in the generated scene description or objects.
    
    Args:
        run_output: The output from the scene generation run
        example: The example containing the input prompt
        
    Returns:
        Dict with 'score' (0-1) and 'reasoning'
    """
    try:
        # Get the original prompt
        prompt = example.get("inputs", {}).get("prompt", "")
        if not prompt:
            prompt = example.get("prompt", "")
        
        # Extract key terms from prompt (nouns and adjectives)
        # Simple approach: extract words longer than 3 chars, excluding common words
        common_words = {
            "create", "make", "with", "and", "the", "that", "this", "from",
            "have", "will", "should", "could", "would", "into", "about",
            "scene", "room", "space"
        }
        words = re.findall(r'\b[a-zA-Z]{4,}\b', prompt.lower())
        key_terms = [w for w in words if w not in common_words]
        
        if not key_terms:
            return {
                "key": "prompt_alignment",
                "score": 1.0,
                "reasoning": "No specific terms to match in prompt"
            }
        
        # Build a string representation of the output
        output_text = _extract_text_from_output(run_output).lower()
        
        # Count how many key terms appear in the output
        found_terms = [term for term in key_terms if term in output_text]
        score = len(found_terms) / len(key_terms) if key_terms else 1.0
        
        return {
            "key": "prompt_alignment",
            "score": score,
            "reasoning": f"Found {len(found_terms)}/{len(key_terms)} key terms from prompt in output"
        }
        
    except Exception as e:
        logger.error(f"Prompt alignment evaluation failed: {e}")
        return {
            "key": "prompt_alignment",
            "score": 0.0,
            "reasoning": f"Evaluation error: {str(e)}"
        }


def validation_pass_evaluator(
    run_output: Dict[str, Any],
    example: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Evaluate if the scene passed internal validation.
    
    Checks the validation_passed flag and counts validation issues.
    
    Args:
        run_output: The output from the scene generation run
        example: The example (unused for this evaluator)
        
    Returns:
        Dict with 'score' (0 or 1) and 'reasoning'
    """
    try:
        # Check validation passed flag
        validation_passed = run_output.get("validation_passed", False)
        
        # Also check scene_data for API response format
        if not validation_passed:
            scene_data = run_output.get("scene_data", {})
            validation_report = run_output.get("validation_report", {})
            validation_passed = validation_report.get("passed", False)
        
        # Count validation issues
        validation_issues = run_output.get("validation_issues", [])
        error_count = sum(
            1 for issue in validation_issues 
            if _get_issue_severity(issue) == "error"
        )
        warning_count = sum(
            1 for issue in validation_issues 
            if _get_issue_severity(issue) == "warning"
        )
        
        score = 1.0 if validation_passed else 0.0
        reasoning = f"Validation {'passed' if validation_passed else 'failed'}."
        if validation_issues:
            reasoning += f" Issues: {error_count} errors, {warning_count} warnings"
        
        return {
            "key": "validation_pass",
            "score": score,
            "reasoning": reasoning
        }
        
    except Exception as e:
        logger.error(f"Validation pass evaluation failed: {e}")
        return {
            "key": "validation_pass",
            "score": 0.0,
            "reasoning": f"Evaluation error: {str(e)}"
        }


def object_count_evaluator(
    run_output: Dict[str, Any],
    example: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Evaluate if the scene has a reasonable number of objects.
    
    Checks if the object count is within expected range.
    
    Args:
        run_output: The output from the scene generation run
        example: The example with optional min/max object counts
        
    Returns:
        Dict with 'score' (0-1) and 'reasoning'
    """
    try:
        # Extract scene objects
        scene_objects = run_output.get("scene_objects", [])
        if not scene_objects:
            scene_data = run_output.get("scene_data", {})
            scene_objects = scene_data.get("objects", [])
        
        object_count = len(scene_objects)
        
        # Get expected range from example (or use defaults)
        min_objects = example.get("min_objects", 1)
        max_objects = example.get("max_objects", 20)
        
        # Calculate score based on whether count is in range
        if min_objects <= object_count <= max_objects:
            score = 1.0
            reasoning = f"Object count ({object_count}) is within expected range [{min_objects}, {max_objects}]"
        elif object_count < min_objects:
            # Partial score for being close
            score = object_count / min_objects if min_objects > 0 else 0.0
            reasoning = f"Object count ({object_count}) is below minimum ({min_objects})"
        else:
            # Over max objects - partial score
            score = max(0.5, max_objects / object_count)
            reasoning = f"Object count ({object_count}) exceeds maximum ({max_objects})"
        
        return {
            "key": "object_count",
            "score": score,
            "reasoning": reasoning
        }
        
    except Exception as e:
        logger.error(f"Object count evaluation failed: {e}")
        return {
            "key": "object_count",
            "score": 0.0,
            "reasoning": f"Evaluation error: {str(e)}"
        }


def _extract_text_from_output(output: Dict[str, Any]) -> str:
    """Extract searchable text from scene output."""
    parts = []
    
    # Add object names and materials
    scene_objects = output.get("scene_objects", [])
    if not scene_objects:
        scene_data = output.get("scene_data", {})
        scene_objects = scene_data.get("objects", [])
    
    for obj in scene_objects:
        if isinstance(obj, dict):
            parts.append(obj.get("name", ""))
            material = obj.get("material", {})
            if isinstance(material, dict):
                parts.append(material.get("name", ""))
        else:
            parts.append(getattr(obj, "name", ""))
            if hasattr(obj, "material") and obj.material:
                parts.append(getattr(obj.material, "name", ""))
    
    # Add lighting info
    lighting = output.get("lighting_setup", {})
    if not lighting:
        scene_data = output.get("scene_data", {})
        lighting = scene_data.get("lighting", {})
    
    if isinstance(lighting, dict):
        parts.append(lighting.get("hdri_map", ""))
        for light in lighting.get("lights", []):
            if isinstance(light, dict):
                parts.append(light.get("name", ""))
    
    # Add master plan info if available
    master_plan = output.get("master_plan")
    if master_plan:
        if isinstance(master_plan, dict):
            parts.append(master_plan.get("interpreted_mood", ""))
            parts.extend(master_plan.get("required_objects", []))
        else:
            parts.append(getattr(master_plan, "interpreted_mood", ""))
            parts.extend(getattr(master_plan, "required_objects", []))
    
    return " ".join(str(p) for p in parts if p)


def _get_issue_severity(issue) -> str:
    """Extract severity from a validation issue."""
    if isinstance(issue, dict):
        return issue.get("severity", "").lower()
    return getattr(issue, "severity", "").lower()
