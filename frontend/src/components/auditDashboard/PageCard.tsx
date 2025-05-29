import React from 'react';
import { ExternalLink, FileText, AlertTriangle, Award } from 'lucide-react';
import { ScoreIndicator } from './ScoreIndicator';
import type { Page } from '../../types/audit';

interface PageCardProps {
  page: Page;
  onClick?: () => void;
  isSelected?: boolean;
}

export const PageCard: React.FC<PageCardProps> = ({ page, onClick, isSelected }) => {
  const getScoreColor = (score: number): string => {
    if (score >= 80) return 'bg-emerald-500';
    if (score >= 60) return 'bg-primaryAccent';
    if (score >= 40) return 'bg-amber-500';
    return 'bg-rose-500';
  };

  return (
    <div 
      className={`p-4 border-b border-border last:border-b-0 hover:bg-surface cursor-pointer transition-colors ${
        isSelected ? 'bg-primaryAccent/5 border-l-4 border-l-primaryAccent' : ''
      }`}
      onClick={onClick}
    >
      <div className="flex items-center justify-between">
        <div className="flex-1 min-w-0">
          <div className="flex items-center mb-2">
            <div className={`w-3 h-3 rounded-full mr-3 ${getScoreColor(page.scores.overall)}`}></div>
            <h4 className="text-sm font-medium text-primaryText truncate">
              {page.page_info.title || 'Untitled Page'}
            </h4>
          </div>
          <p className="text-xs text-secondaryText truncate mb-2">
            {page.page_info.url}
          </p>
          <div className="flex items-center space-x-4 text-xs text-secondaryText">
            <span className="flex items-center">
              <Award className="h-3 w-3 mr-1" />
              {page.scores.overall}/100
            </span>
            <span className="flex items-center">
              <AlertTriangle className="h-3 w-3 mr-1" />
              {page.page_info.issues_count} issues
            </span>
            <span className="flex items-center">
              <FileText className="h-3 w-3 mr-1" />
              {page.page_info.word_count} words
            </span>
          </div>
        </div>
        <div className="flex items-center space-x-3">
          <ScoreIndicator score={page.scores.overall} size="sm" />
          <a 
            href={page.page_info.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-primaryAccent hover:text-primaryAccent/80 transition-colors"
            onClick={e => e.stopPropagation()}
          >
            <ExternalLink className="h-5 w-5" />
          </a>
        </div>
      </div>
    </div>
  );
};