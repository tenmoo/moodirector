// API Types for Moo Director

export interface Coordinate3D {
  x: number;
  y: number;
  z: number;
}

export interface BoundingBox {
  width: number;
  depth: number;
  height: number;
}

export interface Material {
  name: string;
  shader_type: string;
  base_color: number[];
  roughness: number;
  metallic: number;
  subsurface: number;
  subsurface_color?: number[];
  clear_coat: number;
  texture_map: string | null;
  normal_map: string | null;
  roughness_map: string | null;
}

export interface SceneObject {
  id: string;
  name: string;
  asset_path: string | null;
  position: Coordinate3D | null;
  rotation: Coordinate3D | null;
  scale: Coordinate3D | null;
  bounding_box?: BoundingBox;
  material: Material | null;
  polygon_count?: number;
  status: string;
}

export interface LightSource {
  id: string;
  name: string;
  light_type: string;
  position: Coordinate3D;
  rotation: Coordinate3D;
  color_temperature: number;
  intensity: number;
  angle: number;
  size: number;
}

export interface LightingSetup {
  lights: LightSource[];
  hdri_map: string | null;
  ambient_intensity: number;
  exposure: number;
}

export interface CameraSetup {
  position: Coordinate3D;
  target: Coordinate3D;
  focal_length: number;
  aperture: number;
  sensor_size: number;
  depth_of_field: boolean;
  focus_distance: number;
}

export interface ValidationIssue {
  severity: 'error' | 'warning' | 'info';
  category: string;
  description: string;
  affected_object_id: string | null;
  suggested_fix: string | null;
}

export interface SceneData {
  objects: SceneObject[];
  lighting: LightingSetup | null;
  camera: CameraSetup | null;
}

export interface ValidationReport {
  passed: boolean;
  issues: ValidationIssue[];
  final_report: string | null;
}

export interface SceneResponse {
  request_id: string;
  status: string;
  scene_data: SceneData | null;
  validation_report: ValidationReport | null;
  message: string;
  processing_time_ms: number;
}

export interface Agent {
  name: string;
  role: string;
  description: string;
}

export interface AgentListResponse {
  agents: Agent[];
  workflow: string;
}

export interface CreateSceneRequest {
  prompt: string;
  max_iterations?: number;
  async_mode?: boolean;
}

export interface JobStatus {
  job_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: string | null;
  result: SceneData | null;
  error: string | null;
}
