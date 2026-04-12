import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from 'recharts';

export default function BenchmarkRadar({ dimensions }) {
  if (!dimensions) return null;

  const data = Object.entries(dimensions).map(([key, val]) => ({
    subject: key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()),
    percentile: val.percentile,
    fullMark: 100,
  }));

  return (
    <ResponsiveContainer width="100%" height={300}>
      <RadarChart data={data}>
        <PolarGrid stroke="#2e303a" />
        <PolarAngleAxis dataKey="subject" tick={{ fill: '#9ca3af', fontSize: 11 }} />
        <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fill: '#6b7280', fontSize: 10 }} />
        <Radar name="Percentile" dataKey="percentile" stroke="#6366f1" fill="#6366f1" fillOpacity={0.3} />
      </RadarChart>
    </ResponsiveContainer>
  );
}
