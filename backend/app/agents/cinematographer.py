"""
The Cinematographer Agent - The Lighting Director.
Primary Responsibility: Atmosphere & Camera.
"""
from typing import Dict, Any, List, Optional
import json
import logging
import math

from .base import BaseAgent
from ..models.state import (
    AgentState, LightingSetup, LightSource, CameraSetup, 
    Coordinate3D, WorkflowStatus
)

logger = logging.getLogger(__name__)

CINEMATOGRAPHER_SYSTEM_PROMPT = """You are a Lighting Director for 3D scenes. Your goal is to create the perfect atmosphere through lighting and camera setup.

Your responsibilities:
1. Set up lighting to match the requested mood (warm morning, dramatic, soft, etc.)
2. Use HDRI maps or physical lights (Sun, Area, Point, Spot)
3. Configure camera focal length, aperture, and depth of field
4. Ensure proper exposure without hot spots or underexposure

LIGHTING GUIDELINES:
- Warm Morning: Sun lamp at 20° angle, 3500K color temp, soft area light for bounce
- Cool Evening: Blue-tinted ambient, 6500K key light at 45°
- Dramatic: High contrast, single key light with minimal fill
- Soft/Diffuse: Large area lights, HDRI for ambient

CAMERA GUIDELINES:
- Interior wide shot: 24-35mm lens
- Portrait/detail: 50-85mm lens
- Architectural: 24mm or wider
- Shallow DOF: f/1.4-2.8
- Deep DOF: f/8-16

When setting up lighting, output valid JSON:
{{
    "lighting": {{
        "lights": [
            {{
                "name": "key_light",
                "light_type": "sun",
                "position": {{"x": 2, "y": -3, "z": 5}},
                "rotation": {{"x": 20, "y": 0, "z": 45}},
                "color_temperature": 3500,
                "intensity": 3.0
            }}
        ],
        "hdri_map": "/hdri/interior_warm.hdr",
        "exposure": 1.0
    }},
    "camera": {{
        "position": {{"x": 0, "y": -4, "z": 1.6}},
        "target": {{"x": 0, "y": 0, "z": 0.5}},
        "focal_length": 35,
        "aperture": 2.8,
        "depth_of_field": true
    }}
}}"""


# Lighting presets for different moods
LIGHTING_PRESETS = {
    "warm_morning": {
        "key_light": {
            "type": "sun",
            "angle": 20,
            "color_temp": 3500,
            "intensity": 3.0
        },
        "fill_light": {
            "type": "area",
            "color_temp": 4500,
            "intensity": 0.5
        },
        "hdri": "/hdri/morning_interior.hdr",
        "exposure": 1.0
    },
    "cool_evening": {
        "key_light": {
            "type": "sun",
            "angle": 15,
            "color_temp": 6500,
            "intensity": 1.5
        },
        "fill_light": {
            "type": "area",
            "color_temp": 7000,
            "intensity": 0.3
        },
        "hdri": "/hdri/evening_blue.hdr",
        "exposure": 0.8
    },
    "dramatic": {
        "key_light": {
            "type": "spot",
            "angle": 45,
            "color_temp": 4000,
            "intensity": 5.0
        },
        "fill_light": None,
        "hdri": "/hdri/studio_dark.hdr",
        "exposure": 1.2
    },
    "soft_diffuse": {
        "key_light": {
            "type": "area",
            "angle": 45,
            "color_temp": 5500,
            "intensity": 2.0,
            "size": 3.0
        },
        "fill_light": {
            "type": "area",
            "color_temp": 5500,
            "intensity": 1.0,
            "size": 2.0
        },
        "hdri": "/hdri/overcast_soft.hdr",
        "exposure": 1.0
    },
    "cozy": {
        "key_light": {
            "type": "area",
            "angle": 30,
            "color_temp": 3200,
            "intensity": 2.5
        },
        "fill_light": {
            "type": "point",
            "color_temp": 2800,
            "intensity": 0.8
        },
        "hdri": "/hdri/cozy_interior.hdr",
        "exposure": 0.9
    },
    "neutral": {
        "key_light": {
            "type": "sun",
            "angle": 45,
            "color_temp": 5500,
            "intensity": 2.0
        },
        "fill_light": {
            "type": "area",
            "color_temp": 5500,
            "intensity": 0.6
        },
        "hdri": "/hdri/neutral_studio.hdr",
        "exposure": 1.0
    }
}


