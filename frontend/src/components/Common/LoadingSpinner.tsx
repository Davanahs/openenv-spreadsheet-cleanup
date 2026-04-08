import React from 'react';
import { motion } from 'motion/react';
import { spinVariants } from '../../animations/variants';

export function LoadingSpinner({ size = 'md', text }: { size?: 'sm' | 'md' | 'lg', text?: string }) {
  const sizes = {
    sm: "h-4 w-4 border-2",
    md: "h-8 w-8 border-3",
    lg: "h-12 w-12 border-4"
  };

  return (
    <div className="flex flex-col items-center justify-center gap-3">
      <motion.div
        variants={spinVariants}
        animate="animate"
        className="inline-block"
      >
        <div className={`border-gray-200 border-t-blue-600 rounded-full ${sizes[size]}`} />
      </motion.div>
      {text && <span className="text-sm text-gray-500 font-medium">{text}</span>}
    </div>
  );
}
