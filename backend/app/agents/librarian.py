"""
The Asset Librarian Agent - The Fetcher.
Primary Responsibility: Sourcing & Compatibility.
"""
from typing import Dict, Any, List, Optional
import json
import uuid
import logging

from .base import BaseAgent
from ..models.state import AgentState, SceneObject, BoundingBox, WorkflowStatus

logger = logging.getLogger(__name__)

LIBRARIAN_SYSTEM_PROMPT = """You are an expert 3D Asset Librarian. Your goal is to find models that match the user's aesthetic requirements.

Your responsibilities:
1. Search the asset library for requested objects
2. Return file paths and bounding box dimensions for each asset
3. Check polygon counts to ensure the scene doesn't become too heavy to render
4. Convert file formats if needed (e.g., .fbx to .blend)
5. If a model is not found, suggest the closest visual match and flag it for the Material Scientist

CONSTRAINTS:
- Never download 'Heavy' assets (>500,000 polygons) that could crash the render engine
- Always provide bounding box dimensions for the Architect
- Flag any substitutions made

When returning assets, output valid JSON with this structure:
{{
    "assets": [
        {{
            "name": "object_name",
            "asset_path": "/library/category/asset.blend",
            "bounding_box": {{"width": 2.0, "depth": 1.5, "height": 1.0}},
            "polygon_count": 15000,
            "substitution": null,
            "notes": "any relevant notes"
        }}
    ],
    "warnings": ["any warnings about heavy assets or substitutions"]
}}"""


# Simulated asset library (in production, this would query a real database)
ASSET_LIBRARY = {
    "bed": {
        "white_bed": {"path": "/library/furniture/beds/white_modern_bed.blend", "polygons": 25000, "bbox": (2.0, 1.8, 0.9)},
        "wooden_bed": {"path": "/library/furniture/beds/oak_frame_bed.blend", "polygons": 18000, "bbox": (2.0, 1.6, 1.0)},
        "default": {"path": "/library/furniture/beds/standard_bed.blend", "polygons": 20000, "bbox": (2.0, 1.6, 0.8)},
    },
    "desk": {
        "wooden_desk": {"path": "/library/furniture/desks/oak_desk.blend", "polygons": 12000, "bbox": (1.4, 0.7, 0.75)},
        "modern_desk": {"path": "/library/furniture/desks/modern_white_desk.blend", "polygons": 8000, "bbox": (1.2, 0.6, 0.75)},
        "default": {"path": "/library/furniture/desks/standard_desk.blend", "polygons": 10000, "bbox": (1.2, 0.6, 0.75)},
    },
    "chair": {
        "office_chair": {"path": "/library/furniture/chairs/office_chair.blend", "polygons": 15000, "bbox": (0.6, 0.6, 1.1)},
        "wooden_chair": {"path": "/library/furniture/chairs/wooden_chair.blend", "polygons": 8000, "bbox": (0.5, 0.5, 0.9)},
        "default": {"path": "/library/furniture/chairs/standard_chair.blend", "polygons": 10000, "bbox": (0.5, 0.5, 0.9)},
    },
    "lamp": {
        "desk_lamp": {"path": "/library/lighting/lamps/desk_lamp.blend", "polygons": 5000, "bbox": (0.2, 0.2, 0.45)},
        "floor_lamp": {"path": "/library/lighting/lamps/floor_lamp.blend", "polygons": 8000, "bbox": (0.4, 0.4, 1.6)},
        "default": {"path": "/library/lighting/lamps/standard_lamp.blend", "polygons": 5000, "bbox": (0.25, 0.25, 0.5)},
    },
    "bookshelf": {
        "tall_bookshelf": {"path": "/library/furniture/storage/tall_bookshelf.blend", "polygons": 20000, "bbox": (1.0, 0.35, 2.0)},
        "default": {"path": "/library/furniture/storage/bookshelf.blend", "polygons": 15000, "bbox": (0.8, 0.3, 1.8)},
    },
    "plant": {
        "potted_plant": {"path": "/library/decor/plants/potted_plant.blend", "polygons": 30000, "bbox": (0.4, 0.4, 0.6)},
        "large_plant": {"path": "/library/decor/plants/large_indoor_plant.blend", "polygons": 45000, "bbox": (0.8, 0.8, 1.5)},
        "default": {"path": "/library/decor/plants/generic_plant.blend", "polygons": 25000, "bbox": (0.3, 0.3, 0.5)},
    },
    "rug": {
        "area_rug": {"path": "/library/decor/rugs/area_rug.blend", "polygons": 2000, "bbox": (2.5, 2.0, 0.02)},
        "default": {"path": "/library/decor/rugs/standard_rug.blend", "polygons": 1500, "bbox": (2.0, 1.5, 0.02)},
    },
    "window": {
        "large_window": {"path": "/library/architecture/windows/large_window.blend", "polygons": 5000, "bbox": (1.5, 0.1, 2.0)},
        "default": {"path": "/library/architecture/windows/standard_window.blend", "polygons": 3000, "bbox": (1.0, 0.1, 1.2)},
    },
    "curtain": {
        "flowing_curtain": {"path": "/library/decor/curtains/flowing_curtain.blend", "polygons": 35000, "bbox": (2.0, 0.3, 2.5)},
        "default": {"path": "/library/decor/curtains/standard_curtain.blend", "polygons": 20000, "bbox": (1.5, 0.2, 2.2)},
    },
    "books": {
        "book_stack": {"path": "/library/decor/books/book_stack.blend", "polygons": 8000, "bbox": (0.3, 0.2, 0.25)},
        "default": {"path": "/library/decor/books/books_set.blend", "polygons": 6000, "bbox": (0.25, 0.15, 0.2)},
    },
}