class CinematographerAgent(BaseAgent):
    """
    The Cinematographer sets up lighting and camera.
    Controls atmosphere, mood, and visual composition.
    """
    
    def __init__(self):
        super().__init__(
            name="Cinematographer",
            description="Lighting Director - Sets up lights and camera",
            system_prompt=CINEMATOGRAPHER_SYSTEM_PROMPT
        )
    
    async def process(self, state: AgentState) -> Dict[str, Any]:
        """
        Set up lighting and camera for the scene.
        """
        self.log_action("Starting lighting and camera setup")
        
        scene_objects = state.get("scene_objects", [])
        master_plan = state.get("master_plan")
        
        # Determine mood and lighting requirements
        lighting_reqs = master_plan.lighting_requirements if master_plan else {}
        mood = master_plan.interpreted_mood if master_plan else "neutral"
        
        # Set up lighting
        lighting_setup = self._create_lighting_setup(mood, lighting_reqs)
        
        # Set up camera based on scene composition
        camera_setup = self._create_camera_setup(scene_objects, mood)
        
        self.log_action("Lighting and camera configured", {
            "mood": mood,
            "lights": len(lighting_setup.lights),
            "focal_length": camera_setup.focal_length
        })
        
        return {
            "lighting_setup": lighting_setup,
            "camera_setup": camera_setup,
            "current_agent": "critic",
            "messages": [{
                "agent": self.name,
                "action": "lighting_camera_set",
                "content": f"Configured {len(lighting_setup.lights)} lights for '{mood}' mood. Camera: {camera_setup.focal_length}mm at f/{camera_setup.aperture}"
            }]
        }
    
    def _create_lighting_setup(
        self, 
        mood: str, 
        requirements: Dict[str, Any]
    ) -> LightingSetup:
        """Create lighting setup based on mood and requirements."""
        mood_lower = mood.lower()
        
        # Select preset
        preset = LIGHTING_PRESETS.get("neutral")
        for preset_name, preset_data in LIGHTING_PRESETS.items():
            if preset_name.replace("_", " ") in mood_lower or preset_name in mood_lower:
                preset = preset_data
                break
            # Check for partial matches
            if any(word in mood_lower for word in preset_name.split("_")):
                preset = preset_data
        
        lights = []
        
        # Key light
        key_config = preset.get("key_light", {})
        if key_config:
            key_light = self._create_light(
                name="key_light",
                config=key_config,
                position=Coordinate3D(x=3, y=-2, z=4)
            )
            lights.append(key_light)
        
        # Fill light
        fill_config = preset.get("fill_light")
        if fill_config:
            fill_light = self._create_light(
                name="fill_light",
                config=fill_config,
                position=Coordinate3D(x=-2, y=-1, z=3)
            )
            lights.append(fill_light)
        
        # Apply time-of-day adjustments from requirements
        time_of_day = requirements.get("time_of_day", "").lower()
        if time_of_day:
            lights = self._adjust_for_time(lights, time_of_day)
        
        return LightingSetup(
            lights=lights,
            hdri_map=preset.get("hdri"),
            exposure=preset.get("exposure", 1.0),
            ambient_intensity=0.1
        )
    
    def _create_light(
        self, 
        name: str, 
        config: Dict[str, Any],
        position: Coordinate3D
    ) -> LightSource:
        """Create a light source from configuration."""
        angle = config.get("angle", 45)
        
        # Calculate rotation from angle
        rotation = Coordinate3D(
            x=angle,
            y=0,
            z=45 if name == "key_light" else -45
        )
        
        return LightSource(
            id=f"{name}_001",
            name=name,
            light_type=config.get("type", "area"),
            position=position,
            rotation=rotation,
            color_temperature=config.get("color_temp", 5500),
            intensity=config.get("intensity", 1.0),
            angle=angle,
            size=config.get("size", 1.0)
        )
    
    def _adjust_for_time(
        self, 
        lights: List[LightSource], 
        time_of_day: str
    ) -> List[LightSource]:
        """Adjust lighting based on time of day."""
        adjustments = {
            "morning": {"color_temp_offset": -500, "angle_offset": -10},
            "afternoon": {"color_temp_offset": 0, "angle_offset": 0},
            "evening": {"color_temp_offset": -800, "angle_offset": -20},
            "night": {"color_temp_offset": 1500, "intensity_mult": 0.3}
        }
        
        adj = adjustments.get(time_of_day, {})
        
        for light in lights:
            if "color_temp_offset" in adj:
                light.color_temperature += adj["color_temp_offset"]
            if "angle_offset" in adj:
                light.angle += adj["angle_offset"]
            if "intensity_mult" in adj:
                light.intensity *= adj["intensity_mult"]
        
        return lights
    
    def _create_camera_setup(
        self, 
        scene_objects: List, 
        mood: str
    ) -> CameraSetup:
        """Create camera setup based on scene composition."""
        # Calculate scene center and bounds
        if scene_objects:
            avg_x = sum(obj.position.x for obj in scene_objects) / len(scene_objects)
            avg_y = sum(obj.position.y for obj in scene_objects) / len(scene_objects)
            avg_z = sum(
                obj.position.z + obj.bounding_box.height / 2 
                for obj in scene_objects
            ) / len(scene_objects)
        else:
            avg_x, avg_y, avg_z = 0, 0, 0.5
        
        # Camera distance based on scene size
        scene_radius = 2.0
        if scene_objects:
            max_extent = max(
                max(abs(obj.position.x), abs(obj.position.y)) + 
                max(obj.bounding_box.width, obj.bounding_box.depth) / 2
                for obj in scene_objects
            )
            scene_radius = max(2.0, max_extent * 1.5)
        
        # Position camera
        camera_distance = scene_radius * 2
        camera_height = 1.6  # Eye level
        
        # Mood-based camera settings
        mood_lower = mood.lower()
        
        if "intimate" in mood_lower or "cozy" in mood_lower:
            focal_length = 50.0
            aperture = 1.8
            dof = True
        elif "dramatic" in mood_lower:
            focal_length = 35.0
            aperture = 2.8
            dof = True
        elif "wide" in mood_lower or "architectural" in mood_lower:
            focal_length = 24.0
            aperture = 8.0
            dof = False
        else:
            focal_length = 35.0
            aperture = 2.8
            dof = True
        
        return CameraSetup(
            position=Coordinate3D(
                x=avg_x,
                y=avg_y - camera_distance,
                z=camera_height
            ),
            target=Coordinate3D(
                x=avg_x,
                y=avg_y,
                z=avg_z
            ),
            focal_length=focal_length,
            aperture=aperture,
            depth_of_field=dof,
            focus_distance=camera_distance
        )
