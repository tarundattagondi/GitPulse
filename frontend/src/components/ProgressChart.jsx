import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export default function ProgressChart({ snapshots }) {
  if (!snapshots || snapshots.length === 0) {
    return <p className="text-text-muted text-sm">No progress data yet. Run an analysis to start tracking.</p>;
  }

  const data = snapshots.map((s) => ({
    date: new Date(s.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    score: s.overall_score,
    ...s.category_scores,
  }));

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#2e303a" />
        <XAxis dataKey="date" stroke="#6b7280" fontSize={12} />
        <YAxis domain={[0, 100]} stroke="#6b7280" fontSize={12} />
        <Tooltip
          contentStyle={{ background: '#1a1b26', border: '1px solid #2e303a', borderRadius: '8px' }}
          labelStyle={{ color: '#e5e7eb' }} itemStyle={{ color: '#9ca3af' }}
        />
        <Line type="monotone" dataKey="score" stroke="#6366f1" strokeWidth={2} dot={{ r: 4, fill: '#6366f1' }} name="Overall" />
      </LineChart>
    </ResponsiveContainer>
  );
}
