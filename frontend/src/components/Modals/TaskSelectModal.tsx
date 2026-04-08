import React from 'react';
import { motion } from 'motion/react';
import { useStore } from '../../store/appStore';
import { useEnvironment } from '../../hooks/useEnvironment';
import { Card } from '../Common/Card';
import { Badge } from '../Common/Badge';
import { Database, AlertCircle, Zap, FileText, Link as LinkIcon, Trash2 } from 'lucide-react';
import { FileUpload } from '../LeftPanel/FileUpload';

export function TaskSelectModal() {
  const setTaskId = useStore(s => s.setTaskId);
  const setObservation = useStore(s => s.setObservation);
  const setEpisodeStarted = useStore(s => s.setEpisodeStarted);
  const setLastAction = useStore(s => s.setLastAction);
  const addToHistory = useStore(s => s.addToHistory);
  const addLog = useStore(s => s.addLog);
  const setEpisodeDone = useStore(s => s.setEpisodeDone);
  const savedTemplates = useStore(s => s.savedTemplates);
  const deleteTemplate = useStore(s => s.deleteTemplate);
  const { reset, executeAction, loading } = useEnvironment();

  const tasks = [
    {
      id: 'easy',
      title: 'Easy',
      rows: '30 rows × 6 cols',
      issues: '15 issues',
      description: 'Fix missing values only',
      icon: <Zap className="w-5 h-5 text-green-500" />
    },
    {
      id: 'medium',
      title: 'Medium',
      rows: '50 rows × 6 cols',
      issues: '35 issues',
      description: 'Handle missing, duplicates, inconsistent',
      icon: <Database className="w-5 h-5 text-yellow-500" />
    },
    {
      id: 'hard',
      title: 'Hard',
      rows: '100 rows × 7 cols',
      issues: '75 issues',
      description: 'Complex multi-type cleanup',
      icon: <AlertCircle className="w-5 h-5 text-red-500" />
    }
  ];

  const handleSelect = async (id: string) => {
    setTaskId(id);
    
    // Check if it's a template
    const template = savedTemplates.find(t => t.id === id);
    let customData;
    if (template) {
      customData = { type: template.type, content: template.content };
    }
    
    const obs = await reset(id, customData);
    if (obs) {
      setObservation(obs);
      setEpisodeStarted(true);
    }
  };

  return (
    <motion.div 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="flex-1 flex items-center justify-center p-6 overflow-y-auto"
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0, y: 20 }}
        animate={{ scale: 1, opacity: 1, y: 0 }}
        className="bg-white p-8 rounded-2xl w-full max-w-4xl shadow-sm border border-gray-200 my-auto"
      >
        <div className="text-center mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Select a Cleanup Task</h2>
          <p className="text-gray-500">Choose a dataset complexity level to begin the cleaning process.</p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          {tasks.map(task => (
            <motion.div
              key={task.id}
              whileHover={{ scale: 1.03, y: -5 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => !loading && handleSelect(task.id)}
              className={`cursor-pointer ${loading ? 'opacity-50 pointer-events-none' : ''}`}
            >
              <Card className="h-full border-2 hover:border-blue-500 transition-colors">
                <div className="flex flex-col items-center text-center gap-3">
                  <div className="p-3 bg-gray-50 rounded-full">
                    {task.icon}
                  </div>
                  <h3 className="font-bold text-lg">{task.title}</h3>
                  <Badge text={task.issues} variant="warning" />
                  <div className="text-sm text-gray-500 font-mono bg-gray-100 px-2 py-1 rounded">
                    {task.rows}
                  </div>
                  <p className="text-sm text-gray-600 mt-2">{task.description}</p>
                </div>
              </Card>
            </motion.div>
          ))}
        </div>

        {savedTemplates.length > 0 && (
          <div className="mb-8">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Saved Templates</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {savedTemplates.map(template => (
                <Card key={template.id} className="border border-gray-200 hover:border-blue-400 transition-colors relative group">
                  <button 
                    onClick={(e) => { e.stopPropagation(); deleteTemplate(template.id); }}
                    className="absolute top-2 right-2 p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-md opacity-0 group-hover:opacity-100 transition-opacity"
                    title="Delete template"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                  <div 
                    className="cursor-pointer flex flex-col gap-2"
                    onClick={() => !loading && handleSelect(template.id)}
                  >
                    <div className="flex items-center gap-2">
                      {template.type === 'url' ? <LinkIcon className="w-4 h-4 text-blue-500" /> : <FileText className="w-4 h-4 text-blue-500" />}
                      <h4 className="font-semibold text-gray-900 truncate pr-6">{template.title}</h4>
                    </div>
                    <p className="text-sm text-gray-500 line-clamp-2">{template.description}</p>
                    <div className="mt-2">
                      <Badge text={template.type === 'url' ? 'URL Source' : 'Text Source'} variant="info" />
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          </div>
        )}
        
        <FileUpload />
        
        {loading && (
          <div className="mt-8 text-center text-blue-600 font-medium animate-pulse">
            Initializing environment...
          </div>
        )}
      </motion.div>
    </motion.div>
  );
}
