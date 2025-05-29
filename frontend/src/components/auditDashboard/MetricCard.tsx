import React from 'react';
import { DivideIcon as LucideIcon } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string | number;
  description: string;
  icon: React.ReactNode;
  color?: 'success' | 'warning' | 'error' | 'default';
}

const colorClasses = {
  success: 'text-emerald-500',
  warning: 'text-amber-500',
  error: 'text-rose-500',
  default: 'text-primaryAccent'
};

export const MetricCard: React.FC<MetricCardProps> = ({ 
  title, 
  value, 
  description, 
  icon, 
  color = 'default' 
}) => {
  return (
    <div className="bg-secondary rounded-lg p-5 border border-border shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-medium text-secondaryText">{title}</h3>
        <div className={colorClasses[color]}>{icon}</div>
      </div>
      <p className={`text-2xl font-bold ${colorClasses[color]}`}>{value}</p>
      <p className="text-sm text-secondaryText mt-1">{description}</p>
    </div>
  );
};