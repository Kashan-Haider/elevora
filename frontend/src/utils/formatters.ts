export const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };
  
  export const getScoreColor = (score: number): string => {
    if (score >= 80) return 'text-emerald-500';
    if (score >= 60) return 'text-primaryAccent';
    if (score >= 40) return 'text-amber-500';
    return 'text-rose-500';
  };
  
  export const getSeverityColor = (severity: string | null): string => {
    if (!severity) return 'text-secondaryText';
    switch (severity.toLowerCase()) {
      case 'critical':
        return 'text-rose-500';
      case 'high':
        return 'text-orange-500';
      case 'medium':
        return 'text-amber-500';
      case 'low':
        return 'text-emerald-500';
      default:
        return 'text-secondaryText';
    }
  };