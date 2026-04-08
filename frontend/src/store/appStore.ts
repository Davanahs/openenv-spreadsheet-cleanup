import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { Observation, Action } from '../types/api';

export interface TaskTemplate {
  id: string;
  title: string;
  type: 'url' | 'text';
  content: string;
  description?: string;
}

export interface AppState {
  taskId: string | null;
  episodeStarted: boolean;
  episodeDone: boolean;
  
  observation: Observation | null;
  stepCount: number;
  maxSteps: number;
  
  lastAction: Action | null;
  lastReward: number;
  
  stepHistory: Array<{
    step: number;
    action: Action;
    reward: number;
    message: string;
  }>;
  logs: string[];
  
  selectedTask: string | null;
  isLoading: boolean;
  showResultsModal: boolean;
  isResultsModalExpanded: boolean;
  
  savedTemplates: TaskTemplate[];

  setTaskId: (id: string) => void;
  setEpisodeStarted: (started: boolean) => void;
  setEpisodeDone: (done: boolean) => void;
  setObservation: (obs: Observation) => void;
  setLastAction: (action: Action, reward: number) => void;
  addToHistory: (item: any) => void;
  addLog: (log: string) => void;
  reset: () => void;
  setShowResultsModal: (show: boolean) => void;
  setIsResultsModalExpanded: (expanded: boolean) => void;
  
  saveTemplate: (template: TaskTemplate) => void;
  deleteTemplate: (id: string) => void;
}

// Helper to load templates from local storage
const loadTemplates = (): TaskTemplate[] => {
  try {
    const saved = localStorage.getItem('openenv_templates');
    return saved ? JSON.parse(saved) : [];
  } catch (e) {
    return [];
  }
};

export const useStore = create<AppState>()(
  devtools((set) => ({
    taskId: null,
    episodeStarted: false,
    episodeDone: false,
    observation: null,
    stepCount: 0,
    maxSteps: 0,
    lastAction: null,
    lastReward: 0,
    stepHistory: [],
    logs: [],
    selectedTask: null,
    isLoading: false,
    showResultsModal: false,
    isResultsModalExpanded: false,
    savedTemplates: loadTemplates(),

    setTaskId: (id) => set({ taskId: id, selectedTask: id }),
    setEpisodeStarted: (started) => set({ episodeStarted: started }),
    setEpisodeDone: (done) => set({ episodeDone: done }),
    setObservation: (obs) => set({ 
      observation: obs,
      stepCount: obs.step_count,
      maxSteps: obs.max_steps
    }),
    setLastAction: (action, reward) => set({ lastAction: action, lastReward: reward }),
    addToHistory: (item) => set((state) => ({
      stepHistory: [...state.stepHistory, item]
    })),
    addLog: (log) => set((state) => ({
      logs: [...state.logs, `[${new Date().toLocaleTimeString()}] ${log}`]
    })),
    setShowResultsModal: (show) => set({ showResultsModal: show, isResultsModalExpanded: false }),
    setIsResultsModalExpanded: (expanded) => set({ isResultsModalExpanded: expanded }),
    reset: () => set((state) => ({
      ...state,
      taskId: null,
      episodeStarted: false,
      episodeDone: false,
      observation: null,
      stepCount: 0,
      stepHistory: [],
      logs: [],
      lastAction: null,
      lastReward: 0,
      selectedTask: null,
      showResultsModal: false,
      isResultsModalExpanded: false,
    })),
    
    saveTemplate: (template) => set((state) => {
      const newTemplates = [...state.savedTemplates, template];
      localStorage.setItem('openenv_templates', JSON.stringify(newTemplates));
      return { savedTemplates: newTemplates };
    }),
    deleteTemplate: (id) => set((state) => {
      const newTemplates = state.savedTemplates.filter(t => t.id !== id);
      localStorage.setItem('openenv_templates', JSON.stringify(newTemplates));
      return { savedTemplates: newTemplates };
    }),
  }))
);
