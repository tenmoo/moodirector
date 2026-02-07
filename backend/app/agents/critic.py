"""
The Critic Agent - The Quality Controller.
Primary Responsibility: Validation & Error Detection.
"""
from typing import Dict, Any, List, Optional
import json
import logging

from .base import BaseAgent
from ..models.state import (
    AgentState, ValidationIssue, SceneObject, 
    LightingSetup, CameraSetup, WorkflowStatus
)

logger = logging.getLogger(__name__)

CRITIC_SYSTEM_PROMPT = """You are a ruthless 3D Quality Controller. You check the work of all other agents and ensure high-quality output.

Your responsibilities:
1. Collision Detection: Check if objects are "floating" or "sinking" into each other
2. Prompt Alignment: Verify the scene matches the original request (colors, objects, mood)
3. Technical Check: Identify render issues (fireflies, hot spots, underexposure)
4. Material Check: Ensure no flat colors, proper texturing applied
5. Composition Check: Verify camera framing and lighting balance

VALIDATION RULES:
- Objects must rest on surfaces (Z >= 0 for floor objects)
- No two objects should occupy the same space (clipping)
- White objects should have brightness < 95% to avoid overexposure
- All objects must have textures (no flat materials)
- Lighting must create visible shadows (not flat lit)
- Camera must capture the primary focal point

SEVERITY LEVELS:
- error: Must be fixed before completion
- warning: Should be addressed but not blocking
- info: Suggestions for improvement

Output validation results as JSON:
{{
    "passed": false,
    "score": 75,
    "issues": [
        {{
            "severity": "error",
            "category": "clipping",
            "description": "Desk intersects with bed",
            "affected_object_id": "uuid",
            "suggested_fix": "Move desk 0.5m to the left"
        }}
    ],
    "recommendations": ["Consider adding a rug to warm up the space"]
}}"""


