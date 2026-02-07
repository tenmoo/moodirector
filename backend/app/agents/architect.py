"""
The Scene Architect Agent - The Layout Artist.
Primary Responsibility: Spatial Logic & Object Hierarchy.
"""
from typing import Dict, Any, List, Tuple
import json
import logging
import math

from .base import BaseAgent
from ..models.state import AgentState, SceneObject, Coordinate3D, WorkflowStatus

logger = logging.getLogger(__name__)

ARCHITECT_SYSTEM_PROMPT = """You are a 3D Layout Engineer. You receive model dimensions from the Librarian and your task is to output x, y, z coordinates for each object.

COORDINATE SYSTEM: Z-Up (Z is vertical height)
- X: Left/Right
- Y: Forward/Backward  
- Z: Up/Down (height)

Your responsibilities:
1. Assign X, Y, Z coordinates to every object
2. Ensure objects follow spatial relationships (e.g., desk facing window)
3. Manage Parent-Child relationships (if desk moves, items on it move too)
4. CRITICAL: Ensure no two meshes occupy the same space (No Clipping!)

PLACEMENT RULES:
- Primary furniture against walls (bed against wall, desk near window)
- Maintain realistic spacing (at least 0.5m between large furniture)
- Objects should rest on floor (Z = 0) or on other surfaces
- Consider ergonomics (chair at desk, lamp on desk)

When placing objects, output valid JSON with this structure:
{{
    "placements": [
        {{
            "object_id": "uuid",
            "name": "object_name",
            "position": {{"x": 0.0, "y": 0.0, "z": 0.0}},
            "rotation": {{"x": 0.0, "y": 0.0, "z": 0.0}},
            "parent_id": null,
            "reasoning": "brief explanation"
        }}
    ],
    "spatial_notes": "description of the layout"
}}"""


