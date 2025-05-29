import React from 'react';

interface ScoreGaugeProps {
  value: number;
  size?: 'sm' | 'md' | 'lg';
  label?: string;
}

export const ScoreGauge: React.FC<ScoreGaugeProps> = ({ value, size = 'md', label }) => {
  const getScoreColor = (score: number): string => {
    if (score >= 80) return 'text-emerald-500';
    if (score >= 60) return 'text-primaryAccent';
    if (score >= 40) return 'text-amber-500';
    return 'text-rose-500';
  };

  const sizeClasses = {
    sm: 'text-3xl',
    md: 'text-4xl',
    lg: 'text-5xl'
  };

  return (
    <div className="relative flex flex-col items-center">
      <div className={`font-bold ${sizeClasses[size]} ${getScoreColor(value)}`}>
        {value}
      </div>
      {label && (
        <div className="text-xs text-secondaryText uppercase tracking-wide mt-1">
          {label}
        </div>
      )}
    </div>
  );
};