import { useState } from 'react';
import { GitPullRequest, Eye, Code } from 'lucide-react';

export default function PRPreview({ preview, onOpenPR, loading }) {
  const [showDiff, setShowDiff] = useState(false);

  if (!preview) return null;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm text-text-muted">
          <span className="text-success">+{preview.stats?.additions || 0}</span>
          <span className="text-danger">-{preview.stats?.deletions || 0}</span>
          lines changed
        </div>
        <div className="flex gap-2">
          <button onClick={() => setShowDiff(!showDiff)}
            className="px-3 py-1.5 text-xs rounded-lg bg-bg-tertiary border border-border hover:border-accent/50 text-text-secondary flex items-center gap-1">
            {showDiff ? <Eye size={12} /> : <Code size={12} />} {showDiff ? 'Preview' : 'Diff'}
          </button>
          <button onClick={onOpenPR} disabled={loading}
            className="px-3 py-1.5 text-xs rounded-lg bg-accent hover:bg-accent-dark text-white flex items-center gap-1 disabled:opacity-50">
            <GitPullRequest size={12} /> {loading ? 'Opening...' : 'Open PR'}
          </button>
        </div>
      </div>
      <div className="max-h-96 overflow-auto rounded-lg bg-bg-primary border border-border p-4">
        <pre className="text-xs text-text-secondary whitespace-pre-wrap font-mono">
          {showDiff ? preview.diff_summary : preview.suggested_readme}
        </pre>
      </div>
    </div>
  );
}
