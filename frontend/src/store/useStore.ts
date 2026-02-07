import { create } from 'zustand';
import type { SceneResponse, Agent, JobStatus } from '../types';

interface AppState {
  // Scene state
  currentScene: SceneResponse | null;
  isLoading: boolean;
  error: string | null;
  
  // Agent state
  agents: Agent[];
  workflowDescription: string;
  
  // Job tracking for async mode
  currentJobId: string | null;
  jobStatus: JobStatus | null;
  
  // Prompt history
  promptHistory: string[];
  
  // Actions
  setCurrentScene: (scene: SceneResponse | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setAgents: (agents: Agent[], workflow: string) => void;
  setJobStatus: (jobId: string | null, status: JobStatus | null) => void;
  addToHistory: (prompt: string) => void;
  clearScene: () => void;
}

export const useStore = create<AppState>((set) => ({
  // Initial state
  currentScene: null,
  isLoading: false,
  error: null,
  agents: [],
  workflowDescription: '',
  currentJobId: null,
  jobStatus: null,
  promptHistory: [],
  
  // Actions
  setCurrentScene: (scene) => set({ currentScene: scene, error: null }),
  
  setLoading: (loading) => set({ isLoading: loading }),
  
  setError: (error) => set({ error, isLoading: false }),
  
  setAgents: (agents, workflow) => set({ agents, workflowDescription: workflow }),
  
  setJobStatus: (jobId, status) => set({ currentJobId: jobId, jobStatus: status }),
  
  addToHistory: (prompt) => set((state) => ({
    promptHistory: [prompt, ...state.promptHistory.slice(0, 9)], // Keep last 10
  })),
  
  clearScene: () => set({ currentScene: null, error: null }),
}));
