import React, { useRef, useState } from 'react';
import { UploadCloud, Link as LinkIcon, FileText, Save } from 'lucide-react';
import { motion } from 'motion/react';
import { useStore } from '../../store/appStore';
import { useEnvironment } from '../../hooks/useEnvironment';
import { Button } from '../Common/Button';

export function FileUpload() {
  const [activeTab, setActiveTab] = useState<'file' | 'url' | 'text'>('file');
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const [urlValue, setUrlValue] = useState('');
  const [textValue, setTextValue] = useState('');
  const [templateName, setTemplateName] = useState('');
  const [saveAsTemplate, setSaveAsTemplate] = useState(false);
  
  const setTaskId = useStore(s => s.setTaskId);
  const setObservation = useStore(s => s.setObservation);
  const setEpisodeStarted = useStore(s => s.setEpisodeStarted);
  const setLastAction = useStore(s => s.setLastAction);
  const addToHistory = useStore(s => s.addToHistory);
  const addLog = useStore(s => s.addLog);
  const setEpisodeDone = useStore(s => s.setEpisodeDone);
  const saveTemplate = useStore(s => s.saveTemplate);
  const { reset, executeAction, loading } = useEnvironment();

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFile(e.target.files[0]);
    }
  };

  const handleFile = async (file: File) => {
    console.log("File selected:", file.name);
    await startCustomTask({ type: 'file', content: file });
  };

  const handleUrlSubmit = async () => {
    if (!urlValue.trim()) return;
    if (saveAsTemplate && templateName.trim()) {
      saveTemplate({
        id: `tpl_${Date.now()}`,
        title: templateName,
        type: 'url',
        content: urlValue,
        description: 'Custom URL dataset'
      });
    }
    await startCustomTask({ type: 'url', content: urlValue });
  };

  const handleTextSubmit = async () => {
    if (!textValue.trim()) return;
    if (saveAsTemplate && templateName.trim()) {
      saveTemplate({
        id: `tpl_${Date.now()}`,
        title: templateName,
        type: 'text',
        content: textValue,
        description: 'Custom text dataset'
      });
    }
    await startCustomTask({ type: 'text', content: textValue });
  };

  const startCustomTask = async (customData: { type: 'text' | 'url' | 'file', content: string | File }) => {
    setTaskId('custom');
    const obs = await reset('custom', customData);
    if (obs) {
      setObservation(obs);
      setEpisodeStarted(true);
    }
  };

  const handleUrlKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !loading && urlValue.trim() && (!saveAsTemplate || templateName.trim())) {
      e.preventDefault();
      handleUrlSubmit();
    }
  };

  const handleTextKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey) && !loading && textValue.trim() && (!saveAsTemplate || templateName.trim())) {
      e.preventDefault();
      handleTextSubmit();
    }
  };

  const handleTemplateNameKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !loading && templateName.trim()) {
      e.preventDefault();
      if (activeTab === 'url' && urlValue.trim()) {
        handleUrlSubmit();
      } else if (activeTab === 'text' && textValue.trim()) {
        handleTextSubmit();
      }
    }
  };

  return (
    <div className="mt-8 pt-8 border-t border-gray-200">
      <div className="text-center mb-6">
        <h3 className="text-lg font-semibold text-gray-900">Or use your own dataset</h3>
        <p className="text-sm text-gray-500">Upload a file, link a URL, or paste raw data</p>
      </div>
      
      <div className="bg-gray-50 rounded-xl p-1 flex gap-1 mb-6 border border-gray-200 w-full max-w-md mx-auto">
        <button
          onClick={() => setActiveTab('file')}
          className={`flex-1 py-2 px-4 text-sm font-medium rounded-lg flex items-center justify-center gap-2 transition-colors ${activeTab === 'file' ? 'bg-white shadow-sm text-blue-600' : 'text-gray-600 hover:bg-gray-100'}`}
        >
          <UploadCloud className="w-4 h-4" /> File
        </button>
        <button
          onClick={() => setActiveTab('url')}
          className={`flex-1 py-2 px-4 text-sm font-medium rounded-lg flex items-center justify-center gap-2 transition-colors ${activeTab === 'url' ? 'bg-white shadow-sm text-blue-600' : 'text-gray-600 hover:bg-gray-100'}`}
        >
          <LinkIcon className="w-4 h-4" /> URL
        </button>
        <button
          onClick={() => setActiveTab('text')}
          className={`flex-1 py-2 px-4 text-sm font-medium rounded-lg flex items-center justify-center gap-2 transition-colors ${activeTab === 'text' ? 'bg-white shadow-sm text-blue-600' : 'text-gray-600 hover:bg-gray-100'}`}
        >
          <FileText className="w-4 h-4" /> Text
        </button>
      </div>
      
      <div className="max-w-2xl mx-auto">
        {activeTab === 'file' && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            whileHover={{ scale: 1.01 }}
            whileTap={{ scale: 0.99 }}
            className={`relative border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${
              isDragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-blue-400 hover:bg-gray-50'
            } ${loading ? 'opacity-50 pointer-events-none' : ''}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <input 
              type="file" 
              ref={fileInputRef} 
              onChange={handleFileInput} 
              accept=".csv,.xlsx" 
              className="hidden" 
            />
            
            <div className="flex flex-col items-center justify-center gap-3">
              <div className="p-4 bg-blue-100 rounded-full text-blue-600">
                <UploadCloud className="w-8 h-8" />
              </div>
              <div>
                <p className="font-medium text-gray-900">Click to upload or drag and drop</p>
                <p className="text-sm text-gray-500 mt-1">CSV or XLSX (max. 10MB)</p>
              </div>
            </div>
          </motion.div>
        )}

        {activeTab === 'url' && (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Dataset URL (CSV/JSON)</label>
              <input 
                type="url" 
                value={urlValue}
                onChange={(e) => setUrlValue(e.target.value)}
                onKeyDown={handleUrlKeyDown}
                placeholder="https://example.com/data.csv"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
              />
              <p className="text-xs text-gray-500 mt-1">Press Enter to load</p>
            </div>
            
            <div className="flex items-center gap-2 mb-2">
              <input 
                type="checkbox" 
                id="saveUrlTemplate" 
                checked={saveAsTemplate}
                onChange={(e) => setSaveAsTemplate(e.target.checked)}
                className="rounded text-blue-600 focus:ring-blue-500"
              />
              <label htmlFor="saveUrlTemplate" className="text-sm text-gray-700 flex items-center gap-1">
                <Save className="w-3.5 h-3.5" /> Save as template
              </label>
            </div>
            
            {saveAsTemplate && (
              <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }}>
                <input 
                  type="text" 
                  value={templateName}
                  onChange={(e) => setTemplateName(e.target.value)}
                  onKeyDown={handleTemplateNameKeyDown}
                  placeholder="Template Name (e.g., Sales Data Q1)"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all mb-4"
                />
              </motion.div>
            )}
            
            <Button 
              className="w-full" 
              onClick={handleUrlSubmit} 
              disabled={loading || !urlValue.trim() || (saveAsTemplate && !templateName.trim())}
            >
              Load from URL
            </Button>
          </motion.div>
        )}

        {activeTab === 'text' && (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Paste Raw Data (CSV format)</label>
              <textarea 
                value={textValue}
                onChange={(e) => setTextValue(e.target.value)}
                onKeyDown={handleTextKeyDown}
                placeholder="id,name,age&#10;1,John,28&#10;2,Jane,32"
                rows={5}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all font-mono text-sm"
              />
              <p className="text-xs text-gray-500 mt-1">Press Ctrl+Enter (or Cmd+Enter) to load</p>
            </div>
            
            <div className="flex items-center gap-2 mb-2">
              <input 
                type="checkbox" 
                id="saveTextTemplate" 
                checked={saveAsTemplate}
                onChange={(e) => setSaveAsTemplate(e.target.checked)}
                className="rounded text-blue-600 focus:ring-blue-500"
              />
              <label htmlFor="saveTextTemplate" className="text-sm text-gray-700 flex items-center gap-1">
                <Save className="w-3.5 h-3.5" /> Save as template
              </label>
            </div>
            
            {saveAsTemplate && (
              <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }}>
                <input 
                  type="text" 
                  value={templateName}
                  onChange={(e) => setTemplateName(e.target.value)}
                  onKeyDown={handleTemplateNameKeyDown}
                  placeholder="Template Name (e.g., Sample Users)"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all mb-4"
                />
              </motion.div>
            )}
            
            <Button 
              className="w-full" 
              onClick={handleTextSubmit} 
              disabled={loading || !textValue.trim() || (saveAsTemplate && !templateName.trim())}
            >
              Load Text Data
            </Button>
          </motion.div>
        )}
      </div>
    </div>
  );
}
