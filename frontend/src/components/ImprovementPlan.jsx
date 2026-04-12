import { Calendar, Lightbulb, AlertTriangle } from 'lucide-react';

export default function ImprovementPlan({ plan, actions }) {
  return (
    <div className="space-y-6">
      {actions && actions.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-text-primary flex items-center gap-2 mb-3">
            <AlertTriangle size={18} className="text-warning" /> Priority Actions
          </h3>
          <ul className="space-y-2">
            {actions.map((a, i) => (
              <li key={i} className="flex gap-2 text-sm text-text-secondary">
                <span className="text-accent font-bold">{i + 1}.</span> {a}
              </li>
            ))}
          </ul>
        </div>
      )}
      {plan && Object.keys(plan).length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-text-primary flex items-center gap-2 mb-3">
            <Calendar size={18} className="text-accent" /> 30-Day Plan
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {Object.entries(plan).map(([week, data]) => (
              <div key={week} className="p-3 rounded-lg bg-bg-tertiary border border-border">
                <h4 className="text-sm font-medium text-accent-light capitalize">{week.replace('_', ' ')}</h4>
                <p className="text-xs text-text-muted mt-1">{data.focus}</p>
                <ul className="mt-2 space-y-1">
                  {(data.tasks || []).slice(0, 3).map((t, i) => (
                    <li key={i} className="text-xs text-text-secondary flex gap-1">
                      <Lightbulb size={10} className="text-warning mt-0.5 shrink-0" /> {t}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
