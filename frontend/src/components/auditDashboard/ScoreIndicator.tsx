import React from 'react';

interface ScoreIndicatorProps {
  score: number;
  label?: string;
  size?: 'sm' | 'md' | 'lg';
}

export const ScoreIndicator: React.FC<ScoreIndicatorProps> = ({ score, label, size = 'md' }) => {
  const getScoreColor = (score: number): string => {
    if (score >= 80) return 'text-emerald-500';
    if (score >= 60) return 'text-primaryAccent';
    if (score >= 40) return 'text-amber-500';
    return 'text-rose-500';
  };

  const sizeClasses = {
    sm: 'text-xl',
    md: 'text-2xl',
    lg: 'text-3xl'
  };

  return (
    <div className="text-center">
      <div className={`font-bold ${sizeClasses[size]} ${getScoreColor(score)}`}>
        {score}
      </div>
      {label && <div className="text-xs text-secondaryText uppercase tracking-wide">{label}</div>}
    </div>
  );
};