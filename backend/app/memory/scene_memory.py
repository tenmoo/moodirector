"""
Vector Memory for Scene Storage and Retrieval.
Uses ChromaDB for semantic search over past scenes.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import logging
import os
from pydantic import BaseModel, Field

# Disable ChromaDB telemetry via environment variable (before import)
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_TELEMETRY"] = "False"

import chromadb
from chromadb.config import Settings

# Try to import embedding functions, gracefully handle missing sentence_transformers
try:
    from chromadb.utils import embedding_functions
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    embedding_functions = None

from ..models.state import SceneObject, LightingSetup, CameraSetup, MasterPlan

logger = logging.getLogger(__name__)


class SceneRecord(BaseModel):
    """A record of a completed scene stored in memory."""
    id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Original request
    user_prompt: str
    interpreted_mood: str = ""
    
    # Scene summary
    object_names: List[str] = Field(default_factory=list)
    object_count: int = 0
    
    # Lighting summary
    lighting_mood: str = ""
    light_count: int = 0
    color_temperature: Optional[int] = None
    
    # Camera summary
    focal_length: Optional[float] = None
    aperture: Optional[float] = None
    
    # Validation
    validation_passed: bool = False
    validation_score: Optional[int] = None
    
    # Full data (JSON serialized)
    full_scene_data: Optional[str] = None
    
    def to_search_text(self) -> str:
        """Convert to searchable text for embedding."""
        parts = [
            f"Scene: {self.user_prompt}",
            f"Mood: {self.interpreted_mood}",
            f"Objects: {', '.join(self.object_names)}",
        ]
        if self.lighting_mood:
            parts.append(f"Lighting: {self.lighting_mood}")
        if self.focal_length:
            parts.append(f"Camera: {self.focal_length}mm f/{self.aperture}")
        return " | ".join(parts)


class SceneMemory:
    """
    Vector-based memory for storing and retrieving past scenes.
    Uses ChromaDB for similarity search.
    """
    
    def __init__(
        self,
        persist_directory: Optional[str] = None,
        collection_name: str = "scene_memory"
    ):
        """
        Initialize the scene memory.
        
        Args:
            persist_directory: Directory to persist the vector DB (None for in-memory)
            collection_name: Name of the ChromaDB collection
        """
        self.collection_name = collection_name
        self.embedding_function = None
        self.use_embeddings = False
        
        # Initialize ChromaDB with telemetry disabled
        settings = Settings(
            anonymized_telemetry=False,
            allow_reset=True
        )
        
        if persist_directory:
            self.persist_directory = persist_directory
            os.makedirs(persist_directory, exist_ok=True)
            self.client = chromadb.PersistentClient(
                path=persist_directory,
                settings=settings
            )
            logger.info(f"Initialized persistent SceneMemory at {persist_directory}")
        else:
            self.client = chromadb.Client(settings=settings)
            logger.info("Initialized in-memory SceneMemory")
        
        # Try to use sentence-transformers for embeddings (optional)
        if SENTENCE_TRANSFORMERS_AVAILABLE and embedding_functions:
            try:
                self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                    model_name="all-MiniLM-L6-v2"
                )
                self.use_embeddings = True
                logger.info("Using SentenceTransformer embeddings for semantic search")
            except Exception as e:
                logger.warning(f"Could not initialize SentenceTransformer: {e}")
                logger.info("Falling back to default embeddings")
        else:
            logger.info("SentenceTransformers not available, using default ChromaDB embeddings")
        
        # Get or create collection
        if self.embedding_function:
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                embedding_function=self.embedding_function,
                metadata={"description": "Moo Director scene memory"}
            )
        else:
            # Use default ChromaDB embeddings
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"description": "Moo Director scene memory"}
            )
        
        logger.info(f"SceneMemory collection '{collection_name}' has {self.collection.count()} scenes")
    
    def store_scene(
        self,
        scene_id: str,
        user_prompt: str,
        master_plan: Optional[MasterPlan],
        scene_objects: List[SceneObject],
        lighting_setup: Optional[LightingSetup],
        camera_setup: Optional[CameraSetup],
        validation_passed: bool,
        validation_score: Optional[int] = None
    ) -> SceneRecord:
        """
        Store a completed scene in memory.
        
        Args:
            scene_id: Unique identifier for the scene
            user_prompt: Original user request
            master_plan: The orchestrator's master plan
            scene_objects: List of scene objects
            lighting_setup: Lighting configuration
            camera_setup: Camera configuration
            validation_passed: Whether validation passed
            validation_score: Validation score (0-100)
            
        Returns:
            The created SceneRecord
        """
        # Create scene record
        record = SceneRecord(
            id=scene_id,
            user_prompt=user_prompt,
            interpreted_mood=master_plan.interpreted_mood if master_plan else "",
            object_names=[obj.name for obj in scene_objects],
            object_count=len(scene_objects),
            lighting_mood=self._extract_lighting_mood(lighting_setup),
            light_count=len(lighting_setup.lights) if lighting_setup else 0,
            color_temperature=self._get_primary_color_temp(lighting_setup),
            focal_length=camera_setup.focal_length if camera_setup else None,
            aperture=camera_setup.aperture if camera_setup else None,
            validation_passed=validation_passed,
            validation_score=validation_score,
            full_scene_data=self._serialize_scene_data(
                scene_objects, lighting_setup, camera_setup
            )
        )
        
        # Create searchable text
        search_text = record.to_search_text()
        
        # Store in ChromaDB
        self.collection.add(
            ids=[scene_id],
            documents=[search_text],
            metadatas=[{
                "user_prompt": user_prompt,
                "interpreted_mood": record.interpreted_mood,
                "object_count": record.object_count,
                "object_names": json.dumps(record.object_names),
                "lighting_mood": record.lighting_mood,
                "validation_passed": str(validation_passed),
                "timestamp": record.timestamp.isoformat()
            }]
        )
        
        logger.info(f"Stored scene {scene_id} in memory: '{user_prompt[:50]}...'")
        return record
    
    def search_similar_scenes(
        self,
        query: str,
        n_results: int = 3,
        min_score: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Search for similar scenes using semantic similarity.
        
        Args:
            query: Search query (natural language)
            n_results: Maximum number of results
            min_score: Minimum similarity score (0-1)
            
        Returns:
            List of similar scenes with metadata
        """
        if self.collection.count() == 0:
            return []
        
        # Query ChromaDB
        results = self.collection.query(
            query_texts=[query],
            n_results=min(n_results, self.collection.count()),
            include=["documents", "metadatas", "distances"]
        )
        
        similar_scenes = []
        
        if results and results["ids"] and results["ids"][0]:
            for i, scene_id in enumerate(results["ids"][0]):
                # ChromaDB returns L2 distance, convert to similarity score
                distance = results["distances"][0][i] if results["distances"] else 0
                similarity = 1 / (1 + distance)  # Convert distance to similarity
                
                if similarity >= min_score:
                    metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                    
                    similar_scenes.append({
                        "id": scene_id,
                        "similarity": round(similarity, 3),
                        "user_prompt": metadata.get("user_prompt", ""),
                        "interpreted_mood": metadata.get("interpreted_mood", ""),
                        "object_count": metadata.get("object_count", 0),
                        "object_names": json.loads(metadata.get("object_names", "[]")),
                        "lighting_mood": metadata.get("lighting_mood", ""),
                        "validation_passed": metadata.get("validation_passed") == "True",
                        "timestamp": metadata.get("timestamp", "")
                    })
        
        logger.info(f"Found {len(similar_scenes)} similar scenes for query: '{query[:50]}...'")
        return similar_scenes
    
    def get_scene_by_id(self, scene_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific scene by ID.
        
        Args:
            scene_id: The scene ID
            
        Returns:
            Scene data or None if not found
        """
        try:
            result = self.collection.get(
                ids=[scene_id],
                include=["documents", "metadatas"]
            )
            
            if result and result["ids"]:
                metadata = result["metadatas"][0] if result["metadatas"] else {}
                return {
                    "id": scene_id,
                    "document": result["documents"][0] if result["documents"] else "",
                    **metadata
                }
        except Exception as e:
            logger.error(f"Error retrieving scene {scene_id}: {e}")
        
        return None
    
    def get_recent_scenes(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get the most recent scenes.
        
        Args:
            limit: Maximum number of scenes to return
            
        Returns:
            List of recent scenes
        """
        # ChromaDB doesn't have built-in sorting, so we get all and sort
        try:
            result = self.collection.get(
                include=["metadatas"],
                limit=min(limit * 2, self.collection.count())  # Get extra to ensure enough
            )
            
            if not result or not result["ids"]:
                return []
            
            scenes = []
            for i, scene_id in enumerate(result["ids"]):
                metadata = result["metadatas"][i] if result["metadatas"] else {}
                scenes.append({
                    "id": scene_id,
                    "user_prompt": metadata.get("user_prompt", ""),
                    "interpreted_mood": metadata.get("interpreted_mood", ""),
                    "object_count": metadata.get("object_count", 0),
                    "timestamp": metadata.get("timestamp", "")
                })
            
            # Sort by timestamp descending
            scenes.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            return scenes[:limit]
            
        except Exception as e:
            logger.error(f"Error getting recent scenes: {e}")
            return []
    
    def delete_scene(self, scene_id: str) -> bool:
        """
        Delete a scene from memory.
        
        Args:
            scene_id: The scene ID to delete
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            self.collection.delete(ids=[scene_id])
            logger.info(f"Deleted scene {scene_id} from memory")
            return True
        except Exception as e:
            logger.error(f"Error deleting scene {scene_id}: {e}")
            return False
    
    def clear_all(self) -> int:
        """
        Clear all scenes from memory.
        
        Returns:
            Number of scenes deleted
        """
        count = self.collection.count()
        if count > 0:
            # Get all IDs and delete
            all_ids = self.collection.get()["ids"]
            self.collection.delete(ids=all_ids)
            logger.info(f"Cleared {count} scenes from memory")
        return count
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        return {
            "total_scenes": self.collection.count(),
            "collection_name": self.collection_name,
            "embedding_model": "all-MiniLM-L6-v2"
        }
    
    def _extract_lighting_mood(self, lighting: Optional[LightingSetup]) -> str:
        """Extract lighting mood description."""
        if not lighting:
            return ""
        
        moods = []
        if lighting.lights:
            avg_temp = sum(l.color_temperature for l in lighting.lights) / len(lighting.lights)
            if avg_temp < 4000:
                moods.append("warm")
            elif avg_temp > 5500:
                moods.append("cool")
            else:
                moods.append("neutral")
        
        if lighting.hdri_map:
            moods.append("HDRI")
        
        return ", ".join(moods)
    
    def _get_primary_color_temp(self, lighting: Optional[LightingSetup]) -> Optional[int]:
        """Get the primary light's color temperature."""
        if lighting and lighting.lights:
            # Find the brightest light
            brightest = max(lighting.lights, key=lambda l: l.intensity)
            return brightest.color_temperature
        return None
    
    def _serialize_scene_data(
        self,
        objects: List[SceneObject],
        lighting: Optional[LightingSetup],
        camera: Optional[CameraSetup]
    ) -> str:
        """Serialize scene data to JSON."""
        data = {
            "objects": [obj.model_dump() for obj in objects],
            "lighting": lighting.model_dump() if lighting else None,
            "camera": camera.model_dump() if camera else None
        }
        return json.dumps(data)


# Global instance (lazy initialization)
_scene_memory: Optional[SceneMemory] = None


def get_scene_memory(
    persist_directory: Optional[str] = "./data/scene_memory"
) -> SceneMemory:
    """
    Get or create the global SceneMemory instance.
    
    Args:
        persist_directory: Directory for persistent storage
        
    Returns:
        SceneMemory instance
    """
    global _scene_memory
    
    if _scene_memory is None:
        _scene_memory = SceneMemory(persist_directory=persist_directory)
    
    return _scene_memory
