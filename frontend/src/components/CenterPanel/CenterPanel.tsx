import React from 'react';
import { motion } from 'motion/react';
import { panelVariants } from '../../animations/variants';
import { useStore } from '../../store/appStore';
import { useEnvironment } from '../../hooks/useEnvironment';
import { Card } from '../Common/Card';
import { Button } from '../Common/Button';
import { ProgressBar } from '../Common/ProgressBar';
import { LoadingSpinner } from '../Common/LoadingSpinner';
import { BrainCircuit, Play, Activity, CheckCircle2, Zap, TableProperties, MonitorPlay } from 'lucide-react';

export function CenterPanel() {
  const { observation, stepCount, maxSteps, setObservation, setLastAction, addToHistory, addLog, episodeDone, setEpisodeDone, setShowResultsModal } = useStore();
  const { executeAction, quickFix, loading } = useEnvironment();
  
  if (!observation) return null;

  const handleExecute = async (actionToRun: any) => {
    if (!actionToRun) return;
    
    addLog(`Executing: ${actionToRun.action_type}`);
    const result = await executeAction(actionToRun);
    
    if (result) {
      setObservation(result.observation);
      setLastAction(actionToRun, result.reward);
      addToHistory({
        step: result.observation.step_count,
        action: actionToRun,
        reward: result.reward,
        message: result.message
      });
      addLog(`Result: ${result.message} (Reward: ${result.reward})`);
      
      if (result.done || result.observation.step_count >= result.observation.max_steps) {
        setEpisodeDone(true);
        setShowResultsModal(true);
      }
    }
  };

  const handleQuickFixLoop = async () => {
    addLog(`[System] Initiating heuristic agent trace...`);
    const results = await quickFix();
    if (!results || results.length === 0) return;

    for (const result of results) {
      const actionTaken = result.info?.action || { action_type: 'unknown' };
      setObservation(result.observation);
      setLastAction(actionTaken, result.reward);
      addToHistory({
        step: result.observation.step_count,
        action: actionTaken,
        reward: result.reward,
        message: result.message
      });
      
      if (result.done) {
        setEpisodeDone(true);
        setShowResultsModal(true);
        break;
      }
      
      // Delay so the user can see the steps animating one after another
      await new Promise(r => setTimeout(r, 600));
    }
  };

  return (
    <motion.div 
      variants={panelVariants}
      initial="hidden"
      animate="visible"
      className="flex flex-col gap-6 h-full overflow-hidden"
    >
      {/* Top Controls Row */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6 shrink-0">
        {/* Score Card */}
        <Card className="xl:col-span-1 bg-gradient-to-br from-blue-600 to-indigo-700 text-white border-none shadow-md">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-bold flex items-center gap-2 text-white">
              <Activity className="w-5 h-5 text-blue-200" /> Quality Score
            </h2>
            <div className="text-xs font-bold bg-white/20 px-2 py-1 rounded-full text-white">
              Step {stepCount} / {episodeDone ? stepCount : maxSteps}
            </div>
          </div>
          <div className="mb-1">
            <div className="flex justify-between items-end mb-2">
              <span className="text-3xl font-black">{Math.round((observation.quality_score || 0) * 100)}%</span>
            </div>
            <div className="h-2 w-full bg-white/20 rounded-full overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${(observation.quality_score || 0) * 100}%` }}
                transition={{ duration: 0.8, ease: "easeOut" }}
                className="h-full bg-white rounded-full"
              />
            </div>
          </div>
        </Card>

        {/* AI Agent Card */}
        <Card className="xl:col-span-2 shadow-sm border-gray-200 flex flex-col justify-center">
          {episodeDone ? (
            <div className="flex items-center justify-between px-4">
              <div className="flex items-center gap-4">
                <div className="bg-green-100 p-3 rounded-full">
                  <CheckCircle2 className="w-6 h-6 text-green-600" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-gray-900">Cleanup Complete</h3>
                  <p className="text-sm text-gray-500">Dataset has reached target quality.</p>
                </div>
              </div>
              <Button onClick={() => setShowResultsModal(true)}>View Results</Button>
            </div>
          ) : (
            <div className="flex items-center justify-between px-2">
              <div className="flex items-center gap-4">
                <div className="bg-blue-50 p-3 rounded-xl border border-blue-100">
                  <MonitorPlay className="w-6 h-6 text-blue-600 animate-pulse" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-gray-900">External Agent Active</h3>
                  <p className="text-sm text-gray-500">Waiting for actions from external agent / API...</p>
                </div>
              </div>
              <div className="flex gap-3">
                {loading && <LoadingSpinner size="sm" text="Syncing..." />}
                <Button variant="outline" onClick={handleQuickFixLoop} disabled={loading}>
                  <Zap className="w-4 h-4 mr-2 text-yellow-500" /> Quick Fix
                </Button>
              </div>
            </div>
          )}
        </Card>
      </div>

      {/* Data Preview Table */}
      <Card title="Data Preview" icon={<TableProperties className="w-5 h-5 text-blue-500" />} className="flex-1 flex flex-col overflow-hidden shadow-sm border-gray-200">
        <div className="overflow-x-auto border border-gray-200 rounded-lg flex-1 bg-white">
          <table className="w-full text-sm text-left">
            <thead className="text-xs text-gray-700 uppercase bg-gray-50 sticky top-0 shadow-sm z-10">
              <tr>
                {(observation.columns || []).map(col => (
                  <th key={col} className="px-6 py-3 font-semibold whitespace-nowrap border-b border-gray-200">{col}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {(observation.data_sample || []).map((row, idx) => (
                <tr key={idx} className="hover:bg-blue-50/50 transition-colors">
                  {(observation.columns || []).map(col => (
                    <td key={col} className="px-6 py-3 whitespace-nowrap">
                      {row[col] === null || row[col] === undefined || row[col] === '' ? (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800">
                          null
                        </span>
                      ) : (
                        <span className="text-gray-900">{String(row[col])}</span>
                      )}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </motion.div>
  );
}
