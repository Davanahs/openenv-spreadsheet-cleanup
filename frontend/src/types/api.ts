export interface TaskConfig {
  id: string;
  title: string;
  description: string;
  rows: number;
  cols: number;
  issues: number;
}

export interface Observation {
  task_id: string;
  step_count: number;
  max_steps: number;
  quality_score: number;
  columns: string[];
  data_sample: any[];
  issues_summary: {
    missing: number;
    duplicates: number;
    inconsistent: number;
  };
  issues: Issue[];
}

export interface Issue {
  column: string;
  type: string;
  rows: number[];
}

export interface Action {
  action_type: string;
  target_action?: string;
  target_column?: string;
  strategy?: string;
  fill_value?: any;
  column?: string;
}

export interface StepResult {
  observation: Observation;
  reward: number;
  done: boolean;
  message: string;
  available_actions: string[];
  /** Extra metadata injected by the backend (action dict, agent_type, etc.) */
  info?: Record<string, any>;
}

export interface EnvState {
  observation: Observation;
  done: boolean;
}
