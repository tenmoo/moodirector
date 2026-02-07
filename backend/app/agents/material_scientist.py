"""
The Material Scientist Agent - The Look-Dev Artist.
Primary Responsibility: Surface Physics & Texturing.
"""
from typing import Dict, Any, List, Optional
import json
import logging

from .base import BaseAgent
from ..models.state import AgentState, SceneObject, Material, WorkflowStatus

logger = logging.getLogger(__name__)

MATERIAL_SCIENTIST_SYSTEM_PROMPT = """You are a Look-Dev Specialist. You apply PBR (Physically Based Rendering) shaders to 3D objects.

Your responsibilities:
1. Apply appropriate PBR materials based on object type and scene mood
2. Ensure textures are mapped to UV coordinates
3. Set correct roughness, metallic, and subsurface scattering values
4. Match materials to the aesthetic requested (e.g., "cozy" = warm wood tones, soft fabrics)

MATERIAL RULES:
- For 'White Bed': Use Cloth shader with high roughness (0.8-0.9)
- For 'Wooden Desk': Use Wood shader with subtle clear coat (0.05-0.15)
- NEVER use flat colors - everything must have a texture map
- Subsurface scattering for fabrics, skin, wax, leaves

SHADER TYPES:
- cloth: High roughness, slight subsurface for fabric
- wood: Medium roughness, grain texture, optional clear coat
- metal: Low roughness, high metallic
- glass: Low roughness, transmission
- plastic: Medium roughness, no metallic
- ceramic: Medium-high roughness, subtle subsurface

When applying materials, output valid JSON:
{{
    "materials": [
        {{
            "object_id": "uuid",
            "material": {{
                "name": "material_name",
                "shader_type": "cloth",
                "base_color": [1.0, 1.0, 1.0, 1.0],
                "roughness": 0.85,
                "metallic": 0.0,
                "subsurface": 0.1,
                "texture_map": "/textures/fabric_diffuse.png"
            }}
        }}
    ]
}}"""


# Material presets for common object types
MATERIAL_PRESETS = {
    "bed": {
        "default": Material(
            name="bed_fabric",
            shader_type="cloth",
            base_color=[0.95, 0.95, 0.95, 1.0],
            roughness=0.85,
            metallic=0.0,
            subsurface=0.15,
            subsurface_color=[1.0, 0.95, 0.9],
            texture_map="/textures/fabric/linen_diffuse.png"
        ),
        "white": Material(
            name="white_bedding",
            shader_type="cloth",
            base_color=[0.98, 0.98, 0.98, 1.0],
            roughness=0.9,
            subsurface=0.2,
            texture_map="/textures/fabric/cotton_white.png"
        ),
    },
    "desk": {
        "default": Material(
            name="desk_wood",
            shader_type="wood",
            base_color=[0.55, 0.35, 0.2, 1.0],
            roughness=0.4,
            metallic=0.0,
            clear_coat=0.1,
            texture_map="/textures/wood/oak_diffuse.png",
            normal_map="/textures/wood/oak_normal.png"
        ),
        "wooden": Material(
            name="oak_wood",
            shader_type="wood",
            base_color=[0.6, 0.4, 0.25, 1.0],
            roughness=0.35,
            clear_coat=0.15,
            texture_map="/textures/wood/oak_grain.png"
        ),
    },
    "chair": {
        "default": Material(
            name="chair_material",
            shader_type="wood",
            base_color=[0.45, 0.3, 0.18, 1.0],
            roughness=0.5,
            texture_map="/textures/wood/walnut_diffuse.png"
        ),
        "leather": Material(
            name="leather_chair",
            shader_type="cloth",
            base_color=[0.15, 0.1, 0.08, 1.0],
            roughness=0.6,
            subsurface=0.05,
            texture_map="/textures/leather/brown_leather.png"
        ),
    },
    "lamp": {
        "default": Material(
            name="lamp_material",
            shader_type="metal",
            base_color=[0.8, 0.75, 0.65, 1.0],
            roughness=0.3,
            metallic=0.9,
            texture_map="/textures/metal/brushed_metal.png"
        ),
        "shade": Material(
            name="lamp_shade",
            shader_type="cloth",
            base_color=[0.95, 0.92, 0.85, 1.0],
            roughness=0.8,
            subsurface=0.3,
            texture_map="/textures/fabric/lamp_shade.png"
        ),
    },
    "bookshelf": {
        "default": Material(
            name="bookshelf_wood",
            shader_type="wood",
            base_color=[0.4, 0.25, 0.15, 1.0],
            roughness=0.55,
            texture_map="/textures/wood/pine_diffuse.png"
        ),
    },
    "plant": {
        "default": Material(
            name="plant_leaves",
            shader_type="cloth",  # Using cloth for subsurface
            base_color=[0.2, 0.45, 0.15, 1.0],
            roughness=0.7,
            subsurface=0.4,
            subsurface_color=[0.4, 0.6, 0.2],
            texture_map="/textures/nature/leaves_diffuse.png"
        ),
    },
    "rug": {
        "default": Material(
            name="rug_fabric",
            shader_type="cloth",
            base_color=[0.6, 0.55, 0.5, 1.0],
            roughness=0.95,
            subsurface=0.1,
            texture_map="/textures/fabric/rug_pattern.png"
        ),
    },
    "curtain": {
        "default": Material(
            name="curtain_fabric",
            shader_type="cloth",
            base_color=[0.9, 0.88, 0.82, 1.0],
            roughness=0.85,
            subsurface=0.25,
            texture_map="/textures/fabric/sheer_curtain.png"
        ),
    },
    "books": {
        "default": Material(
            name="book_covers",
            shader_type="plastic",
            base_color=[0.3, 0.25, 0.4, 1.0],
            roughness=0.6,
            texture_map="/textures/misc/book_spines.png"
        ),
    },
}


