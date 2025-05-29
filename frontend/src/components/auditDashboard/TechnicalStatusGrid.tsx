import React from 'react';
import { CheckCircle, AlertCircle } from 'lucide-react';
import type { TechnicalSEO } from '../../types/audit';

interface TechnicalStatusGridProps {
  technicalSEO: TechnicalSEO;
}

export const TechnicalStatusGrid: React.FC<TechnicalStatusGridProps> = ({ technicalSEO }) => {
  const items = [
    { label: 'HTTPS', value: technicalSEO.has_https },
    { label: 'Mobile', value: technicalSEO.has_mobile_friendly },
    { label: 'Viewport', value: technicalSEO.has_viewport_meta },
    { label: 'Favicon', value: technicalSEO.has_favicon },
    { label: 'Doctype', value: technicalSEO.has_doctype },
    { label: 'Structured Data', value: technicalSEO.has_structured_data }
  ];

  return (
    <div className="grid grid-cols-2 gap-2">
      {items.map(item => (
        <div key={item.label} className="flex items-center justify-between">
          <span className="text-xs text-secondaryText">{item.label}</span>
          {item.value ? (
            <CheckCircle className="h-4 w-4 text-emerald-500" />
          ) : (
            <AlertCircle className="h-4 w-4 text-rose-500" />
          )}
        </div>
      ))}
    </div>
  );
};