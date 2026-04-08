import React, { useEffect, useRef } from 'react';
import { motion } from 'motion/react';
import { panelVariants, containerVariants, itemVariants } from '../../animations/variants';
import { useStore } from '../../store/appStore';
import { Card } from '../Common/Card';
import { Badge } from '../Common/Badge';
import { History, Terminal, Maximize2, Minimize2 } from 'lucide-react';
import { AnimatePresence } from 'motion/react';
import { useState } from 'react';

export function RightPanel() {
  const { stepHistory, logs } = useStore();
  const logsEndRef = useRef<HTMLDivElement>(null);
  const [isLogsMaximized, setIsLogsMaximized] = useState(false);

  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  return (
    <motion.div 
      variants={panelVariants}
      initial="hidden"
      animate="visible"
      className="flex flex-col gap-4 h-full"
    >
      <div className="mb-2">
        <h2 className="text-lg font-bold text-gray-900">Activity</h2>
        <p className="text-sm text-gray-500">History and live logs</p>
      </div>

      <AnimatePresence>
        {!isLogsMaximized && (
          <motion.div 
            initial={{ opacity: 0, height: 0 }} 
            animate={{ opacity: 1, height: 'auto' }} 
            exit={{ opacity: 0, height: 0 }} 
            className="flex-1 flex flex-col min-h-0 overflow-hidden"
          >
            <Card title="Action History" icon={<History className="w-5 h-5 text-blue-500" />} variant="outlined" className="h-full flex flex-col overflow-hidden">
              <div className="flex-1 overflow-y-auto pr-2 space-y-3">
                {stepHistory.length === 0 ? (
                  <div className="flex flex-col items-center justify-center h-full text-gray-400 space-y-2">
                    <History className="w-8 h-8 opacity-20" />
                    <span className="text-sm">No actions taken yet</span>
                  </div>
                ) : (
                  <motion.div variants={containerVariants} initial="hidden" animate="visible" className="space-y-3">
                    {stepHistory.map((item, idx) => (
                      <motion.div key={idx} variants={itemVariants} className="bg-white border border-gray-200 shadow-sm rounded-lg p-3 text-sm relative overflow-hidden">
                        <div className={`absolute left-0 top-0 bottom-0 w-1 ${item.reward > 0 ? 'bg-green-500' : item.reward < 0 ? 'bg-red-500' : 'bg-gray-300'}`} />
                        <div className="pl-2">
                          <div className="flex justify-between items-start mb-1">
                            <div className="font-bold text-gray-900">
                              Step {item.step}
                            </div>
                            <Badge 
                              text={item.reward > 0 ? `+${item.reward.toFixed(2)}` : item.reward.toFixed(2)} 
                              variant={item.reward > 0 ? "success" : item.reward < 0 ? "error" : "default"} 
                            />
                          </div>
                          <div className="text-blue-700 font-medium mb-1">
                            {item.action.action_type.replace(/_/g, ' ')}
                          </div>
                          <div className="text-gray-500 text-xs mt-1 bg-gray-50 p-1.5 rounded border border-gray-100">
                            {item.message}
                          </div>
                        </div>
                      </motion.div>
                    ))}
                  </motion.div>
                )}
              </div>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      <Card 
        title="Live Logs" 
        icon={<Terminal className="w-5 h-5 text-gray-500" />} 
        action={
          <button onClick={() => setIsLogsMaximized(true)} className="text-gray-500 hover:text-white transition-colors">
            <Maximize2 className="w-4 h-4" />
          </button>
        }
        variant="outlined" 
        className="h-1/3 min-h-[250px] flex flex-col bg-gray-900 text-gray-300 border-gray-800"
      >
        <div className="flex-1 overflow-y-auto font-mono text-xs space-y-1.5 p-3 bg-black/40 rounded-lg border border-gray-800 shadow-inner">
          {logs.length === 0 ? (
            <div className="text-gray-500 italic flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
              Waiting for events...
            </div>
          ) : (
            logs.map((log, idx) => {
              const parts = log.split('] ');
              const timestamp = parts[0] + ']';
              const message = parts.slice(1).join('] ');
              return (
                <div key={idx} className="break-words leading-relaxed">
                  <span className="text-blue-400 opacity-70">{timestamp}</span>{' '}
                  <span className={message.includes('Error') || message.includes('failed') ? 'text-red-400' : 'text-gray-300'}>
                    {message}
                  </span>
                </div>
              );
            })
          )}
          <div ref={logsEndRef} />
        </div>
      </Card>

      <AnimatePresence>
        {isLogsMaximized && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="fixed inset-4 z-[100] shadow-2xl rounded-2xl overflow-hidden bg-gray-950 flex flex-col border border-gray-800"
          >
            <div className="flex items-center justify-between p-4 bg-gray-900 border-b border-gray-800 shrink-0">
              <div className="flex items-center gap-3">
                <Terminal className="w-6 h-6 text-blue-400" />
                <h3 className="font-bold text-gray-200 text-lg">Live Logs (Fullscreen Setup)</h3>
              </div>
              <button 
                onClick={() => setIsLogsMaximized(false)} 
                className="bg-gray-800 p-2 text-gray-300 rounded-full hover:bg-gray-700 hover:text-white transition-colors"
                title="Close Fullscreen"
              >
                <Minimize2 className="w-5 h-5" />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto font-mono text-sm space-y-2 p-6 bg-black/60 shadow-inner">
              {logs.map((log, idx) => {
                const parts = log.split('] ');
                const timestamp = parts[0] + ']';
                const message = parts.slice(1).join('] ');
                return (
                  <div key={idx} className="break-words tracking-wide leading-relaxed">
                    <span className="text-blue-400 opacity-70">{timestamp}</span>{' '}
                    <span className={message.includes('Error') || message.includes('failed') ? 'text-red-400 font-bold' : message.includes('FINAL') ? 'text-green-400 font-bold' : 'text-gray-300'}>
                      {message}
                    </span>
                  </div>
                );
              })}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
