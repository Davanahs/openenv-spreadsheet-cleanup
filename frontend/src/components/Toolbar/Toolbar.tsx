import React, { useState } from 'react';
import { useStore } from '../../store/appStore';
import { Button } from '../Common/Button';
import { DatabaseZap, LogOut, PlayCircle, FileBarChart } from 'lucide-react';
import { getReport, runSuite } from '../../api/environment';

export function Toolbar() {
  const { selectedTask, reset, addLog } = useStore();
  const [isRunningSuite, setIsRunningSuite] = useState(false);
  const [isGettingReport, setIsGettingReport] = useState(false);

  const handleRunSuite = async () => {
    setIsRunningSuite(true);
    addLog('Starting test suite...');
    try {
      const result = await runSuite();
      addLog(`Test Suite Results: ${JSON.stringify(result, null, 2)}`);
    } catch (error: any) {
      if (error.message === 'Network Error') {
        addLog('Test Suite Results: (Mocked) { "scores": { "easy": 0.95, "medium": 0.82, "hard": 0.74 }, "average_score": 0.8367 }');
      } else {
        addLog(`Error running test suite: ${error.message || error}`);
      }
    } finally {
      setIsRunningSuite(false);
    }
  };

  const handleGetReport = async () => {
    setIsGettingReport(true);
    addLog('Fetching report...');
    try {
      const result = await getReport();
      addLog(`Current Report: ${JSON.stringify(result, null, 2)}`);
    } catch (error: any) {
      if (error.message === 'Network Error') {
        addLog('Current Report: (Mocked) { "task_id": "mock", "steps_used": 5, "max_steps": 20, "issues_fixed": 3, "initial_issues": 10, "quality_score": 0.7, "success": false }');
      } else {
        addLog(`Error fetching report: ${error.message || error}`);
      }
    } finally {
      setIsGettingReport(false);
    }
  };

  return (
    <div className="h-16 border-b bg-white px-6 flex items-center justify-between shadow-sm z-10">
      <div className="flex items-center gap-3">
        <div className="bg-blue-600 p-2 rounded-lg">
          <DatabaseZap className="w-5 h-5 text-white" />
        </div>
        <h1 className="text-xl font-bold text-gray-900 tracking-tight">OpenEnv Data Cleanup</h1>
      </div>
      
      <div className="flex items-center gap-4">
        <Button 
          variant="outline" 
          size="sm" 
          onClick={handleRunSuite} 
          disabled={isRunningSuite}
          className="text-gray-600"
        >
          <PlayCircle className="w-4 h-4 mr-2" /> 
          {isRunningSuite ? 'Running...' : 'Run Test Suite'}
        </Button>
        
        {selectedTask && (
          <div className="flex items-center gap-3">
            <Button 
              variant="outline" 
              size="sm" 
              onClick={handleGetReport} 
              disabled={isGettingReport}
              className="text-gray-600"
            >
              <FileBarChart className="w-4 h-4 mr-2" /> 
              {isGettingReport ? 'Fetching...' : 'Get Report'}
            </Button>
            
            <span className="text-sm text-gray-500 border-l pl-3">Current Task:</span>
            <span className="text-sm font-semibold bg-gray-100 px-3 py-1 rounded-full capitalize">{selectedTask}</span>
            <Button variant="ghost" size="sm" onClick={reset} className="ml-2 text-gray-500 hover:text-red-600">
              <LogOut className="w-4 h-4 mr-2" /> Exit Task
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
