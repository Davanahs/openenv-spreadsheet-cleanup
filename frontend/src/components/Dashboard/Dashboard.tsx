import React from 'react';
import { motion } from 'motion/react';
import { useStore } from '../../store/appStore';
import { useWebSocket } from '../../hooks/useWebSocket';
import { Toolbar } from '../Toolbar/Toolbar';
import { LeftPanel } from '../LeftPanel/LeftPanel';
import { CenterPanel } from '../CenterPanel/CenterPanel';
import { RightPanel } from '../RightPanel/RightPanel';
import { TaskSelectModal } from '../Modals/TaskSelectModal';
import { ResultsSummaryModal } from '../Modals/ResultsSummaryModal';

export function Dashboard() {
  const { selectedTask, showResultsModal } = useStore();
  
  // Initialize WebSocket connection
  useWebSocket(!!selectedTask);

  return (
    <div className="h-screen w-full bg-[#f4f4f5] flex flex-col overflow-hidden font-sans">
      <Toolbar />
      
      {!selectedTask ? (
        <TaskSelectModal />
      ) : (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="flex-1 flex overflow-hidden"
        >
          <div className="w-80 bg-white border-r border-gray-200 shadow-[2px_0_8px_-4px_rgba(0,0,0,0.1)] z-10 p-4 overflow-y-auto flex flex-col gap-4">
            <LeftPanel />
          </div>
          
          <div className="flex-1 p-6 overflow-hidden flex flex-col">
            <CenterPanel />
          </div>
          
          <div className="w-80 bg-white border-l border-gray-200 shadow-[-2px_0_8px_-4px_rgba(0,0,0,0.1)] z-10 p-4 overflow-y-auto flex flex-col gap-4">
            <RightPanel />
          </div>
        </motion.div>
      )}
      
      {showResultsModal && <ResultsSummaryModal />}
    </div>
  );
}
