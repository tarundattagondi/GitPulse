import { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { GitBranch, Clock } from 'lucide-react';
import { getProgress } from '../services/api';
import ProgressChart from '../components/ProgressChart';
import ScoreBreakdown from '../components/ScoreBreakdown';

export default function History() {
  const [params] = useSearchParams();
  const username = params.get('username') || '';
  const [input, setInput] = useState(username);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetch = (u) => {
    if (!u) return;
    setLoading(true);
    getProgress(u, null, 365).then((res) => setData(res.data)).catch(() => {}).finally(() => setLoading(false));
  };

  useEffect(() => { if (username) fetch(username); }, [username]);

  return (
    <div className="min-h-screen bg-bg-primary">
      <nav className="border-b border-border px-6 py-4 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2 text-accent font-bold"><GitBranch size={20} /> GitPulse</Link>
        <span className="text-text-muted text-sm">History</span>
      </nav>
      <div className="max-w-4xl mx-auto px-6 py-8">
        <h1 className="text-2xl font-bold text-text-primary mb-6 flex items-center gap-2"><Clock size={24} /> Score History</h1>
        <div className="flex gap-2 mb-6">
          <input value={input} onChange={(e) => setInput(e.target.value)} placeholder="GitHub username"
            className="flex-1 px-3 py-2 rounded-lg bg-bg-secondary border border-border text-text-primary text-sm outline-none focus:border-accent" />
          <button onClick={() => fetch(input)} disabled={loading} className="px-4 py-2 rounded-lg bg-accent text-white text-sm disabled:opacity-50">
            {loading ? 'Loading...' : 'Load'}
          </button>
        </div>
        {data && (
          <div className="space-y-6">
            <div className="p-4 rounded-lg bg-bg-secondary border border-border">
              <ProgressChart snapshots={data.snapshots} />
            </div>
            {data.snapshots && data.snapshots.length > 0 && (
              <div className="space-y-3">
                <h3 className="text-sm font-medium text-text-primary">Snapshots</h3>
                {data.snapshots.slice().reverse().map((s, i) => (
                  <div key={i} className="p-3 rounded-lg bg-bg-tertiary border border-border">
                    <div className="flex justify-between text-sm mb-2">
                      <span className="text-text-muted">{new Date(s.timestamp).toLocaleDateString()}</span>
                      <span className="text-accent font-medium">{s.overall_score}/100</span>
                    </div>
                    <ScoreBreakdown breakdown={s.category_scores} />
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
