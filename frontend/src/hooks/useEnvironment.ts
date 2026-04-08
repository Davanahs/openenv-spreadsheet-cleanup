import { useState, useCallback } from 'react';
import * as api from '../api/environment';
import { Action, Observation, StepResult } from '../types/api';

export function useEnvironment() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * Reset the environment.
   * - For predefined tasks (easy/medium/hard), calls POST /reset.
   * - For custom data, calls POST /load_data with file/url/text payload.
   */
  const reset = useCallback(async (
    taskId: string,
    customData?: { type: 'text' | 'url' | 'file'; content: string | File }
  ): Promise<Observation | null> => {
    setLoading(true);
    setError(null);
    try {
      if (customData) {
        // Route custom uploads through the backend /load_data endpoint
        const observation = await api.loadData({
          type: customData.type,
          content: customData.content,
          datasetName: taskId,
        });
        return observation;
      }

      const observation = await api.resetEnvironment(taskId);
      return observation;
    } catch (err: any) {
      const message = err?.response?.data?.detail || err.message || 'Failed to load data.';
      setError(message);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const executeAction = useCallback(async (action: Action): Promise<StepResult | null> => {
    setLoading(true);
    setError(null);
    try {
      const result = await api.step(action);
      return result;
    } catch (err: any) {
      const message = err?.response?.data?.detail || err.message || 'Action failed.';
      setError(message);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const getState = useCallback(async () => {
    try {
      return await api.getState();
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Failed to get state.');
      return null;
    }
  }, []);

  const quickFix = useCallback(async (): Promise<StepResult[] | null> => {
    setLoading(true);
    setError(null);
    try {
      const results = await api.quickFix();
      return results;
    } catch (err: any) {
      const message = err?.response?.data?.detail || err.message || 'Quick fix failed.';
      setError(message);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  return { reset, executeAction, getState, quickFix, loading, error };
}
