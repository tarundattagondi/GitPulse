export default function ScoreBreakdown({ breakdown }) {
  if (!breakdown) return null;
  const categories = Object.entries(breakdown);

  return (
    <div className="space-y-3">
      {categories.map(([key, data]) => {
        const score = data.score ?? data;
        const max = data.max ?? 100;
        const pct = Math.round((score / max) * 100);
        const label = key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
        const color = pct >= 75 ? 'bg-success' : pct >= 50 ? 'bg-warning' : 'bg-danger';

        return (
          <div key={key}>
            <div className="flex justify-between text-sm mb-1">
              <span className="text-text-secondary">{label}</span>
              <span className="text-text-primary font-medium">{score}/{max}</span>
            </div>
            <div className="h-2 bg-bg-tertiary rounded-full overflow-hidden">
              <div className={`h-full rounded-full ${color} transition-all duration-700`} style={{ width: `${pct}%` }} />
            </div>
            {data.reasoning && (
              <p className="text-xs text-text-muted mt-1">{data.reasoning}</p>
            )}
          </div>
        );
      })}
    </div>
  );
}
