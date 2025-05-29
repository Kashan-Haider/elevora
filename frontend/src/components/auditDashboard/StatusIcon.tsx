import React from 'react';
import { CheckCircle, AlertTriangle, AlertCircle } from 'lucide-react';

interface StatusIconProps {
  status: string;
  className?: string;
}

export const StatusIcon: React.FC<StatusIconProps> = ({ status, className = "h-4 w-4" }) => {
  switch (status?.toLowerCase()) {
    case 'good':
    case 'optimal':
    case 'passed':
      return <CheckCircle className={`${className} text-emerald-500`} />;
    case 'warning':
    case 'needs_improvement':
      return <AlertTriangle className={`${className} text-amber-500`} />;
    case 'critical':
    case 'error':
    case 'failed':
      return <AlertCircle className={`${className} text-rose-500`} />;
    default:
      return <AlertCircle className={`${className} text-secondaryText`} />;
  }
};