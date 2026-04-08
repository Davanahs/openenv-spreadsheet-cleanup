import React from 'react';
import { motion } from 'motion/react';
import { panelVariants } from '../../animations/variants';
import { useStore } from '../../store/appStore';
import { Card } from '../Common/Card';
import { FileSpreadsheet, AlertTriangle } from 'lucide-react';

export function LeftPanel() {
  const { observation } = useStore();

  if (!observation) return null;

  const totalIssues = observation.issues_summary.missing + 
                      observation.issues_summary.duplicates + 
                      observation.issues_summary.inconsistent;

  return (
    <motion.div 
      variants={panelVariants}
      initial="hidden"
      animate="visible"
      className="flex flex-col gap-4 h-full"
    >
      <div className="mb-2">
        <h2 className="text-lg font-bold text-gray-900">Dataset Overview</h2>
        <p className="text-sm text-gray-500">Information and detected issues</p>
      </div>

      <Card title="Dataset Info" icon={<FileSpreadsheet className="w-5 h-5" />} variant="outlined">
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-gray-50 p-3 rounded-lg border border-gray-100">
            <div className="text-xs text-gray-500 uppercase tracking-wider font-semibold mb-1">Columns</div>
            <div className="text-2xl font-bold text-gray-900">{observation.columns.length}</div>
          </div>
          <div className="bg-red-50 p-3 rounded-lg border border-red-100">
            <div className="text-xs text-red-500 uppercase tracking-wider font-semibold mb-1">Issues</div>
            <div className="text-2xl font-bold text-red-600">{totalIssues}</div>
          </div>
        </div>
      </Card>

      <Card title="Detected Issues" icon={<AlertTriangle className="w-5 h-5 text-yellow-500" />} variant="outlined" className="flex-1 flex flex-col">
        <div className="space-y-2 mb-4">
          <div className="flex justify-between items-center p-2 bg-gray-50 rounded border border-gray-100">
            <span className="text-sm font-medium text-gray-700">Missing Values</span>
            <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${observation.issues_summary.missing > 0 ? 'bg-red-100 text-red-600 border border-red-200' : 'bg-green-100 text-green-600 border border-green-200'}`}>
              {observation.issues_summary.missing}
            </div>
          </div>
          <div className="flex justify-between items-center p-2 bg-gray-50 rounded border border-gray-100">
            <span className="text-sm font-medium text-gray-700">Duplicates</span>
            <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${observation.issues_summary.duplicates > 0 ? 'bg-yellow-100 text-yellow-600 border border-yellow-200' : 'bg-green-100 text-green-600 border border-green-200'}`}>
              {observation.issues_summary.duplicates}
            </div>
          </div>
          <div className="flex justify-between items-center p-2 bg-gray-50 rounded border border-gray-100">
            <span className="text-sm font-medium text-gray-700">Inconsistent</span>
            <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${observation.issues_summary.inconsistent > 0 ? 'bg-blue-100 text-blue-600 border border-blue-200' : 'bg-green-100 text-green-600 border border-green-200'}`}>
              {observation.issues_summary.inconsistent}
            </div>
          </div>
        </div>
        
        {observation.issues.length > 0 && (
          <div className="mt-2 pt-4 border-t border-gray-100 flex-1 overflow-hidden flex flex-col">
            <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Specific Issues</h4>
            <div className="space-y-2 overflow-y-auto flex-1 pr-1">
              {observation.issues.map((issue, idx) => (
                <div key={idx} className="text-sm flex items-start gap-2 p-2.5 bg-white border border-red-100 rounded-lg shadow-sm">
                  <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0 text-red-500" />
                  <div>
                    <div className="font-semibold text-gray-900">{issue.column}</div>
                    <div className="text-gray-600 capitalize">{issue.type.replace('_', ' ')}</div>
                    <div className="text-red-500 text-xs mt-1 font-medium">{issue.rows.length} rows affected</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </Card>
    </motion.div>
  );
}