class MaterialScientistAgent(BaseAgent):
    """
    The Material Scientist applies PBR materials and textures.
    Focuses on surface physics and realistic rendering.
    """
    
    def __init__(self):
        super().__init__(
            name="Material Scientist",
            description="Look-Dev Artist - Applies PBR materials and textures",
            system_prompt=MATERIAL_SCIENTIST_SYSTEM_PROMPT
        )
    
    async def process(self, state: AgentState) -> Dict[str, Any]:
        """
        Apply materials to all scene objects.
        """
        self.log_action("Starting material application")
        
        scene_objects = state.get("scene_objects", [])
        master_plan = state.get("master_plan")
        
        if not scene_objects:
            return {
                "errors": ["No scene objects to texture"],
                "current_agent": "orchestrator"
            }
        
        # Get material requirements from master plan
        material_reqs = master_plan.material_requirements if master_plan else {}
        mood = master_plan.interpreted_mood if master_plan else "neutral"
        
        # Apply materials to each object
        textured_objects = []
        
        for obj in scene_objects:
            material = self._select_material(obj, material_reqs, mood)
            obj.material = material
            obj.status = "textured"
            textured_objects.append(obj)
            
            self.log_action(f"Applied material to {obj.name}", {
                "material": material.name,
                "shader": material.shader_type
            })
        
        return {
            "scene_objects": textured_objects,
            "current_agent": "cinematographer",
            "messages": [{
                "agent": self.name,
                "action": "materials_applied",
                "content": f"Applied PBR materials to {len(textured_objects)} objects for '{mood}' mood"
            }]
        }
    
    def _select_material(
        self, 
        obj: SceneObject, 
        requirements: Dict[str, Any],
        mood: str
    ) -> Material:
        """Select appropriate material for an object based on type and mood."""
        obj_lower = obj.name.lower()
        
        # Check for specific requirements
        if obj.name in requirements:
            req = requirements[obj.name]
            return self._create_material_from_requirements(obj.name, req)
        
        # Find matching preset
        for obj_type, presets in MATERIAL_PRESETS.items():
            if obj_type in obj_lower:
                # Check for variant match
                for variant, material in presets.items():
                    if variant != "default" and variant in obj_lower:
                        adjusted = self._adjust_for_mood(material, mood)
                        return adjusted
                
                # Use default preset
                adjusted = self._adjust_for_mood(presets["default"], mood)
                return adjusted
        
        # Fallback: generic material with texture
        return Material(
            name=f"{obj.name}_material",
            shader_type="principled_bsdf",
            roughness=0.5,
            texture_map="/textures/generic/default_diffuse.png"
        )
    
    def _adjust_for_mood(self, material: Material, mood: str) -> Material:
        """Adjust material properties based on scene mood."""
        mood_lower = mood.lower()
        
        # Create a copy to avoid modifying preset
        adjusted = Material(**material.model_dump())
        
        if "warm" in mood_lower or "cozy" in mood_lower:
            # Warm tint
            adjusted.base_color = [
                min(1.0, adjusted.base_color[0] * 1.05),
                adjusted.base_color[1],
                adjusted.base_color[2] * 0.95,
                adjusted.base_color[3]
            ]
            adjusted.roughness = min(1.0, adjusted.roughness + 0.05)
            
        elif "cool" in mood_lower or "modern" in mood_lower:
            # Cool tint
            adjusted.base_color = [
                adjusted.base_color[0] * 0.95,
                adjusted.base_color[1],
                min(1.0, adjusted.base_color[2] * 1.05),
                adjusted.base_color[3]
            ]
            adjusted.roughness = max(0.0, adjusted.roughness - 0.1)
            
        elif "dramatic" in mood_lower:
            # Higher contrast
            adjusted.roughness = max(0.2, adjusted.roughness - 0.15)
        
        return adjusted
    
    def _create_material_from_requirements(
        self, 
        obj_name: str, 
        req: Dict[str, Any]
    ) -> Material:
        """Create a material from explicit requirements."""
        shader_map = {
            "fabric": "cloth",
            "wood": "wood",
            "metal": "metal",
            "glass": "glass",
            "plastic": "plastic",
            "glossy": "plastic",
            "matte": "cloth"
        }
        
        # Texture map based on shader type
        texture_map_lookup = {
            "cloth": "/textures/fabric/generic_fabric.png",
            "wood": "/textures/wood/generic_wood.png",
            "metal": "/textures/metal/generic_metal.png",
            "glass": None,  # Glass doesn't need diffuse texture
            "plastic": "/textures/plastic/generic_plastic.png",
            "principled_bsdf": "/textures/generic/default_diffuse.png"
        }
        
        style = req.get("style", "").lower()
        finish = req.get("finish", "matte").lower()
        
        # Determine shader type
        shader_type = "principled_bsdf"
        for key, shader in shader_map.items():
            if key in style or key in finish:
                shader_type = shader
                break
        
        # Determine roughness from finish
        roughness = 0.5
        if "glossy" in finish or "shiny" in finish:
            roughness = 0.2
        elif "matte" in finish:
            roughness = 0.8
        elif "satin" in finish:
            roughness = 0.4
        
        return Material(
            name=f"{obj_name}_custom",
            shader_type=shader_type,
            roughness=roughness,
            texture_map=texture_map_lookup.get(shader_type, "/textures/generic/default_diffuse.png")
        )
