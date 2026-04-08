import client from './client';
import { Observation, Action, StepResult, EnvState } from '../types/api';

export async function getHealth() {
  return client.get('/');
}

export async function getTasks() {
  return client.get('/tasks');
}

/**
 * Reset the environment with a predefined task.
 * Backend returns ResetResponse { observation, done, info }; we extract observation.
 */
export async function resetEnvironment(taskId: string): Promise<Observation> {
  console.log(`🔄 [Reset] Environment reset — task: "${taskId}"`);
  const res = await client.post('/reset', { task_id: taskId });
  console.log('🔄 [Reset] Done. Observation:', res.data?.observation ?? res.data);
  // Backend returns ResetResponse: { observation: Observation, done: bool, info: {} }
  return res.data.observation ?? res.data;
}

/**
 * Load custom data (file, url, or raw text) into the environment.
 * Returns the observation extracted from ResetResponse.
 */
export async function loadData(params: {
  type: 'file' | 'url' | 'text';
  content: File | string;
  datasetName?: string;
}): Promise<Observation> {
  const formData = new FormData();
  formData.append('dataset', params.datasetName || 'custom');

  if (params.type === 'file' && params.content instanceof File) {
    formData.append('file', params.content);
  } else if (params.type === 'url' && typeof params.content === 'string') {
    formData.append('url', params.content);
  } else if (params.type === 'text' && typeof params.content === 'string') {
    // Convert raw CSV text to a File blob so the backend can parse it
    const blob = new Blob([params.content], { type: 'text/csv' });
    formData.append('file', blob, 'data.csv');
  }

  console.log(`📂 [LoadData] Loading data — type: "${params.type}", dataset: "${params.datasetName || 'custom'}"`);
  const res = await client.post('/load_data', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  console.log('📂 [LoadData] Done. Observation:', res.data?.observation ?? res.data);
  return res.data.observation ?? res.data;
}

export async function step(action: Action): Promise<StepResult> {
  console.log(
    `👤 [Manual Step] action_type: "${action.action_type}"${
      action.column ? ` | column: "${action.column}"` : ''
    }${
      (action as any).strategy ? ` | strategy: "${(action as any).strategy}"` : ''
    }`
  );
  const res = await client.post('/step', action);
  console.log(`👤 [Manual Step] Result → reward: ${res.data?.reward}, done: ${res.data?.done}`);
  return res.data;
}

export async function getState(): Promise<EnvState> {
  const res = await client.get('/state');
  return res.data;
}

export async function quickFix(): Promise<StepResult[]> {
  console.log('⏳ [QuickFix] Triggering agent via POST /quick_fix ...');
  const res = await client.post('/quick_fix');
  const steps: StepResult[] = res.data;
  // The backend embeds agent_type in each step's info field
  const agentType: string = (steps[0]?.info as any)?.agent_type ?? 'Unknown';
  const emoji = agentType === 'LLM' ? '🤖' : '⚙️';
  console.log(`${emoji} [QuickFix] Agent used: ${agentType} — ${steps.length} steps returned`);
  return steps;
}

export async function getReport() {
  const res = await client.get('/report');
  return res.data;
}

export async function runSuite() {
  console.log('⏳ [RunSuite] Triggering agent via POST /run_suite ...');
  const res = await client.post('/run_suite');
  console.log('✅ [RunSuite] Complete:', res.data);
  return res.data;
}
