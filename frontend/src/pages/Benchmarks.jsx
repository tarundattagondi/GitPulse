import { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { GitBranch, Building2, Loader2 } from 'lucide-react';
import { listCompanies, getBenchmark } from '../services/api';
import BenchmarkRadar from '../components/BenchmarkRadar';

export default function Benchmarks() {
  const [params] = useSearchParams();
  const [username, setUsername] = useState(params.get('username') || '');
  const [companies, setCompanies] = useState([]);
  const [selected, setSelected] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    listCompanies().then((res) => setCompanies(res.data.companies)).catch(() => {});
  }, []);

  const runBenchmark = () => {
    if (!username || !selected) return;
    setLoading(true);
    getBenchmark(username, selected)
      .then((res) => setResult(res.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  return (
    <div className="min-h-screen bg-bg-primary">
      <nav className="border-b border-border px-6 py-4 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2 text-accent font-bold"><GitBranch size={20} /> GitPulse</Link>
        <span className="text-text-muted text-sm">Benchmarks</span>
      </nav>
      <div className="max-w-4xl mx-auto px-6 py-8">
        <h1 className="text-2xl font-bold text-text-primary mb-6 flex items-center gap-2"><Building2 size={24} /> Company Benchmarks</h1>
        <div className="flex gap-2 mb-6">
          <input value={username} onChange={(e) => setUsername(e.target.value)} placeholder="GitHub username"
            className="flex-1 px-3 py-2 rounded-lg bg-bg-secondary border border-border text-text-primary text-sm outline-none focus:border-accent" />
          <select value={selected} onChange={(e) => setSelected(e.target.value)}
            className="px-3 py-2 rounded-lg bg-bg-secondary border border-border text-text-primary text-sm outline-none focus:border-accent">
            <option value="">Select company</option>
            {companies.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
          <button onClick={runBenchmark} disabled={loading || !username || !selected}
            className="px-4 py-2 rounded-lg bg-accent text-white text-sm disabled:opacity-50 flex items-center gap-1">
            {loading ? <Loader2 size={14} className="animate-spin" /> : 'Compare'}
          </button>
        </div>

        {result && (
          <div className="space-y-6">
            <div className="p-4 rounded-lg bg-bg-secondary border border-border text-center">
              <p className="text-text-muted text-sm">{result.company} Intern Cohort</p>
              <p className="text-3xl font-bold text-accent mt-1">{result.overall_percentile}th</p>
              <p className="text-sm text-text-secondary">percentile</p>
              <p className="text-xs text-text-muted mt-1">{result.overall_verdict}</p>
            </div>
            <div className="p-4 rounded-lg bg-bg-secondary border border-border">
              <BenchmarkRadar dimensions={result.dimensions} />
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {Object.entries(result.dimensions).map(([key, dim]) => (
                <div key={key} className="p-3 rounded-lg bg-bg-tertiary border border-border">
                  <div className="flex justify-between text-sm">
                    <span className="text-text-secondary">{key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}</span>
                    <span className="text-accent font-medium">p{dim.percentile}</span>
                  </div>
                  {dim.verdict && <p className="text-xs text-text-muted mt-1">{dim.verdict}</p>}
                  {dim.matched && <p className="text-xs text-success mt-1">Matched: {dim.matched.join(', ')}</p>}
                  {dim.missing && dim.missing.length > 0 && <p className="text-xs text-danger mt-1">Missing: {dim.missing.join(', ')}</p>}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
