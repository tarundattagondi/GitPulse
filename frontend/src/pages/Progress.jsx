import { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { GitBranch, TrendingUp } from 'lucide-react';
import { getProgress } from '../services/api';
import ProgressChart from '../components/ProgressChart';

export default function Progress() {
  const [params] = useSearchParams();
  const username = params.get('username') || '';
  const [input, setInput] = useState(username);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetch = (u) => {
    if (!u) return;
    setLoading(true);
    getProgress(u).then((res) => setData(res.data)).catch(() => {}).finally(() => setLoading(false));
  };

  useEffect(() => { if (username) fetch(username); }, [username]);

  return (
    <div className="min-h-screen bg-bg-primary">
      <nav className="border-b border-border px-6 py-4 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2 text-accent font-bold"><GitBranch size={20} /> GitPulse</Link>
        <span className="text-text-muted text-sm">Progress</span>
      </nav>
      <div className="max-w-4xl mx-auto px-6 py-8">
        <h1 className="text-2xl font-bold text-text-primary mb-6 flex items-center gap-2"><TrendingUp size={24} /> Progress History</h1>
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
              <p className="text-text-secondary text-sm mb-2">{data.snapshot_count} snapshots | Latest: {data.latest_score}/100</p>
              <ProgressChart snapshots={data.snapshots} />
            </div>
            {data.deltas && data.deltas.length > 0 && (
              <div className="p-4 rounded-lg bg-bg-secondary border border-border">
                <h3 className="text-sm font-medium text-text-primary mb-2">Changes</h3>
                {data.deltas.map((d, i) => <p key={i} className="text-xs text-text-muted">{d}</p>)}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