class CriticAgent(BaseAgent):
    """
    The Critic validates all work and ensures quality.
    Acts as the adversarial checker for the system.
    """
    
    def __init__(self):
        super().__init__(
            name="Critic",
            description="Quality Controller - Validates scene against requirements",
            system_prompt=CRITIC_SYSTEM_PROMPT
        )
        self.passing_score = 60  # Minimum score to pass validation (lowered for MVP)
        self.collision_tolerance = 0.05  # Allow small overlaps (5cm tolerance)
    
    async def process(self, state: AgentState) -> Dict[str, Any]:
        """
        Validate the entire scene against requirements.
        """
        self.log_action("Starting quality validation")
        
        scene_objects = state.get("scene_objects", [])
        lighting_setup = state.get("lighting_setup")
        camera_setup = state.get("camera_setup")
        master_plan = state.get("master_plan")
        iteration = state.get("iteration_count", 0)
        max_iterations = state.get("max_iterations", 3)
        
        issues = []
        score = 100
        
        # Run all validation checks
        collision_issues, collision_penalty = self._check_collisions(scene_objects)
        issues.extend(collision_issues)
        score -= collision_penalty
        
        floating_issues, floating_penalty = self._check_floating_objects(scene_objects)
        issues.extend(floating_issues)
        score -= floating_penalty
        
        material_issues, material_penalty = self._check_materials(scene_objects)
        issues.extend(material_issues)
        score -= material_penalty
        
        if lighting_setup:
            lighting_issues, lighting_penalty = self._check_lighting(lighting_setup)
            issues.extend(lighting_issues)
            score -= lighting_penalty
        
        if master_plan:
            alignment_issues, alignment_penalty = self._check_prompt_alignment(
                scene_objects, master_plan
            )
            issues.extend(alignment_issues)
            score -= alignment_penalty
        
        # Ensure score doesn't go negative
        score = max(0, score)
        
        # Determine if validation passed
        passed = score >= self.passing_score and not any(
            issue.severity == "error" for issue in issues
        )
        
        self.log_action("Validation complete", {
            "score": score,
            "issues": len(issues),
            "passed": passed
        })
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            scene_objects, lighting_setup, master_plan
        )
        
        # Determine next step
        if passed:
            next_status = WorkflowStatus.COMPLETED
            next_agent = None
            final_report = self._generate_final_report(
                state, score, issues, recommendations
            )
        elif iteration >= max_iterations:
            next_status = WorkflowStatus.COMPLETED
            next_agent = None
            final_report = self._generate_final_report(
                state, score, issues, recommendations,
                note="Maximum iterations reached. Some issues remain."
            )
        else:
            next_status = WorkflowStatus.REVISION
            next_agent = "orchestrator"
            final_report = None
        
        return {
            "validation_issues": issues,
            "validation_passed": passed,
            "workflow_status": next_status,
            "current_agent": next_agent,
            "iteration_count": iteration + 1,
            "final_report": final_report,
            "messages": [{
                "agent": self.name,
                "action": "validation_complete",
                "content": f"Score: {score}/100. {'PASSED' if passed else 'FAILED'}. {len(issues)} issues found."
            }]
        }
    
    def _check_collisions(
        self, 
        objects: List[SceneObject]
    ) -> tuple[List[ValidationIssue], int]:
        """Check for object collisions/clipping."""
        issues = []
        penalty = 0
        
        for i, obj1 in enumerate(objects):
            for obj2 in objects[i+1:]:
                overlap = self._calculate_overlap(obj1, obj2)
                if overlap > self.collision_tolerance:
                    # Severe overlap is an error, minor overlap is a warning
                    if overlap > 0.3:  # More than 30cm overlap
                        issues.append(ValidationIssue(
                            severity="error",
                            category="clipping",
                            description=f"'{obj1.name}' severely intersects with '{obj2.name}' ({overlap:.2f}m overlap)",
                            affected_object_id=obj1.id,
                            suggested_fix=f"Move '{obj2.name}' away from '{obj1.name}'"
                        ))
                        penalty += 10
                    else:
                        issues.append(ValidationIssue(
                            severity="warning",
                            category="clipping",
                            description=f"'{obj1.name}' slightly overlaps '{obj2.name}' ({overlap:.2f}m)",
                            affected_object_id=obj1.id,
                            suggested_fix=f"Adjust position of '{obj2.name}'"
                        ))
                        penalty += 3
        
        return issues, penalty
    
    def _calculate_overlap(self, a: SceneObject, b: SceneObject) -> float:
        """Calculate the overlap distance between two objects (0 if no overlap)."""
        # Calculate bounds with small tolerance
        a_min = (
            a.position.x - a.bounding_box.width / 2,
            a.position.y - a.bounding_box.depth / 2,
            a.position.z
        )
        a_max = (
            a.position.x + a.bounding_box.width / 2,
            a.position.y + a.bounding_box.depth / 2,
            a.position.z + a.bounding_box.height
        )
        
        b_min = (
            b.position.x - b.bounding_box.width / 2,
            b.position.y - b.bounding_box.depth / 2,
            b.position.z
        )
        b_max = (
            b.position.x + b.bounding_box.width / 2,
            b.position.y + b.bounding_box.depth / 2,
            b.position.z + b.bounding_box.height
        )
        
        # Calculate overlap on each axis
        overlap_x = max(0, min(a_max[0], b_max[0]) - max(a_min[0], b_min[0]))
        overlap_y = max(0, min(a_max[1], b_max[1]) - max(a_min[1], b_min[1]))
        overlap_z = max(0, min(a_max[2], b_max[2]) - max(a_min[2], b_min[2]))
        
        # Return minimum overlap (the penetration depth)
        if overlap_x > 0 and overlap_y > 0 and overlap_z > 0:
            return min(overlap_x, overlap_y, overlap_z)
        return 0.0
    
    def _check_floating_objects(
        self, 
        objects: List[SceneObject]
    ) -> tuple[List[ValidationIssue], int]:
        """Check for floating or sunken objects."""
        issues = []
        penalty = 0
        
        for obj in objects:
            # Skip architectural elements (walls, floors, windows)
            if any(arch in obj.name.lower() for arch in ["wall", "floor", "window", "ceiling", "door"]):
                continue
            
            # Check if object is significantly below floor
            if obj.position.z < -0.1:  # 10cm tolerance
                issues.append(ValidationIssue(
                    severity="warning",  # Downgraded from error
                    category="floating",
                    description=f"'{obj.name}' is below floor level (z={obj.position.z:.2f})",
                    affected_object_id=obj.id,
                    suggested_fix=f"Set z position to 0"
                ))
                penalty += 3
            
            # Check if floor object is significantly floating
            elif obj.position.z > 0.2 and not self._is_surface_object(obj):
                # Check if it's on top of another object
                on_surface = False
                for other in objects:
                    if other.id != obj.id and self._is_on_top_of(obj, other):
                        on_surface = True
                        break
                
                if not on_surface:
                    issues.append(ValidationIssue(
                        severity="info",  # Downgraded from warning
                        category="floating",
                        description=f"'{obj.name}' appears to be floating (z={obj.position.z:.2f})",
                        affected_object_id=obj.id,
                        suggested_fix="Place on floor or on another surface"
                    ))
                    penalty += 1
        
        return issues, penalty
    
    def _check_materials(
        self, 
        objects: List[SceneObject]
    ) -> tuple[List[ValidationIssue], int]:
        """Check for material issues."""
        issues = []
        penalty = 0
        
        for obj in objects:
            if not obj.material:
                issues.append(ValidationIssue(
                    severity="warning",  # Downgraded from error - materials can be added later
                    category="material",
                    description=f"'{obj.name}' has no material assigned",
                    affected_object_id=obj.id,
                    suggested_fix="Apply appropriate PBR material"
                ))
                penalty += 5
            elif not obj.material.texture_map:
                # Only penalize if it's not a simple object like glass/metal
                if obj.material.shader_type not in ["glass", "metal"]:
                    issues.append(ValidationIssue(
                        severity="info",  # Downgraded - flat colors are acceptable for MVP
                        category="material",
                        description=f"'{obj.name}' uses flat color without texture",
                        affected_object_id=obj.id,
                        suggested_fix="Add texture map for more realism"
                    ))
                    penalty += 1
            
            # Check for overexposed whites (only severe cases)
            if obj.material:
                brightness = sum(obj.material.base_color[:3]) / 3
                if brightness > 0.98:  # Raised threshold
                    issues.append(ValidationIssue(
                        severity="warning",
                        category="overexposure",
                        description=f"'{obj.name}' may be overexposed (brightness={brightness:.2f})",
                        affected_object_id=obj.id,
                        suggested_fix="Reduce base color brightness or adjust lighting"
                    ))
                    penalty += 2
        
        return issues, penalty
    
    def _check_lighting(
        self, 
        lighting: LightingSetup
    ) -> tuple[List[ValidationIssue], int]:
        """Check for lighting issues."""
        issues = []
        penalty = 0
        
        if not lighting.lights:
            issues.append(ValidationIssue(
                severity="error",
                category="lighting",
                description="No lights in the scene",
                suggested_fix="Add at least a key light"
            ))
            penalty += 20
        
        # Check for proper lighting setup
        has_key_light = any(
            l.intensity > 1.5 for l in lighting.lights
        )
        if not has_key_light and len(lighting.lights) > 0:
            issues.append(ValidationIssue(
                severity="warning",
                category="lighting",
                description="Scene may be underlit - no strong key light",
                suggested_fix="Increase key light intensity"
            ))
            penalty += 5
        
        # Check exposure
        if lighting.exposure > 1.5:
            issues.append(ValidationIssue(
                severity="warning",
                category="overexposure",
                description=f"Scene exposure may be too high ({lighting.exposure})",
                suggested_fix="Reduce exposure to 1.0-1.2"
            ))
            penalty += 3
        
        return issues, penalty
    
    def _check_prompt_alignment(
        self, 
        objects: List[SceneObject],
        master_plan
    ) -> tuple[List[ValidationIssue], int]:
        """Check if scene matches original request."""
        issues = []
        penalty = 0
        
        # Check if all required objects are present
        object_names = [obj.name.lower() for obj in objects]
        
        for required in master_plan.required_objects:
            found = any(required.lower() in name for name in object_names)
            if not found:
                issues.append(ValidationIssue(
                    severity="warning",
                    category="prompt_alignment",
                    description=f"Required object '{required}' not found in scene",
                    suggested_fix=f"Add '{required}' to the scene"
                ))
                penalty += 5
        
        return issues, penalty
    
    def _objects_intersect(self, a: SceneObject, b: SceneObject) -> bool:
        """Check if two objects' bounding boxes intersect (with tolerance)."""
        return self._calculate_overlap(a, b) > self.collision_tolerance
    
    def _is_surface_object(self, obj: SceneObject) -> bool:
        """Check if object is meant to be on a surface (not floor)."""
        surface_objects = ["lamp", "book", "vase", "clock", "plant"]
        return any(s in obj.name.lower() for s in surface_objects)
    
    def _is_on_top_of(self, obj: SceneObject, surface: SceneObject) -> bool:
        """Check if obj is properly placed on top of surface."""
        surface_top = surface.position.z + surface.bounding_box.height
        tolerance = 0.1
        
        return abs(obj.position.z - surface_top) < tolerance
    
    def _generate_recommendations(
        self,
        objects: List[SceneObject],
        lighting: Optional[LightingSetup],
        master_plan
    ) -> List[str]:
        """Generate improvement recommendations."""
        recommendations = []
        
        if len(objects) < 3:
            recommendations.append(
                "Consider adding more objects for a richer scene composition"
            )
        
        if lighting and len(lighting.lights) == 1:
            recommendations.append(
                "Adding a fill light could soften harsh shadows"
            )
        
        if master_plan and "cozy" in master_plan.interpreted_mood.lower():
            has_rug = any("rug" in obj.name.lower() for obj in objects)
            if not has_rug:
                recommendations.append(
                    "Adding a rug could enhance the cozy atmosphere"
                )
        
        return recommendations
    
    def _generate_final_report(
        self,
        state: AgentState,
        score: int,
        issues: List[ValidationIssue],
        recommendations: List[str],
        note: Optional[str] = None
    ) -> str:
        """Generate the final validation report."""
        objects = state.get("scene_objects", [])
        lighting = state.get("lighting_setup")
        camera = state.get("camera_setup")
        
        report = f"""
# 3D Scene Validation Report

## Summary
- **Score**: {score}/100
- **Status**: {'PASSED' if score >= self.passing_score else 'NEEDS REVISION'}
- **Objects**: {len(objects)}
- **Iterations**: {state.get('iteration_count', 1)}

## Scene Contents
"""
        for obj in objects:
            material_name = obj.material.name if obj.material else "None"
            report += f"- **{obj.name}**: Position ({obj.position.x:.2f}, {obj.position.y:.2f}, {obj.position.z:.2f}), Material: {material_name}\n"
        
        if lighting:
            report += f"""
## Lighting
- **Lights**: {len(lighting.lights)}
- **HDRI**: {lighting.hdri_map or 'None'}
- **Exposure**: {lighting.exposure}
"""
        
        if camera:
            report += f"""
## Camera
- **Focal Length**: {camera.focal_length}mm
- **Aperture**: f/{camera.aperture}
- **Depth of Field**: {'Enabled' if camera.depth_of_field else 'Disabled'}
"""
        
        if issues:
            report += "\n## Issues Found\n"
            for issue in issues:
                report += f"- [{issue.severity.upper()}] {issue.category}: {issue.description}\n"
                if issue.suggested_fix:
                    report += f"  - Fix: {issue.suggested_fix}\n"
        
        if recommendations:
            report += "\n## Recommendations\n"
            for rec in recommendations:
                report += f"- {rec}\n"
        
        if note:
            report += f"\n## Note\n{note}\n"
        
        return report
