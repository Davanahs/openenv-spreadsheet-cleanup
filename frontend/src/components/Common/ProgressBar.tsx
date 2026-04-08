import React from 'react';
import { motion } from 'motion/react';
import { scoreBarVariants } from '../../animations/variants';

interface ProgressBarProps {
  value: number; // 0 to 1
  label?: string;
  showValue?: boolean;
}

export function ProgressBar({ value, label, showValue = true }: ProgressBarProps) {
  const percent = Math.max(0, Math.min(100, Math.round(value * 100)));
  
  let colorClass = "bg-red-500";
  if (percent >= 80) colorClass = "bg-green-500";
  else if (percent >= 50) colorClass = "bg-yellow-500";

  return (
    <div className="w-full">
      {(label || showValue) && (
        <div className="flex justify-between items-center mb-1 text-sm font-medium text-gray-700">
          {label && <span>{label}</span>}
          {showValue && <span>{percent}%</span>}
        </div>
      )}
      <div className="h-2.5 w-full bg-gray-200 rounded-full overflow-hidden">
        <motion.div
          custom={percent}
          variants={scoreBarVariants}
          animate="animate"
          className={`h-full rounded-full ${colorClass}`}
        />
      </div>
    </div>
  );
}