class ArchitectAgent(BaseAgent):
    """
    The Architect handles spatial logic and object placement.
    Uses Z-Up coordinate system.
    """
    
    def __init__(self):
        super().__init__(
            name="Architect",
            description="Scene Architect - Places objects in 3D space",
            system_prompt=ARCHITECT_SYSTEM_PROMPT
        )
        # Room dimensions (default 6m x 6m x 3m) - larger room for better spacing
        self.room_bounds = {"x": (-3.0, 3.0), "y": (-3.0, 3.0), "z": (0, 3.0)}
        self.min_spacing = 0.5  # Increased minimum gap between objects
    
    async def process(self, state: AgentState) -> Dict[str, Any]:
        """
        Place all scene objects in 3D space.
        """
        self.log_action("Starting spatial layout")
        
        scene_objects = state.get("scene_objects", [])
        master_plan = state.get("master_plan")
        
        if not scene_objects:
            return {
                "errors": ["No scene objects to place"],
                "current_agent": "orchestrator"
            }
        
        # Get spatial requirements from master plan
        spatial_reqs = master_plan.spatial_requirements if master_plan else {}
        
        # Generate placements using both algorithmic and LLM approaches
        placed_objects = await self._generate_placements(scene_objects, spatial_reqs)
        
        # Validate no clipping
        clipping_issues = self._check_clipping(placed_objects)
        
        if clipping_issues:
            self.log_action("Clipping detected, adjusting", {"issues": len(clipping_issues)})
            placed_objects = self._resolve_clipping(placed_objects, clipping_issues)
        
        return {
            "scene_objects": placed_objects,
            "current_agent": "material_scientist",
            "messages": [{
                "agent": self.name,
                "action": "objects_placed",
                "content": f"Placed {len(placed_objects)} objects in scene. Layout optimized for {spatial_reqs.get('primary_focal_point', 'general arrangement')}"
            }]
        }
    
    async def _generate_placements(
        self, 
        objects: List[SceneObject], 
        spatial_reqs: Dict[str, Any]
    ) -> List[SceneObject]:
        """Generate positions for all objects."""
        placed = []
        occupied_spaces = []
        
        # Sort objects by size (larger first for better placement)
        sorted_objects = sorted(
            objects, 
            key=lambda o: o.bounding_box.width * o.bounding_box.depth,
            reverse=True
        )
        
        # Define placement zones
        zones = self._define_zones(spatial_reqs)
        
        for obj in sorted_objects:
            # Determine appropriate zone for this object
            zone = self._select_zone(obj.name, zones)
            
            # Find valid position in zone
            position = self._find_valid_position(obj, zone, occupied_spaces)
            
            # Update object with placement
            obj.position = Coordinate3D(x=position[0], y=position[1], z=position[2])
            obj.rotation = self._calculate_rotation(obj.name, spatial_reqs)
            obj.status = "placed"
            
            # Track occupied space
            occupied_spaces.append(self._get_occupied_bounds(obj))
            placed.append(obj)
            
            self.log_action(f"Placed {obj.name}", {
                "position": obj.position.to_dict(),
                "rotation": obj.rotation.to_dict()
            })
        
        return placed
    
    def _define_zones(self, spatial_reqs: Dict[str, Any]) -> Dict[str, Dict]:
        """Define placement zones in the room (6m x 6m room)."""
        # Zones are well-separated to minimize clipping
        return {
            "primary_wall": {
                "bounds": {"x": (-1.5, 1.5), "y": (1.5, 2.8), "z": (0, 0)},
                "objects": ["bed", "sofa", "couch"]
            },
            "window_area": {
                "bounds": {"x": (1.0, 2.8), "y": (-1.5, 0.5), "z": (0, 0)},
                "objects": ["desk", "window"]
            },
            "center": {
                "bounds": {"x": (-0.8, 0.8), "y": (-0.8, 0.8), "z": (0, 0)},
                "objects": ["rug", "table"]
            },
            "corner_left": {
                "bounds": {"x": (-2.8, -1.5), "y": (1.0, 2.5), "z": (0, 0)},
                "objects": ["bookshelf", "plant"]
            },
            "corner_right": {
                "bounds": {"x": (1.5, 2.8), "y": (1.0, 2.5), "z": (0, 0)},
                "objects": ["lamp"]
            },
            "opposite_wall": {
                "bounds": {"x": (-1.5, 1.5), "y": (-2.8, -1.5), "z": (0, 0)},
                "objects": ["chair"]
            },
            "wall_mounted": {
                "bounds": {"x": (-2.8, 2.8), "y": (2.5, 2.9), "z": (0, 0)},
                "objects": ["wall", "floor", "ceiling"]
            },
            "default": {
                "bounds": {"x": (-2.0, 2.0), "y": (-2.0, 2.0), "z": (0, 0)},
                "objects": []
            }
        }
    
    def _select_zone(self, object_name: str, zones: Dict) -> Dict:
        """Select the appropriate zone for an object."""
        object_lower = object_name.lower()
        
        for zone_name, zone_data in zones.items():
            if any(obj in object_lower for obj in zone_data.get("objects", [])):
                return zone_data
        
        return zones["default"]
    
    def _find_valid_position(
        self, 
        obj: SceneObject, 
        zone: Dict, 
        occupied: List[Dict]
    ) -> Tuple[float, float, float]:
        """Find a valid position for an object that doesn't clip with others."""
        bounds = zone["bounds"]
        
        # Start from center of zone
        center_x = (bounds["x"][0] + bounds["x"][1]) / 2
        center_y = (bounds["y"][0] + bounds["y"][1]) / 2
        z = bounds["z"][0]  # Floor level
        
        # First try: grid search within zone bounds
        step = 0.4  # 40cm grid
        x_range = bounds["x"][1] - bounds["x"][0]
        y_range = bounds["y"][1] - bounds["y"][0]
        
        for dx in [i * step - x_range/2 for i in range(int(x_range/step) + 1)]:
            for dy in [i * step - y_range/2 for i in range(int(y_range/step) + 1)]:
                x = center_x + dx
                y = center_y + dy
                
                # Check if position is within room bounds
                if not (self.room_bounds["x"][0] <= x <= self.room_bounds["x"][1] and
                        self.room_bounds["y"][0] <= y <= self.room_bounds["y"][1]):
                    continue
                
                test_bounds = {
                    "min": (x - obj.bounding_box.width/2 - self.min_spacing, 
                            y - obj.bounding_box.depth/2 - self.min_spacing, z),
                    "max": (x + obj.bounding_box.width/2 + self.min_spacing, 
                            y + obj.bounding_box.depth/2 + self.min_spacing, 
                            z + obj.bounding_box.height)
                }
                
                if not self._intersects_any(test_bounds, occupied):
                    return (x, y, z)
        
        # Second try: expand to room bounds with spiral pattern
        for radius in [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]:
            for angle in range(0, 360, 30):  # Finer angle steps
                x = center_x + radius * math.cos(math.radians(angle))
                y = center_y + radius * math.sin(math.radians(angle))
                
                # Check room bounds
                if not (self.room_bounds["x"][0] + obj.bounding_box.width/2 <= x <= self.room_bounds["x"][1] - obj.bounding_box.width/2 and
                        self.room_bounds["y"][0] + obj.bounding_box.depth/2 <= y <= self.room_bounds["y"][1] - obj.bounding_box.depth/2):
                    continue
                
                test_bounds = {
                    "min": (x - obj.bounding_box.width/2 - self.min_spacing, 
                            y - obj.bounding_box.depth/2 - self.min_spacing, z),
                    "max": (x + obj.bounding_box.width/2 + self.min_spacing, 
                            y + obj.bounding_box.depth/2 + self.min_spacing, 
                            z + obj.bounding_box.height)
                }
                
                if not self._intersects_any(test_bounds, occupied):
                    return (x, y, z)
        
        # Fallback: find any open corner of the room
        corners = [
            (-2.5, -2.5), (-2.5, 2.5), (2.5, -2.5), (2.5, 2.5),
            (0, -2.5), (0, 2.5), (-2.5, 0), (2.5, 0)
        ]
        for cx, cy in corners:
            test_bounds = {
                "min": (cx - obj.bounding_box.width/2 - self.min_spacing, 
                        cy - obj.bounding_box.depth/2 - self.min_spacing, z),
                "max": (cx + obj.bounding_box.width/2 + self.min_spacing, 
                        cy + obj.bounding_box.depth/2 + self.min_spacing, 
                        z + obj.bounding_box.height)
            }
            if not self._intersects_any(test_bounds, occupied):
                return (cx, cy, z)
        
        logger.warning(f"Could not find non-clipping position for {obj.name}, using offset position")
        # Last resort: offset from center based on number of occupied spaces
        offset = len(occupied) * 0.8
        return (center_x + offset, center_y - offset, z)
    
    def _calculate_rotation(self, object_name: str, spatial_reqs: Dict) -> Coordinate3D:
        """Calculate appropriate rotation for an object."""
        object_lower = object_name.lower()
        
        # Default rotations based on object type
        if "desk" in object_lower:
            # Face away from wall (toward center/window)
            return Coordinate3D(x=0, y=0, z=180)
        elif "bed" in object_lower:
            # Headboard against wall
            return Coordinate3D(x=0, y=0, z=0)
        elif "chair" in object_lower:
            # Face desk/table
            return Coordinate3D(x=0, y=0, z=0)
        
        return Coordinate3D(x=0, y=0, z=0)
    
    def _get_occupied_bounds(self, obj: SceneObject) -> Dict:
        """Get the occupied bounding box for an object."""
        half_w = obj.bounding_box.width / 2 + self.min_spacing
        half_d = obj.bounding_box.depth / 2 + self.min_spacing
        
        return {
            "min": (
                obj.position.x - half_w,
                obj.position.y - half_d,
                obj.position.z
            ),
            "max": (
                obj.position.x + half_w,
                obj.position.y + half_d,
                obj.position.z + obj.bounding_box.height
            )
        }
    
    def _intersects_any(self, bounds: Dict, occupied: List[Dict]) -> bool:
        """Check if bounds intersect with any occupied space."""
        for occ in occupied:
            if self._boxes_intersect(bounds, occ):
                return True
        return False
    
    def _boxes_intersect(self, a: Dict, b: Dict) -> bool:
        """Check if two axis-aligned bounding boxes intersect."""
        return (
            a["min"][0] < b["max"][0] and a["max"][0] > b["min"][0] and
            a["min"][1] < b["max"][1] and a["max"][1] > b["min"][1] and
            a["min"][2] < b["max"][2] and a["max"][2] > b["min"][2]
        )
    
    def _check_clipping(self, objects: List[SceneObject]) -> List[Tuple[str, str]]:
        """Check for clipping between placed objects."""
        issues = []
        
        for i, obj1 in enumerate(objects):
            bounds1 = self._get_occupied_bounds(obj1)
            
            for obj2 in objects[i+1:]:
                bounds2 = self._get_occupied_bounds(obj2)
                
                if self._boxes_intersect(bounds1, bounds2):
                    issues.append((obj1.id, obj2.id))
        
        return issues
    
    def _resolve_clipping(
        self, 
        objects: List[SceneObject], 
        issues: List[Tuple[str, str]]
    ) -> List[SceneObject]:
        """Attempt to resolve clipping issues by adjusting positions."""
        moved_ids = set()
        
        # Build occupied list excluding objects we're about to move
        objects_to_move = set(id2 for _, id2 in issues)
        
        for id1, id2 in issues:
            if id2 in moved_ids:
                continue
            
            obj_to_move = None
            other_obj = None
            for obj in objects:
                if obj.id == id2:
                    obj_to_move = obj
                elif obj.id == id1:
                    other_obj = obj
            
            if not obj_to_move or not other_obj:
                continue
            
            # Calculate direction to move away from the other object
            dx = obj_to_move.position.x - other_obj.position.x
            dy = obj_to_move.position.y - other_obj.position.y
            
            # Normalize and scale
            dist = math.sqrt(dx*dx + dy*dy) or 0.1
            move_dist = (obj_to_move.bounding_box.width + other_obj.bounding_box.width) / 2 + self.min_spacing
            
            # Move away from the other object
            obj_to_move.position.x += (dx / dist) * move_dist
            obj_to_move.position.y += (dy / dist) * move_dist
            
            # Keep within room bounds
            obj_to_move.position.x = max(self.room_bounds["x"][0] + obj_to_move.bounding_box.width/2,
                                         min(self.room_bounds["x"][1] - obj_to_move.bounding_box.width/2,
                                             obj_to_move.position.x))
            obj_to_move.position.y = max(self.room_bounds["y"][0] + obj_to_move.bounding_box.depth/2,
                                         min(self.room_bounds["y"][1] - obj_to_move.bounding_box.depth/2,
                                             obj_to_move.position.y))
            
            moved_ids.add(id2)
            self.log_action(f"Resolved clipping for {obj_to_move.name}", {
                "new_position": obj_to_move.position.to_dict()
            })
        
        return objects
