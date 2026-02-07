import axios from 'axios';
import type {
  SceneResponse,
  AgentListResponse,
  CreateSceneRequest,
  JobStatus,
} from '../types';

const API_BASE_URL = '/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const api = {
  /**
   * Create a new 3D scene from a natural language prompt
   */
  createScene: async (request: CreateSceneRequest): Promise<SceneResponse> => {
    const response = await apiClient.post<SceneResponse>('/scene/create', request);
    return response.data;
  },

  /**
   * Create a scene asynchronously
   */
  createSceneAsync: async (request: CreateSceneRequest): Promise<JobStatus> => {
    const response = await apiClient.post<JobStatus>('/scene/create-async', {
      ...request,
      async_mode: true,
    });
    return response.data;
  },

  /**
   * Get the status of an async job
   */
  getJobStatus: async (jobId: string): Promise<JobStatus> => {
    const response = await apiClient.get<JobStatus>(`/scene/status/${jobId}`);
    return response.data;
  },

  /**
   * List all agents in the system
   */
  listAgents: async (): Promise<AgentListResponse> => {
    const response = await apiClient.get<AgentListResponse>('/agents');
    return response.data;
  },

  /**
   * Health check
   */
  healthCheck: async (): Promise<{ status: string; service: string }> => {
    const response = await apiClient.get('/health');
    return response.data;
  },
};

export default api;