class LibrarianAgent(BaseAgent):
    """
    The Librarian fetches 3D assets from the library.
    It's the only agent with database/internet access permissions.
    """
    
    def __init__(self):
        super().__init__(
            name="Librarian",
            description="Asset Librarian - Fetches and validates 3D assets",
            system_prompt=LIBRARIAN_SYSTEM_PROMPT
        )
        self.max_polygon_count = 500000  # Per asset limit
    
    async def process(self, state: AgentState) -> Dict[str, Any]:
        """
        Fetch assets for all objects in the master plan.
        """
        self.log_action("Starting asset search")
        
        master_plan = state.get("master_plan")
        if not master_plan:
            return {
                "errors": ["No master plan available for asset search"],
                "current_agent": "orchestrator"
            }
        
        required_objects = master_plan.required_objects
        self.log_action("Searching for assets", {"count": len(required_objects)})
        
        scene_objects = []
        warnings = []
        
        for obj_name in required_objects:
            asset_info = self._search_asset_library(obj_name)
            
            if asset_info:
                scene_obj = SceneObject(
                    id=str(uuid.uuid4()),
                    name=obj_name,
                    asset_path=asset_info["path"],
                    bounding_box=BoundingBox(
                        width=asset_info["bbox"][0],
                        depth=asset_info["bbox"][1],
                        height=asset_info["bbox"][2]
                    ),
                    polygon_count=asset_info["polygons"],
                    status="fetched"
                )
                scene_objects.append(scene_obj)
                
                if asset_info.get("substituted"):
                    warnings.append(f"Substituted '{obj_name}' with '{asset_info['original_key']}'")
                
                self.log_action(f"Found asset: {obj_name}", {
                    "path": asset_info["path"],
                    "polygons": asset_info["polygons"]
                })
            else:
                warnings.append(f"Could not find asset for '{obj_name}'")
        
        # Calculate total polygon count
        total_polygons = sum(obj.polygon_count for obj in scene_objects)
        
        return {
            "scene_objects": scene_objects,
            "current_agent": "architect",
            "messages": [{
                "agent": self.name,
                "action": "assets_fetched",
                "content": f"Fetched {len(scene_objects)} assets. Total polygons: {total_polygons}. Warnings: {len(warnings)}"
            }],
            "errors": warnings if warnings else []
        }
    
    def _search_asset_library(self, object_name: str) -> Optional[Dict[str, Any]]:
        """
        Search the asset library for a matching object.
        Returns asset info or None if not found.
        """
        object_lower = object_name.lower()
        
        # Check for exact category match
        for category, assets in ASSET_LIBRARY.items():
            if category in object_lower:
                # Try to find a specific variant
                for variant_key, asset_data in assets.items():
                    if variant_key != "default" and variant_key.replace("_", " ") in object_lower:
                        return {
                            "path": asset_data["path"],
                            "polygons": asset_data["polygons"],
                            "bbox": asset_data["bbox"],
                            "substituted": False
                        }
                
                # Use default for the category
                if "default" in assets:
                    return {
                        "path": assets["default"]["path"],
                        "polygons": assets["default"]["polygons"],
                        "bbox": assets["default"]["bbox"],
                        "substituted": False
                    }
        
        # Try partial matching
        for category, assets in ASSET_LIBRARY.items():
            for variant_key, asset_data in assets.items():
                if variant_key != "default":
                    # Check if any word matches
                    variant_words = variant_key.replace("_", " ").split()
                    object_words = object_lower.replace("_", " ").split()
                    
                    if any(vw in object_words for vw in variant_words):
                        return {
                            "path": asset_data["path"],
                            "polygons": asset_data["polygons"],
                            "bbox": asset_data["bbox"],
                            "substituted": True,
                            "original_key": variant_key
                        }
        
        return None
    
    async def search_external(self, query: str) -> List[Dict[str, Any]]:
        """
        Search external asset sources (MCP integration point).
        This would connect to external APIs via MCP.
        """
        # Placeholder for MCP integration
        self.log_action("External search", {"query": query})
        return []
