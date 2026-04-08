import React, { useEffect, useState } from 'react';
import { motion } from 'motion/react';
import { useStore } from '../../store/appStore';
import { Card } from '../Common/Card';
import { Button } from '../Common/Button';
import { ProgressBar } from '../Common/ProgressBar';
import { Trophy, Download, RotateCcw, Star, X } from 'lucide-react';
import { getReport } from '../../api/environment';

interface ReportData {
  task_id: string;
  steps_used: number;
  max_steps: number;
  issues_fixed: number;
  initial_issues: number;
  quality_score: number;
  unapproved_attempts: number;
  final_score: number;
  success: boolean;
}

export function ResultsSummaryModal() {
  const { observation, stepCount, stepHistory, reset, setShowResultsModal, isResultsModalExpanded, setIsResultsModalExpanded } = useStore();
  const [report, setReport] = useState<ReportData | null>(null);

  useEffect(() => {
    getReport()
      .then(setReport)
      .catch(() => setReport(null));
  }, []);

  if (!observation) return null;

  const qualityScore = report?.quality_score ?? observation.quality_score;
  const finalScore   = report?.final_score   ?? qualityScore;
  const success      = report?.success       ?? qualityScore >= 0.5;
  const issuesFixed  = report
    ? report.issues_fixed
    : (observation.issues_summary.missing === 0 &&
       observation.issues_summary.duplicates === 0 &&
       observation.issues_summary.inconsistent === 0
        ? report?.initial_issues ?? 0
        : 0);

  const handleExportCSV = () => {
    if (!observation.data_sample || !observation.columns) return;

    const headers = observation.columns.join(',');
    const rows = observation.data_sample.map(row =>
      observation.columns!.map(col => {
        const v = row[col];
        if (v === null || v === undefined) return '';
        const str = String(v);
        return str.includes(',') || str.includes('"') || str.includes('\n')
          ? `"${str.replace(/"/g, '""')}"`
          : str;
      }).join(',')
    );
    const csvContent = [headers, ...rows].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url  = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href     = url;
    link.download = `cleaned_${observation.task_id || 'data'}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  };

  if (!isResultsModalExpanded) {
    return (
      <motion.div
        initial={{ y: 50, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        exit={{ y: 50, opacity: 0 }}
        onClick={() => setIsResultsModalExpanded(true)}
        className="fixed bottom-4 left-1/2 -translate-x-1/2 z-50 bg-gray-900 text-white px-6 py-4 rounded-full shadow-2xl flex items-center gap-4 cursor-pointer hover:bg-gray-800 transition-colors"
      >
        <div className={`p-2 rounded-full ${success ? 'bg-green-500/20 text-green-400' : 'bg-yellow-500/20 text-yellow-400'}`}>
          {success ? <Trophy className="w-5 h-5" /> : <Star className="w-5 h-5" />}
        </div>
        <div>
          <h3 className="font-bold text-sm tracking-wide">
            {success ? 'Cleanup Complete' : 'Episode Ended'}
          </h3>
          <p className="text-xs text-gray-400 flex items-center gap-2">
            <span>Score: <strong className="text-white">{(finalScore * 100).toFixed(0)}%</strong></span>
            • 
            <span>Steps: <strong className="text-white">{stepCount}</strong></span>
            <span className="ml-2 text-blue-400 text-xs font-semibold">(Click to expand summary)</span>
          </p>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4"
      onClick={() => setIsResultsModalExpanded(false)}
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0, y: 20 }}
        animate={{ scale: 1, opacity: 1, y: 0 }}
        className="bg-white p-8 rounded-2xl w-full max-w-md shadow-2xl relative"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          onClick={() => setIsResultsModalExpanded(false)}
          className="absolute top-4 right-4 p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-full transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
        <div className="text-center mb-6">
          <div className={`mx-auto w-16 h-16 ${success ? 'bg-yellow-100' : 'bg-gray-100'} rounded-full flex items-center justify-center mb-4`}>
            {success
              ? <Trophy className="w-8 h-8 text-yellow-600" />
              : <Star   className="w-8 h-8 text-gray-500" />
            }
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            {success ? 'Cleanup Complete!' : 'Episode Ended'}
          </h2>
          <p className="text-gray-500">
            {success
              ? "You've successfully cleaned the dataset."
              : "The episode reached its limit. Here's your summary."}
          </p>
        </div>

        <Card className="mb-6 bg-gray-50">
          <div className="space-y-4">
            <div>
              <div className="text-sm text-gray-500 mb-1">Data Quality Score</div>
              <ProgressBar value={qualityScore} showValue />
            </div>

            {report && (
              <div>
                <div className="text-sm text-gray-500 mb-1">Final Score (graded)</div>
                <ProgressBar value={finalScore} showValue />
              </div>
            )}

            <div className="grid grid-cols-2 gap-4 pt-4 border-t border-gray-200">
              <div>
                <div className="text-sm text-gray-500">Steps Taken</div>
                <div className="text-xl font-bold text-gray-900">{stepCount}</div>
              </div>
              <div>
                <div className="text-sm text-gray-500">Total Reward</div>
                <div className="text-xl font-bold text-blue-600">{finalScore.toFixed(2)}</div>
              </div>
              <div>
                <div className="text-sm text-gray-500">Initial Issues</div>
                <div className="text-xl font-bold text-gray-900">
                  {report ? report.initial_issues : (issuesFixed + observation.issues_summary.missing + observation.issues_summary.duplicates + observation.issues_summary.inconsistent)}
                </div>
              </div>
              <div>
                <div className="text-sm text-gray-500">Remaining Issues</div>
                <div className="text-xl font-bold text-gray-900">
                  {observation.issues_summary.missing +
                   observation.issues_summary.duplicates +
                   observation.issues_summary.inconsistent}
                </div>
              </div>
              {report && (
                <>
                  <div>
                    <div className="text-sm text-gray-500">Issues Fixed</div>
                    <div className="text-xl font-bold text-green-600">{issuesFixed}</div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-500">Unapproved Attempts</div>
                    <div className="text-xl font-bold text-red-500">{report.unapproved_attempts}</div>
                  </div>
                </>
              )}
              {!report && (
                 <div>
                   <div className="text-sm text-gray-500">Issues Fixed</div>
                   <div className="text-xl font-bold text-green-600">{issuesFixed}</div>
                 </div>
              )}
            </div>
          </div>
        </Card>

        <div className="flex gap-3">
          <Button variant="outline" className="flex-1" onClick={handleExportCSV}>
            <Download className="w-4 h-4 mr-2" /> Export CSV
          </Button>
          <Button variant="primary" className="flex-1" onClick={() => { setShowResultsModal(false); reset(); }}>
            <RotateCcw className="w-4 h-4 mr-2" /> Try Another
          </Button>
        </div>
      </motion.div>
    </motion.div>
  );
}
