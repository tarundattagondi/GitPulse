import { CheckCircle, XCircle } from 'lucide-react';

export default function SkillsGapChart({ found = [], missing = [] }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div>
        <h4 className="text-sm font-medium text-success mb-2 flex items-center gap-1">
          <CheckCircle size={14} /> Skills Found
        </h4>
        <div className="flex flex-wrap gap-1.5">
          {found.map((s) => (
            <span key={s} className="px-2 py-0.5 text-xs rounded-full bg-success/10 text-success border border-success/20">{s}</span>
          ))}
          {found.length === 0 && <span className="text-xs text-text-muted">None detected</span>}
        </div>
      </div>
      <div>
        <h4 className="text-sm font-medium text-danger mb-2 flex items-center gap-1">
          <XCircle size={14} /> Skills Missing
        </h4>
        <div className="flex flex-wrap gap-1.5">
          {missing.map((s) => (
            <span key={s} className="px-2 py-0.5 text-xs rounded-full bg-danger/10 text-danger border border-danger/20">{s}</span>
          ))}
          {missing.length === 0 && <span className="text-xs text-text-muted">None</span>}
        </div>
      </div>
    </div>
  );
}
