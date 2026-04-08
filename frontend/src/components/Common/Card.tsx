import React from 'react';
import { motion } from 'motion/react';
import { cn } from './Button';

interface CardProps {
  key?: React.Key;
  title?: string;
  children: React.ReactNode;
  icon?: React.ReactNode;
  action?: React.ReactNode;
  variant?: 'default' | 'outlined';
  className?: string;
}

export function Card({ 
  title, 
  children, 
  icon,
  action,
  variant = 'default',
  className
}: CardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        "rounded-xl bg-white p-4 shadow-sm border border-gray-100",
        variant === 'outlined' && "shadow-none border-gray-200",
        className
      )}
    >
      {title && (
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            {icon && <span className="text-gray-500">{icon}</span>}
            <h3 className="font-semibold text-gray-900">{title}</h3>
          </div>
          {action && <div>{action}</div>}
        </div>
      )}
      {children}
    </motion.div>
  );
}
